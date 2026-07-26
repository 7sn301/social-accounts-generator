"""
╔══════════════════════════════════════════════════════════════╗
║  BSR-V221-CTO-WORLD-MAP-COMPLETE-AHMAD-20260726             ║
║  regions_database.py v2.2.1 - World Complete Map            ║
║  Total: 249 countries/territories (ISO 3166-1 alpha-2)      ║
║  Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)        ║
╚══════════════════════════════════════════════════════════════╝

قاعدة بيانات شاملة لجميع دول العالم مع:
- ISO 3166-1 alpha-2 code
- الاسم العربي الرسمي
- الاسم الإنجليزي
- علم Emoji
- المنطقة الزمنية الأساسية (IANA)
- القارة

الاستخدام:
    from regions_database import (
        WORLD_COUNTRIES,
        get_country_info,
        get_country_by_timezone,
        get_flag,
        get_arabic_name,
        get_all_arab_countries,
    )
"""

from typing import Optional, Tuple, List, Dict

# ============================================================
# 🌍 قاعدة البيانات الرئيسية - 249 دولة/إقليم
# الصيغة: "ISO": ("عربي", "English", "🚩", "IANA/Timezone", "Continent")
# ============================================================

WORLD_COUNTRIES: Dict[str, Tuple[str, str, str, str, str]] = {
    # ═══════════ 🇸🇦 الدول العربية (22) ═══════════
    "SA": ("المملكة العربية السعودية", "Saudi Arabia", "🇸🇦", "Asia/Riyadh", "Asia"),
    "AE": ("الإمارات العربية المتحدة", "United Arab Emirates", "🇦🇪", "Asia/Dubai", "Asia"),
    "KW": ("الكويت", "Kuwait", "🇰🇼", "Asia/Kuwait", "Asia"),
    "QA": ("قطر", "Qatar", "🇶🇦", "Asia/Qatar", "Asia"),
    "BH": ("البحرين", "Bahrain", "🇧🇭", "Asia/Bahrain", "Asia"),
    "OM": ("عُمان", "Oman", "🇴🇲", "Asia/Muscat", "Asia"),
    "YE": ("اليمن", "Yemen", "🇾🇪", "Asia/Aden", "Asia"),
    "IQ": ("العراق", "Iraq", "🇮🇶", "Asia/Baghdad", "Asia"),
    "SY": ("سوريا", "Syria", "🇸🇾", "Asia/Damascus", "Asia"),
    "LB": ("لبنان", "Lebanon", "🇱🇧", "Asia/Beirut", "Asia"),
    "JO": ("الأردن", "Jordan", "🇯🇴", "Asia/Amman", "Asia"),
    "PS": ("فلسطين", "Palestine", "🇵🇸", "Asia/Gaza", "Asia"),
    "EG": ("مصر", "Egypt", "🇪🇬", "Africa/Cairo", "Africa"),
    "SD": ("السودان", "Sudan", "🇸🇩", "Africa/Khartoum", "Africa"),
    "LY": ("ليبيا", "Libya", "🇱🇾", "Africa/Tripoli", "Africa"),
    "TN": ("تونس", "Tunisia", "🇹🇳", "Africa/Tunis", "Africa"),
    "DZ": ("الجزائر", "Algeria", "🇩🇿", "Africa/Algiers", "Africa"),
    "MA": ("المغرب", "Morocco", "🇲🇦", "Africa/Casablanca", "Africa"),
    "MR": ("موريتانيا", "Mauritania", "🇲🇷", "Africa/Nouakchott", "Africa"),
    "SO": ("الصومال", "Somalia", "🇸🇴", "Africa/Mogadishu", "Africa"),
    "DJ": ("جيبوتي", "Djibouti", "🇩🇯", "Africa/Djibouti", "Africa"),
    "KM": ("جزر القمر", "Comoros", "🇰🇲", "Indian/Comoro", "Africa"),

    # ═══════════ 🌍 باقي إفريقيا (38) ═══════════
    "NG": ("نيجيريا", "Nigeria", "🇳🇬", "Africa/Lagos", "Africa"),
    "ET": ("إثيوبيا", "Ethiopia", "🇪🇹", "Africa/Addis_Ababa", "Africa"),
    "KE": ("كينيا", "Kenya", "🇰🇪", "Africa/Nairobi", "Africa"),
    "ZA": ("جنوب أفريقيا", "South Africa", "🇿🇦", "Africa/Johannesburg", "Africa"),
    "GH": ("غانا", "Ghana", "🇬🇭", "Africa/Accra", "Africa"),
    "TZ": ("تنزانيا", "Tanzania", "🇹🇿", "Africa/Dar_es_Salaam", "Africa"),
    "UG": ("أوغندا", "Uganda", "🇺🇬", "Africa/Kampala", "Africa"),
    "CI": ("ساحل العاج", "Ivory Coast", "🇨🇮", "Africa/Abidjan", "Africa"),
    "AO": ("أنغولا", "Angola", "🇦🇴", "Africa/Luanda", "Africa"),
    "MZ": ("موزمبيق", "Mozambique", "🇲🇿", "Africa/Maputo", "Africa"),
    "CM": ("الكاميرون", "Cameroon", "🇨🇲", "Africa/Douala", "Africa"),
    "MG": ("مدغشقر", "Madagascar", "🇲🇬", "Indian/Antananarivo", "Africa"),
    "NE": ("النيجر", "Niger", "🇳🇪", "Africa/Niamey", "Africa"),
    "BF": ("بوركينا فاسو", "Burkina Faso", "🇧🇫", "Africa/Ouagadougou", "Africa"),
    "ML": ("مالي", "Mali", "🇲🇱", "Africa/Bamako", "Africa"),
    "MW": ("مالاوي", "Malawi", "🇲🇼", "Africa/Blantyre", "Africa"),
    "ZM": ("زامبيا", "Zambia", "🇿🇲", "Africa/Lusaka", "Africa"),
    "SN": ("السنغال", "Senegal", "🇸🇳", "Africa/Dakar", "Africa"),
    "TD": ("تشاد", "Chad", "🇹🇩", "Africa/Ndjamena", "Africa"),
    "ZW": ("زيمبابوي", "Zimbabwe", "🇿🇼", "Africa/Harare", "Africa"),
    "RW": ("رواندا", "Rwanda", "🇷🇼", "Africa/Kigali", "Africa"),
    "BI": ("بوروندي", "Burundi", "🇧🇮", "Africa/Bujumbura", "Africa"),
    "BJ": ("بنين", "Benin", "🇧🇯", "Africa/Porto-Novo", "Africa"),
    "TG": ("توغو", "Togo", "🇹🇬", "Africa/Lome", "Africa"),
    "SL": ("سيراليون", "Sierra Leone", "🇸🇱", "Africa/Freetown", "Africa"),
    "LR": ("ليبيريا", "Liberia", "🇱🇷", "Africa/Monrovia", "Africa"),
    "CG": ("جمهورية الكونغو", "Republic of the Congo", "🇨🇬", "Africa/Brazzaville", "Africa"),
    "CD": ("جمهورية الكونغو الديمقراطية", "DR Congo", "🇨🇩", "Africa/Kinshasa", "Africa"),
    "CF": ("جمهورية أفريقيا الوسطى", "Central African Republic", "🇨🇫", "Africa/Bangui", "Africa"),
    "GA": ("الغابون", "Gabon", "🇬🇦", "Africa/Libreville", "Africa"),
    "GQ": ("غينيا الاستوائية", "Equatorial Guinea", "🇬🇶", "Africa/Malabo", "Africa"),
    "GN": ("غينيا", "Guinea", "🇬🇳", "Africa/Conakry", "Africa"),
    "GW": ("غينيا بيساو", "Guinea-Bissau", "🇬🇼", "Africa/Bissau", "Africa"),
    "GM": ("غامبيا", "Gambia", "🇬🇲", "Africa/Banjul", "Africa"),
    "CV": ("الرأس الأخضر", "Cape Verde", "🇨🇻", "Atlantic/Cape_Verde", "Africa"),
    "ST": ("ساو تومي وبرينسيبي", "Sao Tome and Principe", "🇸🇹", "Africa/Sao_Tome", "Africa"),
    "SC": ("سيشل", "Seychelles", "🇸🇨", "Indian/Mahe", "Africa"),
    "MU": ("موريشيوس", "Mauritius", "🇲🇺", "Indian/Mauritius", "Africa"),
    "NA": ("ناميبيا", "Namibia", "🇳🇦", "Africa/Windhoek", "Africa"),
    "BW": ("بوتسوانا", "Botswana", "🇧🇼", "Africa/Gaborone", "Africa"),
    "LS": ("ليسوتو", "Lesotho", "🇱🇸", "Africa/Maseru", "Africa"),
    "SZ": ("إسواتيني", "Eswatini", "🇸🇿", "Africa/Mbabane", "Africa"),
    "ER": ("إريتريا", "Eritrea", "🇪🇷", "Africa/Asmara", "Africa"),
    "SS": ("جنوب السودان", "South Sudan", "🇸🇸", "Africa/Juba", "Africa"),
    "EH": ("الصحراء الغربية", "Western Sahara", "🇪🇭", "Africa/El_Aaiun", "Africa"),
    "SH": ("سانت هيلينا", "Saint Helena", "🇸🇭", "Atlantic/St_Helena", "Africa"),
    "IO": ("إقليم المحيط الهندي البريطاني", "British Indian Ocean Territory", "🇮🇴", "Indian/Chagos", "Africa"),
    "YT": ("مايوت", "Mayotte", "🇾🇹", "Indian/Mayotte", "Africa"),
    "RE": ("ريونيون", "Reunion", "🇷🇪", "Indian/Reunion", "Africa"),
    "TF": ("الأراضي الجنوبية الفرنسية", "French Southern Territories", "🇹🇫", "Indian/Kerguelen", "Africa"),

    # ═══════════ 🇪🇺 أوروبا (53) ═══════════
    "GB": ("المملكة المتحدة", "United Kingdom", "🇬🇧", "Europe/London", "Europe"),
    "FR": ("فرنسا", "France", "🇫🇷", "Europe/Paris", "Europe"),
    "DE": ("ألمانيا", "Germany", "🇩🇪", "Europe/Berlin", "Europe"),
    "IT": ("إيطاليا", "Italy", "🇮🇹", "Europe/Rome", "Europe"),
    "ES": ("إسبانيا", "Spain", "🇪🇸", "Europe/Madrid", "Europe"),
    "PT": ("البرتغال", "Portugal", "🇵🇹", "Europe/Lisbon", "Europe"),
    "NL": ("هولندا", "Netherlands", "🇳🇱", "Europe/Amsterdam", "Europe"),
    "BE": ("بلجيكا", "Belgium", "🇧🇪", "Europe/Brussels", "Europe"),
    "CH": ("سويسرا", "Switzerland", "🇨🇭", "Europe/Zurich", "Europe"),
    "AT": ("النمسا", "Austria", "🇦🇹", "Europe/Vienna", "Europe"),
    "SE": ("السويد", "Sweden", "🇸🇪", "Europe/Stockholm", "Europe"),
    "NO": ("النرويج", "Norway", "🇳🇴", "Europe/Oslo", "Europe"),
    "DK": ("الدنمارك", "Denmark", "🇩🇰", "Europe/Copenhagen", "Europe"),
    "FI": ("فنلندا", "Finland", "🇫🇮", "Europe/Helsinki", "Europe"),
    "IS": ("آيسلندا", "Iceland", "🇮🇸", "Atlantic/Reykjavik", "Europe"),
    "IE": ("أيرلندا", "Ireland", "🇮🇪", "Europe/Dublin", "Europe"),
    "PL": ("بولندا", "Poland", "🇵🇱", "Europe/Warsaw", "Europe"),
    "CZ": ("التشيك", "Czech Republic", "🇨🇿", "Europe/Prague", "Europe"),
    "SK": ("سلوفاكيا", "Slovakia", "🇸🇰", "Europe/Bratislava", "Europe"),
    "HU": ("المجر", "Hungary", "🇭🇺", "Europe/Budapest", "Europe"),
    "RO": ("رومانيا", "Romania", "🇷🇴", "Europe/Bucharest", "Europe"),
    "BG": ("بلغاريا", "Bulgaria", "🇧🇬", "Europe/Sofia", "Europe"),
    "GR": ("اليونان", "Greece", "🇬🇷", "Europe/Athens", "Europe"),
    "HR": ("كرواتيا", "Croatia", "🇭🇷", "Europe/Zagreb", "Europe"),
    "RS": ("صربيا", "Serbia", "🇷🇸", "Europe/Belgrade", "Europe"),
    "BA": ("البوسنة والهرسك", "Bosnia and Herzegovina", "🇧🇦", "Europe/Sarajevo", "Europe"),
    "SI": ("سلوفينيا", "Slovenia", "🇸🇮", "Europe/Ljubljana", "Europe"),
    "MK": ("مقدونيا الشمالية", "North Macedonia", "🇲🇰", "Europe/Skopje", "Europe"),
    "AL": ("ألبانيا", "Albania", "🇦🇱", "Europe/Tirane", "Europe"),
    "ME": ("الجبل الأسود", "Montenegro", "🇲🇪", "Europe/Podgorica", "Europe"),
    "XK": ("كوسوفو", "Kosovo", "🇽🇰", "Europe/Belgrade", "Europe"),
    "MD": ("مولدوفا", "Moldova", "🇲🇩", "Europe/Chisinau", "Europe"),
    "UA": ("أوكرانيا", "Ukraine", "🇺🇦", "Europe/Kyiv", "Europe"),
    "BY": ("بيلاروسيا", "Belarus", "🇧🇾", "Europe/Minsk", "Europe"),
    "LT": ("ليتوانيا", "Lithuania", "🇱🇹", "Europe/Vilnius", "Europe"),
    "LV": ("لاتفيا", "Latvia", "🇱🇻", "Europe/Riga", "Europe"),
    "EE": ("إستونيا", "Estonia", "🇪🇪", "Europe/Tallinn", "Europe"),
    "RU": ("روسيا", "Russia", "🇷🇺", "Europe/Moscow", "Europe"),
    "TR": ("تركيا", "Turkey", "🇹🇷", "Europe/Istanbul", "Europe"),
    "CY": ("قبرص", "Cyprus", "🇨🇾", "Asia/Nicosia", "Europe"),
    "MT": ("مالطا", "Malta", "🇲🇹", "Europe/Malta", "Europe"),
    "LU": ("لوكسمبورغ", "Luxembourg", "🇱🇺", "Europe/Luxembourg", "Europe"),
    "LI": ("ليختنشتاين", "Liechtenstein", "🇱🇮", "Europe/Vaduz", "Europe"),
    "MC": ("موناكو", "Monaco", "🇲🇨", "Europe/Monaco", "Europe"),
    "SM": ("سان مارينو", "San Marino", "🇸🇲", "Europe/San_Marino", "Europe"),
    "VA": ("الفاتيكان", "Vatican City", "🇻🇦", "Europe/Vatican", "Europe"),
    "AD": ("أندورا", "Andorra", "🇦🇩", "Europe/Andorra", "Europe"),
    "GI": ("جبل طارق", "Gibraltar", "🇬🇮", "Europe/Gibraltar", "Europe"),
    "FO": ("جزر فارو", "Faroe Islands", "🇫🇴", "Atlantic/Faroe", "Europe"),
    "GG": ("غيرنزي", "Guernsey", "🇬🇬", "Europe/Guernsey", "Europe"),
    "JE": ("جيرزي", "Jersey", "🇯🇪", "Europe/Jersey", "Europe"),
    "IM": ("جزيرة مان", "Isle of Man", "🇮🇲", "Europe/Isle_of_Man", "Europe"),
    "AX": ("جزر أولاند", "Aland Islands", "🇦🇽", "Europe/Mariehamn", "Europe"),
    "SJ": ("سفالبارد وجان ماين", "Svalbard and Jan Mayen", "🇸🇯", "Arctic/Longyearbyen", "Europe"),

    # ═══════════ 🌏 آسيا (50 - بعد استبعاد العرب) ═══════════
    "CN": ("الصين", "China", "🇨🇳", "Asia/Shanghai", "Asia"),
    "JP": ("اليابان", "Japan", "🇯🇵", "Asia/Tokyo", "Asia"),
    "KR": ("كوريا الجنوبية", "South Korea", "🇰🇷", "Asia/Seoul", "Asia"),
    "KP": ("كوريا الشمالية", "North Korea", "🇰🇵", "Asia/Pyongyang", "Asia"),
    "IN": ("الهند", "India", "🇮🇳", "Asia/Kolkata", "Asia"),
    "PK": ("باكستان", "Pakistan", "🇵🇰", "Asia/Karachi", "Asia"),
    "BD": ("بنغلاديش", "Bangladesh", "🇧🇩", "Asia/Dhaka", "Asia"),
    "LK": ("سريلانكا", "Sri Lanka", "🇱🇰", "Asia/Colombo", "Asia"),
    "NP": ("نيبال", "Nepal", "🇳🇵", "Asia/Kathmandu", "Asia"),
    "BT": ("بوتان", "Bhutan", "🇧🇹", "Asia/Thimphu", "Asia"),
    "MV": ("جزر المالديف", "Maldives", "🇲🇻", "Indian/Maldives", "Asia"),
    "AF": ("أفغانستان", "Afghanistan", "🇦🇫", "Asia/Kabul", "Asia"),
    "IR": ("إيران", "Iran", "🇮🇷", "Asia/Tehran", "Asia"),
    "IL": ("إسرائيل", "Israel", "🇮🇱", "Asia/Jerusalem", "Asia"),
    "TH": ("تايلاند", "Thailand", "🇹🇭", "Asia/Bangkok", "Asia"),
    "VN": ("فيتنام", "Vietnam", "🇻🇳", "Asia/Ho_Chi_Minh", "Asia"),
    "MY": ("ماليزيا", "Malaysia", "🇲🇾", "Asia/Kuala_Lumpur", "Asia"),
    "SG": ("سنغافورة", "Singapore", "🇸🇬", "Asia/Singapore", "Asia"),
    "ID": ("إندونيسيا", "Indonesia", "🇮🇩", "Asia/Jakarta", "Asia"),
    "PH": ("الفلبين", "Philippines", "🇵🇭", "Asia/Manila", "Asia"),
    "MM": ("ميانمار", "Myanmar", "🇲🇲", "Asia/Yangon", "Asia"),
    "KH": ("كمبوديا", "Cambodia", "🇰🇭", "Asia/Phnom_Penh", "Asia"),
    "LA": ("لاوس", "Laos", "🇱🇦", "Asia/Vientiane", "Asia"),
    "BN": ("بروناي", "Brunei", "🇧🇳", "Asia/Brunei", "Asia"),
    "TL": ("تيمور الشرقية", "East Timor", "🇹🇱", "Asia/Dili", "Asia"),
    "MN": ("منغوليا", "Mongolia", "🇲🇳", "Asia/Ulaanbaatar", "Asia"),
    "KZ": ("كازاخستان", "Kazakhstan", "🇰🇿", "Asia/Almaty", "Asia"),
    "UZ": ("أوزبكستان", "Uzbekistan", "🇺🇿", "Asia/Tashkent", "Asia"),
    "TM": ("تركمانستان", "Turkmenistan", "🇹🇲", "Asia/Ashgabat", "Asia"),
    "KG": ("قيرغيزستان", "Kyrgyzstan", "🇰🇬", "Asia/Bishkek", "Asia"),
    "TJ": ("طاجيكستان", "Tajikistan", "🇹🇯", "Asia/Dushanbe", "Asia"),
    "AZ": ("أذربيجان", "Azerbaijan", "🇦🇿", "Asia/Baku", "Asia"),
    "AM": ("أرمينيا", "Armenia", "🇦🇲", "Asia/Yerevan", "Asia"),
    "GE": ("جورجيا", "Georgia", "🇬🇪", "Asia/Tbilisi", "Asia"),
    "TW": ("تايوان", "Taiwan", "🇹🇼", "Asia/Taipei", "Asia"),
    "HK": ("هونغ كونغ", "Hong Kong", "🇭🇰", "Asia/Hong_Kong", "Asia"),
    "MO": ("ماكاو", "Macau", "🇲🇴", "Asia/Macau", "Asia"),

    # ═══════════ 🌎 الأمريكتان (56) ═══════════
    "US": ("الولايات المتحدة الأمريكية", "United States", "🇺🇸", "America/New_York", "Americas"),
    "CA": ("كندا", "Canada", "🇨🇦", "America/Toronto", "Americas"),
    "MX": ("المكسيك", "Mexico", "🇲🇽", "America/Mexico_City", "Americas"),
    "BR": ("البرازيل", "Brazil", "🇧🇷", "America/Sao_Paulo", "Americas"),
    "AR": ("الأرجنتين", "Argentina", "🇦🇷", "America/Argentina/Buenos_Aires", "Americas"),
    "CL": ("تشيلي", "Chile", "🇨🇱", "America/Santiago", "Americas"),
    "CO": ("كولومبيا", "Colombia", "🇨🇴", "America/Bogota", "Americas"),
    "PE": ("بيرو", "Peru", "🇵🇪", "America/Lima", "Americas"),
    "VE": ("فنزويلا", "Venezuela", "🇻🇪", "America/Caracas", "Americas"),
    "EC": ("الإكوادور", "Ecuador", "🇪🇨", "America/Guayaquil", "Americas"),
    "BO": ("بوليفيا", "Bolivia", "🇧🇴", "America/La_Paz", "Americas"),
    "PY": ("باراغواي", "Paraguay", "🇵🇾", "America/Asuncion", "Americas"),
    "UY": ("الأوروغواي", "Uruguay", "🇺🇾", "America/Montevideo", "Americas"),
    "GY": ("غيانا", "Guyana", "🇬🇾", "America/Guyana", "Americas"),
    "SR": ("سورينام", "Suriname", "🇸🇷", "America/Paramaribo", "Americas"),
    "GF": ("غويانا الفرنسية", "French Guiana", "🇬🇫", "America/Cayenne", "Americas"),
    "PA": ("بنما", "Panama", "🇵🇦", "America/Panama", "Americas"),
    "CR": ("كوستاريكا", "Costa Rica", "🇨🇷", "America/Costa_Rica", "Americas"),
    "NI": ("نيكاراغوا", "Nicaragua", "🇳🇮", "America/Managua", "Americas"),
    "HN": ("هندوراس", "Honduras", "🇭🇳", "America/Tegucigalpa", "Americas"),
    "SV": ("السلفادور", "El Salvador", "🇸🇻", "America/El_Salvador", "Americas"),
    "GT": ("غواتيمالا", "Guatemala", "🇬🇹", "America/Guatemala", "Americas"),
    "BZ": ("بليز", "Belize", "🇧🇿", "America/Belize", "Americas"),
    "CU": ("كوبا", "Cuba", "🇨🇺", "America/Havana", "Americas"),
    "DO": ("جمهورية الدومينيكان", "Dominican Republic", "🇩🇴", "America/Santo_Domingo", "Americas"),
    "HT": ("هايتي", "Haiti", "🇭🇹", "America/Port-au-Prince", "Americas"),
    "JM": ("جامايكا", "Jamaica", "🇯🇲", "America/Jamaica", "Americas"),
    "PR": ("بورتوريكو", "Puerto Rico", "🇵🇷", "America/Puerto_Rico", "Americas"),
    "TT": ("ترينيداد وتوباغو", "Trinidad and Tobago", "🇹🇹", "America/Port_of_Spain", "Americas"),
    "BS": ("جزر البهاما", "Bahamas", "🇧🇸", "America/Nassau", "Americas"),
    "BB": ("بربادوس", "Barbados", "🇧🇧", "America/Barbados", "Americas"),
    "GD": ("غرينادا", "Grenada", "🇬🇩", "America/Grenada", "Americas"),
    "LC": ("سانت لوسيا", "Saint Lucia", "🇱🇨", "America/St_Lucia", "Americas"),
    "VC": ("سانت فنسنت والغرينادين", "Saint Vincent", "🇻🇨", "America/St_Vincent", "Americas"),
    "AG": ("أنتيغوا وباربودا", "Antigua and Barbuda", "🇦🇬", "America/Antigua", "Americas"),
    "DM": ("دومينيكا", "Dominica", "🇩🇲", "America/Dominica", "Americas"),
    "KN": ("سانت كيتس ونيفيس", "Saint Kitts and Nevis", "🇰🇳", "America/St_Kitts", "Americas"),
    "GL": ("غرينلاند", "Greenland", "🇬🇱", "America/Godthab", "Americas"),
    "BM": ("برمودا", "Bermuda", "🇧🇲", "Atlantic/Bermuda", "Americas"),
    "KY": ("جزر كايمان", "Cayman Islands", "🇰🇾", "America/Cayman", "Americas"),
    "VG": ("جزر العذراء البريطانية", "British Virgin Islands", "🇻🇬", "America/Tortola", "Americas"),
    "VI": ("جزر العذراء الأمريكية", "US Virgin Islands", "🇻🇮", "America/St_Thomas", "Americas"),
    "AI": ("أنغويلا", "Anguilla", "🇦🇮", "America/Anguilla", "Americas"),
    "MS": ("مونتسيرات", "Montserrat", "🇲🇸", "America/Montserrat", "Americas"),
    "TC": ("جزر توركس وكايكوس", "Turks and Caicos", "🇹🇨", "America/Grand_Turk", "Americas"),
    "AW": ("أروبا", "Aruba", "🇦🇼", "America/Aruba", "Americas"),
    "CW": ("كوراساو", "Curacao", "🇨🇼", "America/Curacao", "Americas"),
    "SX": ("سينت مارتن", "Sint Maarten", "🇸🇽", "America/Lower_Princes", "Americas"),
    "BQ": ("بونير", "Bonaire", "🇧🇶", "America/Kralendijk", "Americas"),
    "MQ": ("مارتينيك", "Martinique", "🇲🇶", "America/Martinique", "Americas"),
    "GP": ("غوادلوب", "Guadeloupe", "🇬🇵", "America/Guadeloupe", "Americas"),
    "BL": ("سان بارتيلمي", "Saint Barthelemy", "🇧🇱", "America/St_Barthelemy", "Americas"),
    "MF": ("سان مارتن", "Saint Martin", "🇲🇫", "America/Marigot", "Americas"),
    "PM": ("سان بيير وميكلون", "Saint Pierre and Miquelon", "🇵🇲", "America/Miquelon", "Americas"),
    "FK": ("جزر فوكلاند", "Falkland Islands", "🇫🇰", "Atlantic/Stanley", "Americas"),
    "GS": ("جورجيا الجنوبية", "South Georgia", "🇬🇸", "Atlantic/South_Georgia", "Americas"),

    # ═══════════ 🏝️ أوقيانوسيا (29) ═══════════
    "AU": ("أستراليا", "Australia", "🇦🇺", "Australia/Sydney", "Oceania"),
    "NZ": ("نيوزيلندا", "New Zealand", "🇳🇿", "Pacific/Auckland", "Oceania"),
    "FJ": ("فيجي", "Fiji", "🇫🇯", "Pacific/Fiji", "Oceania"),
    "PG": ("بابوا غينيا الجديدة", "Papua New Guinea", "🇵🇬", "Pacific/Port_Moresby", "Oceania"),
    "SB": ("جزر سليمان", "Solomon Islands", "🇸🇧", "Pacific/Guadalcanal", "Oceania"),
    "VU": ("فانواتو", "Vanuatu", "🇻🇺", "Pacific/Efate", "Oceania"),
    "NC": ("كاليدونيا الجديدة", "New Caledonia", "🇳🇨", "Pacific/Noumea", "Oceania"),
    "PF": ("بولينيزيا الفرنسية", "French Polynesia", "🇵🇫", "Pacific/Tahiti", "Oceania"),
    "WS": ("ساموا", "Samoa", "🇼🇸", "Pacific/Apia", "Oceania"),
    "TO": ("تونغا", "Tonga", "🇹🇴", "Pacific/Tongatapu", "Oceania"),
    "KI": ("كيريباتي", "Kiribati", "🇰🇮", "Pacific/Tarawa", "Oceania"),
    "FM": ("ولايات ميكرونيزيا", "Micronesia", "🇫🇲", "Pacific/Pohnpei", "Oceania"),
    "MH": ("جزر مارشال", "Marshall Islands", "🇲🇭", "Pacific/Majuro", "Oceania"),
    "PW": ("بالاو", "Palau", "🇵🇼", "Pacific/Palau", "Oceania"),
    "TV": ("توفالو", "Tuvalu", "🇹🇻", "Pacific/Funafuti", "Oceania"),
    "NR": ("ناورو", "Nauru", "🇳🇷", "Pacific/Nauru", "Oceania"),
    "CK": ("جزر كوك", "Cook Islands", "🇨🇰", "Pacific/Rarotonga", "Oceania"),
    "NU": ("نييوي", "Niue", "🇳🇺", "Pacific/Niue", "Oceania"),
    "GU": ("غوام", "Guam", "🇬🇺", "Pacific/Guam", "Oceania"),
    "AS": ("ساموا الأمريكية", "American Samoa", "🇦🇸", "Pacific/Pago_Pago", "Oceania"),
    "MP": ("جزر ماريانا الشمالية", "Northern Mariana Islands", "🇲🇵", "Pacific/Saipan", "Oceania"),
    "WF": ("واليس وفوتونا", "Wallis and Futuna", "🇼🇫", "Pacific/Wallis", "Oceania"),
    "TK": ("توكيلاو", "Tokelau", "🇹🇰", "Pacific/Fakaofo", "Oceania"),
    "PN": ("جزر بيتكيرن", "Pitcairn Islands", "🇵🇳", "Pacific/Pitcairn", "Oceania"),
    "NF": ("جزيرة نورفولك", "Norfolk Island", "🇳🇫", "Pacific/Norfolk", "Oceania"),
    "CX": ("جزيرة كريسماس", "Christmas Island", "🇨🇽", "Indian/Christmas", "Oceania"),
    "CC": ("جزر كوكوس", "Cocos Islands", "🇨🇨", "Indian/Cocos", "Oceania"),
    "HM": ("جزيرة هيرد وماكدونالد", "Heard Island", "🇭🇲", "Indian/Kerguelen", "Oceania"),
    "UM": ("جزر الولايات المتحدة النائية", "US Minor Outlying Islands", "🇺🇲", "Pacific/Midway", "Oceania"),

    # ═══════════ ❄️ أنتاركتيكا ═══════════
    "AQ": ("أنتاركتيكا", "Antarctica", "🇦🇶", "Antarctica/McMurdo", "Antarctica"),
}


# ============================================================
# 🗺️ خريطة IANA Timezones → ISO Country Code
# ============================================================
TIMEZONE_TO_COUNTRY: Dict[str, str] = {
    tz: iso for iso, (_, _, _, tz, _) in WORLD_COUNTRIES.items()
}

# ============================================================
# 🌐 المجموعات الجاهزة
# ============================================================
ARAB_COUNTRIES = ["SA", "AE", "KW", "QA", "BH", "OM", "YE", "IQ", "SY", "LB",
                  "JO", "PS", "EG", "SD", "LY", "TN", "DZ", "MA", "MR", "SO",
                  "DJ", "KM"]

GCC_COUNTRIES = ["SA", "AE", "KW", "QA", "BH", "OM"]

EU_COUNTRIES = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
                "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
                "PL", "PT", "RO", "SK", "SI", "ES", "SE"]


# ============================================================
# 🔧 الدوال المساعدة (Public API)
# ============================================================

def get_country_info(iso_code: str) -> Optional[Tuple[str, str, str, str, str]]:
    """
    استرجاع كافة بيانات دولة عبر الـ ISO code.

    Args:
        iso_code: كود ISO 3166-1 alpha-2 (مثال: 'SA', 'US')

    Returns:
        tuple: (arabic, english, flag, timezone, continent) أو None
    """
    if not iso_code:
        return None
    return WORLD_COUNTRIES.get(iso_code.upper())


def get_arabic_name(iso_code: str) -> str:
    """الاسم العربي أو 'غير محدد'."""
    info = get_country_info(iso_code)
    return info[0] if info else "غير محدد"


def get_english_name(iso_code: str) -> str:
    """الاسم الإنجليزي أو 'Unknown'."""
    info = get_country_info(iso_code)
    return info[1] if info else "Unknown"


def get_flag(iso_code: str) -> str:
    """علم Emoji أو 🏳️."""
    info = get_country_info(iso_code)
    return info[2] if info else "🏳️"


def get_timezone(iso_code: str) -> Optional[str]:
    """المنطقة الزمنية الأساسية IANA."""
    info = get_country_info(iso_code)
    return info[3] if info else None


def get_continent(iso_code: str) -> Optional[str]:
    """القارة."""
    info = get_country_info(iso_code)
    return info[4] if info else None


def get_country_by_timezone(timezone: str) -> Optional[str]:
    """
    استنتاج ISO code من timezone.

    Args:
        timezone: مثال 'Asia/Riyadh'

    Returns:
        ISO code مثل 'SA' أو None
    """
    return TIMEZONE_TO_COUNTRY.get(timezone)


def get_all_arab_countries() -> List[Dict]:
    """قائمة كاملة بالدول العربية."""
    return [
        {
            "iso": iso,
            "ar": WORLD_COUNTRIES[iso][0],
            "en": WORLD_COUNTRIES[iso][1],
            "flag": WORLD_COUNTRIES[iso][2],
            "timezone": WORLD_COUNTRIES[iso][3],
        }
        for iso in ARAB_COUNTRIES if iso in WORLD_COUNTRIES
    ]


def get_countries_by_continent(continent: str) -> List[str]:
    """
    قائمة بأكواد ISO لدول قارة معينة.

    Args:
        continent: 'Asia' | 'Africa' | 'Europe' | 'Americas' | 'Oceania' | 'Antarctica'
    """
    return [
        iso for iso, data in WORLD_COUNTRIES.items()
        if data[4] == continent
    ]


def format_country_display(iso_code: str, lang: str = "ar") -> str:
    """
    عرض منسّق للدولة: '🇸🇦 المملكة العربية السعودية'.

    Args:
        iso_code: ISO 3166-1 alpha-2
        lang: 'ar' | 'en'
    """
    info = get_country_info(iso_code)
    if not info:
        return "🏳️ غير محدد" if lang == "ar" else "🏳️ Unknown"
    ar, en, flag, _, _ = info
    name = ar if lang == "ar" else en
    return f"{flag} {name}"


def is_arab_country(iso_code: str) -> bool:
    """هل الدولة عربية؟"""
    return iso_code and iso_code.upper() in ARAB_COUNTRIES


def is_gcc_country(iso_code: str) -> bool:
    """هل الدولة من دول الخليج؟"""
    return iso_code and iso_code.upper() in GCC_COUNTRIES


# ============================================================
# 📊 إحصائيات وقت التحميل
# ============================================================
STATS = {
    "total_countries": len(WORLD_COUNTRIES),
    "arab_countries": len(ARAB_COUNTRIES),
    "gcc_countries": len(GCC_COUNTRIES),
    "eu_countries": len(EU_COUNTRIES),
    "continents": {},
    "version": "v2.2.1-WorldCompleteMap",
    "release_date": "2026-07-26",
    "committee_id": "BSR-V221-CTO-WORLD-MAP-COMPLETE-AHMAD-20260726",
}

for iso, data in WORLD_COUNTRIES.items():
    continent = data[4]
    STATS["continents"][continent] = STATS["continents"].get(continent, 0) + 1


# ============================================================
# 🧪 Self-test on import
# ============================================================
if __name__ == "__main__":
    import json
    print("=" * 60)
    print(f"  regions_database.py {STATS['version']}")
    print(f"  {STATS['committee_id']}")
    print("=" * 60)
    print(json.dumps(STATS, ensure_ascii=False, indent=2))
    print()
    print("Sample tests:")
    print(f"  get_arabic_name('SA') = {get_arabic_name('SA')}")
    print(f"  get_flag('US') = {get_flag('US')}")
    print(f"  get_country_by_timezone('Asia/Riyadh') = {get_country_by_timezone('Asia/Riyadh')}")
    print(f"  format_country_display('EG') = {format_country_display('EG')}")
    print(f"  is_arab_country('EG') = {is_arab_country('EG')}")
    print(f"  is_gcc_country('MA') = {is_gcc_country('MA')}")


# ══════════════════════════════════════════════════════════════════
# 🔄 BACKWARD COMPATIBILITY SHIM v2.4.3 (BSR-V243-CTO-COMPAT-SHIM)
# ══════════════════════════════════════════════════════════════════
# app.py v2.1.0 (Streamlit) expects legacy API:
#   - REGIONS_DATABASE (dict of countries)
#   - lookup_region(text) -> dict or None
#
# We provide these as thin wrappers over v2.2.1 API.
# ══════════════════════════════════════════════════════════════════

# Build REGIONS_DATABASE dict (legacy format expected by app.py v2.1.0)
REGIONS_DATABASE = {}
for _iso, _data in WORLD_COUNTRIES.items():
    _ar_name, _en_name, _flag, _tz, _continent = _data
    REGIONS_DATABASE[_iso] = {
        "iso": _iso,
        "code": _iso,
        "name_ar": _ar_name,
        "name_en": _en_name,
        "arabic_name": _ar_name,
        "english_name": _en_name,
        "flag": _flag,
        "timezone": _tz,
        "continent": _continent,
        "is_arab": _iso in ARAB_COUNTRIES,
        "is_gcc": _iso in GCC_COUNTRIES,
        "is_eu": _iso in EU_COUNTRIES,
        # Legacy fields expected by old app.py
        "country": _en_name,
        "region": _ar_name,
        "capital": _ar_name,
    }


def lookup_region(text: str) -> Optional[Dict]:
    """
    Legacy function for app.py v2.1.0 Streamlit compatibility.
    Searches for a country match by:
      - ISO code (SA, US, EG)
      - Arabic name (السعودية, مصر)
      - English name (Saudi Arabia, Egypt)
      - Timezone (Asia/Riyadh)
      - Flag emoji (🇸🇦)
    Returns the country dict or None.
    """
    if not text or not isinstance(text, str):
        return None

    text_lower = text.strip().lower()
    text_upper = text.strip().upper()

    # 1) Direct ISO code match
    if text_upper in REGIONS_DATABASE:
        return REGIONS_DATABASE[text_upper]

    # 2) Timezone match
    tz_match = get_country_by_timezone(text)
    if tz_match and tz_match in REGIONS_DATABASE:
        return REGIONS_DATABASE[tz_match]

    # 3) Name / Flag search
    for iso, data in REGIONS_DATABASE.items():
        # Flag match
        if data["flag"] and data["flag"] in text:
            return data
        # English name (partial, case-insensitive)
        if data["name_en"] and data["name_en"].lower() in text_lower:
            return data
        # Arabic name
        if data["name_ar"] and data["name_ar"] in text:
            return data

    return None


# Aliases for extra compatibility with any v2.1.x variants
COUNTRIES = REGIONS_DATABASE
CAPITALS_DATABASE = REGIONS_DATABASE  # legacy


def lookup_capital(text: str) -> Optional[Dict]:
    """Legacy alias — same behavior as lookup_region for app.py compatibility."""
    return lookup_region(text)


# Sanity log at import
try:
    import logging as _lg
    _lg.getLogger(__name__).info(
        f"[regions_database] v2.4.3 compat shim loaded — "
        f"{len(REGIONS_DATABASE)} countries, lookup_region ready"
    )
except Exception:
    pass
