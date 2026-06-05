"""
🦅 TikMatrix Pro v1.9.2 - Final Hotfix
═══════════════════════════════════════════════════════════════
4 إصلاحات نهائية:
1. رفع أولوية username_keyword فوق flag_emoji
2. تحسين كشف tunisia في domains (.tn)
3. ضبط ترتيب الفحص (most specific first)
4. حل مشكلة pakistanidrama (pakistan قبل drama)
═══════════════════════════════════════════════════════════════
"""
import sys
sys.path.insert(0, '/home/user/tikmatrix_pro_v19')
from tikmatrix_pro import (
    FetchEngine, DataExtractor, CacheManager, SmartDelayManager,
    LANGUAGE_TO_COUNTRY, BIO_SCRIPT_TO_COUNTRY, CITY_TO_COUNTRY,
    FLAG_EMOJI_TO_COUNTRY, CELEBRITIES_FILE
)
from tikmatrix_pro_v191 import EXPANDED_SUSPICIOUS, TIKTOK_SERVER_COUNTRIES, USERNAME_KEYWORDS
import re
import json
import time

# ═══════════════════════════════════════════════════════════════
# 🔧 الإصلاح #2: TLD Domain → Country (للتعامل مع samira.tn)
# ═══════════════════════════════════════════════════════════════
TLD_TO_COUNTRY = {
    '.tn': 'Tunisia',     '.ma': 'Morocco',    '.dz': 'Algeria',
    '.eg': 'Egypt',       '.sa': 'Saudi Arabia','.ae': 'United Arab Emirates',
    '.kw': 'Kuwait',      '.qa': 'Qatar',      '.bh': 'Bahrain',
    '.om': 'Oman',        '.jo': 'Jordan',     '.lb': 'Lebanon',
    '.iq': 'Iraq',        '.ye': 'Yemen',      '.ly': 'Libya',
    '.ps': 'Palestine',   '.sd': 'Sudan',      '.so': 'Somalia',
    '.tr': 'Turkey',      '.ir': 'Iran',       '.kr': 'South Korea',
    '.jp': 'Japan',       '.cn': 'China',      '.tw': 'Taiwan',
    '.hk': 'Hong Kong',   '.sg': 'Singapore',  '.th': 'Thailand',
    '.vn': 'Vietnam',     '.id': 'Indonesia',  '.my': 'Malaysia',
    '.ph': 'Philippines', '.in': 'India',      '.pk': 'Pakistan',
    '.bd': 'Bangladesh',  '.lk': 'Sri Lanka',  '.np': 'Nepal',
    '.uk': 'United Kingdom', '.gb': 'United Kingdom',
    '.us': 'United States', '.ca': 'Canada',   '.mx': 'Mexico',
    '.fr': 'France',      '.de': 'Germany',    '.es': 'Spain',
    '.it': 'Italy',       '.nl': 'Netherlands','.pt': 'Portugal',
    '.ru': 'Russia',      '.pl': 'Poland',     '.ch': 'Switzerland',
    '.br': 'Brazil',      '.ar': 'Argentina',  '.co': 'Colombia',
    '.cl': 'Chile',       '.pe': 'Peru',       '.ve': 'Venezuela',
    '.ng': 'Nigeria',     '.ke': 'Kenya',      '.za': 'South Africa',
    '.gh': 'Ghana',       '.tz': 'Tanzania',   '.et': 'Ethiopia',
    '.au': 'Australia',   '.nz': 'New Zealand',
}

# ═══════════════════════════════════════════════════════════════
# 🔧 الإصلاح #3: أولوية الكلمات (الأطول أولاً لتجنب التضارب)
# ═══════════════════════════════════════════════════════════════
USERNAME_KEYWORDS_SORTED = sorted(USERNAME_KEYWORDS.items(), key=lambda x: -len(x[0]))


class FinalCorrector:
    """
    أولوية التصحيح النهائية v1.9.2:
    1. Celebrity Database
    2. TLD Domain (.tn → Tunisia)
    3. Username Keyword (بترتيب الطول الأكبر)
    4. BIO Flag Emoji
    5. BIO Script
    6. BIO City
    7. Language Override
    8. Suspicious Filter
    """
    
    def __init__(self, celebrities_file=CELEBRITIES_FILE):
        self.celebrities = self._load(celebrities_file)
    
    def _load(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f).get('celebrities', {})
        except Exception:
            return {}
    
    def correct(self, username, data):
        original = data.get('country')
        language = (data.get('language') or '').lower()[:2]
        bio = data.get('bio', '') or ''
        nickname = data.get('nickname', '') or ''
        text_lower = f"{bio} {nickname}".lower()
        username_lower = username.lower()
        
        log = []
        
        # ═══ 1. Celebrity DB ═══
        celeb = self.celebrities.get(username_lower)
        if celeb:
            log.append(f"✅ مشهور: {celeb['name']} → {celeb['country']}")
            return self._build(celeb['country'], 'celebrity_database', original, log, 98)
        
        # ═══ 2. TLD Domain (جديد - الإصلاح #2) ═══
        for tld, tld_country in TLD_TO_COUNTRY.items():
            if username_lower.endswith(tld):
                log.append(f"🌐 TLD: {tld} → {tld_country}")
                return self._build(tld_country, 'tld_domain', original, log, 90)
        
        # ═══ 3. Username Keyword (مرتّب طول أكبر أولاً - الإصلاح #1+4) ═══
        for keyword, kw_country in USERNAME_KEYWORDS_SORTED:
            if keyword in username_lower:
                if not original or original != kw_country:
                    log.append(f"🔤 username: '{keyword}' → {kw_country}")
                    confidence = 95 if not original else 88
                    return self._build(kw_country, 'username_keyword', original, log, confidence)
                else:
                    log.append(f"✓ تأكيد: '{keyword}' = {kw_country}")
                    return self._build(kw_country, 'username_confirmed', original, log, 96)
        
        # ═══ 4. BIO Flag Emoji ═══
        for flag, c in FLAG_EMOJI_TO_COUNTRY.items():
            if flag in bio or flag in nickname:
                if c != original:
                    log.append(f"🚩 BIO: {flag} → {c}")
                    return self._build(c, 'bio_flag', original, log, 92)
        
        # ═══ 5. BIO Script ═══
        for pattern, c, name in BIO_SCRIPT_TO_COUNTRY:
            if re.search(pattern, bio + nickname):
                if original != c:
                    log.append(f"🔤 {name} → {c}")
                    return self._build(c, 'bio_script', original, log, 88)
        
        # ═══ 6. BIO City ═══
        for city, c in CITY_TO_COUNTRY.items():
            if city in text_lower.replace(' ', '').replace(',', ''):
                if original != c:
                    log.append(f"🏙️ {city} → {c}")
                    return self._build(c, 'bio_city', original, log, 80)
        
        # ═══ 7. Language Override ═══
        if language and language in LANGUAGE_TO_COUNTRY:
            primary, valid = LANGUAGE_TO_COUNTRY[language]
            if original and original not in valid:
                log.append(f"⚠️ لغة {language} ↔ {original} → {primary}")
                return self._build(primary, 'language_override', original, log, 72)
            if original in TIKTOK_SERVER_COUNTRIES and language != 'en':
                log.append(f"⚠️ سيرفر TikTok: {original} (lang {language}) → {primary}")
                return self._build(primary, 'tiktok_server_filter', original, log, 70)
        
        # ═══ 8. Suspicious Filter ═══
        if original in EXPANDED_SUSPICIOUS:
            if language in LANGUAGE_TO_COUNTRY:
                primary, valid = LANGUAGE_TO_COUNTRY[language]
                if original not in valid:
                    log.append(f"⚠️ مشبوهة: {original} → {primary}")
                    return self._build(primary, 'suspicious_filter', original, log, 65)
        
        # افتراضي
        if original:
            log.append(f"ℹ️ قبول TikMatrix: {original}")
        return self._build(original, data.get('country_source', 'tikmatrix'), original, log, 75)
    
    def _build(self, country, source, original, log, confidence):
        flag = ''
        for emoji, c in FLAG_EMOJI_TO_COUNTRY.items():
            if c == country:
                flag = emoji
                break
        return {
            'country': country, 'flag': flag, 'confidence': confidence,
            'source': source, 'original_tikmatrix': original, 'corrections': log,
        }


class TikMatrixProV192:
    VERSION = "1.9.2"
    
    def __init__(self):
        self.cache = CacheManager()
        self.delay_mgr = SmartDelayManager()
        self.fetcher = FetchEngine()
        self.extractor = DataExtractor()
        self.corrector = FinalCorrector()
    
    def lookup(self, username, use_cache=True, apply_delay=True):
        username = self._sanitize(username)
        
        if use_cache:
            cached = self.cache.get(username)
            if cached:
                return cached
        
        fetch = self.fetcher.fetch(username)
        if not fetch['success']:
            return {'success': False, 'username': username, 'error': 'فشل الجلب'}
        
        raw = self.extractor.extract(fetch['content'])
        correction = self.corrector.correct(username, raw)
        
        result = {
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
            'verified': raw.get('verified', False),
            'confidence': correction['confidence'],
            'corrections_log': correction['corrections'],
            'proxy_used': fetch['proxy'],
            'fetch_time': fetch['time'],
        }
        
        self.cache.set(username, result)
        if apply_delay:
            self.delay_mgr.wait()
        return result
    
    def _sanitize(self, username):
        username = username.strip().lower().lstrip('@')
        username = re.sub(r'https?://(?:www\.)?tiktok\.com/@?', '', username)
        return username.split('?')[0].split('/')[0]


if __name__ == "__main__":
    pro = TikMatrixProV192()
    print(f"🦅 v{pro.VERSION} جاهز")
