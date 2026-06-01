# -*- coding: utf-8 -*-
"""
بَصِير v1.3 RTL Fixed Edition
- إصلاح كامل لدعم اللغة العربية (RTL)
- تحسين تباين الألوان (WCAG AAA)
- استبدال st.columns بـ Flexbox مع row-reverse
- بطاقة الحساب احترافية
"""
import streamlit as st
import requests
import re
import json
import time
import logging
from datetime import datetime, timezone
import pandas as pd

# ============= إعدادات السجلات =============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("Baseer")

# ============= إعدادات الصفحة =============
st.set_page_config(
    page_title="بَصِير",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============= CSS احترافي مع دعم RTL كامل =============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Tajawal:wght@400;500;700;800&display=swap');

* {
    font-family: 'Cairo', 'Tajawal', sans-serif !important;
}

/* تطبيق RTL على كامل الواجهة */
.stApp, body, html {
    direction: rtl !important;
    text-align: right !important;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
}

/* إخفاء عناصر Streamlit الافتراضية */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}

/* ===== الشعار والعنوان ===== */
.baseer-hero {
    text-align: center;
    padding: 30px 0 20px 0;
    direction: rtl;
}

.baseer-logo {
    font-size: 180px;
    line-height: 1;
    filter: drop-shadow(0 0 40px rgba(251, 191, 36, 0.6));
    animation: float 3s ease-in-out infinite;
    margin-bottom: 10px;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-15px); }
}

.baseer-name {
    font-size: 90px;
    font-weight: 900;
    background: linear-gradient(135deg, #FCD34D 0%, #F59E0B 50%, #D97706 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 10px 0;
    letter-spacing: 8px;
    text-shadow: 0 0 60px rgba(251, 191, 36, 0.3);
}

/* ===== حقل الإدخال ===== */
.stTextInput > div > div > input {
    direction: rtl !important;
    text-align: right !important;
    background: #1E293B !important;
    color: #F1F5F9 !important;
    border: 2px solid #334155 !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    font-size: 18px !important;
    font-weight: 500 !important;
}

.stTextInput > div > div > input:focus {
    border-color: #F59E0B !important;
    box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.2) !important;
}

.stTextInput > div > div > input::placeholder {
    color: #94A3B8 !important;
    text-align: right !important;
}

/* ===== زر البحث ===== */
.stButton > button {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
    color: #0F172A !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 30px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(251, 191, 36, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(251, 191, 36, 0.5) !important;
}

/* ===== بطاقة الحساب RTL Fixed ===== */
.account-card {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border: 2px solid #F59E0B;
    border-radius: 20px;
    padding: 30px;
    margin: 25px 0;
    direction: rtl;
    text-align: right;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

/* Flexbox للبطاقة - الصورة على اليمين والمعلومات على اليسار في RTL */
.account-flex {
    display: flex;
    flex-direction: row-reverse;
    align-items: center;
    gap: 30px;
    direction: rtl;
}

.account-avatar {
    flex-shrink: 0;
    width: 140px;
    height: 140px;
    border-radius: 50%;
    border: 4px solid #F59E0B;
    box-shadow: 0 0 30px rgba(251, 191, 36, 0.4);
    overflow: hidden;
    background: #0F172A;
}

.account-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.account-info {
    flex: 1;
    text-align: right;
    direction: rtl;
}

.account-name {
    font-size: 32px;
    font-weight: 900;
    color: #FCD34D;
    margin: 0 0 8px 0;
    direction: rtl;
    text-align: right;
}

.account-username {
    font-size: 20px;
    font-weight: 600;
    color: #60A5FA;
    margin: 0 0 15px 0;
    direction: ltr;
    text-align: right;
    display: block;
}

.account-bio {
    font-size: 18px;
    color: #F1F5F9;
    line-height: 1.8;
    margin: 10px 0;
    direction: rtl;
    text-align: right;
    background: rgba(15, 23, 42, 0.5);
    padding: 15px;
    border-radius: 10px;
    border-right: 4px solid #F59E0B;
}

.account-meta {
    font-size: 16px;
    color: #CBD5E1;
    margin-top: 12px;
    direction: rtl;
    text-align: right;
}

.account-meta-item {
    display: inline-block;
    margin-left: 15px;
    padding: 5px 12px;
    background: rgba(245, 158, 11, 0.15);
    border-radius: 8px;
    color: #FCD34D;
    font-weight: 600;
}

/* ===== بطاقة الدولة ===== */
.country-card {
    background: linear-gradient(135deg, #065F46 0%, #047857 100%);
    border: 2px solid #10B981;
    border-radius: 20px;
    padding: 25px;
    margin: 20px 0;
    direction: rtl;
    text-align: center;
    box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
}

.country-flag {
    font-size: 140px;
    line-height: 1;
    margin: 10px 0;
}

.country-name {
    font-size: 36px;
    font-weight: 900;
    color: #F0FDF4;
    margin: 10px 0;
}

.country-confidence {
    font-size: 18px;
    color: #A7F3D0;
    font-weight: 700;
}

/* ===== الإحصائيات ===== */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 15px;
    margin: 20px 0;
    direction: rtl;
}

.stat-box {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border: 1px solid #475569;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    direction: rtl;
}

.stat-value {
    font-size: 28px;
    font-weight: 900;
    color: #FCD34D;
    margin-bottom: 5px;
}

.stat-label {
    font-size: 15px;
    color: #CBD5E1;
    font-weight: 600;
}

/* ===== رسائل التنبيه ===== */
.alert-info {
    background: rgba(59, 130, 246, 0.15);
    border-right: 4px solid #3B82F6;
    padding: 15px 20px;
    border-radius: 10px;
    color: #DBEAFE;
    direction: rtl;
    text-align: right;
    margin: 15px 0;
    font-size: 16px;
}

.alert-warn {
    background: rgba(245, 158, 11, 0.15);
    border-right: 4px solid #F59E0B;
    padding: 15px 20px;
    border-radius: 10px;
    color: #FEF3C7;
    direction: rtl;
    text-align: right;
    margin: 15px 0;
    font-size: 16px;
}

.alert-error {
    background: rgba(239, 68, 68, 0.15);
    border-right: 4px solid #EF4444;
    padding: 15px 20px;
    border-radius: 10px;
    color: #FECACA;
    direction: rtl;
    text-align: right;
    margin: 15px 0;
    font-size: 16px;
}

/* ===== تذييل الصفحة ===== */
.footer {
    text-align: center;
    padding: 30px;
    color: #64748B;
    font-size: 14px;
    margin-top: 50px;
    direction: rtl;
}

/* ===== Responsive للموبايل ===== */
@media (max-width: 768px) {
    .baseer-logo { font-size: 120px; }
    .baseer-name { font-size: 60px; }
    .account-flex { flex-direction: column-reverse; text-align: center; }
    .account-info { text-align: center; }
    .account-name, .account-bio, .account-meta { text-align: center; }
    .country-flag { font-size: 100px; }
    .country-name { font-size: 28px; }
}
</style>
""", unsafe_allow_html=True)

# ============= خريطة الدول ============
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

# ============= أمان: تنظيف اسم المستخدم =============
def sanitize_username(username: str) -> str:
    username = username.strip().lstrip("@").lstrip("https://").replace("tiktok.com/", "").replace("www.", "")
    if not re.match(r"^[a-zA-Z0-9._]{1,24}$", username):
        raise ValueError("❌ اسم مستخدم غير صالح. استخدم حروف وأرقام فقط.")
    return username

# ============= جلب بيانات TikTok =============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_tiktok_profile(username: str) -> dict:
    """جلب بيانات حساب TikTok مع معالجة الأخطاء"""
    import random
    result = {
        "success": False,
        "username": username,
        "nickname": None,
        "bio": None,
        "avatar": None,
        "verified": False,
        "followers": 0,
        "following": 0,
        "likes": 0,
        "videos": 0,
        "language": None,
        "region": None,
        "errors": []
    }
    try:
        url = f"https://www.tiktok.com/@{username}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            result["errors"].append(f"HTTP {resp.status_code}")
            return result

        html = resp.text
        # استخراج JSON
        match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html)
        if match:
            try:
                data = json.loads(match.group(1))
                user_detail = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
                user_info = user_detail.get("userInfo", {})
                user = user_info.get("user", {})
                stats = user_info.get("stats", {}) or user_info.get("statsV2", {})

                result["nickname"] = user.get("nickname")
                result["bio"] = user.get("signature", "")
                result["avatar"] = user.get("avatarLarger") or user.get("avatarMedium") or user.get("avatarThumb")
                result["verified"] = user.get("verified", False)
                result["language"] = user.get("language")
                result["region"] = user.get("region")
                result["followers"] = int(stats.get("followerCount", 0) or 0)
                result["following"] = int(stats.get("followingCount", 0) or 0)
                result["likes"] = int(stats.get("heartCount", 0) or stats.get("heart", 0) or 0)
                result["videos"] = int(stats.get("videoCount", 0) or 0)
                result["success"] = True
            except Exception as e:
                result["errors"].append(f"JSON parse: {str(e)[:50]}")
        else:
            result["errors"].append("لم يتم العثور على بيانات في الصفحة")
    except requests.exceptions.Timeout:
        result["errors"].append("⏱️ انتهت مهلة الاتصال")
    except Exception as e:
        result["errors"].append(f"خطأ: {type(e).__name__}")
        log.error(f"TikTok fetch error: {e}")
    return result

# ============= جلب الدولة من TikMatrix =============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_country_tikmatrix(username: str) -> dict:
    """جلب دولة الحساب من TikMatrix"""
    import random
    result = {"success": False, "country_code": None, "country_name": None, "source": "tikmatrix"}
    try:
        url = f"https://user.tikmatrix.com/?username={username}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            html = resp.text
            # البحث عن الدولة
            patterns = [
                r'Country[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
                r'"country"[:\s]*"([^"]+)"',
                r'<td[^>]*>Country</td>\s*<td[^>]*>([^<]+)',
                r'Region[:\s]*<[^>]+>([^<]+)',
            ]
            for pattern in patterns:
                m = re.search(pattern, html, re.IGNORECASE)
                if m:
                    country_text = m.group(1).strip()
                    result["country_name"] = country_text
                    # تحويل إلى رمز
                    name_to_code = {
                        "saudi arabia": "SA", "united arab emirates": "AE", "egypt": "EG",
                        "kuwait": "KW", "qatar": "QA", "bahrain": "BH", "oman": "OM",
                        "jordan": "JO", "lebanon": "LB", "iraq": "IQ", "morocco": "MA",
                        "algeria": "DZ", "tunisia": "TN", "united states": "US",
                        "united kingdom": "GB", "france": "FR", "germany": "DE",
                        "italy": "IT", "spain": "ES", "turkey": "TR", "japan": "JP",
                        "south korea": "KR", "china": "CN", "afghanistan": "AF",
                    }
                    result["country_code"] = name_to_code.get(country_text.lower(), country_text[:2].upper())
                    result["success"] = True
                    break
    except Exception as e:
        log.warning(f"TikMatrix error: {e}")
    return result

# ============= تنسيق الأرقام =============
def format_number(n):
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)

# ============= التطبيق الرئيسي =============
def main():
    # Hero Section - شعار واسم فقط
    st.markdown("""
    <div class='baseer-hero'>
        <div class='baseer-logo'>🦅</div>
        <div class='baseer-name'>بَصِير</div>
    </div>
    """, unsafe_allow_html=True)

    # حقل الإدخال
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
            # جلب البيانات
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

        # ===== بطاقة الحساب RTL Fixed =====
        avatar_url = profile.get("avatar") or "https://via.placeholder.com/140/F59E0B/0F172A?text=🦅"
        nickname = profile.get("nickname") or username
        bio = profile.get("bio") or "لا يوجد وصف"
        verified_badge = " ✓" if profile.get("verified") else ""

        st.markdown(f"""
        <div class='account-card'>
            <div class='account-flex'>
                <div class='account-avatar'>
                    <img src='{avatar_url}' alt='avatar' onerror="this.src='https://via.placeholder.com/140/F59E0B/0F172A?text=🦅'"/>
                </div>
                <div class='account-info'>
                    <div class='account-name'>{nickname}{verified_badge}</div>
                    <div class='account-username'>@{username}</div>
                    <div class='account-bio'>{bio}</div>
                    <div class='account-meta'>
                        <span class='account-meta-item'>🌐 اللغة: {profile.get('language') or 'غير محدد'}</span>
                        {f"<span class='account-meta-item'>✓ موثّق</span>" if profile.get('verified') else ""}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ===== بطاقة الدولة =====
        country_code = country_data.get("country_code") or profile.get("region")
        if country_code and country_code in COUNTRY_MAP:
            flag, name_ar = COUNTRY_MAP[country_code]
            confidence = 95 if country_data["success"] else 70
            source_text = "TikMatrix (دقة عالية)" if country_data["success"] else "TikTok API"
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

        # ===== الإحصائيات =====
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

        # ===== رابط الملف =====
        st.markdown(f"""
        <div class='alert-info'>
            🔗 <a href='https://www.tiktok.com/@{username}' target='_blank' style='color: #60A5FA; font-weight: 700;'>
                فتح الحساب في TikTok
            </a>
        </div>
        """, unsafe_allow_html=True)

    elif search_btn and not username_input:
        st.markdown("""
        <div class='alert-warn'>
            ⚠️ الرجاء إدخال اسم المستخدم أولاً
        </div>
        """, unsafe_allow_html=True)

    # تذييل الصفحة
    st.markdown("""
    <div class='footer'>
        🦅 بَصِير v1.3 RTL Fixed © 2026
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
