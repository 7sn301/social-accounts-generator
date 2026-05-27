from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

TWITTER_PLACE_IDS = {
    "riyadh": {"id": "07d9d654f4b6d95f", "name": "Riyadh"},
    "dubai": {"id": "c7d0d7f78c2f7eb4", "name": "Dubai"},
    "cairo": {"id": "be3f7343c3e3b0e1", "name": "Cairo"},
    "doha": {"id": "6d59e4ff84c3a0a2", "name": "Doha"},
    "london": {"id": "6416b8512febefc9", "name": "London"},
    "istanbul": {"id": "e57cce06efea3d88", "name": "Istanbul"},
}

FAMOUS_LOCATIONS_AR = [
    ("الرياض", 24.7136, 46.6753),
    ("جدة", 21.5433, 39.1728),
    ("مكة", 21.3891, 39.8579),
    ("القاهرة", 30.0444, 31.2357),
    ("الإسكندرية", 31.2001, 29.9187),
    ("دبي", 25.2048, 55.2708),
    ("أبوظبي", 24.4539, 54.3773),
    ("الدوحة", 25.2854, 51.5310),
    ("الكويت", 29.3759, 47.9774),
    ("عمّان", 31.9539, 35.9106),
    ("بغداد", 33.3152, 44.3661),
    ("إسطنبول", 41.0082, 28.9784),
    ("لندن", 51.5072, -0.1276),
    ("باريس", 48.8566, 2.3522),
    ("نيويورك", 40.7128, -74.0060),
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _clean_query_parts(parts: Iterable[Optional[str]]) -> str:
    return " ".join(p.strip() for p in parts if p and str(p).strip())


def build_geocode_search(lat: float, lon: float, radius_km: float, keywords: str = "", lang: Optional[str] = None,
                         since: Optional[str] = None, until: Optional[str] = None,
                         filter_media: bool = False, min_likes: int = 0) -> str:
    chunks = []
    if keywords:
        chunks.append(f"({keywords})")
    chunks.append(f"geocode:{lat:.6f},{lon:.6f},{float(radius_km):g}km")
    if lang:
        chunks.append(f"lang:{lang}")
    if since:
        chunks.append(f"since:{since}")
    if until:
        chunks.append(f"until:{until}")
    if filter_media:
        chunks.append("filter:media")
    if min_likes and int(min_likes) > 0:
        chunks.append(f"min_faves:{int(min_likes)}")
    q = _clean_query_parts(chunks)
    return f"https://x.com/search?q={quote(q)}&f=live"


def build_near_search(place: str, radius_km: float, keywords: str = "", lang: Optional[str] = None) -> str:
    chunks = []
    if keywords:
        chunks.append(f"({keywords})")
    chunks.append(f'near:"{place}" within:{float(radius_km):g}km')
    if lang:
        chunks.append(f"lang:{lang}")
    q = _clean_query_parts(chunks)
    return f"https://x.com/search?q={quote(q)}&f=live"


def build_user_search(username: str, lat: Optional[float] = None, lon: Optional[float] = None, radius_km: Optional[float] = None) -> str:
    username = username.strip().lstrip("@")
    q = f"from:{username}"
    if lat is not None and lon is not None and radius_km is not None:
        q += f" geocode:{lat:.6f},{lon:.6f},{float(radius_km):g}km"
    return f"https://x.com/search?q={quote(q)}&f=live"


def geocode_place(query: str) -> Optional[Dict[str, object]]:
    if not query:
        return None
    url = "https://nominatim.openstreetmap.org/search"
    resp = requests.get(url, params={"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1}, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        return None
    data = resp.json() or []
    if not data:
        return None
    item = data[0]
    addr = item.get("address", {})
    return {
        "display_name": item.get("display_name", query),
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "country_code": str(addr.get("country_code", "")).upper(),
        "country": addr.get("country"),
        "state": addr.get("state") or addr.get("region"),
        "city": addr.get("city") or addr.get("town") or addr.get("village"),
    }


def reverse_geocode(lat: float, lon: float) -> Optional[Dict[str, object]]:
    url = "https://nominatim.openstreetmap.org/reverse"
    resp = requests.get(url, params={"lat": lat, "lon": lon, "format": "jsonv2", "addressdetails": 1}, headers=HEADERS, timeout=20)
    if resp.status_code != 200:
        return None
    item = resp.json() or {}
    addr = item.get("address", {})
    return {
        "display_name": item.get("display_name"),
        "country": addr.get("country"),
        "country_code": str(addr.get("country_code", "")).upper(),
        "state": addr.get("state") or addr.get("region"),
        "city": addr.get("city") or addr.get("town") or addr.get("village"),
        "neighbourhood": addr.get("neighbourhood") or addr.get("suburb"),
        "road": addr.get("road"),
        "postcode": addr.get("postcode"),
    }


def find_place_id(place_name: str) -> Optional[Dict[str, str]]:
    key = (place_name or "").strip().lower()
    if key in TWITTER_PLACE_IDS:
        item = TWITTER_PLACE_IDS[key]
        return {
            "id": item["id"],
            "name": item["name"],
            "search_url": f"https://x.com/search?q={quote('place:' + item['id'])}&f=live",
        }
    return None


def build_map_verification_links(lat: float, lon: float) -> Dict[str, str]:
    return {
        "Google Maps": f"https://www.google.com/maps?q={lat},{lon}",
        "Google Earth": f"https://earth.google.com/web/@{lat},{lon},500a,0d,35y,0h,0t,0r",
        "Google Street View": f"https://www.google.com/maps?q&layer=c&cbll={lat},{lon}",
        "Bing Maps": f"https://www.bing.com/maps?cp={lat}~{lon}&lvl=16",
        "Yandex Maps": f"https://yandex.com/maps/?ll={lon}%2C{lat}&z=16",
        "Apple Maps": f"https://maps.apple.com/?ll={lat},{lon}",
        "OpenStreetMap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}",
        "Mapillary": f"https://www.mapillary.com/app/?lat={lat}&lng={lon}&z=16",
        "Wikimapia": f"https://wikimapia.org/#lat={lat}&lon={lon}&z=16",
    }


def extract_entities(text: str) -> Dict[str, List[str]]:
    text = text or ""
    return {
        "mentions": sorted(set(re.findall(r"(?<!\w)@([A-Za-z0-9_]{1,15})", text))),
        "hashtags": sorted(set(re.findall(r"(?<!\w)#([\w\u0600-\u06FF_]+)", text))),
        "urls": sorted(set(re.findall(r"https?://\S+", text))),
    }


def cluster_user_locations(records: List[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, Dict[str, object]] = {}
    for rec in records or []:
        user = str(rec.get("user_screen_name") or rec.get("username") or "").strip().lstrip("@")
        if not user:
            continue
        row = grouped.setdefault(user, {"username": user, "count": 0, "countries": {}, "best_confidence": 0})
        row["count"] += 1
        country = rec.get("region") or rec.get("country")
        if country:
            row["countries"][country] = row["countries"].get(country, 0) + 1
        row["best_confidence"] = max(int(rec.get("region_confidence") or 0), row["best_confidence"])
    out = []
    for user, row in grouped.items():
        countries = row["countries"]
        top_country = max(countries.items(), key=lambda x: x[1])[0] if countries else ""
        out.append({
            "username": user,
            "tweet_count": row["count"],
            "top_country": top_country,
            "country_votes": countries,
            "best_confidence": row["best_confidence"],
        })
    return sorted(out, key=lambda x: (-x["tweet_count"], x["username"]))


def analyze_timezone_from_tweets(timestamps: List[datetime]) -> Dict[str, object]:
    timestamps = [dt.astimezone(timezone.utc) for dt in timestamps if isinstance(dt, datetime)]
    if not timestamps:
        return {
            "best_offset": 0,
            "best_offset_str": "UTC+0",
            "confidence": 0,
            "sample_size": 0,
            "candidate_countries": [],
            "histogram_local_hours": {},
            "score_by_offset": {},
        }
    candidate_offsets = list(range(-12, 15))
    score_by_offset = {}
    best_hist = {}
    for offset in candidate_offsets:
        hist = {}
        score = 0.0
        for dt in timestamps:
            local_hour = (dt.hour + offset) % 24
            hist[local_hour] = hist.get(local_hour, 0) + 1
            if 8 <= local_hour <= 23:
                score += 1.0
            elif 6 <= local_hour < 8 or local_hour == 0:
                score += 0.35
        score /= max(1, len(timestamps))
        score_by_offset[offset] = round(score, 4)
        if score == max(score_by_offset.values()):
            best_hist = hist
    best_offset = max(score_by_offset.items(), key=lambda x: x[1])[0]
    confidence = int(round(max(score_by_offset.values()) * 100))
    tz_candidates = {
        -8: ["الولايات المتحدة", "كندا", "المكسيك"],
        -5: ["الولايات المتحدة", "كندا", "كولومبيا", "بيرو"],
        -3: ["البرازيل", "الأرجنتين", "أوروغواي"],
        0: ["المملكة المتحدة", "البرتغال", "المغرب"],
        1: ["مصر", "ألمانيا", "فرنسا", "إيطاليا"],
        2: ["الأردن", "فلسطين", "اليونان", "رومانيا"],
        3: ["السعودية", "العراق", "الكويت", "قطر", "البحرين", "تركيا"],
        4: ["الإمارات", "عُمان", "أذربيجان"],
        5: ["باكستان", "أوزبكستان"],
        6: ["بنغلاديش"],
        7: ["تايلاند", "فيتنام", "إندونيسيا"],
        8: ["الصين", "سنغافورة", "ماليزيا"],
        9: ["اليابان", "كوريا الجنوبية"],
        10: ["أستراليا"],
    }
    return {
        "best_offset": best_offset,
        "best_offset_str": f"UTC{best_offset:+d}",
        "confidence": confidence,
        "sample_size": len(timestamps),
        "candidate_countries": tz_candidates.get(best_offset, []),
        "histogram_local_hours": {int(k): int(v) for k, v in sorted(best_hist.items())},
        "score_by_offset": score_by_offset,
    }
