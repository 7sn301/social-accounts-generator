# -*- coding: utf-8 -*-
"""
بَصِير v1.4 - إصلاح BIO + الإحصائيات
==========================================
الإصلاحات الحرجة:
1. ✅ تنظيف HTML من BIO (إزالة <div/>, <br/>, <p/>)
2. ✅ استعادة الإحصائيات الكاملة (متابعون/إعجابات/فيديوهات)
3. ✅ استخراج BIO من مصادر متعددة (signature + bioLink)
4. ✅ معالجة الأخطاء بشكل أفضل
"""
import streamlit as st
import requests
import re
import json
import html as html_lib
import random
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("Baseer")

st.set_page_config(
    page_title="بَصِير",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============= CSS RTL Fixed =============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Tajawal:wght@400;500;700;800&display=swap');

* { font-family: 'Cairo', 'Tajawal', sans-serif !important; }

.stApp, body, html {
    direction: rtl !important;
    text-align: right !important;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
}

#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}

.baseer-hero { text-align: center; padding: 30px 0 20px 0; direction: rtl; }

.baseer-logo {
    font-size: 180px; line-height: 1;
    filter: drop-shadow(0 0 40px rgba(251, 191, 36, 0.6));
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-15px); }
}

.baseer-name {
    font-size: 90px; font-weight: 900;
    background: linear-gradient(135deg, #FCD34D 0%, #F59E0B 50%, #D97706 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 10px 0; letter-spacing: 8px;
    text-shadow: 0 0 60px rgba(251, 191, 36, 0.3);
}

.stTextInput > div > div > input {
    direction: rtl !important; text-align: right !important;
    background: #1E293B !important; color: #F1F5F9 !important;
    border: 2px solid #334155 !important; border-radius: 12px !important;
    padding: 14px 18px !important; font-size: 18px !important;
    font-weight: 500 !important;
}

.stTextInput > div > div > input:focus {
    border-color: #F59E0B !important;
    box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.2) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
    color: #0F172A !important; border: none !important;
    border-radius: 12px !important; padding: 14px 30px !important;
    font-size: 18px !important; font-weight: 700 !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(251, 191, 36, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(251, 191, 36, 0.5) !important;
}

/* بطاقة الحساب */
.account-card {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border: 2px solid #F59E0B; border-radius: 20px;
    padding: 30px; margin: 25px 0; direction: rtl;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.account-flex {
    display: flex; flex-direction: row-reverse;
    align-items: center; gap: 30px; direction: rtl;
}

.account-avatar {
    flex-shrink: 0; width: 140px; height: 140px;
    border-radius: 50%; border: 4px solid #F59E0B;
    box-shadow: 0 0 30px rgba(251, 191, 36, 0.4);
    overflow: hidden; background: #0F172A;
}

.account-avatar img { width: 100%; height: 100%; object-fit: cover; }

.account-info { flex: 1; text-align: right; direction: rtl; }

.account-name {
    font-size: 32px; font-weight: 900;
    color: #FCD34D; margin: 0 0 8px 0;
    direction: rtl; text-align: right;
}

.account-username {
    font-size: 20px; font-weight: 600;
    color: #60A5FA; margin: 0 0 15px 0;
    direction: ltr; text-align: right; display: block;
}

.account-bio {
    font-size: 18px; color: #F1F5F9; line-height: 1.8;
    margin: 10px 0; direction: rtl; text-align: right;
    background: rgba(15, 23, 42, 0.5); padding: 15px;
    border-radius: 10px; border-right: 4px solid #F59E0B;
    white-space: pre-wrap; word-wrap: break-word;
}

.account-meta { font-size: 16px; color: #CBD5E1; margin-top: 12px; direction: rtl; }

.account-meta-item {
    display: inline-block; margin-left: 10px;
    padding: 6px 14px; background: rgba(245, 158, 11, 0.15);
    border-radius: 8px; color: #FCD34D; font-weight: 600;
}

/* بطاقة الدولة */
.country-card {
    background: linear-gradient(135deg, #065F46 0%, #047857 100%);
    border: 2px solid #10B981; border-radius: 20px;
    padding: 25px; margin: 20px 0; direction: rtl;
    text-align: center;
    box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
}

.country-flag { font-size: 140px; line-height: 1; margin: 10px 0; }
.country-name { font-size: 36px; font-weight: 900; color: #F0FDF4; margin: 10px 0; }
.country-confidence { font-size: 18px; color: #A7F3D0; font-weight: 700; }

/* الإحصائيات */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 15px; margin: 25px 0; direction: rtl;
}

.stat-box {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border: 2px solid #475569; border-radius: 15px;
    padding: 25px 15px; text-align: center; direction: rtl;
    transition: all 0.3s ease;
}

.stat-box:hover {
    border-color: #F59E0B;
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(251, 191, 36, 0.2);
}

.stat-value {
    font-size: 32px; font-weight: 900;
    color: #FCD34D; margin-bottom: 8px;
    line-height: 1;
}

.stat-label { font-size: 16px; color: #CBD5E1; font-weight: 600; }

/* تنبيهات */
.alert-info {
    background: rgba(59, 130, 246, 0.15);
    border-right: 4px solid #3B82F6;
    padding: 15px 20px; border-radius: 10px;
    color: #DBEAFE; direction: rtl;
    text-align: right; margin: 15px 0; font-size: 16px;
}

.alert-warn {
    background: rgba(245, 158, 11, 0.15);
    border-right: 4px solid #F59E0B;
    padding: 15px 20px; border-radius: 10px;
    color: #FEF3C7; direction: rtl;
    text-align: right; margin: 15px 0; font-size: 16px;
}

.alert-error {
    background: rgba(239, 68, 68, 0.15);
    border-right: 4px solid #EF4444;
    padding: 15px 20px; border-radius: 10px;
    color: #FECACA; direction: rtl;
    text-align: right; margin: 15px 0; font-size: 16px;
}

.footer { text-align: center; padding: 30px; color: #64748B; font-size: 14px; }

@media (max-width: 768px) {
    .baseer-logo { font-size: 120px; }
    .baseer-name { font-size: 60px; }
    .account-flex { flex-direction: column-reverse; text-align: center; }
    .account-info { text-align: center; }
    .account-name, .account-bio { text-align: center; }
    .country-flag { font-size: 100px; }
}
</style>
""", unsafe_allow_html=True)

# ============= خريطة الدول =============
COUNTRY_MAP = {
    "SA": ("🇸🇦", "المملكة العربية السعودية"),
    "AE": ("🇦🇪", "الإمارات العربية المتحدة"),
    "EG": ("🇪🇬", "جمهورية مصر العربية"),
    "KW": ("🇰🇼", "دولة الكويت"),
    "QA": ("🇶🇦", "دولة قطر"),
    "BH": ("🇧🇭", "مملكة البحرين"),
    "OM": ("🇴🇲", "سلطنة عُمان"),
    "JO": ("🇯🇴", "المملكة الأردنية"),
    "LB": ("🇱🇧", "الجمهورية اللبنانية"),
    "SY": ("🇸🇾", "الجمهورية العربية السورية"),
    "IQ": ("🇮🇶", "جمهورية العراق"),
    "YE": ("🇾🇪", "الجمهورية اليمنية"),
    "PS": ("🇵🇸", "دولة فلسطين"),
    "MA": ("🇲🇦", "المملكة المغربية"),
    "DZ": ("🇩🇿", "الجمهورية الجزائرية"),
    "TN": ("🇹🇳", "الجمهورية التونسية"),
    "LY": ("🇱🇾", "دولة ليبيا"),
    "SD": ("🇸🇩", "جمهورية السودان"),
    "SO": ("🇸🇴", "جمهورية الصومال"),
    "MR": ("🇲🇷", "موريتانيا"),
    "AF": ("🇦🇫", "أفغانستان"),
    "US": ("🇺🇸", "الولايات المتحدة"),
    "GB": ("🇬🇧", "المملكة المتحدة"),
    "FR": ("🇫🇷", "فرنسا"),
    "DE": ("🇩🇪", "ألمانيا"),
    "IT": ("🇮🇹", "إيطاليا"),
    "ES": ("🇪🇸", "إسبانيا"),
    "TR": ("🇹🇷", "تركيا"),
    "RU": ("🇷🇺", "روسيا"),
    "CN": ("🇨🇳", "الصين"),
    "JP": ("🇯🇵", "اليابان"),
    "KR": ("🇰🇷", "كوريا الجنوبية"),
    "IN": ("🇮🇳", "الهند"),
    "PK": ("🇵🇰", "باكستان"),
    "ID": ("🇮🇩", "إندونيسيا"),
    "BR": ("🇧🇷", "البرازيل"),
    "MX": ("🇲🇽", "المكسيك"),
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# ============= 🔧 الإصلاح الحرج: تنظيف BIO من HTML =============
def clean_bio(raw_bio: str) -> str:
    """
    تنظيف BIO من علامات HTML والرموز غير المرغوبة.
    هذا هو الإصلاح الحرج لمشكلة <div/>, <br/>, <p/>
    """
    if not raw_bio:
        return "لا يوجد وصف"
    
    text = str(raw_bio)
    
    # 1. تحويل <br>, <br/>, <br /> إلى أسطر جديدة
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?p\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?div\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # 2. إزالة جميع علامات HTML الأخرى
    text = re.sub(r'<[^>]+>', '', text)
    
    # 3. فك ترميز HTML entities (&amp; → &, &lt; → < ... )
    text = html_lib.unescape(text)
    
    # 4. إزالة الأسطر الفارغة المتكررة
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 5. تنظيف المسافات
    text = text.strip()
    
    # 6. هروب أي < أو > متبقي لمنع XSS في عرض HTML
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    # 7. تحويل \n إلى <br> للعرض في HTML
    text = text.replace('\n', '<br>')
    
    return text if text else "لا يوجد وصف"


def sanitize_username(username: str) -> str:
    username = username.strip().lstrip("@")
    # دعم الروابط الكاملة
    if "tiktok.com/" in username:
        username = username.split("tiktok.com/")[-1].lstrip("@").split("?")[0].split("/")[0]
    if not re.match(r"^[a-zA-Z0-9._]{1,24}$", username):
        raise ValueError("❌ اسم مستخدم غير صالح. استخدم حروف وأرقام فقط.")
    return username


# ============= جلب بيانات TikTok =============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_tiktok_profile(username: str) -> dict:
    """جلب بيانات حساب TikTok مع استخراج كامل للإحصائيات"""
    result = {
        "success": False,
        "username": username,
        "nickname": None,
        "bio_raw": "",
        "bio_clean": "لا يوجد وصف",
        "avatar": None,
        "verified": False,
        "followers": 0,
        "following": 0,
        "likes": 0,
        "videos": 0,
        "friends": 0,
        "language": None,
        "region": None,
        "user_id": None,
        "sec_uid": None,
        "create_time": None,
        "errors": []
    }
    try:
        url = f"https://www.tiktok.com/@{username}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            result["errors"].append(f"HTTP {resp.status_code}")
            return result

        html_content = resp.text
        match = re.search(
            r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
            html_content
        )
        if not match:
            result["errors"].append("لم يتم العثور على بيانات في الصفحة (قد يكون الحساب محذوف أو محمي)")
            return result
        
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            result["errors"].append(f"خطأ في تحليل JSON: {str(e)[:50]}")
            return result
        
        user_detail = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
        user_info = user_detail.get("userInfo", {})
        user = user_info.get("user", {})
        
        # 🔧 استخراج الإحصائيات من مصادر متعددة
        stats = user_info.get("stats", {}) or {}
        stats_v2 = user_info.get("statsV2", {}) or {}
        
        # دمج الإحصائيات (statsV2 له الأولوية)
        followers = int(stats_v2.get("followerCount") or stats.get("followerCount") or 0)
        following = int(stats_v2.get("followingCount") or stats.get("followingCount") or 0)
        likes = int(stats_v2.get("heartCount") or stats.get("heartCount") or stats.get("heart") or 0)
        videos = int(stats_v2.get("videoCount") or stats.get("videoCount") or 0)
        friends = int(stats_v2.get("friendCount") or stats.get("friendCount") or 0)
        
        # 🔧 BIO من مصادر متعددة
        bio_raw = (
            user.get("signature") or 
            user.get("bioLink", {}).get("link") or 
            ""
        )
        
        result.update({
            "success": True,
            "nickname": user.get("nickname") or username,
            "bio_raw": bio_raw,
            "bio_clean": clean_bio(bio_raw),
            "avatar": user.get("avatarLarger") or user.get("avatarMedium") or user.get("avatarThumb"),
            "verified": bool(user.get("verified", False)),
            "followers": followers,
            "following": following,
            "likes": likes,
            "videos": videos,
            "friends": friends,
            "language": user.get("language"),
            "region": user.get("region"),
            "user_id": user.get("id"),
            "sec_uid": user.get("secUid"),
            "create_time": user.get("createTime"),
        })
        
    except requests.exceptions.Timeout:
        result["errors"].append("⏱️ انتهت مهلة الاتصال")
    except Exception as e:
        result["errors"].append(f"خطأ: {type(e).__name__}: {str(e)[:60]}")
        log.error(f"TikTok fetch error: {e}")
    
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_country_tikmatrix(username: str) -> dict:
    """جلب الدولة من TikMatrix"""
    result = {"success": False, "country_code": None, "country_name": None}
    try:
        url = f"https://user.tikmatrix.com/?username={username}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            html_content = resp.text
            patterns = [
                r'Country[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
                r'"country"\s*:\s*"([^"]+)"',
                r'<td[^>]*>\s*Country\s*</td>\s*<td[^>]*>([^<]+)',
            ]
            for pattern in patterns:
                m = re.search(pattern, html_content, re.IGNORECASE)
                if m:
                    country_text = m.group(1).strip()
                    name_to_code = {
                        "saudi arabia": "SA", "united arab emirates": "AE",
                        "egypt": "EG", "kuwait": "KW", "qatar": "QA",
                        "bahrain": "BH", "oman": "OM", "jordan": "JO",
                        "lebanon": "LB", "iraq": "IQ", "morocco": "MA",
                        "algeria": "DZ", "tunisia": "TN", "yemen": "YE",
                        "palestine": "PS", "syria": "SY", "libya": "LY",
                        "sudan": "SD", "united states": "US", "united kingdom": "GB",
                        "france": "FR", "germany": "DE", "italy": "IT",
                        "spain": "ES", "turkey": "TR", "japan": "JP",
                        "south korea": "KR", "china": "CN", "afghanistan": "AF",
                        "india": "IN", "pakistan": "PK", "indonesia": "ID",
                    }
                    result["country_name"] = country_text
                    result["country_code"] = name_to_code.get(country_text.lower())
                    result["success"] = True
                    break
    except Exception as e:
        log.warning(f"TikMatrix error: {e}")
    return result


def format_number(n):
    if not n:
        return "0"
    n = int(n)
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"


# ============= التطبيق الرئيسي =============
def main():
    st.markdown("""
    <div class='baseer-hero'>
        <div class='baseer-logo'>🦅</div>
        <div class='baseer-name'>بَصِير</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        username_input = st.text_input(
            "",
            placeholder="أدخل اسم المستخدم (مثل: aboflah)",
            label_visibility="collapsed",
            key="username_field"
        )
        search_btn = st.button("🔍 ابحث", use_container_width=True)

    if search_btn and username_input:
        try:
            username = sanitize_username(username_input)
        except ValueError as e:
            st.markdown(f"<div class='alert-error'>{e}</div>", unsafe_allow_html=True)
            return

        with st.spinner("🦅 بَصِير يحلّق فوق الحساب..."):
            profile = fetch_tiktok_profile(username)
            country_data = fetch_country_tikmatrix(username)

        if not profile["success"]:
            st.markdown(f"""
            <div class='alert-error'>
                ❌ تعذّر جلب بيانات الحساب @{username}<br>
                <small>الأخطاء: {', '.join(profile['errors'])}</small>
            </div>
            """, unsafe_allow_html=True)
            return

        # ===== بطاقة الحساب =====
        avatar_url = profile.get("avatar") or "https://via.placeholder.com/140/F59E0B/0F172A?text=%F0%9F%A6%85"
        nickname = profile.get("nickname") or username
        # تنظيف nickname من HTML أيضاً
        nickname_clean = re.sub(r'<[^>]+>', '', str(nickname)).replace('<', '&lt;').replace('>', '&gt;')
        bio_clean = profile.get("bio_clean", "لا يوجد وصف")
        verified_badge = " ✓" if profile.get("verified") else ""

        st.markdown(f"""
        <div class='account-card'>
            <div class='account-flex'>
                <div class='account-avatar'>
                    <img src='{avatar_url}' alt='avatar' onerror="this.src='https://via.placeholder.com/140/F59E0B/0F172A?text=Baseer'"/>
                </div>
                <div class='account-info'>
                    <div class='account-name'>{nickname_clean}{verified_badge}</div>
                    <div class='account-username'>@{username}</div>
                    <div class='account-bio'>{bio_clean}</div>
                    <div class='account-meta'>
                        <span class='account-meta-item'>🌐 اللغة: {profile.get('language') or 'غير محدد'}</span>
                        {"<span class='account-meta-item'>✓ موثّق</span>" if profile.get('verified') else ""}
                        {f"<span class='account-meta-item'>🆔 {profile.get('user_id', '')[:10]}...</span>" if profile.get('user_id') else ""}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ===== 🔧 الإحصائيات (مستعادة بالكامل) =====
        st.markdown(f"""
        <div class='stats-grid'>
            <div class='stat-box'>
                <div class='stat-value'>{format_number(profile['followers'])}</div>
                <div class='stat-label'>👥 المتابعون</div>
            </div>
            <div class='stat-box'>
                <div class='stat-value'>{format_number(profile['following'])}</div>
                <div class='stat-label'>➡️ يتابع</div>
            </div>
            <div class='stat-box'>
                <div class='stat-value'>{format_number(profile['likes'])}</div>
                <div class='stat-label'>❤️ الإعجابات</div>
            </div>
            <div class='stat-box'>
                <div class='stat-value'>{format_number(profile['videos'])}</div>
                <div class='stat-label'>🎬 الفيديوهات</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ===== بطاقة الدولة =====
        country_code = country_data.get("country_code") or profile.get("region")
        if country_code and country_code in COUNTRY_MAP:
            flag, name_ar = COUNTRY_MAP[country_code]
            confidence = 95 if country_data["success"] else 70
            source_text = "TikMatrix" if country_data["success"] else "TikTok API"
            st.markdown(f"""
            <div class='country-card'>
                <div class='country-flag'>{flag}</div>
                <div class='country-name'>{name_ar}</div>
                <div class='country-confidence'>🎯 نسبة الثقة: {confidence}% | المصدر: {source_text}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='alert-warn'>
                ⚠️ لم نتمكن من تحديد الدولة بدقة عالية لهذا الحساب.<br>
                <small>السبب: TikTok أزال حقل الدولة لمعظم الحسابات منذ 2024.</small>
            </div>
            """, unsafe_allow_html=True)

        # ===== رابط TikTok + معلومات إضافية =====
        create_date = ""
        if profile.get("create_time"):
            try:
                dt = datetime.fromtimestamp(int(profile["create_time"]), tz=timezone.utc)
                create_date = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        st.markdown(f"""
        <div class='alert-info'>
            🔗 <a href='https://www.tiktok.com/@{username}' target='_blank' style='color: #60A5FA; font-weight: 700; text-decoration: none;'>
                فتح الحساب في TikTok ↗
            </a>
            {f"<br>📅 تاريخ الإنشاء: <b>{create_date}</b>" if create_date else ""}
        </div>
        """, unsafe_allow_html=True)

    elif search_btn and not username_input:
        st.markdown("""
        <div class='alert-warn'>
            ⚠️ الرجاء إدخال اسم المستخدم أولاً
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class='footer'>
        🦅 بَصِير v1.4 - BIO Fix Edition © 2026
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
