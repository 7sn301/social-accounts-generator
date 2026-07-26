"""
╔══════════════════════════════════════════════════════════════════╗
║  BSR-V221-CTO-INTEGRATION-TIKTOK-WORLDMAP-AHMAD-20260726         ║
║  tiktok_lookup.py v2.2.1 - Integrated with World Map (249)      ║
║  Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)            ║
╚══════════════════════════════════════════════════════════════════╝

Cloudflare Bypass System + World Complete Map Integration:
  L1: TikTok Web Direct (__UNIVERSAL_DATA_FOR_REHYDRATION__ / SIGI_STATE)
  L2: Mobile API (m.tiktok.com/api/user/detail)
  L3: cloudscraper (Cloudflare Challenge bypass)
  L4: Playwright headless (fallback last resort)

Data-Driven Detection ONLY:
  ✓ Video Region (item.region)
  ✓ locationCreated (GPS from videos)
  ✓ Timezone analysis from post timestamps
  ✓ User.region (if available)
  ✗ NO name/dialect/bio-keyword analysis

Country Database: regions_database.py v2.2.1 (249 countries, ISO 3166-1)
"""

import asyncio
import json
import logging
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

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# 🎭 Rotating User Agents
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

TIKTOK_APP_UAS = [
    "com.zhiliaoapp.musically/2023600030 (Linux; U; Android 13; en_US; SM-G991B; Build/TP1A.220624.014; Cronet/58.0.2991.0)",
    "TikTok/2023600030 CFNetwork/1494.0.7 Darwin/23.4.0",
]

def _rand_ua(pool: List[str]) -> str:
    return random.choice(pool)

TIMEOUT = httpx.Timeout(18.0, connect=10.0)


# ═══════════════════════════════════════════════════════════
# 📊 Data classes
# ═══════════════════════════════════════════════════════════
class LookupResult(dict):
    """Container for lookup results with attribute access."""
    def __getattr__(self, key):
        return self.get(key)


# ═══════════════════════════════════════════════════════════
# 🌐 Layer 1: TikTok Web Direct
# ═══════════════════════════════════════════════════════════
async def layer1_tiktok_web(username: str) -> Optional[Dict[str, Any]]:
    """
    Extract data from https://www.tiktok.com/@{username}
    Parses __UNIVERSAL_DATA_FOR_REHYDRATION__ (new) or SIGI_STATE (old).
    """
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": _rand_ua(DESKTOP_UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"[L1] HTTP {resp.status_code} for @{username}")
                return None

            html = resp.text

            # Try __UNIVERSAL_DATA_FOR_REHYDRATION__ (2024+)
            m = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.+?)</script>',
                html, re.DOTALL,
            )
            if m:
                try:
                    data = json.loads(m.group(1))
                    return _parse_universal_data(data, username, source="L1_universal")
                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f"[L1] universal parse err: {e}")

            # Try SIGI_STATE (old format)
            m = re.search(r'<script id="SIGI_STATE"[^>]*>(.+?)</script>', html, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    return _parse_sigi_state(data, username, source="L1_sigi")
                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f"[L1] SIGI parse err: {e}")

            logger.info(f"[L1] no data blocks found for @{username}")
            return None

    except Exception as e:
        logger.warning(f"[L1] exception for @{username}: {e}")
        return None


def _parse_universal_data(data: dict, username: str, source: str) -> Optional[Dict[str, Any]]:
    """Parse __UNIVERSAL_DATA_FOR_REHYDRATION__ structure."""
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
            "avatarThumb": user.get("avatarLarger") or user.get("avatarMedium") or user.get("avatarThumb", ""),
            "signature": user.get("signature", ""),
            "verified": user.get("verified", False),
            "region": user.get("region", ""),  # 🎯 KEY signal
            "language": user.get("language", ""),
            "followerCount": _to_int(stats.get("followerCount", 0)),
            "followingCount": _to_int(stats.get("followingCount", 0)),
            "heartCount": _to_int(stats.get("heartCount", 0)),
            "videoCount": _to_int(stats.get("videoCount", 0)),
            "createTime": user.get("createTime", 0),
            "privateAccount": user.get("privateAccount", False),
            "source": source,
        }
    except Exception as e:
        logger.debug(f"[L1] universal parse structure err: {e}")
        return None


def _parse_sigi_state(data: dict, username: str, source: str) -> Optional[Dict[str, Any]]:
    """Parse legacy SIGI_STATE structure."""
    try:
        users = data.get("UserModule", {}).get("users", {})
        stats = data.get("UserModule", {}).get("stats", {})
        user = users.get(username) or (list(users.values())[0] if users else {})
        stat = stats.get(username) or (list(stats.values())[0] if stats else {})
        if not user:
            return None

        return {
            "id": user.get("id"),
            "uniqueId": user.get("uniqueId", username),
            "nickname": user.get("nickname", ""),
            "avatarThumb": user.get("avatarLarger") or user.get("avatarThumb", ""),
            "signature": user.get("signature", ""),
            "verified": user.get("verified", False),
            "region": user.get("region", ""),
            "language": user.get("language", ""),
            "followerCount": _to_int(stat.get("followerCount", 0)),
            "followingCount": _to_int(stat.get("followingCount", 0)),
            "heartCount": _to_int(stat.get("heartCount", 0)),
            "videoCount": _to_int(stat.get("videoCount", 0)),
            "createTime": user.get("createTime", 0),
            "privateAccount": user.get("privateAccount", False),
            "source": source,
        }
    except Exception as e:
        logger.debug(f"[L1] SIGI parse structure err: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 📱 Layer 2: Mobile API
# ═══════════════════════════════════════════════════════════
async def layer2_mobile_api(username: str) -> Optional[Dict[str, Any]]:
    """Mobile TikTok endpoint - different fingerprint."""
    url = f"https://m.tiktok.com/@{username}"
    headers = {
        "User-Agent": _rand_ua(MOBILE_UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
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
                return _parse_universal_data(data, username, source="L2_mobile")
            return None
    except Exception as e:
        logger.warning(f"[L2] exception: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 🛡️ Layer 3: cloudscraper (bypass Cloudflare)
# ═══════════════════════════════════════════════════════════
def layer3_cloudscraper(username: str) -> Optional[Dict[str, Any]]:
    """Uses cloudscraper to bypass Cloudflare and hit tikwm."""
    if not CLOUDSCRAPER_AVAILABLE:
        logger.debug("[L3] cloudscraper not installed")
        return None
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        # Try tikwm info endpoint
        info_url = f"https://www.tikwm.com/api/user/info?unique_id={username}"
        resp = scraper.get(info_url, timeout=15)
        if resp.status_code != 200:
            return None
        payload = resp.json()
        if payload.get("code") != 0:
            return None
        user_data = payload.get("data", {}).get("user", {})
        stats_data = payload.get("data", {}).get("stats", {})

        info = {
            "id": user_data.get("id"),
            "uniqueId": user_data.get("uniqueId", username),
            "nickname": user_data.get("nickname", ""),
            "avatarThumb": user_data.get("avatarLarger") or user_data.get("avatarThumb", ""),
            "signature": user_data.get("signature", ""),
            "verified": user_data.get("verified", False),
            "region": user_data.get("region", ""),
            "followerCount": _to_int(stats_data.get("followerCount", 0)),
            "followingCount": _to_int(stats_data.get("followingCount", 0)),
            "heartCount": _to_int(stats_data.get("heartCount", 0)),
            "videoCount": _to_int(stats_data.get("videoCount", 0)),
            "source": "L3_cloudscraper",
        }

        # Also fetch user posts for regions
        try:
            posts_url = f"https://www.tikwm.com/api/user/posts?unique_id={username}&count=10"
            posts_resp = scraper.get(posts_url, timeout=15)
            if posts_resp.status_code == 200:
                posts_payload = posts_resp.json()
                if posts_payload.get("code") == 0:
                    videos = posts_payload.get("data", {}).get("videos", [])
                    info["_videos"] = videos
        except Exception:
            pass

        return info
    except Exception as e:
        logger.warning(f"[L3] cloudscraper err: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# 🎭 Layer 4: Playwright (last resort)
# ═══════════════════════════════════════════════════════════
async def layer4_playwright(username: str) -> Optional[Dict[str, Any]]:
    """Headless browser - highest cost, highest success rate."""
    if not PLAYWRIGHT_AVAILABLE:
        logger.debug("[L4] playwright not installed")
        return None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=_rand_ua(DESKTOP_UAS),
                viewport={"width": 1366, "height": 768},
                locale="en-US",
            )
            page = await context.new_page()
            await page.goto(f"https://www.tiktok.com/@{username}", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2500)

            content = await page.content()
            await browser.close()

            m = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.+?)</script>',
                content, re.DOTALL,
            )
            if m:
                data = json.loads(m.group(1))
                return _parse_universal_data(data, username, source="L4_playwright")
            return None
    except Exception as e:
        logger.warning(f"[L4] playwright err: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# ⏰ Timezone Analysis from Timestamps
# ═══════════════════════════════════════════════════════════
def analyze_posting_timezone(timestamps: List[int]) -> Optional[Dict[str, Any]]:
    """
    Estimate user's timezone from posting hour peak.
    Peak hours 18-23 local suggest that timezone.
    """
    if not timestamps or len(timestamps) < 3:
        return None

    hour_counts = Counter()
    for ts in timestamps:
        try:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            hour_counts[dt.hour] += 1
        except Exception:
            continue

    if not hour_counts:
        return None

    # Peak UTC hour
    peak_utc_hour = max(hour_counts, key=hour_counts.get)

    # Assume peak is 20:00 local (typical prime time)
    ASSUMED_LOCAL_PEAK = 20
    utc_offset = (ASSUMED_LOCAL_PEAK - peak_utc_hour) % 24
    if utc_offset > 12:
        utc_offset -= 24

    # Map offset → probable countries
    OFFSET_MAP = {
        0: ["GB", "PT", "IE"],
        1: ["FR", "DE", "IT", "ES", "NL", "MA", "DZ", "TN", "NG"],
        2: ["EG", "LY", "GR", "TR", "FI", "PS", "JO", "LB", "SY", "ZA"],
        3: ["SA", "AE", "KW", "QA", "BH", "IQ", "YE", "OM", "SD", "SO", "RU", "KE", "ET"],
        4: ["AZ", "GE", "AM"],
        5: ["PK", "AF", "UZ", "TM", "TJ", "KZ"],
        6: ["BD", "KZ"],
        7: ["TH", "VN", "ID", "KH", "LA"],
        8: ["CN", "MY", "SG", "PH", "HK", "TW", "AU"],
        9: ["JP", "KR", "KP"],
        -3: ["BR", "AR", "UY", "CL"],
        -4: ["VE", "BO", "PY", "DO"],
        -5: ["CO", "PE", "EC", "CU", "JM", "US"],
        -6: ["MX", "GT", "HN", "SV", "NI", "CR", "US"],
        -7: ["US", "CA"],
        -8: ["US", "CA"],
    }

    candidates = OFFSET_MAP.get(utc_offset, [])
    total_posts = sum(hour_counts.values())
    peak_ratio = hour_counts[peak_utc_hour] / total_posts if total_posts else 0

    return {
        "utc_offset": utc_offset,
        "peak_utc_hour": peak_utc_hour,
        "assumed_local_peak": ASSUMED_LOCAL_PEAK,
        "candidate_countries": candidates,
        "sample_size": len(timestamps),
        "peak_ratio": round(peak_ratio, 2),
    }


# ═══════════════════════════════════════════════════════════
# 🎯 Multi-Signal Verdict
# ═══════════════════════════════════════════════════════════
def compute_verdict(
    user_info: Dict[str, Any],
    videos: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Compute geographic verdict from all available signals.
    Data-driven ONLY - NO name/dialect analysis.
    """
    signals = []
    videos = videos or user_info.get("_videos", []) or []

    # ─── Signal 1: user.region ───
    user_region = (user_info.get("region") or "").upper().strip()
    if user_region and user_region in WORLD_COUNTRIES:
        signals.append({
            "type": "user_region",
            "iso": user_region,
            "weight": 0.5,
            "reason": "TikTok User.region metadata",
        })

    # ─── Signal 2: video regions (heaviest weight) ───
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
        confidence = top_count / len(video_regions)
        signals.append({
            "type": "video_region",
            "iso": top_iso,
            "weight": 0.9 * confidence,
            "reason": f"{top_count}/{len(video_regions)} videos tagged {top_iso}",
            "sample": len(video_regions),
        })

    # ─── Signal 3: timezone analysis ───
    tz_analysis = analyze_posting_timezone(timestamps) if timestamps else None
    if tz_analysis and tz_analysis["candidate_countries"]:
        # Prefer candidate that matches other signals
        candidate = tz_analysis["candidate_countries"][0]
        signals.append({
            "type": "timezone",
            "iso": candidate,
            "weight": 0.3 * tz_analysis["peak_ratio"],
            "reason": f"UTC{tz_analysis['utc_offset']:+d} peak at hour {tz_analysis['peak_utc_hour']}",
            "candidates": tz_analysis["candidate_countries"],
        })

    # ─── Aggregate ───
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
            "note": "لا توجد إشارات جغرافية كافية (بيانات فقط، لا اسم/لهجة)",
        }

    # Vote by weighted signals
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
# 🎯 Main Public API
# ═══════════════════════════════════════════════════════════
async def lookup_tiktok(username: str) -> LookupResult:
    """
    Main entry point - Multi-layer Cloudflare bypass + geo verdict.

    Args:
        username: TikTok username (without @)

    Returns:
        LookupResult with: user info + verdict + layers_used
    """
    if not REGIONS_DB_AVAILABLE:
        logger.error("regions_database.py missing - install it first")

    username = username.strip().lstrip("@")
    result = LookupResult()
    layers_tried = []
    user_info = None
    start = time.time()

    # ── Layer 1 ──
    layers_tried.append("L1_web")
    user_info = await layer1_tiktok_web(username)

    # ── Layer 2 ──
    if not user_info:
        layers_tried.append("L2_mobile")
        user_info = await layer2_mobile_api(username)

    # ── Layer 3 ──
    if not user_info:
        layers_tried.append("L3_cloudscraper")
        user_info = layer3_cloudscraper(username)

    # ── Layer 4 ──
    if not user_info:
        layers_tried.append("L4_playwright")
        user_info = await layer4_playwright(username)

    if not user_info:
        return LookupResult(
            success=False,
            error="جميع الطبقات فشلت في جلب بيانات المستخدم",
            username=username,
            layers_tried=layers_tried,
            elapsed=round(time.time() - start, 2),
        )

    # ── Videos (if L3 didn't fetch them) ──
    videos = user_info.get("_videos", [])
    if not videos and CLOUDSCRAPER_AVAILABLE:
        try:
            scraper = cloudscraper.create_scraper()
            posts_url = f"https://www.tikwm.com/api/user/posts?unique_id={username}&count=10"
            r = scraper.get(posts_url, timeout=12)
            if r.status_code == 200:
                p = r.json()
                if p.get("code") == 0:
                    videos = p.get("data", {}).get("videos", [])
        except Exception:
            pass

    # ── Verdict ──
    verdict = compute_verdict(user_info, videos)

    # ── Assemble result ──
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
    })
    return result


# ═══════════════════════════════════════════════════════════
# 🎨 Arabic Display Formatting
# ═══════════════════════════════════════════════════════════
def format_result_arabic(result: LookupResult) -> str:
    """Render result as Arabic RTL text (for bot messages)."""
    if not result.get("success"):
        return f"❌ فشل جلب البيانات: {result.get('error', 'خطأ غير معروف')}"

    stats = result.get("stats", {})
    geo = result.get("geo", {})

    verified_badge = " ✅ موثّق" if result.get("verified") else ""
    private_badge = " 🔒 خاص" if result.get("private") else ""

    lines = [
        f"👤 {result.get('nickname', '')}{verified_badge}{private_badge}",
        f"🔗 @{result.get('username', '')}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📊 الإحصائيات",
        f"👥 المتابعون: {stats.get('followers', 0):,}",
        f"➕ يتابع: {stats.get('following', 0):,}",
        f"📹 الفيديوهات: {stats.get('videos', 0):,}",
        f"❤️ الإعجابات: {stats.get('hearts', 0):,}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🌍 التحليل الجغرافي",
        f"🎯 الدولة: {geo.get('flag', '🏳️')} {geo.get('country_ar', 'غير محدد')}",
    ]

    conf = geo.get("confidence", 0)
    if conf > 0:
        lines.append(f"📊 مستوى الثقة: {conf}%")

    src = geo.get("primary_source")
    src_labels = {
        "video_region": "📹 من metadata الفيديوهات",
        "user_region": "👤 من ملف المستخدم",
        "timezone": "⏰ من تحليل توقيت النشر",
        "none": "❌ لا توجد إشارات",
    }
    if src:
        lines.append(f"🔍 المصدر: {src_labels.get(src, src)}")

    if geo.get("primary_reason"):
        lines.append(f"ℹ️ {geo['primary_reason']}")

    if geo.get("timezone"):
        lines.append(f"🕐 التوقيت المحلي: {geo['timezone']}")

    if geo.get("continent"):
        continent_ar = {
            "Asia": "آسيا",
            "Africa": "إفريقيا",
            "Europe": "أوروبا",
            "Americas": "الأمريكتان",
            "Oceania": "أوقيانوسيا",
            "Antarctica": "أنتاركتيكا",
        }.get(geo["continent"], geo["continent"])
        lines.append(f"🌐 القارة: {continent_ar}")

    if geo.get("is_arab"):
        badge = "🕌 دولة عربية"
        if geo.get("is_gcc"):
            badge += " (خليجية 🕋)"
        lines.append(badge)

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🔬 تحليل Data-Driven فقط",
        "✅ لا اعتماد على الاسم/اللهجة",
        f"📡 الطبقات المُستخدمة: {', '.join(result.get('layers_tried', []))}",
        f"📹 الفيديوهات المحللة: {result.get('videos_analyzed', 0)}",
        f"⚡ زمن الاستجابة: {result.get('elapsed', 0)}s",
        f"🗺️ قاعدة الدول: {result.get('regions_db_version', '?')} (249 دولة)",
    ])

    return "\n".join(lines)


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
    print(f"\n🔍 Testing lookup for: @{username}\n")

    async def _main():
        result = await lookup_tiktok(username)
        print("=" * 60)
        print(format_result_arabic(result))
        print("=" * 60)
        print("\n📋 Raw JSON:")
        print(json.dumps(dict(result), ensure_ascii=False, indent=2, default=str))

    asyncio.run(_main())


# ═══════════════════════════════════════════════════════════
# 🔄 Backward Compatibility Aliases (for bot.py v2.1.x)
# ═══════════════════════════════════════════════════════════
# bot.py legacy imports:
#   from tiktok_lookup import lookup_tiktok_user, clean_username

def clean_username(raw: str) -> str:
    """Legacy alias - clean TikTok username."""
    if not raw:
        return ""
    return raw.strip().lstrip("@").split("/")[-1].split("?")[0]


def _format_markdown_for_bot(result: LookupResult) -> str:
    """
    Render result as Markdown text ready for Telegram edit_text().
    Returns the exact string that bot.py expects to send to users.
    """
    if not result.get("success"):
        err = result.get("error", "فشل جلب البيانات")
        return f"❌ *فشل البحث*\n\n{err}\n\n💡 تأكد من اسم المستخدم وحاول مرة أخرى."

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
        "user_region": "👤 من ملف المستخدم",
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
        lines.append(f"ℹ️ {reason}")

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

    lines.append("🗺️ قاعدة: `v2.2.1` (249 دولة)")

    return "\n".join(lines)


async def lookup_tiktok_user(username: str) -> str:
    """
    Legacy-compatible wrapper for bot.py v2.1.8.9.

    Returns a Markdown STRING (not dict) ready for Telegram edit_text().
    Includes country name for regex extraction by bot.py.

    Fixes: 'TypeError: expected str, got dict' in bot.py handle_lookup.
    """
    cleaned = clean_username(username)
    try:
        result = await lookup_tiktok(cleaned)
        return _format_markdown_for_bot(result)
    except Exception as e:
        logger.error(f"[lookup_tiktok_user] exception for @{cleaned}: {e}")
        return (
            f"❌ *فشل البحث*\n\n"
            f"حدث خطأ أثناء جلب بيانات @{cleaned}\n"
            f"`{str(e)[:200]}`\n\n"
            f"💡 حاول مرة أخرى بعد قليل."
        )


async def lookup_tiktok_user_dict(username: str) -> Dict[str, Any]:
    """
    New API — returns full structured dict for advanced consumers.
    Use this instead of lookup_tiktok_user() when you need raw data.
    """
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


# Extra common aliases (defensive):
lookup = lookup_tiktok_user
get_tiktok_info = lookup_tiktok_user
tiktok_lookup = lookup_tiktok_user
