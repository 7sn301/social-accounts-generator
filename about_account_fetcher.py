"""
🎯 About Account Fetcher - يجلب بيانات /about من X مباشرة
==========================================================
يستخدم AboutAccountQuery GraphQL endpoint للحصول على:
  ✅ account_based_in: البلد الفعلي حسب X (مثل "United States")
  ✅ location_accurate: True/False — X نفسه يكشف VPN!
  ✅ source: التطبيق المستخدم (مثل "United States App Store")
  ✅ username_changes_count: عدد مرات تغيير اسم المستخدم
  ✅ verified_since: تاريخ التوثيق
  ✅ profile_image_shape: شكل الصورة (Square = حكومي/مؤسسة)

⚠️ يتطلب auth_token + ct0 من cookies المستخدم (تسجيل دخول)
"""
import requests
import json
import re
import time
import threading


GRAPHQL_URL = "https://x.com/i/api/graphql/XRqGa7EeokUU5kppkh13EA/AboutAccountQuery"

# Bearer Token الرسمي لواجهة Twitter Web (ثابت، عام)
DEFAULT_BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3DbjLTczs4TPYjTWnH3tpe9V20"

FEATURES = {
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
}

# Cache
_ABOUT_CACHE = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 1800  # 30 دقيقة


def _cache_get(key):
    with _CACHE_LOCK:
        item = _ABOUT_CACHE.get(key)
        if item and time.time() - item['ts'] < _CACHE_TTL:
            return item['data']
        return None


def _cache_set(key, data):
    with _CACHE_LOCK:
        _ABOUT_CACHE[key] = {'data': data, 'ts': time.time()}


def parse_cookies_string(cookies_str):
    """
    يحول سلسلة cookies إلى dict
    يقبل: "auth_token=...; ct0=...; ..."
    أو: Header String من Cookie-Editor
    """
    if not cookies_str:
        return {}
    cookies = {}
    for part in cookies_str.split(';'):
        part = part.strip()
        if '=' in part:
            k, v = part.split('=', 1)
            cookies[k.strip()] = v.strip()
    return cookies


def fetch_about_account(screen_name, cookies, timeout=15, use_cache=True):
    """
    يجلب بيانات /about لحساب معين
    
    cookies: dict أو string يحتوي على:
        - auth_token (مطلوب)
        - ct0 (مطلوب — CSRF token)
    
    يُرجع dict مع كل الحقول المهمة
    """
    if isinstance(cookies, str):
        cookies = parse_cookies_string(cookies)
    
    if not cookies.get('auth_token') or not cookies.get('ct0'):
        return {
            'success': False,
            'error': 'مطلوب auth_token + ct0 من cookies',
            'help': 'استخدم Cookie-Editor → Export Header String → ألصقه',
        }
    
    cache_key = f"about:{screen_name.lower()}"
    if use_cache:
        cached = _cache_get(cache_key)
        if cached:
            return cached
    
    variables = {"screenName": screen_name}
    params = {
        "variables": json.dumps(variables),
        "features": json.dumps(FEATURES),
    }
    
    headers = {
        "Authorization": f"Bearer {DEFAULT_BEARER}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Referer": f"https://x.com/{screen_name}/about",
        "X-Twitter-Active-User": "yes",
        "X-Twitter-Auth-Type": "OAuth2Session",
        "X-Twitter-Client-Language": "en",
        "X-Csrf-Token": cookies.get('ct0', ''),
        "Content-Type": "application/json",
    }
    
    try:
        r = requests.get(
            GRAPHQL_URL,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
        )
        
        if r.status_code == 401:
            return {
                'success': False,
                'error': 'cookies منتهية أو غير صالحة (401)',
                'help': 'سجل دخول X مرة أخرى وانسخ cookies جديدة',
            }
        
        if r.status_code == 403:
            return {
                'success': False,
                'error': 'محظور (403) - تحقق من ct0',
            }
        
        if r.status_code != 200:
            return {
                'success': False,
                'error': f'HTTP {r.status_code}: {r.text[:200]}',
            }
        
        data = r.json()
        
        # استخرج البيانات
        result_obj = (data.get('data', {})
                      .get('user_result_by_screen_name', {})
                      .get('result', {}))
        
        if not result_obj:
            return {
                'success': False,
                'error': 'لا توجد بيانات للحساب',
                'raw': data,
            }
        
        about = result_obj.get('about_profile', {}) or {}
        
        # legacy info
        legacy = result_obj.get('legacy', {}) or {}
        
        # core info
        core = result_obj.get('core', {}) or {}
        
        result = {
            'success': True,
            # 🎯 المعلومات الذهبية من X مباشرة
            'account_based_in': about.get('account_based_in'),
            'location_accurate': about.get('location_accurate'),  # ⚠️ False = VPN!
            'source': about.get('source'),
            'username_changes_count': about.get('username_changes_count', 0),
            'verified_since_msec': about.get('verified_since_msec'),
            'override_verified_year': about.get('override_verified_year'),
            
            # معلومات إضافية
            'user_id': result_obj.get('rest_id') or core.get('id_str') or legacy.get('id_str'),
            'screen_name': core.get('screen_name') or legacy.get('screen_name') or screen_name,
            'name': core.get('name') or legacy.get('name'),
            'avatar': legacy.get('profile_image_url_https'),
            'profile_image_shape': result_obj.get('profile_image_shape'),
            'is_blue_verified': result_obj.get('is_blue_verified', False),
            'verification': result_obj.get('verification'),
            'created_at': legacy.get('created_at'),
            'affiliate_username': result_obj.get('affiliate_username'),
            'verified_type': about.get('verified_type'),
            
            'raw_about': about,
        }
        
        if use_cache:
            _cache_set(cache_key, result)
        
        return result
    except Exception as e:
        return {'success': False, 'error': f'خطأ: {e}'}


def diagnose_vpn_from_about(about_data):
    """
    تشخيص VPN باستخدام بيانات X الرسمية
    
    🎯 الإشارة الذهبية: location_accurate = False
    """
    if not about_data.get('success'):
        return None
    
    location_accurate = about_data.get('location_accurate')
    account_based_in = about_data.get('account_based_in')
    source = about_data.get('source', '') or ''
    
    indicators = []
    
    # 1. الإشارة المباشرة من X
    if location_accurate is False:
        indicators.append('🚨 X نفسه يقول: location_accurate = False (احتمال VPN قوي)')
        risk_score = 90
        verdict = 'vpn_detected_by_x'
        verdict_ar = '🚨 X اكتشف استخدام VPN/Proxy'
    elif location_accurate is True:
        indicators.append('✅ X يقول: location_accurate = True (الموقع موثوق)')
        risk_score = 0
        verdict = 'verified'
        verdict_ar = '✅ موقع موثوق من X'
    else:
        indicators.append('⚠️ X لم يحدد دقة الموقع')
        risk_score = 30
        verdict = 'unknown'
        verdict_ar = '⚠️ دقة الموقع غير محددة'
    
    # 2. تحقق من تطابق source مع account_based_in
    if account_based_in and source:
        if account_based_in.lower() not in source.lower():
            indicators.append(
                f'⚠️ تناقض: الموقع "{account_based_in}" '
                f'لكن التطبيق من "{source}"'
            )
            if risk_score < 50:
                risk_score = 50
    
    # 3. تغيير اسم المستخدم بكثرة
    changes = about_data.get('username_changes_count', 0)
    if changes >= 5:
        indicators.append(f'⚠️ غيّر اسم المستخدم {changes} مرات (نمط مشبوه)')
        risk_score = max(risk_score, 40)
    elif changes >= 2:
        indicators.append(f'ℹ️ غيّر اسم المستخدم {changes} مرات')
    
    return {
        'verdict': verdict,
        'verdict_ar': verdict_ar,
        'risk_score': risk_score,
        'indicators': indicators,
        'account_based_in': account_based_in,
        'location_accurate': location_accurate,
        'source': source,
        'username_changes': changes,
    }


# ===========================================
# Country name → ISO code
# ===========================================

COUNTRY_NAME_TO_ISO = {
    'united states': 'US', 'usa': 'US', 'america': 'US',
    'united kingdom': 'GB', 'england': 'GB', 'britain': 'GB', 'uk': 'GB', 'scotland': 'GB', 'wales': 'GB',
    'saudi arabia': 'SA', 'kingdom of saudi arabia': 'SA', 'ksa': 'SA',
    'united arab emirates': 'AE', 'uae': 'AE', 'emirates': 'AE',
    'egypt': 'EG',
    'iraq': 'IQ',
    'kuwait': 'KW',
    'qatar': 'QA',
    'bahrain': 'BH',
    'oman': 'OM',
    'yemen': 'YE',
    'jordan': 'JO',
    'lebanon': 'LB',
    'syria': 'SY',
    'palestine': 'PS',
    'morocco': 'MA',
    'algeria': 'DZ',
    'tunisia': 'TN',
    'libya': 'LY',
    'sudan': 'SD',
    'somalia': 'SO',
    'mauritania': 'MR',
    'djibouti': 'DJ',
    'canada': 'CA',
    'australia': 'AU',
    'germany': 'DE',
    'france': 'FR',
    'italy': 'IT',
    'spain': 'ES',
    'netherlands': 'NL',
    'sweden': 'SE',
    'norway': 'NO',
    'denmark': 'DK',
    'finland': 'FI',
    'switzerland': 'CH',
    'belgium': 'BE',
    'austria': 'AT',
    'ireland': 'IE',
    'portugal': 'PT',
    'greece': 'GR',
    'turkey': 'TR', 'türkiye': 'TR',
    'iran': 'IR',
    'pakistan': 'PK',
    'india': 'IN',
    'bangladesh': 'BD',
    'afghanistan': 'AF',
    'china': 'CN',
    'japan': 'JP',
    'south korea': 'KR', 'korea': 'KR',
    'thailand': 'TH',
    'indonesia': 'ID',
    'malaysia': 'MY',
    'singapore': 'SG',
    'philippines': 'PH',
    'vietnam': 'VN',
    'brazil': 'BR',
    'mexico': 'MX',
    'argentina': 'AR',
    'russia': 'RU',
    'ukraine': 'UA',
    'poland': 'PL',
    'israel': 'IL',
    'south africa': 'ZA',
    'nigeria': 'NG',
    'kenya': 'KE',
    'ethiopia': 'ET',
    'new zealand': 'NZ',
}


def country_name_to_iso(name):
    """يحول اسم دولة إلى ISO code"""
    if not name:
        return None
    return COUNTRY_NAME_TO_ISO.get(name.lower().strip())


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    import os
    
    print("🎯 اختبار About Account Fetcher")
    print("="*60)
    
    cookies_str = os.environ.get("X_COOKIES")
    if not cookies_str:
        print("\n⚠️ ضع cookies في X_COOKIES environment variable")
        print("مثال: export X_COOKIES='auth_token=xxx; ct0=yyy'")
        
        # اختبار بدون cookies (للتأكد من syntax فقط)
        result = fetch_about_account("hureyaksa", "")
        print(f"\nبدون cookies: {result}")
    else:
        for username in ['hureyaksa', 'elonmusk', 'salim_Aljomaili']:
            print(f"\n🔍 @{username}")
            result = fetch_about_account(username, cookies_str)
            
            if result.get('success'):
                print(f"  📍 account_based_in: {result.get('account_based_in')}")
                print(f"  🎯 location_accurate: {result.get('location_accurate')}")
                print(f"  📱 source: {result.get('source')}")
                print(f"  🔄 username_changes: {result.get('username_changes_count')}")
                print(f"  🆔 user_id: {result.get('user_id')}")
                print(f"  ✓ blue_verified: {result.get('is_blue_verified')}")
                
                # تشخيص VPN
                diag = diagnose_vpn_from_about(result)
                if diag:
                    print(f"\n  🚨 تشخيص: {diag['verdict_ar']}")
                    print(f"  📊 درجة الخطر: {diag['risk_score']}/100")
                    for ind in diag['indicators']:
                        print(f"    • {ind}")
            else:
                print(f"  ❌ {result.get('error')}")
