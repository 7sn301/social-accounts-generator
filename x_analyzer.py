"""
🐦 X (Twitter) Analyzer v3 - مع حقل Location الحقيقي
يستخدم fxtwitter API لجلب location الفعلي من بروفايل المستخدم
+ Twitter Syndication API كـ backup للتغريدات الفردية
"""
import requests
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

# =====================================================
# Constants
# =====================================================

FXTWITTER_API = "https://api.fxtwitter.com"
TWITTER_SYNDICATION_API = "https://cdn.syndication.twimg.com/tweet-result"

# خريطة الدول الكاملة
X_COUNTRY_MAP = {
    'SA': {'flag': '🇸🇦', 'ar': 'السعودية', 'en': 'Saudi Arabia'},
    'AE': {'flag': '🇦🇪', 'ar': 'الإمارات', 'en': 'United Arab Emirates'},
    'EG': {'flag': '🇪🇬', 'ar': 'مصر', 'en': 'Egypt'},
    'IQ': {'flag': '🇮🇶', 'ar': 'العراق', 'en': 'Iraq'},
    'KW': {'flag': '🇰🇼', 'ar': 'الكويت', 'en': 'Kuwait'},
    'QA': {'flag': '🇶🇦', 'ar': 'قطر', 'en': 'Qatar'},
    'BH': {'flag': '🇧🇭', 'ar': 'البحرين', 'en': 'Bahrain'},
    'OM': {'flag': '🇴🇲', 'ar': 'عمان', 'en': 'Oman'},
    'YE': {'flag': '🇾🇪', 'ar': 'اليمن', 'en': 'Yemen'},
    'JO': {'flag': '🇯🇴', 'ar': 'الأردن', 'en': 'Jordan'},
    'LB': {'flag': '🇱🇧', 'ar': 'لبنان', 'en': 'Lebanon'},
    'SY': {'flag': '🇸🇾', 'ar': 'سوريا', 'en': 'Syria'},
    'PS': {'flag': '🇵🇸', 'ar': 'فلسطين', 'en': 'Palestine'},
    'MA': {'flag': '🇲🇦', 'ar': 'المغرب', 'en': 'Morocco'},
    'DZ': {'flag': '🇩🇿', 'ar': 'الجزائر', 'en': 'Algeria'},
    'TN': {'flag': '🇹🇳', 'ar': 'تونس', 'en': 'Tunisia'},
    'LY': {'flag': '🇱🇾', 'ar': 'ليبيا', 'en': 'Libya'},
    'SD': {'flag': '🇸🇩', 'ar': 'السودان', 'en': 'Sudan'},
    'SO': {'flag': '🇸🇴', 'ar': 'الصومال', 'en': 'Somalia'},
    'MR': {'flag': '🇲🇷', 'ar': 'موريتانيا', 'en': 'Mauritania'},
    'KM': {'flag': '🇰🇲', 'ar': 'جزر القمر', 'en': 'Comoros'},
    'DJ': {'flag': '🇩🇯', 'ar': 'جيبوتي', 'en': 'Djibouti'},
    'US': {'flag': '🇺🇸', 'ar': 'الولايات المتحدة', 'en': 'United States'},
    'GB': {'flag': '🇬🇧', 'ar': 'المملكة المتحدة', 'en': 'United Kingdom'},
    'CA': {'flag': '🇨🇦', 'ar': 'كندا', 'en': 'Canada'},
    'AU': {'flag': '🇦🇺', 'ar': 'أستراليا', 'en': 'Australia'},
    'FR': {'flag': '🇫🇷', 'ar': 'فرنسا', 'en': 'France'},
    'DE': {'flag': '🇩🇪', 'ar': 'ألمانيا', 'en': 'Germany'},
    'IT': {'flag': '🇮🇹', 'ar': 'إيطاليا', 'en': 'Italy'},
    'ES': {'flag': '🇪🇸', 'ar': 'إسبانيا', 'en': 'Spain'},
    'NL': {'flag': '🇳🇱', 'ar': 'هولندا', 'en': 'Netherlands'},
    'SE': {'flag': '🇸🇪', 'ar': 'السويد', 'en': 'Sweden'},
    'NO': {'flag': '🇳🇴', 'ar': 'النرويج', 'en': 'Norway'},
    'DK': {'flag': '🇩🇰', 'ar': 'الدنمارك', 'en': 'Denmark'},
    'FI': {'flag': '🇫🇮', 'ar': 'فنلندا', 'en': 'Finland'},
    'CH': {'flag': '🇨🇭', 'ar': 'سويسرا', 'en': 'Switzerland'},
    'BE': {'flag': '🇧🇪', 'ar': 'بلجيكا', 'en': 'Belgium'},
    'AT': {'flag': '🇦🇹', 'ar': 'النمسا', 'en': 'Austria'},
    'IE': {'flag': '🇮🇪', 'ar': 'أيرلندا', 'en': 'Ireland'},
    'PT': {'flag': '🇵🇹', 'ar': 'البرتغال', 'en': 'Portugal'},
    'GR': {'flag': '🇬🇷', 'ar': 'اليونان', 'en': 'Greece'},
    'TR': {'flag': '🇹🇷', 'ar': 'تركيا', 'en': 'Turkey'},
    'IR': {'flag': '🇮🇷', 'ar': 'إيران', 'en': 'Iran'},
    'PK': {'flag': '🇵🇰', 'ar': 'باكستان', 'en': 'Pakistan'},
    'IN': {'flag': '🇮🇳', 'ar': 'الهند', 'en': 'India'},
    'BD': {'flag': '🇧🇩', 'ar': 'بنغلاديش', 'en': 'Bangladesh'},
    'AF': {'flag': '🇦🇫', 'ar': 'أفغانستان', 'en': 'Afghanistan'},
    'CN': {'flag': '🇨🇳', 'ar': 'الصين', 'en': 'China'},
    'JP': {'flag': '🇯🇵', 'ar': 'اليابان', 'en': 'Japan'},
    'KR': {'flag': '🇰🇷', 'ar': 'كوريا الجنوبية', 'en': 'South Korea'},
    'TH': {'flag': '🇹🇭', 'ar': 'تايلاند', 'en': 'Thailand'},
    'ID': {'flag': '🇮🇩', 'ar': 'إندونيسيا', 'en': 'Indonesia'},
    'MY': {'flag': '🇲🇾', 'ar': 'ماليزيا', 'en': 'Malaysia'},
    'SG': {'flag': '🇸🇬', 'ar': 'سنغافورة', 'en': 'Singapore'},
    'PH': {'flag': '🇵🇭', 'ar': 'الفلبين', 'en': 'Philippines'},
    'VN': {'flag': '🇻🇳', 'ar': 'فيتنام', 'en': 'Vietnam'},
    'BR': {'flag': '🇧🇷', 'ar': 'البرازيل', 'en': 'Brazil'},
    'MX': {'flag': '🇲🇽', 'ar': 'المكسيك', 'en': 'Mexico'},
    'AR': {'flag': '🇦🇷', 'ar': 'الأرجنتين', 'en': 'Argentina'},
    'CL': {'flag': '🇨🇱', 'ar': 'تشيلي', 'en': 'Chile'},
    'CO': {'flag': '🇨🇴', 'ar': 'كولومبيا', 'en': 'Colombia'},
    'RU': {'flag': '🇷🇺', 'ar': 'روسيا', 'en': 'Russia'},
    'UA': {'flag': '🇺🇦', 'ar': 'أوكرانيا', 'en': 'Ukraine'},
    'PL': {'flag': '🇵🇱', 'ar': 'بولندا', 'en': 'Poland'},
    'IL': {'flag': '🇮🇱', 'ar': 'إسرائيل', 'en': 'Israel'},
    'ZA': {'flag': '🇿🇦', 'ar': 'جنوب أفريقيا', 'en': 'South Africa'},
    'NG': {'flag': '🇳🇬', 'ar': 'نيجيريا', 'en': 'Nigeria'},
    'KE': {'flag': '🇰🇪', 'ar': 'كينيا', 'en': 'Kenya'},
    'ET': {'flag': '🇪🇹', 'ar': 'إثيوبيا', 'en': 'Ethiopia'},
    'NZ': {'flag': '🇳🇿', 'ar': 'نيوزيلندا', 'en': 'New Zealand'},
}

# قاموس مدن وأماكن → دولة (يستخدم لتحليل حقل location)
LOCATION_KEYWORDS = {
    # Saudi Arabia
    'SA': ['saudi', 'arabia', 'riyadh', 'jeddah', 'mecca', 'medina', 'dammam', 'khobar', 'taif', 'ksa',
           'السعودية', 'الرياض', 'جدة', 'مكة', 'المدينة', 'الدمام', 'الخبر', 'الطائف', 'القصيم', 'تبوك'],
    'AE': ['uae', 'emirates', 'dubai', 'abu dhabi', 'sharjah', 'ajman',
           'الإمارات', 'دبي', 'أبوظبي', 'الشارقة', 'عجمان', 'العين', 'رأس الخيمة'],
    'EG': ['egypt', 'cairo', 'alexandria', 'giza', 'luxor', 'aswan',
           'مصر', 'القاهرة', 'الإسكندرية', 'الجيزة', 'الأقصر', 'أسوان', 'المنصورة'],
    'IQ': ['iraq', 'baghdad', 'basra', 'mosul', 'erbil', 'najaf', 'karbala',
           'العراق', 'بغداد', 'البصرة', 'الموصل', 'أربيل', 'النجف', 'كربلاء', 'الأنبار', 'كركوك'],
    'KW': ['kuwait', 'الكويت'],
    'QA': ['qatar', 'doha', 'قطر', 'الدوحة'],
    'BH': ['bahrain', 'manama', 'البحرين', 'المنامة'],
    'OM': ['oman', 'muscat', 'عمان', 'مسقط', 'سلطنة عمان'],
    'YE': ['yemen', 'sanaa', 'aden', 'اليمن', 'صنعاء', 'عدن'],
    'JO': ['jordan', 'amman', 'الأردن', 'عمّان'],
    'LB': ['lebanon', 'beirut', 'لبنان', 'بيروت'],
    'SY': ['syria', 'damascus', 'aleppo', 'سوريا', 'سورية', 'دمشق', 'حلب'],
    'PS': ['palestine', 'gaza', 'jerusalem', 'فلسطين', 'غزة', 'القدس', 'الضفة', 'رام الله'],
    'MA': ['morocco', 'casablanca', 'rabat', 'marrakech', 'المغرب', 'الدار البيضاء', 'الرباط', 'مراكش', 'فاس'],
    'DZ': ['algeria', 'algiers', 'الجزائر', 'وهران', 'قسنطينة'],
    'TN': ['tunisia', 'tunis', 'تونس'],
    'LY': ['libya', 'tripoli', 'benghazi', 'ليبيا', 'طرابلس', 'بنغازي'],
    'SD': ['sudan', 'khartoum', 'السودان', 'الخرطوم'],
    'SO': ['somalia', 'mogadishu', 'الصومال', 'مقديشو'],
    'US': ['usa', 'united states', 'america', 'new york', 'washington', 'los angeles', 'chicago', 'texas',
           'california', 'florida', 'boston', 'seattle', 'silicon valley', 'nyc', 'la,', 'd.c.', 'dc',
           'أمريكا', 'الولايات المتحدة', 'نيويورك', 'واشنطن', 'لوس أنجلوس', 'كاليفورنيا', 'تكساس'],
    'GB': ['england', 'united kingdom', 'london', 'manchester', 'liverpool', 'scotland', 'wales', 'britain', 'uk',
           'إنجلترا', 'بريطانيا', 'المملكة المتحدة', 'لندن', 'مانشستر', 'اسكتلندا'],
    'CA': ['canada', 'toronto', 'vancouver', 'montreal', 'ottawa', 'كندا', 'تورنتو', 'فانكوفر', 'مونتريال'],
    'AU': ['australia', 'sydney', 'melbourne', 'أستراليا', 'سيدني', 'ملبورن'],
    'FR': ['france', 'paris', 'lyon', 'فرنسا', 'باريس', 'ليون'],
    'DE': ['germany', 'berlin', 'munich', 'ألمانيا', 'برلين', 'ميونخ'],
    'IT': ['italy', 'rome', 'milan', 'إيطاليا', 'روما', 'ميلانو'],
    'ES': ['spain', 'madrid', 'barcelona', 'إسبانيا', 'مدريد', 'برشلونة'],
    'TR': ['turkey', 'istanbul', 'ankara', 'تركيا', 'إسطنبول', 'أنقرة'],
    'IR': ['iran', 'tehran', 'إيران', 'طهران'],
    'PK': ['pakistan', 'karachi', 'lahore', 'islamabad', 'باكستان', 'كراتشي', 'لاهور'],
    'IN': ['india', 'mumbai', 'delhi', 'bangalore', 'الهند', 'مومباي', 'دلهي'],
    'JP': ['japan', 'tokyo', 'osaka', 'اليابان', 'طوكيو'],
    'CN': ['china', 'beijing', 'shanghai', 'الصين', 'بكين', 'شنغهاي'],
}

# الأعلام في النص
FLAG_TO_COUNTRY = {
    '🇸🇦': 'SA', '🇦🇪': 'AE', '🇪🇬': 'EG', '🇮🇶': 'IQ', '🇰🇼': 'KW',
    '🇶🇦': 'QA', '🇧🇭': 'BH', '🇴🇲': 'OM', '🇾🇪': 'YE', '🇯🇴': 'JO',
    '🇱🇧': 'LB', '🇸🇾': 'SY', '🇵🇸': 'PS', '🇲🇦': 'MA', '🇩🇿': 'DZ',
    '🇹🇳': 'TN', '🇱🇾': 'LY', '🇸🇩': 'SD', '🇸🇴': 'SO',
    '🇺🇸': 'US', '🇬🇧': 'GB', '🇨🇦': 'CA', '🇦🇺': 'AU', '🇫🇷': 'FR',
    '🇩🇪': 'DE', '🇮🇹': 'IT', '🇪🇸': 'ES', '🇹🇷': 'TR', '🇮🇷': 'IR',
    '🇵🇰': 'PK', '🇮🇳': 'IN', '🇯🇵': 'JP', '🇨🇳': 'CN', '🏴󠁧󠁢󠁥󠁮󠁧󠁿': 'GB',
}

LANGUAGE_NAMES_AR = {
    'ar': 'العربية', 'en': 'الإنجليزية', 'fr': 'الفرنسية', 'es': 'الإسبانية',
    'de': 'الألمانية', 'it': 'الإيطالية', 'tr': 'التركية', 'fa': 'الفارسية',
    'ur': 'الأردية', 'hi': 'الهندية', 'ja': 'اليابانية', 'ko': 'الكورية',
    'zh': 'الصينية', 'ru': 'الروسية', 'pt': 'البرتغالية', 'nl': 'الهولندية',
    'und': 'غير محدد', 'qme': 'وسائط فقط', 'qam': 'منشن فقط', 'in': 'الإندونيسية',
}

# =====================================================
# Helper Functions
# =====================================================

def format_count(n):
    """تنسيق الأرقام (1.5K, 2.3M)"""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "0"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def parse_x_url(url):
    """استخراج username و tweet_id من رابط X/Twitter"""
    url = url.strip()
    # رابط بروفايل: https://x.com/username
    # رابط تغريدة: https://x.com/username/status/1234567890
    pattern = r'(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)(?:/status/(\d+))?'
    m = re.search(pattern, url)
    if m:
        username = m.group(1)
        tweet_id = m.group(2)
        # استبعد المسارات الخاصة
        if username.lower() in ('home', 'explore', 'notifications', 'messages', 'i', 'search', 'compose'):
            return None, None
        return username, tweet_id
    # رابط بسيط: @username أو username
    if url.startswith('@'):
        return url[1:], None
    if re.match(r'^[A-Za-z0-9_]+$', url):
        return url, None
    return None, None


def detect_country_from_location_field(location_text):
    """
    تحليل حقل location الرسمي من بروفايل X
    يُرجع (country_code, confidence, evidence)
    """
    if not location_text:
        return None, 0, "حقل الموقع فارغ"
    
    text = location_text.lower().strip()
    text_original = location_text
    
    # 1. ابحث عن أعلام في النص
    for flag, code in FLAG_TO_COUNTRY.items():
        if flag in text_original:
            return code, 95, f"علم {flag} موجود في حقل الموقع"
    
    # 2. ابحث عن مدن/دول
    matches = []
    for code, keywords in LOCATION_KEYWORDS.items():
        for kw in keywords:
            kw_low = kw.lower()
            # مطابقة كلمة كاملة (boundary)
            pattern = r'\b' + re.escape(kw_low) + r'\b'
            if re.search(pattern, text):
                matches.append((code, kw, len(kw)))
    
    if matches:
        # خذ أطول مطابقة (أكثر تحديداً)
        matches.sort(key=lambda x: -x[2])
        code, kw, _ = matches[0]
        return code, 90, f"مطابقة '{kw}' في حقل الموقع: \"{location_text}\""
    
    # 3. هل النص يحتوي كلمات تدل على أنه ليس موقعاً حقيقياً؟
    fake_indicators = ['follow me', 'cookie', 'http', 'www.', '.com', '.net', 'click', 'link', 'subscribe',
                       'youtube', 'instagram', 'tiktok', 'snapchat']
    for indicator in fake_indicators:
        if indicator in text:
            return None, 0, f"حقل الموقع يحتوي على نص دعائي/رابط (\"{location_text}\")"
    
    return None, 0, f"حقل الموقع غير معروف: \"{location_text}\""


def detect_country_from_text(text):
    """تحليل أي نص لاستخراج دولة"""
    if not text:
        return None, 0, []
    
    evidence = []
    scores = {}
    
    # 1. الأعلام
    for flag, code in FLAG_TO_COUNTRY.items():
        if flag in text:
            scores[code] = scores.get(code, 0) + 60
            evidence.append(f"علم {flag} ({X_COUNTRY_MAP.get(code, {}).get('ar', code)})")
    
    # 2. المدن والدول
    text_lower = text.lower()
    for code, keywords in LOCATION_KEYWORDS.items():
        for kw in keywords:
            kw_low = kw.lower()
            pattern = r'\b' + re.escape(kw_low) + r'\b'
            if re.search(pattern, text_lower):
                scores[code] = scores.get(code, 0) + 40
                evidence.append(f"كلمة '{kw}'")
                break  # كلمة واحدة لكل دولة في هذا النص
    
    if not scores:
        return None, 0, []
    
    best = max(scores, key=scores.get)
    confidence = min(scores[best], 100)
    return best, confidence, evidence


# =====================================================
# Main API Functions
# =====================================================

def fetch_x_user_profile(username, timeout=15):
    """
    جلب بروفايل المستخدم من fxtwitter API
    يُرجع dict مع الموقع الحقيقي إن وُجد
    """
    url = f"{FXTWITTER_API}/{username}"
    try:
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if r.status_code != 200:
            return {"success": False, "error": f"HTTP {r.status_code}"}
        
        data = r.json()
        if data.get("code") != 200 or not data.get("user"):
            return {"success": False, "error": data.get("message", "حساب غير موجود")}
        
        u = data["user"]
        return {
            "success": True,
            "screen_name": u.get("screen_name"),
            "user_id": u.get("id"),  # ID الدائم
            "name": u.get("name"),
            "bio": u.get("description", ""),
            "location_field": u.get("location", ""),  # 🎯 الحقل الذهبي
            "url": u.get("url"),
            "website": u.get("website", {}).get("url") if isinstance(u.get("website"), dict) else u.get("website"),
            "avatar_url": u.get("avatar_url"),
            "banner_url": u.get("banner_url"),
            "followers": u.get("followers", 0),
            "following": u.get("following", 0),
            "tweets": u.get("tweets", 0),
            "likes": u.get("likes", 0),
            "media_count": u.get("media_count", 0),
            "joined": u.get("joined"),
            "verification": u.get("verification"),
            "protected": u.get("protected", False),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_x_tweet(username, tweet_id, timeout=15):
    """
    جلب تغريدة محددة من fxtwitter API
    """
    url = f"{FXTWITTER_API}/{username}/status/{tweet_id}"
    try:
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if r.status_code != 200:
            return {"success": False, "error": f"HTTP {r.status_code}"}
        
        data = r.json()
        if data.get("code") != 200 or not data.get("tweet"):
            return {"success": False, "error": data.get("message", "تغريدة غير موجودة")}
        
        t = data["tweet"]
        author = t.get("author", {}) if isinstance(t.get("author"), dict) else {}
        
        return {
            "success": True,
            "tweet_id": t.get("id"),
            "tweet_url": t.get("url"),
            "text": t.get("text", ""),
            "raw_text": t.get("raw_text", {}).get("text") if isinstance(t.get("raw_text"), dict) else t.get("raw_text"),
            "lang": t.get("lang"),
            "created_at": t.get("created_at"),
            "created_timestamp": t.get("created_timestamp"),
            "likes": t.get("likes", 0),
            "retweets": t.get("retweets", 0),
            "replies": t.get("replies", 0),
            "bookmarks": t.get("bookmarks", 0),
            "quotes": t.get("quotes", 0),
            "views": t.get("views", 0),
            "possibly_sensitive": t.get("possibly_sensitive", False),
            "source": t.get("source", ""),
            "media": t.get("media", {}),
            # معلومات المؤلف
            "author_screen_name": author.get("screen_name"),
            "author_id": author.get("id"),
            "author_name": author.get("name"),
            "author_bio": author.get("description", ""),
            "author_location": author.get("location", ""),
            "author_followers": author.get("followers", 0),
            "author_avatar": author.get("avatar_url"),
            "author_verified": bool(author.get("verified")),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_x_account(username_or_url, timeout=15):
    """
    تحليل حساب X كامل: جلب البروفايل + استنتاج الدولة من حقل location الحقيقي
    
    🎯 الميزة الرئيسية: يستخدم حقل location الفعلي من X الذي يدخله المستخدم
    """
    # استخراج username
    if username_or_url.startswith("http"):
        username, tweet_id = parse_x_url(username_or_url)
    else:
        username = username_or_url.lstrip("@").strip()
        tweet_id = None
    
    if not username:
        return {"success": False, "error": "رابط أو اسم مستخدم غير صحيح"}
    
    # جلب البروفايل
    profile = fetch_x_user_profile(username, timeout=timeout)
    if not profile.get("success"):
        return profile
    
    # كشف الدولة من حقل location الرسمي (الأكثر دقة)
    loc_field = profile.get("location_field", "")
    country_code, confidence, evidence = detect_country_from_location_field(loc_field)
    detection_source = "حقل الموقع الرسمي ⭐"
    
    # إذا فشل، جرب البايو
    if not country_code:
        bio = profile.get("bio", "")
        country_code, confidence, ev_list = detect_country_from_text(bio)
        evidence = "; ".join(ev_list) if ev_list else "لم يتم العثور على دلائل"
        detection_source = "تحليل البايو"
    
    # إذا لا يزال فشل، جرب الاسم
    if not country_code:
        name = profile.get("name", "")
        country_code, confidence, ev_list = detect_country_from_text(name)
        evidence = "; ".join(ev_list) if ev_list else evidence
        detection_source = "تحليل الاسم الظاهر"
    
    # تنسيق الناتج
    country_info = X_COUNTRY_MAP.get(country_code, {}) if country_code else {}
    
    profile["country_code"] = country_code
    profile["country_flag"] = country_info.get("flag", "❓")
    profile["country_name_ar"] = country_info.get("ar", "غير محدد")
    profile["country_name_en"] = country_info.get("en", "Unknown")
    profile["confidence"] = confidence
    profile["evidence"] = evidence
    profile["detection_source"] = detection_source
    
    return profile


def analyze_x_tweet(tweet_url_or_id, username=None, timeout=15):
    """
    تحليل تغريدة محددة: جلب البيانات + استنتاج موقع المؤلف
    """
    # استخراج username و tweet_id
    if tweet_url_or_id.startswith("http"):
        u, tid = parse_x_url(tweet_url_or_id)
        if u and tid:
            username, tweet_id = u, tid
        else:
            return {"success": False, "error": "رابط تغريدة غير صحيح"}
    else:
        tweet_id = tweet_url_or_id
        if not username:
            return {"success": False, "error": "يجب توفير username مع tweet_id"}
    
    tweet = fetch_x_tweet(username, tweet_id, timeout=timeout)
    if not tweet.get("success"):
        return tweet
    
    # كشف الموقع من author_location (حقل location للمؤلف)
    author_loc = tweet.get("author_location", "")
    country_code, confidence, evidence = detect_country_from_location_field(author_loc)
    detection_source = "حقل موقع المؤلف الرسمي ⭐"
    
    # backup: تحليل نص التغريدة
    if not country_code:
        text = tweet.get("text", "")
        country_code, confidence, ev_list = detect_country_from_text(text)
        evidence = "; ".join(ev_list) if ev_list else "لا دلائل في التغريدة"
        detection_source = "تحليل نص التغريدة"
    
    country_info = X_COUNTRY_MAP.get(country_code, {}) if country_code else {}
    
    tweet["country_code"] = country_code
    tweet["country_flag"] = country_info.get("flag", "❓")
    tweet["country_name_ar"] = country_info.get("ar", "غير محدد")
    tweet["confidence"] = confidence
    tweet["evidence"] = evidence
    tweet["detection_source"] = detection_source
    tweet["language_ar"] = LANGUAGE_NAMES_AR.get(tweet.get("lang"), tweet.get("lang", "غير محدد"))
    
    return tweet


# =====================================================
# Smart Aggregation (لتحليل عدة تغريدات لنفس الحساب)
# =====================================================

def smart_aggregate_account_results(results):
    """
    تجميع ذكي لنتائج عدة تغريدات لنفس الحساب
    يُعطي قراراً واحداً موحداً للموقع
    """
    by_user = {}
    for r in results:
        if not r.get("success"):
            continue
        uid = r.get("author_id") or r.get("user_id")
        if not uid:
            continue
        by_user.setdefault(uid, []).append(r)
    
    aggregated = []
    for uid, items in by_user.items():
        # خذ أول تغريدة كنموذج للحساب
        first = items[0]
        
        # إذا كان لديها موقع رسمي، استخدمه (الأولوية القصوى)
        author_loc = first.get("author_location", "") or first.get("location_field", "")
        if author_loc:
            code, conf, ev = detect_country_from_location_field(author_loc)
            if code:
                country_info = X_COUNTRY_MAP.get(code, {})
                aggregated.append({
                    "user_id": uid,
                    "screen_name": first.get("author_screen_name") or first.get("screen_name"),
                    "name": first.get("author_name") or first.get("name"),
                    "tweet_count": len(items),
                    "country_code": code,
                    "country_flag": country_info.get("flag", "❓"),
                    "country_name_ar": country_info.get("ar", "غير محدد"),
                    "confidence": conf,
                    "decision_method": "حقل الموقع الرسمي ⭐",
                    "evidence": ev,
                    "location_field": author_loc,
                })
                continue
        
        # وإلا، صوت من نصوص التغريدات
        votes = {}
        for it in items:
            cc = it.get("country_code")
            if cc:
                votes[cc] = votes.get(cc, 0) + 1
        
        if votes:
            best = max(votes, key=votes.get)
            total = sum(votes.values())
            ratio = votes[best] / total
            confidence = int(min(50 + ratio * 40, 90))
            country_info = X_COUNTRY_MAP.get(best, {})
            aggregated.append({
                "user_id": uid,
                "screen_name": first.get("author_screen_name") or first.get("screen_name"),
                "name": first.get("author_name") or first.get("name"),
                "tweet_count": len(items),
                "country_code": best,
                "country_flag": country_info.get("flag", "❓"),
                "country_name_ar": country_info.get("ar", "غير محدد"),
                "confidence": confidence,
                "decision_method": f"تصويت {votes[best]}/{total} تغريدات",
                "evidence": ", ".join([f"{X_COUNTRY_MAP.get(c, {}).get('ar', c)}={v}" for c, v in votes.items()]),
                "location_field": "",
            })
        else:
            aggregated.append({
                "user_id": uid,
                "screen_name": first.get("author_screen_name") or first.get("screen_name"),
                "name": first.get("author_name") or first.get("name"),
                "tweet_count": len(items),
                "country_code": None,
                "country_flag": "❓",
                "country_name_ar": "غير محدد",
                "confidence": 0,
                "decision_method": "لا بيانات كافية",
                "evidence": "",
                "location_field": "",
            })
    
    return aggregated


# =====================================================
# Test
# =====================================================

if __name__ == "__main__":
    print("🐦 X Analyzer v3 - اختبار\n")
    
    test_users = [
        "salim_Aljomaili",
        "elonmusk",
        "SaudiMOH",
        "BarackObama",
    ]
    
    for u in test_users:
        print(f"{'='*70}")
        print(f"🔍 @{u}")
        result = analyze_x_account(u)
        if result.get("success"):
            print(f"  📛 الاسم: {result.get('name')}")
            print(f"  🆔 ID: {result.get('user_id')}")
            print(f"  📍 حقل الموقع: \"{result.get('location_field')}\"")
            print(f"  🌍 الدولة المكتشفة: {result.get('country_flag')} {result.get('country_name_ar')}")
            print(f"  🎯 الثقة: {result.get('confidence')}%")
            print(f"  📊 المصدر: {result.get('detection_source')}")
            print(f"  🔎 الدليل: {result.get('evidence')}")
            print(f"  👥 المتابعون: {format_count(result.get('followers'))}")
        else:
            print(f"  ❌ فشل: {result.get('error')}")
        print()


# =====================================================
# Backward Compatibility (aliases للإصدار القديم)
# =====================================================

X_REGION_MAP = X_COUNTRY_MAP
LANGUAGE_NAMES_AR_X = LANGUAGE_NAMES_AR


def aggregate_user_tweets(results, min_confidence=30):
    """
    Wrapper متوافق مع الإصدار القديم - يُرجع dict بـ user_id كمفتاح
    يستخدم حقل location الرسمي إن وُجد، وإلا تصويت
    """
    by_user = {}
    for r in results:
        if not r.get("success") and r.get("status") != "✅ نجح":
            continue
        # استخراج user_id من حقول متعددة
        uid = r.get("author_id") or r.get("user_id") or r.get("user_id_str")
        if not uid:
            continue
        by_user.setdefault(str(uid), []).append(r)
    
    aggregated = {}
    for uid, items in by_user.items():
        first = items[0]
        screen_name = first.get("author_screen_name") or first.get("user_screen_name") or first.get("screen_name", "")
        name = first.get("author_name") or first.get("user_name") or first.get("name", "")
        avatar = first.get("author_avatar") or first.get("user_profile_image") or first.get("avatar_url", "")
        verified = first.get("author_verified") or first.get("user_blue_verified", False)
        verified_type = first.get("user_verified_type") or first.get("verification", "")
        
        # حقل الموقع الرسمي
        loc_field = first.get("author_location") or first.get("location_field", "")
        
        final_region = None
        final_confidence = 0
        final_method = ""
        final_evidence = ""
        
        # 1. الأولوية: حقل الموقع الرسمي
        if loc_field:
            code, conf, ev = detect_country_from_location_field(loc_field)
            if code and conf >= min_confidence:
                final_region = code
                final_confidence = conf
                final_method = "🎯 حقل الموقع الرسمي من X"
                final_evidence = ev
        
        # 2. وإلا، تصويت من نصوص التغريدات
        if not final_region:
            votes = {}
            for it in items:
                cc = it.get("country_code") or it.get("region")
                conf = it.get("confidence") or it.get("region_confidence", 0)
                if cc and conf >= min_confidence:
                    votes[cc] = votes.get(cc, 0) + 1
            
            if votes:
                best = max(votes, key=votes.get)
                total = sum(votes.values())
                ratio = votes[best] / total
                final_confidence = int(min(50 + ratio * 40, 90))
                final_region = best
                final_method = f"🗳️ تصويت ({votes[best]} من {total} تغريدات)"
                final_evidence = ", ".join([
                    f"{X_COUNTRY_MAP.get(c, {}).get('ar', c)}={v}" for c, v in votes.items()
                ])
        
        country_info = X_COUNTRY_MAP.get(final_region, {}) if final_region else {}
        
        # حساب الإحصائيات
        total_likes = sum(it.get("likes", 0) or it.get("favorite_count", 0) for it in items)
        total_replies = sum(it.get("replies", 0) or it.get("conversation_count", 0) for it in items)
        langs = [it.get("lang") for it in items if it.get("lang")]
        dominant_lang = max(set(langs), key=langs.count) if langs else "-"
        dominant_lang_ar = LANGUAGE_NAMES_AR.get(dominant_lang, dominant_lang)
        
        aggregated[str(uid)] = {
            "user_id": uid,
            "user_screen_name": screen_name,
            "user_name": name,
            "user_profile_image": avatar,
            "user_blue_verified": verified,
            "user_verified_type": verified_type,
            "tweet_count": len(items),
            "total_likes": total_likes,
            "total_replies": total_replies,
            "dominant_language": dominant_lang_ar,
            "location_field": loc_field,  # 🎯 الحقل الذهبي
            "final_region": final_region,
            "final_region_flag": country_info.get("flag", ""),
            "final_region_name_ar": country_info.get("ar", ""),
            "final_confidence": final_confidence,
            "final_method": final_method,
            "final_evidence": final_evidence,
        }
    
    return aggregated


def analyze_x_tweet_legacy(url):
    """
    Wrapper متوافق مع التوقيع القديم (يستخدم في app.py)
    يُرجع dict بالحقول القديمة
    """
    result = analyze_x_tweet(url)
    if not result.get("success"):
        return {
            "tweet_url": url,
            "status": "❌ فشل",
            "error": result.get("error", "خطأ غير معروف"),
        }
    
    # تحويل للحقول القديمة المتوقعة
    media = result.get("media", {})
    if isinstance(media, dict):
        all_media = (media.get("photos") or []) + (media.get("videos") or [])
    else:
        all_media = []
    
    media_count = len(all_media)
    media_type = ""
    if all_media:
        first_m = all_media[0]
        media_type = first_m.get("type", "photo")
    
    text = result.get("text", "")
    hashtags = re.findall(r'#(\w+)', text)
    mentions = re.findall(r'@(\w+)', text)
    
    return {
        "tweet_url": result.get("tweet_url"),
        "tweet_id": result.get("tweet_id"),
        "user_id": result.get("author_id"),
        "user_screen_name": result.get("author_screen_name"),
        "user_name": result.get("author_name"),
        "user_profile_image": result.get("author_avatar"),
        "user_blue_verified": result.get("author_verified"),
        "user_verified_type": "",
        "user_location_field": result.get("author_location", ""),  # 🎯 جديد
        "text": text,
        "lang": result.get("lang", ""),
        "lang_name_ar": LANGUAGE_NAMES_AR.get(result.get("lang"), result.get("lang", "")),
        "created_at": result.get("created_at", ""),
        "favorite_count": result.get("likes", 0),
        "conversation_count": result.get("replies", 0),
        "media_count": media_count,
        "media_type": media_type,
        "hashtags": ", ".join(hashtags[:5]),
        "mentions": ", ".join(mentions[:5]),
        "region": result.get("country_code"),
        "region_flag": result.get("country_flag", ""),
        "region_name_ar": result.get("country_name_ar", ""),
        "region_confidence": result.get("confidence", 0),
        "region_evidence": result.get("evidence", ""),
        "region_source": result.get("detection_source", ""),
        "status": "✅ نجح",
        "author_location": result.get("author_location", ""),
        "country_code": result.get("country_code"),
        "confidence": result.get("confidence", 0),
        "likes": result.get("likes", 0),
        "replies": result.get("replies", 0),
        "author_id": result.get("author_id"),
        "author_screen_name": result.get("author_screen_name"),
        "author_name": result.get("author_name"),
        "author_avatar": result.get("author_avatar"),
        "author_verified": result.get("author_verified"),
    }
