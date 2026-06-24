# ═══════════════════════════════════════════════════════════════
# BSR-V217L-TIKTOK-LOOKUP-V3-BASEER-CLONE-AHMAD-20260613
# نسخة طبق الأصل من آلية موقع بصير (app.py)
# ═══════════════════════════════════════════════════════════════
"""TikTok Lookup v3 - Baseer clone for Telegram Bot"""
import re
import time
import random
import httpx
from datetime import datetime
from collections import Counter
from typing import Optional, Dict, Any

TIKWM_BASE = "https://www.tikwm.com"
TIMEOUT = 15.0

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
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
    'South Africa':'جنوب أفريقيا','Australia':'أستراليا',
}

CELEBRITIES = {
    "khaby.lame":{"country":"Italy","name":"Khabane Lame"},
    "aboflah":{"country":"Kuwait","name":"AboFlah"},
    "amrdiab":{"country":"Egypt","name":"Amr Diab"},
    "mohamedramadanws":{"country":"Egypt","name":"Mohamed Ramadan"},
    "blackpinkofficial":{"country":"South Korea","name":"BLACKPINK"},
    "bts_official_bighit":{"country":"South Korea","name":"BTS"},
    "bellapoarch":{"country":"Philippines","name":"Bella Poarch"},
    "lalisa_manobal":{"country":"Thailand","name":"Lisa"},
    "cristiano":{"country":"Portugal","name":"Cristiano Ronaldo"},
    "mrbeast":{"country":"United States","name":"MrBeast"},
    "charlidamelio":{"country":"United States","name":"Charli D'Amelio"},
    "therock":{"country":"United States","name":"Dwayne Johnson"},
    "selenagomez":{"country":"United States","name":"Selena Gomez"},
    "taylorswift":{"country":"United States","name":"Taylor Swift"},
    "billieeilish":{"country":"United States","name":"Billie Eilish"},
    "drake":{"country":"Canada","name":"Drake"},
    "justinbieber":{"country":"Canada","name":"Justin Bieber"},
    "shakira":{"country":"Colombia","name":"Shakira"},
    "messi":{"country":"Argentina","name":"Lionel Messi"},
    "anitta":{"country":"Brazil","name":"Anitta"},
    "neymarjr":{"country":"Brazil","name":"Neymar Jr"},
    "wizkidayo":{"country":"Nigeria","name":"Wizkid"},
}

def _iso_to_flag(iso_code):
    if not iso_code or len(iso_code)!=2: return ''
    try:
        c1,c2 = iso_code.upper()
        return chr(0x1F1E6+(ord(c1)-65))+chr(0x1F1E6+(ord(c2)-65))
    except: return ''

def clean_username(text):
    text = text.strip()
    m = re.search(r"tiktok\.com/@([\w\.\-_]+)", text)
    if m: return m.group(1).lower()
    return text.lstrip("@").strip().lower()


async def fetch_user_info(username, client):
    """جلب بيانات الحساب من /api/user/info"""
    url = f"{TIKWM_BASE}/api/user/info"
    for attempt in range(3):
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept':'application/json'}
            r = await client.get(url, params={'unique_id': username}, headers=headers)
            if r.status_code == 200:
                j = r.json()
                if j.get('code') == 0 and j.get('data',{}).get('user',{}).get('uniqueId'):
                    return j.get('data')
            if r.status_code == 429:
                await _async_sleep(1.5*(attempt+1))
                continue
        except Exception:
            await _async_sleep(1.0)
            continue
    return None


async def fetch_user_posts(username, client):
    """جلب آخر 5 فيديوهات + region لكل واحد — الآلية السرية لموقع بصير"""
    url = f"{TIKWM_BASE}/api/user/posts"
    for attempt in range(3):
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept':'application/json'}
            r = await client.get(url, params={'unique_id': username, 'count': 5}, headers=headers)
            if r.status_code == 200:
                j = r.json()
                videos = (j.get('data') or {}).get('videos') or []
                if not videos:
                    return {'regions_seq': [], 'times_seq': []}
                # ترتيب حسب create_time DESC
                videos_sorted = sorted(videos, key=lambda v: v.get('create_time') or 0, reverse=True)
                regions_seq = []
                times_seq = []
                for v in videos_sorted:
                    reg = (v.get('region') or '').strip().upper()
                    ts = v.get('create_time') or 0
                    if reg and len(reg)==2 and reg.isalpha():
                        regions_seq.append(reg)
                        times_seq.append(ts)
                return {'regions_seq': regions_seq, 'times_seq': times_seq}
            if r.status_code == 429:
                await _async_sleep(1.5*(attempt+1))
                continue
        except Exception:
            await _async_sleep(1.0)
            continue
    return {'regions_seq': [], 'times_seq': []}


async def _async_sleep(s):
    import asyncio
    await asyncio.sleep(s)


def _infer_timezone_from_hours(timestamps):
    """يستنتج timezone من ساعات النشر UTC"""
    if not timestamps or len(timestamps) < 3:
        return None
    hours_utc = []
    for ts in timestamps:
        try:
            h = datetime.utcfromtimestamp(int(ts)).hour
            hours_utc.append(h)
        except: continue
    if len(hours_utc) < 3: return None
    avg_hour = sum(hours_utc) / len(hours_utc)
    offset = round(19 - avg_hour)
    if offset > 14: offset -= 24
    elif offset < -12: offset += 24
    timezone_map = {
        -8:'US',-7:'US',-6:'US',-5:'US',-4:'US',-3:'BR',-2:'BR',-1:'BR',
        0:'GB',1:'DE',2:'EG',3:'SA',4:'AE',5:'PK',6:'BD',7:'TH',
        8:'CN',9:'JP',10:'AU',
    }
    return timezone_map.get(offset)


def detect_actual_residence(regions_seq, times_seq):
    """الإقامة الفعلية وفق 3 إشارات (نسخ طبق الأصل من موقع بصير)"""
    if not regions_seq:
        return {'actual':None,'previous':None,'confidence':0,'type':'unknown','tz_match':False}
    last_3 = regions_seq[:3]
    last_5 = regions_seq[:5]
    counter_5 = Counter(last_5)
    top_country, top_count = counter_5.most_common(1)[0]
    if len(set(last_3))==1 and last_3[0]:
        actual = last_3[0]
        confidence = 85
        rtype = 'ثابت' if top_count>=4 else 'انتقال حديث'
    elif top_count >= 4:
        actual = top_country
        confidence = 80
        rtype = 'ثابت'
    elif top_count >= 3:
        actual = top_country
        confidence = 70
        rtype = 'غالباً ثابت'
    else:
        actual = regions_seq[0]
        confidence = 50
        rtype = 'مسافر/متنقّل'
    previous = None
    if len(regions_seq) >= 5:
        older = regions_seq[3:]
        if older:
            older_top = Counter(older).most_common(1)[0][0]
            if older_top and older_top != actual:
                previous = older_top
    tz_iso = _infer_timezone_from_hours(times_seq)
    tz_match = bool(tz_iso and tz_iso == actual)
    if tz_match:
        confidence = min(confidence+10, 95)
    return {
        'actual': actual, 'previous': previous,
        'confidence': confidence, 'type': rtype,
        'tz_match': tz_match,
        'distribution': dict(counter_5),
    }


def format_profile_rtl(user_info, residence_data):
    """تنسيق النتيجة RTL — مطابق لشكل موقع بصير"""
    user = user_info.get('user', {})
    stats = user_info.get('stats', {})
    username = user.get('uniqueId','—')
    nickname = user.get('nickname','—')
    verified = '✅ موثّق' if user.get('verified') else '⚪ غير موثّق'
    private = '🔒 خاص' if user.get('privateAccount') else '🌐 عام'
    signature = (user.get('signature') or '—')[:200]
    followers = stats.get('followerCount',0)
    following = stats.get('followingCount',0)
    likes = stats.get('heartCount',0)
    videos = stats.get('videoCount',0)

    # الإقامة الفعلية
    actual = residence_data.get('actual')
    previous = residence_data.get('previous')
    confidence = residence_data.get('confidence', 0)
    rtype = residence_data.get('type', '—')
    distribution = residence_data.get('distribution', {})

    # المشاهير override
    if username.lower() in CELEBRITIES:
        celeb = CELEBRITIES[username.lower()]
        celeb_country = celeb['country']
        # iso reverse
        celeb_iso = None
        for iso, ctry in REGION_ISO_TO_COUNTRY.items():
            if ctry == celeb_country:
                celeb_iso = iso; break
        if not actual:
            actual = celeb_iso
            confidence = 95
            rtype = 'قاعدة المشاهير'

    if actual:
        country_en = REGION_ISO_TO_COUNTRY.get(actual, actual)
        country_ar = COUNTRY_AR.get(country_en, country_en)
        flag = _iso_to_flag(actual)
        country_display = f"{flag} {country_ar}\n   *EG-Code:* `{actual}` — *EN:* `{country_en}`".replace('EG-Code', 'الرمز')
    else:
        country_display = "🌍 غير محدّد"

    # إقامة سابقة
    prev_html = ''
    if previous and previous != actual:
        prev_en = REGION_ISO_TO_COUNTRY.get(previous, previous)
        prev_ar = COUNTRY_AR.get(prev_en, prev_en)
        prev_flag = _iso_to_flag(previous)
        prev_html = f"\n🕒 *إقامة سابقة:* {prev_flag} {prev_ar} (`{previous}`)"

    # توزيع المناطق
    dist_html = ''
    if distribution and len(distribution) > 1:
        items = []
        total = sum(distribution.values())
        for iso, cnt in sorted(distribution.items(), key=lambda x: -x[1]):
            pct = round(cnt*100/total)
            iso_en = REGION_ISO_TO_COUNTRY.get(iso, iso)
            iso_ar = COUNTRY_AR.get(iso_en, iso_en)
            items.append(f"   • {_iso_to_flag(iso)} {iso_ar}: {cnt} ({pct}%)")
        dist_html = "\n\n🗺️ *توزيع آخر 5 فيديوهات:*\n" + "\n".join(items)

    # ثقة
    if confidence >= 85: conf_emoji = '🟢'
    elif confidence >= 70: conf_emoji = '🟡'
    elif confidence >= 50: conf_emoji = '🟠'
    else: conf_emoji = '⚪'

    return (
        f"📱 *نتيجة البحث — بَصِير TikTok Lookup*\n\n"
        f"👤 *الاسم:* {nickname}\n"
        f"🆔 *المعرّف:* @{username}\n"
        f"{verified}  |  {private}\n\n"
        f"📍 *الإقامة الفعلية:*\n   {country_display}\n"
        f"{conf_emoji} *درجة الثقة:* {confidence}%\n"
        f"🏷️ *النوع:* {rtype}"
        f"{prev_html}"
        f"{dist_html}\n\n"
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
        # موازي: info + posts
        import asyncio
        user_info, posts_data = await asyncio.gather(
            fetch_user_info(username, client),
            fetch_user_posts(username, client),
        )
    if not user_info:
        return f"❌ تعذّر العثور على @{username}\nقد يكون خاصاً أو غير موجود."
    residence_data = detect_actual_residence(
        posts_data.get('regions_seq', []),
        posts_data.get('times_seq', []),
    )
    return format_profile_rtl(user_info, residence_data)
