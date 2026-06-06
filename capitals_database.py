"""
🏛️ قاعدة العواصم الذكية لـ Baseer v2.0.0
═══════════════════════════════════════════════════════════════
عند فشل استخراج المنطقة من BIO/Nickname/Username:
نعرض عاصمة الدولة كتقدير ذكي مع شارة "تقديري 40%"
═══════════════════════════════════════════════════════════════
"""

CAPITALS_AR = {
    # 🇸🇦 الخليج العربي
    'Saudi Arabia': {'en': 'Riyadh', 'ar': 'الرياض'},
    'United Arab Emirates': {'en': 'Abu Dhabi', 'ar': 'أبوظبي'},
    'Kuwait': {'en': 'Kuwait City', 'ar': 'مدينة الكويت'},
    'Qatar': {'en': 'Doha', 'ar': 'الدوحة'},
    'Bahrain': {'en': 'Manama', 'ar': 'المنامة'},
    'Oman': {'en': 'Muscat', 'ar': 'مسقط'},
    'Yemen': {'en': 'Sanaa', 'ar': 'صنعاء'},

    # 🌍 الوطن العربي
    'Egypt': {'en': 'Cairo', 'ar': 'القاهرة'},
    'Jordan': {'en': 'Amman', 'ar': 'عمّان'},
    'Lebanon': {'en': 'Beirut', 'ar': 'بيروت'},
    'Iraq': {'en': 'Baghdad', 'ar': 'بغداد'},
    'Syria': {'en': 'Damascus', 'ar': 'دمشق'},
    'Palestine': {'en': 'Jerusalem', 'ar': 'القدس'},
    'Morocco': {'en': 'Rabat', 'ar': 'الرباط'},
    'Algeria': {'en': 'Algiers', 'ar': 'الجزائر العاصمة'},
    'Tunisia': {'en': 'Tunis', 'ar': 'تونس العاصمة'},
    'Libya': {'en': 'Tripoli', 'ar': 'طرابلس'},
    'Sudan': {'en': 'Khartoum', 'ar': 'الخرطوم'},
    'Somalia': {'en': 'Mogadishu', 'ar': 'مقديشو'},

    # 🌏 آسيا
    'South Korea': {'en': 'Seoul', 'ar': 'سيول'},
    'Japan': {'en': 'Tokyo', 'ar': 'طوكيو'},
    'China': {'en': 'Beijing', 'ar': 'بكين'},
    'Taiwan': {'en': 'Taipei', 'ar': 'تايبيه'},
    'Hong Kong': {'en': 'Hong Kong', 'ar': 'هونغ كونغ'},
    'Singapore': {'en': 'Singapore', 'ar': 'سنغافورة'},
    'Thailand': {'en': 'Bangkok', 'ar': 'بانكوك'},
    'Vietnam': {'en': 'Hanoi', 'ar': 'هانوي'},
    'Indonesia': {'en': 'Jakarta', 'ar': 'جاكرتا'},
    'Malaysia': {'en': 'Kuala Lumpur', 'ar': 'كوالالمبور'},
    'Philippines': {'en': 'Manila', 'ar': 'مانيلا'},
    'India': {'en': 'New Delhi', 'ar': 'نيودلهي'},
    'Pakistan': {'en': 'Islamabad', 'ar': 'إسلام آباد'},
    'Bangladesh': {'en': 'Dhaka', 'ar': 'دكا'},
    'Sri Lanka': {'en': 'Colombo', 'ar': 'كولومبو'},
    'Iran': {'en': 'Tehran', 'ar': 'طهران'},
    'Israel': {'en': 'Tel Aviv', 'ar': 'تل أبيب'},

    # 🌍 أوروبا
    'United Kingdom': {'en': 'London', 'ar': 'لندن'},
    'France': {'en': 'Paris', 'ar': 'باريس'},
    'Germany': {'en': 'Berlin', 'ar': 'برلين'},
    'Italy': {'en': 'Rome', 'ar': 'روما'},
    'Spain': {'en': 'Madrid', 'ar': 'مدريد'},
    'Portugal': {'en': 'Lisbon', 'ar': 'لشبونة'},
    'Netherlands': {'en': 'Amsterdam', 'ar': 'أمستردام'},
    'Belgium': {'en': 'Brussels', 'ar': 'بروكسل'},
    'Switzerland': {'en': 'Bern', 'ar': 'برن'},
    'Austria': {'en': 'Vienna', 'ar': 'فيينا'},
    'Turkey': {'en': 'Ankara', 'ar': 'أنقرة'},
    'Russia': {'en': 'Moscow', 'ar': 'موسكو'},
    'Greece': {'en': 'Athens', 'ar': 'أثينا'},
    'Poland': {'en': 'Warsaw', 'ar': 'وارسو'},
    'Sweden': {'en': 'Stockholm', 'ar': 'ستوكهولم'},
    'Norway': {'en': 'Oslo', 'ar': 'أوسلو'},
    'Denmark': {'en': 'Copenhagen', 'ar': 'كوبنهاغن'},
    'Finland': {'en': 'Helsinki', 'ar': 'هلسنكي'},
    'Ireland': {'en': 'Dublin', 'ar': 'دبلن'},

    # 🌎 الأمريكتان
    'United States': {'en': 'Washington', 'ar': 'واشنطن'},
    'Canada': {'en': 'Ottawa', 'ar': 'أوتاوا'},
    'Mexico': {'en': 'Mexico City', 'ar': 'مكسيكو سيتي'},
    'Brazil': {'en': 'Brasilia', 'ar': 'برازيليا'},
    'Argentina': {'en': 'Buenos Aires', 'ar': 'بوينس آيرس'},
    'Colombia': {'en': 'Bogota', 'ar': 'بوغوتا'},
    'Chile': {'en': 'Santiago', 'ar': 'سانتياغو'},
    'Peru': {'en': 'Lima', 'ar': 'ليما'},
    'Venezuela': {'en': 'Caracas', 'ar': 'كاراكاس'},
    'Puerto Rico': {'en': 'San Juan', 'ar': 'سان خوان'},

    # 🌍 أفريقيا
    'Nigeria': {'en': 'Abuja', 'ar': 'أبوجا'},
    'South Africa': {'en': 'Pretoria', 'ar': 'بريتوريا'},
    'Kenya': {'en': 'Nairobi', 'ar': 'نيروبي'},
    'Ghana': {'en': 'Accra', 'ar': 'أكرا'},
    'Tanzania': {'en': 'Dodoma', 'ar': 'دودوما'},
    'Ethiopia': {'en': 'Addis Ababa', 'ar': 'أديس أبابا'},

    # 🌏 أوقيانوسيا
    'Australia': {'en': 'Canberra', 'ar': 'كانبيرا'},
    'New Zealand': {'en': 'Wellington', 'ar': 'ويلينغتون'},
}

# 🏛️ المدن الكبرى (بديل أفضل من العاصمة الإدارية أحياناً)
MAJOR_CITIES_AR = {
    'Saudi Arabia': {'en': 'Riyadh', 'ar': 'الرياض'},
    'United Arab Emirates': {'en': 'Dubai', 'ar': 'دبي'},
    'United States': {'en': 'New York', 'ar': 'نيويورك'},
    'Australia': {'en': 'Sydney', 'ar': 'سيدني'},
    'New Zealand': {'en': 'Auckland', 'ar': 'أوكلاند'},
    'Switzerland': {'en': 'Zurich', 'ar': 'زيورخ'},
    'Brazil': {'en': 'Sao Paulo', 'ar': 'ساو باولو'},
    'Canada': {'en': 'Toronto', 'ar': 'تورنتو'},
    'South Africa': {'en': 'Johannesburg', 'ar': 'جوهانسبرغ'},
    'Italy': {'en': 'Milan', 'ar': 'ميلانو'},
    'Tanzania': {'en': 'Dar es Salaam', 'ar': 'دار السلام'},
}


def lookup_capital(country):
    """
    إرجاع العاصمة أو المدينة الكبرى للدولة كتقدير ذكي
    Returns: dict | None مع confidence منخفض (40%)
    """
    if not country:
        return None

    # نُفضّل المدينة الكبرى على العاصمة الإدارية إن وُجدت
    if country in MAJOR_CITIES_AR:
        info = MAJOR_CITIES_AR[country]
        return {
            'region_en': info['en'],
            'region_ar': info['ar'],
            'confidence': 40,
            'source': 'major_city_estimate',
            'is_estimate': True,
            'estimate_note': f'المدينة الكبرى لـ {country}',
        }
    if country in CAPITALS_AR:
        info = CAPITALS_AR[country]
        return {
            'region_en': info['en'],
            'region_ar': info['ar'],
            'confidence': 40,
            'source': 'capital_estimate',
            'is_estimate': True,
            'estimate_note': f'عاصمة {country}',
        }
    return None


def get_capitals_count():
    return len(CAPITALS_AR) + len(MAJOR_CITIES_AR)


if __name__ == '__main__':
    print(f"📊 عواصم: {len(CAPITALS_AR)}")
    print(f"🏙️ مدن كبرى: {len(MAJOR_CITIES_AR)}")
    print(f"الإجمالي: {get_capitals_count()}")
    for c in ['Italy', 'Saudi Arabia', 'United States', 'Egypt']:
        print(f"\n{c}: {lookup_capital(c)}")
