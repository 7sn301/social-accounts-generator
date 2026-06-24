# ═══════════════════════════════════════════════════════════
# BSR-V217L-TIKTOK-LOOKUP-ENHANCED-V2-AHMAD-20260613
# كشف الدولة بـ 5 مستويات (region + lang + text + hashtag + emoji)
# ═══════════════════════════════════════════════════════════
"""
TikTok Lookup v2 - Enhanced worldwide country detection
- 5 مستويات للكشف
- تحليل النص (Unicode ranges)
- هاشتاجات الدولة
- رموز إيموجي الأعلام
"""
import re
import httpx
from typing import Optional, Dict, Any

TIKWM_BASE = "https://www.tikwm.com"
TIMEOUT = 15.0

# ─────────────────────────────────────────────────────────────
# 1) قاموس region → اسم الدولة (مختصر، التفاصيل في v1)
# ─────────────────────────────────────────────────────────────
REGION_MAP = {
    "SA": "🇸🇦 المملكة العربية السعودية",
    "AE": "🇦🇪 الإمارات", "KW": "🇰🇼 الكويت", "QA": "🇶🇦 قطر",
    "BH": "🇧🇭 البحرين", "OM": "🇴🇲 عُمان", "EG": "🇪🇬 مصر",
    "JO": "🇯🇴 الأردن", "LB": "🇱🇧 لبنان", "SY": "🇸🇾 سوريا",
    "IQ": "🇮🇶 العراق", "PS": "🇵🇸 فلسطين", "YE": "🇾🇪 اليمن",
    "MA": "🇲🇦 المغرب", "DZ": "🇩🇿 الجزائر", "TN": "🇹🇳 تونس",
    "LY": "🇱🇾 ليبيا", "SD": "🇸🇩 السودان", "SO": "🇸🇴 الصومال",
    "US": "🇺🇸 الولايات المتحدة", "CA": "🇨🇦 كندا", "MX": "🇲🇽 المكسيك",
    "BR": "🇧🇷 البرازيل", "AR": "🇦🇷 الأرجنتين", "CL": "🇨🇱 تشيلي",
    "CO": "🇨🇴 كولومبيا", "PE": "🇵🇪 بيرو", "VE": "🇻🇪 فنزويلا",
    "GB": "🇬🇧 المملكة المتحدة", "FR": "🇫🇷 فرنسا", "DE": "🇩🇪 ألمانيا",
    "IT": "🇮🇹 إيطاليا", "ES": "🇪🇸 إسبانيا", "PT": "🇵🇹 البرتغال",
    "NL": "🇳🇱 هولندا", "BE": "🇧🇪 بلجيكا", "CH": "🇨🇭 سويسرا",
    "SE": "🇸🇪 السويد", "NO": "🇳🇴 النرويج", "DK": "🇩🇰 الدنمارك",
    "FI": "🇫🇮 فنلندا", "PL": "🇵🇱 بولندا", "RU": "🇷🇺 روسيا",
    "UA": "🇺🇦 أوكرانيا", "TR": "🇹🇷 تركيا", "IR": "🇮🇷 إيران",
    "IL": "🇮🇱 إسرائيل", "IN": "🇮🇳 الهند", "PK": "🇵🇰 باكستان",
    "BD": "🇧🇩 بنغلاديش", "CN": "🇨🇳 الصين", "JP": "🇯🇵 اليابان",
    "KR": "🇰🇷 كوريا الجنوبية", "TW": "🇹🇼 تايوان", "HK": "🇭🇰 هونغ كونغ",
    "SG": "🇸🇬 سنغافورة", "MY": "🇲🇾 ماليزيا", "ID": "🇮🇩 إندونيسيا",
    "TH": "🇹🇭 تايلاند", "VN": "🇻🇳 فيتنام", "PH": "🇵🇭 الفلبين",
    "NG": "🇳🇬 نيجيريا", "KE": "🇰🇪 كينيا", "ZA": "🇿🇦 جنوب أفريقيا",
    "AU": "🇦🇺 أستراليا", "NZ": "🇳🇿 نيوزيلندا",
}

# ─────────────────────────────────────────────────────────────
# 2) قاموس language → اسم الدولة
# ─────────────────────────────────────────────────────────────
LANG_MAP = {
    "ar": "🇸🇦 دولة عربية", "en": "🇺🇸 إنجليزي (US/UK)",
    "es": "🇪🇸 إسبانيا / أمريكا اللاتينية", "fr": "🇫🇷 فرنسا",
    "de": "🇩🇪 ألمانيا", "it": "🇮🇹 إيطاليا",
    "pt": "🇵🇹 البرتغال / البرازيل", "ru": "🇷🇺 روسيا",
    "tr": "🇹🇷 تركيا", "ja": "🇯🇵 اليابان",
    "ko": "🇰🇷 كوريا الجنوبية", "zh": "🇨🇳 الصين",
    "hi": "🇮🇳 الهند", "id": "🇮🇩 إندونيسيا",
    "th": "🇹🇭 تايلاند", "vi": "🇻🇳 فيتنام",
    "fa": "🇮🇷 إيران", "ur": "🇵🇰 باكستان",
    "nl": "🇳🇱 هولندا", "pl": "🇵🇱 بولندا",
    "he": "🇮🇱 إسرائيل", "el": "🇬🇷 اليونان",
}

# ─────────────────────────────────────────────────────────────
# 3) كلمات مفتاحية في السيرة → دولة
# ─────────────────────────────────────────────────────────────
KEYWORD_MAP = {
    # عربي
    "السعودية": "🇸🇦 المملكة العربية السعودية",
    "السعوديه": "🇸🇦 المملكة العربية السعودية",
    "ksa": "🇸🇦 المملكة العربية السعودية",
    "saudi": "🇸🇦 المملكة العربية السعودية",
    "riyadh": "🇸🇦 المملكة العربية السعودية",
    "الرياض": "🇸🇦 المملكة العربية السعودية",
    "جدة": "🇸🇦 المملكة العربية السعودية",
    "الامارات": "🇦🇪 الإمارات",
    "الإمارات": "🇦🇪 الإمارات",
    "uae": "🇦🇪 الإمارات",
    "dubai": "🇦🇪 الإمارات",
    "دبي": "🇦🇪 الإمارات",
    "أبوظبي": "🇦🇪 الإمارات",
    "الكويت": "🇰🇼 الكويت",
    "kuwait": "🇰🇼 الكويت",
    "قطر": "🇶🇦 قطر",
    "qatar": "🇶🇦 قطر",
    "doha": "🇶🇦 قطر",
    "البحرين": "🇧🇭 البحرين",
    "bahrain": "🇧🇭 البحرين",
    "عمان": "🇴🇲 عُمان",
    "oman": "🇴🇲 عُمان",
    "مصر": "🇪🇬 مصر",
    "egypt": "🇪🇬 مصر",
    "cairo": "🇪🇬 مصر",
    "القاهرة": "🇪🇬 مصر",
    "الأردن": "🇯🇴 الأردن",
    "الاردن": "🇯🇴 الأردن",
    "jordan": "🇯🇴 الأردن",
    "amman": "🇯🇴 الأردن",
    "لبنان": "🇱🇧 لبنان",
    "lebanon": "🇱🇧 لبنان",
    "beirut": "🇱🇧 لبنان",
    "بيروت": "🇱🇧 لبنان",
    "العراق": "🇮🇶 العراق",
    "iraq": "🇮🇶 العراق",
    "baghdad": "🇮🇶 العراق",
    "بغداد": "🇮🇶 العراق",
    "اليمن": "🇾🇪 اليمن",
    "yemen": "🇾🇪 اليمن",
    "المغرب": "🇲🇦 المغرب",
    "morocco": "🇲🇦 المغرب",
    "الجزائر": "🇩🇿 الجزائر",
    "algeria": "🇩🇿 الجزائر",
    "تونس": "🇹🇳 تونس",
    "tunisia": "🇹🇳 تونس",
    "ليبيا": "🇱🇾 ليبيا",
    "libya": "🇱🇾 ليبيا",
    "السودان": "🇸🇩 السودان",
    "sudan": "🇸🇩 السودان",
    "فلسطين": "🇵🇸 فلسطين",
    "palestine": "🇵🇸 فلسطين",
    "سوريا": "🇸🇾 سوريا",
    "syria": "🇸🇾 سوريا",
    # إنجليزي
    "usa": "🇺🇸 الولايات المتحدة",
    "america": "🇺🇸 الولايات المتحدة",
    "new york": "🇺🇸 الولايات المتحدة",
    "los angeles": "🇺🇸 الولايات المتحدة",
    "uk": "🇬🇧 المملكة المتحدة",
    "london": "🇬🇧 المملكة المتحدة",
    "england": "🇬🇧 المملكة المتحدة",
    "canada": "🇨🇦 كندا",
    "toronto": "🇨🇦 كندا",
    "brazil": "🇧🇷 البرازيل",
    "brasil": "🇧🇷 البرازيل",
    "mexico": "🇲🇽 المكسيك",
    "argentina": "🇦🇷 الأرجنتين",
    "france": "🇫🇷 فرنسا",
    "paris": "🇫🇷 فرنسا",
    "germany": "🇩🇪 ألمانيا",
    "berlin": "🇩🇪 ألمانيا",
    "italy": "🇮🇹 إيطاليا",
    "italia": "🇮🇹 إيطاليا",
    "rome": "🇮🇹 إيطاليا",
    "spain": "🇪🇸 إسبانيا",
    "españa": "🇪🇸 إسبانيا",
    "madrid": "🇪🇸 إسبانيا",
    "portugal": "🇵🇹 البرتغال",
    "lisbon": "🇵🇹 البرتغال",
    "netherlands": "🇳🇱 هولندا",
    "russia": "🇷🇺 روسيا",
    "moscow": "🇷🇺 روسيا",
    "turkey": "🇹🇷 تركيا",
    "türkiye": "🇹🇷 تركيا",
    "istanbul": "🇹🇷 تركيا",
    "iran": "🇮🇷 إيران",
    "tehran": "🇮🇷 إيران",
    "india": "🇮🇳 الهند",
    "mumbai": "🇮🇳 الهند",
    "pakistan": "🇵🇰 باكستان",
    "karachi": "🇵🇰 باكستان",
    "china": "🇨🇳 الصين",
    "japan": "🇯🇵 اليابان",
    "tokyo": "🇯🇵 اليابان",
    "korea": "🇰🇷 كوريا الجنوبية",
    "seoul": "🇰🇷 كوريا الجنوبية",
    "indonesia": "🇮🇩 إندونيسيا",
    "jakarta": "🇮🇩 إندونيسيا",
    "thailand": "🇹🇭 تايلاند",
    "bangkok": "🇹🇭 تايلاند",
    "vietnam": "🇻🇳 فيتنام",
    "philippines": "🇵🇭 الفلبين",
    "manila": "🇵🇭 الفلبين",
    "malaysia": "🇲🇾 ماليزيا",
    "australia": "🇦🇺 أستراليا",
    "sydney": "🇦🇺 أستراليا",
    "nigeria": "🇳🇬 نيجيريا",
    "south africa": "🇿🇦 جنوب أفريقيا",
    "kenya": "🇰🇪 كينيا",
}

# ─────────────────────────────────────────────────────────────
# 4) إيموجي الأعلام → دولة
# ─────────────────────────────────────────────────────────────
FLAG_EMOJI_MAP = {
    "🇸🇦": "🇸🇦 المملكة العربية السعودية",
    "🇦🇪": "🇦🇪 الإمارات",
    "🇰🇼": "🇰🇼 الكويت",
    "🇶🇦": "🇶🇦 قطر",
    "🇧🇭": "🇧🇭 البحرين",
    "🇴🇲": "🇴🇲 عُمان",
    "🇪🇬": "🇪🇬 مصر",
    "🇯🇴": "🇯🇴 الأردن",
    "🇱🇧": "🇱🇧 لبنان",
    "🇸🇾": "🇸🇾 سوريا",
    "🇮🇶": "🇮🇶 العراق",
    "🇵🇸": "🇵🇸 فلسطين",
    "🇾🇪": "🇾🇪 اليمن",
    "🇲🇦": "🇲🇦 المغرب",
    "🇩🇿": "🇩🇿 الجزائر",
    "🇹🇳": "🇹🇳 تونس",
    "🇱🇾": "🇱🇾 ليبيا",
    "🇸🇩": "🇸🇩 السودان",
    "🇺🇸": "🇺🇸 الولايات المتحدة",
    "🇬🇧": "🇬🇧 المملكة المتحدة",
    "🇨🇦": "🇨🇦 كندا",
    "🇲🇽": "🇲🇽 المكسيك",
    "🇧🇷": "🇧🇷 البرازيل",
    "🇦🇷": "🇦🇷 الأرجنتين",
    "🇫🇷": "🇫🇷 فرنسا",
    "🇩🇪": "🇩🇪 ألمانيا",
    "🇮🇹": "🇮🇹 إيطاليا",
    "🇪🇸": "🇪🇸 إسبانيا",
    "🇵🇹": "🇵🇹 البرتغال",
    "🇳🇱": "🇳🇱 هولندا",
    "🇷🇺": "🇷🇺 روسيا",
    "🇹🇷": "🇹🇷 تركيا",
    "🇮🇷": "🇮🇷 إيران",
    "🇮🇳": "🇮🇳 الهند",
    "🇵🇰": "🇵🇰 باكستان",
    "🇨🇳": "🇨🇳 الصين",
    "🇯🇵": "🇯🇵 اليابان",
    "🇰🇷": "🇰🇷 كوريا الجنوبية",
    "🇮🇩": "🇮🇩 إندونيسيا",
    "🇹🇭": "🇹🇭 تايلاند",
    "🇵🇭": "🇵🇭 الفلبين",
    "🇲🇾": "🇲🇾 ماليزيا",
    "🇦🇺": "🇦🇺 أستراليا",
    "🇳🇬": "🇳🇬 نيجيريا",
    "🇿🇦": "🇿🇦 جنوب أفريقيا",
}


def clean_username(text: str) -> str:
    """تنظيف اسم المستخدم"""
    text = text.strip()
    m = re.search(r"tiktok\.com/@([\w\.\-_]+)", text)
    if m:
        return m.group(1)
    return text.lstrip("@").strip()


def detect_script(text: str) -> str:
    """كشف نوع الكتابة من Unicode ranges"""
    if not text:
        return ""
    arabic = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    hebrew = sum(1 for c in text if "\u0590" <= c <= "\u05FF")
    cjk = sum(1 for c in text if "\u4E00" <= c <= "\u9FFF")
    hiragana = sum(1 for c in text if "\u3040" <= c <= "\u309F")
    katakana = sum(1 for c in text if "\u30A0" <= c <= "\u30FF")
    hangul = sum(1 for c in text if "\uAC00" <= c <= "\uD7AF")
    thai = sum(1 for c in text if "\u0E00" <= c <= "\u0E7F")
    cyrillic = sum(1 for c in text if "\u0400" <= c <= "\u04FF")
    devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    total = len(text)

    if arabic / max(total, 1) > 0.2:
        return "arabic"
    if hebrew / max(total, 1) > 0.2:
        return "hebrew"
    if (hiragana + katakana) / max(total, 1) > 0.15:
        return "japanese"
    if hangul / max(total, 1) > 0.15:
        return "korean"
    if cjk / max(total, 1) > 0.15:
        return "chinese"
    if thai / max(total, 1) > 0.15:
        return "thai"
    if cyrillic / max(total, 1) > 0.15:
        return "cyrillic"
    if devanagari / max(total, 1) > 0.15:
        return "indian"
    return ""


SCRIPT_TO_COUNTRY = {
    "arabic": "🇸🇦 دولة عربية (محتمل)",
    "hebrew": "🇮🇱 إسرائيل",
    "japanese": "🇯🇵 اليابان",
    "korean": "🇰🇷 كوريا الجنوبية",
    "chinese": "🇨🇳 الصين / تايوان / هونغ كونغ",
    "thai": "🇹🇭 تايلاند",
    "cyrillic": "🇷🇺 روسيا / أوكرانيا",
    "indian": "🇮🇳 الهند",
}


async def fetch_tiktok_profile(username: str) -> Optional[Dict[str, Any]]:
    """جلب بيانات TikTok"""
    url = f"{TIKWM_BASE}/api/user/info"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(url, params={"unique_id": username})
            if r.status_code != 200:
                return None
            data = r.json()
            if data.get("code") != 0:
                return None
            return data.get("data", {})
    except Exception:
        return None


def detect_country(profile: Dict[str, Any]) -> str:
    """كشف الدولة — 5 مستويات"""
    user = profile.get("user", {})
    region = (user.get("region") or "").upper().strip()
    language = (user.get("language") or "").lower().strip()[:2]
    nickname = user.get("nickname") or ""
    signature = user.get("signature") or ""
    unique_id = user.get("uniqueId") or ""
    full_text = f"{nickname} {signature} {unique_id}"
    text_lower = full_text.lower()

    # المستوى 1: region مباشر
    if region and region in REGION_MAP:
        return REGION_MAP[region]

    # المستوى 2: إيموجي الأعلام
    for flag, country in FLAG_EMOJI_MAP.items():
        if flag in full_text:
            return country

    # المستوى 3: كلمات مفتاحية
    for keyword, country in KEYWORD_MAP.items():
        if keyword in text_lower:
            return country

    # المستوى 4: تحليل النص (Unicode)
    script = detect_script(full_text)
    if script and script in SCRIPT_TO_COUNTRY:
        return SCRIPT_TO_COUNTRY[script]

    # المستوى 5: اللغة
    if language and language in LANG_MAP:
        return LANG_MAP[language]

    return "🌍 غير محدّد"


def format_profile_rtl(profile: Dict[str, Any], country: str) -> str:
    """تنسيق RTL"""
    user = profile.get("user", {})
    stats = profile.get("stats", {})
    username = user.get("uniqueId", "—")
    nickname = user.get("nickname", "—")
    verified = "✅ موثّق" if user.get("verified") else "⚪ غير موثّق"
    private = "🔒 خاص" if user.get("privateAccount") else "🌐 عام"
    signature = (user.get("signature") or "—")[:200]

    followers = stats.get("followerCount", 0)
    following = stats.get("followingCount", 0)
    likes = stats.get("heartCount", 0)
    videos = stats.get("videoCount", 0)

    return (
        f"📱 *نتيجة البحث — TikTok Lookup*\n\n"
        f"👤 الاسم: {nickname}\n"
        f"🆔 المعرّف: @{username}\n"
        f"{verified}  |  {private}\n"
        f"🌍 الدولة: {country}\n\n"
        f"📊 الإحصائيات:\n"
        f"  • المتابعون: {followers:,}\n"
        f"  • يتابع: {following:,}\n"
        f"  • الإعجابات: {likes:,}\n"
        f"  • الفيديوهات: {videos:,}\n\n"
        f"📝 السيرة:\n{signature}\n\n"
        f"🔗 https://www.tiktok.com/@{username}"
    )


async def lookup_tiktok_user(query: str) -> str:
    """الواجهة العامة"""
    username = clean_username(query)
    if not username or len(username) > 50:
        return "❌ اسم مستخدم غير صالح."

    profile = await fetch_tiktok_profile(username)
    if not profile:
        return f"❌ تعذّر العثور على الحساب @{username}"

    country = detect_country(profile)
    return format_profile_rtl(profile, country)
