"""
╔══════════════════════════════════════════════════════════════════╗
║  BSR-V233-CTO-RUNTIME-ENV-LOOKUP-AHMAD-20260726                  ║
║  tiktok_lookup.py v2.3.3 - Runtime Env Lookup (Railway fix)      ║
║  Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)             ║
╚══════════════════════════════════════════════════════════════════╝

🏆 Architecture v2.3.1 (VPN-Aware):
  L0: RapidAPI tiktok-scraper7 (PRIMARY - 99% success)
      - /user/info : basic info + stats
      - /user/posts : 30 videos with region + timestamp
  L1-L3: Fallback layers

🧠 VPN Detection Logic:
  1. Fetch 30 videos → collect all video.region values
  2. If ONE region dominates (>80%), check for minority region
  3. Minority region often reveals TRUE origin (VPN forgotten)
  4. Cross-check with posting timezone (VPN can't fake habits)
  5. Weighted verdict:
     - minority + timezone match → HIGH confidence for minority
     - majority alone → MEDIUM confidence
     - timezone strongly matches specific region → override

Environment Variables:
  RAPIDAPI_KEY   - Required for L0
  RAPIDAPI_HOST  - Default: tiktok-scraper7.p.rapidapi.com

Public API (backward compatible with bot.py v2.1.8.9):
  lookup_tiktok_user(username) -> str  (Markdown for Telegram)
  clean_username(raw) -> str
  lookup_tiktok_user_dict(username) -> dict
"""

import asyncio
import json
import logging
import os
import random
import re
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

# ═══════════════════════════════════════════════════════════
# 🌍 Regions Database (249 countries)
# ═══════════════════════════════════════════════════════════
try:
    from regions_database import (
        WORLD_COUNTRIES,
        get_country_info,
        get_arabic_name,
        get_english_name,
        get_flag,
        is_arab_country,
        is_gcc_country,
        STATS as REGIONS_STATS,
    )
    REGIONS_DB_AVAILABLE = True
except ImportError as e:
    logging.error(f"[tiktok_lookup] regions_database not available: {e}")
    REGIONS_DB_AVAILABLE = False
    WORLD_COUNTRIES = {}

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# 🏆 RapidAPI Configuration - RUNTIME LOOKUP (v2.3.3 fix)
# ═══════════════════════════════════════════════════════════
# ⚠️ Do NOT capture os.getenv at module-level. Railway may inject
# ENV variables AFTER Python imports this module. Read them inside
# functions on each call (lazy/runtime lookup).

def _get_rapidapi_config():
    """Read RAPIDAPI credentials at CALL time (not import time).

    Also tries load_dotenv() as fallback for local dev.
    """
    key = os.getenv("RAPIDAPI_KEY", "").strip()
    host = os.getenv("RAPIDAPI_HOST", "tiktok-scraper7.p.rapidapi.com").strip()
    if not key:
        try:
            from dotenv import load_dotenv
            load_dotenv(override=False)
            key = os.getenv("RAPIDAPI_KEY", "").strip()
            host = os.getenv("RAPIDAPI_HOST", host).strip()
        except ImportError:
            pass
    return key, host, bool(key)


# Import-time snapshot (for logging only — not used for decisions)
_INITIAL_KEY, _INITIAL_HOST, _INITIAL_ENABLED = _get_rapidapi_config()
if _INITIAL_ENABLED:
    logger.info(f"[L0] ✅ RapidAPI enabled at import: {_INITIAL_HOST}")
else:
    logger.warning("[L0] ⚠️ RAPIDAPI_KEY not set at import (will retry at runtime)")

# Config
POSTS_COUNT = 30  # Sample size for VPN-aware analysis
TIMEOUT = httpx.Timeout(20.0, connect=10.0)

# ═══════════════════════════════════════════════════════════
# 🗺️ Timezone → Country ranges (for VPN detection)
# ═══════════════════════════════════════════════════════════
# Each entry: prime-time hours in UTC when locals post most
TIMEZONE_PRIME_WINDOWS = {
    # UTC hour ranges → likely country ISO
    (15, 21): "SA",  # 18-24 SA local (also UAE, KW, QA, BH)
    (17, 23): "GB",  # 18-24 GB local
    (0, 4):   "US",  # 20-24 EST (US East)
    (16, 22): "EG",  # 18-24 EG local (also TR, GR)
    (11, 15): "JP",  # 20-24 JST
    (12, 16): "CN",  # 20-24 CST (also SG, MY)
    (23, 3):  "BR",  # 20-24 BRT
    (18, 22): "DE",  # 19-23 CET (also FR, IT, ES, NL)
}

# Countries that share UTC offset (used to disambiguate)
UTC_OFFSET_TO_COUNTRIES = {
    3:  ["SA", "AE", "KW", "QA", "BH", "IQ", "YE", "TR", "RU", "KE", "ET"],
    2:  ["EG", "LY", "GR", "FI", "SD", "JO", "LB", "SY", "ZA", "PS"],
    1:  ["FR", "DE", "IT", "ES", "NL", "MA", "DZ", "TN", "NG", "SE"],
    0:  ["GB", "PT", "IE", "IS"],
    -5: ["US", "CO", "PE", "EC", "CU"],
    -3: ["BR", "AR", "UY", "CL"],
    5:  ["PK", "AF"],
    7:  ["TH", "VN", "ID"],
    8:  ["CN", "MY", "SG", "PH", "HK", "TW", "AU"],
    9:  ["JP", "KR"],
    5.5: ["IN"],
}


# ═══════════════════════════════════════════════════════════
# 📊 Result container
# ═══════════════════════════════════════════════════════════
class LookupResult(dict):
    def __getattr__(self, key):
        return self.get(key)


# ═══════════════════════════════════════════════════════════
# 🏆 LAYER 0: RapidAPI tiktok-scraper7
# ═══════════════════════════════════════════════════════════
async def layer0_rapidapi(username: str) -> Optional[Dict[str, Any]]:
    """RapidAPI primary layer - reads env at CALL time (v2.3.3)."""
    rapidapi_key, rapidapi_host, rapidapi_enabled = _get_rapidapi_config()
    if not rapidapi_enabled:
        logger.warning(f"[L0] RAPIDAPI_KEY still not available for @{username}")
        return None

    logger.info(f"[L0] 🚀 Attempting RapidAPI for @{username} (host={rapidapi_host})")
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": rapidapi_host,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # ── /user/info ──
            info_url = f"https://{rapidapi_host}/user/info"
            info_resp = await client.get(info_url, headers=headers, params={"unique_id": username})

            if info_resp.status_code == 429:
                logger.warning("[L0] rate limit reached")
                return None
            if info_resp.status_code == 401:
                logger.error("[L0] unauthorized - check RAPIDAPI_KEY")
                return None
            if info_resp.status_code != 200:
                logger.warning(f"[L0] info HTTP {info_resp.status_code}")
                return None

            payload = info_resp.json()
            if payload.get("code") not in (0, None):
                logger.warning(f"[L0] info code={payload.get('code')} msg={payload.get('msg')}")
                return None

            data = payload.get("data", {}) or {}
            user = data.get("user", {}) or {}
            stats = data.get("stats", {}) or {}

            info = {
                "id": user.get("id") or user.get("uid"),
                "uniqueId": user.get("uniqueId") or username,
                "nickname": user.get("nickname", ""),
                "avatarThumb": user.get("avatarLarger") or user.get("avatarMedium") or user.get("avatarThumb", ""),
                "signature": user.get("signature", ""),
                "verified": user.get("verified", False),
                "region": (user.get("region") or "").upper(),  # often empty from this endpoint
                "followerCount": _to_int(stats.get("followerCount")),
                "followingCount": _to_int(stats.get("followingCount")),
                "heartCount": _to_int(stats.get("heartCount")),
                "videoCount": _to_int(stats.get("videoCount")),
                "createTime": user.get("createTime", 0),
                "privateAccount": user.get("privateAccount", False),
                "source": "L0_rapidapi",
            }

            # ── /user/posts (30 videos for VPN-aware analysis) ──
            try:
                posts_url = f"https://{rapidapi_host}/user/posts"
                posts_resp = await client.get(
                    posts_url, headers=headers,
                    params={"unique_id": username, "count": str(POSTS_COUNT), "cursor": "0"},
                    timeout=15.0,
                )
                if posts_resp.status_code == 200:
                    posts_payload = posts_resp.json()
                    if posts_payload.get("code") in (0, None):
                        videos = posts_payload.get("data", {}).get("videos", []) or []
                        info["_videos"] = videos
                        logger.info(f"[L0] fetched {len(videos)} videos for @{username}")
                    else:
                        info["_videos"] = []
                else:
                    info["_videos"] = []
            except Exception as e:
                logger.debug(f"[L0] posts fetch skipped: {e}")
                info["_videos"] = []

            logger.info(f"[L0] ✅ SUCCESS for @{username}")
            return info

    except httpx.TimeoutException:
        logger.warning(f"[L0] timeout for @{username}")
        return None
    except Exception as e:
        logger.warning(f"[L0] exception for @{username}: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 🌐 LAYER 1: TikTok Web Direct (fallback)
# ═══════════════════════════════════════════════════════════
async def layer1_tiktok_web(username: str) -> Optional[Dict[str, Any]]:
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            m = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.+?)</script>',
                resp.text, re.DOTALL,
            )
            if m:
                data = json.loads(m.group(1))
                return _parse_universal_data(data, username, source="L1_web")
    except Exception:
        pass
    return None


def _parse_universal_data(data: dict, username: str, source: str) -> Optional[Dict[str, Any]]:
    try:
        scope = data.get("__DEFAULT_SCOPE__", {})
        user_info = scope.get("webapp.user-detail", {}).get("userInfo", {})
        if not user_info:
            return None
        user = user_info.get("user", {}) or {}
        stats = user_info.get("stats", {}) or {}
        return {
            "id": user.get("id"),
            "uniqueId": user.get("uniqueId", username),
            "nickname": user.get("nickname", ""),
            "avatarThumb": user.get("avatarLarger") or user.get("avatarThumb", ""),
            "signature": user.get("signature", ""),
            "verified": user.get("verified", False),
            "region": (user.get("region") or "").upper(),
            "followerCount": _to_int(stats.get("followerCount")),
            "followingCount": _to_int(stats.get("followingCount")),
            "heartCount": _to_int(stats.get("heartCount")),
            "videoCount": _to_int(stats.get("videoCount")),
            "createTime": user.get("createTime", 0),
            "privateAccount": user.get("privateAccount", False),
            "source": source,
            "_videos": [],
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# 🧠 VPN-Aware Verdict (the smart core)
# ═══════════════════════════════════════════════════════════
def compute_verdict_vpn_aware(user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Multi-signal verdict with VPN detection.

    Strategy:
      1. Collect all video regions
      2. If dominant (>80%) region exists, check for MINORITY (10-25%)
         - The minority often = user's TRUE country (forgot VPN)
      3. Cross-check with timezone analysis
      4. If minority + timezone agree → HIGH confidence for minority
      5. Also consider: single video with SA in a sea of GB = strong signal
    """
    videos = user_info.get("_videos", []) or []

    # ── Collect signals ──
    video_regions = [(v.get("region") or "").upper() for v in videos if v.get("region")]
    video_regions = [r for r in video_regions if r in WORLD_COUNTRIES]
    timestamps = []
    for v in videos:
        ts = v.get("create_time") or v.get("createTime")
        if ts:
            try:
                timestamps.append(int(ts))
            except Exception:
                pass

    # ── Signal 1: user.region (from /user/info if present) ──
    signals = []
    user_region = (user_info.get("region") or "").upper().strip()
    if user_region and user_region in WORLD_COUNTRIES:
        signals.append({
            "type": "user_region",
            "iso": user_region,
            "weight": 0.85,
            "reason": f"من ملف المستخدم: {user_region}",
        })

    # ── Signal 2: Video regions analysis (VPN-aware) ──
    region_counter = Counter(video_regions)
    total_videos = len(video_regions)
    vpn_detected = False
    vpn_country = None
    real_country = None

    if total_videos >= 5:
        top_regions = region_counter.most_common()
        majority_iso, majority_count = top_regions[0]
        majority_ratio = majority_count / total_videos

        # Check for minority (potential real country)
        minority_iso = None
        minority_ratio = 0.0
        if len(top_regions) >= 2:
            minority_iso, minority_count = top_regions[1]
            minority_ratio = minority_count / total_videos

        # VPN detection heuristic
        if (majority_ratio >= 0.75 and minority_iso and minority_ratio >= 0.05
                and minority_iso != majority_iso):
            # Likely VPN: dominant = VPN, minority = real
            vpn_detected = True
            vpn_country = majority_iso
            real_country = minority_iso

            # Add minority as HIGH weight (real country)
            signals.append({
                "type": "video_minority_region",
                "iso": minority_iso,
                "weight": 0.95,
                "reason": f"🎯 {minority_count} فيديو من {minority_iso} (VPN مُشتَبَه به: {majority_iso})",
                "sample": total_videos,
            })
            # Add majority as LOW weight (VPN suspected)
            signals.append({
                "type": "video_majority_region_vpn",
                "iso": majority_iso,
                "weight": 0.15,
                "reason": f"⚠️ {majority_count} فيديو من {majority_iso} (يبدو VPN)",
                "sample": total_videos,
            })
        else:
            # Normal case: no VPN suspicion
            signals.append({
                "type": "video_region",
                "iso": majority_iso,
                "weight": 0.75 * majority_ratio,
                "reason": f"{majority_count}/{total_videos} فيديو مُعلَّم {majority_iso}",
                "sample": total_videos,
            })

    # ── Signal 3: Timezone analysis (can't be faked by VPN) ──
    tz_analysis = _analyze_timezone(timestamps)
    if tz_analysis and tz_analysis.get("candidate_countries"):
        candidates = tz_analysis["candidate_countries"]
        primary_candidate = candidates[0]

        # If timezone matches suspected real country → boost it
        if real_country and real_country in candidates:
            signals.append({
                "type": "timezone_confirms_real",
                "iso": real_country,
                "weight": 0.8 * tz_analysis["peak_ratio"],
                "reason": f"⏰ التوقيت يؤكد {real_country} (UTC{tz_analysis['utc_offset']:+d})",
                "candidates": candidates,
            })
        else:
            signals.append({
                "type": "timezone",
                "iso": primary_candidate,
                "weight": 0.5 * tz_analysis["peak_ratio"],
                "reason": f"⏰ UTC{tz_analysis['utc_offset']:+d} (ساعة الذروة {tz_analysis['peak_utc_hour']:02d}:00 UTC)",
                "candidates": candidates,
            })

    # ── No signals? ──
    if not signals:
        return {
            "country_iso": None,
            "country_ar": "غير محدد",
            "country_en": "Unknown",
            "flag": "🏳️",
            "timezone": None,
            "continent": None,
            "confidence": 0,
            "primary_source": "none",
            "signals": [],
            "vpn_detected": False,
        }

    # ── Weighted voting ──
    scores: Dict[str, float] = {}
    for s in signals:
        iso = s["iso"]
        scores[iso] = scores.get(iso, 0) + s["weight"]

    winner_iso = max(scores, key=scores.get)
    winner_score = scores[winner_iso]
    total_score = sum(scores.values())
    confidence = int(round((winner_score / total_score) * 100)) if total_score else 0

    # Get country info
    info = get_country_info(winner_iso) if REGIONS_DB_AVAILABLE else None
    if info:
        ar_name, en_name, flag, tz, continent = info
    else:
        ar_name, en_name, flag, tz, continent = winner_iso, winner_iso, "🏳️", None, None

    primary = max(signals, key=lambda s: s["weight"])

    result = {
        "country_iso": winner_iso,
        "country_ar": ar_name,
        "country_en": en_name,
        "flag": flag,
        "timezone": tz,
        "continent": continent,
        "confidence": confidence,
        "primary_source": primary["type"],
        "primary_reason": primary["reason"],
        "signals": signals,
        "timezone_analysis": tz_analysis,
        "is_arab": is_arab_country(winner_iso) if REGIONS_DB_AVAILABLE else False,
        "is_gcc": is_gcc_country(winner_iso) if REGIONS_DB_AVAILABLE else False,
        "vpn_detected": vpn_detected,
        "vpn_country": vpn_country,
        "real_country": real_country,
        "video_regions_distribution": dict(region_counter),
    }
    return result


def _analyze_timezone(timestamps: List[int]) -> Optional[Dict[str, Any]]:
    """
    Estimate user's timezone from posting hour pattern.
    Assumes peak posting hour = 20:00 local (typical prime time).
    """
    if not timestamps or len(timestamps) < 5:
        return None

    hour_counts = Counter()
    for ts in timestamps:
        try:
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            hour_counts[dt.hour] += 1
        except Exception:
            continue

    if not hour_counts:
        return None

    # Compute prime-window scores for each region
    saudi_prime = sum(hour_counts.get(h, 0) for h in [15, 16, 17, 18, 19, 20, 21])
    british_prime = sum(hour_counts.get(h, 0) for h in [17, 18, 19, 20, 21, 22, 23])
    us_east_prime = sum(hour_counts.get(h, 0) for h in [22, 23, 0, 1, 2, 3, 4])
    total = sum(hour_counts.values())

    # Determine best fit
    scores = {
        "SA_family": saudi_prime,      # UTC+3
        "GB_family": british_prime,    # UTC+0
        "US_east": us_east_prime,      # UTC-5
    }
    best_family = max(scores, key=scores.get)
    best_score = scores[best_family]
    best_ratio = best_score / total if total else 0

    # Peak hour offset calculation
    peak_utc_hour, peak_count = hour_counts.most_common(1)[0]
    ASSUMED_LOCAL_PEAK = 20
    utc_offset = (ASSUMED_LOCAL_PEAK - peak_utc_hour) % 24
    if utc_offset > 12:
        utc_offset -= 24

    # Map to candidate countries
    if best_family == "SA_family":
        candidates = UTC_OFFSET_TO_COUNTRIES.get(3, ["SA"])
    elif best_family == "GB_family":
        candidates = UTC_OFFSET_TO_COUNTRIES.get(0, ["GB"])
    elif best_family == "US_east":
        candidates = UTC_OFFSET_TO_COUNTRIES.get(-5, ["US"])
    else:
        candidates = UTC_OFFSET_TO_COUNTRIES.get(utc_offset, [])

    return {
        "utc_offset": utc_offset,
        "peak_utc_hour": peak_utc_hour,
        "peak_ratio": round(best_ratio, 2),
        "candidate_countries": candidates,
        "sample_size": total,
        "prime_scores": scores,
        "best_family": best_family,
    }


# ═══════════════════════════════════════════════════════════
# 🎯 Main lookup engine
# ═══════════════════════════════════════════════════════════
async def lookup_tiktok(username: str) -> LookupResult:
    username = username.strip().lstrip("@")
    result = LookupResult()
    layers_tried = []
    user_info = None
    start = time.time()

    # v2.3.3: Read env at runtime (not module-level)
    _key, _host, _enabled = _get_rapidapi_config()
    if _enabled:
        layers_tried.append("L0_rapidapi")
        user_info = await layer0_rapidapi(username)
    else:
        logger.warning("[lookup_tiktok] Skipping L0 - no RAPIDAPI_KEY at runtime")

    if not user_info:
        layers_tried.append("L1_web")
        user_info = await layer1_tiktok_web(username)

    if not user_info:
        return LookupResult(
            success=False,
            error="جميع الطبقات فشلت في جلب بيانات المستخدم من TikTok",
            username=username,
            layers_tried=layers_tried,
            elapsed=round(time.time() - start, 2),
        )

    videos = user_info.get("_videos", [])
    verdict = compute_verdict_vpn_aware(user_info)

    result.update({
        "success": True,
        "username": user_info.get("uniqueId", username),
        "user_id": user_info.get("id"),
        "nickname": user_info.get("nickname"),
        "avatar": user_info.get("avatarThumb"),
        "signature": user_info.get("signature"),
        "verified": user_info.get("verified", False),
        "private": user_info.get("privateAccount", False),
        "stats": {
            "followers": user_info.get("followerCount", 0),
            "following": user_info.get("followingCount", 0),
            "hearts": user_info.get("heartCount", 0),
            "videos": user_info.get("videoCount", 0),
        },
        "geo": verdict,
        "layers_tried": layers_tried,
        "primary_source": user_info.get("source"),
        "videos_analyzed": len(videos),
        "elapsed": round(time.time() - start, 2),
        "regions_db_version": REGIONS_STATS.get("version", "unknown") if REGIONS_DB_AVAILABLE else "MISSING",
        "rapidapi_enabled": _enabled,
    })
    return result


# ═══════════════════════════════════════════════════════════
# 🎨 Markdown formatter (VPN-aware display)
# ═══════════════════════════════════════════════════════════
def _md_escape(text: str) -> str:
    """Escape Telegram Markdown special chars: _, *, `, [ to prevent parse errors.
    
    Critical fix for v2.3.2: usernames like 'citizen_lawyerr' contain _ which
    Telegram interprets as italic. Without escaping, Telegram returns
    'Can't parse entities' error.
    """
    if not text:
        return ""
    s = str(text)
    for ch in ('_', '*', '`', '['):
        s = s.replace(ch, '\\' + ch)
    return s


def _format_markdown_for_bot(result: LookupResult) -> str:
    if not result.get("success"):
        err = result.get("error", "فشل جلب البيانات")
        layers = result.get("layers_tried", [])
        return (
            f"❌ *فشل البحث*\n\n{_md_escape(err)}\n"
            f"📡 الطبقات: `{', '.join(layers) if layers else 'لا شيء'}`\n\n"
            f"💡 تأكد من اسم المستخدم وحاول مرة أخرى."
        )

    stats = result.get("stats", {}) or {}
    geo = result.get("geo", {}) or {}

    nickname = _md_escape(result.get("nickname", "") or "")
    username = _md_escape(result.get("username", "") or "")
    verified_badge = " ✅" if result.get("verified") else ""
    private_badge = " 🔒" if result.get("private") else ""

    followers = stats.get("followers", 0) or 0
    following = stats.get("following", 0) or 0
    hearts = stats.get("hearts", 0) or 0
    videos = stats.get("videos", 0) or 0

    flag = geo.get("flag", "🏳️") or "🏳️"
    country_ar = _md_escape(geo.get("country_ar", "غير محدد") or "غير محدد")
    confidence = geo.get("confidence", 0) or 0
    tz = geo.get("timezone") or ""
    continent = geo.get("continent") or ""
    vpn_detected = geo.get("vpn_detected", False)
    vpn_country = geo.get("vpn_country")

    src = geo.get("primary_source") or ""
    src_labels = {
        "video_minority_region": "🎯 كشف الأصل رغم VPN",
        "video_majority_region_vpn": "⚠️ region سطحي (VPN)",
        "video_region": "📹 من metadata الفيديوهات",
        "user_region": "👤 من ملف المستخدم (TikTok)",
        "timezone": "⏰ من تحليل توقيت النشر",
        "timezone_confirms_real": "⏰ التوقيت يؤكد الأصل",
        "none": "❌ لا توجد إشارات كافية",
    }
    src_display = src_labels.get(src, "") if src else ""

    continent_ar = {
        "Asia": "آسيا",
        "Africa": "إفريقيا",
        "Europe": "أوروبا",
        "Americas": "الأمريكتان",
        "Oceania": "أوقيانوسيا",
        "Antarctica": "أنتاركتيكا",
    }.get(continent, continent)

    lines = []
    lines.append(f"👤 *{nickname}*{verified_badge}{private_badge}")
    lines.append(f"🔗 @{username}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("📊 *الإحصائيات*")
    lines.append(f"👥 المتابعون: `{followers:,}`")
    lines.append(f"➕ يتابع: `{following:,}`")
    lines.append(f"📹 الفيديوهات: `{videos:,}`")
    lines.append(f"❤️ الإعجابات: `{hearts:,}`")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🌍 *التحليل الجغرافي*")
    lines.append(f"🎯 الدولة: {flag} *{country_ar}*")

    if confidence > 0:
        conf_bar = "🟢" if confidence >= 70 else ("🟡" if confidence >= 40 else "🔴")
        lines.append(f"📊 مستوى الثقة: {conf_bar} `{confidence}%`")

    if src_display:
        lines.append(f"🔍 المصدر: {src_display}")

    reason = geo.get("primary_reason")
    if reason:
        lines.append(f"ℹ️ _{_md_escape(reason)}_")

    # 🚨 VPN detection alert
    if vpn_detected and vpn_country:
        vpn_info = get_country_info(vpn_country) if REGIONS_DB_AVAILABLE else None
        vpn_flag = vpn_info[2] if vpn_info else "🏳️"
        vpn_name = _md_escape(vpn_info[0] if vpn_info else vpn_country)
        lines.append("")
        lines.append(f"⚠️ *تحذير VPN:*")
        lines.append(f"   يبدو أن المستخدم يستخدم VPN من {vpn_flag} *{vpn_name}*")
        lines.append(f"   _تم اكتشاف الأصل الحقيقي عبر تحليل متعدد الإشارات_")

    # Distribution
    dist = geo.get("video_regions_distribution", {}) or {}
    if dist:
        dist_parts = []
        for iso, count in sorted(dist.items(), key=lambda x: -x[1])[:4]:
            f = get_flag(iso) if REGIONS_DB_AVAILABLE else "🏳️"
            dist_parts.append(f"{f}`{iso}:{count}`")
        if dist_parts:
            lines.append(f"📊 توزيع الفيديوهات: {' '.join(dist_parts)}")

    if tz:
        lines.append(f"🕐 التوقيت المحلي: `{tz}`")

    if continent_ar:
        lines.append(f"🌐 القارة: {continent_ar}")

    if geo.get("is_arab"):
        badge = "🕌 دولة عربية"
        if geo.get("is_gcc"):
            badge += " _(خليجية 🕋)_"
        lines.append(badge)

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🏆 *مدعوم بـ RapidAPI + VPN-Aware*")
    lines.append("✅ لا اعتماد على الاسم/اللهجة")

    layers = result.get("layers_tried", [])
    if layers:
        lines.append(f"📡 الطبقات: `{', '.join(layers)}`")

    analyzed = result.get("videos_analyzed", 0) or 0
    if analyzed:
        lines.append(f"📹 المُحلَّل: `{analyzed} فيديو`")

    elapsed = result.get("elapsed", 0) or 0
    if elapsed:
        lines.append(f"⚡ الاستجابة: `{elapsed}s`")

    lines.append("🗺️ قاعدة: `v2.3.1` (249 دولة)")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# 🔄 Backward-Compat API for bot.py v2.1.8.9
# ═══════════════════════════════════════════════════════════
def clean_username(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip().lstrip("@")
    if "tiktok.com" in s:
        s = s.split("tiktok.com/")[-1]
    s = s.lstrip("@").split("/")[0].split("?")[0].split("#")[0]
    return s.strip()


async def lookup_tiktok_user(username: str) -> str:
    cleaned = clean_username(username)
    try:
        result = await lookup_tiktok(cleaned)
        return _format_markdown_for_bot(result)
    except Exception as e:
        logger.error(f"[lookup_tiktok_user] {cleaned}: {e}", exc_info=True)
        safe_err = _md_escape(str(e)[:200])
        safe_user = _md_escape(cleaned)
        return (
            f"❌ *فشل البحث*\n\n"
            f"حدث خطأ داخلي أثناء جلب بيانات @{safe_user}\n"
            f"`{safe_err}`\n\n"
            f"💡 حاول مرة أخرى بعد قليل."
        )


async def lookup_tiktok_user_dict(username: str) -> Dict[str, Any]:
    cleaned = clean_username(username)
    result = await lookup_tiktok(cleaned)
    if not result.get("success"):
        return {"success": False, "error": result.get("error"), "username": cleaned}
    stats = result.get("stats", {})
    geo = result.get("geo", {})
    return {
        "success": True,
        "username": result.get("username", cleaned),
        "nickname": result.get("nickname", ""),
        "verified": result.get("verified", False),
        "followers": stats.get("followers", 0),
        "following": stats.get("following", 0),
        "hearts": stats.get("hearts", 0),
        "videos": stats.get("videos", 0),
        "country": geo.get("country_ar", "غير محدد"),
        "country_iso": geo.get("country_iso"),
        "flag": geo.get("flag", "🏳️"),
        "timezone": geo.get("timezone"),
        "continent": geo.get("continent"),
        "confidence": geo.get("confidence", 0),
        "is_arab": geo.get("is_arab", False),
        "is_gcc": geo.get("is_gcc", False),
        "vpn_detected": geo.get("vpn_detected", False),
        "vpn_country": geo.get("vpn_country"),
        "formatted_markdown": _format_markdown_for_bot(result),
        "_full_result": dict(result),
    }


# Aliases
lookup = lookup_tiktok_user
get_tiktok_info = lookup_tiktok_user
tiktok_lookup = lookup_tiktok_user


# ═══════════════════════════════════════════════════════════
# 🔧 Helpers
# ═══════════════════════════════════════════════════════════
def _to_int(v) -> int:
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


# ═══════════════════════════════════════════════════════════
# 🧪 CLI test
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    username = sys.argv[1] if len(sys.argv) > 1 else "citizen_lawyerr"
    print(f"\n🔍 Testing: @{username}")
    _, _, _rapid_enabled = _get_rapidapi_config()
    print(f"🏆 RapidAPI: {_rapid_enabled}\n")

    async def _main():
        s = await lookup_tiktok_user(username)
        print(s)

    asyncio.run(_main())
