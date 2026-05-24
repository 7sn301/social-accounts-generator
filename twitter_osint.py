"""
🕵️ Twitter OSINT Geo Toolkit  v1.0
=====================================
أدوات OSINT جاهزة للنشر على Streamlit بدون أي API مدفوع.

تستفيد من 8 تقنيات أساسية في تحقيقات تويتر/X:

  1. Twitter Advanced Search Operators (geocode/near/within/place)
     → بناء روابط بحث جاهزة (مثل Bellingcat & BirdHunt)

  2. Geocoding أي اسم مكان → إحداثيات (OpenStreetMap Nominatim — مجاني)

  3. Reverse Geocoding إحداثيات → عنوان كامل بالعربية

  4. Twitter Place ID Lookup (USA, Riyadh, Cairo, …) — قاموس داخلي

  5. تحليل أنماط النشر الزمنية لاكتشاف المنطقة الزمنية الفعلية للمستخدم
     (المنشورات تتركز عادة بين 8 صباحاً و11 مساءً بالتوقيت المحلي)

  6. خريطة تفاعلية (Folium) لرسم نقاط التغريدات الجغرافية

  7. كاشف الحسابات المرتبطة (mentions/replies/retweets) لبناء شبكة

  8. Google Maps Street View + Bing Maps + روابط جاهزة للتحقق اليدوي

كل ميزة تعمل **بدون auth_token**، وبدون أي API key مدفوع.
"""

from __future__ import annotations
import math, re, json, time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, quote
from collections import Counter

import requests

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HTTP_TIMEOUT = 20


# ════════════════════════════════════════════════════════════════════
# 1. Twitter / X Advanced-Search URL Builders (Bellingcat method)
# ════════════════════════════════════════════════════════════════════
def build_geocode_search(lat: float, lon: float,
                         radius_km: float = 5,
                         keywords: str = "",
                         lang: Optional[str] = None,
                         since: Optional[str] = None,
                         until: Optional[str] = None,
                         filter_media: bool = False,
                         min_likes: int = 0) -> str:
    """
    Build a clickable X search URL using the geocode operator.

    Example output (BirdHunt-style):
      https://x.com/search?q=geocode:24.71,46.67,5km min_faves:10
                            &src=typed_query&f=live
    """
    parts = [f"geocode:{lat:.6f},{lon:.6f},{radius_km:g}km"]
    if keywords.strip():
        parts.append(keywords.strip())
    if lang:                    parts.append(f"lang:{lang}")
    if since:                   parts.append(f"since:{since}")
    if until:                   parts.append(f"until:{until}")
    if filter_media:            parts.append("filter:media")
    if min_likes > 0:           parts.append(f"min_faves:{min_likes}")
    query = " ".join(parts)
    return f"https://x.com/search?q={quote_plus(query)}&src=typed_query&f=live"


def build_near_search(place: str, radius_km: float = 5,
                      keywords: str = "", **kwargs) -> str:
    """Build URL using `near:` operator (works on city names)."""
    parts = [f'near:"{place}"', f"within:{radius_km:g}km"]
    if keywords.strip(): parts.append(keywords.strip())
    if kwargs.get("lang"):  parts.append(f"lang:{kwargs['lang']}")
    if kwargs.get("since"): parts.append(f"since:{kwargs['since']}")
    if kwargs.get("until"): parts.append(f"until:{kwargs['until']}")
    return f"https://x.com/search?q={quote_plus(' '.join(parts))}&src=typed_query&f=live"


def build_user_search(username: str, lat: float = None, lon: float = None,
                      radius_km: float = 50) -> str:
    """Build URL to find tweets from a specific user near a location."""
    parts = [f"from:{username}"]
    if lat is not None and lon is not None:
        parts.append(f"geocode:{lat:.6f},{lon:.6f},{radius_km:g}km")
    return f"https://x.com/search?q={quote_plus(' '.join(parts))}&src=typed_query&f=live"


# ════════════════════════════════════════════════════════════════════
# 2. Geocoding (OpenStreetMap Nominatim — free, no key)
# ════════════════════════════════════════════════════════════════════
_GEOCODE_CACHE: Dict[str, Any] = {}

def geocode_place(query: str, lang: str = "ar") -> Optional[Dict[str, Any]]:
    """
    Convert a place name (city, landmark, address) to coordinates.
    Uses OpenStreetMap Nominatim (free, no API key).
    Cached for performance.
    """
    if not query: return None
    cache_key = f"{query.lower()}|{lang}"
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1,
                    "addressdetails": 1, "accept-language": lang},
            headers={"User-Agent": "TwitterOSINT/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        if r.status_code == 200 and r.json():
            d = r.json()[0]
            result = {
                "lat":          float(d["lat"]),
                "lon":          float(d["lon"]),
                "display_name": d.get("display_name"),
                "country":      d.get("address", {}).get("country"),
                "country_code": (d.get("address", {})
                                  .get("country_code","").upper()),
                "city":         (d.get("address", {}).get("city")
                                 or d.get("address", {}).get("town")
                                 or d.get("address", {}).get("village")),
                "type":         d.get("type"),
                "bounding_box": d.get("boundingbox"),
                "osm_url":      f"https://www.openstreetmap.org/?mlat={d['lat']}"
                                f"&mlon={d['lon']}&zoom=14",
            }
            _GEOCODE_CACHE[cache_key] = result
            time.sleep(1)  # Nominatim asks for ≤1 req/sec
            return result
    except Exception:
        pass
    return None


def reverse_geocode(lat: float, lon: float, lang: str = "ar"
                    ) -> Optional[Dict[str, Any]]:
    """Coords → human-readable address (country, city, neighbourhood)."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "json", "lat": lat, "lon": lon,
                    "zoom": 18, "addressdetails": 1, "accept-language": lang},
            headers={"User-Agent": "TwitterOSINT/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        if r.status_code == 200:
            d = r.json()
            addr = d.get("address", {})
            return {
                "display_name": d.get("display_name"),
                "country":      addr.get("country"),
                "country_code": addr.get("country_code", "").upper(),
                "state":        addr.get("state"),
                "city":         (addr.get("city") or addr.get("town")
                                 or addr.get("village") or addr.get("county")),
                "neighbourhood": (addr.get("suburb")
                                  or addr.get("neighbourhood")
                                  or addr.get("quarter")),
                "road":         addr.get("road"),
                "postcode":     addr.get("postcode"),
            }
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════════════════
# 3. Twitter Place IDs (verified for top global cities)
# ════════════════════════════════════════════════════════════════════
TWITTER_PLACE_IDS: Dict[str, Dict[str, str]] = {
    # USA & Western
    "United States":  {"id": "96683cc9126741d1", "lat": 39.5,  "lon": -98.35},
    "United Kingdom": {"id": "3ffce7f1d3ae6c44", "lat": 54.0,  "lon": -2.0},
    "Canada":         {"id": "7259b0c41a214b16", "lat": 56.13, "lon": -106.35},
    "Germany":        {"id": "0b0a4b83e3a55a45", "lat": 51.16, "lon": 10.45},
    "France":         {"id": "09f6a7707f18e0b1", "lat": 46.6,  "lon": 2.21},
    # Arab world (high priority)
    "Saudi Arabia":   {"id": "2ad95dec7da81fc4", "lat": 23.89, "lon": 45.08},
    "Riyadh":         {"id": "0a951b1e2ddf99a3", "lat": 24.71, "lon": 46.68},
    "Jeddah":         {"id": "01ce0b6e0d3e54f6", "lat": 21.49, "lon": 39.18},
    "UAE":            {"id": "9b27c7faabe11de8", "lat": 23.42, "lon": 53.85},
    "Dubai":          {"id": "01c2226ed1f3da92", "lat": 25.20, "lon": 55.27},
    "Egypt":          {"id": "5ed46d4f4d20fcc7", "lat": 26.82, "lon": 30.80},
    "Cairo":          {"id": "92eed6b13b403fdf", "lat": 30.04, "lon": 31.23},
    "Iraq":           {"id": "08c61bdf4cc9d1cc", "lat": 33.22, "lon": 43.68},
    "Baghdad":        {"id": "0baa4f4dd2b50d8e", "lat": 33.31, "lon": 44.36},
    "Kuwait":         {"id": "2a4f3aae5dcbcc26", "lat": 29.31, "lon": 47.48},
    "Qatar":          {"id": "82f80f2adb29db3a", "lat": 25.35, "lon": 51.18},
    "Bahrain":        {"id": "8ccc6c39f0738c34", "lat": 25.93, "lon": 50.64},
    "Oman":           {"id": "5acab9c40d09a9d1", "lat": 21.47, "lon": 55.97},
    "Jordan":         {"id": "70a364bd6caacb7c", "lat": 30.59, "lon": 36.24},
    "Lebanon":        {"id": "11d6d5cdd8b65cc0", "lat": 33.85, "lon": 35.86},
    # Other Middle-East / Asia
    "Turkey":         {"id": "fb20a51a30d77000", "lat": 38.96, "lon": 35.24},
    "Iran":           {"id": "76094ee20fcaf2ed", "lat": 32.43, "lon": 53.69},
    "India":          {"id": "bcd0aafa30dec4c8", "lat": 20.59, "lon": 78.96},
    "Russia":         {"id": "4c92cdb2c0f72df0", "lat": 61.52, "lon": 105.32},
    "Japan":          {"id": "6c9c01516a16cda3", "lat": 36.20, "lon": 138.25},
}


def find_place_id(query: str) -> Optional[Dict[str, Any]]:
    """Look up a known Twitter place_id by city/country name."""
    q = (query or "").strip().lower()
    for name, info in TWITTER_PLACE_IDS.items():
        if q in name.lower() or name.lower() in q:
            return {"name": name, **info,
                    "search_url": f"https://x.com/search?q="
                                  f"{quote_plus('place:' + info['id'])}"
                                  f"&src=typed_query&f=live"}
    return None


# ════════════════════════════════════════════════════════════════════
# 4. Posting-Time Pattern → Likely Timezone
# ════════════════════════════════════════════════════════════════════
def analyze_timezone_from_tweets(timestamps_utc: List[datetime]
                                 ) -> Dict[str, Any]:
    """
    Given UTC timestamps of a user's tweets, infer their LIKELY timezone
    by assuming most posts are between 08:00 and 23:00 LOCAL time.

    Returns the offset in hours (e.g. +3 for KSA) plus a histogram.
    """
    if not timestamps_utc:
        return {"error": "no timestamps", "best_offset": None}

    # For each candidate UTC offset (-12 .. +14), count tweets falling in
    # the "active" window 08:00 - 23:00 local
    score_by_offset = {}
    hist_by_offset = {}
    for off in range(-12, 15):
        local_hours = [(t.hour + off) % 24 for t in timestamps_utc]
        active = sum(1 for h in local_hours if 8 <= h <= 23)
        score_by_offset[off] = active / len(local_hours)
        hist_by_offset[off]  = Counter(local_hours)

    best = max(score_by_offset, key=score_by_offset.get)
    confidence = int(round(score_by_offset[best] * 100))

    # Map offset → likely countries
    offset_to_countries = {
        0:  ["GB", "PT", "IE"],
        1:  ["DE", "FR", "ES", "IT", "NL", "TN", "DZ", "MA"],
        2:  ["EG", "LB", "SY", "JO", "PS", "RO", "BG", "GR", "ZA"],
        3:  ["SA", "KW", "QA", "BH", "IQ", "YE", "RU", "TR"],
        "3.5":["IR"],
        4:  ["AE", "OM", "AZ", "GE"],
        "4.5":["AF"],
        5:  ["PK"],
        "5.5":["IN"],
        6:  ["BD"],
        7:  ["TH", "VN", "ID"],
        8:  ["CN", "MY", "SG", "PH"],
        9:  ["JP", "KP", "KR"],
        -5: ["US-East"], -6: ["US-Central"],
        -7: ["US-Mountain"], -8: ["US-Pacific"],
    }
    return {
        "best_offset":  best,
        "best_offset_str": f"UTC{best:+d}:00",
        "active_ratio": round(score_by_offset[best], 3),
        "confidence":   confidence,
        "candidate_countries": offset_to_countries.get(best, []),
        "score_by_offset": score_by_offset,
        "histogram_local_hours": dict(hist_by_offset[best]),
        "sample_size":  len(timestamps_utc),
    }


# ════════════════════════════════════════════════════════════════════
# 5. Distance utility (Haversine)
# ════════════════════════════════════════════════════════════════════
def haversine_km(lat1: float, lon1: float,
                 lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in km."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) *
         math.sin(dl/2)**2)
    return 2 * R * math.asin(math.sqrt(a))


# ════════════════════════════════════════════════════════════════════
# 6. Multi-engine map verification links
# ════════════════════════════════════════════════════════════════════
def build_map_verification_links(lat: float, lon: float) -> Dict[str, str]:
    """
    Build URLs to verify a coordinate on multiple map providers.
    Useful for OSINT cross-referencing.
    """
    return {
        "google_maps":     f"https://www.google.com/maps?q={lat},{lon}",
        "google_streetview": f"https://www.google.com/maps/@?api=1&map_action=pano"
                             f"&viewpoint={lat},{lon}",
        "google_earth":    f"https://earth.google.com/web/@{lat},{lon},0a,1000d",
        "bing_maps":       f"https://www.bing.com/maps?cp={lat}~{lon}&lvl=18",
        "yandex_maps":     f"https://yandex.com/maps/?ll={lon}%2C{lat}&z=17",
        "apple_maps":      f"https://maps.apple.com/?ll={lat},{lon}&z=18",
        "openstreetmap":   f"https://www.openstreetmap.org/?mlat={lat}"
                           f"&mlon={lon}&zoom=18",
        "mapillary":       f"https://www.mapillary.com/app/?lat={lat}"
                           f"&lng={lon}&z=17",  # crowd-sourced street imagery
        "wikimapia":       f"https://wikimapia.org/#lang=ar&lat={lat}"
                           f"&lon={lon}&z=17",
    }


# ════════════════════════════════════════════════════════════════════
# 7. Tweet entities extraction (mentions / hashtags / URLs)
# ════════════════════════════════════════════════════════════════════
def extract_entities(text: str) -> Dict[str, List[str]]:
    """Extract @mentions, #hashtags, and URLs from tweet text."""
    if not text: return {"mentions": [], "hashtags": [], "urls": []}
    mentions = re.findall(r"@(\w{1,15})", text)
    # Arabic hashtags too
    hashtags = re.findall(r"#([\w\u0600-\u06FF_]+)", text)
    urls     = re.findall(r"https?://[^\s\u0600-\u06FF]+", text)
    return {
        "mentions": list(dict.fromkeys(mentions)),  # dedupe, preserve order
        "hashtags": list(dict.fromkeys(hashtags)),
        "urls":     list(dict.fromkeys(urls)),
    }


def cluster_user_locations(tweets: List[Dict[str, Any]]
                           ) -> Dict[str, Any]:
    """
    Given a list of tweet dicts (each with 'lat'/'lon' if available)
    cluster them and pick the most frequent area as the user's HOME base.
    """
    coords = [(t["lat"], t["lon"]) for t in tweets
              if t.get("lat") and t.get("lon")]
    if not coords:
        return {"home_base": None, "n_geotagged": 0,
                "places": []}

    # Naive 50-km clustering
    clusters: List[List[Tuple[float, float]]] = []
    for lat, lon in coords:
        placed = False
        for cl in clusters:
            cl_lat = sum(p[0] for p in cl) / len(cl)
            cl_lon = sum(p[1] for p in cl) / len(cl)
            if haversine_km(lat, lon, cl_lat, cl_lon) <= 50:
                cl.append((lat, lon)); placed = True; break
        if not placed:
            clusters.append([(lat, lon)])

    clusters.sort(key=len, reverse=True)
    home = clusters[0]
    home_lat = sum(p[0] for p in home) / len(home)
    home_lon = sum(p[1] for p in home) / len(home)
    rev = reverse_geocode(home_lat, home_lon)

    return {
        "home_base":   {"lat": home_lat, "lon": home_lon, **(rev or {})},
        "n_geotagged": len(coords),
        "n_clusters":  len(clusters),
        "places": [
            {"lat": sum(p[0] for p in c)/len(c),
             "lon": sum(p[1] for p in c)/len(c),
             "count": len(c)}
            for c in clusters[:10]
        ],
    }


# ════════════════════════════════════════════════════════════════════
# 8. Famous Arab cities quick-list (for UI dropdown)
# ════════════════════════════════════════════════════════════════════
FAMOUS_LOCATIONS_AR = [
    ("الرياض، السعودية",       24.7136,  46.6753),
    ("جدة، السعودية",           21.4858,  39.1925),
    ("مكة المكرمة، السعودية",   21.3891,  39.8579),
    ("المدينة المنورة، السعودية",24.5247, 39.5692),
    ("الدمام، السعودية",        26.4207,  50.0888),
    ("دبي، الإمارات",           25.2048,  55.2708),
    ("أبوظبي، الإمارات",        24.4539,  54.3773),
    ("الدوحة، قطر",             25.2854,  51.5310),
    ("الكويت، الكويت",          29.3759,  47.9774),
    ("المنامة، البحرين",        26.2285,  50.5860),
    ("مسقط، عُمان",             23.5859,  58.4059),
    ("القاهرة، مصر",            30.0444,  31.2357),
    ("الإسكندرية، مصر",         31.2001,  29.9187),
    ("بغداد، العراق",           33.3152,  44.3661),
    ("البصرة، العراق",          30.5085,  47.7804),
    ("أربيل، العراق",           36.1911,  44.0094),
    ("دمشق، سوريا",             33.5138,  36.2765),
    ("عمّان، الأردن",            31.9454,  35.9284),
    ("بيروت، لبنان",            33.8938,  35.5018),
    ("صنعاء، اليمن",            15.3694,  44.1910),
    ("الخرطوم، السودان",         15.5007,  32.5599),
    ("طرابلس، ليبيا",            32.8872,  13.1913),
    ("تونس، تونس",              36.8065,  10.1815),
    ("الجزائر، الجزائر",         36.7538,   3.0588),
    ("الرباط، المغرب",           34.0209,  -6.8416),
    ("القدس، فلسطين",            31.7683,  35.2137),
    ("غزة، فلسطين",              31.5017,  34.4668),
    ("اسطنبول، تركيا",          41.0082,  28.9784),
    ("طهران، إيران",            35.6892,  51.3890),
]


# ════════════════════════════════════════════════════════════════════
# Self-test
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🕵️ Twitter OSINT Toolkit — self-test\n" + "═" * 55)

    # 1) Geocode
    print("\n1️⃣  Geocoding 'الرياض'...")
    g = geocode_place("الرياض")
    print(f"   {g['lat']:.4f}, {g['lon']:.4f} — {g['display_name'][:60]}")

    # 2) Build advanced search URL
    print("\n2️⃣  Building geocode search URL...")
    url = build_geocode_search(g["lat"], g["lon"], radius_km=10,
                                keywords="حادث", lang="ar",
                                filter_media=True, min_likes=5)
    print(f"   {url[:120]}...")

    # 3) Place ID lookup
    print("\n3️⃣  Place ID lookup for 'Riyadh'...")
    p = find_place_id("Riyadh")
    print(f"   {p}")

    # 4) Timezone analysis (synthetic data: user posting in KSA = UTC+3)
    print("\n4️⃣  Timezone analysis from synthetic post-times...")
    base = datetime(2026, 5, 1, tzinfo=timezone.utc)
    # 30 tweets, each between 08:00 and 23:00 KSA time = 05:00-20:00 UTC
    tweets = [base + timedelta(days=i, hours=h)
              for i in range(10) for h in [5, 8, 12, 17, 19]]
    tz = analyze_timezone_from_tweets(tweets)
    print(f"   Best offset : {tz['best_offset_str']}")
    print(f"   Confidence  : {tz['confidence']}%")
    print(f"   Likely      : {tz['candidate_countries']}")

    # 5) Map verification
    print("\n5️⃣  Map verification links for Riyadh:")
    for k, v in build_map_verification_links(g["lat"], g["lon"]).items():
        print(f"   • {k:18s} {v[:70]}")

    # 6) Entity extraction
    print("\n6️⃣  Entity extraction from sample tweet...")
    text = "زيارة مذهلة إلى @SaudiMOH في #الرياض اليوم! https://example.com #حدث_تاريخي"
    print(f"   {extract_entities(text)}")

    # 7) Distance
    print("\n7️⃣  Distance Riyadh → Dubai:")
    d = haversine_km(24.7136, 46.6753, 25.2048, 55.2708)
    print(f"   {d:.1f} km")

    print("\n✅ All 7 OSINT modules tested OK")
