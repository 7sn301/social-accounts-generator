# ═══════════════════════════════════════════════════════════════
# BSR-V217L-TIKTOK-LOOKUP-V5-CLEAN-NO-DETECTION-AHMAD-20260613
# نسخة نظيفة بدون أي آلية كشف معروضة (region مباشر فقط)
# ═══════════════════════════════════════════════════════════════
"""TikTok Lookup v5 - Clean output, no detection mechanism shown"""
import re
import random
import httpx
import asyncio
from typing import Optional, Dict, Any

TIKWM_BASE = "https://www.tikwm.com"
TIMEOUT = 15.0

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
]

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


def _iso_to_flag(iso_code):
    """تحويل ISO إلى علم emoji"""
    if not iso_code or len(iso_code) != 2:
        return ''
    try:
        c1, c2 = iso_code.upper()
        return chr(0x1F1E6 + (ord(c1) - 65)) + chr(0x1F1E6 + (ord(c2) - 65))
    except:
        return ''


def clean_username(text):
    """تنظيف اسم المستخدم"""
    text = text.strip()
    m = re.search(r"tiktok\.com/@([\w\.\-_]+)", text)
    if m:
        return m.group(1).lower()
    return text.lstrip("@").strip().lower()


async def fetch_user_info(username, client):
    """جلب بيانات الحساب من /api/user/info"""
    url = f"{TIKWM_BASE}/api/user/info"
    for attempt in range(3):
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept': 'application/json'}
            r = await client.get(url, params={'unique_id': username}, headers=headers)
            if r.status_code == 200:
                j = r.json()
                if j.get('code') == 0 and j.get('data', {}).get('user', {}).get('uniqueId'):
                    return j.get('data')
            if r.status_code == 429:
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
        except Exception:
            await asyncio.sleep(1.0)
            continue
    return None


async def fetch_user_region(username, client):
    """جلب region من آخر فيديو فقط"""
    url = f"{TIKWM_BASE}/api/user/posts"
    for attempt in range(3):
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept': 'application/json'}
            r = await client.get(url, params={'unique_id': username, 'count': 5}, headers=headers)
            if r.status_code == 200:
                j = r.json()
                videos = (j.get('data') or {}).get('videos') or []
                if not videos:
                    return None
                # أحدث فيديو
                videos_sorted = sorted(videos, key=lambda v: v.get('create_time') or 0, reverse=True)
                for v in videos_sorted:
                    reg = (v.get('region') or '').strip().upper()
                    if reg and len(reg) == 2 and reg.isalpha():
                        return reg
                return None
            if r.status_code == 429:
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
        except Exception:
            await asyncio.sleep(1.0)
            continue
    return None


def format_profile_rtl(user_info, region_iso):
    """تنسيق النتيجة RTL بدون أي تفاصيل عن آلية الكشف"""
    user = user_info.get('user', {})
    stats = user_info.get('stats', {})
    username = user.get('uniqueId', '—')
    nickname = user.get('nickname', '—')
    verified = '✅ موثّق' if user.get('verified') else '⚪ غير موثّق'
    private = '🔒 خاص' if user.get('privateAccount') else '🌐 عام'
    signature = (user.get('signature') or '—')[:200]
    followers = stats.get('followerCount', 0)
    following = stats.get('followingCount', 0)
    likes = stats.get('heartCount', 0)
    videos = stats.get('videoCount', 0)

    if region_iso:
        country_en = REGION_ISO_TO_COUNTRY.get(region_iso, region_iso)
        country_ar = COUNTRY_AR.get(country_en, country_en)
        flag = _iso_to_flag(region_iso)
        country_display = f"{flag} {country_ar}\n   الرمز: `{region_iso}` — EN: `{country_en}`"
    else:
        country_display = "🌍 غير محدّد"

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


async def lookup_tiktok_user(query):
    """الواجهة العامة"""
    username = clean_username(query)
    if not username or len(username) > 50:
        return "❌ اسم مستخدم غير صالح."
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        user_info, region_iso = await asyncio.gather(
            fetch_user_info(username, client),
            fetch_user_region(username, client),
        )
    if not user_info:
        return f"❌ تعذّر العثور على @{username}\nقد يكون خاصاً أو غير موجود."
    return format_profile_rtl(user_info, region_iso)
