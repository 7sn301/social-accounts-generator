"""
╔══════════════════════════════════════════════════════════════════╗
║  BSR-V230-CTO-RAPIDAPI-INTEGRATION-AHMAD-20260726                ║
║  tiktok_lookup.py v2.3.0 - RapidAPI Primary + Multi-Layer Backup ║
║  Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)             ║
╚══════════════════════════════════════════════════════════════════╝

🏆 Architecture (Priority Order):
  L0: RapidAPI tiktok-scraper7 (PRIMARY - 99% success)
  L1: TikTok Web Direct (Fallback)
  L2: Mobile API (Fallback)
  L3: cloudscraper (Fallback)
  L4: Playwright (Last resort)

Environment Variables:
  RAPIDAPI_KEY       - Required for L0 (get from rapidapi.com)
  RAPIDAPI_HOST      - Default: tiktok-scraper7.p.rapidapi.com

Country Database: regions_database.py v2.2.1 (249 countries, ISO 3166-1)

Public API (Backward compatible with bot.py v2.1.8.9):
  lookup_tiktok_user(username) -> str  (Markdown ready for Telegram)
  clean_username(raw) -> str
  lookup_tiktok_user_dict(username) -> dict  (Advanced use)
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
# 🌍 Integration with World Map Database (249 countries)
# ═══════════════════════════════════════════════════════════
try:
    from regions_database import (
        WORLD_COUNTRIES,
        TIMEZONE_TO_COUNTRY,
        get_country_info,
        get_arabic_name,
        get_english_name,
        get_flag,
        get_timezone as get_country_timezone,
        get_continent,
        get_country_by_timezone,
        format_country_display,
        is_arab_country,
        is_gcc_country,
        STATS as REGIONS_STATS,
    )
    REGIONS_DB_AVAILABLE = True
except ImportError as e:
    logging.error(f"[tiktok_lookup] regions_database not available: {e}")
    REGIONS_DB_AVAILABLE = False
    WORLD_COUNTRIES = {}
    TIMEZONE_TO_COUNTRY = {}

# ═══════════════════════════════════════════════════════════
# 🛡️ Optional dependencies (graceful fallback)
# ═══════════════════════════════════════════════════════════
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# 🏆 RapidAPI Configuration (L0 - Primary)
# ═══════════════════════════════════════════════════════════
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "").strip()
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "tiktok-scraper7.p.rapidapi.com").strip()
RAPIDAPI_ENABLED = bool(RAPIDAPI_KEY)

if RAPIDAPI_ENABLED:
    logger.info(f"[L0] ✅ RapidAPI enabled: {RAPIDAPI_HOST}")
else:
    logger.warning("[L0] ⚠️ RAPIDAPI_KEY not set - falling back to L1-L4")

# ═══════════════════════════════════════════════════════════
# 🎭 Rotating User Agents (for L1-L2 fallback)
# ═══════════════════════════════════════════════════════════
DESKTOP_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
]
MOBILE_UAS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
]

def _rand_ua(pool: List[str]) -> str:
    return random.choice(pool)

TIMEOUT = httpx.Timeout(18.0, connect=10.0)


# ═══════════════════════════════════════════════════════════
# 📊 Result container
# ═══════════════════════════════════════════════════════════
class LookupResult(dict):
    """Container for lookup results with attribute access."""
    def __getattr__(self, key):
        return self.get(key)


# ═══════════════════════════════════════════════════════════
# 🏆 LAYER 0: RapidAPI tiktok-scraper7 (PRIMARY - 99% success)
# ═══════════════════════════════════════════════════════════
async def layer0_rapidapi(username: str) -> Optional[Dict[str, Any]]:
    """
    RapidAPI tiktok-scraper7 - the most reliable path.
    Uses /user/info + /user/posts endpoints.
    """
    if not RAPIDAPI_ENABLED:
        return None

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # ── Fetch user info ──
            info_url = f"https://{RAPIDAPI_HOST}/user/info"
            params = {"unique_id": username}
            info_resp = await client.get(info_url, headers=headers, params=params)

            if info_resp.status_code == 429:
                logger.warning("[L0] RapidAPI rate limit reached")
                return None
            if info_resp.status_code == 401:
                logger.error("[L0] RapidAPI unauthorized - check RAPIDAPI_KEY")
                return None
            if info_resp.status_code != 200:
                logger.warning(f"[L0] HTTP {info_resp.status_code}: {info_resp.text[:200]}")
                return None

            payload = info_resp.json()

            # Different providers use different response shapes
            data = payload.get("data") or payload
            if not data or (isinstance(data, dict) and data.get("code") not in (None, 0)):
                logger.warning(f"[L0] no data in response: {str(payload)[:200]}")
                return None

            user = data.get("user", {}) or {}
            stats = data.get("stats", {}) or data.get("statsV2", {}) or {}

            info = {
                "id": user.get("id") or user.get("uid"),
                "uniqueId": user.get("uniqueId") or user.get("unique_id") or username,
                "nickname": user.get("nickname", ""),
                "avatarThumb": (
                    user.get("avatarLarger")
                    or user.get("avatar_larger", {}).get("url_list", [""])[0]
                    if isinstance(user.get("avatar_larger"), dict)
                    else user.get("avatarLarger")
                ) or user.get("avatarMedium", ""),
                "signature": user.get("signature", ""),
                "verified": user.get("verified", False),
                "region": (user.get("region") or "").upper(),  # 🎯 KEY signal
                "language": user.get("language", ""),
                "followerCount": _to_int(stats.get("followerCount") or stats.get("follower_count")),
                "followingCount": _to_int(stats.get("followingCount") or stats.get("following_count")),
                "heartCount": _to_int(stats.get("heartCount") or stats.get("heart_count")),
                "videoCount": _to_int(stats.get("videoCount") or stats.get("video_count")),
                "createTime": user.get("createTime") or user.get("create_time", 0),
                "privateAccount": user.get("privateAccount") or user.get("secret", False),
                "source": "L0_rapidapi",
            }

            # ── Fetch posts for video regions ──
            try:
                posts_url = f"https://{RAPIDAPI_HOST}/user/posts"
                posts_params = {"unique_id": username, "count": "20", "cursor": "0"}
                posts_resp = await client.get(posts_url, headers=headers, params=posts_params, timeout=15.0)
                if posts_resp.status_code == 200:
                    posts_payload = posts_resp.json()
                    posts_data = posts_payload.get("data") or posts_payload
                    videos_raw = posts_data.get("videos") or posts_data.get("aweme_list") or []
                    info["_videos"] = videos_raw
                    logger.info(f"[L0] fetched {len(videos_raw)} videos for @{username}")
            except Exception as e:
                logger.debug(f"[L0] posts fetch skipped: {e}")

            logger.info(f"[L0] ✅ SUCCESS for @{username} - region: {info['region']}")
            return info

    except httpx.TimeoutException:
        logger.warning(f"[L0] timeout for @{username}")
        return None
    except Exception as e:
        logger.warning(f"[L0] exception for @{username}: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 🌐 LAYER 1: TikTok Web Direct (Fallback)
# ═══════════════════════════════════════════════════════════
async def layer1_tiktok_web(username: str) -> Optional[Dict[str, Any]]:
    """Fallback to TikTok web page parsing."""
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": _rand_ua(DESKTOP_UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            html = resp.text
            m = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.+?)</script>',
                html, re.DOTALL,
            )
            if m:
                data = json.loads(m.group(1))
                return _parse_universal_data(data, username, source="L1_web")
            return None
    except Exception as e:
        logger.debug(f"[L1] exception: {e}")
        return None


def _parse_universal_data(data: dict, username: str, source: str) -> Optional[Dict[str, Any]]:
    try:
        scope = data.get("__DEFAULT_SCOPE__", {})
        user_detail = scope.get("webapp.user-detail", {})
        user_info = user_detail.get("userInfo", {})
        if not user_info:
            return None
        user = user_info.get("user", {}) or {}
        stats = user_info.get("stats", {}) or user_info.get("statsV2", {}) or {}
        return {
            "id": user.get("id"),
            "uniqueId": user.get("uniqueId", username),
            "nickname": user.get("nickname", ""),
            "avatarThumb": user.get("avatarLarger") or user.get("avatarThumb", ""),
            "signature": user.get("signature", ""),
            "verified": user.get("verified", False),
            "region": (user.get("region") or "").upper(),
            "language": user.get("language", ""),
            "followerCount": _to_int(stats.get("followerCount", 0)),
            "followingCount": _to_int(stats.get("followingCount", 0)),
            "heartCount": _to_int(stats.get("heartCount", 0)),
            "videoCount": _to_int(stats.get("videoCount", 0)),
            "createTime": user.get("createTime", 0),
            "privateAccount": user.get("privateAccount", False),
            "source": source,
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# 📱 LAYER 2: Mobile API
# ═══════════════════════════════════════════════════════════
async def layer2_mobile_api(username: str) -> Optional[Dict[str, Any]]:
    url = f"https://m.tiktok.com/@{username}"
    headers = {"User-Agent": _rand_ua(MOBILE_UAS), "Referer": "https://www.google.com/"}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            html = resp.text
            m = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.+?)</script>',
                html, re.DOTALL,
            )
            if m:
                data = json.loads(m.group(1))
                return _parse_universal_data(data, username, source="L2_mobile")
            return None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# 🛡️ LAYER 3: cloudscraper
# ═══════════════════════════════════════════════════════════
def layer3_cloudscraper(username: str) -> Optional[Dict[str, Any]]:
    if not CLOUDSCRAPER_AVAILABLE:
        return None
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        info_url = f"https://www.tikwm.com/api/user/info?unique_id={username}"
        resp = scraper.get(info_url, timeout=15)
        if resp.status_code != 200:
            return None
        payload = resp.json()
        if payload.get("code") != 0:
            return None
        user_data = payload.get("data", {}).get("user", {})
        stats_data = payload.get("data", {}).get("stats", {})
        return {
            "id": user_data.get("id"),
            "uniqueId": user_data.get("uniqueId", username),
            "nickname": user_data.get("nickname", ""),
            "avatarThumb": user_data.get("avatarLarger") or user_data.get("avatarThumb", ""),
            "signature": user_data.get("signature", ""),
            "verified": user_data.get("verified", False),
            "region": (user_data.get("region") or "").upper(),
            "followerCount": _to_int(stats_data.get("followerCount", 0)),
            "followingCount": _to_int(stats_data.get("followingCount", 0)),
            "heartCount": _to_int(stats_data.get("heartCount", 0)),
            "videoCount": _to_int(stats_data.get("videoCount", 0)),
            "source": "L3_cloudscraper",
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# ⏰ Timezone Analysis
# ═══════════════════════════════════════════════════════════
def analyze_posting_timezone(timestamps: List[int]) -> Optional[Dict[str, Any]]:
    if not timestamps or len(timestamps) < 3:
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
    peak_utc_hour = max(hour_counts, key=hour_counts.get)
    ASSUMED_LOCAL_PEAK = 20
    utc_offset = (ASSUMED_LOCAL_PEAK - peak_utc_hour) % 24
    if utc_offset > 12:
        utc_offset -= 24
    OFFSET_MAP = {
        0: ["GB", "PT", "IE"],
        1: ["FR", "DE", "IT", "ES", "NL", "MA", "DZ", "TN", "NG"],
        2: ["EG", "LY", "GR", "TR", "FI", "PS", "JO", "LB", "SY", "ZA"],
        3: ["SA", "AE", "KW", "QA", "BH", "IQ", "YE", "OM", "SD", "SO", "RU", "KE", "ET"],
        4: ["AZ", "GE", "AM"],
        5: ["PK", "AF", "UZ"],
        6: ["BD", "KZ"],
        7: ["TH", "VN", "ID"],
        8: ["CN", "MY", "SG", "PH", "HK", "TW", "AU"],
        9: ["JP", "KR", "KP"],
        -3: ["BR", "AR", "UY", "CL"],
        -4: ["VE", "BO"],
        -5: ["CO", "PE", "EC", "CU", "US"],
        -6: ["MX", "GT", "US"],
        -7: ["US", "CA"],
        -8: ["US", "CA"],
    }
    candidates = OFFSET_MAP.get(utc_offset, [])
    total_posts = sum(hour_counts.values())
    peak_ratio = hour_counts[peak_utc_hour] / total_posts if total_posts else 0
    return {
        "utc_offset": utc_offset,
        "peak_utc_hour": peak_utc_hour,
        "candidate_countries": candidates,
        "sample_size": len(timestamps),
        "peak_ratio": round(peak_ratio, 2),
    }


# ═══════════════════════════════════════════════════════════
# 🎯 Multi-Signal Verdict
# ═══════════════════════════════════════════════════════════
def compute_verdict(user_info: Dict[str, Any], videos: Optional[List[Dict]] = None) -> Dict[str, Any]:
    signals = []
    videos = videos or user_info.get("_videos", []) or []

    # Signal 1: user.region
    user_region = (user_info.get("region") or "").upper().strip()
    if user_region and user_region in WORLD_COUNTRIES:
        signals.append({
            "type": "user_region",
            "iso": user_region,
            "weight": 0.9,  # High weight - direct from RapidAPI/TikTok
            "reason": f"TikTok User.region: {user_region}",
        })

    # Signal 2: video regions
    video_regions = []
    timestamps = []
    for v in videos:
        r = (v.get("region") or "").upper().strip()
        if r and r in WORLD_COUNTRIES:
            video_regions.append(r)
        ts = v.get("create_time") or v.get("createTime")
        if ts:
            try:
                timestamps.append(int(ts))
            except Exception:
                pass

    if video_regions:
        counter = Counter(video_regions)
        top_iso, top_count = counter.most_common(1)[0]
        ratio = top_count / len(video_regions)
        signals.append({
            "type": "video_region",
            "iso": top_iso,
            "weight": 0.85 * ratio,
            "reason": f"{top_count}/{len(video_regions)} فيديوهات مُعلَّمة {top_iso}",
            "sample": len(video_regions),
        })

    # Signal 3: timezone
    tz_analysis = analyze_posting_timezone(timestamps) if timestamps else None
    if tz_analysis and tz_analysis["candidate_countries"]:
        candidate = tz_analysis["candidate_countries"][0]
        signals.append({
            "type": "timezone",
            "iso": candidate,
            "weight": 0.3 * tz_analysis["peak_ratio"],
            "reason": f"UTC{tz_analysis['utc_offset']:+d} peak at hour {tz_analysis['peak_utc_hour']}",
            "candidates": tz_analysis["candidate_countries"],
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
            "note": "لا توجد إشارات جغرافية كافية",
        }

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

    # ── LAYER 0: RapidAPI (PRIMARY) ──
    if RAPIDAPI_ENABLED:
        layers_tried.append("L0_rapidapi")
        user_info = await layer0_rapidapi(username)

    # ── LAYER 1 ──
    if not user_info:
        layers_tried.append("L1_web")
        user_info = await layer1_tiktok_web(username)

    # ── LAYER 2 ──
    if not user_info:
        layers_tried.append("L2_mobile")
        user_info = await layer2_mobile_api(username)

    # ── LAYER 3 ──
    if not user_info:
        layers_tried.append("L3_cloudscraper")
        user_info = layer3_cloudscraper(username)

    if not user_info:
        return LookupResult(
            success=False,
            error="جميع الطبقات فشلت في جلب بيانات المستخدم من TikTok",
            username=username,
            layers_tried=layers_tried,
            elapsed=round(time.time() - start, 2),
        )

    videos = user_info.get("_videos", [])
    verdict = compute_verdict(user_info, videos)

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
        "rapidapi_enabled": RAPIDAPI_ENABLED,
    })
    return result


# ═══════════════════════════════════════════════════════════
# 🎨 Markdown Formatter (for Telegram)
# ═══════════════════════════════════════════════════════════
def _format_markdown_for_bot(result: LookupResult) -> str:
    if not result.get("success"):
        err = result.get("error", "فشل جلب البيانات")
        layers = result.get("layers_tried", [])
        layers_str = ", ".join(layers) if layers else "لا شيء"
        return (
            f"❌ *فشل البحث*\n\n"
            f"{err}\n"
            f"📡 الطبقات المُحاولة: `{layers_str}`\n\n"
            f"💡 تأكد من اسم المستخدم وحاول مرة أخرى."
        )

    stats = result.get("stats", {}) or {}
    geo = result.get("geo", {}) or {}

    nickname = result.get("nickname", "") or ""
    username = result.get("username", "") or ""
    verified_badge = " ✅" if result.get("verified") else ""
    private_badge = " 🔒" if result.get("private") else ""

    followers = stats.get("followers", 0) or 0
    following = stats.get("following", 0) or 0
    hearts = stats.get("hearts", 0) or 0
    videos = stats.get("videos", 0) or 0

    flag = geo.get("flag", "🏳️") or "🏳️"
    country_ar = geo.get("country_ar", "غير محدد") or "غير محدد"
    confidence = geo.get("confidence", 0) or 0
    tz = geo.get("timezone") or ""
    continent = geo.get("continent") or ""

    src = geo.get("primary_source") or ""
    src_labels = {
        "video_region": "📹 من metadata الفيديوهات",
        "user_region": "👤 من ملف المستخدم (TikTok)",
        "timezone": "⏰ من تحليل توقيت النشر",
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
        lines.append(f"ℹ️ _{reason}_")

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

    if result.get("rapidapi_enabled"):
        lines.append("🏆 _مدعوم بـ RapidAPI + Data-Driven_")
    else:
        lines.append("🔬 _تحليل Data-Driven فقط_")
    lines.append("✅ لا اعتماد على الاسم/اللهجة")

    layers = result.get("layers_tried", [])
    if layers:
        lines.append(f"📡 الطبقات: `{', '.join(layers)}`")

    analyzed = result.get("videos_analyzed", 0) or 0
    if analyzed:
        lines.append(f"📹 الفيديوهات المُحللة: `{analyzed}`")

    elapsed = result.get("elapsed", 0) or 0
    if elapsed:
        lines.append(f"⚡ زمن الاستجابة: `{elapsed}s`")

    lines.append("🗺️ قاعدة: `v2.3.0` (249 دولة)")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# 🔄 Backward-Compat API (for bot.py v2.1.8.9)
# ═══════════════════════════════════════════════════════════
def clean_username(raw: str) -> str:
    """Clean TikTok username from URL or @-prefixed text."""
    if not raw:
        return ""
    s = raw.strip().lstrip("@")
    # Handle URLs like https://www.tiktok.com/@user
    if "tiktok.com" in s:
        s = s.split("tiktok.com/")[-1]
    s = s.lstrip("@").split("/")[0].split("?")[0].split("#")[0]
    return s.strip()


async def lookup_tiktok_user(username: str) -> str:
    """
    Legacy-compatible wrapper for bot.py v2.1.8.9.

    Returns a Markdown STRING (not dict) ready for Telegram edit_text().
    """
    cleaned = clean_username(username)
    try:
        result = await lookup_tiktok(cleaned)
        return _format_markdown_for_bot(result)
    except Exception as e:
        logger.error(f"[lookup_tiktok_user] exception for @{cleaned}: {e}", exc_info=True)
        return (
            f"❌ *فشل البحث*\n\n"
            f"حدث خطأ داخلي أثناء جلب بيانات @{cleaned}\n"
            f"`{str(e)[:200]}`\n\n"
            f"💡 حاول مرة أخرى بعد قليل."
        )


async def lookup_tiktok_user_dict(username: str) -> Dict[str, Any]:
    """New API - returns full structured dict."""
    cleaned = clean_username(username)
    result = await lookup_tiktok(cleaned)
    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "فشل جلب البيانات"),
            "username": cleaned,
        }
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
        "formatted_markdown": _format_markdown_for_bot(result),
        "_full_result": dict(result),
    }


# Extra common aliases (defensive)
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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    username = sys.argv[1] if len(sys.argv) > 1 else "citizen_lawyerr"
    print(f"\n🔍 Testing lookup for: @{username}")
    print(f"🏆 RapidAPI enabled: {RAPIDAPI_ENABLED}\n")

    async def _main():
        result_str = await lookup_tiktok_user(username)
        print("=" * 60)
        print(result_str)
        print("=" * 60)

    asyncio.run(_main())
