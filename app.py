"""
مولد معلومات حسابات التواصل الاجتماعي - النسخة v3
Social Accounts Info Generator - v3 (Improved Country Detection)
"""

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import io
import re
import time
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# ============ إعدادات الصفحة ============
st.set_page_config(
    page_title="مولد معلومات حسابات التواصل الاجتماعي",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ CSS ============
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', 'Tajawal', sans-serif !important;
        direction: rtl; text-align: right;
    }
    .main .block-container { direction: rtl; text-align: right; padding-top: 2rem; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Cairo', sans-serif !important; text-align: right; }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 10px;
        padding: 0.6rem 1.5rem; font-weight: 700;
        font-family: 'Cairo', sans-serif; width: 100%;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102,126,234,0.4); }
    .stTextArea textarea { direction: rtl; text-align: right; font-family: 'Tajawal', monospace; font-size: 14px; }
    .stTextInput input { direction: ltr; text-align: left; }
    [data-testid="stSidebar"] { direction: rtl; text-align: right; }
    .stDataFrame { direction: ltr; }
    .info-box { background: #dbeafe; border-right: 4px solid #3b82f6; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .warn-box { background: #fef3c7; border-right: 4px solid #f59e0b; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============ المنصات ============
PLATFORMS = {
    "x": {"name": "X (Twitter)", "icon": "🐦", "url": "https://x.com/{}", "host": "x.com"},
    "twitter": {"name": "Twitter", "icon": "🐦", "url": "https://twitter.com/{}", "host": "twitter.com"},
    "instagram": {"name": "Instagram", "icon": "📷", "url": "https://www.instagram.com/{}/", "host": "instagram.com"},
    "youtube": {"name": "YouTube", "icon": "▶️", "url": "https://www.youtube.com/@{}", "host": "youtube.com"},
    "facebook": {"name": "Facebook", "icon": "👥", "url": "https://www.facebook.com/{}", "host": "facebook.com"},
    "snapchat": {"name": "Snapchat", "icon": "👻", "url": "https://www.snapchat.com/add/{}", "host": "snapchat.com"},
    "tiktok": {"name": "TikTok", "icon": "🎵", "url": "https://www.tiktok.com/@{}", "host": "tiktok.com"},
    "linkedin": {"name": "LinkedIn", "icon": "💼", "url": "https://www.linkedin.com/in/{}", "host": "linkedin.com"},
    "threads": {"name": "Threads", "icon": "🧵", "url": "https://www.threads.net/@{}", "host": "threads.net"},
    "reddit": {"name": "Reddit", "icon": "🤖", "url": "https://www.reddit.com/user/{}", "host": "reddit.com"},
    "pinterest": {"name": "Pinterest", "icon": "📌", "url": "https://www.pinterest.com/{}/", "host": "pinterest.com"},
    "telegram": {"name": "Telegram", "icon": "✈️", "url": "https://t.me/{}", "host": "t.me"},
    "twitch": {"name": "Twitch", "icon": "🎮", "url": "https://www.twitch.tv/{}", "host": "twitch.tv"},
    "github": {"name": "GitHub", "icon": "💻", "url": "https://github.com/{}", "host": "github.com"},
}

# ============ خريطة الدول ============
COUNTRY_FLAGS = {
    "SA": "🇸🇦", "AE": "🇦🇪", "EG": "🇪🇬", "KW": "🇰🇼", "QA": "🇶🇦",
    "BH": "🇧🇭", "OM": "🇴🇲", "JO": "🇯🇴", "LB": "🇱🇧", "SY": "🇸🇾",
    "IQ": "🇮🇶", "YE": "🇾🇪", "PS": "🇵🇸", "MA": "🇲🇦", "DZ": "🇩🇿",
    "TN": "🇹🇳", "LY": "🇱🇾", "SD": "🇸🇩", "SO": "🇸🇴", "MR": "🇲🇷",
    "DJ": "🇩🇯", "KM": "🇰🇲",
    "US": "🇺🇸", "GB": "🇬🇧", "FR": "🇫🇷", "DE": "🇩🇪", "IT": "🇮🇹",
    "ES": "🇪🇸", "NL": "🇳🇱", "BE": "🇧🇪", "CH": "🇨🇭", "SE": "🇸🇪",
    "NO": "🇳🇴", "DK": "🇩🇰", "FI": "🇫🇮", "PL": "🇵🇱", "GR": "🇬🇷",
    "RU": "🇷🇺", "UA": "🇺🇦", "CN": "🇨🇳", "JP": "🇯🇵", "KR": "🇰🇷",
    "IN": "🇮🇳", "PK": "🇵🇰", "BD": "🇧🇩", "TR": "🇹🇷", "IR": "🇮🇷",
    "AF": "🇦🇫", "BR": "🇧🇷", "AR": "🇦🇷", "MX": "🇲🇽", "CA": "🇨🇦",
    "AU": "🇦🇺", "NZ": "🇳🇿", "ID": "🇮🇩", "MY": "🇲🇾", "SG": "🇸🇬",
    "TH": "🇹🇭", "VN": "🇻🇳", "PH": "🇵🇭", "NG": "🇳🇬", "ZA": "🇿🇦",
    "KE": "🇰🇪", "ET": "🇪🇹", "GH": "🇬🇭",
}

COUNTRY_AR = {
    "SA": "السعودية", "AE": "الإمارات", "EG": "مصر", "KW": "الكويت", "QA": "قطر",
    "BH": "البحرين", "OM": "عُمان", "JO": "الأردن", "LB": "لبنان", "SY": "سوريا",
    "IQ": "العراق", "YE": "اليمن", "PS": "فلسطين", "MA": "المغرب", "DZ": "الجزائر",
    "TN": "تونس", "LY": "ليبيا", "SD": "السودان", "SO": "الصومال", "MR": "موريتانيا",
    "DJ": "جيبوتي", "KM": "جزر القمر",
    "US": "الولايات المتحدة", "GB": "بريطانيا", "FR": "فرنسا", "DE": "ألمانيا", "IT": "إيطاليا",
    "ES": "إسبانيا", "NL": "هولندا", "BE": "بلجيكا", "CH": "سويسرا", "SE": "السويد",
    "NO": "النرويج", "DK": "الدنمارك", "FI": "فنلندا", "PL": "بولندا", "GR": "اليونان",
    "RU": "روسيا", "UA": "أوكرانيا", "CN": "الصين", "JP": "اليابان", "KR": "كوريا الجنوبية",
    "IN": "الهند", "PK": "باكستان", "BD": "بنغلاديش", "TR": "تركيا", "IR": "إيران",
    "AF": "أفغانستان", "BR": "البرازيل", "AR": "الأرجنتين", "MX": "المكسيك", "CA": "كندا",
    "AU": "أستراليا", "NZ": "نيوزيلندا", "ID": "إندونيسيا", "MY": "ماليزيا", "SG": "سنغافورة",
    "TH": "تايلاند", "VN": "فيتنام", "PH": "الفلبين", "NG": "نيجيريا", "ZA": "جنوب أفريقيا",
    "KE": "كينيا", "ET": "إثيوبيا", "GH": "غانا",
}

# ============ خريطة المدن (موسّعة) ============
CITY_TO_COUNTRY = {
    # السعودية
    "riyadh": "SA", "jeddah": "SA", "jiddah": "SA", "mecca": "SA", "makkah": "SA", "medina": "SA", "madinah": "SA",
    "dammam": "SA", "khobar": "SA", "taif": "SA", "abha": "SA", "tabuk": "SA", "qassim": "SA", "hail": "SA",
    "الرياض": "SA", "جدة": "SA", "مكة": "SA", "المدينة": "SA", "الدمام": "SA", "الخبر": "SA",
    "الطائف": "SA", "أبها": "SA", "تبوك": "SA", "السعودية": "SA", "ksa": "SA", "saudi arabia": "SA",
    "saudi": "SA", "القصيم": "SA", "حائل": "SA", "نجران": "SA", "جازان": "SA",
    # الإمارات
    "dubai": "AE", "abu dhabi": "AE", "abudhabi": "AE", "sharjah": "AE", "ajman": "AE", "fujairah": "AE",
    "ras al khaimah": "AE", "al ain": "AE",
    "دبي": "AE", "أبوظبي": "AE", "ابوظبي": "AE", "الشارقة": "AE", "عجمان": "AE", "العين": "AE",
    "الفجيرة": "AE", "رأس الخيمة": "AE", "الإمارات": "AE", "الامارات": "AE", "uae": "AE",
    "united arab emirates": "AE",
    # مصر
    "cairo": "EG", "alexandria": "EG", "giza": "EG", "luxor": "EG", "aswan": "EG", "mansoura": "EG",
    "tanta": "EG", "ismailia": "EG", "suez": "EG", "port said": "EG", "sharm el sheikh": "EG", "egypt": "EG",
    "القاهرة": "EG", "الإسكندرية": "EG", "الاسكندرية": "EG", "الجيزة": "EG", "الأقصر": "EG", "أسوان": "EG",
    "مصر": "EG", "المنصورة": "EG", "طنطا": "EG", "الإسماعيلية": "EG", "السويس": "EG", "بورسعيد": "EG",
    "شرم الشيخ": "EG", "أسيوط": "EG",
    # الكويت
    "kuwait": "KW", "kuwait city": "KW", "الكويت": "KW", "حولي": "KW", "السالمية": "KW",
    # قطر
    "doha": "QA", "qatar": "QA", "الدوحة": "QA", "قطر": "QA", "الريان": "QA",
    # البحرين
    "manama": "BH", "bahrain": "BH", "المنامة": "BH", "البحرين": "BH",
    # عُمان
    "muscat": "OM", "oman": "OM", "salalah": "OM", "مسقط": "OM", "صلالة": "OM",
    "سلطنة عمان": "OM", "السلطنة": "OM",
    # الأردن
    "amman": "JO", "jordan": "JO", "irbid": "JO", "zarqa": "JO",
    "عمّان": "JO", "عمان": "JO", "الأردن": "JO", "الاردن": "JO", "إربد": "JO", "اربد": "JO", "الزرقاء": "JO",
    # لبنان
    "beirut": "LB", "lebanon": "LB", "tripoli lebanon": "LB", "بيروت": "LB", "لبنان": "LB", "صيدا": "LB", "صور": "LB",
    # العراق
    "baghdad": "IQ", "iraq": "IQ", "basra": "IQ", "erbil": "IQ", "mosul": "IQ", "najaf": "IQ", "karbala": "IQ",
    "بغداد": "IQ", "العراق": "IQ", "البصرة": "IQ", "أربيل": "IQ", "اربيل": "IQ", "الموصل": "IQ",
    "النجف": "IQ", "كربلاء": "IQ", "كردستان": "IQ",
    # سوريا
    "damascus": "SY", "syria": "SY", "aleppo": "SY", "homs": "SY", "latakia": "SY",
    "دمشق": "SY", "سوريا": "SY", "حلب": "SY", "حمص": "SY", "اللاذقية": "SY", "حماة": "SY",
    # اليمن
    "sanaa": "YE", "yemen": "YE", "aden": "YE", "صنعاء": "YE", "اليمن": "YE", "عدن": "YE", "تعز": "YE", "حضرموت": "YE",
    # فلسطين
    "palestine": "PS", "gaza": "PS", "ramallah": "PS", "jerusalem": "PS", "hebron": "PS", "nablus": "PS",
    "فلسطين": "PS", "غزة": "PS", "القدس": "PS", "رام الله": "PS", "الخليل": "PS", "نابلس": "PS", "بيت لحم": "PS",
    # المغرب
    "morocco": "MA", "casablanca": "MA", "rabat": "MA", "marrakech": "MA", "marrakesh": "MA", "fez": "MA",
    "tangier": "MA", "agadir": "MA",
    "المغرب": "MA", "الدار البيضاء": "MA", "الرباط": "MA", "مراكش": "MA", "فاس": "MA", "طنجة": "MA", "أكادير": "MA",
    # الجزائر
    "algeria": "DZ", "algiers": "DZ", "oran": "DZ", "constantine": "DZ",
    "الجزائر": "DZ", "وهران": "DZ", "قسنطينة": "DZ", "عنابة": "DZ",
    # تونس
    "tunisia": "TN", "tunis": "TN", "sfax": "TN", "sousse": "TN",
    "تونس": "TN", "صفاقس": "TN", "سوسة": "TN", "بنزرت": "TN",
    # ليبيا
    "libya": "LY", "tripoli libya": "LY", "benghazi": "LY", "misrata": "LY",
    "ليبيا": "LY", "طرابلس": "LY", "بنغازي": "LY", "مصراتة": "LY",
    # السودان
    "sudan": "SD", "khartoum": "SD", "السودان": "SD", "الخرطوم": "SD", "أم درمان": "SD",
    # الصومال
    "somalia": "SO", "mogadishu": "SO", "الصومال": "SO", "مقديشو": "SO",
    # موريتانيا
    "mauritania": "MR", "nouakchott": "MR", "موريتانيا": "MR", "نواكشوط": "MR",
    # دول أخرى
    "usa": "US", "u.s.a": "US", "united states": "US", "america": "US", "new york": "US", "los angeles": "US",
    "san francisco": "US", "chicago": "US", "miami": "US", "boston": "US", "washington": "US", "texas": "US",
    "california": "US", "florida": "US", "nyc": "US", "أمريكا": "US", "امريكا": "US", "نيويورك": "US",
    "uk": "GB", "u.k": "GB", "united kingdom": "GB", "london": "GB", "england": "GB", "britain": "GB",
    "manchester": "GB", "scotland": "GB", "wales": "GB", "بريطانيا": "GB", "لندن": "GB", "إنجلترا": "GB",
    "france": "FR", "paris": "FR", "lyon": "FR", "marseille": "FR", "فرنسا": "FR", "باريس": "FR",
    "germany": "DE", "berlin": "DE", "munich": "DE", "hamburg": "DE", "ألمانيا": "DE", "المانيا": "DE", "برلين": "DE",
    "italy": "IT", "rome": "IT", "milan": "IT", "إيطاليا": "IT", "ايطاليا": "IT", "روما": "IT",
    "spain": "ES", "madrid": "ES", "barcelona": "ES", "إسبانيا": "ES", "اسبانيا": "ES", "مدريد": "ES",
    "netherlands": "NL", "amsterdam": "NL", "هولندا": "NL", "أمستردام": "NL",
    "turkey": "TR", "istanbul": "TR", "ankara": "TR", "izmir": "TR",
    "تركيا": "TR", "إسطنبول": "TR", "اسطنبول": "TR", "أنقرة": "TR", "انقرة": "TR",
    "iran": "IR", "tehran": "IR", "إيران": "IR", "ايران": "IR", "طهران": "IR",
    "afghanistan": "AF", "kabul": "AF", "أفغانستان": "AF", "افغانستان": "AF", "كابول": "AF",
    "india": "IN", "delhi": "IN", "mumbai": "IN", "bangalore": "IN", "الهند": "IN", "نيودلهي": "IN",
    "pakistan": "PK", "karachi": "PK", "lahore": "PK", "islamabad": "PK", "باكستان": "PK", "إسلام آباد": "PK",
    "bangladesh": "BD", "dhaka": "BD", "بنغلاديش": "BD", "دكا": "BD",
    "china": "CN", "beijing": "CN", "shanghai": "CN", "الصين": "CN", "بكين": "CN", "شنغهاي": "CN",
    "japan": "JP", "tokyo": "JP", "osaka": "JP", "اليابان": "JP", "طوكيو": "JP",
    "south korea": "KR", "seoul": "KR", "كوريا الجنوبية": "KR", "كوريا": "KR", "سيول": "KR",
    "russia": "RU", "moscow": "RU", "روسيا": "RU", "موسكو": "RU",
    "ukraine": "UA", "kyiv": "UA", "kiev": "UA", "أوكرانيا": "UA", "اوكرانيا": "UA", "كييف": "UA",
    "canada": "CA", "toronto": "CA", "vancouver": "CA", "montreal": "CA", "كندا": "CA", "تورنتو": "CA",
    "australia": "AU", "sydney": "AU", "melbourne": "AU", "أستراليا": "AU", "استراليا": "AU", "سيدني": "AU",
    "brazil": "BR", "sao paulo": "BR", "rio": "BR", "البرازيل": "BR",
    "mexico": "MX", "المكسيك": "MX",
    "indonesia": "ID", "jakarta": "ID", "إندونيسيا": "ID", "اندونيسيا": "ID",
    "malaysia": "MY", "kuala lumpur": "MY", "ماليزيا": "MY", "كوالالمبور": "MY",
    "singapore": "SG", "سنغافورة": "SG", "سنغافوره": "SG",
    "thailand": "TH", "bangkok": "TH", "تايلاند": "TH",
    "philippines": "PH", "manila": "PH", "الفلبين": "PH",
    "south africa": "ZA", "johannesburg": "ZA", "cape town": "ZA", "جنوب أفريقيا": "ZA",
    "nigeria": "NG", "lagos": "NG", "نيجيريا": "NG",
    "kenya": "KE", "nairobi": "KE", "كينيا": "KE", "نيروبي": "KE",
    "ethiopia": "ET", "addis ababa": "ET", "إثيوبيا": "ET", "اثيوبيا": "ET",
}

# ============ مؤشرات اللهجة العربية → دولة ============
DIALECT_HINTS = {
    "SA": ["والله", "يا اخوي", "يا أخوي", "وش", "ايش", "كيفك", "وش رايك", "تكفى", "لاهنت", "يجزاك", "خويا", "بليز",
           "بسكوت", "كميل", "قاعد", "تو", "خلاص", "حلو", "زين", "مرة", "وايد"],
    "EG": ["ازيك", "إزيك", "ازاي", "إزاي", "كده", "كدا", "اوي", "أوي", "خالص", "يا باشا", "يا معلم", "بقى", "يلا",
           "احنا", "يعني ايه", "ماشي", "تمام", "حاجة", "حاجه", "زي", "عاوز", "عايز"],
    "AE": ["شحالك", "ها يبه", "يبه", "خويا", "عساكم", "هلا والله", "تسلم", "ان شاء الله", "ماعليه", "وايد"],
    "KW": ["شلونك", "حياك", "هلا", "تكفى", "يبه", "ها يبه", "والنبي"],
    "MA": ["واخا", "بزاف", "زعما", "كيفاش", "شنو", "غادي", "دابا", "خويا", "صافي", "بصح"],
    "DZ": ["واش", "كيراك", "بصح", "بزاف", "نتي", "نتا", "خويا"],
    "IQ": ["شلون", "اشلون", "هسة", "هسه", "اكو", "ماكو", "هواي", "خوش", "زين", "وين"],
    "LB": ["شو", "كيفك", "هلق", "بيعمل", "كتير"],
    "SY": ["شو في", "كيفك", "هلق", "بدي", "بيعمل", "كتير"],
    "YE": ["كيف حالك", "وشلون", "متى", "بهالعنا"],
}


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}


# ============ دوال المساعدة ============
def parse_url_to_platform(url: str):
    url = url.strip()
    if not url:
        return None, None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.strip("/")
        mapping = {
            "x.com": "x", "twitter.com": "twitter", "instagram.com": "instagram",
            "youtube.com": "youtube", "youtu.be": "youtube", "facebook.com": "facebook",
            "fb.com": "facebook", "snapchat.com": "snapchat", "tiktok.com": "tiktok",
            "linkedin.com": "linkedin", "threads.net": "threads", "reddit.com": "reddit",
            "pinterest.com": "pinterest", "t.me": "telegram", "telegram.me": "telegram",
            "twitch.tv": "twitch", "github.com": "github",
        }
        platform = mapping.get(host)
        if not platform:
            return None, None
        username = path.split("/")[0] if path else ""
        username = username.replace("@", "")
        if platform == "youtube" and "channel/" in parsed.path:
            username = parsed.path.split("channel/")[-1].strip("/")
        elif platform == "linkedin" and "in/" in parsed.path:
            username = parsed.path.split("in/")[-1].strip("/").split("/")[0]
        elif platform == "reddit" and ("user/" in parsed.path or "u/" in parsed.path):
            for prefix in ["user/", "u/"]:
                if prefix in parsed.path:
                    username = parsed.path.split(prefix)[-1].strip("/").split("/")[0]
                    break
        elif platform == "snapchat" and "add/" in parsed.path:
            username = parsed.path.split("add/")[-1].strip("/").split("/")[0]
        return platform, username if username else None
    except Exception:
        return None, None


def parse_manual_input(text: str):
    entries = []
    seen = set()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        if line.startswith("#"):
            continue
        platform, username = None, None
        if "http" in line or any(d in line for d in [".com", ".net", ".tv", "t.me"]):
            platform, username = parse_url_to_platform(line)
        else:
            for sep in [",", ":", "\t", "|", " "]:
                if sep in line:
                    parts = [p.strip() for p in line.split(sep, 1)]
                    if len(parts) == 2 and parts[0].lower() in PLATFORMS:
                        platform = parts[0].lower()
                        username = parts[1].replace("@", "").strip()
                        break
        if platform and username:
            key = (platform, username.lower())
            if key not in seen:
                seen.add(key)
                entries.append({"platform": platform, "username": username})
    return entries


# ============ كشف الدولة من النص ============
def detect_country_from_text(text: str):
    """استنتاج الدولة من النص (بايو، اسم، الخ) مع إرجاع (الكود, مستوى الثقة)."""
    if not text:
        return None, 0
    text_lower = text.lower()

    # 1. أعلام مباشرة (ثقة عالية جداً)
    for code, flag in COUNTRY_FLAGS.items():
        if flag in text:
            return code, 95

    # 2. كلمات مفتاحية للمدن/الدول (ثقة عالية)
    # ترتيب حسب الطول (الأطول أولاً) لتجنب التداخل
    sorted_keywords = sorted(CITY_TO_COUNTRY.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        code = CITY_TO_COUNTRY[keyword]
        # عربي أو متعدد الأحرف
        if any(ord(c) > 127 for c in keyword):
            if keyword in text:
                return code, 85
        else:
            # إنجليزي مع word boundary
            if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
                return code, 85

    # 3. لهجات عربية (ثقة متوسطة)
    for code, hints in DIALECT_HINTS.items():
        matches = sum(1 for h in hints if h in text)
        if matches >= 2:  # على الأقل تطابقين
            return code, 60
        elif matches == 1:
            # حفظه كاحتمال ضعيف، لكن نكمل البحث
            pass

    # 4. لهجة واحدة فقط (ثقة منخفضة)
    for code, hints in DIALECT_HINTS.items():
        for h in hints:
            if h in text:
                return code, 40

    return None, 0


# ============ IP Geolocation للسيرفر فقط ============
@st.cache_data(ttl=86400, show_spinner=False)
def get_ip_geolocation(host: str):
    try:
        ip = socket.gethostbyname(host)
        resp = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city",
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                return {
                    "ip": ip,
                    "server_country": data.get("country", ""),
                    "server_country_code": data.get("countryCode", ""),
                    "server_city": data.get("city", ""),
                }
    except Exception:
        pass
    return {"ip": "", "server_country": "", "server_country_code": "", "server_city": ""}


# ============ استخراج الـ ID الدائم ============
def extract_permanent_id(platform: str, username: str, html: str, soup: BeautifulSoup):
    permanent_id = ""
    try:
        if platform in ("x", "twitter"):
            for p in [r'"rest_id"\s*:\s*"(\d+)"', r'"id_str"\s*:\s*"(\d+)"', r'"user_id"\s*:\s*"?(\d+)"?']:
                m = re.search(p, html)
                if m:
                    permanent_id = m.group(1)
                    break

        elif platform == "instagram":
            m = re.search(r'"profilePage_(\d+)"', html) or \
                re.search(r'"owner":\{"id":"(\d+)"', html) or \
                re.search(r'"user_id"\s*:\s*"(\d+)"', html) or \
                re.search(r'"profile_id"\s*:\s*"?(\d+)"?', html)
            if m:
                permanent_id = m.group(1)

        elif platform == "youtube":
            m = re.search(r'"channelId":"(UC[\w-]{20,24})"', html) or \
                re.search(r'"externalId":"(UC[\w-]{20,24})"', html) or \
                re.search(r'channel/(UC[\w-]{20,24})', html)
            if m:
                permanent_id = m.group(1)

        elif platform == "facebook":
            m = re.search(r'"userID":"(\d+)"', html) or \
                re.search(r'"profile_id":(\d+)', html) or \
                re.search(r'fb://profile/(\d+)', html) or \
                re.search(r'"entity_id":"(\d+)"', html)
            if m:
                permanent_id = m.group(1)

        elif platform == "tiktok":
            m = re.search(r'"id":"(\d{15,25})"', html) or \
                re.search(r'"user_id":"(\d+)"', html)
            sec_m = re.search(r'"secUid":"([^"]+)"', html)
            if m:
                permanent_id = m.group(1)
            if sec_m and not permanent_id:
                permanent_id = sec_m.group(1)

        elif platform == "github":
            try:
                api = requests.get(f"https://api.github.com/users/{username}",
                                   headers={"User-Agent": USER_AGENT}, timeout=5)
                if api.status_code == 200:
                    permanent_id = str(api.json().get("id", ""))
            except Exception:
                pass

        elif platform == "reddit":
            try:
                api = requests.get(f"https://www.reddit.com/user/{username}/about.json",
                                   headers=HEADERS, timeout=5)
                if api.status_code == 200:
                    data = api.json().get("data", {})
                    permanent_id = data.get("id", "") or data.get("subreddit", {}).get("name", "")
            except Exception:
                pass

        elif platform == "linkedin":
            m = re.search(r'"publicIdentifier":"([^"]+)"', html) or \
                re.search(r'"entityUrn":"urn:li:fsd_profile:([^"]+)"', html)
            if m:
                permanent_id = m.group(1)

        elif platform == "twitch":
            m = re.search(r'"userID":"(\d+)"', html) or re.search(r'"channelID":"(\d+)"', html)
            if m:
                permanent_id = m.group(1)

        elif platform == "pinterest":
            m = re.search(r'"id":"(\d{6,20})"', html)
            if m:
                permanent_id = m.group(1)

        elif platform == "threads":
            m = re.search(r'"user_id":"(\d+)"', html) or re.search(r'"pk":"(\d+)"', html)
            if m:
                permanent_id = m.group(1)

        elif platform == "snapchat":
            m = re.search(r'"userId":"([^"]+)"', html) or re.search(r'"bitmojiUserId":"([^"]+)"', html)
            if m:
                permanent_id = m.group(1)
    except Exception:
        pass
    return permanent_id


# ============ استخراج الموقع المُعلن (المستخدم نفسه كتبه) ============
def extract_user_declared_location(platform: str, html: str, soup: BeautifulSoup):
    """استخراج الموقع الذي كتبه المستخدم بنفسه فقط (غير region السيرفر)."""
    location = ""
    try:
        # X/Twitter: حقل location في البروفايل
        if platform in ("x", "twitter"):
            patterns = [
                r'"location"\s*:\s*"([^"]{2,100})"',
                r'data-testid="UserLocation"[^>]*>([^<]+)<',
            ]
            for p in patterns:
                m = re.search(p, html)
                if m:
                    val = m.group(1).strip()
                    # تجاهل القيم الفارغة أو رموز الدولة الافتراضية
                    if val and val.lower() not in ("us", "en", "und"):
                        location = val
                        break

        # Instagram: business_address
        elif platform == "instagram":
            m = re.search(r'"business_address_json"\s*:\s*"([^"]+)"', html)
            if m:
                location = m.group(1).replace("\\", "")

        # GitHub: حقل homeLocation
        elif platform == "github":
            tag = soup.find("li", {"itemprop": "homeLocation"})
            if tag:
                location = tag.get_text(strip=True)

        # LinkedIn: addressLocality
        elif platform == "linkedin":
            m = re.search(r'"addressLocality":"([^"]+)"', html) or \
                re.search(r'"locality":"([^"]+)"', html)
            if m:
                location = m.group(1)

        # Facebook: current_city/hometown
        elif platform == "facebook":
            m = re.search(r'"current_city":\s*\{[^}]*"text":"([^"]+)"', html) or \
                re.search(r'"hometown":\s*\{[^}]*"text":"([^"]+)"', html)
            if m:
                location = m.group(1)

        # ⚠️ TikTok و YouTube: لا نأخذ region لأنه يعكس منطقة السيرفر/الزائر
        # نتجاهلهما تماماً ونعتمد على البايو فقط
    except Exception:
        pass
    return location.strip()


# ============ استخراج اللغة ============
def extract_language(platform: str, html: str, soup: BeautifulSoup):
    """استخراج اللغة - مع تجاهل اللغة الافتراضية للسيرفر."""
    try:
        # ⚠️ تجاهل lang="en" من HTML tag للمنصات التي تعطي لغة موحدة (TikTok, YouTube, Twitter)
        # لأن هذه لغة الواجهة من جانب السيرفر، وليست لغة المستخدم
        if platform in ("tiktok", "youtube", "x", "twitter", "instagram"):
            # ابحث في بيانات المستخدم بدلاً من html lang
            m = re.search(r'"language":"([a-z]{2,5})"', html) or \
                re.search(r'"user_language":"([a-z]{2,5})"', html) or \
                re.search(r'"profile_language":"([a-z]{2,5})"', html)
            if m:
                return m.group(1)
            return ""  # لا نأخذ اللغة الافتراضية

        # للمنصات الأخرى يمكن أخذ html lang
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            return html_tag.get("lang")
    except Exception:
        pass
    return ""


# ============ السحب الرئيسي ============
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_account_info(platform: str, username: str):
    result = {
        "platform": platform, "username": username, "permanent_id": "",
        "profile_url": "", "display_name": "", "bio": "", "followers": "",
        "verified": False, "profile_image": "",
        "location_text": "",          # الموقع المُعلن من المستخدم
        "country_code": "",           # كود الدولة المستنتج
        "country_name_ar": "",
        "country_flag": "",
        "country_source": "",         # مصدر الكشف: declared/bio/name/dialect
        "country_confidence": 0,      # درجة الثقة 0-100
        "language": "", "server_country": "", "server_ip": "",
        "status": "❌ فشل", "error": "",
    }

    if platform not in PLATFORMS:
        result["error"] = "منصة غير مدعومة"
        return result

    profile_url = PLATFORMS[platform]["url"].format(username)
    host = PLATFORMS[platform]["host"]
    result["profile_url"] = profile_url

    geo = get_ip_geolocation(host)
    result["server_country"] = geo.get("server_country", "")
    result["server_ip"] = geo.get("ip", "")

    try:
        # طلب الصفحة مع لغة عربية لتحسين فرص اكتشاف المحتوى العربي
        custom_headers = HEADERS.copy()
        custom_headers["Accept-Language"] = "ar,en;q=0.5"
        response = requests.get(profile_url, headers=custom_headers, timeout=10, allow_redirects=True)

        if response.status_code == 404:
            result["error"] = "الحساب غير موجود"
            return result
        if response.status_code != 200:
            result["error"] = f"كود الاستجابة: {response.status_code}"
            result["status"] = "⚠️ الرابط فقط"
            return result

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        def get_meta(prop):
            tag = soup.find("meta", {"property": prop}) or soup.find("meta", {"name": prop})
            return tag.get("content", "") if tag else ""

        result["display_name"] = (
            get_meta("og:title") or get_meta("twitter:title")
            or (soup.title.string if soup.title else "")
        ).strip()

        result["bio"] = (
            get_meta("og:description") or get_meta("description") or get_meta("twitter:description")
        ).strip()

        result["profile_image"] = get_meta("og:image") or get_meta("twitter:image")
        result["permanent_id"] = extract_permanent_id(platform, username, html, soup)

        # ===== الموقع المُعلن من المستخدم =====
        location_text = extract_user_declared_location(platform, html, soup)
        result["location_text"] = location_text

        result["language"] = extract_language(platform, html, soup)

        # ===== استنتاج الدولة بطبقات متعددة مع تتبع المصدر والثقة =====
        country_code, confidence, source = None, 0, ""

        # الطبقة 1: الموقع المُعلن (الأولوية القصوى)
        if location_text:
            cc, conf = detect_country_from_text(location_text)
            if cc:
                country_code, confidence, source = cc, max(conf, 90), "📍 معلن"

        # الطبقة 2: البايو
        if not country_code and result["bio"]:
            cc, conf = detect_country_from_text(result["bio"])
            if cc:
                country_code, confidence, source = cc, conf, "📝 بايو"

        # الطبقة 3: الاسم الظاهر
        if not country_code and result["display_name"]:
            cc, conf = detect_country_from_text(result["display_name"])
            if cc:
                country_code, confidence, source = cc, max(conf - 10, 30), "👤 الاسم"

        # الطبقة 4: اسم المستخدم نفسه
        if not country_code:
            cc, conf = detect_country_from_text(username)
            if cc:
                country_code, confidence, source = cc, max(conf - 20, 25), "🔤 يوزر"

        if country_code:
            result["country_code"] = country_code
            result["country_name_ar"] = COUNTRY_AR.get(country_code, "")
            result["country_flag"] = COUNTRY_FLAGS.get(country_code, "")
            result["country_source"] = source
            result["country_confidence"] = confidence

        # المتابعون
        followers_match = re.search(
            r"([\d,.]+\s*[KMB]?)\s*(?:Followers|متابع|subscribers|مشترك|fans)",
            result["bio"], re.IGNORECASE,
        )
        if followers_match:
            result["followers"] = followers_match.group(1).strip()

        # التوثيق
        if '"is_verified":true' in html.lower() or '"verified":true' in html.lower():
            result["verified"] = True

        if result["display_name"] or result["bio"] or result["permanent_id"]:
            result["status"] = "✅ نجح"
        else:
            result["status"] = "⚠️ معلومات محدودة"

    except requests.Timeout:
        result["error"] = "انتهت مهلة الاتصال"
    except requests.ConnectionError:
        result["error"] = "خطأ في الاتصال"
    except Exception as e:
        result["error"] = str(e)[:100]

    return result


def fetch_batch(entries, max_workers=10, progress_callback=None):
    results = []
    total = len(entries)
    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_account_info, e["platform"], e["username"]): e for e in entries}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                entry = futures[future]
                results.append({
                    "platform": entry["platform"], "username": entry["username"],
                    "status": "❌ فشل", "error": str(e)[:100],
                    "permanent_id": "", "profile_url": "", "display_name": "", "bio": "",
                    "followers": "", "verified": False, "profile_image": "",
                    "location_text": "", "country_code": "", "country_name_ar": "",
                    "country_flag": "", "country_source": "", "country_confidence": 0,
                    "language": "", "server_country": "", "server_ip": "",
                })
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
    return results


def create_sample_excel():
    sample_data = {
        "platform": ["x", "instagram", "youtube", "tiktok", "github", "twitch"],
        "username": ["nasa", "natgeo", "MrBeast", "khaby.lame", "torvalds", "shroud"],
    }
    df = pd.DataFrame(sample_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="accounts")
    return output.getvalue()


def results_to_excel(results):
    df = pd.DataFrame(results)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="results")
    return output.getvalue()


# ============ الواجهة ============
st.markdown(
    """
    <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h1 style="color: white; margin: 0;">🌐 مولد معلومات حسابات التواصل الاجتماعي</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.95;">
            🆔 الـ ID الدائم • 🌍 كشف الدولة بالذكاء • 14+ منصة • 300+ حساب
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============ الشريط الجانبي ============
with st.sidebar:
    st.markdown("### ⚙️ الإعدادات")
    max_workers = st.slider("عدد العمليات المتوازية", 1, 20, 10)

    min_confidence = st.slider(
        "🎯 الحد الأدنى لثقة كشف الدولة",
        0, 100, 30,
        help="إذا كانت الثقة أقل من هذا الرقم، لن تُعرض الدولة",
    )

    st.markdown("---")
    st.markdown("### 🌍 طبقات كشف الدولة")
    st.markdown("""
    **بأولوية تنازلية:**
    1. 📍 **معلن**: المستخدم كتب مدينته (90%+)
    2. 📝 **بايو**: كلمات في الوصف (60-85%)
    3. 👤 **الاسم**: المدينة في اسم الحساب (30-75%)
    4. 🔤 **يوزر**: في اسم المستخدم نفسه (25-65%)

    💡 **لا نستخدم region من السيرفر** لأنه يُظهر US دائماً!
    """)

    st.markdown("---")
    st.markdown("### 📊 المنصات المدعومة")
    cols = st.columns(2)
    for i, (key, info) in enumerate(PLATFORMS.items()):
        cols[i % 2].markdown(f"{info['icon']} **{info['name']}**")

    st.markdown("---")
    st.download_button(
        "⬇️ تحميل ملف Excel نموذجي",
        data=create_sample_excel(),
        file_name="sample_accounts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.caption("💡 يستخدم التطبيق scraping للبيانات العامة فقط.")

# ============ التبويبات ============
tab1, tab2, tab3 = st.tabs(["📝 الإدخال اليدوي", "📂 رفع ملف Excel", "ℹ️ التعليمات"])

with tab1:
    st.markdown("### 📝 الإدخال اليدوي - يدعم أكثر من 300 حساب")
    st.markdown(
        """
        <div class="info-box">
        <strong>الصيغ المدعومة:</strong> 
        <code>platform,username</code> • <code>platform:username</code> • 
        <code>platform username</code> • <code>https://x.com/nasa</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_text = """# الصق ما يصل إلى 300+ حساب أو رابط هنا
x,nasa
instagram,natgeo
youtube:MrBeast
https://www.tiktok.com/@khaby.lame
github,torvalds
twitch,shroud
"""
    col_input, col_actions = st.columns([4, 1])
    with col_input:
        manual_input = st.text_area(
            "الصق الحسابات أو الروابط:",
            value=default_text, height=400, key="manual_input",
        )
    with col_actions:
        st.markdown("#### 🛠️ أدوات")
        if st.button("🔍 معاينة", use_container_width=True):
            st.session_state["preview_entries"] = parse_manual_input(manual_input)
        if st.button("🧹 مسح", use_container_width=True):
            st.session_state["manual_input"] = ""
            st.rerun()
        live_count = len([l for l in manual_input.splitlines() if l.strip() and not l.strip().startswith("#")])
        st.metric("📊 الأسطر النشطة", live_count)

    if "preview_entries" in st.session_state:
        entries = st.session_state["preview_entries"]
        if entries:
            st.success(f"✅ تم التعرف على **{len(entries)}** حساب")
            with st.expander(f"عرض الحسابات ({len(entries)})"):
                st.dataframe(pd.DataFrame(entries), use_container_width=True, height=300)
        else:
            st.warning("⚠️ لم يتم التعرف على أي حساب صحيح.")

    st.markdown("---")
    if st.button("🚀 ابدأ سحب المعلومات", type="primary", use_container_width=True, key="manual_fetch"):
        entries = parse_manual_input(manual_input)
        if not entries:
            st.error("❌ لم يتم العثور على حسابات صحيحة.")
        else:
            st.info(f"🔄 جارٍ سحب معلومات **{len(entries)}** حساب...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            start_time = time.time()

            def update_progress(done, total):
                progress_bar.progress(done / total)
                status_text.text(f"⏳ تمت معالجة {done}/{total} حساب...")

            results = fetch_batch(entries, max_workers=max_workers, progress_callback=update_progress)
            elapsed = time.time() - start_time
            progress_bar.empty()
            status_text.empty()
            st.session_state["results"] = results
            st.session_state["elapsed"] = elapsed
            st.session_state["min_confidence"] = min_confidence
            st.success(f"✅ تم الانتهاء في **{elapsed:.1f}** ثانية!")

with tab2:
    st.markdown("### 📂 رفع ملف Excel")
    uploaded = st.file_uploader("اختر ملف Excel (.xlsx)", type=["xlsx", "xls", "csv"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns = [c.lower().strip() for c in df.columns]
            if "platform" not in df.columns or "username" not in df.columns:
                st.error("❌ الملف يجب أن يحتوي على `platform` و `username`")
            else:
                df = df[["platform", "username"]].dropna()
                df["platform"] = df["platform"].astype(str).str.lower().str.strip()
                df["username"] = df["username"].astype(str).str.replace("@", "").str.strip()
                st.success(f"✅ تم تحميل **{len(df)}** حساب")
                with st.expander("معاينة"):
                    st.dataframe(df.head(20), use_container_width=True)
                if st.button("🚀 ابدأ", type="primary", use_container_width=True, key="excel_fetch"):
                    entries = df.to_dict("records")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    start_time = time.time()

                    def update_progress(done, total):
                        progress_bar.progress(done / total)
                        status_text.text(f"⏳ {done}/{total}")

                    results = fetch_batch(entries, max_workers=max_workers, progress_callback=update_progress)
                    elapsed = time.time() - start_time
                    progress_bar.empty()
                    status_text.empty()
                    st.session_state["results"] = results
                    st.session_state["elapsed"] = elapsed
                    st.session_state["min_confidence"] = min_confidence
                    st.success(f"✅ تم في **{elapsed:.1f}** ثانية!")
        except Exception as e:
            st.error(f"❌ خطأ: {e}")

with tab3:
    st.markdown("""
    ### ℹ️ تحسينات الإصدار v3 - كشف الدولة الذكي

    #### 🐛 المشكلة في الإصدار السابق
    كان التطبيق يعرض **"الولايات المتحدة"** لكل حسابات TikTok و YouTube لأنه كان يقرأ
    `region` من بيانات السيرفر بدلاً من بيانات المستخدم.

    #### ✅ الحل في v3
    1. ❌ **تجاهلنا** كود `region` و `country` القادم من السيرفر
    2. ✅ نعتمد فقط على **حقول البروفايل التي يكتبها المستخدم**:
       - X/Twitter: `location`
       - Instagram: `business_address`
       - GitHub: `homeLocation`
       - LinkedIn: `addressLocality`
       - Facebook: `current_city`
    3. ✅ **تحليل البايو والاسم** بحثاً عن أكثر من **400 مدينة/دولة** بالعربية والإنجليزية
    4. ✅ **كشف اللهجات العربية** للتمييز بين السعودية/مصر/الإمارات/الكويت/المغرب/الجزائر/العراق
    5. ✅ **مقياس ثقة 0-100%** لكل اكتشاف + **مصدر الكشف**

    #### 📊 المصادر مرتبة بالأولوية والثقة
    | الطبقة | المصدر | الثقة |
    |--------|--------|-------|
    | 1 | 📍 الموقع المُعلن صراحة | 90-95% |
    | 2 | 📝 من البايو | 40-85% |
    | 3 | 👤 من الاسم الظاهر | 30-75% |
    | 4 | 🔤 من اسم المستخدم | 25-65% |

    #### ⚠️ ملاحظات صادقة
    - **TikTok** لا يكشف موقع المستخدم العادي في HTML العام، فالاكتشاف يعتمد على ما كتبه في البايو فقط.
    - **Instagram & Facebook** يحجبان معظم البيانات للزوار غير المسجلين.
    - **Twitter/X** الحسابات الخاصة قد لا تظهر بياناتها كاملة.
    - **حسابات بدون موقع مُعلن** ستظهر بدون دولة (وهذا أصدق من تخمين خاطئ).

    #### 💡 نصيحة
    استخدم **شريط الثقة الجانبي** لتصفية النتائج حسب درجة موثوقية الكشف.
    """)

# ============ عرض النتائج ============
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    df_results = pd.DataFrame(results)
    min_conf = st.session_state.get("min_confidence", 30)

    # تطبيق فلتر الثقة على عرض الدولة
    df_display = df_results.copy()
    df_display.loc[df_display["country_confidence"] < min_conf, ["country_code", "country_name_ar", "country_flag", "country_source"]] = ""

    st.markdown("---")
    st.markdown("## 📊 النتائج")

    total = len(results)
    success = sum(1 for r in results if r["status"] == "✅ نجح")
    with_id = sum(1 for r in results if r.get("permanent_id"))
    with_country = sum(1 for _, r in df_display.iterrows() if r.get("country_code"))
    failed = sum(1 for r in results if r["status"] == "❌ فشل")
    verified = sum(1 for r in results if r.get("verified"))

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("📋 الإجمالي", total)
    col2.metric("✅ ناجح", success)
    col3.metric("🆔 ID دائم", with_id)
    col4.metric("🌍 دولة", with_country, delta=f"ثقة ≥{min_conf}%")
    col5.metric("✓ موثّق", verified)
    col6.metric("❌ فشل", failed)

    if "elapsed" in st.session_state:
        st.caption(f"⏱️ زمن المعالجة: {st.session_state['elapsed']:.1f} ثانية")

    # توزيع الدول (مع فلتر الثقة)
    countries_found = df_display[df_display["country_code"] != ""]
    if not countries_found.empty:
        st.markdown(f"#### 🌍 توزيع الدول (بثقة ≥ {min_conf}%)")
        country_counts = countries_found.apply(
            lambda r: f"{r['country_flag']} {r['country_name_ar']}", axis=1
        ).value_counts()
        col_chart, col_list = st.columns([2, 1])
        with col_chart:
            st.bar_chart(country_counts)
        with col_list:
            st.markdown("**أكثر الدول ظهوراً:**")
            for country, count in country_counts.head(10).items():
                st.markdown(f"- {country}: **{count}**")
    else:
        st.markdown(
            f'<div class="warn-box">⚠️ لم يتم اكتشاف دول بثقة ≥ {min_conf}%. '
            f'جرّب خفض الحد الأدنى من الشريط الجانبي.</div>',
            unsafe_allow_html=True,
        )

    # فلترة
    st.markdown("#### 🔍 فلترة النتائج")
    col_f1, col_f2, col_f3 = st.columns(3)
    status_filter = col_f1.multiselect(
        "حسب الحالة", df_display["status"].unique().tolist(),
        default=df_display["status"].unique().tolist(),
    )
    platform_filter = col_f2.multiselect(
        "حسب المنصة", df_display["platform"].unique().tolist(),
        default=df_display["platform"].unique().tolist(),
    )
    countries_options = [c for c in df_display["country_code"].unique().tolist() if c]
    country_filter = col_f3.multiselect(
        "حسب الدولة", countries_options, default=countries_options,
    )

    filtered = df_display[
        df_display["status"].isin(status_filter) &
        df_display["platform"].isin(platform_filter) &
        (df_display["country_code"].isin(country_filter) | (df_display["country_code"] == ""))
    ]

    # جدول النتائج
    st.markdown(f"#### 📋 جدول النتائج ({len(filtered)} سجل)")
    display_cols = [
        "platform", "username", "permanent_id", "display_name",
        "country_flag", "country_name_ar", "country_source", "country_confidence",
        "location_text", "language", "followers", "verified", "status", "profile_url",
    ]
    display_cols = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[display_cols], use_container_width=True, height=400,
        column_config={
            "profile_url": st.column_config.LinkColumn("🔗 الرابط"),
            "verified": st.column_config.CheckboxColumn("✓"),
            "permanent_id": st.column_config.TextColumn("🆔 ID الدائم", width="medium"),
            "country_flag": st.column_config.TextColumn("🚩", width="small"),
            "country_name_ar": st.column_config.TextColumn("الدولة", width="small"),
            "country_source": st.column_config.TextColumn("مصدر الكشف"),
            "country_confidence": st.column_config.ProgressColumn(
                "الثقة %", min_value=0, max_value=100, format="%d%%",
            ),
            "location_text": st.column_config.TextColumn("📍 الموقع المُعلن"),
            "language": st.column_config.TextColumn("🌐 اللغة", width="small"),
        },
    )

    # تصدير
    st.markdown("#### 📥 تصدير النتائج")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    col_e1, col_e2, col_e3 = st.columns(3)

    csv_data = filtered.to_csv(index=False).encode("utf-8-sig")
    col_e1.download_button("⬇️ CSV", data=csv_data,
                           file_name=f"social_results_{timestamp}.csv",
                           mime="text/csv", use_container_width=True)

    json_data = filtered.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
    col_e2.download_button("⬇️ JSON", data=json_data,
                           file_name=f"social_results_{timestamp}.json",
                           mime="application/json", use_container_width=True)

    excel_data = results_to_excel(filtered.to_dict("records"))
    col_e3.download_button("⬇️ Excel", data=excel_data,
                           file_name=f"social_results_{timestamp}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

    # بطاقات
    successful = [r for r in filtered.to_dict("records") if r["status"] in ("✅ نجح", "⚠️ معلومات محدودة")][:12]
    if successful:
        st.markdown("#### 🎴 بطاقات الحسابات (أول 12)")
        cols = st.columns(3)
        for i, r in enumerate(successful):
            with cols[i % 3]:
                platform_info = PLATFORMS.get(r["platform"], {"icon": "🌐"})
                with st.container(border=True):
                    if r.get("profile_image"):
                        try:
                            st.image(r["profile_image"], width=80)
                        except Exception:
                            pass
                    flag = r.get("country_flag", "")
                    st.markdown(f"**{platform_info['icon']} {r.get('display_name') or r['username']}** {flag}")
                    st.caption(f"@{r['username']} • {r['platform']}")
                    if r.get("permanent_id"):
                        st.caption(f"🆔 `{str(r['permanent_id'])[:30]}`")
                    if r.get("country_name_ar"):
                        conf = r.get("country_confidence", 0)
                        src = r.get("country_source", "")
                        st.caption(f"🌍 {r['country_name_ar']} ({src} • ثقة {conf}%)")
                    if r.get("location_text"):
                        st.caption(f"📍 {r['location_text'][:50]}")
                    if r.get("bio"):
                        st.caption(r["bio"][:100] + ("..." if len(r["bio"]) > 100 else ""))
                    if r.get("verified"):
                        st.caption("✓ موثّق")
                    st.markdown(f"[🔗 فتح الحساب]({r['profile_url']})")
