"""
🦅 بَصِير v1.9.7 - النسخة المستقلة (Standalone)
═══════════════════════════════════════════════════════════════
التحديث v1.9.7:
  🔧 Pattern BIO الصحيح المكتشف من البيانات الخام
  🔧 50+ مشهور مرتبط بمنطقة افتراضية
  🔧 إزالة المشاهير غير المفهرسين (5 حسابات)
  🔧 البحث في nickname + username كحلّ احتياطي للمنطقة
  ✅ قاعدة 1112+ منطقة عالمياً (69 دولة)
═══════════════════════════════════════════════════════════════
"""
import streamlit as st
import requests
import re
import json
import time
import random
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent / 'data'))
from regions_database import REGIONS_DATABASE, lookup_region, get_total_regions, get_countries_count
from capitals_database import lookup_capital, get_capitals_count

VERSION = "v2.0.0"

# ═══════════════════════════════════════════════════════════════
# 🎨 إعدادات الصفحة (RTL + خطوط عربية)
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=f"بَصِير {VERSION} | مولّد معلومات TikTok",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# 🌐 بروكسيات
# ═══════════════════════════════════════════════════════════════
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
]

PROXY_CHAIN = [
    {'name': 'jina', 'url': 'https://r.jina.ai/', 'timeout': 15},
    {'name': 'corsproxy', 'url': 'https://corsproxy.io/?', 'timeout': 12},
    {'name': 'allorigins', 'url': 'https://api.allorigins.win/raw?url=', 'timeout': 15},
]

# ═══════════════════════════════════════════════════════════════
# 🎯 Patterns - v1.9.7: Pattern BIO الصحيح المكتشف
# ═══════════════════════════════════════════════════════════════
PATTERNS = {
    'country_flag':    r'(?:🇺🇸|🇬🇧|🇰🇷|🇯🇵|🇨🇳|🇮🇳|🇧🇷|🇿🇦|🇦🇺|🇪🇬|🇸🇦|🇦🇪|🇰🇼|🇶🇦|🇧🇭|🇴🇲|🇯🇴|🇱🇧|🇮🇶|🇾🇪|🇵🇸|🇲🇦|🇩🇿|🇹🇳|🇱🇾|🇸🇩|🇸🇴|🇹🇷|🇮🇷|🇮🇹|🇫🇷|🇩🇪|🇪🇸|🇳🇱|🇷🇺|🇨🇦|🇲🇽|🇦🇷|🇨🇴|🇨🇱|🇵🇪|🇻🇪|🇳🇬|🇰🇪|🇪🇹|🇬🇭|🇹🇭|🇻🇳|🇮🇩|🇲🇾|🇵🇭|🇸🇬|🇵🇰|🇧🇩|🇱🇰|🇳🇿|🇵🇹|🇵🇷|🇹🇿|🇹🇼|🇭🇰)([A-Za-z][A-Za-z\s&\.\(\)\']+?)(?:\n|🌐)',
    'country_globe':   r'🌍\s*([A-Za-z][A-Za-z\s&\.\(\)\']+?)(?:\n|🌐|<|$)',
    'language':        r'🌐([a-zA-Z]{2,7})',
    'followers':       r'([\d,]+)\s*👥\s*Followers|👥 Followers\s*\n*([\d,]+)',
    'following':       r'([\d,]+)\s*➕\s*Following|➕ Following\s*\n*([\d,]+)',
    'hearts':          r'([\d,]+)\s*❤️\s*Hearts|❤️ Hearts\s*\n*([\d,]+)',
    'videos':          r'([\d,]+)\s*🎬\s*Videos|🎬 Videos\s*\n*([\d,]+)',
    'friends':         r'([\d,]+)\s*👫\s*Friends|👫 Friends\s*\n*([\d,]+)',
    'user_id':         r'User ID:[*\s`]*(\d+)',
    'sec_uid':         r'SecUID:[*\s`]*([A-Za-z0-9_-]+)',
    'created':         r'Account Created:[*\s]*([^\n]+)',
    'nickname':        r'##\s*([^\n#]+)\n\n@',
    'avatar':          r'!\[Image[^\]]*\]\((https://[^)]+)\)',
}

# 🆕 v1.9.7: 3 أنماط بديلة لاستخراج BIO
BIO_PATTERNS = [
    # نمط 1: بعد Download Videos مباشرة (الأكثر شيوعاً)
    r'\[📥 Download Videos\][^\n]*\n+([^\n\[]{2,300}?)(?:\n+\[|\n+###|$)',
    # نمط 2: About:** صريح
    r'\*\*📝 About:\*\*\s*([^\n*]+)',
    r'About:\*\*\s*([^\n*]+)',
    # نمط 3: بعد 🌐 lang ثم سطر فارغ ثم نص
    r'🌐[a-z]{2,7}\n+(?:\[[^\]]+\][^\n]*\n+)+([^\n\[]{2,300}?)(?:\n+\[|\n+###|$)',
]

# ═══════════════════════════════════════════════════════════════
# 🌟 قاعدة المشاهير المُحدَّثة v1.9.7 (50+ مع مناطق افتراضية)
# تمت إزالة 5 مشاهير غير مفهرسين في TikMatrix
# ═══════════════════════════════════════════════════════════════
CELEBRITIES = {
    # 🇮🇹 إيطاليا
    "khaby.lame":           {"country": "Italy",         "flag": "🇮🇹", "name": "Khabane Lame", "region": "ميلانو"},
    # 🇰🇼 الكويت
    "aboflah":              {"country": "Kuwait",        "flag": "🇰🇼", "name": "AboFlah", "region": "مدينة الكويت"},
    "shougalhady":          {"country": "Kuwait",        "flag": "🇰🇼", "name": "Shoug Alhady", "region": "مدينة الكويت"},
    "hayaalshuaibi":        {"country": "Kuwait",        "flag": "🇰🇼", "name": "Haya Alshuaibi", "region": "مدينة الكويت"},
    # 🇪🇬 مصر
    "amrdiab":              {"country": "Egypt",         "flag": "🇪🇬", "name": "Amr Diab", "region": "القاهرة"},
    "mohamedramadanws":     {"country": "Egypt",         "flag": "🇪🇬", "name": "Mohamed Ramadan", "region": "القاهرة"},
    # 🇶🇦 قطر
    "aljazeera":            {"country": "Qatar",         "flag": "🇶🇦", "name": "Al Jazeera", "region": "الدوحة"},
    # 🇰🇷 كوريا الجنوبية
    "blackpinkofficial":    {"country": "South Korea",   "flag": "🇰🇷", "name": "BLACKPINK", "region": "سيول"},
    "bts_official_bighit":  {"country": "South Korea",   "flag": "🇰🇷", "name": "BTS", "region": "سيول"},
    "newjeans_official":    {"country": "South Korea",   "flag": "🇰🇷", "name": "NewJeans", "region": "سيول"},
    "twice_tiktok_official":{"country": "South Korea",   "flag": "🇰🇷", "name": "TWICE", "region": "سيول"},
    "ive_official":         {"country": "South Korea",   "flag": "🇰🇷", "name": "IVE", "region": "سيول"},
    "lesserafim_official":  {"country": "South Korea",   "flag": "🇰🇷", "name": "LE SSERAFIM", "region": "سيول"},
    "straykids":            {"country": "South Korea",   "flag": "🇰🇷", "name": "Stray Kids", "region": "سيول"},
    "itzofficial":          {"country": "South Korea",   "flag": "🇰🇷", "name": "ITZY", "region": "سيول"},
    # 🇵🇭 الفلبين
    "bellapoarch":          {"country": "Philippines",   "flag": "🇵🇭", "name": "Bella Poarch", "region": "مانيلا"},
    # 🇹🇭 تايلاند
    "lalisa_manobal":       {"country": "Thailand",      "flag": "🇹🇭", "name": "Lisa (BLACKPINK)", "region": "بانكوك"},
    # 🇮🇩 إندونيسيا
    "raffinagita1717":      {"country": "Indonesia",     "flag": "🇮🇩", "name": "Raffi Nagita", "region": "جاكرتا"},
    # 🇮🇳 الهند
    "priyankachopra":       {"country": "India",         "flag": "🇮🇳", "name": "Priyanka Chopra", "region": "مومباي"},
    "viratkohli":           {"country": "India",         "flag": "🇮🇳", "name": "Virat Kohli", "region": "مومباي"},
    "deepikapadukone":      {"country": "India",         "flag": "🇮🇳", "name": "Deepika Padukone", "region": "مومباي"},
    "alia.bhatt":           {"country": "India",         "flag": "🇮🇳", "name": "Alia Bhatt", "region": "مومباي"},
    # 🇵🇰 باكستان
    "atifaslam":            {"country": "Pakistan",      "flag": "🇵🇰", "name": "Atif Aslam", "region": "كراتشي"},
    # 🇻🇳 فيتنام
    "son.tung.mtp":         {"country": "Vietnam",       "flag": "🇻🇳", "name": "Sơn Tùng M-TP", "region": "هو تشي مينه"},
    # 🇵🇹 البرتغال
    "cristiano":            {"country": "Portugal",      "flag": "🇵🇹", "name": "Cristiano Ronaldo", "region": "لشبونة"},
    # 🇩🇪 ألمانيا
    "youness_zarou":        {"country": "Germany",       "flag": "🇩🇪", "name": "Younes Zarou", "region": "فرانكفورت"},
    "twincoach":            {"country": "Germany",       "flag": "🇩🇪", "name": "TwinCoach", "region": "برلين"},
    # 🇲🇦 المغرب
    "younesnaffaa":         {"country": "Morocco",       "flag": "🇲🇦", "name": "Younes Naffa", "region": "الدار البيضاء"},
    # 🇺🇸 الولايات المتحدة
    "mrbeast":              {"country": "United States", "flag": "🇺🇸", "name": "MrBeast", "region": "نيويورك"},
    "charlidamelio":        {"country": "United States", "flag": "🇺🇸", "name": "Charli D'Amelio", "region": "لوس أنجلوس"},
    "kingjames":            {"country": "United States", "flag": "🇺🇸", "name": "LeBron James", "region": "لوس أنجلوس"},
    "therock":              {"country": "United States", "flag": "🇺🇸", "name": "Dwayne Johnson", "region": "لوس أنجلوس"},
    "selenagomez":          {"country": "United States", "flag": "🇺🇸", "name": "Selena Gomez", "region": "لوس أنجلوس"},
    "taylorswift":          {"country": "United States", "flag": "🇺🇸", "name": "Taylor Swift", "region": "ناشفيل"},
    "kimkardashian":        {"country": "United States", "flag": "🇺🇸", "name": "Kim Kardashian", "region": "لوس أنجلوس"},
    "kyliejenner":          {"country": "United States", "flag": "🇺🇸", "name": "Kylie Jenner", "region": "لوس أنجلوس"},
    "billieeilish":         {"country": "United States", "flag": "🇺🇸", "name": "Billie Eilish", "region": "لوس أنجلوس"},
    "arianagrande":         {"country": "United States", "flag": "🇺🇸", "name": "Ariana Grande", "region": "لوس أنجلوس"},
    "zendaya":              {"country": "United States", "flag": "🇺🇸", "name": "Zendaya", "region": "لوس أنجلوس"},
    "addisonre":            {"country": "United States", "flag": "🇺🇸", "name": "Addison Rae", "region": "لوس أنجلوس"},
    "willsmith":            {"country": "United States", "flag": "🇺🇸", "name": "Will Smith", "region": "لوس أنجلوس"},
    # 🇨🇦 كندا
    "drake":                {"country": "Canada",        "flag": "🇨🇦", "name": "Drake", "region": "تورنتو"},
    "shawnmendes":          {"country": "Canada",        "flag": "🇨🇦", "name": "Shawn Mendes", "region": "تورنتو"},
    "justinbieber":         {"country": "Canada",        "flag": "🇨🇦", "name": "Justin Bieber", "region": "تورنتو"},
    # 🇨🇴 كولومبيا
    "shakira":              {"country": "Colombia",      "flag": "🇨🇴", "name": "Shakira", "region": "بارانكويلا"},
    "jbalvin":              {"country": "Colombia",      "flag": "🇨🇴", "name": "J Balvin", "region": "ميديلين"},
    "karolg":               {"country": "Colombia",      "flag": "🇨🇴", "name": "Karol G", "region": "ميديلين"},
    # 🇦🇷 الأرجنتين
    "messi":                {"country": "Argentina",     "flag": "🇦🇷", "name": "Lionel Messi", "region": "بوينس آيرس"},
    "tini":                 {"country": "Argentina",     "flag": "🇦🇷", "name": "TINI", "region": "بوينس آيرس"},
    # 🇧🇷 البرازيل
    "anitta":               {"country": "Brazil",        "flag": "🇧🇷", "name": "Anitta", "region": "ريو دي جانيرو"},
    "neymarjr":             {"country": "Brazil",        "flag": "🇧🇷", "name": "Neymar Jr", "region": "ساو باولو"},
    # 🇻🇪 فنزويلا
    "lelepons":             {"country": "Venezuela",     "flag": "🇻🇪", "name": "Lele Pons", "region": "كاراكاس"},
    # 🇵🇷 بورتو ريكو
    "badbunny":             {"country": "Puerto Rico",   "flag": "🇵🇷", "name": "Bad Bunny", "region": "بورتو ريكو"},
    # 🇳🇬 نيجيريا
    "wizkidayo":            {"country": "Nigeria",       "flag": "🇳🇬", "name": "Wizkid", "region": "لاغوس"},
    "burnaboygram":         {"country": "Nigeria",       "flag": "🇳🇬", "name": "Burna Boy", "region": "لاغوس"},
    "davidoofficial":       {"country": "Nigeria",       "flag": "🇳🇬", "name": "Davido", "region": "لاغوس"},
    "tiwasavage":           {"country": "Nigeria",       "flag": "🇳🇬", "name": "Tiwa Savage", "region": "لاغوس"},
    # 🇿🇦 جنوب أفريقيا
    "trevornoah":           {"country": "South Africa",  "flag": "🇿🇦", "name": "Trevor Noah", "region": "جوهانسبرغ"},
    "blackcoffeeofficial":  {"country": "South Africa",  "flag": "🇿🇦", "name": "Black Coffee", "region": "جوهانسبرغ"},
    # 🇹🇿 تنزانيا
    "diamondplatnumz":      {"country": "Tanzania",      "flag": "🇹🇿", "name": "Diamond Platnumz", "region": "دار السلام"},
    # 🇦🇺 أستراليا
    "chrishemsworth":       {"country": "Australia",     "flag": "🇦🇺", "name": "Chris Hemsworth", "region": "سيدني"},
}

# ═══════════════════════════════════════════════════════════════
# 🔒 قاعدة التحقق المحلي
# ═══════════════════════════════════════════════════════════════
LOCAL_VERIFIED_DB = {
    "zahranabill1": {
        "country": "Kuwait", "flag": "🇰🇼", "name": "Zahra Nabill",
        "region": "مدينة الكويت",
        "verified_by": "اللجنة الفنية - 2026-06-05",
        "note": "حساب كويتي صغير، تحقق يدوي",
    },
}

# ═══════════════════════════════════════════════════════════════
# 🗣️ خرائط التصحيح
# ═══════════════════════════════════════════════════════════════
LANGUAGE_TO_COUNTRY = {
    'ar': ('Arab Region', ['Saudi Arabia', 'United Arab Emirates', 'Egypt', 'Kuwait', 'Qatar', 'Bahrain', 'Oman', 'Jordan', 'Lebanon', 'Iraq', 'Yemen', 'Palestine', 'Morocco', 'Algeria', 'Tunisia', 'Libya', 'Sudan', 'Somalia']),
    'ko': ('South Korea', ['South Korea', 'Korea']),
    'ja': ('Japan', ['Japan']),
    'zh': ('China', ['China', 'Taiwan', 'Hong Kong', 'Singapore']),
    'th': ('Thailand', ['Thailand']),
    'vi': ('Vietnam', ['Vietnam']),
    'id': ('Indonesia', ['Indonesia']),
    'tr': ('Turkey', ['Turkey']),
    'fa': ('Iran', ['Iran']),
    'hi': ('India', ['India']),
    'ur': ('Pakistan', ['Pakistan']),
    'pt': ('Brazil', ['Brazil', 'Portugal']),
    'es': ('Spain', ['Spain', 'Mexico', 'Argentina', 'Colombia', 'Chile', 'Peru', 'Venezuela']),
    'fr': ('France', ['France', 'Belgium', 'Canada', 'Switzerland']),
    'de': ('Germany', ['Germany', 'Austria', 'Switzerland']),
    'it': ('Italy', ['Italy']),
    'ru': ('Russia', ['Russia', 'Kazakhstan']),
    'en': ('United States', ['United States', 'United Kingdom', 'Canada', 'Australia', 'New Zealand']),
}

USERNAME_KEYWORDS = {
    'japan': 'Japan', 'tokyo': 'Japan', 'osaka': 'Japan',
    'korea': 'South Korea', 'seoul': 'South Korea', 'kpop': 'South Korea',
    'china': 'China', 'beijing': 'China', 'shanghai': 'China',
    'thai': 'Thailand', 'bangkok': 'Thailand',
    'viet': 'Vietnam', 'hanoi': 'Vietnam',
    'indo': 'Indonesia', 'jakarta': 'Indonesia',
    'malay': 'Malaysia', 'manila': 'Philippines',
    'india': 'India', 'mumbai': 'India', 'delhi': 'India',
    'pakistan': 'Pakistan', 'bangladesh': 'Bangladesh',
    'qatar': 'Qatar', 'doha': 'Qatar',
    'kuwait': 'Kuwait', 'saudi': 'Saudi Arabia', 'riyadh': 'Saudi Arabia',
    'emirates': 'United Arab Emirates', 'dubai': 'United Arab Emirates',
    'egypt': 'Egypt', 'cairo': 'Egypt',
    'morocco': 'Morocco', 'tunisia': 'Tunisia',
    'lebanon': 'Lebanon', 'jordan': 'Jordan',
    'france': 'France', 'paris': 'France',
    'germany': 'Germany', 'berlin': 'Germany',
    'spain': 'Spain', 'madrid': 'Spain',
    'italy': 'Italy', 'brazil': 'Brazil',
    'argentina': 'Argentina', 'mexico': 'Mexico',
    'nigeria': 'Nigeria', 'kenya': 'Kenya',
    'australia': 'Australia', 'sydney': 'Australia',
    'newzealand': 'New Zealand',
}
USERNAME_KEYWORDS_SORTED = sorted(USERNAME_KEYWORDS.items(), key=lambda x: -len(x[0]))

FLAG_EMOJI_TO_COUNTRY = {
    '🇸🇦': 'Saudi Arabia', '🇦🇪': 'United Arab Emirates', '🇪🇬': 'Egypt',
    '🇰🇼': 'Kuwait', '🇶🇦': 'Qatar', '🇧🇭': 'Bahrain', '🇴🇲': 'Oman',
    '🇯🇴': 'Jordan', '🇱🇧': 'Lebanon', '🇮🇶': 'Iraq', '🇾🇪': 'Yemen',
    '🇵🇸': 'Palestine', '🇲🇦': 'Morocco', '🇩🇿': 'Algeria', '🇹🇳': 'Tunisia',
    '🇱🇾': 'Libya', '🇸🇩': 'Sudan', '🇸🇴': 'Somalia',
    '🇰🇷': 'South Korea', '🇯🇵': 'Japan', '🇨🇳': 'China', '🇹🇼': 'Taiwan',
    '🇭🇰': 'Hong Kong', '🇸🇬': 'Singapore', '🇹🇭': 'Thailand', '🇻🇳': 'Vietnam',
    '🇮🇩': 'Indonesia', '🇲🇾': 'Malaysia', '🇵🇭': 'Philippines',
    '🇮🇳': 'India', '🇵🇰': 'Pakistan', '🇧🇩': 'Bangladesh', '🇱🇰': 'Sri Lanka',
    '🇺🇸': 'United States', '🇬🇧': 'United Kingdom', '🇨🇦': 'Canada',
    '🇫🇷': 'France', '🇩🇪': 'Germany', '🇮🇹': 'Italy', '🇪🇸': 'Spain',
    '🇳🇱': 'Netherlands', '🇵🇹': 'Portugal', '🇹🇷': 'Turkey', '🇷🇺': 'Russia',
    '🇲🇽': 'Mexico', '🇧🇷': 'Brazil', '🇦🇷': 'Argentina', '🇨🇴': 'Colombia',
    '🇨🇱': 'Chile', '🇵🇪': 'Peru', '🇻🇪': 'Venezuela', '🇵🇷': 'Puerto Rico',
    '🇳🇬': 'Nigeria', '🇿🇦': 'South Africa', '🇰🇪': 'Kenya', '🇬🇭': 'Ghana',
    '🇹🇿': 'Tanzania', '🇪🇹': 'Ethiopia',
    '🇦🇺': 'Australia', '🇳🇿': 'New Zealand',
    '🇮🇷': 'Iran', '🇮🇱': 'Israel',
}

BIO_SCRIPT_TO_COUNTRY = [
    (r'[\uAC00-\uD7AF]', 'South Korea', 'Hangul (한글)'),
    (r'[\u3040-\u309F]', 'Japan', 'Hiragana (ひらがな)'),
    (r'[\u30A0-\u30FF]', 'Japan', 'Katakana (カタカナ)'),
    (r'[\u4E00-\u9FFF]', 'China', 'Chinese (中文)'),
    (r'[\u0E00-\u0E7F]', 'Thailand', 'Thai (ภาษาไทย)'),
    (r'[\u0900-\u097F]', 'India', 'Devanagari (हिन्दी)'),
]

# 🔧 v1.9.8: توسيع TLD ليشمل المغرب العربي وأفريقيا الشمالية
TLD_TO_COUNTRY = {
    '.sa': 'Saudi Arabia', '.ae': 'United Arab Emirates', '.kw': 'Kuwait',
    '.qa': 'Qatar', '.eg': 'Egypt', '.bh': 'Bahrain', '.om': 'Oman',
    '.jo': 'Jordan', '.lb': 'Lebanon', '.iq': 'Iraq', '.ye': 'Yemen',
    '.ps': 'Palestine', '.sy': 'Syria',
    '.tn': 'Tunisia', '.ma': 'Morocco', '.dz': 'Algeria', '.ly': 'Libya',
    '.sd': 'Sudan', '.so': 'Somalia',
    '.kr': 'South Korea', '.jp': 'Japan', '.cn': 'China', '.tw': 'Taiwan',
    '.hk': 'Hong Kong', '.sg': 'Singapore', '.th': 'Thailand', '.vn': 'Vietnam',
    '.id': 'Indonesia', '.my': 'Malaysia', '.ph': 'Philippines',
    '.in': 'India', '.pk': 'Pakistan', '.bd': 'Bangladesh',
    '.fr': 'France', '.de': 'Germany', '.it': 'Italy', '.es': 'Spain',
    '.nl': 'Netherlands', '.pt': 'Portugal', '.tr': 'Turkey', '.ru': 'Russia',
    '.br': 'Brazil', '.ar': 'Argentina', '.mx': 'Mexico',
    '.ng': 'Nigeria', '.za': 'South Africa', '.ke': 'Kenya', '.gh': 'Ghana',
    '.au': 'Australia', '.nz': 'New Zealand', '.ca': 'Canada',
    '.uk': 'United Kingdom', '.us': 'United States',
}

# 🔧 v1.9.8: توسيع قائمة الدول المشبوهة لتشمل هولندا وإيرلندا (TikTok HQ)
EXPANDED_SUSPICIOUS = {'Turks and Caicos Islands', 'Norway', 'Sweden', 'Finland', 'Puerto Rico', 'Sri Lanka', 'Netherlands', 'Ireland', 'Iraq'}
TIKTOK_SERVER_COUNTRIES = {'United States', 'United Kingdom'}
GLOBAL_LANGUAGES = {'en'}
TRUSTED_TIKMATRIX_COUNTRIES = {
    'Egypt', 'Saudi Arabia', 'United Arab Emirates', 'Kuwait', 'Qatar',
    'Bahrain', 'Oman', 'Jordan', 'Lebanon', 'Iraq', 'Yemen', 'Palestine',
    'Morocco', 'Algeria', 'Tunisia', 'Libya', 'Sudan', 'South Korea',
    'Japan', 'China', 'Taiwan', 'Singapore', 'Thailand', 'Vietnam',
    'Indonesia', 'Malaysia', 'Philippines', 'India', 'Pakistan',
    'France', 'Germany', 'Italy', 'Spain', 'Portugal', 'Turkey', 'Russia',
    'Brazil', 'Argentina', 'Mexico', 'Colombia', 'Chile', 'Peru',
    'Nigeria', 'South Africa', 'Kenya', 'Ghana', 'Australia', 'New Zealand',
    'Canada', 'Iran', 'Israel',
}

# ═══════════════════════════════════════════════════════════════
# 🦅 المحرك
# ═══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_user(username):
    target = f"https://user.tikmatrix.com/?username={username}"
    for proxy in PROXY_CHAIN:
        url = proxy['url'] + target
        headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept': 'text/html,application/xhtml+xml'}
        if proxy['name'] == 'jina':
            headers['X-Return-Format'] = 'markdown'
        try:
            start = time.time()
            r = requests.get(url, headers=headers, timeout=proxy['timeout'])
            elapsed = time.time() - start
            if r.status_code == 200 and len(r.text) > 1000:
                return {'success': True, 'content': r.text, 'proxy': proxy['name'], 'time': round(elapsed, 2)}
        except Exception:
            continue
    return {'success': False, 'content': None, 'proxy': None, 'time': 0}


def verify_username_match(content, requested):
    """v1.9.6+: التحقق من تطابق Username للحماية من Fallback المضلل"""
    m = re.search(r'@([\w\.]+)', content)
    if m:
        actual = m.group(1).lower().strip()
        if actual in {'tikmatrix001', 'tikmatrixphonefarm'}:
            return False, actual
    return True, None


def extract_bio_v197(content):
    """🔧 v1.9.7: استخراج BIO بـ 3 أنماط بديلة"""
    if not content:
        return None
    for pattern in BIO_PATTERNS:
        m = re.search(pattern, content, re.DOTALL)
        if m:
            bio = m.group(1).strip()
            # تنقية
            if bio and 2 < len(bio) < 500:
                if 'no about' in bio.lower() or bio.startswith('[') or bio.startswith('http'):
                    continue
                return bio
    return None


def extract_fields(content):
    if not content:
        return {}
    data = {}
    # الدولة
    m = re.search(PATTERNS['country_flag'], content)
    if m:
        data['country'] = re.sub(r'\s+', ' ', m.group(1)).strip()
        data['country_source'] = 'flag_emoji'
    else:
        m = re.search(PATTERNS['country_globe'], content)
        if m:
            c = re.sub(r'\s+', ' ', m.group(1)).strip()
            if 2 < len(c) < 50:
                data['country'] = c
                data['country_source'] = 'globe_emoji'
    # نصوص
    for key in ['language', 'user_id', 'sec_uid', 'created', 'nickname', 'avatar']:
        m = re.search(PATTERNS[key], content)
        if m:
            data[key] = m.group(1).strip()
    # أرقام
    for key in ['followers', 'following', 'hearts', 'videos', 'friends']:
        m = re.search(PATTERNS[key], content)
        if m:
            value = (m.group(1) or m.group(2) or '').replace(',', '').strip()
            if value.isdigit():
                data[key] = int(value)
    # 🆕 v1.9.7: استخراج BIO بالأنماط الجديدة
    bio = extract_bio_v197(content)
    if bio:
        data['bio'] = bio
    return data


def correct_country(username, data):
    original = data.get('country')
    language = (data.get('language') or '').lower()[:2]
    bio = data.get('bio', '') or ''
    nickname = data.get('nickname', '') or ''
    username_lower = username.lower()
    log = []

    # 0. تحقق محلي
    if username_lower in LOCAL_VERIFIED_DB:
        ver = LOCAL_VERIFIED_DB[username_lower]
        log.append(f"🔒 تحقق محلي مُعتمد: {ver['name']} → {ver['country']}")
        return _build(ver['country'], 'local_verified', original, log, 99, ver.get('region'))

    # 1. مشاهير
    if username_lower in CELEBRITIES:
        celeb = CELEBRITIES[username_lower]
        log.append(f"✅ مشهور: {celeb['name']} → {celeb['country']}")
        return _build(celeb['country'], 'celebrity_database', original, log, 98, celeb.get('region'))

    # 2. TLD
    for tld, c in TLD_TO_COUNTRY.items():
        if username_lower.endswith(tld):
            log.append(f"🌐 TLD: {tld} → {c}")
            return _build(c, 'tld_domain', original, log, 90)

    # 3. Username Keyword
    for keyword, c in USERNAME_KEYWORDS_SORTED:
        if keyword in username_lower:
            if not original or original != c:
                log.append(f"🔤 username: '{keyword}' → {c}")
                return _build(c, 'username_keyword', original, log, 95 if not original else 88)
            else:
                log.append(f"✓ تأكيد: '{keyword}' = {c}")
                return _build(c, 'username_confirmed', original, log, 96)

    # 4. BIO Flag
    for flag, c in FLAG_EMOJI_TO_COUNTRY.items():
        if flag in bio or flag in nickname:
            if c != original:
                log.append(f"🚩 BIO: {flag} → {c}")
                return _build(c, 'bio_flag', original, log, 92)

    # 5. BIO Script
    for pattern, c, name in BIO_SCRIPT_TO_COUNTRY:
        if re.search(pattern, bio + nickname):
            if original != c:
                log.append(f"🔤 {name} → {c}")
                return _build(c, 'bio_script', original, log, 88)

    # 6. Language Override
    if language and language in LANGUAGE_TO_COUNTRY and language not in GLOBAL_LANGUAGES:
        primary, valid = LANGUAGE_TO_COUNTRY[language]
        if original and original not in valid and original not in TRUSTED_TIKMATRIX_COUNTRIES:
            log.append(f"⚠️ لغة {language} ↔ {original} → {primary}")
            return _build(primary, 'language_override', original, log, 72)
        if original in TIKTOK_SERVER_COUNTRIES and language != 'en':
            log.append(f"⚠️ سيرفر TikTok: {original} (lang {language}) → {primary}")
            return _build(primary, 'tiktok_server_filter', original, log, 70)

    # 🔧 v1.9.8 - الإصلاح الثاني: معالجة الأسماء المضللة (Misleading Names)
    # مثال: @kingofnewyork ← TikMatrix أعطى Netherlands، لكن الاسم يحتوي 'newyork'
    MISLEADING_PATTERNS = {
        'newyork': 'United States', 'nyc': 'United States', 'losangeles': 'United States',
        'california': 'United States', 'texas': 'United States', 'florida': 'United States',
        'london': 'United Kingdom', 'england': 'United Kingdom',
        'paris': 'France', 'berlin': 'Germany', 'roma': 'Italy', 'madrid': 'Spain',
    }
    for misleading, real in MISLEADING_PATTERNS.items():
        if misleading in username_lower:
            if original != real:
                log.append(f"🎭 اسم مضلل: '{misleading}' → {real} (تجاوز {original})")
                return _build(real, 'misleading_name_fix', original, log, 85)

    # 7. مشبوهة (مع توسيع v1.9.8)
    if original in EXPANDED_SUSPICIOUS and language in LANGUAGE_TO_COUNTRY:
        primary, valid = LANGUAGE_TO_COUNTRY[language]
        if original not in valid:
            log.append(f"⚠️ مشبوهة: {original} → {primary}")
            return _build(primary, 'suspicious_filter', original, log, 65)

    # 🔧 v1.9.9 - الحلّ الوسط المُعتمد بإجماع 7/7
    # AMBIGUOUS_TLDS: لاحقات غامضة لا تعني دولة بالضرورة
    AMBIGUOUS_TLDS = {'.tn', '.tv', '.io', '.ai', '.co', '.me', '.ly', '.fm'}

    for tld, c in TLD_TO_COUNTRY.items():
        if username_lower.endswith(tld):
            # حالة 1: TLD غامض → ثقة منخفضة 50% + شارة غامض
            if tld in AMBIGUOUS_TLDS:
                if original and original != c:
                    log.append(f"❓ TLD غامض {tld} (إشارة ضعيفة) و TikMatrix يقول {original}")
                    log.append(f"⚖️ احتمالات متعددة: {c} (50%) | {original} (50%)")
                    log.append(f"⚠️ تحقق يدوي مطلوب - لا أدلة قاطعة")
                    result = _build(original, 'ambiguous_tld', original, log, 50, None)
                    result['ambiguous'] = True
                    result['alternative_country'] = c
                    return result
                else:
                    log.append(f"❓ TLD غامض {tld} (ثقة منخفضة)")
                    return _build(c, 'tld_ambiguous_weak', original, log, 55)
            # حالة 2: TLD واضح (مثل .sa .ae .eg) → أولوية عالية
            elif original in EXPANDED_SUSPICIOUS or (original and original != c):
                log.append(f"🌐 TLD {tld} يتفوق على {original} → {c}")
                return _build(c, 'tld_priority_fix', original, log, 88)

    if original:
        log.append(f"ℹ️ قبول TikMatrix: {original}")
    return _build(original, data.get('country_source', 'tikmatrix'), original, log, 75)


def _build(country, source, original, log, confidence, region=None):
    flag = ''
    for emoji, c in FLAG_EMOJI_TO_COUNTRY.items():
        if c == country:
            flag = emoji
            break
    return {
        'country': country, 'flag': flag, 'confidence': confidence,
        'source': source, 'original_tikmatrix': original, 'corrections': log,
        'preset_region': region,
        'ambiguous': False, 'alternative_country': None,
    }


def detect_expatriate(nationality, residence, source):
    if not nationality or not residence or nationality == residence:
        return {'is_expat': False, 'confidence': 0, 'reason': 'نفس البلد'}
    confidence_map = {
        'local_verified': 99, 'celebrity_database': 95,
        'bio_flag': 90, 'bio_script': 85, 'tld_domain': 88,
        'username_keyword': 80, 'username_confirmed': 92,
    }
    conf = confidence_map.get(source, 60)
    return {
        'is_expat': True, 'confidence': conf,
        'reason': f'الجنسية {nationality} ({source}) ≠ الإقامة {residence} (TikMatrix)'
    }


def extract_region_from_text(country, bio, nickname, username):
    """🌍 v2.0.0: استخراج المنطقة من BIO + nickname + username"""
    if not country:
        return None
    text_combined = f"{bio or ''} {nickname or ''} {username or ''}".strip()
    if not text_combined:
        return None
    return lookup_region(country, text_combined)


def get_smart_region(country, residence, bio, nickname, username, preset_region=None):
    """🧠 v2.0.0: التحليل الذكي للمنطقة بخمس طبقات
    طبقة 1: preset_region من قاعدة المشاهير (ثقة 99%)
    طبقة 2: استخراج من BIO+Nickname+Username في دولة الإقامة (ثقة 90%)
    طبقة 3: استخراج من BIO+Nickname+Username في دولة الجنسية (ثقة 85%)
    طبقة 4: عاصمة/مدينة كبرى لدولة الإقامة (تقديري 40%)
    طبقة 5: عاصمة/مدينة كبرى لدولة الجنسية (تقديري 35%)
    """
    # طبقة 1: preset من المشاهير
    if preset_region:
        return {
            'region_ar': preset_region, 'region_en': preset_region,
            'confidence': 99, 'source': 'preset', 'is_estimate': False,
        }

    # تحديد الدولة الأقرب للموقع الفعلي
    actual_location = residence if residence else country

    # طبقة 2: BIO + nickname + username في دولة الإقامة
    text = f"{bio or ''} {nickname or ''} {username or ''}".strip()
    if text and actual_location:
        r = lookup_region(actual_location, text)
        if r:
            r['source'] = 'bio_extraction'
            r['is_estimate'] = False
            return r

    # طبقة 3: BIO + nickname + username في دولة الجنسية (إن اختلفت عن الإقامة)
    if text and country and country != actual_location:
        r = lookup_region(country, text)
        if r:
            r['source'] = 'bio_nationality'
            r['confidence'] = 85
            r['is_estimate'] = False
            return r

    # طبقة 4: عاصمة/مدينة كبرى للإقامة (تقديري)
    if actual_location:
        cap = lookup_capital(actual_location)
        if cap:
            cap['source'] = 'capital_residence'
            cap['estimate_note'] = f'مدينة رئيسية في {actual_location}'
            return cap

    # طبقة 5: عاصمة/مدينة كبرى للجنسية (أخير احتياطي)
    if country and country != actual_location:
        cap = lookup_capital(country)
        if cap:
            cap['source'] = 'capital_nationality'
            cap['confidence'] = 35
            cap['estimate_note'] = f'مدينة رئيسية لدولة الجنسية {country}'
            return cap

    return None


def lookup_user(username):
    username = username.strip().lower().lstrip('@')
    username = re.sub(r'https?://(?:www\.)?tiktok\.com/@?', '', username)
    username = username.split('?')[0].split('/')[0]

    fetch = fetch_user(username)
    if not fetch['success']:
        return {'success': False, 'username': username, 'error': 'فشل الجلب من كل البروكسيات'}

    is_match, actual = verify_username_match(fetch['content'], username)
    if not is_match:
        return {
            'success': False, 'username': username,
            'error': f'الحساب @{username} غير موجود أو خاص. TikMatrix أرجع حساب @{actual} بدلاً منه.',
            'reason': 'account_not_found',
        }

    raw = extract_fields(fetch['content'])
    correction = correct_country(username, raw)

    # 🧠 v2.0.0: استخراج المنطقة بخمس طبقات ذكية
    region_info = get_smart_region(
        country=correction['country'],
        residence=correction['original_tikmatrix'],
        bio=raw.get('bio'),
        nickname=raw.get('nickname'),
        username=username,
        preset_region=correction.get('preset_region'),
    )

    expat = detect_expatriate(
        correction['country'], correction['original_tikmatrix'], correction['source']
    )

    return {
        'success': True, 'username': username,
        'nickname': raw.get('nickname'),
        'country': correction['country'],
        'country_flag': correction['flag'],
        'country_source': correction['source'],
        'country_original': correction['original_tikmatrix'],
        'language': raw.get('language'),
        'followers': raw.get('followers', 0),
        'following': raw.get('following', 0),
        'hearts': raw.get('hearts', 0),
        'videos': raw.get('videos', 0),
        'friends': raw.get('friends', 0),
        'user_id': raw.get('user_id'),
        'sec_uid': raw.get('sec_uid'),
        'created': raw.get('created'),
        'bio': raw.get('bio'),
        'avatar': raw.get('avatar'),
        'confidence': correction['confidence'],
        'corrections_log': correction['corrections'],
        'proxy_used': fetch['proxy'],
        'fetch_time': fetch['time'],
        'is_expatriate': expat['is_expat'],
        'expat_confidence': expat['confidence'],
        'expat_reason': expat['reason'],
        'region_info': region_info,
        # 🔧 v1.9.9: حقول الغموض
        'ambiguous': correction.get('ambiguous', False),
        'alternative_country': correction.get('alternative_country'),
    }


# ═══════════════════════════════════════════════════════════════
# 🌍 ترجمة الدول
# ═══════════════════════════════════════════════════════════════
COUNTRY_AR = {
    'Saudi Arabia': 'المملكة العربية السعودية', 'United Arab Emirates': 'الإمارات العربية المتحدة',
    'Egypt': 'جمهورية مصر العربية', 'Kuwait': 'دولة الكويت', 'Qatar': 'دولة قطر',
    'Bahrain': 'مملكة البحرين', 'Oman': 'سلطنة عُمان', 'Jordan': 'المملكة الأردنية',
    'Lebanon': 'الجمهورية اللبنانية', 'Iraq': 'العراق', 'Yemen': 'اليمن',
    'Palestine': 'فلسطين', 'Morocco': 'المغرب', 'Algeria': 'الجزائر', 'Tunisia': 'تونس',
    'Libya': 'ليبيا', 'Sudan': 'السودان', 'Somalia': 'الصومال', 'Syria': 'سوريا',
    'South Korea': 'كوريا الجنوبية', 'Japan': 'اليابان', 'China': 'الصين',
    'Taiwan': 'تايوان', 'Hong Kong': 'هونغ كونغ', 'Singapore': 'سنغافورة',
    'Thailand': 'تايلاند', 'Vietnam': 'فيتنام', 'Indonesia': 'إندونيسيا',
    'Malaysia': 'ماليزيا', 'Philippines': 'الفلبين',
    'India': 'الهند', 'Pakistan': 'باكستان', 'Bangladesh': 'بنغلاديش',
    'United States': 'الولايات المتحدة الأمريكية', 'United Kingdom': 'المملكة المتحدة',
    'Canada': 'كندا', 'France': 'فرنسا', 'Germany': 'ألمانيا', 'Italy': 'إيطاليا',
    'Spain': 'إسبانيا', 'Netherlands': 'هولندا', 'Portugal': 'البرتغال',
    'Turkey': 'تركيا', 'Russia': 'روسيا', 'Mexico': 'المكسيك',
    'Brazil': 'البرازيل', 'Argentina': 'الأرجنتين', 'Colombia': 'كولومبيا',
    'Chile': 'تشيلي', 'Peru': 'البيرو', 'Venezuela': 'فنزويلا',
    'Puerto Rico': 'بورتو ريكو',
    'Nigeria': 'نيجيريا', 'South Africa': 'جنوب أفريقيا', 'Kenya': 'كينيا',
    'Ghana': 'غانا', 'Tanzania': 'تنزانيا', 'Ethiopia': 'إثيوبيا',
    'Australia': 'أستراليا', 'New Zealand': 'نيوزيلندا',
    'Iran': 'إيران', 'Israel': 'إسرائيل',
}

SOURCE_AR = {
    'local_verified': '🔒 تحقق محلي مُعتمد', 'celebrity_database': '🌟 قاعدة المشاهير',
    'tld_domain': '🌐 نطاق الدولة', 'username_keyword': '🔤 كلمة في اسم المستخدم',
    'username_confirmed': '✓ تأكيد اسم المستخدم', 'bio_flag': '🚩 علم في الوصف',
    'bio_script': '📝 نص غير لاتيني', 'language_override': '🗣️ تصحيح اللغة',
    'tiktok_server_filter': '🛡️ فلتر سيرفر TikTok',
    'suspicious_filter': '⚠️ فلتر الدول المشبوهة',
    'flag_emoji': '🚩 علم Emoji', 'globe_emoji': '🌍 الكرة الأرضية',
    'tikmatrix': '📊 TikMatrix مباشر',
    'tld_priority_fix': '🌐 TLD ذو أولوية',
    'misleading_name_fix': '🎭 إصلاح اسم مضلل',
    'ambiguous_tld': '❓ TLD غامض - احتمالات متعددة',
    'tld_ambiguous_weak': '❓ TLD غامض (ثقة ضعيفة)',
    # 🔧 v2.0.0: مصادر المنطقة الذكية
    'preset': '🌟 منطقة مُعدّة مع المشهور',
    'bio_extraction': '📝 مستخرجة من الوصف',
    'bio_nationality': '📝 مستخرجة من دولة الجنسية',
    'capital_residence': '🏛️ تقدير عاصمة الإقامة',
    'capital_nationality': '🏛️ تقدير عاصمة الجنسية',
    'major_city_estimate': '🏙️ تقدير المدينة الكبرى',
    'capital_estimate': '🏛️ تقدير العاصمة',
}

# ═══════════════════════════════════════════════════════════════
# 🎨 CSS (RTL + Noto Sans Arabic)
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;700;900&family=Tajawal:wght@400;700;900&display=swap');
* { font-family: 'Noto Sans Arabic', 'Tajawal', sans-serif !important; }
html, body, [class*="css"] { direction: rtl; text-align: right; }
.main-title {
    font-size: 3rem; font-weight: 900; text-align: center;
    background: linear-gradient(135deg, #F59E0B, #FCD34D);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 1rem 0;
}
.subtitle { text-align: center; color: #94A3B8; font-size: 1.1rem; margin-bottom: 2rem; }
.country-card {
    background: linear-gradient(135deg, #1E3A8A, #3B82F6);
    border-radius: 16px; padding: 1.5rem; text-align: center;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3); margin: 1rem 0;
}
.residence-card {
    background: linear-gradient(135deg, #065F46, #10B981);
    border-radius: 16px; padding: 1.5rem; text-align: center;
    box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3); margin: 1rem 0;
}
.region-card {
    background: linear-gradient(135deg, #7C2D12, #F97316);
    border-radius: 16px; padding: 1.5rem; text-align: center;
    box-shadow: 0 8px 32px rgba(249, 115, 22, 0.3); margin: 1rem 0;
}
.region-card-estimate {
    background: linear-gradient(135deg, #713F12, #CA8A04);
    border-radius: 16px; padding: 1.5rem; text-align: center;
    box-shadow: 0 8px 32px rgba(202, 138, 4, 0.3); margin: 1rem 0;
    border: 2px dashed #FBBF24;
}
.estimate-badge {
    background: #FBBF24; color: #0F172A; padding: 0.4rem 1rem;
    border-radius: 999px; font-weight: 700; display: inline-block;
    margin-top: 0.8rem; font-size: 0.8rem;
}
.country-flag { font-size: 3rem; line-height: 1; margin-bottom: 0.5rem; }
.country-name { color: #F1F5F9; font-size: 1.4rem; font-weight: 700; }
.confidence-high { background: #10B981; color: white; padding: 0.4rem 1rem; border-radius: 999px; font-weight: 700; }
.confidence-medium { background: #F59E0B; color: white; padding: 0.4rem 1rem; border-radius: 999px; font-weight: 700; }
.confidence-low { background: #EF4444; color: white; padding: 0.4rem 1rem; border-radius: 999px; font-weight: 700; }
.result-card {
    background: rgba(15, 23, 42, 0.6); border: 1px solid #334155;
    border-radius: 16px; padding: 2rem; margin: 1rem 0;
}
.stat-card {
    background: rgba(15, 23, 42, 0.6); border: 1px solid #334155;
    border-radius: 12px; padding: 1rem; text-align: center;
}
.stat-number { font-size: 1.8rem; font-weight: 900; color: #F59E0B; }
.stat-label { color: #94A3B8; font-size: 0.9rem; }
.correction-log {
    background: rgba(59, 130, 246, 0.1); border-right: 4px solid #3B82F6;
    padding: 0.8rem 1rem; margin: 0.3rem 0; border-radius: 8px; color: #F1F5F9;
}
.expat-badge {
    background: linear-gradient(135deg, #7C3AED, #A78BFA);
    color: white; padding: 0.5rem 1.2rem; border-radius: 999px;
    font-weight: 700; display: inline-block; margin: 0.5rem 0;
}
.ambiguous-badge {
    background: linear-gradient(135deg, #CA8A04, #FBBF24);
    color: #0F172A; padding: 0.5rem 1.2rem; border-radius: 999px;
    font-weight: 700; display: inline-block; margin: 0.5rem 0;
}
.alt-country-card {
    background: linear-gradient(135deg, #7C2D12, #C2410C);
    border-radius: 16px; padding: 1.5rem; text-align: center;
    box-shadow: 0 8px 32px rgba(194, 65, 12, 0.3); margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 📊 الشريط الجانبي
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🦅 بَصِير")
    st.markdown(f"### الإصدار {VERSION}")
    st.markdown("---")
    st.markdown("### 🆕 v2.0.0 - تحليل ذكي")
    st.markdown("- 🧠 5 طبقات لاستخراج المنطقة")
    st.markdown("- 🏛️ عاصمة الإقامة كتقدير ذكي")
    st.markdown("- 🏙️ مدينة كبرى بديلة")
    st.markdown("- 🟡 شارة 'تقديري' واضحة")
    st.markdown("- ✅ ثقة شفافة لكل طبقة")
    st.markdown(f"- 🏛️ **{get_capitals_count()}** عاصمة/مدينة")
    st.markdown("---")
    st.markdown("### 📊 الإحصائيات")
    st.markdown(f"- 🌍 **{get_total_regions()}+** منطقة")
    st.markdown(f"- 🌐 **{get_countries_count()}** دولة")
    st.markdown(f"- 🌟 **{len(CELEBRITIES)}** مشهور")
    st.markdown("---")
    st.markdown("### 🎯 طبقات التصحيح")
    st.markdown("0. 🔒 تحقق محلي مُعتمد")
    st.markdown("1. 🌟 قاعدة المشاهير")
    st.markdown("2. 🌐 نطاق الدولة")
    st.markdown("3. 🔤 اسم المستخدم")
    st.markdown("4. 🚩 علم الوصف")
    st.markdown("5. 📝 نص غير لاتيني")
    st.markdown("6. 🗣️ اللغة")
    st.markdown("7. 🌍 استخراج المنطقة")

# ═══════════════════════════════════════════════════════════════
# 🎨 المحتوى الرئيسي
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="main-title">🦅 بَصِير</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle" dir="rtl">مولّد ذكي لحسابات TikTok | {VERSION} | استخراج المنطقة + كشف المغترب</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    username = st.text_input("اسم المستخدم على TikTok", placeholder="مثال: aboflah", help="بدون @")
    search_btn = st.button("🔍 ابحث الآن", type="primary")

if search_btn and username:
    with st.spinner(f"🔍 جاري البحث عن @{username}..."):
        result = lookup_user(username)

    if not result.get('success'):
        st.error(f"❌ {result.get('error', 'فشل البحث')}")
        if result.get('reason') == 'account_not_found':
            st.info("ℹ️ **الأسباب المحتملة**: حساب خاص، محذوف، محظور، أو خطأ إملائي")
    else:
        col_a, col_b = st.columns([1, 2])

        with col_a:
            country = result.get('country', 'غير متوفرة')
            flag = result.get('country_flag', '')
            country_ar = COUNTRY_AR.get(country, country)

            residence = result.get('country_original')
            residence_flag = ''
            residence_ar = ''
            show_residence = result.get('is_expatriate', False)
            if show_residence and residence:
                for emoji, c in FLAG_EMOJI_TO_COUNTRY.items():
                    if c == residence:
                        residence_flag = emoji
                        break
                residence_ar = COUNTRY_AR.get(residence, residence)

            # 🎟️ بطاقة الجنسية
            st.markdown(f"""
            <div class="country-card" dir="rtl">
                <div style="color: #FCD34D; font-size: 0.85rem; font-weight: 700; margin-bottom: 0.5rem;">🎟️ الجنسية</div>
                <div class="country-flag">{flag}</div>
                <div class="country-name">{country_ar}</div>
                <div style="color: #93C5FD; font-size: 0.9rem; margin-top: 0.5rem;">{country}</div>
            </div>
            """, unsafe_allow_html=True)

            # 📍 بطاقة الإقامة (مغترب فقط)
            if show_residence:
                st.markdown(f"""
                <div class="residence-card" dir="rtl">
                    <div style="color: #D1FAE5; font-size: 0.85rem; font-weight: 700; margin-bottom: 0.5rem;">📍 موقع الإقامة الحالي</div>
                    <div style="font-size: 3rem; line-height: 1; margin-bottom: 0.5rem;">{residence_flag}</div>
                    <div style="color: #F1F5F9; font-size: 1.4rem; font-weight: 700;">{residence_ar}</div>
                    <div style="color: #A7F3D0; font-size: 0.85rem; margin-top: 0.5rem;">{residence}</div>
                </div>
                """, unsafe_allow_html=True)
                expat_conf = result.get('expat_confidence', 0)
                st.markdown(f'<div style="text-align: center;" dir="rtl"><span class="expat-badge">🛂 مغترب (ثقة {expat_conf}%)</span></div>', unsafe_allow_html=True)

            # 🔧 v1.9.9: بطاقة الدولة البديلة (للغامض)
            if result.get('ambiguous') and result.get('alternative_country'):
                alt_c = result.get('alternative_country')
                alt_flag = ''
                for emoji, c in FLAG_EMOJI_TO_COUNTRY.items():
                    if c == alt_c:
                        alt_flag = emoji
                        break
                alt_ar = COUNTRY_AR.get(alt_c, alt_c)
                st.markdown(f"""
                <div class="alt-country-card" dir="rtl">
                    <div style="color: #FED7AA; font-size: 0.85rem; font-weight: 700; margin-bottom: 0.5rem;">⚖️ احتمال بديل (50%)</div>
                    <div style="font-size: 3rem; line-height: 1; margin-bottom: 0.5rem;">{alt_flag}</div>
                    <div style="color: #F1F5F9; font-size: 1.4rem; font-weight: 700;">{alt_ar}</div>
                    <div style="color: #FFEDD5; font-size: 0.85rem; margin-top: 0.5rem;">{alt_c}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f'<div style="text-align: center;" dir="rtl"><span class="ambiguous-badge">❓ غامض - تحقق يدوي مطلوب</span></div>', unsafe_allow_html=True)

            # 🏙️ بطاقة المنطقة الذكية v2.0.0
            region_info = result.get('region_info')
            if region_info:
                is_estimate = region_info.get('is_estimate', False)
                estimate_note = region_info.get('estimate_note', '')
                card_class = 'region-card-estimate' if is_estimate else 'region-card'
                title = '🏙️ المنطقة / المدينة (تقديري)' if is_estimate else '🏙️ المنطقة / المدينة'
                st.markdown(f"""
                <div class="{card_class}" dir="rtl">
                    <div style="color: #FED7AA; font-size: 0.85rem; font-weight: 700; margin-bottom: 0.5rem;">{title}</div>
                    <div style="font-size: 3rem; line-height: 1; margin-bottom: 0.5rem;">📍</div>
                    <div style="color: #F1F5F9; font-size: 1.4rem; font-weight: 700;">{region_info.get('region_ar')}</div>
                    <div style="color: #FFEDD5; font-size: 0.85rem; margin-top: 0.5rem;">{region_info.get('region_en')} · ثقة {region_info.get('confidence', 90)}%</div>
                    {f'<div class="estimate-badge">🟡 {estimate_note}</div>' if is_estimate else ''}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.4); border: 1px dashed #475569; border-radius: 16px; padding: 1.5rem; text-align: center; margin: 1rem 0;" dir="rtl">
                    <div style="color: #94A3B8; font-size: 0.85rem; font-weight: 700;">🏙️ المنطقة / المدينة</div>
                    <div style="font-size: 2rem; color: #64748B; margin: 0.5rem 0;">—</div>
                    <div style="color: #64748B; font-size: 0.85rem;">لم يتم العثور على منطقة موثوقة</div>
                </div>
                """, unsafe_allow_html=True)

            conf = result.get('confidence', 0)
            if conf >= 90:
                conf_class, conf_text = "confidence-high", "موثوق جداً"
            elif conf >= 70:
                conf_class, conf_text = "confidence-medium", "موثوق"
            else:
                conf_class, conf_text = "confidence-low", "تحقق يدوي"
            st.markdown(f'<div style="text-align: center; margin: 1rem 0;" dir="rtl"><span class="{conf_class}">🛡️ {conf_text} ({conf}%)</span></div>', unsafe_allow_html=True)

        with col_b:
            nickname = result.get('nickname', username)
            st.markdown(f"""
            <div class="result-card" dir="rtl">
                <h2 style="color: #F59E0B; margin-bottom: 0.5rem;">{nickname}</h2>
                <p style="color: #94A3B8; font-size: 1.1rem;">@{result.get('username')}</p>
                <p style="color: #CBD5E1; margin-top: 1rem; line-height: 1.8;">{result.get('bio') or 'لا يوجد وصف'}</p>
                <p style="color: #94A3B8; font-size: 0.9rem; margin-top: 1rem;">
                    🗣️ اللغة: <strong style="color: #F59E0B;">{result.get('language') or 'غير محددة'}</strong> |
                    📅 الإنشاء: <strong style="color: #F59E0B;">{result.get('created') or 'غير متوفر'}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<h3 dir="rtl" style="text-align:right;">📊 الإحصائيات</h3>', unsafe_allow_html=True)
        stat_cols = st.columns(5)
        stats = [
            ("👥", "المتابعون", result.get('followers', 0)),
            ("❤️", "الإعجابات", result.get('hearts', 0)),
            ("🎬", "الفيديوهات", result.get('videos', 0)),
            ("➕", "يتابع", result.get('following', 0)),
            ("👫", "الأصدقاء", result.get('friends', 0)),
        ]
        for i, (icon, label, value) in enumerate(stats):
            with stat_cols[i]:
                if value >= 1_000_000:
                    formatted = f"{value/1_000_000:.1f}M"
                elif value >= 1_000:
                    formatted = f"{value/1_000:.1f}K"
                else:
                    formatted = f"{value:,}"
                st.markdown(f'<div class="stat-card" dir="rtl"><div style="font-size: 2.5rem;">{icon}</div><div class="stat-number">{formatted}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

        corrections = result.get('corrections_log', [])
        if corrections:
            st.markdown('<h3 dir="rtl" style="text-align:right;">🔧 سجل اكتشاف الجنسية</h3>', unsafe_allow_html=True)
            for c in corrections:
                st.markdown(f'<div class="correction-log" dir="rtl">{c}</div>', unsafe_allow_html=True)
            if result.get('is_expatriate'):
                st.info(f"ℹ️ **توضيح المغترب**: {result.get('expat_reason')}")

        source = result.get('country_source', 'tikmatrix')
        source_ar = SOURCE_AR.get(source, source)
        st.markdown(f'<div style="text-align: center; margin: 2rem 0; padding: 1rem; background: rgba(59, 130, 246, 0.1); border-radius: 12px;" dir="rtl"><strong style="color: #F59E0B;">مصدر اكتشاف الدولة:</strong> <span style="color: #F1F5F9;">{source_ar}</span></div>', unsafe_allow_html=True)

        with st.expander("🔧 تفاصيل تقنية"):
            col_x, col_y = st.columns(2)
            with col_x:
                st.text(f"User ID: {result.get('user_id', 'N/A')}")
                st.text(f"Proxy: {result.get('proxy_used', 'N/A')}")
                st.text(f"Fetch time: {result.get('fetch_time', 0)}s")
            with col_y:
                st.text(f"SecUID: {(result.get('sec_uid') or 'N/A')[:30]}...")
                st.text(f"Source: {result.get('country_source', 'N/A')}")
                st.text(f"الإصدار: {VERSION}")

st.markdown(f"""
<div style="text-align: center; margin-top: 3rem; padding: 1rem; color: #64748B;" dir="rtl">
    <p>🦅 <strong style="color: #F59E0B;">بَصِير {VERSION}</strong> - مولّد ذكي لمعلومات حسابات TikTok</p>
    <p style="font-size: 0.85rem;">قاعدة {get_total_regions()}+ منطقة عبر {get_countries_count()} دولة · {len(CELEBRITIES)} مشهور · قرار اللجنة 7/7 - 2026-06-05</p>
</div>
""", unsafe_allow_html=True)
