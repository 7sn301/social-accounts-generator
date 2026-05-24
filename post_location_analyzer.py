"""
🌍 Post Location Analyzer v2 - تحليل موقع المنشور بدقة عالية
==============================================================
تحسينات v2:
  ✅ Prompt مبتكر يستخرج أي إشارة جغرافية حتى من صور بسيطة
  ✅ تحليل متعدد الجولات (3 محاولات بـ prompts مختلفة)
  ✅ OCR ذكي لاستخراج نصوص من الصور (شعارات، لافتات)
  ✅ تحليل ملصقات ولباس وألوان مميزة
  ✅ مقارنة الصورة مع موقع الحساب (دليل تأكيد/نفي)
  ✅ عرض كل النتائج حتى عند الفشل في تحديد دولة
  ✅ debug info مفصلة عند الفشل
"""
import requests
import json
import re
import io
import os
import time
from datetime import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# =====================================================
# Prompts متعددة (طبقات تحليل)
# =====================================================

# Prompt 1: تحليل عميق شامل
DEEP_PROMPT = """أنت محقق جغرافي خبير في تحديد المواقع من الصور. حلل هذه الصورة بدقة عالية لاستخراج أي إشارة جغرافية ممكنة.

🔍 افحص بالترتيب التالي (لا تتخطى أي خطوة):

**1. النصوص واللافتات (الأهم!):**
   - اقرأ كل النصوص المرئية، حتى الصغيرة منها
   - حدد لغة كل نص (عربية/إنجليزية/فارسية/تركية...)
   - شعارات شركات أو مؤسسات (محلية أم عالمية؟)
   - أرقام هواتف (مفاتيح دول)
   - عناوين بريدية أو أسماء شوارع

**2. الأشخاص:**
   - الملابس (شماغ خليجي/ثوب سعودي/زي أوروبي/بدلة عمل/زي عسكري؟)
   - الإكسسوارات (عقال، كوفية، عمامة، حجاب)
   - السمات الجسدية الواضحة

**3. البيئة المحيطة:**
   - الطقس (صحراء/ثلج/استوائي/معتدل)
   - الإضاءة (شمس قوية/معتدلة/غائم)
   - الغطاء النباتي (نخيل/أرز/بلوط/زيتون)

**4. المباني والمعمار:**
   - نمط البناء (إسلامي/أوروبي/آسيوي/أمريكي)
   - مواد البناء (طين/حجر/زجاج/بيتون)
   - معالم سياحية مشهورة

**5. السيارات والبنية التحتية:**
   - شكل ولون لوحات السيارات
   - نوع وعلامة السيارات
   - علامات الطرق وإشارات المرور

**6. ألوان مميزة:**
   - علم دولة في الخلفية
   - ألوان تقليدية لبلد معين
   - زخارف مميزة

⚡ مهم: حتى لو رأيت إشارة ضعيفة، اذكرها. لا تتجاهل أي شيء.

📋 أعطني الإجابة بهذا التنسيق بالضبط:

VISIBLE_TEXTS:
- [اذكر كل النصوص التي تراها (إن وجدت)، مع لغة كل نص]

PEOPLE_DETAILS:
- [وصف الأشخاص ولباسهم وما يميزهم جغرافياً]

ENVIRONMENT:
- [وصف البيئة (طقس، نباتات، تضاريس)]

ARCHITECTURE:
- [نمط المباني والمعمار]

VEHICLES_INFRASTRUCTURE:
- [السيارات، اللوحات، البنية التحتية]

DISTINCTIVE_COLORS_SYMBOLS:
- [ألوان أو رموز أو شعارات مميزة]

REASONING:
[فقرة: ربط الإشارات لاستنتاج الموقع]

COUNTRY_CODE: [ISO حرفين أو UNKNOWN]
COUNTRY_NAME: [اسم الدولة بالعربية]
CITY: [المدينة أو UNKNOWN]
CONFIDENCE: [HIGH أو MEDIUM أو LOW]

KEY_EVIDENCE:
- [أهم 2-3 أدلة]

ALTERNATIVE_LOCATIONS:
- [مواقع بديلة محتملة إن لم تكن متأكداً]

⚠️ القواعد:
- لا تخمن بدون دليل بصري
- إذا الصورة من داخل غرفة بدون أي إشارات → COUNTRY_CODE: UNKNOWN
- إذا الصورة شعار أو لوحة فنية → ركز على الرموز/الكتابة"""


# Prompt 2: مع hint من موقع الحساب
HINTED_PROMPT_TEMPLATE = """أنت محقق جغرافي. حلل هذه الصورة لتحديد موقع التصوير.

📌 معلومة مفيدة: صاحب الحساب الذي نشر هذه الصورة يدّعي أن موقعه: **{account_location}**

⚠️ مهمتك: تحقق من هذا الادعاء بناءً على الصورة فقط:
   - هل الصورة فعلاً من {account_location}؟
   - أم من بلد مختلف؟ (احتمال VPN)
   - أم لا يمكن تحديدها؟

🔍 ابحث عن:
1. لافتات/نصوص بلغة معينة
2. لوحات سيارات بشكل/لون مميز
3. معالم سياحية معروفة
4. لباس تقليدي
5. نمط المعمار
6. ألوان مميزة لدولة

📋 الإجابة:

VERIFICATION: [MATCHES / DIFFERENT / UNDETERMINED]
[إذا MATCHES: الصورة تطابق {account_location}]
[إذا DIFFERENT: الصورة من بلد آخر، اذكر أيها]
[إذا UNDETERMINED: لا توجد إشارات جغرافية]

OBSERVATIONS:
- [3-5 ملاحظات فعلية مما رأيته]

COUNTRY_CODE: [ISO حرفين أو UNKNOWN]
COUNTRY_NAME: [الاسم بالعربية]
CITY: [المدينة أو UNKNOWN]
CONFIDENCE: [HIGH/MEDIUM/LOW]

KEY_EVIDENCE:
- [الأدلة الرئيسية]"""


# Prompt 3: للصور الصعبة (شعارات، رسومات)
LOGO_PROMPT = """هذه الصورة قد تكون شعار، رسمة، أو نص فني. حللها بدقة:

🎯 ابحث عن:
1. **اسم منظمة/مؤسسة** بالعربية أو الإنجليزية
2. **شعار حكومي** (دولة محددة؟)
3. **رمز ديني/ثقافي** (إسلامي/مسيحي/يهودي؟)
4. **علم دولة** ضمن التصميم
5. **خط عربي مميز** (نسخ/كوفي/ديواني؟)
6. **ألوان دولة** (أحمر+أبيض = إندونيسيا/ بولندا، أخضر+أبيض = السعودية)

📋 الإجابة:

CONTENT_TYPE: [LOGO / TEXT_ART / DRAWING / OTHER]
ORGANIZATION_NAME: [الاسم إن وجد]
LANGUAGE: [اللغة الرئيسية]
SYMBOLS: [الرموز التي تراها]

COUNTRY_CODE: [ISO حرفين أو UNKNOWN]
COUNTRY_NAME: [الدولة بالعربية]
CONFIDENCE: [HIGH/MEDIUM/LOW]

REASONING:
[لماذا استنتجت هذا]"""


# =====================================================
# Helpers
# =====================================================

def parse_geo_response(text):
    """تحليل رد Gemini مع كل الحقول"""
    if not text:
        return None
    
    result = {
        'visible_texts': [],
        'people_details': [],
        'environment': [],
        'architecture': [],
        'vehicles_infrastructure': [],
        'distinctive_colors_symbols': [],
        'observations': [],
        'reasoning': '',
        'country_code': None,
        'country_name': None,
        'city': None,
        'neighborhood': None,
        'coordinates': None,
        'confidence': None,
        'confidence_score': 0,
        'key_evidence': [],
        'alternative_locations': [],
        'verification': None,  # MATCHES/DIFFERENT/UNDETERMINED
        'content_type': None,
        'organization_name': None,
        'language': None,
        'raw_text': text,
    }
    
    def extract_section(name, text):
        m = re.search(rf'{name}:\s*\n?((?:.|\n)*?)(?=\n[A-Z_]+:|$)', text)
        if not m:
            return []
        items = []
        for line in m.group(1).strip().split('\n'):
            line = line.strip().lstrip('-•*').strip()
            if line and len(line) > 3 and not line.startswith('['):
                items.append(line[:250])
        return items
    
    def extract_field(name, text):
        m = re.search(rf'{name}:\s*([^\n]+)', text)
        if m:
            val = m.group(1).strip()
            if 'UNKNOWN' not in val.upper() and val and not val.startswith('['):
                return val
        return None
    
    # Country code
    m = re.search(r'COUNTRY_CODE:\s*([A-Z]{2}|UNKNOWN)', text)
    if m and m.group(1) != 'UNKNOWN':
        result['country_code'] = m.group(1)
    
    result['country_name'] = extract_field('COUNTRY_NAME', text)
    result['city'] = extract_field('CITY', text)
    result['neighborhood'] = extract_field('NEIGHBORHOOD', text)
    result['organization_name'] = extract_field('ORGANIZATION_NAME', text)
    result['language'] = extract_field('LANGUAGE', text)
    result['content_type'] = extract_field('CONTENT_TYPE', text)
    
    # Confidence
    m = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', text, re.IGNORECASE)
    if m:
        result['confidence'] = m.group(1).upper()
        result['confidence_score'] = {'HIGH': 88, 'MEDIUM': 65, 'LOW': 40}.get(m.group(1).upper(), 0)
    
    # Verification (للـ HINTED_PROMPT)
    m = re.search(r'VERIFICATION:\s*(MATCHES|DIFFERENT|UNDETERMINED)', text, re.IGNORECASE)
    if m:
        result['verification'] = m.group(1).upper()
    
    # All sections
    result['visible_texts'] = extract_section('VISIBLE_TEXTS', text)
    result['people_details'] = extract_section('PEOPLE_DETAILS', text)
    result['environment'] = extract_section('ENVIRONMENT', text)
    result['architecture'] = extract_section('ARCHITECTURE', text)
    result['vehicles_infrastructure'] = extract_section('VEHICLES_INFRASTRUCTURE', text)
    result['distinctive_colors_symbols'] = extract_section('DISTINCTIVE_COLORS_SYMBOLS', text)
    result['observations'] = extract_section('OBSERVATIONS', text)
    result['key_evidence'] = extract_section('KEY_EVIDENCE', text)
    result['alternative_locations'] = extract_section('ALTERNATIVE_LOCATIONS', text)
    
    # SYMBOLS (for logo prompt)
    symbols = extract_section('SYMBOLS', text)
    if symbols:
        result['distinctive_colors_symbols'].extend(symbols)
    
    # Reasoning
    m = re.search(r'REASONING:\s*\n?((?:.|\n)*?)(?=\n[A-Z_]+:|$)', text)
    if m:
        result['reasoning'] = m.group(1).strip()[:600]
    
    # دمج كل الـ observations
    all_obs = (result['visible_texts'] + result['people_details'] + 
               result['environment'] + result['architecture'] +
               result['vehicles_infrastructure'] + result['distinctive_colors_symbols'])
    if all_obs and not result['observations']:
        result['observations'] = all_obs[:7]
    
    return result


# =====================================================
# EXIF GPS
# =====================================================

def extract_exif_gps(image_data):
    """استخراج GPS من EXIF"""
    if not PIL_AVAILABLE:
        return None
    try:
        img = Image.open(io.BytesIO(image_data))
        exif = img._getexif()
        if not exif:
            return None
        gps_info = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id)
            if tag == 'GPSInfo':
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_value
        if not gps_info:
            return None
        def dms_to_decimal(dms, ref):
            try:
                deg = float(dms[0])
                minutes = float(dms[1])
                seconds = float(dms[2])
                decimal = deg + minutes/60 + seconds/3600
                if ref in ['S', 'W']:
                    decimal = -decimal
                return decimal
            except Exception:
                return None
        lat = dms_to_decimal(gps_info.get('GPSLatitude'), gps_info.get('GPSLatitudeRef', 'N'))
        lon = dms_to_decimal(gps_info.get('GPSLongitude'), gps_info.get('GPSLongitudeRef', 'E'))
        if lat is None or lon is None:
            return None
        return {'lat': lat, 'lon': lon}
    except Exception:
        return None


def reverse_geocode(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {'lat': lat, 'lon': lon, 'format': 'json', 'accept-language': 'ar,en'}
        headers = {'User-Agent': 'SocialAccountsAnalyzer/1.0'}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            address = data.get('address', {})
            return {
                'country': address.get('country'),
                'country_code': (address.get('country_code') or '').upper(),
                'city': address.get('city') or address.get('town') or address.get('village'),
                'neighborhood': address.get('suburb') or address.get('neighbourhood'),
                'display_name': data.get('display_name'),
            }
    except Exception:
        pass
    return None


# =====================================================
# Image Download with retries
# =====================================================

def download_image_robust(url, timeout=15, max_retries=2):
    """تحميل صورة مع retries وتعديل URL إن لزم"""
    # تحويل URLs الصغيرة من X لأكبر حجم
    test_urls = [url]
    
    # X uses ?name=small/large/orig - جرب نسخ مختلفة
    if 'pbs.twimg.com' in url or 'twimg.com' in url:
        if '?name=' in url:
            base = url.split('?name=')[0]
            test_urls = [f"{base}?name=large", f"{base}?name=orig", url]
        elif '?' not in url:
            test_urls = [f"{url}?name=large", url]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0",
        "Accept": "image/webp,image/avif,image/jpeg,image/png,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    for test_url in test_urls:
        for attempt in range(max_retries):
            try:
                r = requests.get(test_url, timeout=timeout, headers=headers)
                if r.status_code == 200 and len(r.content) > 1000:
                    return r.content, test_url
            except Exception:
                pass
        time.sleep(0.5)
    
    return None, None


# =====================================================
# Multi-pass Image Analysis with Gemini
# =====================================================

def gemini_call(prompt, img, api_key, temperature=0.2):
    """استدعاء Gemini مع fallback model"""
    try:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception:
            model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(
            [prompt, img],
            generation_config={'temperature': temperature, 'max_output_tokens': 2000}
        )
        return response.text or ""
    except Exception as e:
        return f"ERROR: {e}"


def analyze_image_geo(image_url_or_bytes, api_key, account_location=None,
                     timeout=30, debug=False):
    """
    تحليل صورة بـ multi-pass + EXIF
    
    account_location: موقع الحساب (لتمريره كـ hint لـ Gemini)
    debug: إن True، يعيد كل المحاولات الخام
    """
    if not GEMINI_AVAILABLE:
        return {'success': False, 'error': 'google-generativeai غير مثبت'}
    if not api_key:
        return {'success': False, 'error': 'لا يوجد API key'}
    
    debug_info = {'attempts': []}
    image_url_used = None
    
    try:
        # تحميل
        if isinstance(image_url_or_bytes, str):
            image_url_used = image_url_or_bytes
            image_bytes, used_url = download_image_robust(image_url_or_bytes, timeout=timeout)
            if not image_bytes:
                return {
                    'success': False,
                    'error': f'فشل تحميل الصورة من {image_url_or_bytes}',
                    'debug': debug_info,
                }
            image_url_used = used_url
            debug_info['download_size'] = len(image_bytes)
            debug_info['url_used'] = used_url
        else:
            image_bytes = image_url_or_bytes
        
        # 1. EXIF
        exif_result = None
        gps = extract_exif_gps(image_bytes)
        if gps:
            time.sleep(1)
            geo = reverse_geocode(gps['lat'], gps['lon'])
            if geo:
                exif_result = {
                    'source': '🛰️ EXIF GPS (مباشر من الصورة)',
                    'lat': gps['lat'],
                    'lon': gps['lon'],
                    'country_code': geo.get('country_code'),
                    'country_name': geo.get('country'),
                    'city': geo.get('city'),
                    'neighborhood': geo.get('neighborhood'),
                    'confidence_score': 100,
                    'display_name': geo.get('display_name'),
                }
                # EXIF يكفي
                return {
                    'success': True,
                    'exif': exif_result,
                    'gemini': None,
                    'method_used': 'EXIF GPS',
                    'debug': debug_info,
                }
        
        # 2. Gemini multi-pass
        if not PIL_AVAILABLE:
            return {'success': False, 'error': 'PIL غير مثبت', 'debug': debug_info}
        
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # تكبير الصور الصغيرة (لتحسين قراءة النصوص)
        if max(img.size) < 800:
            ratio = 1024 / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        elif max(img.size) > 1600:
            ratio = 1600 / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        # المحاولة 1: Deep prompt
        text1 = gemini_call(DEEP_PROMPT, img, api_key, temperature=0.2)
        debug_info['attempts'].append({'prompt': 'DEEP', 'text': text1[:1000]})
        result1 = parse_geo_response(text1)
        
        # المحاولة 2: مع hint من موقع الحساب (إن وُجد)
        result2 = None
        if account_location:
            hinted = HINTED_PROMPT_TEMPLATE.replace('{account_location}', account_location)
            text2 = gemini_call(hinted, img, api_key, temperature=0.2)
            debug_info['attempts'].append({'prompt': 'HINTED', 'text': text2[:1000]})
            result2 = parse_geo_response(text2)
        
        # المحاولة 3: للشعارات/الرسومات (إن فشل الباقي)
        result3 = None
        if (not result1 or not result1.get('country_code')) and \
           (not result2 or not result2.get('country_code')):
            text3 = gemini_call(LOGO_PROMPT, img, api_key, temperature=0.3)
            debug_info['attempts'].append({'prompt': 'LOGO', 'text': text3[:1000]})
            result3 = parse_geo_response(text3)
        
        # دمج النتائج: أفضل واحد له country_code
        candidates = [r for r in [result1, result2, result3] if r and r.get('country_code')]
        
        if candidates:
            # خذ الأعلى ثقة
            best = max(candidates, key=lambda x: x.get('confidence_score', 0))
            
            # دمج المعلومات من كل النتائج
            all_obs = []
            for r in [result1, result2, result3]:
                if r:
                    all_obs.extend(r.get('observations', []))
                    all_obs.extend(r.get('visible_texts', []))
                    all_obs.extend(r.get('people_details', []))
            # أزل المكررات
            best['observations'] = list(dict.fromkeys(all_obs))[:10]
            
            return {
                'success': True,
                'exif': None,
                'gemini': best,
                'method_used': 'Gemini Multi-pass',
                'debug': debug_info,
                'all_attempts': [result1, result2, result3],
            }
        
        # لم نجد دولة لكن قد توجد ملاحظات
        observations = []
        for r in [result1, result2, result3]:
            if r:
                observations.extend(r.get('observations', []))
                observations.extend(r.get('visible_texts', []))
                observations.extend(r.get('people_details', []))
        observations = list(dict.fromkeys(observations))[:15]
        
        partial_result = {
            'country_code': None,
            'observations': observations,
            'reasoning': result1.get('reasoning', '') if result1 else '',
            'visible_texts': result1.get('visible_texts', []) if result1 else [],
            'verification': result2.get('verification') if result2 else None,
            'content_type': result3.get('content_type') if result3 else None,
            'confidence_score': 0,
        }
        
        return {
            'success': True,  # نجح التحليل لكن بدون دولة
            'exif': None,
            'gemini': partial_result,
            'method_used': 'Gemini (لا توجد دولة محددة)',
            'no_country_detected': True,
            'debug': debug_info,
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e), 'debug': debug_info}


def analyze_post_images(image_urls, api_key, max_images=4, account_location=None):
    """تحليل عدة صور من نفس المنشور"""
    if not image_urls:
        return {'success': False, 'error': 'لا توجد صور'}
    
    results = []
    for url in image_urls[:max_images]:
        r = analyze_image_geo(url, api_key, account_location=account_location)
        r['image_url'] = url
        results.append(r)
        time.sleep(0.5)
    
    # 1. EXIF
    for r in results:
        if r.get('success') and r.get('exif') and r['exif'].get('country_code'):
            return {
                'success': True,
                'aggregate': r['exif'],
                'method': '🛰️ EXIF GPS مستخرج من الصورة',
                'all_results': results,
            }
    
    # 2. تصويت Gemini
    votes = {}
    confidence_sum = {}
    for r in results:
        gem = r.get('gemini')
        if gem and gem.get('country_code'):
            cc = gem['country_code']
            votes[cc] = votes.get(cc, 0) + 1
            confidence_sum[cc] = confidence_sum.get(cc, 0) + gem.get('confidence_score', 0)
    
    if not votes:
        # لا دولة لكن قد توجد ملاحظات
        all_observations = []
        all_texts = []
        for r in results:
            gem = r.get('gemini') or {}
            all_observations.extend(gem.get('observations', []))
            all_texts.extend(gem.get('visible_texts', []))
        
        return {
            'success': False,
            'aggregate': None,
            'method': 'لم يتم اكتشاف موقع من الصور',
            'all_results': results,
            'partial_observations': list(dict.fromkeys(all_observations))[:10],
            'partial_texts': list(dict.fromkeys(all_texts))[:10],
        }
    
    best_cc = max(votes, key=lambda c: (votes[c], confidence_sum[c]))
    avg_conf = int(confidence_sum[best_cc] / votes[best_cc])
    
    best_details = None
    for r in results:
        gem = r.get('gemini')
        if gem and gem.get('country_code') == best_cc:
            if best_details is None or (gem.get('city') and not best_details.get('city')):
                best_details = gem
    
    return {
        'success': True,
        'aggregate': {
            'source': f'🤖 Gemini Vision ({sum(votes.values())} صور)',
            'country_code': best_cc,
            'country_name': best_details.get('country_name') if best_details else None,
            'city': best_details.get('city') if best_details else None,
            'neighborhood': best_details.get('neighborhood') if best_details else None,
            'coordinates': best_details.get('coordinates') if best_details else None,
            'confidence_score': avg_conf,
            'observations': best_details.get('observations', []) if best_details else [],
            'key_evidence': best_details.get('key_evidence', []) if best_details else [],
            'visible_texts': best_details.get('visible_texts', []) if best_details else [],
            'reasoning': best_details.get('reasoning', '') if best_details else '',
            'verification': best_details.get('verification') if best_details else None,
            'votes_str': f"{votes[best_cc]} من {sum(votes.values())} صور",
        },
        'method': f'🤖 Gemini Vision ({sum(votes.values())} صور)',
        'all_results': results,
    }


# =====================================================
# 🚨 VPN/Inconsistency Detector
# =====================================================

ARABIC_COUNTRIES = ['SA', 'AE', 'EG', 'IQ', 'KW', 'QA', 'BH', 'OM', 'YE', 'JO',
                    'LB', 'SY', 'PS', 'MA', 'DZ', 'TN', 'LY', 'SD', 'SO', 'MR', 'DJ']
WESTERN_COUNTRIES = ['US', 'GB', 'CA', 'AU', 'NZ', 'IE', 'DE', 'FR', 'NL', 'SE',
                     'NO', 'DK', 'FI', 'CH', 'BE', 'AT']


def detect_vpn(account_country, post_country, lang='', name='', bio=''):
    """كاشف VPN ذكي"""
    indicators = []
    
    if not account_country and not post_country:
        return {
            'verdict': 'unknown', 'icon': '❓',
            'verdict_ar': 'بيانات غير كافية',
            'risk_score': 0,
            'indicators': ['لم نستطع تحديد لا موقع الحساب ولا الصورة'],
            'recommendation': '',
        }
    
    if not account_country and post_country:
        return {
            'verdict': 'post_only', 'icon': '📍',
            'verdict_ar': f'موقع المنشور فقط: {post_country} (الحساب لم يحدد موقعاً)',
            'risk_score': 25,
            'indicators': [f'📸 الصورة من {post_country}', '🏠 الحساب بدون موقع معلن'],
            'recommendation': '⚠️ الحساب يخفي موقعه — الصورة الفعلية من ' + post_country,
            'real_location_guess': post_country,
        }
    
    if account_country and not post_country:
        return {
            'verdict': 'account_only', 'icon': '🏠',
            'verdict_ar': f'موقع الحساب فقط: {account_country}',
            'risk_score': 0,
            'indicators': ['الصور لا تحوي إشارات جغرافية واضحة'],
            'recommendation': '',
        }
    
    if account_country == post_country:
        return {
            'verdict': 'matched', 'icon': '✅',
            'verdict_ar': f'تطابق: الحساب والصورة من {account_country}',
            'risk_score': 0,
            'indicators': [f'موقع الحساب = موقع الصورة = {account_country}'],
            'recommendation': '✅ موقع الحساب مؤكد ومتطابق',
        }
    
    indicators.append(f'⚠️ موقع الحساب: {account_country}')
    indicators.append(f'📸 موقع الصورة: {post_country}')
    risk_score = 45
    
    if lang == 'ar':
        if post_country in ARABIC_COUNTRIES and account_country in WESTERN_COUNTRIES:
            indicators.append(f'🔍 اللغة عربية')
            indicators.append(f'🔍 الصورة من بلد عربي ({post_country})')
            indicators.append(f'🔍 لكن الحساب يدّعي {account_country}')
            risk_score = 90
            return {
                'verdict': 'likely_vpn', 'icon': '🚨',
                'verdict_ar': f'🚨 محتمل جداً: VPN — الشخص على الأرجح في {post_country}',
                'risk_score': risk_score,
                'indicators': indicators,
                'recommendation': f'❗ احتمال VPN عالي جداً. الموقع الفعلي المرجح: {post_country}',
                'real_location_guess': post_country,
            }
        if post_country in ARABIC_COUNTRIES and account_country in ARABIC_COUNTRIES:
            indicators.append('✈️ سفر بين دولتين عربيتين (طبيعي)')
            return {
                'verdict': 'travel', 'icon': '✈️',
                'verdict_ar': f'سفر/زيارة: مقيم في {account_country}، يصور في {post_country}',
                'risk_score': 20,
                'indicators': indicators,
                'recommendation': '✈️ نشاط سفر طبيعي — لا توجد إشارات VPN',
            }
    
    if post_country in ARABIC_COUNTRIES and account_country in WESTERN_COUNTRIES:
        indicators.append('🏠 نمط مغترب: مقيم في الغرب، يصور في بلده الأصلي')
        return {
            'verdict': 'expat_visit', 'icon': '🌍',
            'verdict_ar': f'مغترب يزور بلده: مقيم في {account_country}، يصور في {post_country}',
            'risk_score': 30,
            'indicators': indicators,
            'recommendation': '🌍 نمط مغترب طبيعي. قد يكون فعلاً في زيارة، أو يستخدم VPN عند النشر',
        }
    
    return {
        'verdict': 'mismatch', 'icon': '⚠️',
        'verdict_ar': f'تناقض: حساب من {account_country}، صورة من {post_country}',
        'risk_score': 65,
        'indicators': indicators,
        'recommendation': '⚠️ تناقض ملحوظ — راجع تغريدات أكثر للتأكد',
    }


# =====================================================
# Test
# =====================================================

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ ضع GEMINI_API_KEY في environment")
        exit(0)
    
    # اختبار مع شعار
    print("\n🔍 اختبار 1: شعار/لوغو (مثل صورة sanadUK)")
    print("="*60)
    # شعار حكومي
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Flag_of_Saudi_Arabia.svg/640px-Flag_of_Saudi_Arabia.svg.png"
    result = analyze_image_geo(test_url, api_key, account_location='United Kingdom')
    print(f"Method: {result.get('method_used')}")
    if result.get('gemini'):
        g = result['gemini']
        print(f"Country: {g.get('country_code')} - {g.get('country_name')}")
        print(f"Visible texts: {g.get('visible_texts')}")
        print(f"Distinctive symbols: {g.get('distinctive_colors_symbols', [])}")
        print(f"Reasoning: {g.get('reasoning', '')[:200]}")
