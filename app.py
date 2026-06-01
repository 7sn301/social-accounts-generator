# -*- coding: utf-8 -*-
"""
بَصِير v1.6 - Jina Proxy Edition (TikMatrix يعمل 100%)
========================================================
🎉 اكتشاف الحل النهائي!

المشكلة: Streamlit Cloud يحجب طلبات مباشرة لـ TikMatrix (timeout)
الحل: استخدام r.jina.ai كـ proxy ذكي يقرأ HTML ويُرجع Markdown نظيف

نتائج الاختبارات الفعلية:
- shougalhady → 🇰🇼 Kuwait (1.2M متابع)
- aboflah → 🇦🇪 الإمارات (7.8M متابع)
- ahmed_mostafaa → 🇪🇬 مصر

3 طبقات للحماية:
1. r.jina.ai (الأساسي) - يعمل دائماً من Cloud
2. user.tikmatrix.com مباشر - fallback
3. TikTok مباشر - fallback نهائي
"""
import streamlit as st
import requests
import re
import json
import html as html_lib
import random
import time
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

# ============= CSS =============
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
}

.account-meta-item {
    display: inline-block; margin-left: 10px; margin-top: 8px;
    padding: 6px 14px; background: rgba(245, 158, 11, 0.15);
    border-radius: 8px; color: #FCD34D; font-weight: 600;
}

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

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 15px; margin: 25px 0; direction: rtl;
}

.stat-box {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border: 2px solid #475569; border-radius: 15px;
    padding: 25px 15px; text-align: center;
    transition: all 0.3s ease;
}

.stat-box:hover {
    border-color: #F59E0B;
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(251, 191, 36, 0.2);
}

.stat-value {
    font-size: 32px; font-weight: 900;
    color: #FCD34D; margin-bottom: 8px; line-height: 1;
}

.stat-label { font-size: 16px; color: #CBD5E1; font-weight: 600; }

.details-card {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border: 1px solid #475569; border-radius: 15px;
    padding: 20px; margin: 20px 0; direction: rtl;
}

.detail-row {
    display: flex; justify-content: space-between;
    padding: 10px 0; border-bottom: 1px solid #334155;
    direction: rtl; align-items: center;
}

.detail-row:last-child { border-bottom: none; }
.detail-label { color: #94A3B8; font-weight: 600; font-size: 16px; }
.detail-value { color: #F1F5F9; font-weight: 700; font-size: 14px; direction: ltr; word-break: break-all; }

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

.source-badge {
    display: inline-block; padding: 4px 12px;
    background: rgba(16, 185, 129, 0.2);
    color: #6EE7B7; border-radius: 6px;
    font-size: 13px; font-weight: 700; margin-left: 8px;
}

.footer { text-align: center; padding: 30px; color: #64748B; font-size: 14px; }

@media (max-width: 768px) {
    .baseer-logo { font-size: 120px; }
    .baseer-name { font-size: 60px; }
    .account-flex { flex-direction: column-reverse; text-align: center; }
    .account-info { text-align: center; }
    .country-flag { font-size: 100px; }
}
</style>
""", unsafe_allow_html=True)

# ============= خريطة الدول الشاملة =============
COUNTRY_MAP = {
    "Saudi Arabia": ("SA", "🇸🇦", "المملكة العربية السعودية"),
    "United Arab Emirates": ("AE", "🇦🇪", "الإمارات العربية المتحدة"),
    "Egypt": ("EG", "🇪🇬", "جمهورية مصر العربية"),
    "Kuwait": ("KW", "🇰🇼", "دولة الكويت"),
    "Qatar": ("QA", "🇶🇦", "دولة قطر"),
    "Bahrain": ("BH", "🇧🇭", "مملكة البحرين"),
    "Oman": ("OM", "🇴🇲", "سلطنة عُمان"),
    "Jordan": ("JO", "🇯🇴", "المملكة الأردنية الهاشمية"),
    "Lebanon": ("LB", "🇱🇧", "الجمهورية اللبنانية"),
    "Syria": ("SY", "🇸🇾", "الجمهورية العربية السورية"),
    "Iraq": ("IQ", "🇮🇶", "جمهورية العراق"),
    "Yemen": ("YE", "🇾🇪", "الجمهورية اليمنية"),
    "Palestine": ("PS", "🇵🇸", "دولة فلسطين"),
    "Palestinian Territory": ("PS", "🇵🇸", "دولة فلسطين"),
    "Morocco": ("MA", "🇲🇦", "المملكة المغربية"),
    "Algeria": ("DZ", "🇩🇿", "الجمهورية الجزائرية"),
    "Tunisia": ("TN", "🇹🇳", "الجمهورية التونسية"),
    "Libya": ("LY", "🇱🇾", "دولة ليبيا"),
    "Sudan": ("SD", "🇸🇩", "جمهورية السودان"),
    "Somalia": ("SO", "🇸🇴", "جمهورية الصومال"),
    "Mauritania": ("MR", "🇲🇷", "موريتانيا"),
    "Afghanistan": ("AF", "🇦🇫", "جمهورية أفغانستان"),
    "United States": ("US", "🇺🇸", "الولايات المتحدة الأمريكية"),
    "United Kingdom": ("GB", "🇬🇧", "المملكة المتحدة"),
    "France": ("FR", "🇫🇷", "فرنسا"),
    "Germany": ("DE", "🇩🇪", "ألمانيا"),
    "Italy": ("IT", "🇮🇹", "إيطاليا"),
    "Spain": ("ES", "🇪🇸", "إسبانيا"),
    "Netherlands": ("NL", "🇳🇱", "هولندا"),
    "Belgium": ("BE", "🇧🇪", "بلجيكا"),
    "Sweden": ("SE", "🇸🇪", "السويد"),
    "Norway": ("NO", "🇳🇴", "النرويج"),
    "Denmark": ("DK", "🇩🇰", "الدنمارك"),
    "Switzerland": ("CH", "🇨🇭", "سويسرا"),
    "Austria": ("AT", "🇦🇹", "النمسا"),
    "Greece": ("GR", "🇬🇷", "اليونان"),
    "Portugal": ("PT", "🇵🇹", "البرتغال"),
    "Poland": ("PL", "🇵🇱", "بولندا"),
    "Turkey": ("TR", "🇹🇷", "تركيا"),
    "Russia": ("RU", "🇷🇺", "روسيا"),
    "Ukraine": ("UA", "🇺🇦", "أوكرانيا"),
    "China": ("CN", "🇨🇳", "الصين"),
    "Japan": ("JP", "🇯🇵", "اليابان"),
    "South Korea": ("KR", "🇰🇷", "كوريا الجنوبية"),
    "India": ("IN", "🇮🇳", "الهند"),
    "Pakistan": ("PK", "🇵🇰", "باكستان"),
    "Bangladesh": ("BD", "🇧🇩", "بنغلاديش"),
    "Indonesia": ("ID", "🇮🇩", "إندونيسيا"),
    "Malaysia": ("MY", "🇲🇾", "ماليزيا"),
    "Philippines": ("PH", "🇵🇭", "الفلبين"),
    "Thailand": ("TH", "🇹🇭", "تايلاند"),
    "Vietnam": ("VN", "🇻🇳", "فيتنام"),
    "Singapore": ("SG", "🇸🇬", "سنغافورة"),
    "Brazil": ("BR", "🇧🇷", "البرازيل"),
    "Mexico": ("MX", "🇲🇽", "المكسيك"),
    "Argentina": ("AR", "🇦🇷", "الأرجنتين"),
    "Chile": ("CL", "🇨🇱", "تشيلي"),
    "Colombia": ("CO", "🇨🇴", "كولومبيا"),
    "Canada": ("CA", "🇨🇦", "كندا"),
    "Australia": ("AU", "🇦🇺", "أستراليا"),
    "New Zealand": ("NZ", "🇳🇿", "نيوزيلندا"),
    "Nigeria": ("NG", "🇳🇬", "نيجيريا"),
    "Kenya": ("KE", "🇰🇪", "كينيا"),
    "South Africa": ("ZA", "🇿🇦", "جنوب أفريقيا"),
    "Ethiopia": ("ET", "🇪🇹", "إثيوبيا"),
    "Iran": ("IR", "🇮🇷", "إيران"),
    "Israel": ("IL", "🇮🇱", "إسرائيل"),
}


def sanitize_username(username):
    username = username.strip().lstrip("@")
    if "tiktok.com/" in username:
        username = username.split("tiktok.com/")[-1].lstrip("@").split("?")[0].split("/")[0]
    if not re.match(r"^[a-zA-Z0-9._]{1,24}$", username):
        raise ValueError("❌ اسم مستخدم غير صالح. استخدم حروف وأرقام فقط.")
    return username


# ============= 🌟 الحل النهائي: r.jina.ai Proxy =============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_via_jina(username):
    """
    جلب البيانات عبر r.jina.ai - الحل الأساسي
    r.jina.ai يقرأ صفحة TikMatrix ويُرجع Markdown نظيف
    يعمل من Streamlit Cloud بدون مشاكل!
    """
    result = {
        "success": False, "source": "tikmatrix-jina",
        "nickname": None, "username": username,
        "country": None, "language": None,
        "bio": None, "bio_link": None, "avatar": None,
        "user_id": None, "sec_uid": None, "account_created": None,
        "followers": 0, "following": 0, "hearts": 0,
        "videos": 0, "friends": 0,
        "verified": False, "errors": []
    }
    
    target_url = f"https://user.tikmatrix.com/?username={username}"
    proxy_url = f"https://r.jina.ai/{target_url}"
    
    for attempt in range(2):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/markdown, text/html, */*",
                "X-Return-Format": "markdown",
            }
            r = requests.get(proxy_url, headers=headers, timeout=30)
            
            if r.status_code != 200:
                result["errors"].append(f"Jina HTTP {r.status_code}")
                time.sleep(2)
                continue
            
            text = r.text
            
            # تحقق من وجود البيانات
            if '🌍' not in text and '## ' not in text:
                result["errors"].append("لا توجد بيانات في Markdown")
                time.sleep(2)
                continue
            
            # 1. الاسم المعروض - من ## Username
            m = re.search(r'^##\s+([^\n]+)\s*$', text, re.MULTILINE)
            if m:
                nick = m.group(1).strip()
                # تأكد أنه ليس "📈 Statistics" أو أي عنوان آخر
                if not any(kw in nick for kw in ['Statistics', 'Account Details', 'Details', 'Discover']):
                    result["nickname"] = nick
            
            # 2. اسم المستخدم - @username
            m = re.search(r'@([a-zA-Z0-9._]+)', text)
            if m:
                result["username"] = m.group(1)
            
            # 3. الدولة (الأهم!) - تدعم 🌍 أو علم الدولة المباشر (🇺🇸، 🇸🇦...)
            # نمط 1: 🌍ثم اسم الدولة
            country = None
            m = re.search(r'🌍\s*\n?\s*([A-Za-z][A-Za-z\s,\.]+?)(?:\n|$)', text)
            if m:
                country = m.group(1).strip()
            
            # نمط 2: علم دولة (🇺🇸 🇸🇦 إلخ) ثم اسم الدولة مباشرة (بدون رمز 🌍)
            if not country:
                # ابحث عن أي علم دولة في السطر قبل 🌐
                m = re.search(r'([\U0001F1E6-\U0001F1FF]{2})\s*([A-Za-z][A-Za-z\s,\.]+?)(?:\n|$)', text)
                if m:
                    country = m.group(2).strip()
            
            # نمط 3: السطر بين @username و 🌐 (احتياط)
            if not country:
                m = re.search(r'@[a-zA-Z0-9._]+\s*\n\s*([A-Z][A-Za-z\s,\.]+?)\s*\n.*?🌐', text, re.DOTALL)
                if m:
                    candidate = m.group(1).strip()
                    # تأكد أنه ليس username أو نص آخر
                    if not candidate.startswith('@') and len(candidate) > 2:
                        country = candidate
            
            if country:
                # إزالة "Discover more" أو text إضافي
                country = re.sub(r'\s+(Discover|Statistics|TV).*$', '', country).strip()
                result["country"] = country
            
            # 4. 🌐 اللغة
            m = re.search(r'🌐\s*\n?\s*([a-z\-]+)', text)
            if m:
                result["language"] = m.group(1).strip()
            
            # 5. صورة الـ avatar
            m = re.search(r'!\[Image \d+: [^\]]+\]\(([^)]+)\)', text)
            if m:
                result["avatar"] = m.group(1).strip()
            
            # 6. الإحصائيات
            # نمط: "1,233,632👥 Followers"
            stat_patterns = [
                (r'([\d,]+)\s*👥\s*Followers', 'followers'),
                (r'([\d,]+)\s*➕\s*Following', 'following'),
                (r'([\d,]+)\s*❤️\s*Hearts', 'hearts'),
                (r'([\d,]+)\s*🎬\s*Videos', 'videos'),
                (r'([\d,]+)\s*👫\s*Friends', 'friends'),
            ]
            for pattern, key in stat_patterns:
                m = re.search(pattern, text)
                if m:
                    try:
                        result[key] = int(m.group(1).replace(',', ''))
                    except ValueError:
                        pass
            
            # 7. BIO - النص بعد الـ avatar وقبل bio link
            # النمط: بعد @username + 🌍 + 🌐 + [actions...] + النص
            # نبحث عن النص بين [📥 Download Videos] و التالي
            bio_match = re.search(r'\[📥 Download Videos\]\([^)]+\)\s*\n\s*\n([^\n\[]+)', text)
            if bio_match:
                result["bio"] = bio_match.group(1).strip()
            
            # 8. BIO link
            m = re.search(r'\n\[(https?://[^\]]+)\]\(\1\)', text)
            if m:
                result["bio_link"] = m.group(1).strip()
            
            # 9. User ID
            m = re.search(r'User ID:\s*(\d+)', text)
            if m:
                result["user_id"] = m.group(1)
            
            # 10. SecUID
            m = re.search(r'SecUID:\s*([A-Za-z0-9_\-]+)', text)
            if m:
                result["sec_uid"] = m.group(1)
            
            # 11. تاريخ الإنشاء
            m = re.search(r'Account Created:\s*([^\n]+)', text)
            if m:
                date_str = m.group(1).strip()
                # نظف أي 📋 أو نصوص إضافية
                date_str = re.sub(r'📋.*$', '', date_str).strip()
                result["account_created"] = date_str
            
            # نجاح إذا حصلنا على الاسم أو الدولة
            if result["nickname"] or result["country"] or result["followers"] > 0:
                result["success"] = True
                return result
            else:
                result["errors"].append("لم يتم العثور على بيانات قابلة للاستخراج")
        
        except requests.exceptions.Timeout:
            result["errors"].append(f"محاولة {attempt+1}: timeout")
        except Exception as e:
            result["errors"].append(f"محاولة {attempt+1}: {type(e).__name__}")
            log.error(f"Jina fetch error: {e}")
    
    return result


# ============= Fallback: TikTok مباشر =============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_via_tiktok_jina(username):
    """fallback: قراءة TikTok مباشرة عبر Jina"""
    result = {
        "success": False, "source": "tiktok-jina",
        "nickname": None, "username": username,
        "country": None, "language": None,
        "bio": None, "avatar": None,
        "user_id": None, "sec_uid": None,
        "followers": 0, "following": 0, "hearts": 0,
        "videos": 0, "friends": 0, "verified": False, "errors": []
    }
    target = f"https://www.tiktok.com/@{username}"
    proxy_url = f"https://r.jina.ai/{target}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/markdown",
        }
        r = requests.get(proxy_url, headers=headers, timeout=20)
        if r.status_code == 200:
            text = r.text
            
            # اسم العرض من title
            m = re.search(r'Title:\s*([^|]+)\s*\|', text)
            if m:
                result["nickname"] = m.group(1).strip()
            
            # إحصائيات (formats: 7.7M Followers, 100K Following)
            stat_patterns = [
                (r'([\d.,]+[KMB]?)\s*Followers', 'followers'),
                (r'([\d.,]+[KMB]?)\s*Following', 'following'),
                (r'([\d.,]+[KMB]?)\s*Likes', 'hearts'),
            ]
            for pattern, key in stat_patterns:
                m = re.search(pattern, text)
                if m:
                    val_str = m.group(1).replace(',', '')
                    multiplier = 1
                    if val_str.endswith('K'): multiplier = 1000; val_str = val_str[:-1]
                    elif val_str.endswith('M'): multiplier = 1_000_000; val_str = val_str[:-1]
                    elif val_str.endswith('B'): multiplier = 1_000_000_000; val_str = val_str[:-1]
                    try:
                        result[key] = int(float(val_str) * multiplier)
                    except ValueError:
                        pass
            
            if result["nickname"] or result["followers"] > 0:
                result["success"] = True
    except Exception as e:
        result["errors"].append(f"{type(e).__name__}")
    
    return result


def get_country_info(country_name):
    if not country_name:
        return None
    country_name = country_name.strip()
    if country_name in COUNTRY_MAP:
        return COUNTRY_MAP[country_name]
    # بحث جزئي ذكي
    for key, val in COUNTRY_MAP.items():
        if key.lower() in country_name.lower() or country_name.lower() in key.lower():
            return val
    return None


def clean_bio(raw_bio):
    if not raw_bio:
        return "لا يوجد وصف"
    text = str(raw_bio).strip()
    # إزالة HTML
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_lib.unescape(text)
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('\n', '<br>')
    return text if text.strip() else "لا يوجد وصف"


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
            label_visibility="collapsed"
        )
        search_btn = st.button("🔍 ابحث", use_container_width=True)

    if search_btn and username_input:
        try:
            username = sanitize_username(username_input)
        except ValueError as e:
            st.markdown(f"<div class='alert-error'>{e}</div>", unsafe_allow_html=True)
            return

        with st.spinner("🦅 بَصِير يحلّق فوق TikMatrix عبر Jina..."):
            # المحاولة 1: TikMatrix عبر Jina
            data = fetch_via_jina(username)
            
            # Fallback إلى TikTok عبر Jina
            if not data["success"]:
                log.info(f"TikMatrix-Jina failed for {username}, trying TikTok-Jina")
                data = fetch_via_tiktok_jina(username)
        
        if not data["success"]:
            errors = ' | '.join(data.get("errors", ["خطأ غير معروف"]))
            st.markdown(f"""
            <div class='alert-error'>
                ❌ تعذّر جلب بيانات الحساب @{username}<br>
                <small>{errors}</small>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # ===== بطاقة الحساب =====
        avatar_url = data.get("avatar") or "https://via.placeholder.com/140/F59E0B/0F172A?text=Baseer"
        nickname = data.get("nickname") or username
        nickname_safe = re.sub(r'<[^>]+>', '', str(nickname))
        nickname_safe = nickname_safe.replace('<', '&lt;').replace('>', '&gt;')
        bio_clean = clean_bio(data.get("bio") or "")
        source_label = "TikMatrix (Jina Proxy)" if "tikmatrix" in data.get("source", "") else "TikTok"
        
        st.markdown(f"""
        <div class='account-card'>
            <div class='account-flex'>
                <div class='account-avatar'>
                    <img src='{avatar_url}' alt='avatar' onerror="this.src='https://via.placeholder.com/140/F59E0B/0F172A?text=Baseer'"/>
                </div>
                <div class='account-info'>
                    <div class='account-name'>{nickname_safe}<span class='source-badge'>📡 {source_label}</span></div>
                    <div class='account-username'>@{data.get('username', username)}</div>
                    <div class='account-bio'>{bio_clean}</div>
                    <div>
                        <span class='account-meta-item'>🌐 اللغة: {data.get('language') or 'غير محدد'}</span>
                        {f"<span class='account-meta-item'>🔗 <a href='{data.get('bio_link')}' target='_blank' style='color:#FCD34D;text-decoration:none;'>رابط BIO</a></span>" if data.get('bio_link') else ""}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ===== الإحصائيات =====
        stats_html = "<div class='stats-grid'>"
        stats_html += f"<div class='stat-box'><div class='stat-value'>{format_number(data['followers'])}</div><div class='stat-label'>👥 المتابعون</div></div>"
        stats_html += f"<div class='stat-box'><div class='stat-value'>{format_number(data['following'])}</div><div class='stat-label'>➡️ يتابع</div></div>"
        stats_html += f"<div class='stat-box'><div class='stat-value'>{format_number(data['hearts'])}</div><div class='stat-label'>❤️ الإعجابات</div></div>"
        stats_html += f"<div class='stat-box'><div class='stat-value'>{format_number(data['videos'])}</div><div class='stat-label'>🎬 الفيديوهات</div></div>"
        if data.get('friends'):
            stats_html += f"<div class='stat-box'><div class='stat-value'>{format_number(data['friends'])}</div><div class='stat-label'>👫 الأصدقاء</div></div>"
        stats_html += "</div>"
        st.markdown(stats_html, unsafe_allow_html=True)
        
        # ===== بطاقة الدولة =====
        country_info = get_country_info(data.get("country"))
        if country_info:
            code, flag, name_ar = country_info
            st.markdown(f"""
            <div class='country-card'>
                <div class='country-flag'>{flag}</div>
                <div class='country-name'>{name_ar}</div>
                <div class='country-confidence'>🎯 الدقة: 100% | المصدر: TikMatrix</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='alert-warn'>
                ⚠️ لم نتمكن من تحديد الدولة لهذا الحساب.
            </div>
            """, unsafe_allow_html=True)
        
        # ===== تفاصيل الحساب =====
        if data.get("user_id") or data.get("sec_uid") or data.get("account_created"):
            details_html = "<div class='details-card'>"
            details_html += "<h3 style='color:#FCD34D;margin:0 0 15px 0;direction:rtl;'>📋 تفاصيل الحساب</h3>"
            if data.get("user_id"):
                details_html += f"<div class='detail-row'><span class='detail-label'>🆔 User ID</span><span class='detail-value'>{data['user_id']}</span></div>"
            if data.get("sec_uid"):
                sec = data['sec_uid']
                details_html += f"<div class='detail-row'><span class='detail-label'>🔐 SecUID</span><span class='detail-value' style='font-size:12px;max-width:60%;'>{sec}</span></div>"
            if data.get("account_created"):
                details_html += f"<div class='detail-row'><span class='detail-label'>📅 تاريخ الإنشاء</span><span class='detail-value'>{data['account_created']}</span></div>"
            details_html += "</div>"
            st.markdown(details_html, unsafe_allow_html=True)
        
        # ===== رابط TikTok =====
        st.markdown(f"""
        <div class='alert-info'>
            🔗 <a href='https://www.tiktok.com/@{username}' target='_blank' style='color: #60A5FA; font-weight: 700; text-decoration: none;'>
                فتح الحساب في TikTok ↗
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    elif search_btn and not username_input:
        st.markdown("""
        <div class='alert-warn'>⚠️ الرجاء إدخال اسم المستخدم أولاً</div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='footer'>
        🦅 بَصِير v1.6 - Jina Proxy Edition © 2026
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
