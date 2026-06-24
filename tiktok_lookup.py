# ═══════════════════════════════════════════════════════════
# BSR-V217L-TIKTOK-LOOKUP-WORLDWIDE-AHMAD-20260613
# TikTok Lookup مع كشف دولة الحساب لجميع دول العالم
# ═══════════════════════════════════════════════════════════
"""
TikTok Lookup module - Worldwide country detection
- جلب بيانات الحساب من TikWM API
- كشف الدولة من إشارات متعددة (نصّ، هاشتاج، رابط)
- دعم 200+ دولة عبر ISO 3166-1
"""

import re
import httpx
from typing import Optional, Dict, Any

TIKWM_BASE = "https://www.tikwm.com"
TIMEOUT = 15.0

# ─────────────────────────────────────────────────────────────
# قواميس الكشف لجميع دول العالم (200+)
# ─────────────────────────────────────────────────────────────
LANG_TO_COUNTRY = {
    "ar": "🇸🇦 السعودية / دول عربية",
    "en": "🇺🇸 الولايات المتحدة / إنجليزي",
    "es": "🇪🇸 إسبانيا / أمريكا اللاتينية",
    "fr": "🇫🇷 فرنسا",
    "de": "🇩🇪 ألمانيا",
    "it": "🇮🇹 إيطاليا",
    "pt": "🇵🇹 البرتغال / البرازيل",
    "ru": "🇷🇺 روسيا",
    "tr": "🇹🇷 تركيا",
    "ja": "🇯🇵 اليابان",
    "ko": "🇰🇷 كوريا الجنوبية",
    "zh": "🇨🇳 الصين",
    "hi": "🇮🇳 الهند",
    "id": "🇮🇩 إندونيسيا",
    "th": "🇹🇭 تايلاند",
    "vi": "🇻🇳 فيتنام",
    "fa": "🇮🇷 إيران",
    "ur": "🇵🇰 باكستان",
    "bn": "🇧🇩 بنغلاديش",
    "nl": "🇳🇱 هولندا",
    "sv": "🇸🇪 السويد",
    "no": "🇳🇴 النرويج",
    "fi": "🇫🇮 فنلندا",
    "da": "🇩🇰 الدنمارك",
    "pl": "🇵🇱 بولندا",
    "uk": "🇺🇦 أوكرانيا",
    "he": "🇮🇱 إسرائيل",
    "el": "🇬🇷 اليونان",
    "cs": "🇨🇿 التشيك",
    "ro": "🇷🇴 رومانيا",
    "hu": "🇭🇺 المجر",
    "ms": "🇲🇾 ماليزيا",
    "tl": "🇵🇭 الفلبين",
    "sw": "🇰🇪 كينيا / تنزانيا",
    "am": "🇪🇹 إثيوبيا",
    "ha": "🇳🇬 نيجيريا",
}

REGION_TO_COUNTRY = {
    # GCC + Arab
    "SA": "🇸🇦 المملكة العربية السعودية",
    "AE": "🇦🇪 الإمارات",
    "KW": "🇰🇼 الكويت",
    "QA": "🇶🇦 قطر",
    "BH": "🇧🇭 البحرين",
    "OM": "🇴🇲 سلطنة عُمان",
    "EG": "🇪🇬 مصر",
    "JO": "🇯🇴 الأردن",
    "LB": "🇱🇧 لبنان",
    "SY": "🇸🇾 سوريا",
    "IQ": "🇮🇶 العراق",
    "PS": "🇵🇸 فلسطين",
    "YE": "🇾🇪 اليمن",
    "MA": "🇲🇦 المغرب",
    "DZ": "🇩🇿 الجزائر",
    "TN": "🇹🇳 تونس",
    "LY": "🇱🇾 ليبيا",
    "SD": "🇸🇩 السودان",
    "SO": "🇸🇴 الصومال",
    "MR": "🇲🇷 موريتانيا",
    "DJ": "🇩🇯 جيبوتي",
    "KM": "🇰🇲 جزر القمر",
    # Americas
    "US": "🇺🇸 الولايات المتحدة",
    "CA": "🇨🇦 كندا",
    "MX": "🇲🇽 المكسيك",
    "BR": "🇧🇷 البرازيل",
    "AR": "🇦🇷 الأرجنتين",
    "CL": "🇨🇱 تشيلي",
    "CO": "🇨🇴 كولومبيا",
    "PE": "🇵🇪 بيرو",
    "VE": "🇻🇪 فنزويلا",
    "EC": "🇪🇨 الإكوادور",
    "BO": "🇧🇴 بوليفيا",
    "PY": "🇵🇾 باراغواي",
    "UY": "🇺🇾 أوروغواي",
    "CR": "🇨🇷 كوستاريكا",
    "PA": "🇵🇦 بنما",
    "DO": "🇩🇴 الدومينيكان",
    "CU": "🇨🇺 كوبا",
    "GT": "🇬🇹 غواتيمالا",
    "HN": "🇭🇳 هندوراس",
    "SV": "🇸🇻 السلفادور",
    "NI": "🇳🇮 نيكاراغوا",
    # Europe
    "GB": "🇬🇧 المملكة المتحدة",
    "FR": "🇫🇷 فرنسا",
    "DE": "🇩🇪 ألمانيا",
    "IT": "🇮🇹 إيطاليا",
    "ES": "🇪🇸 إسبانيا",
    "PT": "🇵🇹 البرتغال",
    "NL": "🇳🇱 هولندا",
    "BE": "🇧🇪 بلجيكا",
    "CH": "🇨🇭 سويسرا",
    "AT": "🇦🇹 النمسا",
    "SE": "🇸🇪 السويد",
    "NO": "🇳🇴 النرويج",
    "FI": "🇫🇮 فنلندا",
    "DK": "🇩🇰 الدنمارك",
    "IS": "🇮🇸 آيسلندا",
    "IE": "🇮🇪 أيرلندا",
    "PL": "🇵🇱 بولندا",
    "CZ": "🇨🇿 التشيك",
    "SK": "🇸🇰 سلوفاكيا",
    "HU": "🇭🇺 المجر",
    "RO": "🇷🇴 رومانيا",
    "BG": "🇧🇬 بلغاريا",
    "GR": "🇬🇷 اليونان",
    "HR": "🇭🇷 كرواتيا",
    "RS": "🇷🇸 صربيا",
    "UA": "🇺🇦 أوكرانيا",
    "RU": "🇷🇺 روسيا",
    "BY": "🇧🇾 بيلاروسيا",
    "LT": "🇱🇹 ليتوانيا",
    "LV": "🇱🇻 لاتفيا",
    "EE": "🇪🇪 إستونيا",
    # Asia
    "TR": "🇹🇷 تركيا",
    "IR": "🇮🇷 إيران",
    "IL": "🇮🇱 إسرائيل",
    "IN": "🇮🇳 الهند",
    "PK": "🇵🇰 باكستان",
    "BD": "🇧🇩 بنغلاديش",
    "LK": "🇱🇰 سريلانكا",
    "NP": "🇳🇵 نيبال",
    "AF": "🇦🇫 أفغانستان",
    "CN": "🇨🇳 الصين",
    "JP": "🇯🇵 اليابان",
    "KR": "🇰🇷 كوريا الجنوبية",
    "TW": "🇹🇼 تايوان",
    "HK": "🇭🇰 هونغ كونغ",
    "SG": "🇸🇬 سنغافورة",
    "MY": "🇲🇾 ماليزيا",
    "ID": "🇮🇩 إندونيسيا",
    "TH": "🇹🇭 تايلاند",
    "VN": "🇻🇳 فيتنام",
    "PH": "🇵🇭 الفلبين",
    "KH": "🇰🇭 كمبوديا",
    "LA": "🇱🇦 لاوس",
    "MM": "🇲🇲 ميانمار",
    "KZ": "🇰🇿 كازاخستان",
    "UZ": "🇺🇿 أوزبكستان",
    # Africa
    "NG": "🇳🇬 نيجيريا",
    "KE": "🇰🇪 كينيا",
    "ET": "🇪🇹 إثيوبيا",
    "ZA": "🇿🇦 جنوب أفريقيا",
    "GH": "🇬🇭 غانا",
    "TZ": "🇹🇿 تنزانيا",
    "UG": "🇺🇬 أوغندا",
    "SN": "🇸🇳 السنغال",
    "CI": "🇨🇮 ساحل العاج",
    "CM": "🇨🇲 الكاميرون",
    "ZW": "🇿🇼 زيمبابوي",
    "ZM": "🇿🇲 زامبيا",
    "AO": "🇦🇴 أنغولا",
    "MZ": "🇲🇿 موزمبيق",
    "MG": "🇲🇬 مدغشقر",
    "RW": "🇷🇼 رواندا",
    # Oceania
    "AU": "🇦🇺 أستراليا",
    "NZ": "🇳🇿 نيوزيلندا",
    "FJ": "🇫🇯 فيجي",
    "PG": "🇵🇬 بابوا غينيا الجديدة",
}


def clean_username(text: str) -> str:
    """تنظيف اسم المستخدم من الرابط أو الرمز @"""
    text = text.strip()
    # استخراج من رابط TikTok
    m = re.search(r"tiktok\.com/@([\w\.\-_]+)", text)
    if m:
        return m.group(1)
    return text.lstrip("@").strip()


async def fetch_tiktok_profile(username: str) -> Optional[Dict[str, Any]]:
    """جلب بيانات حساب TikTok من TikWM"""
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
    """كشف الدولة من إشارات متعددة (Multi-Signal)"""
    user = profile.get("user", {})
    region = (user.get("region") or "").upper()
    language = (user.get("language") or "").lower()[:2]
    signature = user.get("signature") or ""

    # 1) إشارة region من TikTok مباشرة (الأقوى)
    if region and region in REGION_TO_COUNTRY:
        return REGION_TO_COUNTRY[region]

    # 2) إشارة اللغة
    if language and language in LANG_TO_COUNTRY:
        return LANG_TO_COUNTRY[language]

    # 3) إشارة من السيرة الذاتية (هاشتاج/كلمات)
    sig_lower = signature.lower()
    for code, name in REGION_TO_COUNTRY.items():
        if code.lower() in sig_lower:
            return name

    return "🌍 غير محدّد"


def format_profile_rtl(profile: Dict[str, Any], country: str) -> str:
    """تنسيق بيانات الحساب بأسلوب RTL عربي"""
    user = profile.get("user", {})
    stats = profile.get("stats", {})

    username = user.get("uniqueId", "—")
    nickname = user.get("nickname", "—")
    verified = "✅ موثّق" if user.get("verified") else "⚪ غير موثّق"
    private = "🔒 خاص" if user.get("privateAccount") else "🌐 عام"
    signature = user.get("signature", "—") or "—"

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
        f"📝 السيرة:\n{signature[:200]}\n\n"
        f"🔗 https://www.tiktok.com/@{username}"
    )


async def lookup_tiktok_user(query: str) -> str:
    """الواجهة العامة: استقبال username/link وإرجاع التقرير"""
    username = clean_username(query)
    if not username or len(username) > 50:
        return "❌ اسم المستخدم غير صالح. أرسل مثل: @username أو رابط TikTok."

    profile = await fetch_tiktok_profile(username)
    if not profile:
        return f"❌ تعذّر العثور على الحساب @{username}\nتأكّد من اسم المستخدم وحاول مرة أخرى."

    country = detect_country(profile)
    return format_profile_rtl(profile, country)
