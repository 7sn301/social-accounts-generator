"""
🦅 TikMatrix Pro v1.9 - محرك الاستخراج والتصحيح الذكي
═══════════════════════════════════════════════════════════════
المعتمَد من لجنة بَصِير (7/7 إجماع) - 35 متطلب
التاريخ: 2026-06-05
═══════════════════════════════════════════════════════════════
"""
import requests
import re
import json
import time
import sqlite3
import hashlib
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# 📋 المتطلب #34: المسارات والإعدادات
# ═══════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
CACHE_DB = BASE_DIR / 'tikmatrix_cache.db'
CELEBRITIES_FILE = DATA_DIR / 'celebrities.json'

# ═══════════════════════════════════════════════════════════════
# 🌐 المتطلب #1-5: منظومة البروكسيات
# ═══════════════════════════════════════════════════════════════
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]

PROXY_CHAIN = [
    {'name': 'jina',       'url': 'https://r.jina.ai/',                  'timeout': 15, 'priority': 1},
    {'name': 'corsproxy',  'url': 'https://corsproxy.io/?',              'timeout': 12, 'priority': 2},
    {'name': 'allorigins', 'url': 'https://api.allorigins.win/raw?url=', 'timeout': 15, 'priority': 3},
]

# ═══════════════════════════════════════════════════════════════
# 🎯 المتطلب #1-2: Patterns الصحيحة المُكتشفة من HTML الفعلي
# ═══════════════════════════════════════════════════════════════
PATTERNS = {
    'country_flag':    r'(?:🇺🇸|🇬🇧|🇰🇷|🇯🇵|🇨🇳|🇮🇳|🇧🇷|🇿🇦|🇦🇺|🇪🇬|🇸🇦|🇦🇪|🇰🇼|🇶🇦|🇧🇭|🇴🇲|🇯🇴|🇱🇧|🇮🇶|🇾🇪|🇵🇸|🇲🇦|🇩🇿|🇹🇳|🇱🇾|🇸🇩|🇸🇴|🇹🇷|🇮🇷|🇮🇹|🇫🇷|🇩🇪|🇪🇸|🇳🇱|🇷🇺|🇨🇦|🇲🇽|🇦🇷|🇨🇴|🇨🇱|🇵🇪|🇻🇪|🇳🇬|🇰🇪|🇪🇹|🇬🇭|🇿🇼|🇹🇭|🇻🇳|🇮🇩|🇲🇾|🇵🇭|🇸🇬|🇵🇰|🇧🇩|🇱🇰|🇳🇵|🇰🇿|🇺🇿|🇦🇿|🇦🇲|🇬🇪|🇲🇳|🇳🇿|🇵🇹|🇵🇷|🇹🇿|🇲🇿)([A-Za-z][A-Za-z\s&\.\(\)\']+?)(?:\n|🌐)',
    'country_globe':   r'🌍([A-Za-z][A-Za-z\s&\.\(\)\']+?)(?:\n|🌐|<|$)',
    'language':        r'🌐([a-zA-Z]{2,7})',
    'followers':       r'([\d,]+)\s*👥\s*Followers',
    'following':       r'([\d,]+)\s*➕\s*Following',
    'hearts':          r'([\d,]+)\s*❤️\s*Hearts',
    'videos':          r'([\d,]+)\s*🎬\s*Videos',
    'friends':         r'([\d,]+)\s*👫\s*Friends',
    'user_id':         r'User ID:\s*(\d+)',
    'sec_uid':         r'SecUID:\s*([A-Za-z0-9_-]+)',
    'created':         r'Account Created:\s*([^\n]+)',
    'nickname':        r'##\s*([^\n#]+)\n\n@',
    'verified':        r'(verified|Verified|✓|☑)',
    'avatar':          r'!\[Image[^\]]*\]\((https://[^)]+)\)',
}

# ═══════════════════════════════════════════════════════════════
# 🌍 المتطلب #6: خريطة اللغة → الدولة (20+ لغة)
# ═══════════════════════════════════════════════════════════════
LANGUAGE_TO_COUNTRY = {
    'ar': ('Arab Region', ['Saudi Arabia', 'United Arab Emirates', 'Egypt', 'Kuwait',
                            'Qatar', 'Bahrain', 'Oman', 'Jordan', 'Lebanon', 'Iraq',
                            'Yemen', 'Palestine', 'Morocco', 'Algeria', 'Tunisia',
                            'Libya', 'Sudan', 'Somalia']),
    'ko': ('South Korea', ['South Korea', 'Korea']),
    'ja': ('Japan',       ['Japan']),
    'zh': ('China',       ['China', 'Taiwan', 'Hong Kong', 'Singapore']),
    'th': ('Thailand',    ['Thailand']),
    'vi': ('Vietnam',     ['Vietnam']),
    'id': ('Indonesia',   ['Indonesia']),
    'ms': ('Malaysia',    ['Malaysia']),
    'tl': ('Philippines', ['Philippines']),
    'tr': ('Turkey',      ['Turkey']),
    'fa': ('Iran',        ['Iran']),
    'hi': ('India',       ['India']),
    'ur': ('Pakistan',    ['Pakistan', 'India']),
    'bn': ('Bangladesh',  ['Bangladesh', 'India']),
    'pt': ('Brazil',      ['Brazil', 'Portugal']),
    'es': ('Spain',       ['Spain', 'Mexico', 'Argentina', 'Colombia', 'Chile',
                           'Peru', 'Venezuela', 'Ecuador', 'Cuba']),
    'fr': ('France',      ['France', 'Belgium', 'Canada', 'Switzerland',
                           'Senegal', "Côte d'Ivoire", 'Morocco', 'Algeria']),
    'de': ('Germany',     ['Germany', 'Austria', 'Switzerland']),
    'it': ('Italy',       ['Italy', 'Switzerland']),
    'ru': ('Russia',      ['Russia', 'Kazakhstan', 'Belarus', 'Ukraine']),
    'nl': ('Netherlands', ['Netherlands', 'Belgium']),
    'pl': ('Poland',      ['Poland']),
    'el': ('Greece',      ['Greece', 'Cyprus']),
    'he': ('Israel',      ['Israel']),
    'sw': ('Tanzania',    ['Tanzania', 'Kenya']),
}

# ═══════════════════════════════════════════════════════════════
# 🔤 المتطلب #7: خريطة النصوص غير اللاتينية → الدولة
# ═══════════════════════════════════════════════════════════════
BIO_SCRIPT_TO_COUNTRY = [
    (r'[\uAC00-\uD7AF]',  'South Korea', 'Hangul (한글)'),
    (r'[\u3040-\u309F]',  'Japan',       'Hiragana (ひらがな)'),
    (r'[\u30A0-\u30FF]',  'Japan',       'Katakana (カタカナ)'),
    (r'[\u4E00-\u9FFF]',  'China',       'Chinese (中文)'),
    (r'[\u0E00-\u0E7F]',  'Thailand',    'Thai (ภาษาไทย)'),
    (r'[\u0900-\u097F]',  'India',       'Devanagari (हिन्दी)'),
    (r'[\u0980-\u09FF]',  'Bangladesh',  'Bengali (বাংলা)'),
    (r'[\u05D0-\u05EA]',  'Israel',      'Hebrew (עברית)'),
]

# ═══════════════════════════════════════════════════════════════
# 🏙️ المتطلب #8: خريطة المدن → الدولة (50+ مدينة)
# ═══════════════════════════════════════════════════════════════
CITY_TO_COUNTRY = {
    'dubai': 'United Arab Emirates', 'abudhabi': 'United Arab Emirates',
    'riyadh': 'Saudi Arabia', 'jeddah': 'Saudi Arabia', 'mecca': 'Saudi Arabia',
    'cairo': 'Egypt', 'alexandria': 'Egypt',
    'kuwait': 'Kuwait', 'doha': 'Qatar', 'manama': 'Bahrain', 'muscat': 'Oman',
    'amman': 'Jordan', 'beirut': 'Lebanon', 'baghdad': 'Iraq', 'sanaa': 'Yemen',
    'casablanca': 'Morocco', 'rabat': 'Morocco', 'algiers': 'Algeria', 'tunis': 'Tunisia',
    'seoul': 'South Korea', 'busan': 'South Korea',
    'tokyo': 'Japan', 'osaka': 'Japan', 'kyoto': 'Japan',
    'beijing': 'China', 'shanghai': 'China', 'shenzhen': 'China',
    'taipei': 'Taiwan', 'hongkong': 'Hong Kong', 'singapore': 'Singapore',
    'bangkok': 'Thailand', 'hanoi': 'Vietnam', 'saigon': 'Vietnam', 'hcmc': 'Vietnam',
    'jakarta': 'Indonesia', 'bali': 'Indonesia',
    'kualalumpur': 'Malaysia', 'manila': 'Philippines',
    'mumbai': 'India', 'delhi': 'India', 'bangalore': 'India', 'kolkata': 'India',
    'karachi': 'Pakistan', 'islamabad': 'Pakistan', 'lahore': 'Pakistan',
    'dhaka': 'Bangladesh',
    'london': 'United Kingdom', 'manchester': 'United Kingdom',
    'paris': 'France', 'lyon': 'France', 'marseille': 'France',
    'berlin': 'Germany', 'munich': 'Germany',
    'rome': 'Italy', 'milan': 'Italy', 'naples': 'Italy',
    'madrid': 'Spain', 'barcelona': 'Spain',
    'amsterdam': 'Netherlands', 'istanbul': 'Turkey', 'ankara': 'Turkey',
    'moscow': 'Russia', 'lisbon': 'Portugal',
    'newyork': 'United States', 'losangeles': 'United States', 'la': 'United States',
    'miami': 'United States', 'chicago': 'United States',
    'toronto': 'Canada', 'vancouver': 'Canada', 'montreal': 'Canada',
    'mexicocity': 'Mexico', 'cdmx': 'Mexico',
    'saopaulo': 'Brazil', 'rio': 'Brazil', 'brasilia': 'Brazil',
    'buenosaires': 'Argentina', 'bogota': 'Colombia', 'medellin': 'Colombia',
    'santiago': 'Chile', 'lima': 'Peru', 'caracas': 'Venezuela',
    'lagos': 'Nigeria', 'abuja': 'Nigeria', 'johannesburg': 'South Africa',
    'capetown': 'South Africa', 'nairobi': 'Kenya', 'accra': 'Ghana',
    'addisababa': 'Ethiopia', 'darussalam': 'Tanzania',
    'sydney': 'Australia', 'melbourne': 'Australia', 'brisbane': 'Australia',
    'auckland': 'New Zealand', 'wellington': 'New Zealand',
}

# ═══════════════════════════════════════════════════════════════
# 🚩 المتطلب #9: خريطة Emoji الأعلام → الدولة
# ═══════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════
# ⚠️ المتطلب #11: قائمة الدول المشبوهة
# ═══════════════════════════════════════════════════════════════
SUSPICIOUS_COUNTRIES = {
    'Turks and Caicos Islands', 'Norway', 'Sweden',
    'Sri Lanka', 'Finland', 'Puerto Rico',
}

# ═══════════════════════════════════════════════════════════════
# 💾 المتطلب #19-22: SQLite Cache
# ═══════════════════════════════════════════════════════════════
class CacheManager:
    """مدير Cache مع TTL = 1 ساعة"""
    
    def __init__(self, db_path=CACHE_DB):
        self.db_path = str(db_path)
        self._init_db()
        self.hits = 0
        self.misses = 0
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                username TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    
    def get(self, username, ttl=3600):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            'SELECT data, timestamp FROM cache WHERE username = ?',
            (username.lower(),)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data_str, ts = row
            if time.time() - ts < ttl:
                self.hits += 1
                data = json.loads(data_str)
                data['_from_cache'] = True
                return data
        
        self.misses += 1
        return None
    
    def set(self, username, data):
        conn = sqlite3.connect(self.db_path)
        # تنظيف البيانات قبل الحفظ
        clean_data = {k: v for k, v in data.items() if not k.startswith('_')}
        conn.execute(
            'INSERT OR REPLACE INTO cache (username, data, timestamp) VALUES (?, ?, ?)',
            (username.lower(), json.dumps(clean_data, ensure_ascii=False), time.time())
        )
        conn.commit()
        conn.close()
    
    def cleanup_expired(self, ttl=86400):
        """حذف cache التالف كل 24 ساعة"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM cache WHERE timestamp < ?', (time.time() - ttl,))
        conn.commit()
        conn.close()
    
    def stats(self):
        total = self.hits + self.misses
        rate = (self.hits / total * 100) if total > 0 else 0
        return {'hits': self.hits, 'misses': self.misses, 'hit_rate': round(rate, 1)}


# ═══════════════════════════════════════════════════════════════
# 🌐 المتطلب #24-28: نظام التأخير الذكي ضد الحجب
# ═══════════════════════════════════════════════════════════════
class SmartDelayManager:
    """مدير التأخير التصاعدي - مُختبَر على 24 حساب بدون حجب"""
    
    def __init__(self):
        self.consecutive = 0
        self.logs = []
    
    def get_delay(self):
        if self.consecutive < 5:   return 3.0
        elif self.consecutive < 10: return 4.0
        elif self.consecutive < 15: return 5.0
        else:                        return 6.0
    
    def wait(self):
        delay = self.get_delay()
        self.logs.append(delay)
        time.sleep(delay)
        self.consecutive += 1
        return delay
    
    def reset(self):
        self.consecutive = 0


# ═══════════════════════════════════════════════════════════════
# 🧠 المتطلب #1-5: محرك الجلب الذكي
# ═══════════════════════════════════════════════════════════════
class FetchEngine:
    """محرك جلب البيانات من TikMatrix عبر سلسلة بروكسيات"""
    
    def __init__(self):
        self.proxies = PROXY_CHAIN
        self.failed_logs = []
    
    def fetch(self, username):
        target = f"https://user.tikmatrix.com/?username={username}"
        
        for proxy in self.proxies:
            url = proxy['url'] + target
            user_agent = random.choice(USER_AGENTS)
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml',
                'X-Return-Format': 'markdown' if proxy['name'] == 'jina' else None,
            }
            headers = {k: v for k, v in headers.items() if v}
            
            try:
                start = time.time()
                r = requests.get(url, headers=headers, timeout=proxy['timeout'])
                elapsed = time.time() - start
                
                if r.status_code == 200 and len(r.text) > 1000:
                    return {
                        'success': True,
                        'content': r.text,
                        'proxy': proxy['name'],
                        'time': round(elapsed, 2),
                    }
                else:
                    self.failed_logs.append({
                        'username': username,
                        'proxy': proxy['name'],
                        'status': r.status_code,
                        'time': datetime.now().isoformat(),
                    })
            except Exception as e:
                self.failed_logs.append({
                    'username': username,
                    'proxy': proxy['name'],
                    'error': str(e)[:100],
                    'time': datetime.now().isoformat(),
                })
                continue
        
        return {'success': False, 'content': None, 'proxy': None, 'time': 0}


# ═══════════════════════════════════════════════════════════════
# 📊 المتطلب #1-5: استخراج البيانات
# ═══════════════════════════════════════════════════════════════
class DataExtractor:
    """مستخرج 12+ حقل من محتوى TikMatrix"""
    
    def extract(self, content):
        if not content:
            return {}
        
        data = {}
        
        # 1. الدولة (محاولة Flag أولاً)
        m = re.search(PATTERNS['country_flag'], content)
        if m:
            country = self._clean(m.group(1))
            if country and 2 < len(country) < 50:
                data['country'] = country
                data['country_source'] = 'flag_emoji'
        else:
            m = re.search(PATTERNS['country_globe'], content)
            if m:
                country = self._clean(m.group(1))
                if country and 2 < len(country) < 50:
                    data['country'] = country
                    data['country_source'] = 'globe_emoji'
        
        # 2. باقي الحقول
        text_fields = ['language', 'user_id', 'sec_uid', 'created', 'nickname', 'avatar']
        for key in text_fields:
            if key in PATTERNS:
                m = re.search(PATTERNS[key], content)
                if m:
                    data[key] = self._clean(m.group(1))
        
        # 3. الأرقام
        num_fields = ['followers', 'following', 'hearts', 'videos', 'friends']
        for key in num_fields:
            m = re.search(PATTERNS[key], content)
            if m:
                value = m.group(1).replace(',', '').strip()
                if value.isdigit():
                    data[key] = int(value)
        
        # 4. التحقق Verified
        data['verified'] = bool(re.search(PATTERNS['verified'], content))
        
        # 5. استخراج BIO (بين الإحصائيات والروابط)
        bio_match = re.search(r'🌐[a-z]{2,7}\n\n(?:\[[^\]]+\]\([^)]+\))*\n*([^\n\[]+)', content)
        if bio_match:
            bio = bio_match.group(1).strip()
            if bio and len(bio) < 500:
                data['bio'] = bio
        
        return data
    
    def _clean(self, value):
        """تنظيف القيم من الفوضى"""
        if not value:
            return None
        value = re.sub(r'\*+', '', value)
        value = re.sub(r'\s+', ' ', value)
        return value.strip()


# ═══════════════════════════════════════════════════════════════
# 🎯 المتطلب #6-13: طبقة التصحيح الذكي
# ═══════════════════════════════════════════════════════════════
class CountryCorrector:
    """
    أولوية التصحيح المعتمدة:
    1. Celebrity Database (الأعلى)
    2. BIO Flag Emoji
    3. BIO Script (Hangul, Kanji, ...)
    4. BIO City Name
    5. Language Detection
    6. TikMatrix Original (الأدنى)
    """
    
    def __init__(self, celebrities_file=CELEBRITIES_FILE):
        self.celebrities = self._load_celebrities(celebrities_file)
    
    def _load_celebrities(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f).get('celebrities', {})
        except Exception:
            return {}
    
    def correct(self, username, data):
        """تطبيق منطق التصحيح حسب الأولوية"""
        original_country = data.get('country')
        language = data.get('language', '')
        bio = data.get('bio', '')
        nickname = data.get('nickname', '')
        text_to_scan = f"{bio} {nickname}".lower()
        
        correction_log = []
        confidence = 100
        corrected_country = original_country
        correction_source = data.get('country_source', 'tikmatrix')
        
        # ═══ الأولوية 1: Celebrity Database ═══
        celeb = self.celebrities.get(username.lower())
        if celeb:
            corrected_country = celeb['country']
            correction_source = 'celebrity_database'
            correction_log.append(f"✅ مشهور معروف: {celeb['name']} → {celeb['country']}")
            confidence = 98
            return {
                'country': corrected_country,
                'flag': celeb.get('flag', ''),
                'confidence': confidence,
                'source': correction_source,
                'original_tikmatrix': original_country,
                'corrections': correction_log,
            }
        
        # ═══ الأولوية 2: BIO Flag Emoji ═══
        for flag_emoji, country in FLAG_EMOJI_TO_COUNTRY.items():
            if flag_emoji in bio or flag_emoji in nickname:
                if country != original_country:
                    correction_log.append(f"🚩 علم في BIO: {flag_emoji} → {country}")
                    corrected_country = country
                    correction_source = 'bio_flag'
                    confidence = 92
                    break
        
        # ═══ الأولوية 3: BIO Script Detection ═══
        if correction_source == data.get('country_source', 'tikmatrix'):
            for pattern, country, script_name in BIO_SCRIPT_TO_COUNTRY:
                if re.search(pattern, bio + nickname):
                    if original_country != country:
                        correction_log.append(f"🔤 نص {script_name} → {country}")
                        corrected_country = country
                        correction_source = 'bio_script'
                        confidence = 88
                        break
        
        # ═══ الأولوية 4: City Name ═══
        if correction_source == data.get('country_source', 'tikmatrix'):
            for city, country in CITY_TO_COUNTRY.items():
                if city in text_to_scan.replace(' ', '').replace(',', ''):
                    if original_country != country:
                        correction_log.append(f"🏙️ مدينة {city} → {country}")
                        corrected_country = country
                        correction_source = 'bio_city'
                        confidence = 80
                        break
        
        # ═══ الأولوية 5: Language Detection ═══
        if correction_source == data.get('country_source', 'tikmatrix') and language:
            lang_code = language[:2].lower()
            if lang_code in LANGUAGE_TO_COUNTRY:
                primary, valid_countries = LANGUAGE_TO_COUNTRY[lang_code]
                if original_country not in valid_countries and original_country in SUSPICIOUS_COUNTRIES:
                    correction_log.append(f"🗣️ اللغة {language} → {primary}")
                    corrected_country = primary
                    correction_source = 'language'
                    confidence = 70
                elif lang_code == 'pt' and original_country == 'United States':
                    # حالة خاصة: pt + US = البرازيل غالباً (مثل shakira خطأ)
                    pass  # احتفظ بالأصلي
        
        # ═══ المتطلب #11: رفض الدول المشبوهة ═══
        if corrected_country in SUSPICIOUS_COUNTRIES:
            lang_code = language[:2].lower() if language else ''
            if lang_code in LANGUAGE_TO_COUNTRY:
                primary, valid = LANGUAGE_TO_COUNTRY[lang_code]
                if corrected_country not in valid:
                    correction_log.append(f"⚠️ دولة مشبوهة: {corrected_country} (اللغة {language}) → {primary}")
                    corrected_country = primary
                    correction_source = 'suspicious_filter'
                    confidence = 65
        
        # ═══ الحصول على Flag ═══
        flag = ''
        for emoji, country in FLAG_EMOJI_TO_COUNTRY.items():
            if country == corrected_country:
                flag = emoji
                break
        
        return {
            'country': corrected_country,
            'flag': flag,
            'confidence': confidence,
            'source': correction_source,
            'original_tikmatrix': original_country,
            'corrections': correction_log,
        }


# ═══════════════════════════════════════════════════════════════
# 🦅 المحرك الرئيسي - TikMatrix Pro v1.9
# ═══════════════════════════════════════════════════════════════
class TikMatrixPro:
    """المحرك الكامل - يدمج كل المكوّنات"""
    
    VERSION = "1.9.0"
    
    def __init__(self):
        self.cache = CacheManager()
        self.delay_mgr = SmartDelayManager()
        self.fetcher = FetchEngine()
        self.extractor = DataExtractor()
        self.corrector = CountryCorrector()
    
    def lookup(self, username, use_cache=True, apply_delay=True):
        """البحث عن حساب مع كل طبقات الذكاء"""
        username = self._sanitize(username)
        
        # 1. تحقق من Cache
        if use_cache:
            cached = self.cache.get(username)
            if cached:
                return cached
        
        # 2. جلب البيانات
        fetch_result = self.fetcher.fetch(username)
        if not fetch_result['success']:
            return {
                'success': False,
                'username': username,
                'error': 'فشل الجلب من كل البروكسيات',
            }
        
        # 3. استخراج البيانات
        raw_data = self.extractor.extract(fetch_result['content'])
        
        # 4. تطبيق التصحيح
        correction = self.corrector.correct(username, raw_data)
        
        # 5. بناء النتيجة النهائية
        result = {
            'success': True,
            'username': username,
            'nickname': raw_data.get('nickname'),
            'country': correction['country'],
            'country_flag': correction['flag'],
            'country_source': correction['source'],
            'country_original': correction['original_tikmatrix'],
            'language': raw_data.get('language'),
            'followers': raw_data.get('followers', 0),
            'following': raw_data.get('following', 0),
            'hearts': raw_data.get('hearts', 0),
            'videos': raw_data.get('videos', 0),
            'friends': raw_data.get('friends', 0),
            'user_id': raw_data.get('user_id'),
            'sec_uid': raw_data.get('sec_uid'),
            'created': raw_data.get('created'),
            'bio': raw_data.get('bio'),
            'avatar': raw_data.get('avatar'),
            'verified': raw_data.get('verified', False),
            'confidence': correction['confidence'],
            'corrections_log': correction['corrections'],
            'proxy_used': fetch_result['proxy'],
            'fetch_time': fetch_result['time'],
        }
        
        # 6. حفظ في Cache
        self.cache.set(username, result)
        
        # 7. تطبيق التأخير
        if apply_delay:
            self.delay_mgr.wait()
        
        return result
    
    def _sanitize(self, username):
        """تنظيف اسم المستخدم"""
        username = username.strip().lower()
        username = username.lstrip('@')
        username = re.sub(r'https?://(?:www\.)?tiktok\.com/@?', '', username)
        username = username.split('?')[0].split('/')[0]
        return username
    
    def get_stats(self):
        """إحصائيات شاملة"""
        return {
            'version': self.VERSION,
            'cache_stats': self.cache.stats(),
            'celebrities_loaded': len(self.corrector.celebrities),
            'languages_supported': len(LANGUAGE_TO_COUNTRY),
            'cities_supported': len(CITY_TO_COUNTRY),
            'flags_supported': len(FLAG_EMOJI_TO_COUNTRY),
        }


# ═══════════════════════════════════════════════════════════════
# 🚀 نقطة الاختبار
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    pro = TikMatrixPro()
    print(f"🦅 TikMatrix Pro v{pro.VERSION}")
    print(f"📊 الإحصائيات: {pro.get_stats()}")
