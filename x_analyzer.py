"""
🐦 X (Twitter) Smart Location Analyzer v4 - محرك كشف ذكي متعدد الطبقات
=====================================================================
الميزات الجذرية الجديدة:
  ✅ 7 طبقات كشف مع أوزان مدروسة
  ✅ قاموس مدن موسّع (500+ مدينة)
  ✅ كاش بروفايل ذكي (يجلب مرة واحدة لكل حساب)
  ✅ تحليل صور المنشورات بالذكاء الاصطناعي (معالم، نصوص، لوحات)
  ✅ معالجة التناقضات (مثل علم في الاسم vs علم في البايو)
  ✅ نظام تجميع ثقة قوي يصل إلى 95%+
"""
import requests
import json
import re
import time
import threading
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# =====================================================
# Constants
# =====================================================

FXTWITTER_API = "https://api.fxtwitter.com"

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

# 🌍 قاموس مُوسّع للمدن والبلدان (500+ مدخل)
LOCATION_KEYWORDS = {
    'SA': [
        'saudi', 'arabia', 'riyadh', 'jeddah', 'jiddah', 'mecca', 'makkah', 'medina', 'madinah',
        'dammam', 'khobar', 'al-khobar', 'taif', 'ksa', 'qassim', 'tabuk', 'abha', 'najran', 'jazan', 'hail',
        'السعودية', 'المملكة العربية السعودية', 'الرياض', 'جدة', 'مكة', 'مكة المكرمة',
        'المدينة', 'المدينة المنورة', 'الدمام', 'الخبر', 'الطائف', 'القصيم', 'تبوك', 'أبها',
        'بريدة', 'حائل', 'نجران', 'جازان', 'الأحساء', 'ينبع', 'رأس تنورة', 'الجبيل',
    ],
    'AE': [
        'uae', 'emirates', 'dubai', 'abu dhabi', 'sharjah', 'ajman', 'fujairah', 'ras al khaimah', 'umm al quwain',
        'الإمارات', 'الامارات', 'دبي', 'أبوظبي', 'ابوظبي', 'الشارقة', 'عجمان',
        'العين', 'رأس الخيمة', 'الفجيرة', 'أم القيوين',
    ],
    'EG': [
        'egypt', 'cairo', 'alexandria', 'giza', 'luxor', 'aswan', 'mansoura', 'sharm el sheikh',
        'مصر', 'القاهرة', 'الإسكندرية', 'الاسكندرية', 'الجيزة', 'الأقصر', 'أسوان',
        'المنصورة', 'شرم الشيخ', 'الغردقة', 'بورسعيد', 'السويس', 'طنطا', 'الفيوم', 'أسيوط',
    ],
    'IQ': [
        'iraq', 'baghdad', 'basra', 'basrah', 'mosul', 'erbil', 'arbil', 'najaf', 'karbala',
        'kirkuk', 'sulaymaniyah', 'duhok', 'fallujah', 'ramadi',
        'العراق', 'بغداد', 'البصرة', 'الموصل', 'أربيل', 'النجف', 'كربلاء',
        'الأنبار', 'كركوك', 'السليمانية', 'دهوك', 'الفلوجة', 'الرمادي', 'ديالى', 'بابل',
        'الناصرية', 'العمارة', 'الكوت', 'الديوانية', 'سامراء', 'تكريت', 'الحلة',
    ],
    'KW': ['kuwait', 'الكويت', 'الكويت العاصمة', 'حولي', 'الفروانية', 'الجهراء', 'الأحمدي'],
    'QA': ['qatar', 'doha', 'قطر', 'الدوحة', 'الريان', 'الوكرة'],
    'BH': ['bahrain', 'manama', 'البحرين', 'المنامة', 'المحرق', 'الرفاع'],
    'OM': ['oman', 'muscat', 'sultanate of oman', 'سلطنة عمان', 'مسقط', 'صلالة', 'صحار', 'نزوى'],
    'YE': ['yemen', 'sanaa', 'sana\'a', 'aden', 'taiz', 'hodeidah', 'اليمن', 'صنعاء', 'عدن', 'تعز', 'الحديدة', 'حضرموت'],
    'JO': ['jordan', 'amman', 'zarqa', 'irbid', 'aqaba', 'الأردن', 'الاردن', 'عمّان', 'عمان الأردن', 'الزرقاء', 'إربد', 'العقبة'],
    'LB': ['lebanon', 'beirut', 'tripoli lebanon', 'لبنان', 'بيروت', 'طرابلس لبنان', 'صيدا', 'صور', 'بعلبك', 'جونية'],
    'SY': ['syria', 'damascus', 'aleppo', 'homs', 'latakia', 'سوريا', 'سورية', 'دمشق', 'حلب', 'حمص', 'حماة', 'اللاذقية', 'دير الزور', 'إدلب'],
    'PS': ['palestine', 'gaza', 'jerusalem', 'ramallah', 'hebron', 'nablus', 'bethlehem',
           'فلسطين', 'غزة', 'القدس', 'الضفة', 'الضفة الغربية', 'رام الله', 'الخليل', 'نابلس', 'بيت لحم', 'جنين'],
    'MA': ['morocco', 'casablanca', 'rabat', 'marrakech', 'fez', 'tangier', 'agadir',
           'المغرب', 'الدار البيضاء', 'الرباط', 'مراكش', 'فاس', 'طنجة', 'أكادير', 'مكناس', 'وجدة'],
    'DZ': ['algeria', 'algiers', 'oran', 'constantine', 'الجزائر', 'وهران', 'قسنطينة', 'عنابة', 'تلمسان'],
    'TN': ['tunisia', 'tunis', 'sfax', 'sousse', 'تونس', 'صفاقس', 'سوسة', 'بنزرت', 'القيروان'],
    'LY': ['libya', 'tripoli', 'benghazi', 'misrata', 'ليبيا', 'طرابلس', 'بنغازي', 'مصراتة', 'سرت'],
    'SD': ['sudan', 'khartoum', 'omdurman', 'السودان', 'الخرطوم', 'أم درمان', 'بورتسودان'],
    'SO': ['somalia', 'mogadishu', 'الصومال', 'مقديشو', 'هرجيسا'],
    'MR': ['mauritania', 'nouakchott', 'موريتانيا', 'نواكشوط'],
    'DJ': ['djibouti', 'جيبوتي'],

    'US': [
        'usa', 'united states', 'america', 'new york', 'washington', 'los angeles', 'chicago',
        'texas', 'california', 'florida', 'boston', 'seattle', 'silicon valley', 'nyc',
        'd.c.', 'dc', 'washington dc', 'houston', 'dallas', 'phoenix', 'atlanta',
        'philadelphia', 'san francisco', 'san diego', 'miami', 'detroit', 'minneapolis',
        'denver', 'portland', 'austin', 'nashville', 'orlando', 'las vegas',
        'أمريكا', 'الولايات المتحدة', 'نيويورك', 'واشنطن', 'لوس أنجلوس', 'كاليفورنيا',
        'تكساس', 'فلوريدا', 'هيوستن', 'شيكاغو', 'ميامي',
    ],
    'GB': [
        'england', 'united kingdom', 'london', 'manchester', 'liverpool', 'birmingham',
        'scotland', 'wales', 'britain', 'great britain', 'uk', 'edinburgh', 'glasgow',
        'leeds', 'newcastle', 'oxford', 'cambridge', 'cardiff', 'belfast',
        'إنجلترا', 'انجلترا', 'بريطانيا', 'المملكة المتحدة', 'لندن', 'مانشستر',
        'ليفربول', 'برمنغهام', 'اسكتلندا', 'إدنبرة', 'ويلز',
    ],
    'CA': ['canada', 'toronto', 'vancouver', 'montreal', 'ottawa', 'calgary', 'edmonton', 'quebec',
           'كندا', 'تورنتو', 'فانكوفر', 'مونتريال', 'أوتاوا', 'كالغاري', 'كيبيك'],
    'AU': ['australia', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'canberra',
           'أستراليا', 'استراليا', 'سيدني', 'ملبورن', 'بيرث', 'بريسبان'],
    'NZ': ['new zealand', 'auckland', 'wellington', 'نيوزيلندا', 'نيوزلندا', 'أوكلاند'],

    'FR': ['france', 'paris', 'lyon', 'marseille', 'toulouse', 'nice', 'bordeaux',
           'فرنسا', 'باريس', 'ليون', 'مرسيليا', 'تولوز', 'نيس'],
    'DE': ['germany', 'berlin', 'munich', 'munchen', 'hamburg', 'frankfurt', 'cologne', 'koln', 'dusseldorf', 'stuttgart',
           'ألمانيا', 'المانيا', 'برلين', 'ميونخ', 'هامبورغ', 'فرانكفورت', 'كولونيا'],
    'IT': ['italy', 'rome', 'roma', 'milan', 'milano', 'naples', 'napoli', 'turin', 'torino', 'florence', 'venice',
           'إيطاليا', 'ايطاليا', 'روما', 'ميلانو', 'نابولي', 'فلورنسا', 'البندقية'],
    'ES': ['spain', 'madrid', 'barcelona', 'valencia', 'seville', 'sevilla',
           'إسبانيا', 'اسبانيا', 'مدريد', 'برشلونة', 'فالنسيا', 'إشبيلية'],
    'NL': ['netherlands', 'holland', 'amsterdam', 'rotterdam', 'the hague',
           'هولندا', 'أمستردام', 'روتردام', 'لاهاي'],
    'BE': ['belgium', 'brussels', 'antwerp', 'بلجيكا', 'بروكسل', 'أنتويرب'],
    'CH': ['switzerland', 'zurich', 'geneva', 'bern', 'basel',
           'سويسرا', 'زيوريخ', 'جنيف', 'برن'],
    'AT': ['austria', 'vienna', 'salzburg', 'النمسا', 'فيينا', 'سالزبورغ'],
    'PT': ['portugal', 'lisbon', 'porto', 'البرتغال', 'لشبونة'],
    'IE': ['ireland', 'dublin', 'أيرلندا', 'دبلن'],
    'GR': ['greece', 'athens', 'thessaloniki', 'اليونان', 'أثينا'],

    # 🎯 الشمال الأوروبي (مهم للحالات مثل Oslo, Norway)
    'NO': ['norway', 'oslo', 'bergen', 'stavanger', 'trondheim',
           'النرويج', 'النروج', 'أوسلو', 'اوسلو', 'بيرغن'],
    'SE': ['sweden', 'stockholm', 'gothenburg', 'malmo', 'malmö',
           'السويد', 'ستوكهولم', 'يوتيبوري', 'مالمو'],
    'DK': ['denmark', 'copenhagen', 'aarhus',
           'الدنمارك', 'الدنمرك', 'كوبنهاغن'],
    'FI': ['finland', 'helsinki', 'espoo', 'tampere',
           'فنلندا', 'هلسنكي'],

    'TR': ['turkey', 'turkiye', 'türkiye', 'istanbul', 'ankara', 'izmir', 'antalya', 'bursa',
           'تركيا', 'إسطنبول', 'استانبول', 'اسطنبول', 'أنقرة', 'انقرة', 'إزمير', 'أنطاليا', 'بورصة'],
    'IR': ['iran', 'tehran', 'teheran', 'isfahan', 'mashhad', 'shiraz', 'tabriz', 'ahvaz', 'qom',
           'إيران', 'ايران', 'طهران', 'تهران', 'أصفهان', 'مشهد', 'شيراز', 'تبريز', 'الأهواز', 'قم'],
    'PK': ['pakistan', 'karachi', 'lahore', 'islamabad', 'rawalpindi', 'peshawar', 'multan',
           'باكستان', 'كراتشي', 'لاهور', 'إسلام أباد', 'إسلام آباد'],
    'IN': ['india', 'mumbai', 'bombay', 'delhi', 'new delhi', 'bangalore', 'bengaluru', 'hyderabad', 'kolkata', 'chennai',
           'الهند', 'مومباي', 'دلهي', 'بنغالور', 'حيدر أباد'],
    'BD': ['bangladesh', 'dhaka', 'chittagong', 'بنغلاديش', 'دكا'],
    'AF': ['afghanistan', 'kabul', 'kandahar', 'أفغانستان', 'افغانستان', 'كابول', 'قندهار'],

    'JP': ['japan', 'tokyo', 'osaka', 'kyoto', 'yokohama',
           'اليابان', 'طوكيو', 'أوساكا', 'كيوتو'],
    'CN': ['china', 'beijing', 'shanghai', 'guangzhou', 'shenzhen', 'hong kong', 'hongkong',
           'الصين', 'بكين', 'شنغهاي', 'هونغ كونغ', 'هونغكونغ'],
    'KR': ['south korea', 'korea', 'seoul', 'busan', 'كوريا الجنوبية', 'كوريا', 'سيول'],
    'TH': ['thailand', 'bangkok', 'phuket', 'تايلاند', 'بانكوك', 'بوكيت'],
    'ID': ['indonesia', 'jakarta', 'bali', 'إندونيسيا', 'اندونيسيا', 'جاكرتا', 'بالي'],
    'MY': ['malaysia', 'kuala lumpur', 'kl,', 'penang', 'ماليزيا', 'كوالالمبور', 'كوالا لمبور'],
    'SG': ['singapore', 'سنغافورة'],
    'PH': ['philippines', 'manila', 'الفلبين', 'مانيلا'],
    'VN': ['vietnam', 'hanoi', 'ho chi minh', 'saigon', 'فيتنام', 'هانوي', 'هوشي منه'],

    'BR': ['brazil', 'brasil', 'sao paulo', 'são paulo', 'rio de janeiro', 'brasilia',
           'البرازيل', 'ساو باولو', 'ريو دي جانيرو'],
    'MX': ['mexico', 'mexico city', 'guadalajara', 'monterrey', 'المكسيك', 'مكسيكو سيتي'],
    'AR': ['argentina', 'buenos aires', 'الأرجنتين', 'الارجنتين', 'بوينس آيرس'],
    'CL': ['chile', 'santiago', 'تشيلي', 'سانتياغو'],
    'CO': ['colombia', 'bogota', 'medellin', 'كولومبيا', 'بوغوتا'],

    'RU': ['russia', 'moscow', 'saint petersburg', 'st. petersburg',
           'روسيا', 'موسكو', 'سان بطرسبرغ'],
    'UA': ['ukraine', 'kyiv', 'kiev', 'odesa', 'lviv',
           'أوكرانيا', 'اوكرانيا', 'كييف'],
    'PL': ['poland', 'warsaw', 'krakow', 'بولندا', 'وارسو'],
    'IL': ['israel', 'tel aviv', 'jerusalem israel', 'haifa',
           'إسرائيل', 'تل أبيب', 'تل ابيب'],

    'ZA': ['south africa', 'johannesburg', 'cape town', 'pretoria',
           'جنوب أفريقيا', 'جوهانسبرغ', 'كيب تاون'],
    'NG': ['nigeria', 'lagos', 'abuja', 'نيجيريا', 'لاغوس'],
    'KE': ['kenya', 'nairobi', 'mombasa', 'كينيا', 'نيروبي'],
    'ET': ['ethiopia', 'addis ababa', 'إثيوبيا', 'أديس أبابا'],
}

# الأعلام المرئية (emoji)
FLAG_TO_COUNTRY = {
    '🇸🇦': 'SA', '🇦🇪': 'AE', '🇪🇬': 'EG', '🇮🇶': 'IQ', '🇰🇼': 'KW',
    '🇶🇦': 'QA', '🇧🇭': 'BH', '🇴🇲': 'OM', '🇾🇪': 'YE', '🇯🇴': 'JO',
    '🇱🇧': 'LB', '🇸🇾': 'SY', '🇵🇸': 'PS', '🇲🇦': 'MA', '🇩🇿': 'DZ',
    '🇹🇳': 'TN', '🇱🇾': 'LY', '🇸🇩': 'SD', '🇸🇴': 'SO', '🇲🇷': 'MR', '🇩🇯': 'DJ',
    '🇺🇸': 'US', '🇬🇧': 'GB', '🇨🇦': 'CA', '🇦🇺': 'AU', '🇫🇷': 'FR',
    '🇩🇪': 'DE', '🇮🇹': 'IT', '🇪🇸': 'ES', '🇳🇱': 'NL', '🇸🇪': 'SE',
    '🇳🇴': 'NO', '🇩🇰': 'DK', '🇫🇮': 'FI', '🇨🇭': 'CH', '🇧🇪': 'BE',
    '🇦🇹': 'AT', '🇮🇪': 'IE', '🇵🇹': 'PT', '🇬🇷': 'GR',
    '🇹🇷': 'TR', '🇮🇷': 'IR', '🇵🇰': 'PK', '🇮🇳': 'IN', '🇧🇩': 'BD', '🇦🇫': 'AF',
    '🇨🇳': 'CN', '🇯🇵': 'JP', '🇰🇷': 'KR', '🇹🇭': 'TH', '🇮🇩': 'ID',
    '🇲🇾': 'MY', '🇸🇬': 'SG', '🇵🇭': 'PH', '🇻🇳': 'VN',
    '🇧🇷': 'BR', '🇲🇽': 'MX', '🇦🇷': 'AR', '🇨🇱': 'CL', '🇨🇴': 'CO',
    '🇷🇺': 'RU', '🇺🇦': 'UA', '🇵🇱': 'PL', '🇮🇱': 'IL', '🇳🇿': 'NZ',
    '🇿🇦': 'ZA', '🇳🇬': 'NG', '🇰🇪': 'KE', '🇪🇹': 'ET',
    '🏴󠁧󠁢󠁥󠁮󠁧󠁿': 'GB',  # علم إنجلترا
    '🏴󠁧󠁢󠁳󠁣󠁴󠁿': 'GB',  # علم اسكتلندا
    '🏴󠁧󠁢󠁷󠁬󠁳󠁿': 'GB',  # علم ويلز
}

# اختصارات الدول الشائعة
COUNTRY_CODE_HINTS = {
    'KSA': 'SA', 'UAE': 'AE', 'UK': 'GB', 'USA': 'US',
    '🇸🇦KSA': 'SA',
}

LANGUAGE_NAMES_AR = {
    'ar': 'العربية', 'en': 'الإنجليزية', 'fr': 'الفرنسية', 'es': 'الإسبانية',
    'de': 'الألمانية', 'it': 'الإيطالية', 'tr': 'التركية', 'fa': 'الفارسية',
    'ur': 'الأردية', 'hi': 'الهندية', 'ja': 'اليابانية', 'ko': 'الكورية',
    'zh': 'الصينية', 'ru': 'الروسية', 'pt': 'البرتغالية', 'nl': 'الهولندية',
    'no': 'النرويجية', 'sv': 'السويدية', 'da': 'الدنماركية', 'fi': 'الفنلندية',
    'pl': 'البولندية', 'uk': 'الأوكرانية', 'th': 'التايلاندية', 'id': 'الإندونيسية',
    'und': 'غير محدد', 'qme': 'وسائط فقط', 'qam': 'منشن فقط', 'in': 'الإندونيسية',
}

# عبارات تدل على عدم السكن في الدولة المذكورة (لتفادي الفخاخ)
RESIDENCE_NEGATIVE_HINTS_AR = [
    'مهتم ب', 'متابع ل', 'أكتب عن', 'محب ل', 'أهوى', 'أعشق',
    'مغترب', 'بعيد عن', 'أحلم ب', 'مشتاق ل',
]

# =====================================================
# Profile Cache
# =====================================================

_PROFILE_CACHE = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 3600  # ساعة

def _cache_get(key):
    with _CACHE_LOCK:
        item = _PROFILE_CACHE.get(key)
        if item and time.time() - item['ts'] < _CACHE_TTL:
            return item['data']
        return None

def _cache_set(key, data):
    with _CACHE_LOCK:
        _PROFILE_CACHE[key] = {'data': data, 'ts': time.time()}

# =====================================================
# Helper Functions
# =====================================================

def format_count(n):
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
    url = url.strip()
    pattern = r'(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)(?:/status/(\d+))?'
    m = re.search(pattern, url)
    if m:
        username = m.group(1)
        tweet_id = m.group(2)
        if username.lower() in ('home', 'explore', 'notifications', 'messages', 'i', 'search', 'compose'):
            return None, None
        return username, tweet_id
    if url.startswith('@'):
        return url[1:], None
    if re.match(r'^[A-Za-z0-9_]+$', url):
        return url, None
    return None, None


def find_flags_in_text(text):
    """يجد كل الأعلام في النص ويُرجع قائمة الدول"""
    if not text:
        return []
    found = []
    # علم إنجلترا (تركيب خاص)
    if '🏴󠁧󠁢󠁥󠁮󠁧󠁿' in text:
        found.append('GB')
    if '🏴󠁧󠁢󠁳󠁣󠁴󠁿' in text or '🏴󠁧󠁢󠁷󠁬󠁳󠁿' in text:
        found.append('GB')
    # الأعلام العادية
    for flag, code in FLAG_TO_COUNTRY.items():
        if len(flag) <= 4 and flag in text:  # تجاوز tag-based flags
            count = text.count(flag)
            for _ in range(count):
                found.append(code)
    return found


# إزالة التشكيل العربي والتطويل
_ARABIC_DIACRITICS_RE = re.compile(r'[\u064B-\u0652\u0670\u0640]')

def _normalize_arabic(text):
    """إزالة التشكيل والتطويل لتحسين المطابقة"""
    if not text:
        return ''
    # احذف التشكيل
    text = _ARABIC_DIACRITICS_RE.sub('', text)
    # وحّد الألف
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    # وحّد الياء/الألف المقصورة
    text = text.replace('ى', 'ي')
    # وحّد التاء المربوطة (للبحث فقط)
    text = text.replace('ة', 'ه')
    return text


def find_keywords_in_text(text):
    """يجد كل أسماء المدن/الدول في النص (يدعم التشكيل والبادئات العربية)"""
    if not text:
        return []
    text_lower = text.lower()
    text_normalized = _normalize_arabic(text_lower)
    matches = []
    for code, keywords in LOCATION_KEYWORDS.items():
        for kw in keywords:
            kw_low = kw.lower()
            kw_normalized = _normalize_arabic(kw_low)
            
            # 1. مطابقة كلمة كاملة (boundaries حروف)
            full_match = re.search(
                r'(?:^|[^A-Za-z\u0600-\u06FF])' + re.escape(kw_low) + r'(?:$|[^A-Za-z\u0600-\u06FF])',
                text_lower
            )
            if full_match:
                matches.append((code, kw, len(kw)))
                break
            
            # 2. مع التطبيع العربي (لتجاوز التشكيل)
            full_match_norm = re.search(
                r'(?:^|[^A-Za-z\u0600-\u06FF])' + re.escape(kw_normalized) + r'(?:$|[^A-Za-z\u0600-\u06FF])',
                text_normalized
            )
            if full_match_norm:
                matches.append((code, kw, len(kw)))
                break
            
            # 3. للكلمات العربية التي تبدأ بـ ال - اسمح ببادئات (ب، ل، و، ف، ك، س)
            # مثال: "العراق" → match "بالعراق" أو "للعراق"
            if kw.startswith('ال'):
                pattern_with_prefix = r'(?:^|[^A-Za-z\u0600-\u06FF])[بلوفكس]?' + re.escape(kw_normalized) + r'(?:$|[^A-Za-z\u0600-\u06FF])'
                if re.search(pattern_with_prefix, text_normalized):
                    matches.append((code, kw, len(kw)))
                    break
    return matches


def has_negative_residence_context(text, country_keyword):
    """يفحص إذا كان السياق ينفي السكن (مثل 'مهتم بالعراق' لكن لا يسكن فيه)"""
    if not text or not country_keyword:
        return False
    text_normalized = _normalize_arabic(text.lower())
    kw_normalized = _normalize_arabic(country_keyword.lower())
    # ابحث عن العبارات السلبية قبل الكلمة
    for hint in RESIDENCE_NEGATIVE_HINTS_AR:
        hint_norm = _normalize_arabic(hint.lower())
        # مثال: "مهتم بالعراق"
        pattern = re.escape(hint_norm) + r'\s*\S{0,15}?\s*[بلوفكس]?' + re.escape(kw_normalized)
        if re.search(pattern, text_normalized):
            return True
    return False


# عبارات تدل بقوة على السكن في الدولة
RESIDENCE_POSITIVE_HINTS_AR = [
    'من العراق', 'من السعودية', 'من مصر', 'من الإمارات', 'من الكويت',
    'مقيم في', 'أعيش في', 'ساكن في', 'من اهل', 'من أهل', 'مولود في',
    'مدينتي', 'بلدي', 'وطني',
    # عبارات شعرية/عاطفية تدل غالباً على الانتماء
    'مصاب ب', 'حبيبتي', 'يا بلادي',
]

def has_positive_residence_context(text, country_keyword):
    """يفحص إذا كان السياق يؤكد السكن/الانتماء بقوة"""
    if not text or not country_keyword:
        return False
    text_normalized = _normalize_arabic(text.lower())
    kw_normalized = _normalize_arabic(country_keyword.lower())
    for hint in RESIDENCE_POSITIVE_HINTS_AR:
        hint_norm = _normalize_arabic(hint.lower())
        pattern = re.escape(hint_norm) + r'\s*\S{0,10}?\s*[بلوفكس]?' + re.escape(kw_normalized)
        if re.search(pattern, text_normalized):
            return True
    return False


# =====================================================
# المحرك الذكي - 7 طبقات كشف
# =====================================================

# أوزان كل مصدر (الأعلى = أقوى)
SOURCE_WEIGHTS = {
    'location_field_exact': 100,    # حقل الموقع مع مدينة دقيقة (مثل "Riyadh, SA")
    'location_field_country': 95,   # حقل الموقع مع اسم دولة فقط
    'location_field_flag': 95,       # علم في حقل الموقع
    'flag_in_bio': 80,               # علم في البايو (يعرّف المستخدم نفسه)
    'flag_in_name': 70,              # علم في الاسم الظاهر
    'city_in_bio': 75,               # مدينة في البايو
    'country_in_bio': 65,            # دولة في البايو (قد لا يسكن)
    'city_in_name': 70,              # مدينة في الاسم
    'image_landmark': 70,            # معلم في الصورة (AI Vision)
    'image_text': 65,                # نص جغرافي في الصورة (لوحة، علامة)
    'tweet_city': 35,                # مدينة في نص التغريدة (قد يكون موضوع فقط)
    'tweet_flag': 40,                # علم في التغريدة
    'language_dialect': 25,          # اللغة/اللهجة
}


def smart_detect_country(profile_data, tweet_data=None, image_analysis=None):
    """
    🎯 المحرك الذكي متعدد الطبقات
    يجمع كل الإشارات ويُرجع أفضل دولة مع الثقة + قائمة الأدلة
    
    profile_data: dict من fetch_x_user_profile
    tweet_data: dict من fetch_x_tweet (اختياري)
    image_analysis: dict من analyze_post_images (اختياري)
    """
    scores = {}     # country_code → total_score
    evidence = {}   # country_code → list of evidence strings
    sources = {}    # country_code → set of sources used
    
    def add_score(code, source_key, evidence_text):
        if not code:
            return
        weight = SOURCE_WEIGHTS.get(source_key, 30)
        scores[code] = scores.get(code, 0) + weight
        evidence.setdefault(code, []).append(evidence_text)
        sources.setdefault(code, set()).add(source_key)
    
    # ============================================
    # الطبقة 1️⃣: حقل الموقع الرسمي (الأقوى)
    # ============================================
    location_field = (profile_data.get('location_field') or '').strip()
    if location_field:
        # 1.أ - علم في الحقل
        flags = find_flags_in_text(location_field)
        for flag_code in flags:
            add_score(flag_code, 'location_field_flag',
                     f"علم في حقل الموقع: \"{location_field}\"")
        
        # 1.ب - مدينة/دولة في الحقل
        kw_matches = find_keywords_in_text(location_field)
        if kw_matches:
            # أولوية لأطول مطابقة (أكثر تحديداً)
            kw_matches.sort(key=lambda x: -x[2])
            best_code, best_kw, _ = kw_matches[0]
            # نوع المطابقة: مدينة محددة (طول > 4) = exact، اسم دولة قصير = country
            source = 'location_field_exact' if len(best_kw) >= 5 else 'location_field_country'
            add_score(best_code, source, f"مطابقة \"{best_kw}\" في حقل الموقع: \"{location_field}\"")
    
    # ============================================
    # الطبقة 2️⃣: البايو
    # ============================================
    bio = (profile_data.get('bio') or '').strip()
    if bio:
        # 2.أ - أعلام
        bio_flags = find_flags_in_text(bio)
        for flag_code in bio_flags:
            add_score(flag_code, 'flag_in_bio', f"علم في البايو ({X_COUNTRY_MAP.get(flag_code,{}).get('ar','')})")
        
        # 2.ب - مدن/دول
        bio_matches = find_keywords_in_text(bio)
        for code, kw, length in bio_matches:
            # تحقق من السياق الإيجابي أولاً (مثل 'مصاب بالعراق' = انتماء قوي)
            if has_positive_residence_context(bio, kw):
                add_score(code, 'city_in_bio', f"انتماء/سكن واضح: \"{kw}\" في البايو")
                continue
            # ثم السياق السلبي ("مهتم بـ..." لا يعني سكن)
            if has_negative_residence_context(bio, kw):
                # إعطاء وزن أقل
                scores[code] = scores.get(code, 0) + 20
                evidence.setdefault(code, []).append(f"إشارة ضعيفة في البايو لـ \"{kw}\" (سياق غير سكني)")
                continue
            source = 'city_in_bio' if length >= 5 else 'country_in_bio'
            add_score(code, source, f"\"{kw}\" في البايو")
    
    # ============================================
    # الطبقة 3️⃣: الاسم الظاهر
    # ============================================
    name = (profile_data.get('name') or '').strip()
    if name:
        # 3.أ - أعلام
        name_flags = find_flags_in_text(name)
        for flag_code in name_flags:
            add_score(flag_code, 'flag_in_name', f"علم في الاسم: \"{name}\"")
        
        # 3.ب - مدن/دول
        name_matches = find_keywords_in_text(name)
        for code, kw, length in name_matches:
            source = 'city_in_name' if length >= 5 else 'country_in_bio'
            add_score(code, source, f"\"{kw}\" في الاسم")
        
        # 3.ج - اختصارات (KSA, UK, UAE)
        for hint, code in COUNTRY_CODE_HINTS.items():
            if re.search(r'\b' + re.escape(hint) + r'\b', name, re.IGNORECASE):
                add_score(code, 'flag_in_name', f"اختصار \"{hint}\" في الاسم")
    
    # ============================================
    # الطبقة 4️⃣: نص التغريدة (اختياري)
    # ============================================
    if tweet_data:
        tweet_text = tweet_data.get('text') or tweet_data.get('raw_text') or ''
        if tweet_text:
            tw_flags = find_flags_in_text(tweet_text)
            for flag_code in tw_flags:
                add_score(flag_code, 'tweet_flag', f"علم في التغريدة")
            
            tw_matches = find_keywords_in_text(tweet_text)
            for code, kw, length in tw_matches:
                add_score(code, 'tweet_city', f"\"{kw}\" مذكورة في التغريدة")
    
    # ============================================
    # الطبقة 5️⃣: تحليل الصور بالذكاء الاصطناعي (اختياري)
    # ============================================
    if image_analysis:
        for finding in image_analysis.get('findings', []):
            code = finding.get('country_code')
            if not code:
                continue
            kind = finding.get('kind', 'image_landmark')
            ev_text = finding.get('description', 'دليل من الصورة')
            add_score(code, kind, f"📸 {ev_text}")
    
    # ============================================
    # القرار النهائي
    # ============================================
    if not scores:
        return {
            'country_code': None,
            'confidence': 0,
            'evidence': ['لم يتم العثور على أي دلائل'],
            'sources_used': [],
            'all_scores': {},
        }
    
    # احسب نسبة بين أعلى وثاني أعلى نتيجة
    sorted_codes = sorted(scores.items(), key=lambda x: -x[1])
    best_code, best_score = sorted_codes[0]
    second_score = sorted_codes[1][1] if len(sorted_codes) > 1 else 0
    
    # حساب الثقة:
    # - النتيجة الخام مقسومة على 100 = ثقة أساسية (max 100)
    # - مع تعديل بناءً على نسبة الفجوة عن الثاني
    base_confidence = min(int(best_score), 100)
    
    if second_score > 0:
        gap_ratio = (best_score - second_score) / best_score
        # إذا الفجوة صغيرة (< 30%) = نقص الثقة
        if gap_ratio < 0.3:
            base_confidence = int(base_confidence * 0.85)
    
    # لا تتجاوز 95% إلا إذا كان لدينا حقل موقع موثوق + علم
    has_official_field = 'location_field_exact' in sources.get(best_code, set()) or \
                         'location_field_flag' in sources.get(best_code, set())
    if has_official_field and best_score >= 95:
        base_confidence = min(95, max(base_confidence, 90))
    
    final_confidence = max(0, min(100, base_confidence))
    
    return {
        'country_code': best_code,
        'confidence': final_confidence,
        'evidence': evidence.get(best_code, []),
        'sources_used': sorted(sources.get(best_code, set())),
        'all_scores': dict(sorted_codes[:5]),  # أعلى 5
        'raw_score': best_score,
    }


# =====================================================
# AI Vision: تحليل صور المنشورات (سيُستدعى من app.py)
# =====================================================

def analyze_post_images_with_ai(image_urls, vision_callback=None):
    """
    تحليل صور المنشور باستخدام دالة AI Vision خارجية
    
    vision_callback: دالة تأخذ قائمة URLs و prompt وتُرجع نص التحليل
                     (يُستخدم understand_images من Streamlit)
    
    يُرجع dict مع 'findings': قائمة { country_code, kind, description }
    """
    if not image_urls or not vision_callback:
        return {'findings': [], 'raw_text': ''}
    
    prompt = """
حلل هذه الصور لاستخراج أي إشارات جغرافية تساعد في تحديد البلد:
1. معالم سياحية معروفة (برج، مسجد، مبنى مميز)
2. لوحات سيارات (شكلها، لونها، الرموز الجغرافية)
3. لافتات أو نصوص بلغة معينة
4. أعلام دول
5. ملابس تقليدية (شماغ، كوفية، عباءة، عمامة...)
6. عملات نقدية
7. علامات تجارية محلية معروفة

أعطني الإجابة بالشكل التالي بالضبط:
DETECTED_COUNTRY: [رمز ISO للدولة بحرفين، مثل SA أو US، أو NONE إذا لم تتأكد]
KIND: [landmark / text / flag / clothing / car_plate / other]
DESCRIPTION: [وصف قصير بالعربية لما رأيته يدل على البلد]
CONFIDENCE: [HIGH / MEDIUM / LOW]

إذا كان هناك أكثر من إشارة، اذكر كل واحدة بشكل منفصل بنفس الصيغة.
إذا لم تجد أي إشارة جغرافية، اكتب: NO_GEO_SIGNALS
"""
    
    try:
        result_text = vision_callback(image_urls, prompt)
    except Exception as e:
        return {'findings': [], 'raw_text': f'خطأ AI: {e}', 'error': str(e)}
    
    if not result_text or 'NO_GEO_SIGNALS' in result_text.upper():
        return {'findings': [], 'raw_text': result_text}
    
    findings = []
    # استخرج كل الـ blocks
    blocks = re.split(r'(?=DETECTED_COUNTRY:)', result_text)
    for block in blocks:
        if 'DETECTED_COUNTRY' not in block:
            continue
        country_match = re.search(r'DETECTED_COUNTRY:\s*([A-Z]{2})', block)
        if not country_match:
            continue
        code = country_match.group(1)
        if code == 'NONE' or code not in X_COUNTRY_MAP:
            continue
        
        kind_match = re.search(r'KIND:\s*(\w+)', block)
        kind = (kind_match.group(1).lower() if kind_match else 'landmark').strip()
        kind_map = {
            'landmark': 'image_landmark',
            'text': 'image_text',
            'flag': 'image_landmark',
            'clothing': 'image_landmark',
            'car_plate': 'image_landmark',
            'other': 'image_text',
        }
        
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?:CONFIDENCE:|DETECTED_COUNTRY:|$)', block, re.DOTALL)
        desc = desc_match.group(1).strip() if desc_match else 'دليل في الصورة'
        # نظّف الوصف
        desc = re.sub(r'\s+', ' ', desc)[:200]
        
        findings.append({
            'country_code': code,
            'kind': kind_map.get(kind, 'image_landmark'),
            'description': desc,
        })
    
    return {'findings': findings, 'raw_text': result_text}


# =====================================================
# Main API Functions
# =====================================================

def fetch_x_user_profile(username, timeout=15, use_cache=True):
    """جلب بروفايل المستخدم من fxtwitter API مع كاش"""
    cache_key = f"profile:{username.lower()}"
    if use_cache:
        cached = _cache_get(cache_key)
        if cached:
            return cached
    
    url = f"{FXTWITTER_API}/{username}"
    try:
        r = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if r.status_code != 200:
            result = {"success": False, "error": f"HTTP {r.status_code}"}
            return result
        
        data = r.json()
        if data.get("code") != 200 or not data.get("user"):
            return {"success": False, "error": data.get("message", "حساب غير موجود")}
        
        u = data["user"]
        result = {
            "success": True,
            "screen_name": u.get("screen_name"),
            "user_id": u.get("id"),
            "name": u.get("name"),
            "bio": u.get("description", ""),
            "location_field": u.get("location", ""),
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
        if use_cache:
            _cache_set(cache_key, result)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_x_tweet(username, tweet_id, timeout=15):
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
        media = t.get("media", {})
        
        # استخرج صور المنشور
        photos = []
        if isinstance(media, dict):
            for p in (media.get("photos") or []):
                if isinstance(p, dict) and p.get("url"):
                    photos.append(p["url"])
            for v in (media.get("videos") or []):
                # خذ الـ thumbnail للفيديو
                if isinstance(v, dict) and v.get("thumbnail_url"):
                    photos.append(v["thumbnail_url"])
        
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
            "media": media,
            "photos_urls": photos,  # 🎯 لاستخدامها مع AI Vision
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


def analyze_x_account(username_or_url, timeout=15, image_analysis=None):
    """تحليل حساب X كامل مع المحرك الذكي"""
    if username_or_url.startswith("http"):
        username, _ = parse_x_url(username_or_url)
    else:
        username = username_or_url.lstrip("@").strip()
    
    if not username:
        return {"success": False, "error": "اسم مستخدم غير صحيح"}
    
    profile = fetch_x_user_profile(username, timeout=timeout)
    if not profile.get("success"):
        return profile
    
    # المحرك الذكي
    detection = smart_detect_country(profile, tweet_data=None, image_analysis=image_analysis)
    
    code = detection['country_code']
    country_info = X_COUNTRY_MAP.get(code, {}) if code else {}
    
    profile["country_code"] = code
    profile["country_flag"] = country_info.get("flag", "❓")
    profile["country_name_ar"] = country_info.get("ar", "غير محدد")
    profile["country_name_en"] = country_info.get("en", "Unknown")
    profile["confidence"] = detection['confidence']
    profile["evidence"] = "; ".join(detection['evidence'][:3])
    profile["all_evidence"] = detection['evidence']
    profile["sources_used"] = detection['sources_used']
    profile["all_scores"] = detection['all_scores']
    profile["detection_source"] = "🧠 محرك ذكي متعدد الطبقات"
    
    return profile


def analyze_x_tweet(tweet_url_or_id, username=None, timeout=15, vision_callback=None):
    """تحليل تغريدة + استنتاج موقع المؤلف بالمحرك الذكي + AI Vision"""
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
    
    # 1. جلب التغريدة
    tweet = fetch_x_tweet(username, tweet_id, timeout=timeout)
    if not tweet.get("success"):
        return tweet
    
    # 2. جلب البروفايل الكامل (للحصول على location field كاملاً)
    profile = fetch_x_user_profile(username, timeout=timeout)
    if not profile.get("success"):
        # استخدم بيانات author من التغريدة كـ fallback
        profile = {
            "success": True,
            "screen_name": tweet.get("author_screen_name"),
            "user_id": tweet.get("author_id"),
            "name": tweet.get("author_name"),
            "bio": tweet.get("author_bio"),
            "location_field": tweet.get("author_location", ""),
            "avatar_url": tweet.get("author_avatar"),
            "followers": tweet.get("author_followers", 0),
        }
    
    # 3. تحليل الصور بالـ AI (إن توفر)
    image_analysis = None
    if vision_callback and tweet.get("photos_urls"):
        try:
            image_analysis = analyze_post_images_with_ai(
                tweet["photos_urls"][:3],  # أول 3 صور فقط لتوفير الوقت/الرصيد
                vision_callback=vision_callback,
            )
        except Exception as e:
            image_analysis = {'findings': [], 'error': str(e)}
    
    # 4. تشغيل المحرك الذكي على كل المصادر
    detection = smart_detect_country(profile, tweet_data=tweet, image_analysis=image_analysis)
    
    code = detection['country_code']
    country_info = X_COUNTRY_MAP.get(code, {}) if code else {}
    
    tweet["country_code"] = code
    tweet["country_flag"] = country_info.get("flag", "❓")
    tweet["country_name_ar"] = country_info.get("ar", "غير محدد")
    tweet["confidence"] = detection['confidence']
    tweet["evidence"] = "; ".join(detection['evidence'][:3])
    tweet["all_evidence"] = detection['evidence']
    tweet["sources_used"] = detection['sources_used']
    tweet["all_scores"] = detection['all_scores']
    tweet["detection_source"] = "🧠 محرك ذكي متعدد الطبقات"
    tweet["language_ar"] = LANGUAGE_NAMES_AR.get(tweet.get("lang"), tweet.get("lang", "غير محدد"))
    tweet["image_analysis"] = image_analysis or {}
    
    # دمج بيانات البروفايل (للعرض في الجدول)
    tweet["user_location_field"] = profile.get("location_field", "")
    tweet["user_bio"] = profile.get("bio", "")
    tweet["user_followers_full"] = profile.get("followers", tweet.get("author_followers", 0))
    
    return tweet


# =====================================================
# Backward Compatibility (aliases للإصدار القديم)
# =====================================================

X_REGION_MAP = X_COUNTRY_MAP
LANGUAGE_NAMES_AR_X = LANGUAGE_NAMES_AR


def aggregate_user_tweets(results, min_confidence=30):
    """تجميع ذكي - يفضل القرار من البروفايل (location field) إن وُجد"""
    by_user = {}
    for r in results:
        if not r.get("success") and r.get("status") != "✅ نجح":
            continue
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
        
        # حقل الموقع من البروفايل (الأولوية)
        loc_field = (first.get("user_location_field") or 
                     first.get("author_location") or 
                     first.get("location_field", ""))
        
        # 1. حاول إعادة تشغيل المحرك الذكي على بيانات البروفايل
        if loc_field or first.get("user_bio") or name:
            fake_profile = {
                "location_field": loc_field,
                "bio": first.get("user_bio") or first.get("author_bio", ""),
                "name": name,
            }
            detection = smart_detect_country(fake_profile, tweet_data=None)
            final_region = detection['country_code']
            final_confidence = detection['confidence']
            final_evidence = "; ".join(detection['evidence'][:3])
            final_method = "🧠 محرك ذكي (من البروفايل)"
        else:
            final_region = None
            final_confidence = 0
            final_evidence = ""
            final_method = ""
        
        # 2. إذا لم نجد، صوّت من نتائج التغريدات
        if not final_region:
            votes = {}
            best_evidence_per_country = {}
            for it in items:
                cc = it.get("country_code") or it.get("region")
                conf = it.get("confidence") or it.get("region_confidence", 0)
                if cc and conf >= min_confidence:
                    votes[cc] = votes.get(cc, 0) + 1
                    if cc not in best_evidence_per_country:
                        best_evidence_per_country[cc] = it.get("evidence", "")
            
            if votes:
                best = max(votes, key=votes.get)
                total = sum(votes.values())
                ratio = votes[best] / total
                final_confidence = int(min(50 + ratio * 40, 90))
                final_region = best
                final_method = f"🗳️ تصويت ({votes[best]}/{total} تغريدات)"
                final_evidence = best_evidence_per_country.get(best, "")
        
        country_info = X_COUNTRY_MAP.get(final_region, {}) if final_region else {}
        
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
            "user_verified_type": first.get("user_verified_type", ""),
            "tweet_count": len(items),
            "total_likes": total_likes,
            "total_replies": total_replies,
            "dominant_language": dominant_lang_ar,
            "location_field": loc_field,
            "user_bio": first.get("user_bio") or first.get("author_bio", ""),
            "final_region": final_region,
            "final_region_flag": country_info.get("flag", ""),
            "final_region_name_ar": country_info.get("ar", ""),
            "final_confidence": final_confidence,
            "final_method": final_method,
            "final_evidence": final_evidence,
        }
    
    return aggregated


def analyze_x_tweet_legacy(url, vision_callback=None):
    """Wrapper يعطي الحقول التي يتوقعها app.py القديم"""
    result = analyze_x_tweet(url, vision_callback=vision_callback)
    if not result.get("success"):
        return {
            "tweet_url": url,
            "status": "❌ فشل",
            "error": result.get("error", "خطأ غير معروف"),
        }
    
    media = result.get("media", {})
    if isinstance(media, dict):
        all_media = (media.get("photos") or []) + (media.get("videos") or [])
    else:
        all_media = []
    
    media_count = len(all_media)
    media_type = ""
    if all_media:
        first_m = all_media[0]
        media_type = first_m.get("type", "photo") if isinstance(first_m, dict) else "photo"
    
    text = result.get("text", "")
    hashtags = re.findall(r'#(\w+)', text)
    mentions = re.findall(r'@(\w+)', text)
    
    # هل تم استخدام تحليل صور؟
    img_findings = (result.get("image_analysis") or {}).get("findings", [])
    used_image_ai = bool(img_findings)
    
    return {
        "tweet_url": result.get("tweet_url"),
        "tweet_id": result.get("tweet_id"),
        "user_id": result.get("author_id"),
        "user_screen_name": result.get("author_screen_name"),
        "user_name": result.get("author_name"),
        "user_profile_image": result.get("author_avatar"),
        "user_blue_verified": result.get("author_verified"),
        "user_verified_type": "",
        "user_location_field": result.get("user_location_field", ""),
        "user_bio": result.get("user_bio", ""),
        "text": text,
        "lang": result.get("lang", ""),
        "lang_name_ar": LANGUAGE_NAMES_AR.get(result.get("lang"), result.get("lang", "")),
        "created_at": result.get("created_at", ""),
        "favorite_count": result.get("likes", 0),
        "conversation_count": result.get("replies", 0),
        "media_count": media_count,
        "media_type": media_type,
        "used_image_ai": "✅" if used_image_ai else "—",
        "hashtags": ", ".join(hashtags[:5]),
        "mentions": ", ".join(mentions[:5]),
        "region": result.get("country_code"),
        "region_flag": result.get("country_flag", ""),
        "region_name_ar": result.get("country_name_ar", ""),
        "region_confidence": result.get("confidence", 0),
        "region_evidence": result.get("evidence", ""),
        "region_source": result.get("detection_source", ""),
        "all_evidence": result.get("all_evidence", []),
        "sources_used": result.get("sources_used", []),
        "image_findings": img_findings,
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


# =====================================================
# Test
# =====================================================

if __name__ == "__main__":
    print("🐦 X Smart Analyzer v4 - اختبار الحالات المُشكلة\n")
    
    # الحالات من الصورة
    test_users = [
        ("AzharJumaili", "🇳🇴 النرويج (Oslo, Norway في حقل الموقع)"),
        ("basharalsabti", "🇮🇶 العراق (البايو فيه 'العراق')"),
        ("707Reno", "🇸🇦 السعودية (🇸🇦 في البايو) أو 🇬🇧 (في الاسم)"),
        ("DAbdulljabar", "🇮🇶 العراق (محتمل من البايو)"),
        ("ibeli0", "🇸🇦 السعودية (Jeddah)"),
        ("salim_Aljomaili", "🇬🇧 المملكة المتحدة (England, UK)"),
        ("zniby16372", "🇬🇧 (Scotland)"),
    ]
    
    for username, expected in test_users:
        print("=" * 75)
        print(f"🔍 @{username}")
        print(f"   المتوقع: {expected}")
        result = analyze_x_account(username)
        if result.get("success"):
            print(f"   📍 حقل الموقع: \"{result.get('location_field', '')}\"")
            print(f"   📝 البايو: {(result.get('bio') or '')[:80]}")
            print(f"   👤 الاسم: {result.get('name')}")
            print(f"   🌍 الكشف: {result.get('country_flag')} {result.get('country_name_ar')}")
            print(f"   🎯 الثقة: {result.get('confidence')}%")
            print(f"   📊 المصادر: {', '.join(result.get('sources_used', []))}")
            print(f"   🔎 الأدلة:")
            for e in result.get('all_evidence', [])[:5]:
                print(f"      • {e}")
        else:
            print(f"   ❌ {result.get('error')}")
        print()
