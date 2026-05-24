"""
محلل TikTok المتقدم v5 - مع تحليل الفيديوهات

🔥 الاكتشاف الذهبي:
TikTok يحجب region من البروفايل، لكن metadata الفيديو تحوي:
- locationCreated: مكان تصوير الفيديو (دقيق جداً)
- author.region: منطقة المؤلف (نادر)
- textLanguage: لغة المحتوى

نعرض ميزتين:
1. تحليل البروفايل الأساسي + استنتاج من البايو/اللهجة
2. تحليل رابط فيديو محدد (يعطي locationCreated مباشرة)
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime, timezone


TIKTOK_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# ============ الخرائط ============
TIKTOK_REGION_MAP = {
    "SA": ("🇸🇦", "السعودية"), "AE": ("🇦🇪", "الإمارات"), "EG": ("🇪🇬", "مصر"),
    "KW": ("🇰🇼", "الكويت"), "QA": ("🇶🇦", "قطر"), "BH": ("🇧🇭", "البحرين"),
    "OM": ("🇴🇲", "عُمان"), "JO": ("🇯🇴", "الأردن"), "LB": ("🇱🇧", "لبنان"),
    "SY": ("🇸🇾", "سوريا"), "IQ": ("🇮🇶", "العراق"), "YE": ("🇾🇪", "اليمن"),
    "PS": ("🇵🇸", "فلسطين"), "MA": ("🇲🇦", "المغرب"), "DZ": ("🇩🇿", "الجزائر"),
    "TN": ("🇹🇳", "تونس"), "LY": ("🇱🇾", "ليبيا"), "SD": ("🇸🇩", "السودان"),
    "SO": ("🇸🇴", "الصومال"), "MR": ("🇲🇷", "موريتانيا"),
    "US": ("🇺🇸", "الولايات المتحدة"), "GB": ("🇬🇧", "بريطانيا"), "FR": ("🇫🇷", "فرنسا"),
    "DE": ("🇩🇪", "ألمانيا"), "IT": ("🇮🇹", "إيطاليا"), "ES": ("🇪🇸", "إسبانيا"),
    "NL": ("🇳🇱", "هولندا"), "BE": ("🇧🇪", "بلجيكا"), "CH": ("🇨🇭", "سويسرا"),
    "SE": ("🇸🇪", "السويد"), "PT": ("🇵🇹", "البرتغال"), "AT": ("🇦🇹", "النمسا"),
    "PL": ("🇵🇱", "بولندا"), "GR": ("🇬🇷", "اليونان"),
    "RU": ("🇷🇺", "روسيا"), "UA": ("🇺🇦", "أوكرانيا"),
    "CN": ("🇨🇳", "الصين"), "JP": ("🇯🇵", "اليابان"), "KR": ("🇰🇷", "كوريا الجنوبية"),
    "IN": ("🇮🇳", "الهند"), "PK": ("🇵🇰", "باكستان"), "BD": ("🇧🇩", "بنغلاديش"),
    "TR": ("🇹🇷", "تركيا"), "IR": ("🇮🇷", "إيران"), "AF": ("🇦🇫", "أفغانستان"),
    "IL": ("🇮🇱", "إسرائيل"),
    "BR": ("🇧🇷", "البرازيل"), "AR": ("🇦🇷", "الأرجنتين"), "MX": ("🇲🇽", "المكسيك"),
    "CA": ("🇨🇦", "كندا"), "AU": ("🇦🇺", "أستراليا"), "NZ": ("🇳🇿", "نيوزيلندا"),
    "ID": ("🇮🇩", "إندونيسيا"), "MY": ("🇲🇾", "ماليزيا"), "SG": ("🇸🇬", "سنغافورة"),
    "TH": ("🇹🇭", "تايلاند"), "VN": ("🇻🇳", "فيتنام"), "PH": ("🇵🇭", "الفلبين"),
    "NG": ("🇳🇬", "نيجيريا"), "ZA": ("🇿🇦", "جنوب أفريقيا"), "KE": ("🇰🇪", "كينيا"),
}

LANGUAGE_NAMES_AR = {
    "ar": "العربية", "en": "الإنجليزية", "es": "الإسبانية", "fr": "الفرنسية",
    "de": "الألمانية", "it": "الإيطالية", "pt": "البرتغالية", "ru": "الروسية",
    "tr": "التركية", "fa": "الفارسية", "ur": "الأردية", "hi": "الهندية",
    "zh": "الصينية", "ja": "اليابانية", "ko": "الكورية", "id": "الإندونيسية",
    "ms": "الماليزية", "th": "التايلاندية", "vi": "الفيتنامية", "tl": "الفلبينية",
    "nl": "الهولندية", "pl": "البولندية", "el": "اليونانية", "he": "العبرية",
    "uk": "الأوكرانية", "ro": "الرومانية", "bn": "البنغالية", "un": "غير محدد",
}

LANG_TO_COUNTRIES = {
    "ar": ["SA", "EG", "AE", "MA", "DZ", "IQ", "KW", "QA", "JO", "LB", "TN", "LY", "SY", "YE", "OM", "BH", "PS", "SD"],
    "tr": ["TR"], "fa": ["IR", "AF"], "ur": ["PK"], "hi": ["IN"], "bn": ["BD"],
    "id": ["ID"], "ms": ["MY"], "th": ["TH"], "vi": ["VN"], "tl": ["PH"],
    "ja": ["JP"], "ko": ["KR"], "ru": ["RU"], "uk": ["UA"], "pl": ["PL"],
    "es": ["ES", "MX", "AR"], "pt": ["BR", "PT"], "de": ["DE"], "it": ["IT"],
    "nl": ["NL"], "el": ["GR"], "he": ["IL"],
}

CITY_TO_COUNTRY = {
    "riyadh": "SA", "jeddah": "SA", "mecca": "SA", "makkah": "SA", "medina": "SA",
    "dammam": "SA", "khobar": "SA", "taif": "SA", "abha": "SA", "tabuk": "SA",
    "الرياض": "SA", "جدة": "SA", "مكة": "SA", "المدينة": "SA", "الدمام": "SA",
    "الطائف": "SA", "أبها": "SA", "تبوك": "SA", "السعودية": "SA", "ksa": "SA", "saudi": "SA",
    "dubai": "AE", "abu dhabi": "AE", "abudhabi": "AE", "sharjah": "AE",
    "دبي": "AE", "أبوظبي": "AE", "ابوظبي": "AE", "الشارقة": "AE",
    "الإمارات": "AE", "الامارات": "AE", "uae": "AE",
    "cairo": "EG", "alexandria": "EG", "giza": "EG", "egypt": "EG",
    "القاهرة": "EG", "الإسكندرية": "EG", "الجيزة": "EG", "مصر": "EG",
    "kuwait": "KW", "الكويت": "KW", "doha": "QA", "qatar": "QA", "قطر": "QA",
    "manama": "BH", "bahrain": "BH", "البحرين": "BH",
    "muscat": "OM", "oman": "OM", "مسقط": "OM", "سلطنة عمان": "OM",
    "amman": "JO", "jordan": "JO", "عمّان": "JO", "عمان": "JO", "الأردن": "JO",
    "beirut": "LB", "lebanon": "LB", "بيروت": "LB", "لبنان": "LB",
    "baghdad": "IQ", "iraq": "IQ", "بغداد": "IQ", "العراق": "IQ", "البصرة": "IQ", "أربيل": "IQ",
    "damascus": "SY", "syria": "SY", "دمشق": "SY", "سوريا": "SY", "حلب": "SY",
    "sanaa": "YE", "yemen": "YE", "صنعاء": "YE", "اليمن": "YE", "عدن": "YE",
    "palestine": "PS", "gaza": "PS", "فلسطين": "PS", "غزة": "PS", "القدس": "PS",
    "morocco": "MA", "casablanca": "MA", "rabat": "MA", "marrakech": "MA",
    "المغرب": "MA", "الدار البيضاء": "MA", "الرباط": "MA", "مراكش": "MA",
    "algeria": "DZ", "algiers": "DZ", "الجزائر": "DZ",
    "tunisia": "TN", "tunis": "TN", "تونس": "TN",
    "libya": "LY", "ليبيا": "LY", "طرابلس": "LY", "بنغازي": "LY",
    "sudan": "SD", "khartoum": "SD", "السودان": "SD", "الخرطوم": "SD",
    "somalia": "SO", "الصومال": "SO",
    "usa": "US", "united states": "US", "america": "US", "new york": "US", "los angeles": "US",
    "uk": "GB", "london": "GB", "england": "GB", "britain": "GB",
    "france": "FR", "paris": "FR", "فرنسا": "FR", "باريس": "FR",
    "germany": "DE", "berlin": "DE", "ألمانيا": "DE",
    "turkey": "TR", "istanbul": "TR", "تركيا": "TR", "إسطنبول": "TR",
    "iran": "IR", "tehran": "IR", "إيران": "IR",
    "india": "IN", "الهند": "IN", "pakistan": "PK", "باكستان": "PK",
    "indonesia": "ID", "إندونيسيا": "ID", "malaysia": "MY", "ماليزيا": "MY",
    "japan": "JP", "اليابان": "JP", "korea": "KR", "كوريا": "KR",
    "russia": "RU", "روسيا": "RU", "ukraine": "UA", "أوكرانيا": "UA",
    "brazil": "BR", "البرازيل": "BR", "mexico": "MX", "المكسيك": "MX",
    "canada": "CA", "كندا": "CA", "australia": "AU", "أستراليا": "AU",
}

DIALECT_HINTS = {
    "SA": ["والله", "وش رايك", "تكفى", "يا اخوي", "وايد", "خوش", "حياك", "هلا والله"],
    "EG": ["ازيك", "إزيك", "ازاي", "إزاي", "كده", "كدا", "اوي", "أوي", "خالص", "بقى", "يلا", "عاوز", "عايز"],
    "AE": ["شحالك", "هلا والله", "تسلم", "وايد", "ها يبه"],
    "KW": ["شلونك", "حياك", "تكفى", "والنبي"],
    "MA": ["واخا", "بزاف", "زعما", "كيفاش", "شنو", "غادي", "دابا", "صافي", "بصح"],
    "DZ": ["واش", "كيراك", "بصح", "بزاف", "خويا"],
    "IQ": ["شلون", "اشلون", "هسة", "اكو", "ماكو", "هواي", "وين", "شكد"],
    "LB": ["شو في", "كيفك", "هلق", "بدي", "كتير"],
    "SY": ["شو في", "كيفك", "هلق", "بدي", "كتير", "هلأ"],
    "YE": ["كيف حالك", "وشلون"],
}

USERNAME_PATTERNS = {
    "SA": ["_ksa", "ksa_", "saudi", "_sa_", "_sa.", "riyadh", "jeddah", "966"],
    "AE": ["_uae", "uae_", "_ae_", "_ae.", "dubai", "971"],
    "EG": ["_egypt", "egypt_", "_eg_", "_eg.", "masr", "cairo"],
    "IQ": ["_iraq", "iraq_", "_iq_", "baghdad", "964"],
    "KW": ["_kuwait", "kuwait_", "_kw_", "965"],
    "QA": ["_qatar", "qatar_", "_qa_", "974"],
    "JO": ["_jordan", "jordan_", "_jo_", "962"],
    "MA": ["_morocco", "morocco_", "_ma_", "maroc", "212"],
    "DZ": ["_algeria", "algeria_", "_dz_", "algerie", "213"],
    "TN": ["_tunisia", "tunisia_", "_tn_", "216"],
    "LB": ["_lebanon", "lebanon_", "_lb_", "961"],
    "SY": ["_syria", "syria_", "_sy_"],
    "YE": ["_yemen", "yemen_", "_ye_"],
    "OM": ["_oman", "oman_"],
    "BH": ["_bahrain", "bahrain_"],
    "TR": ["_turkey", "turkey_", "_tr_"],
    "IR": ["_iran", "iran_", "_ir_"],
    "PK": ["_pakistan", "pakistan_", "_pk_"],
    "IN": ["_india", "india_", "_in_", "_ind"],
}


def format_count(n):
    try:
        n = int(n)
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f}B"
        elif n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)
    except (ValueError, TypeError):
        return "0"


# ============ نظام كشف الموقع ============
class LocationDetector:
    def __init__(self):
        self.scores = {}
        self.evidence = []

    def add_score(self, country_code, points, source):
        if not country_code:
            return
        self.scores[country_code] = self.scores.get(country_code, 0) + points
        self.evidence.append(f"{source} (+{points})")

    def add_score_multiple(self, countries, points, source):
        if not countries:
            return
        per = points // len(countries) if len(countries) > 1 else points
        for cc in countries:
            self.scores[cc] = self.scores.get(cc, 0) + per
        if per > 0:
            self.evidence.append(f"{source} (+{per})")

    def get_winner(self, threshold=20):
        if not self.scores:
            return None, 0, []
        sorted_c = sorted(self.scores.items(), key=lambda x: -x[1])
        top, score = sorted_c[0]
        if score < threshold:
            return None, 0, [c for c, s in sorted_c[:5]]
        total = sum(self.scores.values())
        confidence = min(int((score / total) * 100), 100)
        if len(sorted_c) > 1 and score >= sorted_c[1][1] * 2:
            confidence = min(confidence + 15, 100)
        candidates = [c for c, s in sorted_c[:3] if c != top]
        return top, confidence, candidates


def detect_country_from_text(text, source_name, detector, base=30):
    if not text:
        return
    text_lower = text.lower()
    for cc, (flag, _) in TIKTOK_REGION_MAP.items():
        if flag in text:
            detector.add_score(cc, base + 30, f"🚩 علم {cc} في {source_name}")
            return
    for kw in sorted(CITY_TO_COUNTRY.keys(), key=len, reverse=True):
        cc = CITY_TO_COUNTRY[kw]
        if any(ord(c) > 127 for c in kw):
            if kw in text:
                detector.add_score(cc, base + 20, f"🏙️ '{kw}' في {source_name}")
                return
        else:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                detector.add_score(cc, base + 15, f"🏙️ '{kw}' في {source_name}")
                return
    for cc, hints in DIALECT_HINTS.items():
        cnt = sum(1 for h in hints if h in text)
        if cnt >= 2:
            detector.add_score(cc, base + 5, f"🗣️ لهجة {cc} ({cnt}) في {source_name}")
            return
        elif cnt == 1:
            detector.add_score(cc, base - 10, f"🗣️ احتمال لهجة {cc} في {source_name}")


def analyze_username_patterns(username, detector):
    u = username.lower()
    for cc, pats in USERNAME_PATTERNS.items():
        for p in pats:
            if p in u:
                detector.add_score(cc, 35, f"🔤 نمط '{p}' في اليوزر")
                return


# ============ Parsing ============
def parse_universal_data(html, key="webapp.user-detail"):
    try:
        m = re.search(
            r'<script[^>]*id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
            html, re.DOTALL,
        )
        if m:
            data = json.loads(m.group(1).strip())
            return data.get("__DEFAULT_SCOPE__", {}).get(key, {})
        soup = BeautifulSoup(html, "html.parser")
        s = soup.find("script", {"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"})
        if s:
            content = re.search(r'>(.*?)</script>', str(s), re.DOTALL)
            if content:
                data = json.loads(content.group(1).strip())
                return data.get("__DEFAULT_SCOPE__", {}).get(key, {})
        return None
    except Exception:
        return None


def parse_tiktok_video_url(url):
    """استخراج username و video_id من رابط TikTok."""
    url = url.strip()
    # https://www.tiktok.com/@username/video/1234567890123456789
    m = re.search(r'tiktok\.com/@([\w._-]+)/video/(\d+)', url)
    if m:
        return m.group(1), m.group(2)
    # https://vm.tiktok.com/XXXXXX/  (رابط مختصر)
    if 'vm.tiktok.com' in url:
        try:
            r = requests.get(url, headers=TIKTOK_HEADERS, timeout=10, allow_redirects=True)
            return parse_tiktok_video_url(r.url)
        except Exception:
            return None, None
    return None, None


def fetch_video_metadata(username, video_id, timeout=15):
    """🔥 جلب metadata الفيديو - يحوي locationCreated وauthor.region."""
    url = f"https://www.tiktok.com/@{username}/video/{video_id}"
    result = {
        "video_id": video_id,
        "video_url": url,
        "username": username,
        "status": "❌ فشل",
        "error": "",
        "location_created": "",
        "location_flag": "",
        "location_name_ar": "",
        "text_language": "",
        "create_date": "",
        "author_region": "",
        "author_region_flag": "",
        "author_region_name_ar": "",
        "author_id": "",
        "author_nickname": "",
        "author_verified": False,
        "video_desc": "",
        "video_views": 0,
        "video_likes": 0,
        "video_shares": 0,
        "video_comments": 0,
    }
    try:
        r = requests.get(url, headers=TIKTOK_HEADERS, timeout=timeout)
        if r.status_code != 200:
            result["error"] = f"كود {r.status_code}"
            return result
        vd = parse_universal_data(r.text, "webapp.video-detail")
        if not vd:
            result["error"] = "لا توجد بيانات في الصفحة"
            return result
        sc = vd.get("statusCode", 0)
        if sc != 0:
            result["error"] = f"TikTok statusCode={sc} ({vd.get('statusMsg', '')})"
            return result
        item = vd.get("itemInfo", {}).get("itemStruct", {})
        if not item:
            result["error"] = "بيانات الفيديو فارغة"
            return result

        # 🔥 المعلومات الذهبية
        loc = item.get("locationCreated", "") or ""
        result["location_created"] = loc
        if loc in TIKTOK_REGION_MAP:
            result["location_flag"] = TIKTOK_REGION_MAP[loc][0]
            result["location_name_ar"] = TIKTOK_REGION_MAP[loc][1]

        result["text_language"] = item.get("textLanguage", "") or ""
        ct = item.get("createTime", 0)
        if ct:
            try:
                dt = datetime.fromtimestamp(int(ct), tz=timezone.utc)
                result["create_date"] = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                pass

        result["video_desc"] = (item.get("desc", "") or "")[:300]

        # Stats
        stats = item.get("stats", {}) or item.get("statsV2", {}) or {}
        result["video_views"] = int(stats.get("playCount", 0) or 0)
        result["video_likes"] = int(stats.get("diggCount", 0) or 0)
        result["video_shares"] = int(stats.get("shareCount", 0) or 0)
        result["video_comments"] = int(stats.get("commentCount", 0) or 0)

        # Author
        author = item.get("author", {}) or {}
        result["author_id"] = str(author.get("id", "") or "")
        result["author_nickname"] = author.get("nickname", "") or ""
        result["author_verified"] = bool(author.get("verified", False))
        ar = (author.get("region") or "").upper()
        result["author_region"] = ar
        if ar in TIKTOK_REGION_MAP:
            result["author_region_flag"] = TIKTOK_REGION_MAP[ar][0]
            result["author_region_name_ar"] = TIKTOK_REGION_MAP[ar][1]

        result["status"] = "✅ نجح"
    except requests.Timeout:
        result["error"] = "انتهت مهلة الاتصال"
    except Exception as e:
        result["error"] = str(e)[:150]
    return result


# ============ التحليل الرئيسي للحساب ============
def fetch_tiktok_profile(username, timeout=15):
    """تحليل ملف TikTok الأساسي."""
    username = username.replace("@", "").strip()
    profile_url = f"https://www.tiktok.com/@{username}"

    result = {
        "username": username, "profile_url": profile_url,
        "status": "❌ فشل", "error": "",
        "user_id": "", "sec_uid": "", "short_id": "",
        "nickname": "", "signature": "", "create_date": "",
        "create_time_raw": 0, "create_hour_utc": "",
        "avatar_thumb": "", "avatar_medium": "", "avatar_large": "",
        "region": "", "region_flag": "", "region_name_ar": "",
        "region_source": "", "region_confidence": 0,
        "region_evidence": "", "candidates": "",
        "language": "", "language_name_ar": "",
        "verified": False, "private_account": False,
        "tt_seller": False, "is_organization": False, "secret": False,
        "follower_count": 0, "following_count": 0,
        "heart_count": 0, "video_count": 0,
        "digg_count": 0, "friend_count": 0,
        "follower_count_formatted": "", "heart_count_formatted": "",
        "bio_link": "",
    }

    try:
        response = requests.get(profile_url, headers=TIKTOK_HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code == 404:
            result["error"] = "الحساب غير موجود (404)"
            return result
        if response.status_code != 200:
            result["error"] = f"كود استجابة: {response.status_code}"
            return result

        user_detail = parse_universal_data(response.text, "webapp.user-detail")
        if not user_detail or "userInfo" not in user_detail:
            result["error"] = "لم يتم العثور على بيانات في الصفحة"
            return result

        sc = user_detail.get("statusCode", 0)
        if sc != 0:
            msg = user_detail.get("statusMsg", "")
            if msg:
                result["error"] = f"TikTok: {msg}"
                return result

        ui = user_detail.get("userInfo", {})
        user = ui.get("user", {}) or {}
        stats = ui.get("stats", {}) or ui.get("statsV2", {}) or {}

        if not user:
            result["error"] = "بيانات المستخدم فارغة"
            return result

        result["user_id"] = str(user.get("id", "") or "")
        result["sec_uid"] = user.get("secUid", "") or ""
        result["short_id"] = str(user.get("shortId", "") or "")
        result["nickname"] = user.get("nickname", "") or ""
        result["signature"] = user.get("signature", "") or ""
        result["avatar_thumb"] = user.get("avatarThumb", "") or ""
        result["avatar_medium"] = user.get("avatarMedium", "") or ""
        result["avatar_large"] = user.get("avatarLarger", "") or ""

        ct = user.get("createTime", 0) or 0
        result["create_time_raw"] = int(ct) if ct else 0
        if ct:
            try:
                dt = datetime.fromtimestamp(int(ct), tz=timezone.utc)
                result["create_date"] = dt.strftime("%Y-%m-%d")
                result["create_hour_utc"] = f"{dt.hour:02d}:{dt.minute:02d} UTC"
            except Exception:
                pass

        result["verified"] = bool(user.get("verified", False))
        result["private_account"] = bool(user.get("privateAccount", False))
        result["tt_seller"] = bool(user.get("ttSeller", False))
        result["secret"] = bool(user.get("secret", False))
        commerce = user.get("commerceUserInfo", {}) or {}
        result["is_organization"] = bool(commerce.get("commerceUser", False))

        result["follower_count"] = int(stats.get("followerCount", 0) or 0)
        result["following_count"] = int(stats.get("followingCount", 0) or 0)
        result["heart_count"] = max(int(stats.get("heart", 0) or 0), int(stats.get("heartCount", 0) or 0))
        if result["heart_count"] < 0:
            result["heart_count"] = int(stats.get("heart", 0) or 0)
        result["video_count"] = int(stats.get("videoCount", 0) or 0)
        result["digg_count"] = int(stats.get("diggCount", 0) or 0)
        result["friend_count"] = int(stats.get("friendCount", 0) or 0)

        result["follower_count_formatted"] = format_count(result["follower_count"])
        result["heart_count_formatted"] = format_count(result["heart_count"])

        bl = user.get("bioLink", {})
        if isinstance(bl, dict):
            result["bio_link"] = bl.get("link", "") or ""

        lang = (user.get("language") or "").lower()
        result["language"] = lang
        if lang in LANGUAGE_NAMES_AR:
            result["language_name_ar"] = LANGUAGE_NAMES_AR[lang]

        # كشف الموقع متعدد الإشارات
        detector = LocationDetector()

        api_region = (user.get("region") or "").upper()
        if api_region and api_region in TIKTOK_REGION_MAP:
            detector.add_score(api_region, 1000, "🎯 TikTok API region")

        if result["signature"]:
            detect_country_from_text(result["signature"], "البايو", detector, 30)
        if result["nickname"]:
            detect_country_from_text(result["nickname"], "الاسم", detector, 20)
        detect_country_from_text(username, "اليوزر", detector, 15)
        analyze_username_patterns(username, detector)

        if lang in LANG_TO_COUNTRIES:
            possible = LANG_TO_COUNTRIES[lang]
            if len(possible) == 1:
                detector.add_score(possible[0], 30, f"🌐 اللغة {lang}")
            else:
                detector.add_score_multiple(possible, 20, f"🌐 اللغة {lang}")

        winner, confidence, candidates = detector.get_winner(threshold=15)

        if winner:
            result["region"] = winner
            flag, name_ar = TIKTOK_REGION_MAP.get(winner, ("🌍", winner))
            result["region_flag"] = flag
            result["region_name_ar"] = name_ar
            result["region_confidence"] = confidence
            result["region_source"] = "🧠 تحليل ذكي"
            result["region_evidence"] = " | ".join(detector.evidence[:5])
            if candidates:
                result["candidates"] = "|".join(candidates)
        elif candidates:
            result["candidates"] = "|".join(candidates)
            result["region_source"] = "دول محتملة"
            result["region_evidence"] = " | ".join(detector.evidence[:3])

        if result["user_id"] or result["nickname"]:
            result["status"] = "✅ نجح"
        else:
            result["status"] = "⚠️ معلومات محدودة"

    except requests.Timeout:
        result["error"] = "انتهت مهلة الاتصال"
    except requests.ConnectionError:
        result["error"] = "خطأ في الاتصال"
    except Exception as e:
        result["error"] = f"خطأ: {str(e)[:150]}"

    return result


# ============ دالة جديدة: تحليل فيديو محدد ============
def analyze_tiktok_video(video_url, timeout=15):
    """
    🎯 تحليل رابط فيديو محدد للحصول على:
    - locationCreated: مكان التصوير الفعلي (دقيق جداً!)
    - author.region: منطقة المؤلف
    - textLanguage: لغة المحتوى
    - معلومات المؤلف الكاملة
    """
    username, video_id = parse_tiktok_video_url(video_url)
    if not username or not video_id:
        return {
            "status": "❌ فشل",
            "error": "رابط الفيديو غير صحيح. يجب أن يكون: https://www.tiktok.com/@username/video/ID",
            "video_url": video_url,
        }
    return fetch_video_metadata(username, video_id, timeout=timeout)


def calculate_engagement_metrics(data):
    metrics = {
        "engagement_rate": 0.0, "avg_likes_per_video": 0,
        "follower_to_following_ratio": 0.0, "tier": "",
    }
    f, fl, h, v = (data.get(k, 0) for k in ("follower_count", "following_count", "heart_count", "video_count"))
    if v > 0 and h > 0:
        metrics["avg_likes_per_video"] = h // v
    if f > 0 and metrics["avg_likes_per_video"] > 0:
        metrics["engagement_rate"] = round((metrics["avg_likes_per_video"] / f) * 100, 2)
    if fl > 0:
        metrics["follower_to_following_ratio"] = round(f / fl, 1)

    if f >= 10_000_000:
        metrics["tier"] = "🌟 Mega Influencer (10M+)"
    elif f >= 1_000_000:
        metrics["tier"] = "⭐ Macro Influencer (1M+)"
    elif f >= 100_000:
        metrics["tier"] = "✨ Mid-Tier (100K+)"
    elif f >= 10_000:
        metrics["tier"] = "💫 Micro Influencer (10K+)"
    elif f >= 1_000:
        metrics["tier"] = "🔹 Nano (1K+)"
    else:
        metrics["tier"] = "🆕 جديد/صغير (<1K)"
    return metrics


# ============ اختبار ============
if __name__ == "__main__":
    import sys
    print("="*60)
    print("اختبار 1: تحليل ملف شخصي")
    print("="*60)
    p = fetch_tiktok_profile("khaby.lame")
    print(f"@{p['username']}: {p['nickname']} - {p['follower_count_formatted']} متابع")
    print(f"الموقع: {p['region_flag']} {p['region_name_ar']} ({p['region_confidence']}%)")
    
    print("\n" + "="*60)
    print("اختبار 2: تحليل فيديو محدد (للحصول على locationCreated)")
    print("="*60)
    v = analyze_tiktok_video("https://www.tiktok.com/@noorstars/video/7518458932478725406")
    if v["status"] == "✅ نجح":
        print(f"✅ المؤلف: {v['author_nickname']} (@{v['username']})")
        print(f"🆔 ID: {v['author_id']}")
        print(f"📅 تاريخ: {v['create_date']}")
        print(f"🌐 لغة الفيديو: {v['text_language']}")
        print(f"\n🔥 المعلومات الذهبية:")
        print(f"   📍 مكان التصوير: {v['location_flag']} {v['location_name_ar']} ({v['location_created']})")
        print(f"   🌍 منطقة المؤلف: {v['author_region_flag']} {v['author_region_name_ar']} ({v['author_region']})")
        print(f"\n📊 الإحصائيات:")
        print(f"   👁️ المشاهدات: {format_count(v['video_views'])}")
        print(f"   ❤️ الإعجابات: {format_count(v['video_likes'])}")
        print(f"   💬 التعليقات: {format_count(v['video_comments'])}")
        print(f"\n📝 الوصف: {v['video_desc'][:150]}")
    else:
        print(f"❌ {v['error']}")
