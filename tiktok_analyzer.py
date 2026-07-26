from __future__ import annotations

# =============================================================================
# tiktok_analyzer.py — v2.0.0  (Baseer Project — Geo Detection Fix)
# =============================================================================
# Fix ID    : BSR-GEO-FIX-2026-0726-02
# Date      : 2026-07-26
# Author    : Baseer Engineering Committee (Backend + DevOps + QA)
# Purpose   : إصلاح جذري لنظام كشف الموقع الجغرافي في تطبيق "بصير".
#
# سجل التغييرات (Changelog):
#   [FIX-1] طبقة شبكة متعددة الاستراتيجيات (Session + Cookies + Retry + Fallback API).
#   [FIX-2] تحليل JSON من الصفحة عبر عدة مسارات (UNIVERSAL / SIGI / __DEFAULT_SCOPE__ / __NEXT_DATA__).
#   [FIX-3] موازنة add_score_multiple بحد أدنى نقاط (min_per) لمنع تصفير الدول العربية.
#   [FIX-4] عتبة get_winner القابلة للتكيف (adaptive threshold).
#   [FIX-5] توسيع DIALECT_HINTS ليشمل 18 دولة عربية + مؤشرات لهجية معاصرة.
#   [FIX-6] ربط CITY_TO_COUNTRY فعلياً بمسح bio/nickname (سابقاً كان معرَّفاً بلا استخدام).
#   [FIX-7] إرجاع debug_report شفاف يعرض كل الأدلة + كود استجابة HTTP + سبب الفشل.
# =============================================================================

import json
import math
import os
import random
import re
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    Retry = None


# ============================================================
# [FIX-1] طبقة شبكة صلبة — Session + Retry + User-Agent Rotation
# ============================================================

USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
]


def _build_headers(mobile: bool = False) -> Dict[str, str]:
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
    }


def _build_session(proxy: Optional[str] = None) -> requests.Session:
    """Session مع Retry تلقائي + كوكيز أولية تحاكي متصفح حقيقي."""
    s = requests.Session()
    if Retry is not None:
        retry = Retry(
            total=3,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
    # كوكيز افتراضية تُقلّل احتمال الحجب
    s.cookies.set("tt_webid_v2", str(random.randint(10**18, 10**19 - 1)), domain=".tiktok.com")
    s.cookies.set("passport_csrf_token", os.urandom(16).hex(), domain=".tiktok.com")
    if proxy:
        s.proxies.update({"http": proxy, "https": proxy})
    elif os.environ.get("TIKTOK_PROXY"):
        p = os.environ["TIKTOK_PROXY"]
        s.proxies.update({"http": p, "https": p})
    return s


# ============================================================
# قواميس المرجعية (تم توسيعها في هذه النسخة)
# ============================================================

TIKTOK_REGION_MAP = {
    "US": ("🇺🇸", "الولايات المتحدة"), "GB": ("🇬🇧", "المملكة المتحدة"),
    "SA": ("🇸🇦", "السعودية"), "AE": ("🇦🇪", "الإمارات"), "EG": ("🇪🇬", "مصر"),
    "IQ": ("🇮🇶", "العراق"), "JO": ("🇯🇴", "الأردن"), "KW": ("🇰🇼", "الكويت"),
    "QA": ("🇶🇦", "قطر"), "BH": ("🇧🇭", "البحرين"), "OM": ("🇴🇲", "عُمان"),
    "SY": ("🇸🇾", "سوريا"), "LB": ("🇱🇧", "لبنان"), "MA": ("🇲🇦", "المغرب"),
    "TN": ("🇹🇳", "تونس"), "DZ": ("🇩🇿", "الجزائر"), "LY": ("🇱🇾", "ليبيا"),
    "YE": ("🇾🇪", "اليمن"), "SD": ("🇸🇩", "السودان"), "SO": ("🇸🇴", "الصومال"),
    "PS": ("🇵🇸", "فلسطين"), "MR": ("🇲🇷", "موريتانيا"), "DJ": ("🇩🇯", "جيبوتي"),
    "KM": ("🇰🇲", "جزر القمر"),
    "TR": ("🇹🇷", "تركيا"), "IN": ("🇮🇳", "الهند"), "PK": ("🇵🇰", "باكستان"),
    "ID": ("🇮🇩", "إندونيسيا"), "PH": ("🇵🇭", "الفلبين"), "TH": ("🇹🇭", "تايلاند"),
    "VN": ("🇻🇳", "فيتنام"), "MY": ("🇲🇾", "ماليزيا"), "SG": ("🇸🇬", "سنغافورة"),
    "JP": ("🇯🇵", "اليابان"), "KR": ("🇰🇷", "كوريا الجنوبية"), "CN": ("🇨🇳", "الصين"),
    "RU": ("🇷🇺", "روسيا"), "DE": ("🇩🇪", "ألمانيا"), "FR": ("🇫🇷", "فرنسا"),
    "IT": ("🇮🇹", "إيطاليا"), "ES": ("🇪🇸", "إسبانيا"), "BR": ("🇧🇷", "البرازيل"),
    "MX": ("🇲🇽", "المكسيك"), "CA": ("🇨🇦", "كندا"), "AU": ("🇦🇺", "أستراليا"),
    "NG": ("🇳🇬", "نيجيريا"), "ZA": ("🇿🇦", "جنوب أفريقيا"), "NL": ("🇳🇱", "هولندا"),
    "SE": ("🇸🇪", "السويد"), "NO": ("🇳🇴", "النرويج"), "PL": ("🇵🇱", "بولندا"),
    "UA": ("🇺🇦", "أوكرانيا"), "GR": ("🇬🇷", "اليونان"), "PT": ("🇵🇹", "البرتغال"),
    "BE": ("🇧🇪", "بلجيكا"), "AT": ("🇦🇹", "النمسا"), "CH": ("🇨🇭", "سويسرا"),
    "IL": ("🇮🇱", "إسرائيل"), "IR": ("🇮🇷", "إيران"), "BD": ("🇧🇩", "بنغلاديش"),
    "MM": ("🇲🇲", "ميانمار"), "NP": ("🇳🇵", "نيبال"), "LK": ("🇱🇰", "سريلانكا"),
    "ET": ("🇪🇹", "إثيوبيا"), "GH": ("🇬🇭", "غانا"), "KE": ("🇰🇪", "كينيا"),
    "TZ": ("🇹🇿", "تنزانيا"), "CL": ("🇨🇱", "تشيلي"), "PE": ("🇵🇪", "بيرو"),
    "AR": ("🇦🇷", "الأرجنتين"), "CO": ("🇨🇴", "كولومبيا"), "VE": ("🇻🇪", "فنزويلا"),
    "EC": ("🇪🇨", "الإكوادور"), "NZ": ("🇳🇿", "نيوزيلندا"), "IE": ("🇮🇪", "أيرلندا"),
}

LANGUAGE_NAMES_AR = {
    "ar": "العربية", "en": "الإنجليزية", "fr": "الفرنسية", "de": "الألمانية", "es": "الإسبانية",
    "pt": "البرتغالية", "tr": "التركية", "ur": "الأردية", "hi": "الهندية", "id": "الإندونيسية",
    "ms": "الماليزية", "tl": "التاغالوغية", "th": "التايلاندية", "vi": "الفيتنامية",
    "ja": "اليابانية", "ko": "الكورية", "zh": "الصينية", "ru": "الروسية",
}

LANG_TO_COUNTRIES = {
    "ar": ["SA", "EG", "AE", "IQ", "JO", "KW", "QA", "BH", "OM", "SY", "LB",
           "MA", "DZ", "TN", "LY", "SD", "SO", "YE", "PS", "MR"],
    "tr": ["TR"], "ja": ["JP"], "ko": ["KR"], "th": ["TH"], "vi": ["VN"],
    "id": ["ID"], "ms": ["MY"], "tl": ["PH"], "hi": ["IN"], "ur": ["PK"],
    "de": ["DE", "AT", "CH"], "fr": ["FR", "BE", "CH", "MA", "DZ", "TN"],
    "pt": ["BR", "PT"], "ru": ["RU", "UA"], "zh": ["CN"], "en": ["US", "GB", "CA", "AU", "NZ", "IE"],
}

CITY_TO_COUNTRY = {
    # السعودية
    "riyadh": "SA", "jeddah": "SA", "mecca": "SA", "medina": "SA", "dammam": "SA", "khobar": "SA",
    "الرياض": "SA", "جدة": "SA", "مكة": "SA", "المدينة": "SA", "الدمام": "SA", "الخبر": "SA",
    # مصر
    "cairo": "EG", "alexandria": "EG", "giza": "EG", "mansoura": "EG", "aswan": "EG",
    "القاهرة": "EG", "الإسكندرية": "EG", "اسكندرية": "EG", "الجيزة": "EG", "المنصورة": "EG", "أسوان": "EG",
    # الإمارات
    "dubai": "AE", "abu dhabi": "AE", "sharjah": "AE", "ajman": "AE",
    "دبي": "AE", "أبوظبي": "AE", "ابوظبي": "AE", "الشارقة": "AE", "عجمان": "AE",
    # العراق
    "baghdad": "IQ", "basra": "IQ", "mosul": "IQ", "erbil": "IQ", "najaf": "IQ", "karbala": "IQ",
    "بغداد": "IQ", "البصرة": "IQ", "الموصل": "IQ", "أربيل": "IQ", "النجف": "IQ", "كربلاء": "IQ",
    # الأردن / الكويت / قطر / سوريا / لبنان
    "amman": "JO", "عمّان": "JO", "عمان": "JO",
    "kuwait": "KW", "الكويت": "KW",
    "doha": "QA", "الدوحة": "QA",
    "damascus": "SY", "aleppo": "SY", "دمشق": "SY", "حلب": "SY",
    "beirut": "LB", "بيروت": "LB", "طرابلس": "LB",
    # المغرب / تونس / الجزائر / ليبيا
    "rabat": "MA", "casablanca": "MA", "marrakech": "MA", "fes": "MA",
    "الرباط": "MA", "الدار البيضاء": "MA", "مراكش": "MA", "فاس": "MA",
    "tunis": "TN", "تونس": "TN", "sfax": "TN", "صفاقس": "TN",
    "algiers": "DZ", "الجزائر": "DZ", "oran": "DZ", "وهران": "DZ",
    "tripoli": "LY", "benghazi": "LY", "طرابلس ليبيا": "LY", "بنغازي": "LY",
    # اليمن / السودان / فلسطين / عُمان / البحرين
    "sanaa": "YE", "aden": "YE", "صنعاء": "YE", "عدن": "YE",
    "khartoum": "SD", "الخرطوم": "SD",
    "gaza": "PS", "ramallah": "PS", "غزة": "PS", "رام الله": "PS", "القدس": "PS",
    "muscat": "OM", "مسقط": "OM",
    "manama": "BH", "المنامة": "BH",
    # تركيا / إيران
    "istanbul": "TR", "ankara": "TR", "izmir": "TR",
    "اسطنبول": "TR", "إسطنبول": "TR", "أنقرة": "TR", "أزمير": "TR",
    "tehran": "IR", "طهران": "IR",
    # عواصم غربية شائعة
    "london": "GB", "manchester": "GB",
    "new york": "US", "los angeles": "US", "chicago": "US",
    "paris": "FR", "باريس": "FR",
    "berlin": "DE", "برلين": "DE",
    "toronto": "CA", "sydney": "AU",
}

# [FIX-5] توسيع كبير لقاعدة اللهجات — 18 دولة عربية بكلمات معاصرة
DIALECT_HINTS = {
    "SA": ["والله", "مره", "مرة", "ياخي", "يالربع", "وش", "مو", "جيك", "كذا", "شخبارك",
           "ابغى", "ابي", "زين", "طاف", "قهر", "طقطقة"],
    "EG": ["ازيك", "ازاي", "عامل ايه", "جدع", "أوي", "اوي", "مش كده", "بتاع", "كده",
           "خالص", "يلا", "معلش", "دلوقتي", "فين", "ازاى"],
    "AE": ["وايد", "شو", "هالشي", "هاي", "شحالك", "خيتو", "خيوو", "زين", "عيل"],
    "IQ": ["شلونك", "شلون", "هواي", "زود", "اشكد", "شبيك", "خوش", "همين", "هسه", "هسا", "اكو", "ماكو"],
    "JO": ["كتير", "هسا", "شو", "زلمة", "يعطيك العافية", "شغلة"],
    "KW": ["شلون", "وايد", "يعني", "چم", "شخبارك", "عيال"],
    "QA": ["شحالك", "شخبارك", "وايد"],
    "BH": ["شخبارك", "شنو", "وايد"],
    "OM": ["شخبارك", "بومسك", "كيفك"],
    "SY": ["كتير", "شو", "لهون", "منيح", "طيّب", "هلق", "شلون"],
    "LB": ["كتير", "شو", "هيدا", "هيدي", "منيح", "معلش", "يلا"],
    "PS": ["اشي", "زلمة", "منيح", "شو", "كتير", "هسا"],
    "MA": ["واخا", "بزاف", "دابا", "خويا", "زعما", "شنو", "غا", "دير", "ليا", "الله يعطيك الصحة", "درهم"],
    "DZ": ["واش", "بصح", "برك", "خويا", "دير", "كيما", "علاش", "نتاع", "زعما"],
    "TN": ["برشا", "علاش", "شنية", "خويا", "باهي", "ياسر", "قداش", "توا"],
    "LY": ["هلبة", "شن", "كيف", "متاعك", "بزاف"],
    "YE": ["ذمار", "قدح", "معك", "شبك", "كيفك"],
    "SD": ["ياخي", "شديد", "زول", "كيفنك", "دايراً"],
}

USERNAME_PATTERNS = {
    "SA": ["_ksa", "ksa_", "saudi", "riyadh", "jeddah", "makkah", "dammam"],
    "EG": ["_egypt", "egypt_", "cairo", "alex", "_eg", "eg_", "masry", "masr"],
    "AE": ["_uae", "uae_", "dubai", "abudhabi", "sharjah", "emirates"],
    "IQ": ["_iraq", "iraq_", "baghdad", "basra", "_iq", "iq_"],
    "JO": ["_jordan", "jordan_", "amman", "_jo"],
    "KW": ["_kuwait", "kuwait_", "_kw"],
    "QA": ["_qatar", "qatar_", "doha", "_qa"],
    "MA": ["_morocco", "morocco_", "maroc", "casa", "rabat"],
    "DZ": ["_algeria", "algeria_", "algerie", "_dz"],
    "TN": ["_tunisia", "tunisia_", "tunisie", "_tn"],
    "TR": ["_turkey", "turkey_", "turk", "istanbul", "_tr"],
    "US": ["_usa", "usa_", "_us"],
    "GB": ["_uk", "uk_", "london"],
}


# ============================================================
# أدوات مساعدة
# ============================================================

def _safe_region(code: str) -> str:
    if not code or not isinstance(code, str):
        return ""
    code = code.strip().upper()
    return code if code in TIKTOK_REGION_MAP else ""


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        s = str(value).strip().replace(",", "")
        if not s:
            return default
        return int(float(s))
    except Exception:
        return default


def format_count(num: Any) -> str:
    n = _safe_int(num, 0)
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}".rstrip("0").rstrip(".") + "B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 1_000:
        return f"{n/1_000:.1f}".rstrip("0").rstrip(".") + "K"
    return str(n)


def _extract_json_object(text: str, marker: str) -> Optional[dict]:
    idx = text.find(marker)
    if idx == -1:
        return None
    start = text.find("{", idx)
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    raw = text[start:i + 1]
                    try:
                        return json.loads(raw)
                    except Exception:
                        return None
    return None


# [FIX-2] تحليل JSON من الصفحة عبر عدة مسارات
def _parse_script_json(html: str) -> Dict[str, Any]:
    if not html:
        return {}
    candidates = [
        "__UNIVERSAL_DATA_FOR_REHYDRATION__",
        "SIGI_STATE",
        "__NEXT_DATA__",
    ]
    for script_id in candidates:
        m = re.search(
            rf'<script[^>]*id="{re.escape(script_id)}"[^>]*>(.*?)</script>',
            html, re.DOTALL,
        )
        if m:
            raw = m.group(1).strip()
            try:
                return json.loads(raw)
            except Exception:
                pass
    for marker in ('"__DEFAULT_SCOPE__"', '"webapp.user-detail"', '"UserModule"'):
        obj = _extract_json_object(html, marker)
        if obj:
            return obj
    return {}


def _ts_to_date(ts: Any) -> str:
    ts_int = _safe_int(ts, 0)
    if ts_int <= 0:
        return ""
    if ts_int > 10_000_000_000:
        ts_int //= 1000
    try:
        return datetime.fromtimestamp(ts_int, tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return ""


# ============================================================
# [FIX-3, FIX-4] نظام كشف الموقع المُحدَّث
# ============================================================

class LocationDetector:
    def __init__(self):
        self.scores: Dict[str, int] = {}
        self.evidence: List[str] = []
        self.debug: List[str] = []

    def add_score(self, country_code: str, points: int, source: str):
        if not country_code or points <= 0:
            return
        self.scores[country_code] = self.scores.get(country_code, 0) + points
        self.evidence.append(f"{source} → {country_code} (+{points})")

    def add_score_multiple(self, countries: List[str], points: int, source: str, min_per: int = 5):
        """[FIX-3] لا نُقسّم بالتساوي — نُطبّق حد أدنى per=max(points//N, min_per)."""
        if not countries or points <= 0:
            return
        n = len(countries)
        per = max(points // n, min_per) if n > 1 else points
        for cc in countries:
            self.scores[cc] = self.scores.get(cc, 0) + per
        self.evidence.append(f"{source} → [{','.join(countries[:5])}{'...' if n > 5 else ''}] (+{per} لكل دولة)")

    def get_winner(self, threshold: int = 15):
        """[FIX-4] عتبة قابلة للتكيف: تُخفَّض تلقائياً إن كان مجموع النقاط ضعيفاً."""
        if not self.scores:
            return None, 0, []
        sorted_c = sorted(self.scores.items(), key=lambda x: -x[1])
        top, score = sorted_c[0]
        total = sum(self.scores.values())
        # عتبة ديناميكية: لا تقل عن 8 نقاط، ولا تتجاوز threshold
        effective = min(threshold, max(8, total // 5))
        if score < effective:
            return None, 0, [c for c, _ in sorted_c[:5]]
        confidence = min(int((score / total) * 100), 100)
        if len(sorted_c) > 1 and score >= sorted_c[1][1] * 2:
            confidence = min(confidence + 5, 100)
        candidates = [c for c, _ in sorted_c[:3] if c != top]
        return top, confidence, candidates


# [FIX-6] فحص المدن مربوط فعلياً — تُستدعى من داخل detect_country_from_text
def detect_country_from_text(text: str, source_name: str, detector: LocationDetector, base: int = 30):
    if not text:
        return
    text_lower = text.lower()

    # 1) الأعلام (أقوى إشارة نصية)
    for cc, (flag, _) in TIKTOK_REGION_MAP.items():
        if flag and flag in text:
            detector.add_score(cc, base + 30, f"🚩 علم {cc} في {source_name}")
            return

    # 2) المدن — نمر على الكل ونجمع (بدلاً من return مبكر)
    city_matched = False
    for kw in sorted(CITY_TO_COUNTRY.keys(), key=len, reverse=True):
        cc = CITY_TO_COUNTRY[kw]
        matched = False
        if any(ord(c) > 127 for c in kw):
            if kw in text:
                matched = True
        else:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                matched = True
        if matched:
            detector.add_score(cc, base + 20, f"🏙️ '{kw}' في {source_name}")
            city_matched = True

    # 3) اللهجات
    for cc, words in DIALECT_HINTS.items():
        hits = sum(1 for w in words if w in text)
        if hits:
            detector.add_score(cc, base + min(hits * 6, 24), f"🗣️ {hits} كلمة لهجة {cc} في {source_name}")

    # 4) أنماط اسم المستخدم
    for cc, pats in USERNAME_PATTERNS.items():
        hits = sum(1 for p in pats if p in text_lower)
        if hits:
            detector.add_score(cc, base + min(hits * 7, 20), f"👤 نمط اسم {cc} في {source_name}")


def _extract_profile_objects(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    user, stats = {}, {}
    if not data:
        return user, stats

    scope = data.get("__DEFAULT_SCOPE__", {}) if isinstance(data, dict) else {}
    if scope:
        user_detail = scope.get("webapp.user-detail", {}) or {}
        user_info = user_detail.get("userInfo", {}) or {}
        user = user_info.get("user", {}) or {}
        stats = user_info.get("stats", {}) or {}
        if not user:
            share_user = scope.get("webapp.reflow.global.shareUser", {}) or {}
            user = share_user.get("user", {}) or {}
            stats = share_user.get("stats", {}) or stats

    if not user:
        um = (data.get("UserModule", {}) or {}).get("users", {}) if isinstance(data, dict) else {}
        if isinstance(um, dict) and um:
            user = next(iter(um.values())) or {}
        sm = (data.get("UserModule", {}) or {}).get("stats", {}) if isinstance(data, dict) else {}
        if isinstance(sm, dict) and sm:
            stats = next(iter(sm.values())) or {}

    # __NEXT_DATA__ style
    if not user and isinstance(data, dict):
        props = data.get("props", {}).get("pageProps", {})
        if isinstance(props, dict):
            user = props.get("userInfo", {}).get("user", {}) or user
            stats = props.get("userInfo", {}).get("stats", {}) or stats

    return user or {}, stats or {}


def _build_default_profile(username: str) -> Dict[str, Any]:
    return {
        "username": username.lstrip("@"),
        "user_id": "",
        "sec_uid": "",
        "profile_url": f"https://www.tiktok.com/@{username.lstrip('@')}",
        "nickname": "",
        "signature": "",
        "follower_count": 0,
        "following_count": 0,
        "heart_count": 0,
        "video_count": 0,
        "follower_count_formatted": "0",
        "verified": False,
        "private_account": False,
        "is_organization": False,
        "avatar_medium": "",
        "region": "",
        "region_flag": "",
        "region_name_ar": "",
        "region_source": "",
        "region_confidence": 0,
        "region_evidence": "",
        "language": "",
        "language_name_ar": "",
        "create_date": "",
        "bio_link": "",
        "candidates": "",
        "status": "⚠️ معلومات محدودة",
        "error": "",
        # [FIX-7] تقرير تصحيح شفاف
        "debug_report": {
            "http_status": 0,
            "html_length": 0,
            "json_parsed": False,
            "user_found": False,
            "attempts": [],
            "all_evidence": [],
            "all_scores": {},
        },
    }


# ============================================================
# [FIX-1] جلب البروفايل عبر عدة استراتيجيات
# ============================================================

def _fetch_with_strategy(session: requests.Session, url: str, mobile: bool,
                         referer: Optional[str], timeout: int) -> Tuple[int, str]:
    headers = _build_headers(mobile=mobile)
    if referer:
        headers["Referer"] = referer
        headers["Sec-Fetch-Site"] = "same-origin"
    r = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    return r.status_code, (r.text or "")


def fetch_tiktok_profile(username: str, timeout: int = 20,
                         proxy: Optional[str] = None) -> Dict[str, Any]:
    username = (username or "").strip().lstrip("@")
    result = _build_default_profile(username)
    if not username:
        result["error"] = "اسم المستخدم فارغ"
        return result

    session = _build_session(proxy=proxy)
    debug = result["debug_report"]

    # قائمة استراتيجيات بترتيب الأولوية
    strategies = [
        ("desktop_direct", f"https://www.tiktok.com/@{quote(username)}", False, None),
        ("desktop_google", f"https://www.tiktok.com/@{quote(username)}", False, "https://www.google.com/"),
        ("mobile_direct",  f"https://m.tiktok.com/@{quote(username)}",  True,  None),
    ]

    html = ""
    status = 0
    for name, url, mobile, referer in strategies:
        try:
            status, html = _fetch_with_strategy(session, url, mobile, referer, timeout)
            debug["attempts"].append({"name": name, "status": status, "len": len(html)})
            if status == 200 and html and len(html) > 5000:
                # نتحقق من وجود مؤشر JSON قبل قبول الاستجابة
                if any(k in html for k in ("__UNIVERSAL_DATA_FOR_REHYDRATION__",
                                           "webapp.user-detail", "SIGI_STATE", "__NEXT_DATA__")):
                    break
            time.sleep(random.uniform(0.4, 0.9))
        except requests.Timeout:
            debug["attempts"].append({"name": name, "status": -1, "error": "timeout"})
        except requests.ConnectionError as e:
            debug["attempts"].append({"name": name, "status": -2, "error": f"conn: {str(e)[:80]}"})
        except Exception as e:
            debug["attempts"].append({"name": name, "status": -3, "error": str(e)[:80]}) 

    debug["http_status"] = status
    debug["html_length"] = len(html)

    if not html:
        result["error"] = f"فشل جلب البيانات من TikTok (كود آخر محاولة: {status})"
        result["status"] = "❌ فشل شبكي"
        return result

    if status in (403, 429):
        result["error"] = f"TikTok يحجب الطلب (HTTP {status}). جرّب Proxy سكني."
        result["status"] = "🚫 محجوب"
        # نُكمل — قد يكون HTML مفيداً جزئياً

    try:
        data = _parse_script_json(html)
        debug["json_parsed"] = bool(data)
        user, stats = _extract_profile_objects(data)
        debug["user_found"] = bool(user)

        result.update({
            "user_id": str(user.get("id") or user.get("uid") or ""),
            "sec_uid": user.get("secUid") or user.get("sec_uid") or "",
            "nickname": user.get("nickname") or user.get("displayName") or "",
            "signature": user.get("signature") or user.get("bio") or "",
            "verified": bool(user.get("verified") or user.get("isVerified")),
            "private_account": bool(user.get("privateAccount") or user.get("private_account")),
            "is_organization": bool(user.get("commerceUserInfo") or user.get("isOrganization")),
            "avatar_medium": (user.get("avatarMedium") or user.get("avatarThumb")
                              or user.get("avatarLarger") or ""),
            "bio_link": (user.get("bioLink", {}).get("link")
                         if isinstance(user.get("bioLink"), dict)
                         else (user.get("bioLink") or user.get("bio_link") or "")),
            "language": (user.get("language") or user.get("lang") or "").lower(),
            "create_date": _ts_to_date(user.get("createTime") or user.get("create_time") or user.get("id")),
            "follower_count": _safe_int(stats.get("followerCount") or stats.get("followers")
                                        or stats.get("follower_count")),
            "following_count": _safe_int(stats.get("followingCount") or stats.get("following")
                                         or stats.get("following_count")),
            "heart_count": _safe_int(stats.get("heartCount") or stats.get("heart")
                                     or stats.get("heart_count")),
            "video_count": _safe_int(stats.get("videoCount") or stats.get("videos")
                                     or stats.get("video_count")),
        })
        result["follower_count_formatted"] = format_count(result["follower_count"])
        result["language_name_ar"] = LANGUAGE_NAMES_AR.get(result["language"], result["language"])

        # ============ كشف الموقع ============
        detector = LocationDetector()

        # 1) إشارة مباشرة من TikTok API
        direct_region = _safe_region(user.get("region") or stats.get("region") or "")
        if direct_region:
            detector.add_score(direct_region, 1000, "📡 TikTok API region")

        # 2) [FIX-6] المدن + اللهجات + الأعلام في bio / nickname / username
        detect_country_from_text(result["signature"], "bio", detector, base=30)
        detect_country_from_text(result["nickname"], "nickname", detector, base=20)
        detect_country_from_text(result["username"], "username", detector, base=15)

        # 3) استنتاج من اللغة
        lang_countries = LANG_TO_COUNTRIES.get(result["language"], [])
        if len(lang_countries) == 1:
            detector.add_score(lang_countries[0], 30, f"🌐 language={result['language']}")
        elif len(lang_countries) > 1:
            # [FIX-3] min_per يضمن ألا تصفر الدول العربية
            detector.add_score_multiple(lang_countries, 30, f"🌐 language={result['language']}", min_per=3)

        # 4) استنتاج القرار
        winner, confidence, candidates = detector.get_winner(threshold=15)

        # [FIX-7] احفظ كل الأدلة والنقاط في debug_report
        debug["all_evidence"] = list(detector.evidence)
        debug["all_scores"] = dict(sorted(detector.scores.items(), key=lambda x: -x[1]))

        if winner:
            has_api = any(ev.startswith("📡 TikTok API region") for ev in detector.evidence)
            capped = confidence if has_api else min(confidence, 60)

            if not has_api and capped < 35:
                result["region"] = ""
                result["region_flag"] = "🌍"
                result["region_name_ar"] = "غير محدد (تحليل ضعيف)"
                result["region_confidence"] = capped
                result["region_source"] = "❓ استنتاج غير مؤكد"
                result["region_evidence"] = " | ".join(detector.evidence[:5])
                result["candidates"] = "|".join([winner] + candidates)
            else:
                result["region"] = winner
                flag, name_ar = TIKTOK_REGION_MAP.get(winner, ("🌍", winner))
                result["region_flag"] = flag
                result["region_name_ar"] = name_ar
                result["region_confidence"] = capped
                result["region_source"] = "📡 TikTok API" if has_api else "🧠 تحليل ذكي (v2.0)"
                result["region_evidence"] = " | ".join(detector.evidence[:5])
                if candidates:
                    result["candidates"] = "|".join(candidates)
        else:
            result["candidates"] = "|".join(candidates)
            result["region_source"] = "دول محتملة" if candidates else "لا توجد أدلة كافية"
            result["region_evidence"] = " | ".join(detector.evidence[:3])
            result["region"] = ""
            result["region_flag"] = "🌍"
            result["region_name_ar"] = "غير محدد"
            result["region_confidence"] = 0

        if result["user_id"] or result["nickname"]:
            result["status"] = "✅ نجح"
        else:
            result["status"] = "⚠️ معلومات محدودة"

    except Exception as e:
        result["error"] = f"خطأ تحليل: {str(e)[:200]}"
        result["status"] = "⚠️ خطأ في التحليل"

    return result


# ============================================================
# تحليل فيديو محدد (مع نفس تحسينات الشبكة)
# ============================================================

def analyze_tiktok_video(video_url: str, timeout: int = 20,
                         proxy: Optional[str] = None) -> Dict[str, Any]:
    result = {
        "video_url": video_url,
        "username": "",
        "video_id": "",
        "description": "",
        "location_created": "",
        "location_created_flag": "",
        "location_created_name_ar": "",
        "author_region": "",
        "author_region_flag": "",
        "author_region_name_ar": "",
        "text_language": "",
        "text_language_name_ar": "",
        "status": "⚠️ معلومات محدودة",
        "error": "",
        "debug_report": {"http_status": 0, "html_length": 0},
    }
    try:
        if not video_url:
            result["error"] = "رابط الفيديو فارغ"
            return result

        m = re.search(r"@([^/]+)/video/(\d{10,25})", video_url)
        if m:
            result["username"] = m.group(1)
            result["video_id"] = m.group(2)

        session = _build_session(proxy=proxy)
        status, html = _fetch_with_strategy(session, video_url, mobile=False,
                                            referer="https://www.google.com/", timeout=timeout)
        result["debug_report"]["http_status"] = status
        result["debug_report"]["html_length"] = len(html)

        if not html:
            result["error"] = f"فشل جلب الفيديو (HTTP {status})"
            return result

        data = _parse_script_json(html)
        scope = data.get("__DEFAULT_SCOPE__", {}) if isinstance(data, dict) else {}
        item = {}
        if scope:
            item = (scope.get("webapp.reflow.video.detail", {})
                    .get("itemInfo", {}).get("itemStruct", {}) or {})
            if not item:
                item = (scope.get("webapp.video-detail", {})
                        .get("itemInfo", {}).get("itemStruct", {}) or {})
        if not item and isinstance(data, dict):
            im = data.get("ItemModule", {})
            if isinstance(im, dict) and im:
                item = next(iter(im.values())) or {}

        author = item.get("author", {}) if isinstance(item, dict) else {}
        loc = _safe_region(item.get("locationCreated") if isinstance(item, dict) else "")
        ar_reg = _safe_region(author.get("region") if isinstance(author, dict) else "")
        lang = ((item.get("textLanguage") or item.get("language") or "").lower()
                if isinstance(item, dict) else "")
        desc = item.get("desc") or item.get("description") or ""

        result["description"] = desc
        if author and not result["username"]:
            result["username"] = author.get("uniqueId") or author.get("nickname") or ""
        if loc:
            result["location_created"] = loc
            result["location_created_flag"], result["location_created_name_ar"] = \
                TIKTOK_REGION_MAP.get(loc, ("🌍", loc))
        if ar_reg:
            result["author_region"] = ar_reg
            result["author_region_flag"], result["author_region_name_ar"] = \
                TIKTOK_REGION_MAP.get(ar_reg, ("🌍", ar_reg))
        result["text_language"] = lang
        result["text_language_name_ar"] = LANGUAGE_NAMES_AR.get(lang, lang)
        result["status"] = ("✅ نجح" if any([result["username"], result["location_created"],
                                            result["author_region"], desc])
                            else "⚠️ معلومات محدودة")
    except requests.Timeout:
        result["error"] = "انتهت مهلة الاتصال"
    except requests.ConnectionError:
        result["error"] = "خطأ في الاتصال"
    except Exception as e:
        result["error"] = f"خطأ: {str(e)[:150]}"
    return result


# ============================================================
# مؤشرات التفاعل (بدون تغيير جوهري)
# ============================================================

def calculate_engagement_metrics(row: Dict[str, Any]) -> Dict[str, Any]:
    followers = _safe_int(row.get("follower_count") or row.get("followers") or 0)
    likes = _safe_int(row.get("heart_count") or row.get("likes") or row.get("total_likes") or 0)
    videos = max(_safe_int(row.get("video_count") or row.get("videos") or 0), 0)
    comments = _safe_int(row.get("reply_count") or row.get("comments") or row.get("total_replies") or 0)
    avg_likes = (likes / videos) if videos > 0 else 0.0
    er = ((likes + comments) / followers * 100.0) if followers > 0 else 0.0
    return {
        "followers": followers,
        "likes": likes,
        "videos": videos,
        "comments": comments,
        "avg_likes_per_video": round(avg_likes, 2),
        "engagement_rate": round(er, 2),
        "engagement_level": "مرتفع" if er >= 10 else ("متوسط" if er >= 3 else "منخفض"),
    }


# ============================================================
# CLI للاختبار السريع
# ============================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        p = fetch_tiktok_profile(sys.argv[1])
        print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        print("Usage: python tiktok_analyzer.py <username>")
