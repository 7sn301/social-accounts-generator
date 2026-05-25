"""
🕵️ TikTok OSINT Geo Toolkit v1.0
=================================
أدوات OSINT جغرافية لتيك توك تعمل بدون API مدفوع وتعتمد على:

1) تحليل locationCreated من الفيديوهات لاستخراج الدولة المرجحة للحساب
2) تحليل author.region كإشارة مساندة
3) Geocoding مجاني عبر OpenStreetMap Nominatim
4) بناء روابط بحث TikTok جغرافي وروابط تحقق متعددة
5) تحليل أوقات النشر لاستنتاج المنطقة الزمنية الفعلية
6) مراكز إحداثية جاهزة للدول لرسم الخرائط بسرعة
"""

from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote, quote_plus

import requests

try:
    from tiktok_analyzer import TIKTOK_REGION_MAP, LANGUAGE_NAMES_AR
except Exception:
    TIKTOK_REGION_MAP = {
        "SA": ("🇸🇦", "السعودية"), "AE": ("🇦🇪", "الإمارات"), "EG": ("🇪🇬", "مصر"),
        "KW": ("🇰🇼", "الكويت"), "QA": ("🇶🇦", "قطر"), "BH": ("🇧🇭", "البحرين"),
        "OM": ("🇴🇲", "عُمان"), "JO": ("🇯🇴", "الأردن"), "LB": ("🇱🇧", "لبنان"),
        "SY": ("🇸🇾", "سوريا"), "IQ": ("🇮🇶", "العراق"), "YE": ("🇾🇪", "اليمن"),
        "PS": ("🇵🇸", "فلسطين"), "MA": ("🇲🇦", "المغرب"), "DZ": ("🇩🇿", "الجزائر"),
        "TN": ("🇹🇳", "تونس"), "LY": ("🇱🇾", "ليبيا"), "SD": ("🇸🇩", "السودان"),
        "US": ("🇺🇸", "الولايات المتحدة"), "GB": ("🇬🇧", "بريطانيا"), "FR": ("🇫🇷", "فرنسا"),
        "DE": ("🇩🇪", "ألمانيا"), "TR": ("🇹🇷", "تركيا"), "IR": ("🇮🇷", "إيران"),
        "PK": ("🇵🇰", "باكستان"), "IN": ("🇮🇳", "الهند"), "JP": ("🇯🇵", "اليابان"),
        "KR": ("🇰🇷", "كوريا الجنوبية"), "ID": ("🇮🇩", "إندونيسيا"), "MY": ("🇲🇾", "ماليزيا"),
        "TH": ("🇹🇭", "تايلاند"), "VN": ("🇻🇳", "فيتنام"), "PH": ("🇵🇭", "الفلبين"),
        "RU": ("🇷🇺", "روسيا"), "UA": ("🇺🇦", "أوكرانيا"), "BR": ("🇧🇷", "البرازيل"),
        "MX": ("🇲🇽", "المكسيك"), "CA": ("🇨🇦", "كندا"), "AU": ("🇦🇺", "أستراليا"),
        "NG": ("🇳🇬", "نيجيريا"), "ZA": ("🇿🇦", "جنوب أفريقيا"),
    }
    LANGUAGE_NAMES_AR = {
        "ar": "العربية", "en": "الإنجليزية", "es": "الإسبانية", "fr": "الفرنسية",
        "de": "الألمانية", "it": "الإيطالية", "pt": "البرتغالية", "ru": "الروسية",
        "tr": "التركية", "fa": "الفارسية", "ur": "الأردية", "hi": "الهندية",
        "zh": "الصينية", "ja": "اليابانية", "ko": "الكورية", "id": "الإندونيسية",
        "ms": "الماليزية", "th": "التايلاندية", "vi": "الفيتنامية", "tl": "الفلبينية",
        "un": "غير محدد",
    }

HTTP_TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

COUNTRY_CENTERS: Dict[str, List[float]] = {
    "SA": [24.7136, 46.6753], "AE": [25.2048, 55.2708], "EG": [30.0444, 31.2357],
    "KW": [29.3759, 47.9774], "QA": [25.2854, 51.5310], "BH": [26.2235, 50.5876],
    "OM": [23.5880, 58.3829], "JO": [31.9539, 35.9106], "LB": [33.8938, 35.5018],
    "SY": [33.5138, 36.2765], "IQ": [33.3152, 44.3661], "YE": [15.3694, 44.1910],
    "PS": [31.9522, 35.2332], "MA": [33.5731, -7.5898], "DZ": [36.7538, 3.0588],
    "TN": [36.8065, 10.1815], "LY": [32.8872, 13.1913], "SD": [15.5007, 32.5599],
    "SO": [2.0469, 45.3182], "MR": [18.0790, -15.9650], "US": [38.9072, -77.0369],
    "GB": [51.5074, -0.1278], "FR": [48.8566, 2.3522], "DE": [52.5200, 13.4050],
    "IT": [41.9028, 12.4964], "ES": [40.4168, -3.7038], "NL": [52.3676, 4.9041],
    "BE": [50.8503, 4.3517], "CH": [46.9480, 7.4474], "SE": [59.3293, 18.0686],
    "NO": [59.9139, 10.7522], "DK": [55.6761, 12.5683], "FI": [60.1699, 24.9384],
    "PT": [38.7223, -9.1393], "AT": [48.2082, 16.3738], "PL": [52.2297, 21.0122],
    "GR": [37.9838, 23.7275], "TR": [41.0082, 28.9784], "IR": [35.6892, 51.3890],
    "PK": [24.8607, 67.0011], "IN": [28.6139, 77.2090], "BD": [23.8103, 90.4125],
    "AF": [34.5553, 69.2075], "CN": [39.9042, 116.4074], "JP": [35.6762, 139.6503],
    "KR": [37.5665, 126.9780], "ID": [-6.2088, 106.8456], "MY": [3.1390, 101.6869],
    "SG": [1.3521, 103.8198], "TH": [13.7563, 100.5018], "VN": [21.0278, 105.8342],
    "PH": [14.5995, 120.9842], "RU": [55.7558, 37.6173], "UA": [50.4501, 30.5234],
    "BR": [-23.5505, -46.6333], "AR": [-34.6037, -58.3816], "MX": [19.4326, -99.1332],
    "CA": [45.4215, -75.6972], "AU": [-33.8688, 151.2093], "NZ": [-36.8485, 174.7633],
    "NG": [9.0765, 7.3986], "ZA": [-26.2041, 28.0473], "KE": [-1.2921, 36.8219],
    "ET": [8.9806, 38.7578], "IL": [31.7683, 35.2137],
}

LANG_TO_COUNTRIES: Dict[str, List[str]] = {
    "ar": ["SA", "EG", "AE", "KW", "QA", "BH", "OM", "JO", "LB", "SY", "IQ", "YE", "PS", "MA", "DZ", "TN", "LY", "SD"],
    "tr": ["TR"], "fa": ["IR"], "ur": ["PK"], "hi": ["IN"], "bn": ["BD"],
    "id": ["ID"], "ms": ["MY"], "th": ["TH"], "vi": ["VN"], "tl": ["PH"],
    "ja": ["JP"], "ko": ["KR"], "ru": ["RU"], "uk": ["UA"],
    "es": ["ES", "MX", "AR"], "pt": ["BR", "PT"], "de": ["DE"],
    "it": ["IT"], "nl": ["NL"], "el": ["GR"], "he": ["IL"], "en": ["US", "GB", "CA", "AU"],
}

OFFSET_TO_COUNTRIES: Dict[Any, List[str]] = {
    0:  ["GB", "PT", "IE"],
    1:  ["DE", "FR", "ES", "IT", "NL", "TN", "DZ", "MA"],
    2:  ["EG", "LB", "SY", "JO", "PS", "GR", "ZA"],
    3:  ["SA", "KW", "QA", "BH", "IQ", "YE", "TR", "RU"],
    4:  ["AE", "OM"],
    5:  ["PK"],
    6:  ["BD"],
    7:  ["TH", "VN", "ID"],
    8:  ["CN", "MY", "SG", "PH"],
    9:  ["JP", "KR"],
    -5: ["US", "CA"],
    -6: ["US"],
    -7: ["US"],
    -8: ["US"],
    -3: ["BR", "AR"],
}

FAMOUS_LOCATIONS_TT: List[str] = [
    "الرياض", "جدة", "دبي", "أبوظبي", "القاهرة", "الإسكندرية", "الكويت", "الدوحة",
    "المنامة", "مسقط", "عمّان", "بيروت", "بغداد", "إسطنبول", "الدار البيضاء",
    "الرباط", "مراكش", "الجزائر", "تونس", "طرابلس", "لندن", "باريس", "برلين",
    "نيويورك", "لوس أنجلوس", "تورونتو", "طوكيو", "سيول", "كوالالمبور", "جاكرتا",
]

_GEOCODE_CACHE: Dict[str, Any] = {}


def _country_tuple(code: str) -> tuple:
    code = (code or "").upper()
    return TIKTOK_REGION_MAP.get(code, ("🌍", code or "غير معروف"))


def get_region_center(region_code: str) -> Optional[List[float]]:
    code = (region_code or "").upper().strip()
    return COUNTRY_CENTERS.get(code)


def geocode_place(query: str, lang: str = "ar") -> Optional[Dict[str, Any]]:
    if not query:
        return None
    cache_key = f"{query.lower()}|{lang}"
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "json",
                "limit": 1,
                "addressdetails": 1,
                "accept-language": lang,
            },
            headers={"User-Agent": "TikTokOSINT/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code == 200 and response.json():
            item = response.json()[0]
            address = item.get("address", {})
            result = {
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "display_name": item.get("display_name", query),
                "country": address.get("country", ""),
                "country_code": address.get("country_code", "").upper(),
                "city": address.get("city") or address.get("town") or address.get("village") or address.get("state"),
                "type": item.get("type", ""),
                "bounding_box": item.get("boundingbox", []),
                "osm_url": f"https://www.openstreetmap.org/?mlat={item['lat']}&mlon={item['lon']}&zoom=14",
            }
            _GEOCODE_CACHE[cache_key] = result
            time.sleep(1)
            return result
    except Exception:
        return None
    return None


def reverse_geocode(lat: float, lon: float, lang: str = "ar") -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "format": "json",
                "lat": lat,
                "lon": lon,
                "zoom": 18,
                "addressdetails": 1,
                "accept-language": lang,
            },
            headers={"User-Agent": "TikTokOSINT/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            return {
                "display_name": data.get("display_name"),
                "country": address.get("country"),
                "country_code": address.get("country_code", "").upper(),
                "state": address.get("state"),
                "city": address.get("city") or address.get("town") or address.get("village") or address.get("county"),
                "road": address.get("road"),
                "postcode": address.get("postcode"),
            }
    except Exception:
        return None
    return None


def build_map_verification_links(lat: float, lon: float) -> Dict[str, str]:
    return {
        "google_maps":   f"https://www.google.com/maps?q={lat},{lon}",
        "yandex_maps":   f"https://yandex.com/maps/?ll={lon}%2C{lat}&z=13",
        "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=13",
        "apple_maps":    f"https://maps.apple.com/?ll={lat},{lon}&z=13",
    }


def _normalize_for_hashtag(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w\u0600-\u06FF]", "", text)
    return text


def build_tiktok_search_links(place: str, keywords: str = "", geo: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    place = (place or "").strip()
    keywords = (keywords or "").strip()
    query = " ".join(x for x in [place, keywords] if x).strip()
    hashtag = _normalize_for_hashtag(place) or _normalize_for_hashtag(query)
    country_name = ""
    country_code = ""
    lat = None
    lon = None
    if geo:
        country_name = geo.get("country", "") or ""
        country_code = geo.get("country_code", "") or ""
        lat = geo.get("lat")
        lon = geo.get("lon")
    regional_terms = " ".join(x for x in [country_name, place, keywords] if x).strip()
    return {
        "query":          query,
        "hashtag":        hashtag,
        "country_name":   country_name,
        "country_code":   country_code,
        "lat":            lat,
        "lon":            lon,
        "general_search": f"https://www.tiktok.com/search?q={quote(query or place)}",
        "hashtag_search": f"https://www.tiktok.com/tag/{quote(hashtag)}",
        "regional_search":f"https://www.tiktok.com/search?q={quote(regional_terms or query or place)}",
        "maps": build_map_verification_links(lat, lon) if lat is not None and lon is not None else {},
    }


def build_tiktok_user_search(username: str, place: str = "", keywords: str = "") -> Dict[str, str]:
    username = (username or "").replace("@", "").strip()
    place = (place or "").strip()
    keywords = (keywords or "").strip()
    profile_url = f"https://www.tiktok.com/@{quote(username)}" if username else ""
    search_query = " ".join(x for x in [f"@{username}" if username else "", place, keywords] if x).strip()
    google_query = " ".join(x for x in [f"site:tiktok.com/@{username}" if username else "site:tiktok.com", place, keywords] if x).strip()
    return {
        "profile_url":   profile_url,
        "tiktok_search": f"https://www.tiktok.com/search?q={quote(search_query)}" if search_query else "https://www.tiktok.com/search",
        "google_search": f"https://www.google.com/search?q={quote_plus(google_query)}",
        "query":         search_query,
    }


def build_tiktok_verification_links(username: str) -> Dict[str, str]:
    username = (username or "").replace("@", "").strip()
    direct_profile = f"https://www.tiktok.com/@{quote(username)}"
    return {
        "tiktok_profile": direct_profile,
        "wayback":        f"https://web.archive.org/web/*/{quote(direct_profile, safe=':/@')}",
        "google":         f"https://www.google.com/search?q={quote_plus('site:tiktok.com/@' + username)}",
        "yandex":         f"https://yandex.com/search/?text={quote_plus('site:tiktok.com/@' + username)}",
        "urlebird":       f"https://urlebird.com/user/{quote(username)}/",
    }


def _parse_video_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    s = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M UTC", "%Y-%m-%d %H:%M:%S UTC", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def infer_user_location_from_videos(video_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_videos = len(video_results or [])
    valid_rows = [r for r in (video_results or []) if isinstance(r, dict)]
    successful_rows = [
        r for r in valid_rows
        if str(r.get("status", "")).startswith("✅") or r.get("location_created") or r.get("author_region")
    ]
    location_counter: Counter = Counter()
    author_counter: Counter = Counter()
    language_counter: Counter = Counter()
    weighted_scores: Dict[str, float] = defaultdict(float)
    evidence: List[str] = []

    for row in successful_rows:
        loc = (row.get("location_created") or "").upper().strip()
        author_region = (row.get("author_region") or "").upper().strip()
        lang = (row.get("text_language") or "").lower().strip()

        if loc:
            location_counter[loc] += 1
            weighted_scores[loc] += 3.0
        if author_region:
            author_counter[author_region] += 1
            weighted_scores[author_region] += 1.5
        if loc and author_region and loc == author_region:
            weighted_scores[loc] += 1.0
        if lang:
            language_counter[lang] += 1
            for cc in LANG_TO_COUNTRIES.get(lang, []):
                weighted_scores[cc] += 0.35

    videos_with_location = sum(location_counter.values())
    videos_with_author_region = sum(author_counter.values())

    location_counts = []
    for code, count in location_counter.most_common():
        flag, country_name_ar = _country_tuple(code)
        location_counts.append({
            "country_code":    code,
            "country_name_ar": country_name_ar,
            "flag":            flag,
            "count":           count,
        })

    probable_code = ""
    if location_counter:
        probable_code = location_counter.most_common(1)[0][0]
    elif author_counter:
        probable_code = author_counter.most_common(1)[0][0]
    elif weighted_scores:
        probable_code = max(weighted_scores, key=weighted_scores.get)

    probable_flag, probable_country_name_ar = _country_tuple(probable_code)

    confidence = 0
    if probable_code:
        if videos_with_location > 0:
            top_loc_count = location_counter.get(probable_code, 0)
            dominance = top_loc_count / max(videos_with_location, 1)
            author_agreement = (
                author_counter.get(probable_code, 0) / max(videos_with_author_region, 1)
                if videos_with_author_region else 0
            )
            coverage = videos_with_location / max(total_videos, 1)
            confidence = int(round(min(95,
                (dominance * 55) + (coverage * 25) + (author_agreement * 15) +
                (5 if top_loc_count >= 2 else 0)
            )))
        elif videos_with_author_region > 0:
            top_author_count = author_counter.get(probable_code, 0)
            author_share = top_author_count / max(videos_with_author_region, 1)
            confidence = int(round(min(70, (author_share * 45) + 15)))

    if probable_code:
        if location_counter.get(probable_code):
            evidence.append(
                f"أكثر locationCreated تكراراً هو {probable_flag} {probable_country_name_ar} "
                f"بعدد {location_counter[probable_code]} فيديو"
            )
        if author_counter.get(probable_code):
            evidence.append(
                f"author.region يدعم نفس الدولة في {author_counter[probable_code]} فيديو"
            )

    if location_counter and len(location_counter) > 1:
        top_two = location_counter.most_common(2)
        evidence.append(
            f"الترتيب الأعلى للمواقع: {', '.join([f'{code} ({count})' for code, count in top_two])}"
        )

    if language_counter:
        lang, lang_count = language_counter.most_common(1)[0]
        evidence.append(
            f"أكثر لغة محتوى متكررة: {LANGUAGE_NAMES_AR.get(lang, lang)} ({lang_count} فيديو)"
        )

    if total_videos and videos_with_location == 0 and videos_with_author_region == 0:
        evidence.append("لا توجد إشارات locationCreated أو author.region كافية داخل الفيديوهات الحالية")

    return {
        "total_videos":             total_videos,
        "analyzed_videos":          len(successful_rows),
        "videos_with_location":     videos_with_location,
        "videos_with_author_region":videos_with_author_region,
        "probable_country_code":    probable_code,
        "probable_country_name_ar": probable_country_name_ar,
        "probable_flag":            probable_flag,
        "confidence":               confidence,
        "location_counts":          location_counts,
        "location_counts_raw":      dict(location_counter),
        "author_region_counts":     dict(author_counter),
        "language_counts":          dict(language_counter),
        "weighted_scores":          dict(sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)),
        "evidence":                 evidence,
    }


def analyze_timezone_from_videos(video_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    timestamps = []
    for row in (video_results or []):
        dt = _parse_video_datetime(row.get("create_date"))
        if dt:
            timestamps.append(dt)

    if not timestamps:
        return {"error": "no timestamps", "best_offset": None}

    score_by_offset: Dict[int, float] = {}
    hist_by_offset: Dict[int, Counter] = {}
    for offset in range(-12, 15):
        local_hours = [(ts.hour + offset) % 24 for ts in timestamps]
        active  = sum(1 for hour in local_hours if 8 <= hour <= 23)
        evening = sum(1 for hour in local_hours if 18 <= hour <= 23)
        score = (active / len(local_hours)) * 0.75 + (evening / len(local_hours)) * 0.25
        score_by_offset[offset] = round(score, 6)
        hist_by_offset[offset]  = Counter(local_hours)

    best_offset = max(score_by_offset, key=score_by_offset.get)
    confidence  = int(round(score_by_offset[best_offset] * 100))

    top_offsets = []
    for offset, score in sorted(score_by_offset.items(), key=lambda x: x[1], reverse=True)[:5]:
        top_offsets.append({
            "offset":            offset,
            "offset_str":        f"UTC{offset:+d}:00",
            "score":             round(score, 3),
            "confidence":        int(round(score * 100)),
            "candidate_countries": OFFSET_TO_COUNTRIES.get(offset, []),
        })

    return {
        "best_offset":          best_offset,
        "best_offset_str":      f"UTC{best_offset:+d}:00",
        "confidence":           confidence,
        "active_ratio":         round(score_by_offset[best_offset], 3),
        "candidate_countries":  OFFSET_TO_COUNTRIES.get(best_offset, []),
        "score_by_offset":      score_by_offset,
        "histogram_local_hours":dict(hist_by_offset[best_offset]),
        "sample_size":          len(timestamps),
        "top_offsets":          top_offsets,
    }


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a  = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


__all__ = [
    "FAMOUS_LOCATIONS_TT",
    "build_tiktok_search_links",
    "build_tiktok_user_search",
    "build_tiktok_verification_links",
    "build_map_verification_links",
    "geocode_place",
    "reverse_geocode",
    "infer_user_location_from_videos",
    "analyze_timezone_from_videos",
    "get_region_center",
    "haversine_km",
]
