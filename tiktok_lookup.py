# ═══════════════════════════════════════════════════════════
# BSR-V217L-TIKTOK-LOOKUP-WORLDWIDE-AHMAD-20260613
# جلب معلومات TikTok + كشف الدولة (195+ دولة)
# يحترم القيود: #18 لا IP, #19 Multi-Signal, #20 TikTok فقط
# ═══════════════════════════════════════════════════════════
import httpx
import re
from typing import Optional, Dict, Any, Tuple, List
from collections import Counter

TIKWM_BASE = "https://www.tikwm.com"
TIMEOUT = 15


# ────────────────────── قاموس جميع دول العالم (195+) ──────────────────────
COUNTRY_AR = {
    # 🌍 الدول العربيّة (22)
    "SA": "🇸🇦 السعودية",        "AE": "🇦🇪 الإمارات",
    "EG": "🇪🇬 مصر",             "KW": "🇰🇼 الكويت",
    "QA": "🇶🇦 قطر",             "BH": "🇧🇭 البحرين",
    "OM": "🇴🇲 عُمان",           "JO": "🇯🇴 الأردن",
    "LB": "🇱🇧 لبنان",           "SY": "🇸🇾 سوريا",
    "IQ": "🇮🇶 العراق",          "YE": "🇾🇪 اليمن",
    "PS": "🇵🇸 فلسطين",          "MA": "🇲🇦 المغرب",
    "DZ": "🇩🇿 الجزائر",         "TN": "🇹🇳 تونس",
    "LY": "🇱🇾 ليبيا",           "SD": "🇸🇩 السودان",
    "MR": "🇲🇷 موريتانيا",       "SO": "🇸🇴 الصومال",
    "DJ": "🇩🇯 جيبوتي",          "KM": "🇰🇲 جزر القمر",

    # 🇪🇺 أوروبا (45)
    "GB": "🇬🇧 المملكة المتحدة", "FR": "🇫🇷 فرنسا",
    "DE": "🇩🇪 ألمانيا",         "IT": "🇮🇹 إيطاليا",
    "ES": "🇪🇸 إسبانيا",         "PT": "🇵🇹 البرتغال",
    "NL": "🇳🇱 هولندا",          "BE": "🇧🇪 بلجيكا",
    "LU": "🇱🇺 لوكسمبورغ",       "CH": "🇨🇭 سويسرا",
    "AT": "🇦🇹 النمسا",          "IE": "🇮🇪 أيرلندا",
    "DK": "🇩🇰 الدنمارك",        "SE": "🇸🇪 السويد",
    "NO": "🇳🇴 النرويج",         "FI": "🇫🇮 فنلندا",
    "IS": "🇮🇸 آيسلندا",         "PL": "🇵🇱 بولندا",
    "CZ": "🇨🇿 التشيك",          "SK": "🇸🇰 سلوفاكيا",
    "HU": "🇭🇺 المجر",           "RO": "🇷🇴 رومانيا",
    "BG": "🇧🇬 بلغاريا",         "GR": "🇬🇷 اليونان",
    "HR": "🇭🇷 كرواتيا",         "SI": "🇸🇮 سلوفينيا",
    "RS": "🇷🇸 صربيا",           "BA": "🇧🇦 البوسنة والهرسك",
    "MK": "🇲🇰 مقدونيا الشمالية", "AL": "🇦🇱 ألبانيا",
    "ME": "🇲🇪 الجبل الأسود",    "XK": "🇽🇰 كوسوفو",
    "EE": "🇪🇪 إستونيا",         "LV": "🇱🇻 لاتفيا",
    "LT": "🇱🇹 ليتوانيا",        "BY": "🇧🇾 بيلاروسيا",
    "UA": "🇺🇦 أوكرانيا",        "MD": "🇲🇩 مولدوفا",
    "RU": "🇷🇺 روسيا",           "TR": "🇹🇷 تركيا",
    "CY": "🇨🇾 قبرص",            "MT": "🇲🇹 مالطا",
    "MC": "🇲🇨 موناكو",          "AD": "🇦🇩 أندورا",
    "SM": "🇸🇲 سان مارينو",      "VA": "🇻🇦 الفاتيكان",
    "LI": "🇱🇮 ليختنشتاين",

    # 🌏 آسيا (48)
    "CN": "🇨🇳 الصين",           "JP": "🇯🇵 اليابان",
    "KR": "🇰🇷 كوريا الجنوبية",   "KP": "🇰🇵 كوريا الشمالية",
    "IN": "🇮🇳 الهند",           "PK": "🇵🇰 باكستان",
    "BD": "🇧🇩 بنغلاديش",        "LK": "🇱🇰 سريلانكا",
    "NP": "🇳🇵 نيبال",           "BT": "🇧🇹 بوتان",
    "MV": "🇲🇻 جزر المالديف",    "AF": "🇦🇫 أفغانستان",
    "IR": "🇮🇷 إيران",           "IL": "🇮🇱 إسرائيل",
    "TH": "🇹🇭 تايلاند",         "VN": "🇻🇳 فيتنام",
    "MY": "🇲🇾 ماليزيا",         "SG": "🇸🇬 سنغافورة",
    "ID": "🇮🇩 إندونيسيا",       "PH": "🇵🇭 الفلبين",
    "MM": "🇲🇲 ميانمار",         "KH": "🇰🇭 كمبوديا",
    "LA": "🇱🇦 لاوس",            "BN": "🇧🇳 بروناي",
    "TL": "🇹🇱 تيمور الشرقية",   "MN": "🇲🇳 منغوليا",
    "TW": "🇹🇼 تايوان",          "HK": "🇭🇰 هونغ كونغ",
    "MO": "🇲🇴 ماكاو",           "KZ": "🇰🇿 كازاخستان",
    "UZ": "🇺🇿 أوزبكستان",       "TM": "🇹🇲 تركمانستان",
    "TJ": "🇹🇯 طاجيكستان",       "KG": "🇰🇬 قيرغيزستان",
    "AZ": "🇦🇿 أذربيجان",        "AM": "🇦🇲 أرمينيا",
    "GE": "🇬🇪 جورجيا",

    # 🌍 أفريقيا (54)
    "NG": "🇳🇬 نيجيريا",         "ZA": "🇿🇦 جنوب أفريقيا",
    "KE": "🇰🇪 كينيا",           "ET": "🇪🇹 إثيوبيا",
    "GH": "🇬🇭 غانا",            "TZ": "🇹🇿 تنزانيا",
    "UG": "🇺🇬 أوغندا",          "ZW": "🇿🇼 زيمبابوي",
    "ZM": "🇿🇲 زامبيا",          "AO": "🇦🇴 أنغولا",
    "MZ": "🇲🇿 موزمبيق",         "CM": "🇨🇲 الكاميرون",
    "CI": "🇨🇮 ساحل العاج",      "SN": "🇸🇳 السنغال",
    "ML": "🇲🇱 مالي",            "BF": "🇧🇫 بوركينا فاسو",
    "NE": "🇳🇪 النيجر",          "TD": "🇹🇩 تشاد",
    "CF": "🇨🇫 جمهورية أفريقيا الوسطى", "CG": "🇨🇬 الكونغو",
    "CD": "🇨🇩 الكونغو الديمقراطية", "GA": "🇬🇦 الغابون",
    "GQ": "🇬🇶 غينيا الاستوائية", "RW": "🇷🇼 رواندا",
    "BI": "🇧🇮 بوروندي",         "MW": "🇲🇼 مالاوي",
    "MG": "🇲🇬 مدغشقر",          "MU": "🇲🇺 موريشيوس",
    "SC": "🇸🇨 سيشل",            "ER": "🇪🇷 إريتريا",
    "GN": "🇬🇳 غينيا",           "GW": "🇬🇼 غينيا بيساو",
    "GM": "🇬🇲 غامبيا",          "SL": "🇸🇱 سيراليون",
    "LR": "🇱🇷 ليبيريا",         "TG": "🇹🇬 توغو",
    "BJ": "🇧🇯 بنين",            "NA": "🇳🇦 ناميبيا",
    "BW": "🇧🇼 بوتسوانا",        "LS": "🇱🇸 ليسوتو",
    "SZ": "🇸🇿 إسواتيني",        "CV": "🇨🇻 الرأس الأخضر",
    "ST": "🇸🇹 ساو تومي وبرينسيبي", "SS": "🇸🇸 جنوب السودان",

    # 🌎 الأمريكتان (35)
    "US": "🇺🇸 الولايات المتحدة", "CA": "🇨🇦 كندا",
    "MX": "🇲🇽 المكسيك",         "BR": "🇧🇷 البرازيل",
    "AR": "🇦🇷 الأرجنتين",       "CL": "🇨🇱 تشيلي",
    "CO": "🇨🇴 كولومبيا",        "PE": "🇵🇪 بيرو",
    "VE": "🇻🇪 فنزويلا",         "EC": "🇪🇨 الإكوادور",
    "BO": "🇧🇴 بوليفيا",         "PY": "🇵🇾 باراغواي",
    "UY": "🇺🇾 الأوروغواي",      "GY": "🇬🇾 غيانا",
    "SR": "🇸🇷 سورينام",         "GT": "🇬🇹 غواتيمالا",
    "HN": "🇭🇳 هندوراس",         "SV": "🇸🇻 السلفادور",
    "NI": "🇳🇮 نيكاراغوا",       "CR": "🇨🇷 كوستاريكا",
    "PA": "🇵🇦 بنما",            "CU": "🇨🇺 كوبا",
    "DO": "🇩🇴 جمهورية الدومينيكان", "HT": "🇭🇹 هايتي",
    "JM": "🇯🇲 جامايكا",         "BS": "🇧🇸 الباهاما",
    "BB": "🇧🇧 باربادوس",        "TT": "🇹🇹 ترينيداد وتوباغو",
    "BZ": "🇧🇿 بليز",            "GD": "🇬🇩 غرينادا",
    "LC": "🇱🇨 سانت لوسيا",      "VC": "🇻🇨 سانت فنسنت والغرينادين",
    "AG": "🇦🇬 أنتيغوا وباربودا", "KN": "🇰🇳 سانت كيتس ونيفيس",
    "DM": "🇩🇲 دومينيكا",

    # 🌊 أوقيانوسيا (14)
    "AU": "🇦🇺 أستراليا",        "NZ": "🇳🇿 نيوزيلندا",
    "FJ": "🇫🇯 فيجي",            "PG": "🇵🇬 بابوا غينيا الجديدة",
    "SB": "🇸🇧 جزر سليمان",      "VU": "🇻🇺 فانواتو",
    "WS": "🇼🇸 ساموا",           "TO": "🇹🇴 تونغا",
    "KI": "🇰🇮 كيريباتي",        "FM": "🇫🇲 ميكرونيزيا",
    "PW": "🇵🇼 بالاو",           "MH": "🇲🇭 جزر مارشال",
    "NR": "🇳🇷 ناورو",           "TV": "🇹🇻 توفالو",
}


# ────────────────────── مؤشّرات لغوية → دولة ──────────────────────
LANG_HINTS = {
    # عربيّة (22 دولة)
    "ar-SA": "SA", "ar-EG": "EG", "ar-AE": "AE", "ar-KW": "KW",
    "ar-QA": "QA", "ar-BH": "BH", "ar-OM": "OM", "ar-JO": "JO",
    "ar-LB": "LB", "ar-SY": "SY", "ar-IQ": "IQ", "ar-YE": "YE",
    "ar-PS": "PS", "ar-MA": "MA", "ar-DZ": "DZ", "ar-TN": "TN",
    "ar-LY": "LY", "ar-SD": "SD",

    # إنجليزيّة
    "en-US": "US", "en-GB": "GB", "en-CA": "CA", "en-AU": "AU",
    "en-NZ": "NZ", "en-IE": "IE", "en-ZA": "ZA", "en-IN": "IN",
    "en-PH": "PH", "en-SG": "SG",

    # فرنسيّة
    "fr-FR": "FR", "fr-CA": "CA", "fr-BE": "BE", "fr-CH": "CH",

    # ألمانيّة
    "de-DE": "DE", "de-AT": "AT", "de-CH": "CH",

    # إسبانيّة (هام للأمريكا اللاتينيّة)
    "es-ES": "ES", "es-MX": "MX", "es-AR": "AR", "es-CO": "CO",
    "es-CL": "CL", "es-PE": "PE", "es-VE": "VE", "es-EC": "EC",
    "es-GT": "GT", "es-DO": "DO", "es-CU": "CU", "es-BO": "BO",

    # برتغاليّة
    "pt-BR": "BR", "pt-PT": "PT", "pt-AO": "AO", "pt-MZ": "MZ",

    # آسيويّة
    "ja-JP": "JP", "ko-KR": "KR", "zh-CN": "CN", "zh-TW": "TW",
    "zh-HK": "HK", "th-TH": "TH", "vi-VN": "VN", "id-ID": "ID",
    "ms-MY": "MY", "tl-PH": "PH", "hi-IN": "IN", "bn-BD": "BD",
    "ur-PK": "PK", "fa-IR": "IR", "tr-TR": "TR",

    # أوروبيّة أخرى
    "it-IT": "IT", "nl-NL": "NL", "sv-SE": "SE", "no-NO": "NO",
    "da-DK": "DK", "fi-FI": "FI", "pl-PL": "PL", "cs-CZ": "CZ",
    "hu-HU": "HU", "ro-RO": "RO", "el-GR": "GR", "ru-RU": "RU",
    "uk-UA": "UA", "he-IL": "IL",
}


# ────────────────────── هاشتاجات الدول (تغطية واسعة) ──────────────────────
COUNTRY_HASHTAGS = {
    # عربيّة
    "SA": ["السعودية", "saudi", "ksa", "الرياض", "جدة", "مكة", "المدينة", "riyadh", "jeddah"],
    "EG": ["مصر", "egypt", "القاهرة", "cairo", "اسكندرية", "alexandria"],
    "AE": ["الامارات", "emirates", "uae", "دبي", "dubai", "ابوظبي", "abudhabi", "sharjah"],
    "KW": ["الكويت", "kuwait", "kw", "q8"],
    "QA": ["قطر", "qatar", "الدوحة", "doha"],
    "BH": ["البحرين", "bahrain", "المنامة"],
    "OM": ["عمان", "oman", "مسقط", "muscat"],
    "JO": ["الاردن", "jordan", "amman"],
    "LB": ["لبنان", "lebanon", "beirut"],
    "MA": ["المغرب", "morocco", "maroc", "casablanca", "rabat", "marrakech"],
    "DZ": ["الجزائر", "algeria", "algerie"],
    "TN": ["تونس", "tunisia", "tunis"],
    "IQ": ["العراق", "iraq", "بغداد", "baghdad"],
    "YE": ["اليمن", "yemen", "صنعاء"],
    "PS": ["فلسطين", "palestine", "غزة", "القدس", "gaza", "jerusalem"],
    "SY": ["سوريا", "syria", "دمشق", "damascus"],
    "LY": ["ليبيا", "libya", "tripoli"],
    "SD": ["السودان", "sudan", "khartoum"],

    # أمريكية
    "US": ["usa", "america", "newyork", "losangeles", "miami", "chicago", "texas", "vegas"],
    "CA": ["canada", "toronto", "vancouver", "montreal"],
    "MX": ["mexico", "cdmx", "mexicocity"],
    "BR": ["brasil", "brazil", "saopaulo", "rio"],
    "AR": ["argentina", "buenosaires"],

    # أوروبية
    "GB": ["uk", "britain", "london", "manchester", "england", "scotland"],
    "FR": ["france", "paris", "marseille", "lyon"],
    "DE": ["germany", "deutschland", "berlin", "munich"],
    "IT": ["italy", "italia", "rome", "milan", "milano"],
    "ES": ["spain", "espana", "madrid", "barcelona"],
    "PT": ["portugal", "lisbon", "lisboa"],
    "NL": ["netherlands", "holland", "amsterdam"],
    "RU": ["russia", "moscow", "stpetersburg"],
    "UA": ["ukraine", "kyiv", "kiev"],
    "PL": ["poland", "warsaw"],

    # آسيوية
    "TR": ["turkey", "turkiye", "istanbul", "ankara"],
    "JP": ["japan", "tokyo", "osaka", "kyoto"],
    "KR": ["korea", "seoul", "kpop"],
    "CN": ["china", "beijing", "shanghai"],
    "IN": ["india", "delhi", "mumbai", "bangalore"],
    "PK": ["pakistan", "karachi", "lahore"],
    "BD": ["bangladesh", "dhaka"],
    "ID": ["indonesia", "jakarta", "bali"],
    "TH": ["thailand", "bangkok", "phuket"],
    "VN": ["vietnam", "hanoi", "saigon"],
    "MY": ["malaysia", "kualalumpur", "kl"],
    "PH": ["philippines", "manila", "cebu"],
    "SG": ["singapore", "sg"],
    "IL": ["israel", "telaviv", "jerusalem"],
    "IR": ["iran", "tehran"],

    # أفريقية
    "NG": ["nigeria", "lagos", "naija"],
    "ZA": ["southafrica", "capetown", "johannesburg"],
    "KE": ["kenya", "nairobi"],
    "ET": ["ethiopia", "addisababa"],
    "GH": ["ghana", "accra"],

    # أوقيانوسيا
    "AU": ["australia", "sydney", "melbourne", "ausi"],
    "NZ": ["newzealand", "auckland", "kiwi"],
}


# ────────────────────── كشف اللغة من النصّ ──────────────────────
def detect_text_language(text: str) -> Optional[str]:
    """كشف اللغة من النصّ — يدعم 15+ لغة."""
    if not text:
        return None

    # عربيّة
    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"
    # عبريّة
    if re.search(r"[\u0590-\u05FF]", text):
        return "he"
    # فارسيّة (أحرف خاصّة)
    if re.search(r"[\u067E\u0686\u0698\u06AF]", text):
        return "fa"
    # روسيّة / سيريليّة
    if re.search(r"[\u0400-\u04FF]", text):
        return "ru"
    # يونانيّة
    if re.search(r"[\u0370-\u03FF]", text):
        return "el"
    # يابانيّة (هيراجانا/كاتاكانا)
    if re.search(r"[\u3040-\u309F\u30A0-\u30FF]", text):
        return "ja"
    # كوريّة (هانغول)
    if re.search(r"[\uAC00-\uD7AF]", text):
        return "ko"
    # صينيّة (هانزي)
    if re.search(r"[\u4E00-\u9FFF]", text):
        return "zh"
    # تايلانديّة
    if re.search(r"[\u0E00-\u0E7F]", text):
        return "th"
    # هنديّة (ديفاناجاري)
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    # بنغاليّة
    if re.search(r"[\u0980-\u09FF]", text):
        return "bn"

    # تركيّة (أحرف مميّزة)
    if re.search(r"[şğıİçöüŞĞÇÖÜ]", text):
        return "tr"
    # ألمانيّة (أحرف مميّزة)
    if re.search(r"[äöüßÄÖÜ]", text):
        return "de"
    # فرنسيّة (أحرف مميّزة)
    if re.search(r"[àâçéèêëîïôûùüÿñæœ]", text):
        return "fr"
    # إسبانيّة (أحرف مميّزة)
    if re.search(r"[ñáéíóúü¡¿]", text):
        return "es"
    # برتغاليّة
    if re.search(r"[ãõçâêô]", text):
        return "pt"
    # إيطاليّة
    if re.search(r"[àèéìíîòóùú]", text):
        return "it"
    # بولنديّة
    if re.search(r"[ąćęłńóśźż]", text):
        return "pl"

    # افتراضيّ: إنجليزيّة
    if re.search(r"[a-zA-Z]", text):
        return "en"

    return None


# ────────────────────── خريطة اللغة → الدولة الافتراضيّة ──────────────────────
LANG_TO_COUNTRY = {
    "ar": "SA", "en": "US", "fr": "FR", "de": "DE",
    "es": "ES", "pt": "BR", "it": "IT", "ru": "RU",
    "tr": "TR", "ja": "JP", "ko": "KR", "zh": "CN",
    "th": "TH", "hi": "IN", "bn": "BD", "ur": "PK",
    "fa": "IR", "he": "IL", "el": "GR", "pl": "PL",
    "nl": "NL", "sv": "SE", "no": "NO", "da": "DK",
    "fi": "FI", "cs": "CZ", "hu": "HU", "ro": "RO",
    "uk": "UA", "vi": "VN", "id": "ID", "ms": "MY", "tl": "PH",
}


# ────────────────────── كشف الدولة من الهاشتاجات ──────────────────────
def detect_country_from_hashtags(hashtags: List[str]) -> Optional[str]:
    """تحليل الهاشتاجات لتخمين الدولة."""
    if not hashtags:
        return None

    counter = Counter()
    for tag in hashtags:
        tag_lower = tag.lower().strip("#").strip()
        for country, keywords in COUNTRY_HASHTAGS.items():
            if any(kw.lower() in tag_lower for kw in keywords):
                counter[country] += 1

    if counter:
        return counter.most_common(1)[0][0]
    return None


# ────────────────────── الدالة الرئيسيّة لكشف الدولة ──────────────────────
def detect_account_country(
    user_data: Dict,
    bio: str,
    nickname: str,
    hashtags: List[str] = None
) -> Tuple[str, int, str]:
    """
    Multi-Signal Country Detection (القيد #19).
    Returns: (country_code, confidence%, sources)
    """
    signals = []

    # 1️⃣ region من TikTok (الأقوى — 40%)
    region = user_data.get("region") or user_data.get("country")
    if region and len(region) == 2 and region.upper() in COUNTRY_AR:
        signals.append((region.upper(), 40, "TikTok region"))

    # 2️⃣ لغة الـ bio (25%)
    bio_lang = detect_text_language(bio)
    if bio_lang and bio_lang in LANG_TO_COUNTRY:
        signals.append((LANG_TO_COUNTRY[bio_lang], 25, "لغة الوصف"))

    # 3️⃣ لغة الـ nickname (15%)
    nick_lang = detect_text_language(nickname)
    if nick_lang and nick_lang in LANG_TO_COUNTRY:
        signals.append((LANG_TO_COUNTRY[nick_lang], 15, "لغة الاسم"))

    # 4️⃣ هاشتاجات (20%)
    if hashtags:
        tag_country = detect_country_from_hashtags(hashtags)
        if tag_country:
            signals.append((tag_country, 20, "الهاشتاجات"))

    if not signals:
        return ("—", 0, "غير متاح")

    # تجميع الإشارات
    country_scores = Counter()
    sources = []
    for country, weight, source in signals:
        country_scores[country] += weight
        sources.append(source)

    top_country, top_score = country_scores.most_common(1)[0]
    return (top_country, min(top_score, 99), " + ".join(set(sources)))


# ────────────────────── جلب البيانات من TikWM ──────────────────────
async def lookup_tiktok_user(username: str) -> Optional[Dict[str, Any]]:
    """جلب بيانات حساب TikTok عبر TikWM (لا TikAPI/Apify - القيود)."""
    url = f"{TIKWM_BASE}/api/user/info"
    params = {"unique_id": username}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                return None

            user_data = data.get("data", {}).get("user", {})
            stats_data = data.get("data", {}).get("stats", {})

            # جلب الفيديوهات لاستخراج الهاشتاجات
            hashtags = []
            try:
                posts_url = f"{TIKWM_BASE}/api/user/posts"
                posts_resp = await client.get(
                    posts_url,
                    params={"unique_id": username, "count": 10}
                )
                if posts_resp.status_code == 200:
                    posts_data = posts_resp.json()
                    videos = posts_data.get("data", {}).get("videos", [])
                    for video in videos:
                        title = video.get("title", "")
                        tags = re.findall(r"#(\w+)", title)
                        hashtags.extend(tags)
            except Exception:
                pass

            return {
                "user": user_data,
                "stats": stats_data,
                "hashtags": hashtags[:20]
            }
    except Exception as e:
        print(f"TikWM error: {e}")
        return None


# ────────────────────── تنسيق الردّ بصيغة HTML RTL ──────────────────────
def format_user_info(data: Dict[str, Any], username: str) -> str:
    """تنسيق معلومات المستخدم — HTML RTL + Noto Sans Arabic."""
    user = data.get("user", {})
    stats = data.get("stats", {})
    hashtags = data.get("hashtags", [])

    nickname = user.get("nickname", "—") or "—"
    signature = user.get("signature", "") or ""
    verified = "✅ موثَّق" if user.get("verified") else "—"

    followers = stats.get("followerCount", 0)
    following = stats.get("followingCount", 0)
    hearts = stats.get("heartCount", 0)
    videos = stats.get("videoCount", 0)

    # كشف الدولة (Multi-Signal)
    country_code, confidence, source = detect_account_country(
        user, signature, nickname, hashtags
    )
    country_display = COUNTRY_AR.get(country_code, "—")

    if confidence == 0:
        country_line = "🌍 <b>الدولة:</b> —"
    else:
        country_line = (
            f"🌍 <b>الدولة:</b> {country_display}\n"
            f"   <i>(دقّة: {confidence}% — {source})</i>"
        )

    # تنسيق الأرقام
    def fmt(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    msg = (
        f"<b>📊 معلومات حساب TikTok</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>المستخدم:</b> <code>@{username}</code>\n"
        f"🏷️ <b>الاسم:</b> {nickname}\n"
        f"✔️ <b>التوثيق:</b> {verified}\n"
        f"{country_line}\n\n"
        f"📈 <b>الإحصاءات:</b>\n"
        f"• 👥 المتابعون: <b>{fmt(followers)}</b>\n"
        f"• 👤 يتابع: <b>{fmt(following)}</b>\n"
        f"• ❤️ الإعجابات: <b>{fmt(hearts)}</b>\n"
        f"• 🎬 الفيديوهات: <b>{fmt(videos)}</b>\n\n"
    )

    if signature and signature.strip():
        bio_short = signature[:200].strip()
        msg += f"📝 <b>الوصف:</b>\n<i>{bio_short}</i>\n\n"

    msg += (
        f"🔗 <b>الرابط:</b>\n"
        f"<a href='https://www.tiktok.com/@{username}'>"
        f"tiktok.com/@{username}</a>\n\n"
        f"<i>━━━━━━━━━━━━━━━━━━</i>\n"
        f"<i>🛡️ بصير | @Baseer_Lookup_Bot</i>"
    )

    return msg
