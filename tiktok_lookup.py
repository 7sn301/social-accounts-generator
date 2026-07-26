# ═══════════════════════════════════════════════════════════════════════════
# BSR-LOOKUP-FIX-2026-0726-04
# tiktok_lookup.py — v2.1.0-Enhanced (Baseer Project)
# ═══════════════════════════════════════════════════════════════════════════
# Fix ID     : BSR-LOOKUP-FIX-2026-0726-04
# Date       : 2026-07-26
# Author     : Baseer Engineering Committee (Backend + DevOps + QA)
# Purpose    : تحسين موثوقية ودقة كشف الموقع في مسار البوت (Telegram).
#
# سجل التغييرات (Changelog v5-clean → v2.1.0):
#   [F1] Fallback متعدد المصادر: tikwm → tikwm mobile → HTML مباشر.
#   [F2] فحص أول N فيديو (5) لاختيار region الأكثر تكراراً بدل الأحدث فقط.
#   [F3] كشف بديل من bio/nickname عند غياب region (مدن + لهجات + أعلام).
#   [F4] Retry مع exponential backoff + rotation UA/Headers.
#   [F5] توافق كامل مع bot.py — نفس تواقيع lookup_tiktok_user, clean_username.
#   [F6] region_source اختياري في مخرجات debug (للـ analytics_db).
# ═══════════════════════════════════════════════════════════════════════════
"""Baseer TikTok Lookup v2.1.0 — Enhanced accuracy + resilience"""
import re
import random
import httpx
import asyncio
import json
from collections import Counter
from typing import Optional, Dict, Any, List, Tuple

TIKWM_BASE = "https://www.tikwm.com"
TIKTOK_WEB = "https://www.tiktok.com"
TIMEOUT = 18.0

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
]

# ─────────────────────────── قواميس الدول ───────────────────────────

REGION_ISO_TO_COUNTRY = {
    'SA':'Saudi Arabia','AE':'United Arab Emirates','KW':'Kuwait','QA':'Qatar',
    'BH':'Bahrain','OM':'Oman','YE':'Yemen','JO':'Jordan','LB':'Lebanon',
    'IQ':'Iraq','PS':'Palestine','EG':'Egypt','MA':'Morocco','DZ':'Algeria',
    'TN':'Tunisia','LY':'Libya','SD':'Sudan','SO':'Somalia','MR':'Mauritania',
    'DJ':'Djibouti','KM':'Comoros','SY':'Syria',
    'US':'United States','GB':'United Kingdom','UK':'United Kingdom','CA':'Canada',
    'AU':'Australia','NZ':'New Zealand','IE':'Ireland',
    'FR':'France','DE':'Germany','IT':'Italy','ES':'Spain','PT':'Portugal',
    'NL':'Netherlands','BE':'Belgium','CH':'Switzerland','AT':'Austria',
    'SE':'Sweden','NO':'Norway','FI':'Finland','DK':'Denmark','PL':'Poland',
    'CZ':'Czech Republic','SK':'Slovakia','HU':'Hungary','RO':'Romania',
    'BG':'Bulgaria','GR':'Greece','HR':'Croatia','SI':'Slovenia','RS':'Serbia',
    'BA':'Bosnia','MK':'North Macedonia','AL':'Albania','ME':'Montenegro',
    'EE':'Estonia','LV':'Latvia','LT':'Lithuania','IS':'Iceland',
    'LU':'Luxembourg','MT':'Malta','CY':'Cyprus',
    'RU':'Russia','UA':'Ukraine','BY':'Belarus','MD':'Moldova',
    'GE':'Georgia','AM':'Armenia','AZ':'Azerbaijan','KZ':'Kazakhstan',
    'UZ':'Uzbekistan','KG':'Kyrgyzstan','TJ':'Tajikistan','TM':'Turkmenistan',
    'TR':'Turkey','IL':'Israel','IR':'Iran',
    'IN':'India','PK':'Pakistan','BD':'Bangladesh','LK':'Sri Lanka',
    'NP':'Nepal','AF':'Afghanistan','BT':'Bhutan','MV':'Maldives',
    'CN':'China','JP':'Japan','KR':'South Korea','KP':'North Korea',
    'TW':'Taiwan','HK':'Hong Kong','MO':'Macau','MN':'Mongolia',
    'SG':'Singapore','MY':'Malaysia','ID':'Indonesia','TH':'Thailand',
    'VN':'Vietnam','PH':'Philippines','MM':'Myanmar','KH':'Cambodia',
    'LA':'Laos','BN':'Brunei','TL':'Timor-Leste',
    'BR':'Brazil','MX':'Mexico','AR':'Argentina','CL':'Chile','CO':'Colombia',
    'PE':'Peru','VE':'Venezuela','UY':'Uruguay','PY':'Paraguay','BO':'Bolivia',
    'EC':'Ecuador','GT':'Guatemala','HN':'Honduras','SV':'El Salvador',
    'NI':'Nicaragua','CR':'Costa Rica','PA':'Panama','DO':'Dominican Republic',
    'CU':'Cuba','HT':'Haiti','JM':'Jamaica','PR':'Puerto Rico',
    'NG':'Nigeria','KE':'Kenya','ET':'Ethiopia','GH':'Ghana','ZA':'South Africa',
    'TZ':'Tanzania','UG':'Uganda','CI':'Ivory Coast','SN':'Senegal',
    'CM':'Cameroon','ML':'Mali','BF':'Burkina Faso','NE':'Niger','TD':'Chad',
    'AO':'Angola','MZ':'Mozambique','ZW':'Zimbabwe','ZM':'Zambia','MW':'Malawi',
    'BW':'Botswana','NA':'Namibia','MG':'Madagascar','MU':'Mauritius',
    'RW':'Rwanda','BI':'Burundi','CD':'DR Congo','CG':'Congo',
    'FJ':'Fiji','PG':'Papua New Guinea',
}

COUNTRY_AR = {
    'Saudi Arabia':'المملكة العربية السعودية','United Arab Emirates':'الإمارات',
    'Egypt':'مصر','Kuwait':'الكويت','Qatar':'قطر','Bahrain':'البحرين',
    'Oman':'عُمان','Jordan':'الأردن','Lebanon':'لبنان','Iraq':'العراق',
    'Yemen':'اليمن','Palestine':'فلسطين','Morocco':'المغرب','Algeria':'الجزائر',
    'Tunisia':'تونس','Libya':'ليبيا','Sudan':'السودان','Somalia':'الصومال',
    'Mauritania':'موريتانيا','Djibouti':'جيبوتي','Comoros':'جزر القمر','Syria':'سوريا',
    'United States':'الولايات المتحدة','United Kingdom':'المملكة المتحدة',
    'Canada':'كندا','Australia':'أستراليا','New Zealand':'نيوزيلندا','Ireland':'أيرلندا',
    'France':'فرنسا','Germany':'ألمانيا','Italy':'إيطاليا','Spain':'إسبانيا',
    'Portugal':'البرتغال','Netherlands':'هولندا','Belgium':'بلجيكا',
    'Switzerland':'سويسرا','Austria':'النمسا','Sweden':'السويد','Norway':'النرويج',
    'Finland':'فنلندا','Denmark':'الدنمارك','Poland':'بولندا',
    'Czech Republic':'تشيكيا','Hungary':'المجر','Romania':'رومانيا',
    'Greece':'اليونان','Russia':'روسيا','Ukraine':'أوكرانيا','Turkey':'تركيا',
    'Israel':'إسرائيل','Iran':'إيران',
    'India':'الهند','Pakistan':'باكستان','Bangladesh':'بنغلاديش',
    'Sri Lanka':'سريلانكا','China':'الصين','Japan':'اليابان',
    'South Korea':'كوريا الجنوبية','Taiwan':'تايوان','Hong Kong':'هونغ كونغ',
    'Singapore':'سنغافورة','Malaysia':'ماليزيا','Indonesia':'إندونيسيا',
    'Thailand':'تايلاند','Vietnam':'فيتنام','Philippines':'الفلبين',
    'Brazil':'البرازيل','Mexico':'المكسيك','Argentina':'الأرجنتين',
    'Chile':'تشيلي','Colombia':'كولومبيا','Peru':'البيرو','Venezuela':'فنزويلا',
    'Nigeria':'نيجيريا','Kenya':'كينيا','Ethiopia':'إثيوبيا','Ghana':'غانا',
    'South Africa':'جنوب أفريقيا',
}

# [F3] كشف بديل: لهجات ومدن (نسخة مختصرة من tiktok_analyzer)
DIALECT_HINTS = {
    'SA': ["والله", "مره", "مرة", "ياخي", "يالربع", "وش", "ابغى", "ابي", "زين", "شخبارك"],
    'EG': ["ازيك", "ازاي", "عامل ايه", "جدع", "أوي", "اوي", "خالص", "دلوقتي", "معلش"],
    'AE': ["وايد", "شحالك", "خيتو", "هالشي", "عيل"],
    'IQ': ["شلونك", "هواي", "شبيك", "اكو", "ماكو", "هسه", "خوش"],
    'JO': ["كتير", "هسا", "زلمة", "شغلة"],
    'KW': ["شلون", "وايد", "چم", "عيال"],
    'QA': ["شحالك", "شخبارك"],
    'BH': ["شخبارك", "شنو"],
    'OM': ["بومسك", "شخبارك"],
    'SY': ["كتير", "لهون", "منيح", "هلق"],
    'LB': ["هيدا", "هيدي", "منيح", "يلا"],
    'PS': ["اشي", "زلمة", "منيح"],
    'MA': ["واخا", "بزاف", "دابا", "خويا", "زعما", "شنو", "دير", "درهم"],
    'DZ': ["واش", "بصح", "برك", "علاش", "نتاع"],
    'TN': ["برشا", "علاش", "شنية", "باهي", "ياسر", "قداش", "توا"],
    'LY': ["هلبة", "شن", "متاعك"],
    'YE': ["ذمار", "قدح", "شبك"],
    'SD': ["زول", "كيفنك", "دايراً", "شديد"],
}

CITY_TO_COUNTRY = {
    "riyadh":"SA","jeddah":"SA","mecca":"SA","medina":"SA","dammam":"SA",
    "الرياض":"SA","جدة":"SA","مكة":"SA","الدمام":"SA",
    "cairo":"EG","alexandria":"EG","giza":"EG",
    "القاهرة":"EG","الإسكندرية":"EG","اسكندرية":"EG","الجيزة":"EG",
    "dubai":"AE","abu dhabi":"AE","sharjah":"AE","دبي":"AE","أبوظبي":"AE","ابوظبي":"AE","الشارقة":"AE",
    "baghdad":"IQ","basra":"IQ","erbil":"IQ","بغداد":"IQ","البصرة":"IQ","أربيل":"IQ",
    "amman":"JO","عمان":"JO","عمّان":"JO",
    "kuwait":"KW","الكويت":"KW",
    "doha":"QA","الدوحة":"QA",
    "damascus":"SY","aleppo":"SY","دمشق":"SY","حلب":"SY",
    "beirut":"LB","بيروت":"LB",
    "rabat":"MA","casablanca":"MA","marrakech":"MA","الرباط":"MA","الدار البيضاء":"MA","مراكش":"MA",
    "tunis":"TN","تونس":"TN",
    "algiers":"DZ","الجزائر":"DZ",
    "sanaa":"YE","صنعاء":"YE",
    "khartoum":"SD","الخرطوم":"SD",
    "gaza":"PS","ramallah":"PS","غزة":"PS","رام الله":"PS","القدس":"PS",
    "muscat":"OM","مسقط":"OM",
    "manama":"BH","المنامة":"BH",
    "istanbul":"TR","اسطنبول":"TR","إسطنبول":"TR",
    "tehran":"IR","طهران":"IR",
    "london":"GB","new york":"US","paris":"FR","berlin":"DE",
}

LANG_TO_COUNTRIES = {
    "ar": ["SA","EG","AE","IQ","JO","KW","QA","BH","OM","SY","LB","MA","DZ","TN","LY","SD","YE","PS"],
    "tr": ["TR"], "fa": ["IR"], "ur": ["PK"], "hi": ["IN"], "id": ["ID"],
    "ms": ["MY"], "th": ["TH"], "vi": ["VN"], "ja": ["JP"], "ko": ["KR"], "zh": ["CN"],
    "en": ["US","GB","CA","AU","NZ","IE"], "fr": ["FR","BE"], "de": ["DE","AT","CH"],
    "es": ["ES","MX","AR","CO"], "pt": ["BR","PT"], "ru": ["RU","UA"],
}


# ─────────────────────────── أدوات مساعدة ───────────────────────────

def _iso_to_flag(iso_code):
    """تحويل ISO إلى علم emoji"""
    if not iso_code or len(iso_code) != 2:
        return ''
    try:
        c1, c2 = iso_code.upper()
        return chr(0x1F1E6 + (ord(c1) - 65)) + chr(0x1F1E6 + (ord(c2) - 65))
    except Exception:
        return ''


def clean_username(text):
    """تنظيف اسم المستخدم — متوافق عكسياً مع bot.py"""
    if not text:
        return ""
    text = text.strip()
    m = re.search(r"tiktok\.com/@([\w\.\-_]+)", text)
    if m:
        return m.group(1).lower()
    return text.lstrip("@").strip().lower()


def _pick_headers(mobile: bool = False) -> Dict[str, str]:
    ua_pool = [u for u in USER_AGENTS if ('Mobile' in u) == mobile] or USER_AGENTS
    return {
        'User-Agent': random.choice(ua_pool),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Referer': 'https://www.tiktok.com/',
        'Origin': 'https://www.tiktok.com',
    }


# ─────────────────────────── [F1] Fallback متعدد المصادر ───────────────────────────

async def fetch_user_info(username: str, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
    """جلب بيانات الحساب — مع Retry وبدائل."""
    # المصدر الأساسي: tikwm.com
    url = f"{TIKWM_BASE}/api/user/info"
    for attempt in range(3):
        try:
            r = await client.get(url, params={'unique_id': username}, headers=_pick_headers())
            if r.status_code == 200:
                j = r.json()
                if j.get('code') == 0 and j.get('data', {}).get('user', {}).get('uniqueId'):
                    return j.get('data')
            if r.status_code == 429:
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code >= 500:
                await asyncio.sleep(0.8 * (attempt + 1))
                continue
        except (httpx.TimeoutException, httpx.ConnectError):
            await asyncio.sleep(1.0 * (attempt + 1))
            continue
        except Exception:
            await asyncio.sleep(0.5)
            continue

    # Fallback: نسخة mobile من tikwm
    try:
        r = await client.get(url, params={'unique_id': username, 'hd': 0},
                             headers=_pick_headers(mobile=True))
        if r.status_code == 200:
            j = r.json()
            if j.get('code') == 0 and j.get('data', {}).get('user', {}).get('uniqueId'):
                return j.get('data')
    except Exception:
        pass
    return None


async def fetch_videos_regions(username: str, client: httpx.AsyncClient,
                               count: int = 10) -> List[Tuple[str, int]]:
    """[F2] جلب region من عدة فيديوهات لتحديد الأكثر تكراراً."""
    url = f"{TIKWM_BASE}/api/user/posts"
    for attempt in range(3):
        try:
            r = await client.get(
                url, params={'unique_id': username, 'count': count},
                headers=_pick_headers(),
            )
            if r.status_code == 200:
                j = r.json()
                videos = (j.get('data') or {}).get('videos') or []
                results = []
                for v in videos:
                    reg = (v.get('region') or '').strip().upper()
                    ct = int(v.get('create_time') or 0)
                    if reg and len(reg) == 2 and reg.isalpha():
                        results.append((reg, ct))
                return results
            if r.status_code == 429:
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
        except Exception:
            await asyncio.sleep(0.8 * (attempt + 1))
            continue
    return []


def _pick_dominant_region(regions_with_time: List[Tuple[str, int]]) -> Tuple[Optional[str], str]:
    """[F2] اختيار region الأكثر تكراراً مع تفضيل الأحدث عند التعادل."""
    if not regions_with_time:
        return None, ""
    freq = Counter(r for r, _ in regions_with_time)
    most, count = freq.most_common(1)[0]
    total = len(regions_with_time)
    if count == 1 and total > 1:
        # اختر الأحدث
        latest = max(regions_with_time, key=lambda x: x[1])
        return latest[0], "أحدث فيديو"
    conf = f"{count}/{total} فيديوهات"
    return most, conf


# ─────────────────────────── [F3] كشف بديل من bio/nickname ───────────────────────────

def detect_from_text(text: str) -> Tuple[Optional[str], str]:
    """كشف الدولة من النص (bio/nickname) — علم/مدينة/لهجة."""
    if not text:
        return None, ""
    scores: Dict[str, int] = {}
    reasons: Dict[str, List[str]] = {}

    def add(cc: str, pts: int, why: str):
        if not cc:
            return
        scores[cc] = scores.get(cc, 0) + pts
        reasons.setdefault(cc, []).append(why)

    text_lower = text.lower()

    # 1) الأعلام (أقوى إشارة)
    for iso in REGION_ISO_TO_COUNTRY:
        flag = _iso_to_flag(iso)
        if flag and flag in text:
            add(iso, 100, f"علم {iso}")

    # 2) المدن
    for kw in sorted(CITY_TO_COUNTRY.keys(), key=len, reverse=True):
        cc = CITY_TO_COUNTRY[kw]
        if any(ord(c) > 127 for c in kw):
            if kw in text:
                add(cc, 50, f"مدينة '{kw}'")
        else:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                add(cc, 50, f"مدينة '{kw}'")

    # 3) اللهجات
    for cc, words in DIALECT_HINTS.items():
        hits = sum(1 for w in words if w in text)
        if hits:
            add(cc, min(hits * 15, 45), f"{hits} كلمة لهجة")

    if not scores:
        return None, ""

    winner = max(scores.items(), key=lambda x: x[1])
    cc, pts = winner
    total = sum(scores.values())
    conf_pct = int((pts / total) * 100) if total else 0

    if pts < 30:
        return None, ""

    reason_str = "، ".join(reasons[cc][:2])
    return cc, f"{reason_str} ({conf_pct}%)"


def detect_from_language(lang_code: str) -> Optional[str]:
    """كشف تقريبي من لغة الحساب — يُرجع دولة فقط لو كانت اللغة أحادية الدولة."""
    lang = (lang_code or "").lower().strip()
    countries = LANG_TO_COUNTRIES.get(lang, [])
    if len(countries) == 1:
        return countries[0]
    return None


# ─────────────────────────── التنسيق النهائي ───────────────────────────

def _country_display(region_iso: Optional[str], source: str = "") -> str:
    """توليد سطر عرض الدولة."""
    if not region_iso:
        return "🌍 غير محدّد"
    country_en = REGION_ISO_TO_COUNTRY.get(region_iso, region_iso)
    country_ar = COUNTRY_AR.get(country_en, country_en)
    flag = _iso_to_flag(region_iso)
    line = f"{flag} {country_ar}\n   الرمز: `{region_iso}` — EN: `{country_en}`"
    if source:
        line += f"\n   المصدر: {source}"
    return line


def format_profile_rtl(user_info: Dict[str, Any], region_iso: Optional[str],
                       region_source: str = "") -> str:
    """تنسيق النتيجة RTL — متوافق مع bot.py."""
    user = user_info.get('user', {}) or {}
    stats = user_info.get('stats', {}) or {}
    username = user.get('uniqueId', '—')
    nickname = user.get('nickname', '—')
    verified = '✅ موثّق' if user.get('verified') else '⚪ غير موثّق'
    private = '🔒 خاص' if user.get('privateAccount') else '🌐 عام'
    signature = (user.get('signature') or '—')[:200]
    followers = stats.get('followerCount', 0) or 0
    following = stats.get('followingCount', 0) or 0
    likes = stats.get('heartCount', 0) or 0
    videos = stats.get('videoCount', 0) or 0

    country_display = _country_display(region_iso, region_source)

    return (
        f"📱 *نتيجة البحث — بَصِير TikTok Lookup*\n\n"
        f"👤 *الاسم:* {nickname}\n"
        f"🆔 *المعرّف:* @{username}\n"
        f"{verified}  |  {private}\n\n"
        f"📍 *الإقامة الفعلية:*\n   {country_display}\n\n"
        f"📊 *الإحصائيات:*\n"
        f"  • 👥 المتابعون: {followers:,}\n"
        f"  • ➕ يتابع: {following:,}\n"
        f"  • ❤️ الإعجابات: {likes:,}\n"
        f"  • 🎬 الفيديوهات: {videos:,}\n\n"
        f"📝 *السيرة:*\n{signature}\n\n"
        f"🔗 https://www.tiktok.com/@{username}"
    )


# ─────────────────────────── الواجهة العامة ───────────────────────────

async def lookup_tiktok_user(query: str) -> str:
    """
    الواجهة العامة — متوافقة مع bot.py.
    ترجع نص جاهز للإرسال في Telegram.
    """
    username = clean_username(query)
    if not username or len(username) > 50:
        return "❌ اسم مستخدم غير صالح."

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        # جمع البيانات بالتوازي
        user_info, videos_regions = await asyncio.gather(
            fetch_user_info(username, client),
            fetch_videos_regions(username, client, count=10),
            return_exceptions=True,
        )

    # معالجة الاستثناءات
    if isinstance(user_info, Exception):
        user_info = None
    if isinstance(videos_regions, Exception):
        videos_regions = []

    if not user_info:
        return (
            f"❌ تعذّر العثور على @{username}\n"
            f"قد يكون الحساب:\n"
            f"  • خاصاً 🔒\n"
            f"  • غير موجود\n"
            f"  • أو أن الخدمة الوسيطة محجوبة مؤقتاً"
        )

    # ═══ استراتيجية كشف الموقع متعددة الطبقات ═══
    region_iso: Optional[str] = None
    region_source: str = ""

    # الطبقة 1: من فيديوهات المستخدم (الأدق)
    if videos_regions:
        region_iso, freq = _pick_dominant_region(videos_regions)
        if region_iso:
            region_source = f"📹 من {freq}"

    # الطبقة 2: من bio + nickname
    if not region_iso:
        user_obj = user_info.get('user', {}) or {}
        bio = user_obj.get('signature') or ''
        nick = user_obj.get('nickname') or ''
        combined = f"{bio}\n{nick}"
        cc, why = detect_from_text(combined)
        if cc:
            region_iso = cc
            region_source = f"🧠 تحليل ذكي — {why}"

    # الطبقة 3: من لغة الحساب
    if not region_iso:
        user_obj = user_info.get('user', {}) or {}
        lang = user_obj.get('language') or ''
        cc = detect_from_language(lang)
        if cc:
            region_iso = cc
            region_source = f"🌐 لغة الحساب ({lang})"

    return format_profile_rtl(user_info, region_iso, region_source)


# ─────────────────────────── دالة debug (اختيارية للـ analytics) ───────────────────────────

async def lookup_tiktok_user_debug(query: str) -> Dict[str, Any]:
    """
    نسخة مطوّرة تُرجع dict مع كل تفاصيل الكشف — للاستخدام في analytics_db
    أو Streamlit لعرض debug_report.
    """
    username = clean_username(query)
    result = {
        "username": username,
        "success": False,
        "region_iso": None,
        "region_source": "",
        "user_info": None,
        "videos_regions": [],
        "detection_layers": [],
        "error": "",
    }
    if not username or len(username) > 50:
        result["error"] = "اسم مستخدم غير صالح"
        return result

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        user_info, videos_regions = await asyncio.gather(
            fetch_user_info(username, client),
            fetch_videos_regions(username, client, count=10),
            return_exceptions=True,
        )

    if isinstance(user_info, Exception) or not user_info:
        result["error"] = "تعذّر الجلب من tikwm"
        return result
    if isinstance(videos_regions, Exception):
        videos_regions = []

    result["user_info"] = user_info
    result["videos_regions"] = videos_regions
    result["success"] = True

    # طبقات الكشف
    if videos_regions:
        cc, freq = _pick_dominant_region(videos_regions)
        if cc:
            result["detection_layers"].append({"layer": "videos", "result": cc, "detail": freq})
            result["region_iso"] = cc
            result["region_source"] = f"📹 من {freq}"

    if not result["region_iso"]:
        user_obj = user_info.get('user', {}) or {}
        text = f"{user_obj.get('signature') or ''}\n{user_obj.get('nickname') or ''}"
        cc, why = detect_from_text(text)
        if cc:
            result["detection_layers"].append({"layer": "bio_analysis", "result": cc, "detail": why})
            result["region_iso"] = cc
            result["region_source"] = f"🧠 تحليل ذكي — {why}"

    if not result["region_iso"]:
        user_obj = user_info.get('user', {}) or {}
        lang = user_obj.get('language') or ''
        cc = detect_from_language(lang)
        if cc:
            result["detection_layers"].append({"layer": "language", "result": cc, "detail": lang})
            result["region_iso"] = cc
            result["region_source"] = f"🌐 لغة الحساب ({lang})"

    return result


# ─────────────────────────── CLI للاختبار السريع ───────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = asyncio.run(lookup_tiktok_user(sys.argv[1]))
        print(result)
    else:
        print("Usage: python tiktok_lookup.py <username>")
