# -*- coding: utf-8 -*-
"""
بَصِير v1.8 - Global Coverage Edition Edition
============================================
🎯 يدمج 3 مصادر بنظام ذكي:

1. TikTok مباشر (عبر Jina Proxy)
   - يعمل لكل الحسابات
   - يجلب: nickname, bio, followers, hearts, videos, avatar
   - لا يجلب: country بشكل مباشر

2. TikMatrix (عبر Jina Proxy)
   - أفضل مصدر للدولة
   - قاعدة بيانات محدودة

3. تحليل اللغة + Bio + Hashtags (Fallback)
   - يستخدم عند فشل المصدرين الأولين

نظام Confidence Score:
- 🟢 95-100%: TikMatrix + TikTok يتفقان
- 🟡 70-94%: TikMatrix فقط أو TikTok + تحليل قوي
- 🟠 50-69%: مصدر واحد ضعيف
- 🔴 < 50%: تخمين فقط
"""
import streamlit as st
import requests
import re
import json
import html as html_lib
import random
import time
import logging
from datetime import datetime

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

.country-card-high {
    background: linear-gradient(135deg, #065F46 0%, #047857 100%);
    border: 2px solid #10B981;
    box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
}
.country-card-medium {
    background: linear-gradient(135deg, #92400E 0%, #B45309 100%);
    border: 2px solid #F59E0B;
    box-shadow: 0 10px 40px rgba(245, 158, 11, 0.3);
}
.country-card-low {
    background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 100%);
    border: 2px solid #EF4444;
    box-shadow: 0 10px 40px rgba(239, 68, 68, 0.3);
}

.country-card {
    border-radius: 20px;
    padding: 25px; margin: 20px 0; direction: rtl;
    text-align: center;
}

.country-flag { font-size: 140px; line-height: 1; margin: 10px 0; }
.country-name { font-size: 36px; font-weight: 900; color: #F0FDF4; margin: 10px 0; }
.country-confidence { font-size: 18px; color: #FFFFFF; font-weight: 700; opacity: 0.95; }

.sources-bar {
    display: flex; gap: 8px; justify-content: center;
    margin-top: 15px; flex-wrap: wrap;
}

.source-tag {
    padding: 6px 14px; border-radius: 8px;
    font-size: 13px; font-weight: 700;
    background: rgba(255, 255, 255, 0.15); color: #FFFFFF;
}

.source-tag.success { background: rgba(16, 185, 129, 0.3); }
.source-tag.fail { background: rgba(239, 68, 68, 0.3); opacity: 0.6; }

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

.rate-limit-notice {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid #3B82F6;
    padding: 10px 15px; border-radius: 8px;
    color: #93C5FD; direction: rtl;
    text-align: center; margin: 10px 0; font-size: 14px;
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
    # ============ 🌍 الدول العربية (22) ============
    "Saudi Arabia": ("SA", "🇸🇦", "المملكة العربية السعودية"),
    "United Arab Emirates": ("AE", "🇦🇪", "الإمارات العربية المتحدة"),
    "UAE": ("AE", "🇦🇪", "الإمارات العربية المتحدة"),
    "Egypt": ("EG", "🇪🇬", "جمهورية مصر العربية"),
    "Kuwait": ("KW", "🇰🇼", "دولة الكويت"),
    "Qatar": ("QA", "🇶🇦", "دولة قطر"),
    "Bahrain": ("BH", "🇧🇭", "مملكة البحرين"),
    "Oman": ("OM", "🇴🇲", "سلطنة عُمان"),
    "Jordan": ("JO", "🇯🇴", "المملكة الأردنية"),
    "Lebanon": ("LB", "🇱🇧", "الجمهورية اللبنانية"),
    "Syria": ("SY", "🇸🇾", "سوريا"),
    "Iraq": ("IQ", "🇮🇶", "العراق"),
    "Yemen": ("YE", "🇾🇪", "اليمن"),
    "Palestine": ("PS", "🇵🇸", "فلسطين"),
    "Palestinian Territory": ("PS", "🇵🇸", "فلسطين"),
    "Morocco": ("MA", "🇲🇦", "المغرب"),
    "Algeria": ("DZ", "🇩🇿", "الجزائر"),
    "Tunisia": ("TN", "🇹🇳", "تونس"),
    "Libya": ("LY", "🇱🇾", "ليبيا"),
    "Sudan": ("SD", "🇸🇩", "السودان"),
    "Somalia": ("SO", "🇸🇴", "الصومال"),
    "Mauritania": ("MR", "🇲🇷", "موريتانيا"),
    "Djibouti": ("DJ", "🇩🇯", "جيبوتي"),
    "Comoros": ("KM", "🇰🇲", "جزر القمر"),

    # ============ 🌏 شرق آسيا (10) ============
    "China": ("CN", "🇨🇳", "الصين"),
    "Japan": ("JP", "🇯🇵", "اليابان"),
    "South Korea": ("KR", "🇰🇷", "كوريا الجنوبية"),
    "Korea": ("KR", "🇰🇷", "كوريا الجنوبية"),
    "North Korea": ("KP", "🇰🇵", "كوريا الشمالية"),
    "Taiwan": ("TW", "🇹🇼", "تايوان"),
    "Hong Kong": ("HK", "🇭🇰", "هونغ كونغ"),
    "Macau": ("MO", "🇲🇴", "ماكاو"),
    "Macao": ("MO", "🇲🇴", "ماكاو"),
    "Mongolia": ("MN", "🇲🇳", "منغوليا"),

    # ============ 🌏 جنوب شرق آسيا (11) ============
    "Indonesia": ("ID", "🇮🇩", "إندونيسيا"),
    "Malaysia": ("MY", "🇲🇾", "ماليزيا"),
    "Singapore": ("SG", "🇸🇬", "سنغافورة"),
    "Thailand": ("TH", "🇹🇭", "تايلاند"),
    "Vietnam": ("VN", "🇻🇳", "فيتنام"),
    "Viet Nam": ("VN", "🇻🇳", "فيتنام"),
    "Philippines": ("PH", "🇵🇭", "الفلبين"),
    "Cambodia": ("KH", "🇰🇭", "كمبوديا"),
    "Laos": ("LA", "🇱🇦", "لاوس"),
    "Myanmar": ("MM", "🇲🇲", "ميانمار"),
    "Burma": ("MM", "🇲🇲", "ميانمار"),
    "Brunei": ("BN", "🇧🇳", "بروناي"),
    "Timor-Leste": ("TL", "🇹🇱", "تيمور الشرقية"),
    "East Timor": ("TL", "🇹🇱", "تيمور الشرقية"),

    # ============ 🌏 جنوب آسيا (8) ============
    "India": ("IN", "🇮🇳", "الهند"),
    "Pakistan": ("PK", "🇵🇰", "باكستان"),
    "Bangladesh": ("BD", "🇧🇩", "بنغلاديش"),
    "Sri Lanka": ("LK", "🇱🇰", "سريلانكا"),
    "Nepal": ("NP", "🇳🇵", "نيبال"),
    "Bhutan": ("BT", "🇧🇹", "بوتان"),
    "Maldives": ("MV", "🇲🇻", "المالديف"),
    "Afghanistan": ("AF", "🇦🇫", "أفغانستان"),

    # ============ 🌏 وسط آسيا (5) ============
    "Kazakhstan": ("KZ", "🇰🇿", "كازاخستان"),
    "Uzbekistan": ("UZ", "🇺🇿", "أوزبكستان"),
    "Kyrgyzstan": ("KG", "🇰🇬", "قيرغيزستان"),
    "Tajikistan": ("TJ", "🇹🇯", "طاجيكستان"),
    "Turkmenistan": ("TM", "🇹🇲", "تركمانستان"),

    # ============ 🌏 غرب آسيا / القوقاز (6) ============
    "Turkey": ("TR", "🇹🇷", "تركيا"),
    "Iran": ("IR", "🇮🇷", "إيران"),
    "Israel": ("IL", "🇮🇱", "إسرائيل"),
    "Armenia": ("AM", "🇦🇲", "أرمينيا"),
    "Azerbaijan": ("AZ", "🇦🇿", "أذربيجان"),
    "Georgia": ("GE", "🇬🇪", "جورجيا"),

    # ============ 🇺🇸 أمريكا الشمالية (3) ============
    "United States": ("US", "🇺🇸", "الولايات المتحدة"),
    "USA": ("US", "🇺🇸", "الولايات المتحدة"),
    "Canada": ("CA", "🇨🇦", "كندا"),
    "Mexico": ("MX", "🇲🇽", "المكسيك"),

    # ============ 🇧🇷 أمريكا اللاتينية (15) ============
    "Brazil": ("BR", "🇧🇷", "البرازيل"),
    "Argentina": ("AR", "🇦🇷", "الأرجنتين"),
    "Chile": ("CL", "🇨🇱", "تشيلي"),
    "Colombia": ("CO", "🇨🇴", "كولومبيا"),
    "Peru": ("PE", "🇵🇪", "بيرو"),
    "Venezuela": ("VE", "🇻🇪", "فنزويلا"),
    "Ecuador": ("EC", "🇪🇨", "الإكوادور"),
    "Bolivia": ("BO", "🇧🇴", "بوليفيا"),
    "Paraguay": ("PY", "🇵🇾", "باراغواي"),
    "Uruguay": ("UY", "🇺🇾", "أوروغواي"),
    "Cuba": ("CU", "🇨🇺", "كوبا"),
    "Dominican Republic": ("DO", "🇩🇴", "جمهورية الدومينيكان"),
    "Puerto Rico": ("PR", "🇵🇷", "بورتوريكو"),
    "Guatemala": ("GT", "🇬🇹", "غواتيمالا"),
    "Honduras": ("HN", "🇭🇳", "هندوراس"),

    # ============ 🇪🇺 أوروبا (25) ============
    "United Kingdom": ("GB", "🇬🇧", "المملكة المتحدة"),
    "France": ("FR", "🇫🇷", "فرنسا"),
    "Germany": ("DE", "🇩🇪", "ألمانيا"),
    "Italy": ("IT", "🇮🇹", "إيطاليا"),
    "Spain": ("ES", "🇪🇸", "إسبانيا"),
    "Portugal": ("PT", "🇵🇹", "البرتغال"),
    "Netherlands": ("NL", "🇳🇱", "هولندا"),
    "Belgium": ("BE", "🇧🇪", "بلجيكا"),
    "Sweden": ("SE", "🇸🇪", "السويد"),
    "Norway": ("NO", "🇳🇴", "النرويج"),
    "Denmark": ("DK", "🇩🇰", "الدنمارك"),
    "Finland": ("FI", "🇫🇮", "فنلندا"),
    "Iceland": ("IS", "🇮🇸", "أيسلندا"),
    "Ireland": ("IE", "🇮🇪", "أيرلندا"),
    "Switzerland": ("CH", "🇨🇭", "سويسرا"),
    "Austria": ("AT", "🇦🇹", "النمسا"),
    "Greece": ("GR", "🇬🇷", "اليونان"),
    "Poland": ("PL", "🇵🇱", "بولندا"),
    "Czech Republic": ("CZ", "🇨🇿", "التشيك"),
    "Czechia": ("CZ", "🇨🇿", "التشيك"),
    "Hungary": ("HU", "🇭🇺", "المجر"),
    "Romania": ("RO", "🇷🇴", "رومانيا"),
    "Bulgaria": ("BG", "🇧🇬", "بلغاريا"),
    "Russia": ("RU", "🇷🇺", "روسيا"),
    "Ukraine": ("UA", "🇺🇦", "أوكرانيا"),
    "Croatia": ("HR", "🇭🇷", "كرواتيا"),
    "Serbia": ("RS", "🇷🇸", "صربيا"),

    # ============ 🌍 أفريقيا (15) ============
    "Nigeria": ("NG", "🇳🇬", "نيجيريا"),
    "South Africa": ("ZA", "🇿🇦", "جنوب أفريقيا"),
    "Kenya": ("KE", "🇰🇪", "كينيا"),
    "Ethiopia": ("ET", "🇪🇹", "إثيوبيا"),
    "Ghana": ("GH", "🇬🇭", "غانا"),
    "Tanzania": ("TZ", "🇹🇿", "تنزانيا"),
    "Uganda": ("UG", "🇺🇬", "أوغندا"),
    "Senegal": ("SN", "🇸🇳", "السنغال"),
    "Ivory Coast": ("CI", "🇨🇮", "ساحل العاج"),
    "Côte d'Ivoire": ("CI", "🇨🇮", "ساحل العاج"),
    "Cameroon": ("CM", "🇨🇲", "الكاميرون"),
    "Madagascar": ("MG", "🇲🇬", "مدغشقر"),
    "Zimbabwe": ("ZW", "🇿🇼", "زيمبابوي"),
    "Angola": ("AO", "🇦🇴", "أنغولا"),
    "Mozambique": ("MZ", "🇲🇿", "موزمبيق"),

    # ============ 🇦🇺 أوقيانوسيا (3) ============
    "Australia": ("AU", "🇦🇺", "أستراليا"),
    "New Zealand": ("NZ", "🇳🇿", "نيوزيلندا"),
    "Fiji": ("FJ", "🇫🇯", "فيجي"),
}

# ============= ربط اللغة بالدول المحتملة =============
LANGUAGE_TO_COUNTRY = {
    # 🌍 العربية
    "ar": ["Saudi Arabia", "Egypt", "United Arab Emirates", "Morocco", "Kuwait"],
    
    # 🌏 شرق آسيا
    "zh": ["China", "Taiwan", "Hong Kong", "Singapore"],
    "zh-cn": ["China"],
    "zh-tw": ["Taiwan"],
    "zh-hk": ["Hong Kong"],
    "ja": ["Japan"],
    "ko": ["South Korea"],
    "mn": ["Mongolia"],
    
    # 🌏 جنوب شرق آسيا
    "id": ["Indonesia"],
    "ms": ["Malaysia"],
    "th": ["Thailand"],
    "vi": ["Vietnam"],
    "tl": ["Philippines"],
    "fil": ["Philippines"],
    "km": ["Cambodia"],
    "lo": ["Laos"],
    "my": ["Myanmar"],
    
    # 🌏 جنوب آسيا
    "hi": ["India"],
    "bn": ["Bangladesh", "India"],
    "ur": ["Pakistan", "India"],
    "ta": ["India", "Sri Lanka"],
    "te": ["India"],
    "mr": ["India"],
    "gu": ["India"],
    "pa": ["India", "Pakistan"],
    "ne": ["Nepal"],
    "si": ["Sri Lanka"],
    "dv": ["Maldives"],
    
    # 🌏 وسط/غرب آسيا
    "kk": ["Kazakhstan"],
    "uz": ["Uzbekistan"],
    "ky": ["Kyrgyzstan"],
    "tg": ["Tajikistan"],
    "tk": ["Turkmenistan"],
    "tr": ["Turkey"],
    "fa": ["Iran", "Afghanistan"],
    "ps": ["Afghanistan", "Pakistan"],
    "he": ["Israel"],
    "iw": ["Israel"],
    "hy": ["Armenia"],
    "az": ["Azerbaijan"],
    "ka": ["Georgia"],
    
    # 🌍 أوروبا
    "en": ["United States", "United Kingdom"],
    "en-us": ["United States"],
    "en-gb": ["United Kingdom"],
    "fr": ["France"],
    "de": ["Germany"],
    "es": ["Spain", "Mexico", "Argentina"],
    "it": ["Italy"],
    "pt": ["Brazil", "Portugal"],
    "pt-br": ["Brazil"],
    "pt-pt": ["Portugal"],
    "nl": ["Netherlands"],
    "sv": ["Sweden"],
    "no": ["Norway"],
    "da": ["Denmark"],
    "fi": ["Finland"],
    "pl": ["Poland"],
    "cs": ["Czech Republic"],
    "hu": ["Hungary"],
    "ro": ["Romania"],
    "bg": ["Bulgaria"],
    "el": ["Greece"],
    "ru": ["Russia"],
    "uk": ["Ukraine"],
    "hr": ["Croatia"],
    "sr": ["Serbia"],
    
    # 🌍 أفريقيا
    "sw": ["Kenya", "Tanzania"],
    "am": ["Ethiopia"],
    "ha": ["Nigeria"],
    "yo": ["Nigeria"],
    "ig": ["Nigeria"],
    "zu": ["South Africa"],
}

# ============= كلمات جغرافية في BIO =============
GEO_KEYWORDS = {
    # 🌍 الدول العربية
    "Saudi Arabia": ["السعودية", "السعوديه", "saudi", "ksa", "riyadh", "الرياض", "جدة", "مكة", "المدينة", "الدمام"],
    "United Arab Emirates": ["الإمارات", "الامارات", "uae", "emirates", "dubai", "دبي", "أبوظبي", "ابوظبي", "الشارقة", "العين"],
    "Egypt": ["مصر", "egypt", "cairo", "القاهرة", "alexandria", "الإسكندرية", "الاسكندرية", "الجيزة"],
    "Kuwait": ["الكويت", "kuwait", "kw", "السالمية"],
    "Qatar": ["قطر", "qatar", "doha", "الدوحة"],
    "Bahrain": ["البحرين", "bahrain", "manama", "المنامة"],
    "Oman": ["عُمان", "عمان", "oman", "muscat", "مسقط"],
    "Jordan": ["الأردن", "الاردن", "jordan", "amman", "عمّان"],
    "Lebanon": ["لبنان", "lebanon", "beirut", "بيروت"],
    "Iraq": ["العراق", "iraq", "baghdad", "بغداد", "البصرة"],
    "Morocco": ["المغرب", "morocco", "rabat", "casablanca", "الدار البيضاء", "marrakech"],
    "Algeria": ["الجزائر", "algeria", "algiers"],
    "Tunisia": ["تونس", "tunisia", "tunis"],
    "Palestine": ["فلسطين", "palestine", "gaza", "غزة", "القدس", "jerusalem"],
    "Syria": ["سوريا", "syria", "damascus", "دمشق", "حلب", "aleppo"],
    "Yemen": ["اليمن", "yemen", "sanaa", "صنعاء", "عدن", "aden"],
    "Libya": ["ليبيا", "libya", "tripoli", "طرابلس"],
    "Sudan": ["السودان", "sudan", "khartoum", "الخرطوم"],
    
    # 🌏 شرق آسيا
    "China": ["china", "中国", "beijing", "shanghai", "北京", "上海"],
    "Japan": ["japan", "日本", "tokyo", "東京", "osaka", "kyoto", "京都"],
    "South Korea": ["korea", "한국", "seoul", "서울", "busan", "kpop", "k-pop"],
    "Taiwan": ["taiwan", "台灣", "taipei", "台北"],
    "Hong Kong": ["hong kong", "hongkong", "香港", "hk"],
    "Macau": ["macau", "macao", "澳門"],
    "Mongolia": ["mongolia", "ulaanbaatar", "монгол"],
    
    # 🌏 جنوب شرق آسيا
    "Indonesia": ["indonesia", "jakarta", "bali", "bahasa indonesia"],
    "Malaysia": ["malaysia", "kuala lumpur", "kl", "bahasa malaysia"],
    "Singapore": ["singapore", "sg", "singapura"],
    "Thailand": ["thailand", "bangkok", "ประเทศไทย", "กรุงเทพ", "thai"],
    "Vietnam": ["vietnam", "viet nam", "hanoi", "hồ chí minh", "saigon"],
    "Philippines": ["philippines", "manila", "pinas", "filipino", "tagalog"],
    "Cambodia": ["cambodia", "phnom penh", "កម្ពុជា"],
    "Laos": ["laos", "vientiane"],
    "Myanmar": ["myanmar", "burma", "yangon", "မြန်မာ"],
    "Brunei": ["brunei"],
    
    # 🌏 جنوب آسيا
    "India": ["india", "delhi", "mumbai", "bangalore", "भारत", "indian", "desi"],
    "Pakistan": ["pakistan", "islamabad", "karachi", "lahore", "پاکستان"],
    "Bangladesh": ["bangladesh", "dhaka", "বাংলাদেশ"],
    "Sri Lanka": ["sri lanka", "colombo", "ශ්‍රී ලංකා"],
    "Nepal": ["nepal", "kathmandu", "नेपाल"],
    
    # 🌏 وسط/غرب آسيا
    "Turkey": ["turkey", "türkiye", "istanbul", "ankara", "turkish"],
    "Iran": ["iran", "tehran", "ایران", "persian"],
    "Israel": ["israel", "tel aviv", "ישראל"],
    "Kazakhstan": ["kazakhstan", "almaty", "astana"],
    "Uzbekistan": ["uzbekistan", "tashkent"],
    "Afghanistan": ["afghanistan", "kabul", "افغانستان"],
    "Armenia": ["armenia", "yerevan", "հայաստան"],
    "Azerbaijan": ["azerbaijan", "baku"],
    "Georgia": ["georgia", "tbilisi", "საქართველო"],
    
    # 🇺🇸 الأمريكتان
    "United States": ["usa", "america", "ny", "nyc", "la", "california", "texas", "florida", "boston"],
    "Canada": ["canada", "toronto", "vancouver", "montreal"],
    "Mexico": ["mexico", "méxico", "mexico city", "cdmx", "mexicano"],
    "Brazil": ["brazil", "brasil", "rio", "são paulo", "sao paulo", "português"],
    "Argentina": ["argentina", "buenos aires", "argentino"],
    "Colombia": ["colombia", "bogotá", "medellín"],
    "Chile": ["chile", "santiago"],
    "Peru": ["peru", "lima", "perú"],
    "Cuba": ["cuba", "havana", "la habana"],
    "Puerto Rico": ["puerto rico", "pr", "boricua"],
    
    # 🌍 أوروبا
    "United Kingdom": ["uk", "london", "britain", "england", "british"],
    "France": ["france", "paris", "français", "française"],
    "Italy": ["italy", "italia", "roma", "milano", "italian"],
    "Spain": ["spain", "españa", "madrid", "barcelona"],
    "Germany": ["germany", "berlin", "deutschland", "münchen"],
    "Netherlands": ["netherlands", "holland", "amsterdam"],
    "Portugal": ["portugal", "lisboa", "lisbon"],
    "Sweden": ["sweden", "stockholm", "sverige"],
    "Norway": ["norway", "oslo", "norge"],
    "Russia": ["russia", "moscow", "россия"],
    "Ukraine": ["ukraine", "kiev", "kyiv", "україна"],
    "Poland": ["poland", "warsaw", "polska"],
    "Greece": ["greece", "athens", "ελλάδα"],
    
    # 🌍 أفريقيا
    "Nigeria": ["nigeria", "lagos", "abuja", "naija"],
    "South Africa": ["south africa", "cape town", "johannesburg", "joburg"],
    "Kenya": ["kenya", "nairobi"],
    "Ethiopia": ["ethiopia", "addis ababa"],
    "Ghana": ["ghana", "accra"],
    
    # 🇦🇺 أوقيانوسيا
    "Australia": ["australia", "sydney", "melbourne", "aussie"],
    "New Zealand": ["new zealand", "auckland", "wellington", "kiwi"],
}


def sanitize_username(username):
    """تنظيف اسم المستخدم"""
    username = username.strip().lstrip("@")
    if "tiktok.com/" in username:
        username = username.split("tiktok.com/")[-1].lstrip("@").split("?")[0].split("/")[0]
    if not re.match(r"^[a-zA-Z0-9._]{1,24}$", username):
        raise ValueError("❌ اسم مستخدم غير صالح. استخدم حروف وأرقام فقط.")
    return username


def clean_bio(raw_bio):
    """تنظيف BIO من HTML"""
    if not raw_bio:
        return "لا يوجد وصف"
    text = str(raw_bio).strip()
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_lib.unescape(text)
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('\n', '<br>')
    return text if text.strip() else "لا يوجد وصف"


def format_number(n):
    """تنسيق الأرقام"""
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


def get_country_info(country_name):
    """إرجاع (code, flag, name_ar) من اسم الدولة"""
    if not country_name:
        return None
    country_name = country_name.strip()
    if country_name in COUNTRY_MAP:
        return COUNTRY_MAP[country_name]
    for key, val in COUNTRY_MAP.items():
        if key.lower() in country_name.lower() or country_name.lower() in key.lower():
            return val
    return None


# ============= 🌟 المصدر 1: TikMatrix عبر Jina =============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_tikmatrix(username):
    """جلب البيانات من TikMatrix"""
    result = {
        "source": "tikmatrix", "success": False,
        "nickname": None, "country": None, "language": None,
        "bio": None, "bio_link": None, "avatar": None,
        "user_id": None, "sec_uid": None, "account_created": None,
        "followers": 0, "following": 0, "hearts": 0,
        "videos": 0, "friends": 0, "error": None
    }
    try:
        target = f"https://user.tikmatrix.com/?username={username}"
        url = f"https://r.jina.ai/{target}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/markdown",
        }
        r = requests.get(url, headers=headers, timeout=25)

        if r.status_code == 429:
            result["error"] = "rate_limit"
            return result
        if r.status_code != 200:
            result["error"] = f"HTTP {r.status_code}"
            return result

        text = r.text
        if '🌍' not in text and '## ' not in text:
            result["error"] = "not_found"
            return result

        # الاسم
        m = re.search(r'^##\s+([^\n]+)\s*$', text, re.MULTILINE)
        if m:
            nick = m.group(1).strip()
            if not any(kw in nick for kw in ['Statistics', 'Account Details', 'Discover']):
                result["nickname"] = nick

        # الدولة
        m = re.search(r'🌍\s*\n?\s*([A-Za-z][A-Za-z\s,\.]+?)(?:\n|$)', text)
        if m:
            country = m.group(1).strip()
            country = re.sub(r'\s+(Discover|Statistics|TV).*$', '', country).strip()
            result["country"] = country

        # اللغة
        m = re.search(r'🌐\s*\n?\s*([a-z\-]+)', text)
        if m: result["language"] = m.group(1).strip()

        # الصورة
        m = re.search(r'!\[Image \d+: [^\]]+\]\(([^)]+)\)', text)
        if m: result["avatar"] = m.group(1).strip()

        # الإحصائيات
        for pattern, key in [
            (r'([\d,]+)\s*👥\s*Followers', 'followers'),
            (r'([\d,]+)\s*➕\s*Following', 'following'),
            (r'([\d,]+)\s*❤️\s*Hearts', 'hearts'),
            (r'([\d,]+)\s*🎬\s*Videos', 'videos'),
            (r'([\d,]+)\s*👫\s*Friends', 'friends'),
        ]:
            m = re.search(pattern, text)
            if m:
                try:
                    result[key] = int(m.group(1).replace(',', ''))
                except ValueError:
                    pass

        # BIO
        bio_match = re.search(r'\[📥 Download Videos\]\([^)]+\)\s*\n\s*\n([^\n\[]+)', text)
        if bio_match:
            result["bio"] = bio_match.group(1).strip()

        m = re.search(r'\n\[(https?://[^\]]+)\]\(\1\)', text)
        if m: result["bio_link"] = m.group(1).strip()

        m = re.search(r'User ID:\s*(\d+)', text)
        if m: result["user_id"] = m.group(1)

        m = re.search(r'SecUID:\s*([A-Za-z0-9_\-]+)', text)
        if m: result["sec_uid"] = m.group(1)

        m = re.search(r'Account Created:\s*([^\n]+)', text)
        if m:
            date_str = m.group(1).strip()
            date_str = re.sub(r'📋.*$', '', date_str).strip()
            result["account_created"] = date_str

        if result["nickname"] or result["country"] or result["followers"] > 0:
            result["success"] = True
    except requests.exceptions.Timeout:
        result["error"] = "timeout"
    except Exception as e:
        result["error"] = f"{type(e).__name__}"
        log.warning(f"TikMatrix error: {e}")
    return result


# ============= 🌟 المصدر 2: TikTok مباشر عبر Jina =============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_tiktok(username):
    """جلب البيانات من TikTok مباشرة عبر Jina"""
    result = {
        "source": "tiktok", "success": False,
        "nickname": None, "bio": None, "avatar": None,
        "followers": 0, "following": 0, "hearts": 0,
        "videos": 0, "verified": False, "language": None,
        "error": None
    }
    try:
        target = f"https://www.tiktok.com/@{username}"
        url = f"https://r.jina.ai/{target}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/markdown",
        }
        r = requests.get(url, headers=headers, timeout=25)
        if r.status_code != 200:
            result["error"] = f"HTTP {r.status_code}"
            return result

        text = r.text

        # اسم العرض من Title
        m = re.search(r'Title:\s*([^|(]+?)(?:\(@|\s*\|)', text)
        if m:
            result["nickname"] = m.group(1).strip()

        # تحقق: علامة التوثيق
        if '✓' in text[:500] or 'verified' in text.lower()[:1000]:
            result["verified"] = True

        # الإحصائيات (TikTok يعرضها بصيغة 7.7M)
        for pattern_list, key in [
            ([r'([\d.,]+[KMB]?)\s*Followers', r'([\d.,]+[KMB]?)\s*Following'], 'followers'),
            ([r'([\d.,]+[KMB]?)\s*Likes', r'([\d.,]+[KMB]?)\s*Hearts'], 'hearts'),
        ]:
            for pattern in pattern_list:
                m = re.search(pattern, text)
                if m:
                    val_str = m.group(1).replace(',', '')
                    mult = 1
                    if val_str.endswith('K'): mult = 1000; val_str = val_str[:-1]
                    elif val_str.endswith('M'): mult = 1_000_000; val_str = val_str[:-1]
                    elif val_str.endswith('B'): mult = 1_000_000_000; val_str = val_str[:-1]
                    try:
                        result[key] = int(float(val_str) * mult)
                        break
                    except ValueError:
                        pass

        # نمط آخر للمتابعين: "100M Followers"
        if not result["followers"]:
            m = re.search(r'(\d+(?:\.\d+)?)\s*([KMB])\s*Followers', text)
            if m:
                val = float(m.group(1))
                unit = m.group(2)
                mult = {"K": 1000, "M": 1_000_000, "B": 1_000_000_000}[unit]
                result["followers"] = int(val * mult)

        # BIO من Markdown
        bio_patterns = [
            r'@[a-zA-Z0-9._]+\s*\n+([^\n]+)\n',
            r'verified\s*\n+([^\n]+)\n',
        ]
        for p in bio_patterns:
            m = re.search(p, text)
            if m:
                bio = m.group(1).strip()
                if 5 < len(bio) < 200 and not bio.startswith('http'):
                    result["bio"] = bio
                    break

        # الصورة
        m = re.search(r'!\[[^\]]*\]\((https://[^)]+tiktokcdn[^)]+)\)', text)
        if m: result["avatar"] = m.group(1)

        if result["nickname"] or result["followers"] > 0 or result["bio"]:
            result["success"] = True
    except requests.exceptions.Timeout:
        result["error"] = "timeout"
    except Exception as e:
        result["error"] = f"{type(e).__name__}"
    return result


# ============= 🌟 المصدر 3: تحليل ذكي =============
def smart_country_analysis(bio, language, nickname):
    """تحليل ذكي للدولة من BIO + اللغة + الاسم"""
    candidates = {}  # {country: score}

    # 1. تحليل BIO للكلمات الجغرافية
    text = f"{bio or ''} {nickname or ''}".lower()
    for country, keywords in GEO_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                candidates[country] = candidates.get(country, 0) + 30
                break

    # 2. تحليل اللغة - أوزان متفاوتة (اللغات النادرة أكثر دقة)
    # لغات تشير لدولة واحدة بقوة (ko=كوريا، ja=اليابان، vi=فيتنام...)
    HIGH_CONFIDENCE_LANGS = {
        "ko": 50, "ja": 50, "th": 50, "vi": 50, "tl": 45, "fil": 45,
        "km": 50, "lo": 50, "my": 50, "mn": 50, "si": 45, "ne": 45,
        "kk": 45, "uz": 45, "ky": 45, "tg": 45, "tk": 45,
        "fa": 40, "ps": 40, "he": 45, "iw": 45,
        "hy": 50, "az": 45, "ka": 50,
        "el": 45, "uk": 35, "pl": 30, "cs": 35, "hu": 40, "ro": 35,
        "sv": 35, "no": 35, "da": 35, "fi": 40, "nl": 30,
        "tr": 35, "ru": 25, "ar": 15,  # ar منخفض لأنه يشمل دول كثيرة
        "en": 8, "es": 10, "fr": 12, "de": 25, "it": 25, "pt": 15,
        "zh-tw": 50, "zh-hk": 50, "zh-cn": 40, "zh": 25,
        "en-us": 25, "en-gb": 30,
    }
    if language and language in LANGUAGE_TO_COUNTRY:
        # خذ أول دولة في القائمة (الأكثر احتمالاً) وأعطها الوزن الأعلى
        weight = HIGH_CONFIDENCE_LANGS.get(language, 10)
        countries_list = LANGUAGE_TO_COUNTRY[language]
        if countries_list:
            # الدولة الأولى تأخذ الوزن الكامل
            candidates[countries_list[0]] = candidates.get(countries_list[0], 0) + weight
            # الدول الأخرى تأخذ نصف الوزن
            for c in countries_list[1:]:
                candidates[c] = candidates.get(c, 0) + weight // 3

    # 3. حروف عربية في الـ BIO
    if bio:
        arabic_chars = sum(1 for c in bio if '\u0600' <= c <= '\u06FF')
        if arabic_chars > 5:
            # رفع وزن الدول العربية الموجودة
            for country in list(candidates.keys()):
                if country in ["Saudi Arabia", "United Arab Emirates", "Egypt", "Kuwait",
                              "Qatar", "Bahrain", "Oman", "Jordan", "Lebanon", "Iraq",
                              "Morocco", "Algeria", "Tunisia", "Palestine", "Syria", "Yemen"]:
                    candidates[country] += 15

    if not candidates:
        return None, 0

    # ترتيب حسب النقاط
    best = max(candidates.items(), key=lambda x: x[1])
    return best[0], best[1]


# ============= 🎯 الدمج الذكي =============
def merge_sources(tm_data, tt_data, username):
    """
    دمج ذكي لمصادر TikMatrix + TikTok + تحليل
    يستخدم Voting + Confidence Score
    """
    merged = {
        "username": username,
        "nickname": None,
        "bio": None,
        "avatar": None,
        "country": None,
        "country_confidence": 0,
        "country_sources": [],
        "language": None,
        "followers": 0,
        "following": 0,
        "hearts": 0,
        "videos": 0,
        "friends": 0,
        "verified": False,
        "user_id": None,
        "sec_uid": None,
        "account_created": None,
        "bio_link": None,
        "sources_status": {
            "tikmatrix": tm_data.get("success", False),
            "tiktok": tt_data.get("success", False),
        },
        "errors": []
    }

    # دمج البيانات الأساسية (الأولوية لـ TikMatrix ثم TikTok)
    merged["nickname"] = tm_data.get("nickname") or tt_data.get("nickname") or username
    merged["bio"] = tm_data.get("bio") or tt_data.get("bio")
    merged["avatar"] = tm_data.get("avatar") or tt_data.get("avatar")
    merged["language"] = tm_data.get("language") or tt_data.get("language")
    merged["verified"] = tm_data.get("verified", False) or tt_data.get("verified", False)

    # تفاصيل من TikMatrix فقط
    merged["user_id"] = tm_data.get("user_id")
    merged["sec_uid"] = tm_data.get("sec_uid")
    merged["account_created"] = tm_data.get("account_created")
    merged["bio_link"] = tm_data.get("bio_link")
    merged["friends"] = tm_data.get("friends", 0)

    # الإحصائيات: أكبر قيمة بين المصدرين (التيك توك دائماً أحدث)
    merged["followers"] = max(tm_data.get("followers", 0), tt_data.get("followers", 0))
    merged["hearts"] = max(tm_data.get("hearts", 0), tt_data.get("hearts", 0))
    merged["videos"] = max(tm_data.get("videos", 0), tt_data.get("videos", 0))
    merged["following"] = tm_data.get("following", 0) or tt_data.get("following", 0)

    # =========== 🎯 منطق كشف الدولة (الأهم) ===========
    tm_country = tm_data.get("country")
    smart_country, smart_score = smart_country_analysis(
        merged["bio"], merged["language"], merged["nickname"]
    )

    confidence = 0
    sources_used = []

    if tm_country:
        merged["country"] = tm_country
        confidence = 75  # TikMatrix فقط
        sources_used.append("TikMatrix")

        # تأكيد من التحليل الذكي
        if smart_country and tm_country and smart_country.lower() in tm_country.lower():
            confidence = 98  # تأكيد قوي
            sources_used.append("تحليل ذكي")
        elif smart_country:
            # تعارض → نقلل الثقة قليلاً
            confidence = 65
            sources_used.append("⚠️ تحليل مختلف")

    elif smart_country and smart_score >= 30:
        # لا توجد دولة في TikMatrix → نستخدم التحليل
        merged["country"] = smart_country
        confidence = min(smart_score + 20, 70)  # حد أقصى 70%
        sources_used.append("تحليل ذكي")

    elif merged["language"] and merged["language"] in LANGUAGE_TO_COUNTRY:
        # ملاذ أخير: اللغة فقط
        merged["country"] = LANGUAGE_TO_COUNTRY[merged["language"]][0]
        confidence = 35
        sources_used.append("لغة فقط")

    merged["country_confidence"] = confidence
    merged["country_sources"] = sources_used

    # جمع الأخطاء
    if tm_data.get("error"):
        merged["errors"].append(f"TikMatrix: {tm_data['error']}")
    if tt_data.get("error"):
        merged["errors"].append(f"TikTok: {tt_data['error']}")

    return merged


# ============= معدل الطلبات =============
def check_rate_limit():
    """منع المستخدم من إرسال أكثر من طلب كل 3 ثوانٍ"""
    now = time.time()
    if 'last_request' in st.session_state:
        elapsed = now - st.session_state['last_request']
        if elapsed < 3:
            return False, 3 - elapsed
    st.session_state['last_request'] = now
    return True, 0


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
        # تحقق من Rate Limit
        ok, wait_time = check_rate_limit()
        if not ok:
            st.markdown(f"""
            <div class='rate-limit-notice'>
                ⏱️ الرجاء الانتظار {wait_time:.1f} ثانية قبل البحث التالي
            </div>
            """, unsafe_allow_html=True)
            return

        try:
            username = sanitize_username(username_input)
        except ValueError as e:
            st.markdown(f"<div class='alert-error'>{e}</div>", unsafe_allow_html=True)
            return

        # جلب البيانات من مصدرين بالتوازي
        with st.spinner("🦅 بَصِير يحلّق على مصدرين..."):
            tm_data = fetch_from_tikmatrix(username)
            tt_data = fetch_from_tiktok(username)
            data = merge_sources(tm_data, tt_data, username)

        # تحقق من نجاح المصدرين معاً
        if not (data["sources_status"]["tikmatrix"] or data["sources_status"]["tiktok"]):
            errors = ' | '.join(data["errors"]) if data["errors"] else "غير معروف"
            st.markdown(f"""
            <div class='alert-error'>
                ❌ تعذّر جلب بيانات الحساب @{username} من أي مصدر<br>
                <small>{errors}</small>
            </div>
            """, unsafe_allow_html=True)
            return

        # ===== شريط المصادر =====
        tm_status = "success" if data["sources_status"]["tikmatrix"] else "fail"
        tt_status = "success" if data["sources_status"]["tiktok"] else "fail"
        tm_icon = "✅" if tm_status == "success" else "❌"
        tt_icon = "✅" if tt_status == "success" else "❌"

        # ===== بطاقة الحساب =====
        avatar_url = data.get("avatar") or "https://via.placeholder.com/140/F59E0B/0F172A?text=Baseer"
        nickname_safe = re.sub(r'<[^>]+>', '', str(data["nickname"]))
        nickname_safe = nickname_safe.replace('<', '&lt;').replace('>', '&gt;')
        bio_clean = clean_bio(data.get("bio") or "")
        verified_badge = " ✓" if data.get("verified") else ""

        st.markdown(f"""
        <div class='account-card'>
            <div class='account-flex'>
                <div class='account-avatar'>
                    <img src='{avatar_url}' alt='avatar' onerror="this.src='https://via.placeholder.com/140/F59E0B/0F172A?text=Baseer'"/>
                </div>
                <div class='account-info'>
                    <div class='account-name'>{nickname_safe}{verified_badge}</div>
                    <div class='account-username'>@{username}</div>
                    <div class='account-bio'>{bio_clean}</div>
                    <div>
                        <span class='account-meta-item'>🌐 اللغة: {data.get('language') or 'غير محدد'}</span>
                        {f"<span class='account-meta-item'>🔗 <a href='{data['bio_link']}' target='_blank' style='color:#FCD34D;text-decoration:none;'>رابط BIO</a></span>" if data.get('bio_link') else ""}
                    </div>
                </div>
            </div>
            <div class='sources-bar'>
                <span class='source-tag {tm_status}'>{tm_icon} TikMatrix</span>
                <span class='source-tag {tt_status}'>{tt_icon} TikTok</span>
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

        # ===== بطاقة الدولة مع Confidence Score =====
        country_info = get_country_info(data.get("country"))
        if country_info:
            code, flag, name_ar = country_info
            conf = data["country_confidence"]
            sources_str = " + ".join(data["country_sources"])

            # اختيار اللون حسب الثقة
            if conf >= 90:
                card_class = "country-card-high"
                conf_emoji = "🟢"
                conf_text = "دقة عالية جداً"
            elif conf >= 65:
                card_class = "country-card-medium"
                conf_emoji = "🟡"
                conf_text = "دقة متوسطة"
            else:
                card_class = "country-card-low"
                conf_emoji = "🟠"
                conf_text = "دقة منخفضة"

            st.markdown(f"""
            <div class='country-card {card_class}'>
                <div class='country-flag'>{flag}</div>
                <div class='country-name'>{name_ar}</div>
                <div class='country-confidence'>
                    {conf_emoji} الثقة: {conf}% ({conf_text})<br>
                    <span style='font-size:14px;opacity:0.9;'>المصادر: {sources_str}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='alert-warn'>
                ⚠️ لم نتمكن من تحديد الدولة لهذا الحساب<br>
                <small>قد يكون الحساب جديداً أو محمياً أو خاصاً</small>
            </div>
            """, unsafe_allow_html=True)

        # ===== تفاصيل الحساب =====
        if data.get("user_id") or data.get("sec_uid") or data.get("account_created"):
            details_html = "<div class='details-card'>"
            details_html += "<h3 style='color:#FCD34D;margin:0 0 15px 0;direction:rtl;'>📋 تفاصيل الحساب</h3>"
            if data.get("user_id"):
                details_html += f"<div class='detail-row'><span class='detail-label'>🆔 User ID</span><span class='detail-value'>{data['user_id']}</span></div>"
            if data.get("sec_uid"):
                details_html += f"<div class='detail-row'><span class='detail-label'>🔐 SecUID</span><span class='detail-value' style='font-size:11px;max-width:60%;'>{data['sec_uid']}</span></div>"
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
        🦅 بَصِير v1.8 - Global Coverage Edition © 2026
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
