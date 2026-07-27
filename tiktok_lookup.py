"""
╔══════════════════════════════════════════════════════════════════╗
║  BSR-V240-CTO-NUCLEAR-FIX-FULL-STACK-AHMAD-20260726              ║
║  tiktok_lookup.py v2.4.0 - NUCLEAR FIX (HTML + Runtime Env)      ║
║  Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)             ║
╚══════════════════════════════════════════════════════════════════╝

🏆 v2.4.0 NUCLEAR FIX:
  1. Runtime env lookup (no module-level RAPIDAPI_KEY capture)
  2. HTML output (parse_mode="HTML" - safer than Markdown)
  3. VPN-aware detection (minority region as REAL country)
  4. 30 videos analysis + timezone cross-check
  5. Defensive error handling everywhere

Public API (backward compatible):
  lookup_tiktok_user(username) -> str  (HTML for Telegram)
  clean_username(raw) -> str
  lookup_tiktok_user_dict(username) -> dict
"""

import asyncio
import html
import json
import logging
import os
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
    REGIONS_STATS = {"version": "MISSING"}

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# 🔧 Runtime env lookup (v2.4.0 KEY FIX)
# ═══════════════════════════════════════════════════════════
def _get_rapidapi_config() -> Tuple[str, str, bool]:
    """Read RAPIDAPI credentials at CALL time (not import time).

    v2.4.0: Also loads .env file as fallback for both local dev
    and edge cases where Railway env injection is delayed.
    """
    # ═══════════════════════════════════════════════════════════
    # 🚨 HARDCODED FALLBACK v2.4.2 (BSR-V242-CTO-HARDCODED-AHMAD)
    # Railway env-vars take PRECEDENCE. Fallback ensures bot works.
    # ⚠️ SECURITY: Rotate this key after successful deployment.
    # ═══════════════════════════════════════════════════════════
    _HARDCODED_KEY = "f7974f4f47msh1b8ab00838958e6p16d7c6jsn25b0a2e8a564"
    _HARDCODED_HOST = "tiktok-scraper7.p.rapidapi.com"

    key = os.getenv("RAPIDAPI_KEY", "").strip() or _HARDCODED_KEY
    host = os.getenv("RAPIDAPI_HOST", "").strip() or _HARDCODED_HOST

    if not key:
        try:
            from dotenv import load_dotenv
            load_dotenv(override=False)
            key = os.getenv("RAPIDAPI_KEY", "").strip()
            host = os.getenv("RAPIDAPI_HOST", host).strip()
        except ImportError:
            pass

    return key, host, bool(key)


# Import-time snapshot (informational only)
_k, _h, _e = _get_rapidapi_config()
if _e:
    logger.info(f"[L0] ✅ RapidAPI available at import: {_h}")
else:
    logger.warning("[L0] ⚠️ RAPIDAPI_KEY not set at import (will retry at runtime)")

POSTS_COUNT = 30
TIMEOUT = httpx.Timeout(20.0, connect=10.0)

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
}


class LookupResult(dict):
    def __getattr__(self, key):
        return self.get(key)


# ═══════════════════════════════════════════════════════════
# 🏆 LAYER 0: RapidAPI (with runtime env lookup)
# ═══════════════════════════════════════════════════════════
async def layer0_rapidapi(username: str) -> Optional[Dict[str, Any]]:
    """RapidAPI primary layer - reads env at CALL time."""
    key, host, enabled = _get_rapidapi_config()
    if not enabled:
        logger.warning(f"[L0] RAPIDAPI_KEY not available for @{username}")
        return None

    logger.info(f"[L0] 🚀 Attempting RapidAPI for @{username}")
    headers = {"x-rapidapi-key": key, "x-rapidapi-host": host}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # /user/info
            info_url = f"https://{host}/user/info"
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
                logger.warning(f"[L0] code={payload.get('code')} msg={payload.get('msg')}")
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
                "region": (user.get("region") or "").upper(),
                "followerCount": _to_int(stats.get("followerCount")),
                "followingCount": _to_int(stats.get("followingCount")),
                "heartCount": _to_int(stats.get("heartCount")),
                "videoCount": _to_int(stats.get("videoCount")),
                "createTime": user.get("createTime", 0),
                "privateAccount": user.get("privateAccount", False),
                "source": "L0_rapidapi",
            }

            # /user/posts (30 videos for VPN-aware analysis)
            try:
                posts_url = f"https://{host}/user/posts"
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

    except Exception as e:
        logger.warning(f"[L0] exception for @{username}: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 🌐 LAYER 1: TikTok Web Direct (fallback)
# ═══════════════════════════════════════════════════════════
async def layer1_tiktok_web(username: str) -> Optional[Dict[str, Any]]:
    """Fallback: Direct TikTok web scraping."""
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
                return _parse_universal_data(data, username)
    except Exception as e:
        logger.debug(f"[L1] exception: {e}")
    return None


def _parse_universal_data(data: dict, username: str) -> Optional[Dict[str, Any]]:
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
            "source": "L1_web",
            "_videos": [],
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# 🧠 VPN-Aware Verdict
# ═══════════════════════════════════════════════════════════
def compute_verdict_vpn_aware(user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Multi-signal verdict with VPN detection."""
    videos = user_info.get("_videos", []) or []

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

    signals = []
    vpn_detected = False
    vpn_country = None
    real_country = None

    # Signal 1: user.region
    user_region = (user_info.get("region") or "").upper().strip()
    if user_region and user_region in WORLD_COUNTRIES:
        signals.append({
            "type": "user_region",
            "iso": user_region,
            "weight": 0.85,
            "reason": f"من ملف المستخدم: {user_region}",
        })

    # Signal 2: Video regions analysis (VPN-aware)
    region_counter = Counter(video_regions)
    total = len(video_regions)

    if total >= 5:
        # 🚀 v2.5.2 - Arab-preference VPN detection (matches Streamlit v2.5.1)
        ARAB_ISOS_V252 = {'SA','AE','KW','QA','BH','OM','YE','IQ','SY','LB','JO','PS',
                          'EG','SD','LY','TN','DZ','MA','MR','SO','DJ','KM'}

        top = region_counter.most_common()
        majority_iso, majority_count = top[0]
        majority_ratio = majority_count / total

        # 🎯 Step 1: Look for ANY Arab country in the distribution
        arab_in_dist = [(iso, cnt) for iso, cnt in region_counter.items() if iso in ARAB_ISOS_V252]

        if arab_in_dist:
            # Arab country present — prefer it as REAL origin
            arab_in_dist.sort(key=lambda x: -x[1])  # sort by count desc
            arab_iso, arab_count = arab_in_dist[0]
            arab_total = sum(cnt for _, cnt in arab_in_dist)

            # Check if non-Arab country has more videos (= VPN suspected)
            non_arab_top = [(iso, cnt) for iso, cnt in region_counter.items() if iso not in ARAB_ISOS_V252]
            non_arab_top.sort(key=lambda x: -x[1])

            if non_arab_top and non_arab_top[0][1] > arab_total:
                # VPN detected: real=Arab, VPN=non-Arab majority
                vpn_detected = True
                vpn_country = non_arab_top[0][0]
                real_country = arab_iso

                signals.append({
                    "type": "video_minority_region",
                    "iso": arab_iso,
                    "weight": 0.95,
                    "reason": f"🎯 {arab_count} فيديو من {arab_iso} (VPN مُشتَبَه به: {vpn_country})",
                    "sample": total,
                })
                signals.append({
                    "type": "video_majority_region_vpn",
                    "iso": vpn_country,
                    "weight": 0.15,
                    "reason": f"⚠️ {non_arab_top[0][1]} فيديو من {vpn_country} (يبدو VPN)",
                    "sample": total,
                })
            else:
                # No VPN — Arab country dominates naturally
                signals.append({
                    "type": "video_region",
                    "iso": arab_iso,
                    "weight": 0.75 * (arab_total / total),
                    "reason": f"{arab_total}/{total} فيديو من دولة عربية ({arab_iso})",
                    "sample": total,
                })
        else:
            # No Arab country — use original logic (75% threshold)
            minority_iso = None
            minority_ratio = 0.0
            if len(top) >= 2:
                minority_iso, minority_count = top[1]
                minority_ratio = minority_count / total

            if (majority_ratio >= 0.75 and minority_iso and minority_ratio >= 0.05
                    and minority_iso != majority_iso):
                # Classic VPN detection (non-Arab)
                vpn_detected = True
                vpn_country = majority_iso
                real_country = minority_iso

                signals.append({
                    "type": "video_minority_region",
                    "iso": minority_iso,
                    "weight": 0.95,
                    "reason": f"🎯 {minority_count} فيديو من {minority_iso} (VPN مُشتَبَه به: {majority_iso})",
                    "sample": total,
                })
                signals.append({
                    "type": "video_majority_region_vpn",
                    "iso": majority_iso,
                    "weight": 0.15,
                    "reason": f"⚠️ {majority_count} فيديو من {majority_iso} (يبدو VPN)",
                    "sample": total,
                })
            else:
                signals.append({
                    "type": "video_region",
                    "iso": majority_iso,
                    "weight": 0.75 * majority_ratio,
                    "reason": f"{majority_count}/{total} فيديو مُعلَّم {majority_iso}",
                    "sample": total,
                })

    # Signal 3: Timezone
    tz_analysis = _analyze_timezone(timestamps)
    if tz_analysis and tz_analysis.get("candidate_countries"):
        candidates = tz_analysis["candidate_countries"]
        primary_candidate = candidates[0]

        if real_country and real_country in candidates:
            signals.append({
                "type": "timezone_confirms_real",
                "iso": real_country,
                "weight": 0.8 * tz_analysis["peak_ratio"],
                "reason": f"⏰ التوقيت يؤكد {real_country}",
                "candidates": candidates,
            })
        else:
            signals.append({
                "type": "timezone",
                "iso": primary_candidate,
                "weight": 0.5 * tz_analysis["peak_ratio"],
                "reason": f"⏰ UTC{tz_analysis['utc_offset']:+d}",
                "candidates": candidates,
            })

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

    # Weighted voting
    scores: Dict[str, float] = {}
    for s in signals:
        iso = s["iso"]
        scores[iso] = scores.get(iso, 0) + s["weight"]

    winner_iso = max(scores, key=scores.get)
    winner_score = scores[winner_iso]
    total_score = sum(scores.values())
    confidence = int(round((winner_score / total_score) * 100)) if total_score else 0

    info = get_country_info(winner_iso) if REGIONS_DB_AVAILABLE else None
    if info:
        ar_name, en_name, flag, tz, continent = info
    else:
        ar_name, en_name, flag, tz, continent = winner_iso, winner_iso, "🏳️", None, None

    primary = max(signals, key=lambda s: s["weight"])

    return {
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


def _analyze_timezone(timestamps: List[int]) -> Optional[Dict[str, Any]]:
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

    saudi_prime = sum(hour_counts.get(h, 0) for h in [15, 16, 17, 18, 19, 20, 21])
    british_prime = sum(hour_counts.get(h, 0) for h in [17, 18, 19, 20, 21, 22, 23])
    us_east_prime = sum(hour_counts.get(h, 0) for h in [22, 23, 0, 1, 2, 3, 4])
    total = sum(hour_counts.values())

    scores = {
        "SA_family": saudi_prime,
        "GB_family": british_prime,
        "US_east": us_east_prime,
    }
    best_family = max(scores, key=scores.get)
    best_ratio = scores[best_family] / total if total else 0

    peak_utc_hour, _ = hour_counts.most_common(1)[0]
    utc_offset = (20 - peak_utc_hour) % 24
    if utc_offset > 12:
        utc_offset -= 24

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
    }


# ═══════════════════════════════════════════════════════════
# 🎯 Main engine
# ═══════════════════════════════════════════════════════════
async def lookup_tiktok(username: str) -> LookupResult:
    username = username.strip().lstrip("@")
    result = LookupResult()
    layers_tried = []
    user_info = None
    start = time.time()

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
            error="جميع الطبقات فشلت في جلب بيانات المستخدم",
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
        "regions_db_version": REGIONS_STATS.get("version", "unknown"),
        "rapidapi_enabled": _enabled,
    })
    return result


# ═══════════════════════════════════════════════════════════
# 🎨 HTML formatter (v2.4.0 - safer than Markdown)
# ═══════════════════════════════════════════════════════════
def _html_escape(text: str) -> str:
    """Escape HTML special chars for Telegram parse_mode='HTML'."""
    if text is None:
        return ""
    return html.escape(str(text), quote=False)


def _format_html_for_bot(result: LookupResult) -> str:
    """Render result as HTML text (Telegram parse_mode='HTML')."""
    if not result.get("success"):
        err = _html_escape(result.get("error", "فشل جلب البيانات"))
        layers = result.get("layers_tried", [])
        return (
            f"❌ <b>فشل البحث</b>\n\n"
            f"{err}\n"
            f"📡 الطبقات: <code>{', '.join(layers) if layers else 'لا شيء'}</code>\n\n"
            f"💡 تأكد من اسم المستخدم وحاول مرة أخرى."
        )

    stats = result.get("stats", {}) or {}
    geo = result.get("geo", {}) or {}

    nickname = _html_escape(result.get("nickname", "") or "")
    username = _html_escape(result.get("username", "") or "")
    verified_badge = " ✅" if result.get("verified") else ""
    private_badge = " 🔒" if result.get("private") else ""

    followers = stats.get("followers", 0) or 0
    following = stats.get("following", 0) or 0
    hearts = stats.get("hearts", 0) or 0
    videos = stats.get("videos", 0) or 0

    flag = geo.get("flag", "🏳️") or "🏳️"
    country_ar = _html_escape(geo.get("country_ar", "غير محدد") or "غير محدد")
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
    src_display = _html_escape(src_labels.get(src, "") if src else "")

    continent_ar = {
        "Asia": "آسيا",
        "Africa": "إفريقيا",
        "Europe": "أوروبا",
        "Americas": "الأمريكتان",
        "Oceania": "أوقيانوسيا",
        "Antarctica": "أنتاركتيكا",
    }.get(continent, continent)

    lines = []
    lines.append(f"👤 <b>{nickname}</b>{verified_badge}{private_badge}")
    lines.append(f"🔗 @{username}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("📊 <b>الإحصائيات</b>")
    lines.append(f"👥 المتابعون: <code>{followers:,}</code>")
    lines.append(f"➕ يتابع: <code>{following:,}</code>")
    lines.append(f"📹 الفيديوهات: <code>{videos:,}</code>")
    lines.append(f"❤️ الإعجابات: <code>{hearts:,}</code>")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🌍 <b>التحليل الجغرافي</b>")
    lines.append(f"🎯 الدولة: {flag} <b>{country_ar}</b>")

    if confidence > 0:
        conf_bar = "🟢" if confidence >= 70 else ("🟡" if confidence >= 40 else "🔴")
        lines.append(f"📊 مستوى الثقة: {conf_bar} <code>{confidence}%</code>")

    if src_display:
        lines.append(f"🔍 المصدر: {src_display}")

    reason = geo.get("primary_reason")
    if reason:
        lines.append(f"ℹ️ <i>{_html_escape(reason)}</i>")

    if vpn_detected and vpn_country:
        vpn_info = get_country_info(vpn_country) if REGIONS_DB_AVAILABLE else None
        vpn_flag = vpn_info[2] if vpn_info else "🏳️"
        vpn_name = _html_escape(vpn_info[0] if vpn_info else vpn_country)
        lines.append("")
        lines.append(f"⚠️ <b>تحذير VPN:</b>")
        lines.append(f"   يبدو أن المستخدم يستخدم VPN من {vpn_flag} <b>{vpn_name}</b>")
        lines.append(f"   <i>تم اكتشاف الأصل الحقيقي عبر تحليل متعدد الإشارات</i>")

    dist = geo.get("video_regions_distribution", {}) or {}
    if dist:
        parts = []
        for iso, count in sorted(dist.items(), key=lambda x: -x[1])[:4]:
            f = get_flag(iso) if REGIONS_DB_AVAILABLE else "🏳️"
            parts.append(f"{f}<code>{_html_escape(iso)}:{count}</code>")
        if parts:
            lines.append(f"📊 توزيع الفيديوهات: {' '.join(parts)}")

    if tz:
        lines.append(f"🕐 التوقيت المحلي: <code>{_html_escape(tz)}</code>")

    if continent_ar:
        lines.append(f"🌐 القارة: {_html_escape(continent_ar)}")

    if geo.get("is_arab"):
        badge = "🕌 دولة عربية"
        if geo.get("is_gcc"):
            badge += " <i>(خليجية 🕋)</i>"
        lines.append(badge)

    # 🎨 v2.4.8: Footer section removed for cleaner output
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# 🔄 Public API (backward compat with bot.py)
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
    """Legacy wrapper - returns HTML string for Telegram."""
    cleaned = clean_username(username)
    try:
        result = await lookup_tiktok(cleaned)
        return _format_html_for_bot(result)
    except Exception as e:
        logger.error(f"[lookup_tiktok_user] {cleaned}: {e}", exc_info=True)
        safe_err = _html_escape(str(e)[:200])
        safe_user = _html_escape(cleaned)
        return (
            f"❌ <b>فشل البحث</b>\n\n"
            f"حدث خطأ داخلي أثناء جلب بيانات @{safe_user}\n"
            f"<code>{safe_err}</code>\n\n"
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
        "formatted_html": _format_html_for_bot(result),
        "_full_result": dict(result),
    }


# Aliases
lookup = lookup_tiktok_user
get_tiktok_info = lookup_tiktok_user
tiktok_lookup = lookup_tiktok_user


def _to_int(v) -> int:
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    username = sys.argv[1] if len(sys.argv) > 1 else "citizen_lawyerr"
    _, _, _en = _get_rapidapi_config()
    print(f"\n🔍 Testing: @{username}")
    print(f"🏆 RapidAPI: {_en}\n")

    async def _main():
        s = await lookup_tiktok_user(username)
        print(s)

    asyncio.run(_main())
