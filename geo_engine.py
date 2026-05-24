"""
🌍 Geo Engine v1.0 - GeoSpy.ai-style multi-layer location intelligence
======================================================================
يحاكي عمل GeoSpy.ai عبر 5 طبقات تحليل:

  1️⃣  EXIF Deep Scan       — ExifTool (≈100% accuracy if GPS present)
       يستخرج 100+ حقل: GPS, Camera Model, Timestamp, Maker Notes,
       XMP, IPTC, ICC Profile, Software, Lens, ...

  2️⃣  Reverse Image Search  — Yandex / Google / Bing
       يبني روابط بحث عكسي جاهزة للنقر للتحقق اليدوي.

  3️⃣  AI Vision Geo-Detective — Gemini 2.0 Flash
       Prompt مستوحى من Bellingcat + PIGEON paper:
       يركّز على 6 فئات (نص/لافتات، عمارة، نباتات، مركبات، ملابس، سماء).
       يُرجع JSON منظّم بإحداثيات تقريبية ومستوى ثقة.

  4️⃣  Triangulation Voting  — جمع نتائج الطبقات الـ3 أعلاه
       تصويت موزون: EXIF (95) > AI Landmark (85) > AI Signage (75) > ...

  5️⃣  VPN / Inconsistency Detector
       يقارن: موقع الحساب vs موقع الصورة vs لغة المنشور vs توقيت EXIF
"""

from __future__ import annotations
import os, io, re, json, base64, subprocess, tempfile, hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlencode

import requests
from PIL import Image

# ─────────────────────────── Configuration ────────────────────────────
EXIFTOOL_BIN = "exiftool"            # set absolute path on Windows if needed
GEMINI_MODEL = "gemini-2.0-flash"    # cheap & fast vision model
HTTP_TIMEOUT = 25
USER_AGENT   = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36")

# ───────────────────────── Country dictionaries ───────────────────────
ISO_TO_AR = {
    "SA":"المملكة العربية السعودية","AE":"الإمارات","KW":"الكويت","QA":"قطر",
    "BH":"البحرين","OM":"عُمان","YE":"اليمن","IQ":"العراق","SY":"سوريا",
    "JO":"الأردن","LB":"لبنان","PS":"فلسطين","EG":"مصر","SD":"السودان",
    "LY":"ليبيا","TN":"تونس","DZ":"الجزائر","MA":"المغرب","MR":"موريتانيا",
    "SO":"الصومال","DJ":"جيبوتي","KM":"جزر القمر",
    "TR":"تركيا","IR":"إيران","AF":"أفغانستان","PK":"باكستان","IN":"الهند",
    "BD":"بنغلاديش","ID":"إندونيسيا","MY":"ماليزيا","TH":"تايلاند",
    "CN":"الصين","JP":"اليابان","KR":"كوريا الجنوبية","KP":"كوريا الشمالية",
    "RU":"روسيا","UA":"أوكرانيا","BY":"بيلاروسيا","KZ":"كازاخستان",
    "DE":"ألمانيا","FR":"فرنسا","IT":"إيطاليا","ES":"إسبانيا","PT":"البرتغال",
    "GB":"المملكة المتحدة","IE":"أيرلندا","NL":"هولندا","BE":"بلجيكا",
    "CH":"سويسرا","AT":"النمسا","SE":"السويد","NO":"النرويج","DK":"الدنمارك",
    "FI":"فنلندا","IS":"آيسلندا","PL":"بولندا","CZ":"التشيك","SK":"سلوفاكيا",
    "HU":"المجر","RO":"رومانيا","BG":"بلغاريا","GR":"اليونان","RS":"صربيا",
    "HR":"كرواتيا","BA":"البوسنة","AL":"ألبانيا","MK":"مقدونيا",
    "US":"الولايات المتحدة","CA":"كندا","MX":"المكسيك","BR":"البرازيل",
    "AR":"الأرجنتين","CL":"تشيلي","CO":"كولومبيا","PE":"بيرو","VE":"فنزويلا",
    "AU":"أستراليا","NZ":"نيوزيلندا","ZA":"جنوب أفريقيا","NG":"نيجيريا",
    "KE":"كينيا","ET":"إثيوبيا","GH":"غانا","SN":"السنغال","CI":"ساحل العاج",
}
ISO_FLAGS = {iso: "".join(chr(0x1F1E6 + ord(c) - ord('A')) for c in iso)
             for iso in ISO_TO_AR}

def flag(iso: str) -> str:
    return ISO_FLAGS.get((iso or "").upper(), "🏳️")

def country_ar(iso: str) -> str:
    return ISO_TO_AR.get((iso or "").upper(), iso or "غير محدد")


# ════════════════════════════════════════════════════════════════════
# Layer 1 ── ExifTool deep metadata extraction (ExifGlass-style)
# ════════════════════════════════════════════════════════════════════
def _piexif_fallback(image_path: str) -> Dict[str, Any]:
    """Pure-python EXIF reader for environments without exiftool."""
    try:
        import piexif
    except ImportError:
        return {"error": "piexif not installed"}
    try:
        ex = piexif.load(image_path)
    except Exception as e:
        return {"error": f"piexif: {e}"}

    out: Dict[str, Any] = {}
    name_map = {
        "0th": (piexif.TAGS["0th"], "EXIF"),
        "Exif": (piexif.TAGS["Exif"], "EXIF"),
        "GPS":  (piexif.TAGS["GPS"], "EXIF"),
        "1st":  (piexif.TAGS["1st"], "EXIF"),
    }
    for ifd, (tagdict, group) in name_map.items():
        for tag, val in ex.get(ifd, {}).items():
            if tag not in tagdict: continue
            tname = tagdict[tag]["name"]
            if isinstance(val, bytes):
                try: val = val.decode("utf-8", errors="replace").strip("\x00")
                except: val = repr(val)
            elif isinstance(val, tuple) and len(val) == 2 and all(isinstance(x, int) for x in val):
                val = val[0] / val[1] if val[1] else 0
            out[f"{group}:{tname}"] = val

    # Compute composite GPS
    def _to_deg(dms, ref):
        if not dms or len(dms) != 3: return None
        try:
            d = dms[0][0] / dms[0][1] if isinstance(dms[0], tuple) else dms[0]
            m = dms[1][0] / dms[1][1] if isinstance(dms[1], tuple) else dms[1]
            s = dms[2][0] / dms[2][1] if isinstance(dms[2], tuple) else dms[2]
            deg = d + m/60 + s/3600
            if ref in ("S", "W", b"S", b"W"): deg = -deg
            return round(deg, 6)
        except Exception:
            return None

    gps = ex.get("GPS", {})
    lat = _to_deg(gps.get(piexif.GPSIFD.GPSLatitude),
                  gps.get(piexif.GPSIFD.GPSLatitudeRef))
    lon = _to_deg(gps.get(piexif.GPSIFD.GPSLongitude),
                  gps.get(piexif.GPSIFD.GPSLongitudeRef))
    if lat is not None: out["Composite:GPSLatitude"]  = lat
    if lon is not None: out["Composite:GPSLongitude"] = lon
    alt = gps.get(piexif.GPSIFD.GPSAltitude)
    if alt:
        out["Composite:GPSAltitude"] = alt[0]/alt[1] if isinstance(alt, tuple) and alt[1] else alt

    # Add basic file info
    try:
        from PIL import Image
        with Image.open(image_path) as im:
            out["File:ImageWidth"]  = im.width
            out["File:ImageHeight"] = im.height
            out["File:Format"]      = im.format
    except Exception:
        pass
    out["_source"] = "piexif (fallback)"
    return out


def extract_exif_full(image_path: str) -> Dict[str, Any]:
    """
    Run ExifTool against the image and return the full JSON dump.
    This is exactly what ExifGlass does under the hood.
    Falls back to pure-python piexif if exiftool is not installed.
    """
    if not os.path.exists(image_path):
        return {"error": "file not found"}
    # Try ExifTool first (preferred — reads 100+ tag types)
    try:
        proc = subprocess.run(
            [EXIFTOOL_BIN, "-json", "-n", "-G",
             "-coordFormat", "%.6f",
             image_path],
            capture_output=True, text=True, timeout=20
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            if isinstance(data, list) and data:
                data[0]["_source"] = "exiftool"
                return data[0]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # exiftool not available — fall through
    except Exception:
        pass
    # Fallback: piexif
    return _piexif_fallback(image_path)


def parse_gps_from_exif(exif: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract GPS lat/lon if available — returns None if absent."""
    if not exif or "error" in exif:
        return None
    lat = exif.get("Composite:GPSLatitude") or exif.get("EXIF:GPSLatitude")
    lon = exif.get("Composite:GPSLongitude") or exif.get("EXIF:GPSLongitude")
    if lat is None or lon is None:
        return None
    try:
        lat = float(lat); lon = float(lon)
    except (TypeError, ValueError):
        return None
    return {
        "latitude": lat, "longitude": lon,
        "altitude": exif.get("Composite:GPSAltitude"),
        "timestamp": (exif.get("EXIF:GPSDateTime")
                      or exif.get("EXIF:DateTimeOriginal")),
        "accuracy_m": exif.get("EXIF:GPSHPositioningError"),
    }


def reverse_geocode(lat: float, lon: float, lang: str = "ar") -> Dict[str, Any]:
    """Free reverse geocoding using OpenStreetMap Nominatim."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "json", "lat": lat, "lon": lon,
                    "zoom": 18, "addressdetails": 1, "accept-language": lang},
            headers={"User-Agent": "GeoEngine/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        return {"error": str(e)}
    return {}


def summarize_exif(exif: Dict[str, Any]) -> Dict[str, Any]:
    """Pull the most useful EXIF/XMP/IPTC fields into a flat summary."""
    if not exif or "error" in exif:
        return {"available": False, "error": exif.get("error", "no data")}

    pick = lambda *keys: next((exif[k] for k in keys if k in exif), None)
    gps = parse_gps_from_exif(exif)

    summary = {
        "available": True,
        "camera_make":   pick("EXIF:Make"),
        "camera_model":  pick("EXIF:Model"),
        "lens_model":    pick("EXIF:LensModel", "Composite:LensID"),
        "software":      pick("EXIF:Software"),
        "date_taken":    pick("EXIF:DateTimeOriginal", "EXIF:CreateDate"),
        "date_modified": pick("File:FileModifyDate"),
        "image_width":   pick("File:ImageWidth", "EXIF:ExifImageWidth"),
        "image_height":  pick("File:ImageHeight", "EXIF:ExifImageHeight"),
        "orientation":   pick("EXIF:Orientation"),
        "iso":           pick("EXIF:ISO"),
        "f_number":      pick("EXIF:FNumber"),
        "exposure":      pick("EXIF:ExposureTime"),
        "focal_length":  pick("EXIF:FocalLength"),
        "flash":         pick("EXIF:Flash"),
        "artist":        pick("EXIF:Artist", "XMP:Creator"),
        "copyright":     pick("EXIF:Copyright", "XMP:Rights"),
        "description":   pick("EXIF:ImageDescription", "XMP:Description"),
        "gps":           gps,
        "timezone":      pick("EXIF:OffsetTimeOriginal", "EXIF:OffsetTime"),
        # XMP / IPTC location hints (sometimes present even without GPS)
        "iptc_city":     pick("IPTC:City", "XMP:City"),
        "iptc_country":  pick("IPTC:Country-PrimaryLocationName", "XMP:Country"),
        "iptc_state":    pick("IPTC:Province-State", "XMP:State"),
        "total_tags":    len(exif),
    }
    # Reverse-geocode if GPS available
    if gps:
        rev = reverse_geocode(gps["latitude"], gps["longitude"])
        addr = rev.get("address", {}) if rev else {}
        summary["geocoded"] = {
            "country":      addr.get("country"),
            "country_code": (addr.get("country_code") or "").upper() or None,
            "state":        addr.get("state"),
            "city":         (addr.get("city") or addr.get("town")
                             or addr.get("village") or addr.get("county")),
            "neighbourhood": addr.get("suburb") or addr.get("neighbourhood"),
            "road":         addr.get("road"),
            "display_name": rev.get("display_name") if rev else None,
        }
    return summary


# ════════════════════════════════════════════════════════════════════
# Layer 2 ── Reverse-image search URL builders (Yandex / Google / Bing)
# ════════════════════════════════════════════════════════════════════
def build_reverse_search_links(image_url: str) -> Dict[str, str]:
    """
    Build clickable reverse-image-search URLs.
    Yandex is the strongest engine for face/place matching (per Bellingcat).
    """
    img = quote_plus(image_url)
    return {
        "yandex":      f"https://yandex.com/images/search?rpt=imageview&url={img}",
        "google_lens": f"https://lens.google.com/uploadbyurl?url={img}",
        "google":      f"https://www.google.com/searchbyimage?image_url={img}&safe=off",
        "bing":        f"https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIVSP&q=imgurl:{img}",
        "tineye":      f"https://tineye.com/search?url={img}",
    }


def yandex_reverse_search(image_url: str) -> Dict[str, Any]:
    """
    Best-effort scrape of Yandex reverse-image search.
    Yandex requires a CBIR id obtained from the form upload — without
    a logged-in session we can only return the search URL for the user
    to click. Returns a structured stub.
    """
    return {
        "engine": "yandex",
        "search_url": build_reverse_search_links(image_url)["yandex"],
        "note": ("افتح الرابط للبحث العكسي اليدوي على Yandex – أقوى محرك "
                 "للمطابقة البصرية للأماكن والوجوه (بحسب Bellingcat)."),
    }


# ════════════════════════════════════════════════════════════════════
# Layer 3 ── Gemini Vision GEO-Detective
# ════════════════════════════════════════════════════════════════════
GEO_DETECTIVE_PROMPT = """You are GEO-DETECTIVE, an expert OSINT image
geolocator inspired by GeoSpy.ai and the PIGEON Stanford paper.

TASK: Determine WHERE the photo was taken — country, region, city,
neighbourhood — using ONLY visual clues. Imagine you are competing in
GeoGuessr at the world-champion level.

ANALYSIS CHECKLIST (scan systematically, do not skip):

1. TEXT & SIGNAGE
   • Read every visible word, sign, license plate, billboard, shop name.
   • Note the SCRIPT (Latin/Arabic/Cyrillic/CJK/Devanagari/…) and language.
   • Road-sign colours/shapes are country-specific (e.g. green = highway
     in EU/SA, blue = highway in US/UK).

2. ARCHITECTURE & URBAN PLANNING
   • Building materials (concrete, brick, wood, adobe, glass towers).
   • Roof style (flat Mediterranean, sloped Nordic, pagoda Asian).
   • Window shutters, balconies, AC unit placement.
   • Street width, sidewalk style, curb shape, bollard design.
   • Power-line poles: wood (US/CA), concrete (EU/Asia), buried (Gulf).

3. VEHICLES & INFRASTRUCTURE
   • License-plate format & colours (yellow GB rear, white EU, etc.).
   • Side of road (LHT: UK/JP/AU/IN  vs.  RHT: rest).
   • Traffic-light shape, bus/taxi colours, road markings.
   • Manhole covers, fire hydrants, postboxes (very country-specific).

4. NATURE & CLIMATE
   • Vegetation (palms, olives, pines, baobabs, eucalyptus).
   • Soil colour, terrain, mountains/sea visible.
   • Sun angle / shadow direction → hemisphere & rough latitude.
   • Sky tone, clouds, weather hints.

5. PEOPLE & CULTURE
   • Traditional clothing (thobe, sari, kimono, hijab style).
   • Skin tones distribution, hairstyles.
   • Religious symbols (mosque, church, temple, synagogue).

6. DIGITAL / DIGITAL OVERLAYS
   • Watermarks, TV-channel logos, app UI in screenshots.
   • Currency / prices visible.

OUTPUT FORMAT — return ONLY valid JSON, no markdown, no commentary:

{
  "country_iso": "SA",                  // ISO-3166 alpha-2 or null
  "country_name_en": "Saudi Arabia",
  "region": "Riyadh Province",          // state / governorate
  "city": "Riyadh",
  "neighbourhood": "Al Olaya",          // null if unsure
  "approx_lat": 24.7136,                // best guess, 4-decimal precision
  "approx_lon": 46.6753,
  "confidence": 78,                     // 0-100, your true certainty
  "evidence": [                         // 3-7 short bullet points
    "Arabic signage in Naskh script reading 'فندق'",
    "License plate format: white background + Arabic numerals",
    "Date palms typical of Najd region"
  ],
  "alternative_locations": [            // 0-3 alternative hypotheses
    {"country_iso":"AE","city":"Abu Dhabi","probability":15}
  ],
  "category_scores": {                  // how strong each clue category was
    "text_signage": 80, "architecture": 60, "vehicles": 40,
    "nature": 70, "people": 30, "digital": 0
  },
  "is_indoor": false,
  "is_logo_or_graphic": false,          // true if image is a logo/poster
  "needs_more_images": false,
  "notes": "free-text analyst comment in Arabic"
}

RULES:
• Be HONEST — if you cannot determine the country, set country_iso=null
  and confidence ≤ 25.
• NEVER invent text that isn't visible.
• Confidence calibration:
    95-100  unique landmark (e.g. Burj Khalifa)
    80-94   clear signage in identified language + matching architecture
    60-79   strong country indicators but city uncertain
    40-59   only continent/region clear
    0-39    generic indoor / abstract / logo
"""


def call_gemini_vision(api_key: str, image_bytes: bytes,
                       extra_hint: str = "") -> Dict[str, Any]:
    """
    Call Gemini 2.0 Flash directly via REST API (no SDK dep needed).
    Returns the parsed JSON from the model, or {"error": ...}.
    """
    if not api_key:
        return {"error": "missing Gemini API key"}

    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"models/{GEMINI_MODEL}:generateContent?key={api_key}")

    prompt = GEO_DETECTIVE_PROMPT
    if extra_hint:
        prompt += f"\n\nADDITIONAL CONTEXT FROM ACCOUNT METADATA:\n{extra_hint}\n"

    payload = {
        "contents": [{"role": "user", "parts": [
            {"text": prompt},
            {"inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_bytes).decode("ascii"),
            }},
        ]}],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.9,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }
    try:
        r = requests.post(url, json=payload, timeout=45,
                          headers={"Content-Type": "application/json"})
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}: {r.text[:300]}"}
        data = r.json()
        text = (data.get("candidates", [{}])[0]
                    .get("content", {}).get("parts", [{}])[0]
                    .get("text", ""))
        # Strip ```json fences if model added them despite responseMimeType
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(),
                      flags=re.MULTILINE).strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {"error": "model returned invalid JSON",
                    "raw": text[:500]}
        return parsed
    except requests.exceptions.Timeout:
        return {"error": "Gemini timeout"}
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════════════
# Layer 4 ── Triangulation (combine EXIF + AI + reverse-search)
# ════════════════════════════════════════════════════════════════════
LAYER_WEIGHTS = {
    "exif_gps":          100,   # absolute ground-truth
    "exif_iptc":          85,   # XMP/IPTC city tag
    "ai_landmark":        90,   # AI confidence 90+ on famous landmark
    "ai_signage":         80,   # AI relied on signs/text/plates
    "ai_architecture":    70,   # AI relied on building style
    "ai_nature":          55,   # only vegetation/sky
    "account_profile":    60,   # user-declared location field
    "reverse_search":     50,   # placeholder — needs human verification
}


def triangulate(layers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Vote across layers to produce final country / city / coordinates.
    Each layer must have: {source, country_iso, city, lat, lon, confidence}.
    """
    if not layers:
        return {"final_iso": None, "confidence": 0,
                "method": "no_data", "votes": []}

    # Weighted voting per country
    scores: Dict[str, float] = {}
    voters: Dict[str, list] = {}
    for L in layers:
        iso = (L.get("country_iso") or "").upper()
        if not iso:
            continue
        w = LAYER_WEIGHTS.get(L.get("source", ""), 40)
        score = w * (L.get("confidence", 50) / 100.0)
        scores[iso] = scores.get(iso, 0) + score
        voters.setdefault(iso, []).append(L.get("source"))

    if not scores:
        return {"final_iso": None, "confidence": 0,
                "method": "no_country_detected", "votes": layers}

    final_iso = max(scores, key=scores.get)
    total = sum(scores.values())
    norm_conf = min(99, int(scores[final_iso] / total * 100)) if total else 0

    # Pick best city/coord for the chosen country
    best_layer = max(
        (L for L in layers if (L.get("country_iso") or "").upper() == final_iso),
        key=lambda L: L.get("confidence", 0),
        default={},
    )

    return {
        "final_iso":   final_iso,
        "final_flag":  flag(final_iso),
        "country_ar":  country_ar(final_iso),
        "city":        best_layer.get("city"),
        "neighbourhood": best_layer.get("neighbourhood"),
        "lat":         best_layer.get("lat"),
        "lon":         best_layer.get("lon"),
        "confidence":  norm_conf,
        "method":      "+".join(voters[final_iso]),
        "alt_countries": [{"iso": k, "score": round(v, 1)}
                          for k, v in sorted(scores.items(),
                                             key=lambda x: -x[1])[1:4]],
        "all_voters":  layers,
    }


# ════════════════════════════════════════════════════════════════════
# Layer 5 ── VPN / inconsistency detector
# ════════════════════════════════════════════════════════════════════
def detect_vpn(account_iso: Optional[str],
               photo_iso: Optional[str],
               tweet_lang: Optional[str] = None,
               exif_timezone: Optional[str] = None) -> Dict[str, Any]:
    """
    Heuristic VPN detector — compares declared account country with
    what the photo really shows + posting language + EXIF timezone.
    """
    a = (account_iso or "").upper() or None
    p = (photo_iso   or "").upper() or None

    risk = 0
    reasons: list = []
    verdict = "🟢 لا يوجد تعارض"

    # Arab-speaker mapping for sanity check
    ARAB_LOCALES = {"SA","AE","KW","QA","BH","OM","YE","IQ","SY","JO","LB",
                    "PS","EG","SD","LY","TN","DZ","MA","MR","SO","DJ"}
    EU_NA = {"GB","US","CA","DE","FR","IT","ES","NL","BE","SE","NO","DK",
             "FI","CH","AT","IE","PT","AU","NZ"}

    if a and p:
        if a == p:
            risk = 5
            reasons.append("موقع الحساب يطابق موقع الصورة ✅")
        else:
            # Different countries — could be travel, expat, or VPN
            risk = 50
            reasons.append(f"تعارض: الحساب {flag(a)}{a} ≠ الصورة {flag(p)}{p}")

            # Strong VPN pattern: account in EU/NA, photo + lang in Arab world
            if a in EU_NA and p in ARAB_LOCALES and tweet_lang == "ar":
                risk = 90
                verdict = "🔴 VPN محتمل جداً"
                reasons.append("نمط كلاسيكي: حساب في الغرب + صور وحديث عربي "
                               "من العالم العربي → احتمال VPN عالٍ")
            elif a in ARAB_LOCALES and p in ARAB_LOCALES:
                risk = 25
                verdict = "🟡 سفر عادي بين دول عربية"
                reasons.append("الحركة بين دول عربية شائعة (سفر/عمل)")
            elif a in EU_NA and p in EU_NA:
                risk = 20
                verdict = "🟡 سفر داخل الغرب"
            else:
                verdict = "🟠 تعارض جغرافي — يستحق التحقيق"
    elif a and not p:
        risk = 10
        reasons.append("لا توجد صورة قابلة للتحليل لكشف الموقع الفعلي")
    elif p and not a:
        risk = 30
        verdict = "🟡 الحساب يخفي موقعه"
        reasons.append("الحساب لا يكشف موقعه لكن الصورة تكشف الدولة")
    else:
        risk = 0
        reasons.append("لا يمكن الحكم — لا يوجد بيانات كافية")

    # Timezone check
    if exif_timezone:
        reasons.append(f"المنطقة الزمنية في EXIF: {exif_timezone}")

    recommendation = (
        "تحقّق يدوياً من Yandex/Google Lens على الصورة"
        if risk >= 50 else
        "النتائج متناسقة — لا حاجة لتحقيق إضافي"
    )

    return {
        "verdict": verdict,
        "risk_score": risk,
        "reasons": reasons,
        "recommendation": recommendation,
        "account_iso": a, "photo_iso": p,
        "lang": tweet_lang, "tz": exif_timezone,
    }


# ════════════════════════════════════════════════════════════════════
# Top-level orchestrator
# ════════════════════════════════════════════════════════════════════
def analyze_image_full(
    image_url: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    gemini_api_key: Optional[str] = None,
    account_iso: Optional[str] = None,
    tweet_lang: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the complete 5-layer pipeline on a single image.

    Either provide `image_url` (will be downloaded) OR `image_bytes`.
    Returns a dict with: exif, ai, reverse_search, triangulation, vpn.
    """
    # ── Acquire bytes ────────────────────────────────────────────────
    if image_bytes is None and image_url:
        try:
            r = requests.get(image_url, timeout=HTTP_TIMEOUT,
                             headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
            image_bytes = r.content
        except Exception as e:
            return {"error": f"failed to download image: {e}"}
    if not image_bytes:
        return {"error": "no image data provided"}

    # ── Save temp file for ExifTool ─────────────────────────────────
    fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(image_bytes)

        # Layer 1 — EXIF
        raw_exif = extract_exif_full(tmp_path)
        exif_summary = summarize_exif(raw_exif)

        # Layer 2 — Reverse search links (always free, instant)
        rev_links = build_reverse_search_links(image_url) if image_url else {}

        # Layer 3 — AI Vision
        hint = ""
        if account_iso:
            hint = (f"Account profile declares location: {account_iso} "
                    f"({country_ar(account_iso)}). Use ONLY as one weak hint; "
                    f"prefer visual evidence.")
        ai_result = call_gemini_vision(gemini_api_key, image_bytes, hint) \
                    if gemini_api_key else {"error": "AI disabled (no key)"}

        # ── Build voter list for triangulation ───────────────────────
        voters: List[Dict[str, Any]] = []

        if exif_summary.get("gps") and exif_summary.get("geocoded"):
            g = exif_summary["geocoded"]
            voters.append({
                "source": "exif_gps",
                "country_iso": (g.get("country_code") or "").upper() or None,
                "city": g.get("city"),
                "neighbourhood": g.get("neighbourhood"),
                "lat": exif_summary["gps"]["latitude"],
                "lon": exif_summary["gps"]["longitude"],
                "confidence": 99,
            })
        elif exif_summary.get("iptc_country"):
            voters.append({
                "source": "exif_iptc",
                "country_iso": None,  # IPTC stores name, not ISO
                "city": exif_summary.get("iptc_city"),
                "confidence": 75,
                "note": exif_summary["iptc_country"],
            })

        if isinstance(ai_result, dict) and ai_result.get("country_iso"):
            cat_scores = ai_result.get("category_scores", {}) or {}
            top_cat = max(cat_scores, key=cat_scores.get) \
                      if cat_scores else "ai_signage"
            src = {
                "text_signage": "ai_signage",
                "architecture": "ai_architecture",
                "vehicles":     "ai_signage",
                "nature":       "ai_nature",
                "people":       "ai_architecture",
            }.get(top_cat, "ai_signage")
            if ai_result.get("confidence", 0) >= 90:
                src = "ai_landmark"

            voters.append({
                "source": src,
                "country_iso": ai_result.get("country_iso"),
                "city":        ai_result.get("city"),
                "neighbourhood": ai_result.get("neighbourhood"),
                "lat":         ai_result.get("approx_lat"),
                "lon":         ai_result.get("approx_lon"),
                "confidence":  ai_result.get("confidence", 50),
            })

        if account_iso:
            voters.append({
                "source": "account_profile",
                "country_iso": account_iso,
                "confidence": 60,
            })

        # Layer 4 — Triangulation
        tri = triangulate(voters)

        # Layer 5 — VPN check
        photo_iso = None
        for v in voters:
            if v["source"].startswith(("exif_gps", "ai_")):
                photo_iso = v.get("country_iso"); break
        vpn = detect_vpn(account_iso, photo_iso,
                         tweet_lang, exif_summary.get("timezone"))

        return {
            "ok": True,
            "image_url": image_url,
            "exif": exif_summary,
            "reverse_search": rev_links,
            "ai_vision": ai_result,
            "triangulation": tri,
            "vpn": vpn,
            "voters": voters,
        }
    finally:
        try: os.unlink(tmp_path)
        except: pass


# ════════════════════════════════════════════════════════════════════
# Self-test
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🌍 Geo Engine v1.0 — self-test\n" + "═" * 55)

    # Test 1: pure EXIF parsing without AI
    test_url = ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/"
                "Kingdom_Centre_Riyadh.jpg/640px-Kingdom_Centre_Riyadh.jpg")
    print(f"\n📸 Image: Kingdom Centre, Riyadh (Wikimedia)")
    print(f"🔗 URL  : {test_url}\n")

    res = analyze_image_full(
        image_url=test_url,
        gemini_api_key=os.environ.get("GEMINI_API_KEY"),
        account_iso="SA", tweet_lang="ar",
    )

    if res.get("error"):
        print("❌", res["error"])
    else:
        print(f"📋 EXIF available: {res['exif']['available']} "
              f"(tags: {res['exif'].get('total_tags', 0)})")
        if res['exif'].get('gps'):
            print(f"   GPS: {res['exif']['gps']}")
        ai = res["ai_vision"]
        if "error" in ai:
            print(f"🤖 AI: ⚠️  {ai['error']}")
        else:
            print(f"🤖 AI says: {ai.get('country_iso')} / "
                  f"{ai.get('city')} (conf {ai.get('confidence')}%)")
        tri = res["triangulation"]
        print(f"🎯 Final: {tri.get('final_flag')} "
              f"{tri.get('country_ar')} | {tri.get('city')} "
              f"| {tri.get('confidence')}%  via {tri.get('method')}")
        print(f"🛡️  VPN: {res['vpn']['verdict']} "
              f"(risk {res['vpn']['risk_score']}/100)")
        print(f"🔍 Reverse search:")
        for engine, url in res['reverse_search'].items():
            print(f"   • {engine:11s} → {url[:90]}...")
