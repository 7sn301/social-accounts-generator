"""
🌍 Post Location Analyzer - تحليل موقع المنشور بدقة
====================================================
الميزات:
  ✅ EXIF GPS (إن وُجد - الأدق 100%)
  ✅ Gemini Vision لتحليل الصور (تقنية GEO-Detective)
  ✅ تحليل إطارات الفيديو (Key frames)
  ✅ كاشف VPN ذكي (مقارنة موقع الحساب ↔ موقع المنشور)
  ✅ تمييز واضح بين الحساب والمنشور
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
# Prompt متخصص (تقنية GEO-Detective)
# =====================================================

GEO_DETECTIVE_PROMPT = """أنت محقق جغرافي خبير. حلل هذه الصورة لتحديد موقع التصوير بأقصى دقة ممكنة.

🔍 افحص بترتيب 5 فئات:

1️⃣ **معمار/مباني**: نمط البناء (إسلامي/أوروبي/آسيوي)، مواد، شرفات، ارتفاعات
2️⃣ **بنية تحتية**: لوحات السيارات (شكل/لون/نوع الخط)، إشارات المرور، أعمدة الإنارة، الأرصفة
3️⃣ **بيئة**: الغطاء النباتي، التضاريس، الطقس، الصحراء/الجبال/البحر
4️⃣ **تخطيط حضري**: تخطيط الشوارع، أنواع المركبات السائدة، الكثافة
5️⃣ **لافتات/نصوص**: لغة اللافتات، نوع الخط، أسماء شوارع، علامات تجارية محلية

📋 الإجابة بهذا التنسيق:

OBSERVATIONS:
- [ملاحظة 1]
- [ملاحظة 2]
- [ملاحظة 3]

REASONING:
[فقرة قصيرة: كيف استنتجت الموقع]

COUNTRY_CODE: [ISO رمز حرفين أو UNKNOWN]
COUNTRY_NAME: [اسم الدولة بالعربية]
CITY: [المدينة أو UNKNOWN]
NEIGHBORHOOD: [الحي أو UNKNOWN]
COORDINATES: [lat,lon تقريبية أو UNKNOWN]
CONFIDENCE: [HIGH أو MEDIUM أو LOW]

KEY_EVIDENCE:
- [أهم دليل 1]
- [أهم دليل 2]

ALTERNATIVE_LOCATIONS:
- [موقع بديل محتمل إن لم تكن متأكداً]

⚠️ القواعد:
- لا تخمن دون دليل بصري
- إذا كانت الصورة لشخص داخل غرفة بدون أي إشارات → COUNTRY_CODE: UNKNOWN
- ركز على ما تراه فعلياً في البكسلات
"""


# =====================================================
# Helpers
# =====================================================

def parse_geo_response(text):
    """تحليل رد Gemini"""
    if not text:
        return None
    
    result = {
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
        'raw_text': text,
    }
    
    # COUNTRY_CODE
    m = re.search(r'COUNTRY_CODE:\s*([A-Z]{2}|UNKNOWN)', text)
    if m and m.group(1) != 'UNKNOWN':
        result['country_code'] = m.group(1)
    
    # COUNTRY_NAME
    m = re.search(r'COUNTRY_NAME:\s*([^\n]+)', text)
    if m:
        result['country_name'] = m.group(1).strip()
    
    # CITY
    m = re.search(r'CITY:\s*([^\n]+)', text)
    if m and 'UNKNOWN' not in m.group(1).upper():
        result['city'] = m.group(1).strip()
    
    # NEIGHBORHOOD
    m = re.search(r'NEIGHBORHOOD:\s*([^\n]+)', text)
    if m and 'UNKNOWN' not in m.group(1).upper():
        result['neighborhood'] = m.group(1).strip()
    
    # COORDINATES
    m = re.search(r'COORDINATES:\s*([\d\.\-,\s]+)', text)
    if m and 'UNKNOWN' not in m.group(0).upper():
        coords = m.group(1).strip()
        if ',' in coords:
            result['coordinates'] = coords
    
    # CONFIDENCE
    m = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', text, re.IGNORECASE)
    if m:
        result['confidence'] = m.group(1).upper()
        confidence_map = {'HIGH': 88, 'MEDIUM': 65, 'LOW': 40}
        result['confidence_score'] = confidence_map.get(result['confidence'], 0)
    
    # OBSERVATIONS
    obs_match = re.search(r'OBSERVATIONS:\s*\n((?:.|\n)*?)(?=REASONING:|$)', text)
    if obs_match:
        for line in obs_match.group(1).strip().split('\n'):
            line = line.strip().lstrip('-•*').strip()
            if line and len(line) > 5:
                result['observations'].append(line[:200])
    
    # REASONING
    reason_match = re.search(r'REASONING:\s*\n?((?:.|\n)*?)(?=COUNTRY_CODE:|$)', text)
    if reason_match:
        result['reasoning'] = reason_match.group(1).strip()[:500]
    
    # KEY_EVIDENCE
    ke_match = re.search(r'KEY_EVIDENCE:\s*\n((?:.|\n)*?)(?=ALTERNATIVE_LOCATIONS:|$)', text)
    if ke_match:
        for line in ke_match.group(1).strip().split('\n'):
            line = line.strip().lstrip('-•*').strip()
            if line and len(line) > 5:
                result['key_evidence'].append(line[:200])
    
    # ALTERNATIVE_LOCATIONS
    alt_match = re.search(r'ALTERNATIVE_LOCATIONS:\s*\n((?:.|\n)*?)$', text)
    if alt_match:
        for line in alt_match.group(1).strip().split('\n'):
            line = line.strip().lstrip('-•*').strip()
            if line and len(line) > 3:
                result['alternative_locations'].append(line[:150])
    
    return result


# =====================================================
# EXIF GPS
# =====================================================

def extract_exif_gps(image_data):
    """استخراج GPS من EXIF (نادر لكن قاطع 100%)"""
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
    """إحداثيات → دولة/مدينة (Nominatim مجاني)"""
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
# Image Analysis with Gemini Vision
# =====================================================

def analyze_image_geo(image_url_or_bytes, api_key, timeout=30):
    """
    تحليل صورة لتحديد موقع التصوير
    يحاول EXIF أولاً ثم Gemini Vision
    """
    if not GEMINI_AVAILABLE:
        return {'success': False, 'error': 'google-generativeai غير مثبت'}
    if not api_key:
        return {'success': False, 'error': 'لا يوجد API key'}
    
    try:
        if isinstance(image_url_or_bytes, str):
            r = requests.get(image_url_or_bytes, timeout=15)
            if r.status_code != 200:
                return {'success': False, 'error': f'فشل تحميل: HTTP {r.status_code}'}
            image_bytes = r.content
        else:
            image_bytes = image_url_or_bytes
        
        # 1. EXIF GPS (الأقوى)
        exif_result = None
        gps = extract_exif_gps(image_bytes)
        if gps:
            time.sleep(1)  # rate limit Nominatim
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
        
        # 2. Gemini Vision
        if not PIL_AVAILABLE:
            return {'success': bool(exif_result), 'exif': exif_result, 'gemini': None}
        
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # تصغير للصور الكبيرة
        max_dim = 1024
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        genai.configure(api_key=api_key)
        # gemini-2.0-flash-exp = الأحدث والأسرع
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception:
            model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(
            [GEO_DETECTIVE_PROMPT, img],
            generation_config={'temperature': 0.2, 'max_output_tokens': 1500}
        )
        
        gemini_text = response.text or ""
        gemini_result = parse_geo_response(gemini_text)
        
        return {'success': True, 'exif': exif_result, 'gemini': gemini_result}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =====================================================
# Multi-image Aggregation
# =====================================================

def analyze_post_images(image_urls, api_key, max_images=4):
    """تحليل عدة صور من نفس المنشور ودمج النتائج"""
    if not image_urls:
        return {'success': False, 'error': 'لا توجد صور'}
    
    results = []
    for url in image_urls[:max_images]:
        r = analyze_image_geo(url, api_key)
        r['image_url'] = url
        results.append(r)
        time.sleep(0.5)  # تجنب rate limits
    
    # 1. EXIF أولاً
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
        return {
            'success': False,
            'aggregate': None,
            'method': 'لم يتم اكتشاف موقع من الصور',
            'all_results': results,
        }
    
    best_cc = max(votes, key=lambda c: (votes[c], confidence_sum[c]))
    avg_conf = int(confidence_sum[best_cc] / votes[best_cc])
    
    # خذ أفضل تفاصيل
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
            'reasoning': best_details.get('reasoning', '') if best_details else '',
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
    """
    🚨 كاشف VPN ذكي
    يقارن موقع الحساب (المُعلَن) مع موقع المنشور (من الصورة)
    + يستخدم اللغة والاسم لتعزيز التشخيص
    """
    indicators = []
    
    # حالة 1: لا توجد بيانات كافية
    if not account_country and not post_country:
        return {
            'verdict': 'unknown', 'icon': '❓',
            'verdict_ar': 'بيانات غير كافية',
            'risk_score': 0,
            'indicators': ['لم نستطع تحديد لا موقع الحساب ولا الصورة'],
            'recommendation': '',
        }
    
    # حالة 2: موقع منشور بدون موقع حساب
    if not account_country and post_country:
        return {
            'verdict': 'post_only', 'icon': '📍',
            'verdict_ar': f'موقع المنشور فقط: {post_country} (الحساب لم يحدد موقعاً)',
            'risk_score': 25,
            'indicators': [f'📸 الصورة من {post_country}', '🏠 الحساب بدون موقع معلن'],
            'recommendation': '⚠️ الحساب يخفي موقعه — الصورة الفعلية من ' + post_country,
            'real_location_guess': post_country,
        }
    
    # حالة 3: موقع حساب بدون موقع منشور
    if account_country and not post_country:
        return {
            'verdict': 'account_only', 'icon': '🏠',
            'verdict_ar': f'موقع الحساب فقط: {account_country}',
            'risk_score': 0,
            'indicators': ['الصور لا تحوي إشارات جغرافية واضحة'],
            'recommendation': '',
        }
    
    # حالة 4: تطابق
    if account_country == post_country:
        return {
            'verdict': 'matched', 'icon': '✅',
            'verdict_ar': f'تطابق: الحساب والصورة من {account_country}',
            'risk_score': 0,
            'indicators': [f'موقع الحساب = موقع الصورة = {account_country}'],
            'recommendation': '✅ موقع الحساب مؤكد ومتطابق',
        }
    
    # حالة 5: تناقض — تحليل عميق
    indicators.append(f'⚠️ موقع الحساب: {account_country}')
    indicators.append(f'📸 موقع الصورة: {post_country}')
    
    risk_score = 45
    
    # اللغة عربية + الصورة من بلد عربي + الحساب من الغرب = مؤشر VPN قوي
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
        
        # عربي ↔ عربي = سفر بين دول عربية (طبيعي)
        if post_country in ARABIC_COUNTRIES and account_country in ARABIC_COUNTRIES:
            indicators.append('✈️ سفر بين دولتين عربيتين (طبيعي)')
            return {
                'verdict': 'travel', 'icon': '✈️',
                'verdict_ar': f'سفر/زيارة: مقيم في {account_country}، يصور في {post_country}',
                'risk_score': 20,
                'indicators': indicators,
                'recommendation': '✈️ نشاط سفر طبيعي — لا توجد إشارات VPN',
            }
    
    # نمط مغترب: حساب في الغرب، صورة من بلد عربي
    if post_country in ARABIC_COUNTRIES and account_country in WESTERN_COUNTRIES:
        indicators.append('🏠 نمط مغترب: مقيم في الغرب، يصور في بلده الأصلي')
        return {
            'verdict': 'expat_visit', 'icon': '🌍',
            'verdict_ar': f'مغترب يزور بلده: مقيم في {account_country}، يصور في {post_country}',
            'risk_score': 30,
            'indicators': indicators,
            'recommendation': '🌍 نمط مغترب طبيعي. قد يكون فعلاً في زيارة، أو يستخدم VPN عند النشر',
        }
    
    # تناقض غير مفسر
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
    
    print("🔍 اختبار كاشف VPN (بدون API):")
    print("="*60)
    
    test_cases = [
        ('GB', 'IQ', 'ar', 'سالم الجميلي'),  # حساب GB، صورة عراق، عربي
        ('US', 'SA', 'ar', 'محمد'),            # حساب US، صورة سعودية
        ('SA', 'SA', 'ar', 'فهد'),              # تطابق
        ('SA', 'AE', 'ar', 'علي'),              # سفر عربي
        (None, 'EG', 'ar', 'أحمد'),             # حساب بدون موقع
    ]
    
    for acc, post, lang, name in test_cases:
        result = detect_vpn(acc, post, lang, name)
        print(f"\n{result['icon']} حساب={acc}, صورة={post}, لغة={lang}")
        print(f"   التشخيص: {result['verdict_ar']}")
        print(f"   درجة الخطر: {result['risk_score']}/100")
        print(f"   التوصية: {result.get('recommendation', '')}")
    
    if api_key:
        print("\n\n" + "="*60)
        print("🔍 اختبار تحليل صورة معلم سعودي:")
        # برج المملكة بالرياض
        url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Kingdom_Centre_Riyadh.jpg/640px-Kingdom_Centre_Riyadh.jpg"
        result = analyze_image_geo(url, api_key)
        if result.get('success') and result.get('gemini'):
            g = result['gemini']
            print(f"📍 الدولة: {g.get('country_code')} - {g.get('country_name')}")
            print(f"🏙️ المدينة: {g.get('city')}")
            print(f"🎯 الثقة: {g.get('confidence')} ({g.get('confidence_score')}%)")
            print(f"📊 الأدلة:")
            for ev in g.get('key_evidence', []):
                print(f"   • {ev}")
