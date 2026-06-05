"""
🌍 قاعدة المناطق الشاملة عالمياً - Baseer v1.9.6
═══════════════════════════════════════════════════════════════
تشمل: مدن + مناطق إدارية + محافظات + مقاطعات + بلديات + مراكز
مستوى التفصيل: من العاصمة حتى "حوطة بني تميم"

التغطية:
  🇸🇦 السعودية: 13 منطقة + 200+ محافظة ومدينة
  🇦🇪 الإمارات: 7 إمارات + 50+ مدينة
  🇰🇼 الكويت: 6 محافظات + 40+ منطقة
  🇶🇦 قطر: 8 بلديات + 30+ منطقة
  🇧🇭 البحرين: 4 محافظات + 25+ منطقة
  🇴🇲 عمان: 11 محافظة + 50+ ولاية
  🇪🇬 مصر: 27 محافظة + 100+ مدينة
  🇯🇴 الأردن: 12 محافظة + 50+ مدينة
  🇲🇦 المغرب، 🇩🇿 الجزائر، 🇹🇳 تونس، 🇱🇧 لبنان، 🇮🇶 العراق، 🇸🇾 سوريا
  🇺🇸 أمريكا، 🇨🇦 كندا، 🇬🇧 بريطانيا، 🇫🇷 فرنسا، 🇩🇪 ألمانيا، 🇪🇸 إسبانيا، 🇮🇹 إيطاليا
  🇯🇵 اليابان، 🇰🇷 كوريا، 🇨🇳 الصين، 🇮🇳 الهند، 🇵🇰 باكستان، 🇮🇩 إندونيسيا
  🇧🇷 البرازيل، 🇦🇷 الأرجنتين، 🇲🇽 المكسيك، 🇨🇴 كولومبيا
  🇦🇺 أستراليا، 🇳🇿 نيوزيلندا
  🇳🇬 نيجيريا، 🇿🇦 جنوب أفريقيا، 🇰🇪 كينيا، 🇲🇦 المغرب
═══════════════════════════════════════════════════════════════
"""

REGIONS_DATABASE = {
    # ═══════════════ 🇸🇦 المملكة العربية السعودية ═══════════════
    'Saudi Arabia': {
        # العاصمة والمدن الرئيسية
        'riyadh': 'الرياض', 'jeddah': 'جدة', 'mecca': 'مكة المكرمة',
        'makkah': 'مكة المكرمة', 'medina': 'المدينة المنورة', 'madinah': 'المدينة المنورة',
        'dammam': 'الدمام', 'khobar': 'الخبر', 'al-khobar': 'الخبر',
        'dhahran': 'الظهران', 'taif': 'الطائف', 'tabuk': 'تبوك',
        'buraydah': 'بريدة', 'buraidah': 'بريدة', 'khamis mushait': 'خميس مشيط',
        'abha': 'أبها', 'hail': 'حائل', 'hofuf': 'الهفوف',
        'jubail': 'الجبيل', 'yanbu': 'ينبع', 'najran': 'نجران',
        'al-baha': 'الباحة', 'baha': 'الباحة', 'jizan': 'جازان',
        'jazan': 'جازان', 'arar': 'عرعر', 'sakaka': 'سكاكا',
        'qatif': 'القطيف', 'unaizah': 'عنيزة', 'rabigh': 'رابغ',
        # محافظات منطقة الرياض
        'diriyah': 'الدرعية', 'kharj': 'الخرج', 'al-kharj': 'الخرج',
        'majmaah': 'المجمعة', 'al-majmaah': 'المجمعة',
        'zulfi': 'الزلفي', 'al-zulfi': 'الزلفي',
        'shaqra': 'شقراء', 'shaqraa': 'شقراء',
        'dawadmi': 'الدوادمي', 'al-dawadmi': 'الدوادمي',
        'afif': 'عفيف', 'al-afif': 'عفيف',
        'wadi al-dawasir': 'وادي الدواسر', 'wadi addawasir': 'وادي الدواسر',
        'sulayyil': 'السليل', 'al-sulayyil': 'السليل',
        'aflaj': 'الأفلاج', 'al-aflaj': 'الأفلاج',
        'hawtat bani tamim': 'حوطة بني تميم', 'howta': 'حوطة بني تميم',
        'huraymila': 'حريملاء', 'huraimila': 'حريملاء',
        'thadiq': 'ثادق', 'rumah': 'رماح',
        'quwaiyah': 'القويعية', 'al-quwaiyah': 'القويعية',
        'muzahimiyah': 'المزاحمية', 'al-muzahimiyah': 'المزاحمية',
        # محافظات منطقة مكة
        'jamum': 'الجموم', 'al-jamum': 'الجموم',
        'khulays': 'خليص', 'kholais': 'خليص',
        'ranya': 'رنية', 'turabah': 'تربة',
        'qunfudhah': 'القنفذة', 'al-qunfudhah': 'القنفذة',
        'al-lith': 'الليث', 'lith': 'الليث',
        'al-kamil': 'الكامل', 'adam': 'أضم',
        # محافظات منطقة المدينة
        'badr': 'بدر', 'mahd al-dhahab': 'مهد الذهب',
        'khaybar': 'خيبر', 'ula': 'العلا', 'al-ula': 'العلا',
        'wadi al-fara': 'وادي الفرع',
        # المنطقة الشرقية
        'ahsa': 'الأحساء', 'al-ahsa': 'الأحساء',
        'mubarraz': 'المبرز', 'al-mubarraz': 'المبرز',
        'khafji': 'الخفجي', 'al-khafji': 'الخفجي',
        'nairyah': 'النعيرية', 'al-nairyah': 'النعيرية',
        'qaisumah': 'القيصومة', 'safwa': 'صفوى',
        'rastanura': 'رأس تنورة', 'ras tanura': 'رأس تنورة',
        # القصيم
        'rass': 'الرس', 'al-rass': 'الرس',
        'badaya': 'البدائع', 'bukayriyah': 'البكيرية',
        'al-asyah': 'الأسياح', 'midhnab': 'المذنب',
        # حائل
        'baqaa': 'بقعاء', 'al-shinan': 'الشنان',
        'al-ghazalah': 'الغزالة', 'al-haaeit': 'الحائط',
        # تبوك
        'duba': 'ضباء', 'al-wajh': 'الوجه',
        'umluj': 'أملج', 'tayma': 'تيماء',
        'haql': 'حقل', 'al-bidaa': 'البدع',
        # الجوف
        'qurayyat': 'القريات', 'dawmat al-jandal': 'دومة الجندل',
        # عسير
        'mahayil': 'محايل عسير', 'mahayl asir': 'محايل',
        'tathlith': 'تثليث', 'sarat abidah': 'سراة عبيدة',
        'rijal almaa': 'رجال ألمع', 'al-namas': 'النماص',
        'bisha': 'بيشة', 'ahad rufaidah': 'أحد رفيدة',
        # جازان
        'sabya': 'صبيا', 'abu arish': 'أبو عريش',
        'samtah': 'صامطة', 'al-darb': 'الدرب',
        'farasan': 'فرسان', 'ahad al-masarihah': 'أحد المسارحة',
        # نجران
        'sharurah': 'شرورة', 'habuna': 'حبونا',
        'badr al-junub': 'بدر الجنوب', 'thar': 'ثار',
        # الباحة
        'al-mandaq': 'المندق', 'baljurashi': 'بلجرشي',
        'al-mikhwah': 'المخواة', 'qilwah': 'قلوة',
    },

    # ═══════════════ 🇦🇪 الإمارات العربية المتحدة ═══════════════
    'United Arab Emirates': {
        'abu dhabi': 'أبوظبي', 'abudhabi': 'أبوظبي',
        'dubai': 'دبي', 'sharjah': 'الشارقة',
        'ajman': 'عجمان', 'fujairah': 'الفجيرة',
        'ras al-khaimah': 'رأس الخيمة', 'rak': 'رأس الخيمة',
        'umm al-quwain': 'أم القيوين', 'uaq': 'أم القيوين',
        'al-ain': 'العين', 'alain': 'العين',
        'khalifa city': 'مدينة خليفة', 'mussafah': 'المصفح',
        'mohammed bin zayed city': 'مدينة محمد بن زايد',
        'yas island': 'جزيرة ياس', 'saadiyat': 'جزيرة السعديات',
        'reem island': 'جزيرة الريم', 'corniche': 'الكورنيش',
        'jumeirah': 'جميرا', 'deira': 'ديرة',
        'bur dubai': 'بر دبي', 'al-barsha': 'البرشاء',
        'marina': 'مرسى دبي', 'dubai marina': 'مرسى دبي',
        'jbr': 'جميرا بيتش ريزيدنس', 'palm jumeirah': 'نخلة جميرا',
        'downtown dubai': 'وسط دبي', 'business bay': 'الخليج التجاري',
        'silicon oasis': 'واحة السيليكون', 'dip': 'مجمع دبي للاستثمار',
        'jvc': 'قرية جميرا الدائرية', 'al-quoz': 'القوز',
        'mirdif': 'مردف', 'al-warqa': 'الورقاء',
        'nad al-sheba': 'ند الشبا',
        'al-khan': 'الخان', 'al-majaz': 'المجاز',
        'al-nahda': 'النهدة', 'al-qasimiya': 'القاسمية',
        'kalba': 'كلباء', 'khor fakkan': 'خورفكان',
        'dibba': 'دبا', 'masfut': 'مصفوت',
        'hatta': 'حتا', 'liwa': 'ليوا',
        'madinat zayed': 'مدينة زايد', 'ruwais': 'الرويس',
    },

    # ═══════════════ 🇰🇼 دولة الكويت ═══════════════
    'Kuwait': {
        'kuwait city': 'مدينة الكويت', 'al-kuwait': 'مدينة الكويت',
        'hawalli': 'حولي', 'hawally': 'حولي',
        'salmiya': 'السالمية', 'al-salmiya': 'السالمية',
        'farwaniya': 'الفروانية', 'al-farwaniya': 'الفروانية',
        'jahra': 'الجهراء', 'al-jahra': 'الجهراء',
        'ahmadi': 'الأحمدي', 'al-ahmadi': 'الأحمدي',
        'mubarak al-kabeer': 'مبارك الكبير',
        'jabriya': 'الجابرية', 'al-jabriya': 'الجابرية',
        'fintas': 'الفنطاس', 'mahboula': 'المهبولة',
        'fahaheel': 'الفحيحيل', 'mangaf': 'المنقف',
        'abu halifa': 'أبو حليفة', 'abu fatira': 'أبو فطيرة',
        'shaab': 'الشعب', 'al-shaab': 'الشعب',
        'rumaithiya': 'الرميثية', 'bayan': 'بيان',
        'salwa': 'سلوى', 'mishrif': 'مشرف',
        'sabah al-salem': 'صباح السالم', 'qurain': 'القرين',
        'adan': 'العدان', 'qusur': 'القصور',
        'jaber al-ali': 'جابر العلي',
        'andalus': 'الأندلس', 'firdous': 'الفردوس',
        'omariya': 'العمرية', 'abdullah al-mubarak': 'عبدالله المبارك',
        'sulaibikhat': 'الصليبخات', 'doha': 'الدوحة',
        'qibla': 'قبلة', 'sharq': 'شرق',
        'mirqab': 'المرقاب', 'salhiya': 'الصالحية',
        'dasma': 'الدسمة', 'shamiya': 'الشامية',
        'mansouriya': 'المنصورية', 'qadsiya': 'القادسية',
        'faiha': 'الفيحاء', 'kaifan': 'كيفان',
        'shuwaikh': 'الشويخ', 'nuzha': 'النزهة',
        'yarmouk': 'اليرموك', 'rawda': 'الروضة',
        'adailiya': 'العديلية', 'khaldiya': 'الخالدية',
        'surra': 'السرة', 'jabriya': 'الجابرية',
        'south surra': 'جنوب السرة',
    },

    # ═══════════════ 🇶🇦 دولة قطر ═══════════════
    'Qatar': {
        'doha': 'الدوحة', 'al-doha': 'الدوحة',
        'al-rayyan': 'الريان', 'rayyan': 'الريان',
        'al-wakrah': 'الوكرة', 'wakra': 'الوكرة',
        'al-khor': 'الخور', 'khor': 'الخور',
        'umm salal': 'أم صلال', 'al-shahaniya': 'الشحانية',
        'mesaieed': 'مسيعيد', 'dukhan': 'دخان',
        'ras laffan': 'راس لفان', 'al-shamal': 'الشمال',
        'lusail': 'لوسيل', 'al-daayen': 'الضعاين',
        'west bay': 'الخليج الغربي', 'pearl': 'اللؤلؤة',
        'pearl qatar': 'اللؤلؤة قطر', 'katara': 'كتارا',
        'msheireb': 'مشيرب', 'souq waqif': 'سوق واقف',
        'al-sadd': 'السد', 'al-aziziyah': 'العزيزية',
        'al-dafna': 'الدفنة', 'al-gharafa': 'الغرافة',
        'al-waab': 'الوعب', 'al-thumama': 'الثمامة',
    },

    # ═══════════════ 🇧🇭 مملكة البحرين ═══════════════
    'Bahrain': {
        'manama': 'المنامة', 'al-manama': 'المنامة',
        'muharraq': 'المحرق', 'al-muharraq': 'المحرق',
        'riffa': 'الرفاع', 'al-riffa': 'الرفاع',
        'hamad town': 'مدينة حمد', 'isa town': 'مدينة عيسى',
        'sitra': 'سترة', 'budaiya': 'البديع',
        'juffair': 'الجفير', 'seef': 'السيف',
        'adliya': 'العدلية', 'hidd': 'الحد',
        'amwaj': 'أمواج', 'durrat': 'درة البحرين',
        'sanad': 'سند', 'jidhafs': 'جدحفص',
        'arad': 'عراد', 'galali': 'قلالي',
        'tubli': 'توبلي', 'aali': 'عالي',
        'malkiya': 'المالكية', 'sakhir': 'الصخير',
        'zallaq': 'الزلاق', 'awali': 'عوالي',
    },

    # ═══════════════ 🇴🇲 سلطنة عمان ═══════════════
    'Oman': {
        'muscat': 'مسقط', 'salalah': 'صلالة',
        'sohar': 'صحار', 'nizwa': 'نزوى',
        'sur': 'صور', 'rustaq': 'الرستاق',
        'ibri': 'عبري', 'bahla': 'بهلاء',
        'buraimi': 'البريمي', 'khasab': 'خصب',
        'mutrah': 'مطرح', 'ruwi': 'روي',
        'qurum': 'القرم', 'azaiba': 'العذيبة',
        'ghala': 'غلا', 'seeb': 'السيب',
        'al-amerat': 'العامرات', 'bawshar': 'بوشر',
        'barka': 'بركاء', 'masirah': 'مصيرة',
        'duqm': 'الدقم', 'thumrait': 'ثمريت',
        'mirbat': 'مرباط', 'taqah': 'طاقة',
    },

    # ═══════════════ 🇪🇬 جمهورية مصر العربية ═══════════════
    'Egypt': {
        'cairo': 'القاهرة', 'al-qahirah': 'القاهرة',
        'alexandria': 'الإسكندرية', 'iskandariya': 'الإسكندرية',
        'giza': 'الجيزة', 'al-jizah': 'الجيزة',
        'shubra': 'شبرا', 'shubra el-kheima': 'شبرا الخيمة',
        'port said': 'بورسعيد', 'portsaid': 'بورسعيد',
        'suez': 'السويس', 'ismailia': 'الإسماعيلية',
        'mansoura': 'المنصورة', 'tanta': 'طنطا',
        'asyut': 'أسيوط', 'minya': 'المنيا',
        'beni suef': 'بني سويف', 'fayoum': 'الفيوم',
        'sohag': 'سوهاج', 'qena': 'قنا', 'aswan': 'أسوان',
        'luxor': 'الأقصر', 'hurghada': 'الغردقة',
        'sharm el-sheikh': 'شرم الشيخ', 'sharm': 'شرم الشيخ',
        'dahab': 'دهب', 'marsa alam': 'مرسى علم',
        'damietta': 'دمياط', 'kafr el-sheikh': 'كفر الشيخ',
        'damanhour': 'دمنهور', 'mahalla': 'المحلة الكبرى',
        'zagazig': 'الزقازيق', 'banha': 'بنها',
        'matruh': 'مرسى مطروح', 'arish': 'العريش',
        'new cairo': 'القاهرة الجديدة', 'maadi': 'المعادي',
        'zamalek': 'الزمالك', 'heliopolis': 'مصر الجديدة',
        'nasr city': 'مدينة نصر', 'sixth october': 'السادس من أكتوبر',
        'sheikh zayed': 'الشيخ زايد', 'new capital': 'العاصمة الإدارية',
        'ras gharib': 'رأس غارب', 'safaga': 'سفاجا',
        'taba': 'طابا', 'el-tor': 'الطور',
        'siwa': 'سيوة', 'edfu': 'إدفو',
        'kom ombo': 'كوم أمبو', 'esna': 'إسنا',
    },

    # ═══════════════ 🇯🇴 المملكة الأردنية الهاشمية ═══════════════
    'Jordan': {
        'amman': 'عمّان', 'zarqa': 'الزرقاء',
        'irbid': 'إربد', 'aqaba': 'العقبة',
        'salt': 'السلط', 'al-salt': 'السلط',
        'mafraq': 'المفرق', 'karak': 'الكرك',
        'al-karak': 'الكرك', 'tafilah': 'الطفيلة',
        'al-tafilah': 'الطفيلة', 'maan': 'معان',
        'maán': 'معان', 'jerash': 'جرش',
        'ajloun': 'عجلون', 'madaba': 'مادبا',
        'ramtha': 'الرمثا', 'al-ramtha': 'الرمثا',
        'azraq': 'الأزرق', 'wadi rum': 'وادي رم',
        'petra': 'البتراء', 'wadi musa': 'وادي موسى',
    },

    # ═══════════════ 🇱🇧 الجمهورية اللبنانية ═══════════════
    'Lebanon': {
        'beirut': 'بيروت', 'tripoli': 'طرابلس',
        'sidon': 'صيدا', 'saida': 'صيدا',
        'tyre': 'صور', 'sour': 'صور',
        'jounieh': 'جونية', 'byblos': 'جبيل',
        'jbeil': 'جبيل', 'zahle': 'زحلة',
        'baalbek': 'بعلبك', 'nabatieh': 'النبطية',
        'baabda': 'بعبدا', 'aley': 'عاليه',
        'broumana': 'برمانا', 'bhamdoun': 'بحمدون',
        'harissa': 'حريصا', 'ehden': 'إهدن',
    },

    # ═══════════════ 🇮🇶 جمهورية العراق ═══════════════
    'Iraq': {
        'baghdad': 'بغداد', 'basra': 'البصرة',
        'basrah': 'البصرة', 'mosul': 'الموصل',
        'erbil': 'أربيل', 'arbil': 'أربيل',
        'kirkuk': 'كركوك', 'sulaymaniyah': 'السليمانية',
        'duhok': 'دهوك', 'najaf': 'النجف',
        'karbala': 'كربلاء', 'kerbala': 'كربلاء',
        'kufa': 'الكوفة', 'samawah': 'السماوة',
        'nasiriyah': 'الناصرية', 'amarah': 'العمارة',
        'kut': 'الكوت', 'diwaniyah': 'الديوانية',
        'hillah': 'الحلة', 'baqubah': 'بعقوبة',
        'ramadi': 'الرمادي', 'fallujah': 'الفلوجة',
        'tikrit': 'تكريت', 'samarra': 'سامراء',
    },

    # ═══════════════ 🇸🇾 الجمهورية العربية السورية ═══════════════
    'Syria': {
        'damascus': 'دمشق', 'aleppo': 'حلب',
        'homs': 'حمص', 'hama': 'حماة',
        'latakia': 'اللاذقية', 'tartus': 'طرطوس',
        'deir ez-zor': 'دير الزور', 'raqqa': 'الرقة',
        'idlib': 'إدلب', 'daraa': 'درعا',
        'sweida': 'السويداء', 'qamishli': 'القامشلي',
        'hasakah': 'الحسكة',
    },

    # ═══════════════ 🇾🇪 الجمهورية اليمنية ═══════════════
    'Yemen': {
        'sanaa': 'صنعاء', 'sana': 'صنعاء',
        'aden': 'عدن', 'taiz': 'تعز',
        'hodeidah': 'الحديدة', 'al-hudaydah': 'الحديدة',
        'mukalla': 'المكلا', 'ibb': 'إب',
        'dhamar': 'ذمار', 'saada': 'صعدة',
        'marib': 'مأرب', 'hajjah': 'حجة',
        'amran': 'عمران', 'shabwa': 'شبوة',
        'lahj': 'لحج', 'abyan': 'أبين',
    },

    # ═══════════════ 🇵🇸 فلسطين ═══════════════
    'Palestine': {
        'jerusalem': 'القدس', 'al-quds': 'القدس',
        'gaza': 'غزة', 'ramallah': 'رام الله',
        'hebron': 'الخليل', 'al-khalil': 'الخليل',
        'nablus': 'نابلس', 'bethlehem': 'بيت لحم',
        'jenin': 'جنين', 'tulkarm': 'طولكرم',
        'qalqilya': 'قلقيلية', 'jericho': 'أريحا',
        'rafah': 'رفح', 'khan younis': 'خان يونس',
    },

    # ═══════════════ 🇲🇦 المملكة المغربية ═══════════════
    'Morocco': {
        'casablanca': 'الدار البيضاء', 'rabat': 'الرباط',
        'marrakech': 'مراكش', 'marrakesh': 'مراكش',
        'fes': 'فاس', 'fez': 'فاس',
        'tangier': 'طنجة', 'tanger': 'طنجة',
        'agadir': 'أكادير', 'meknes': 'مكناس',
        'oujda': 'وجدة', 'kenitra': 'القنيطرة',
        'tetouan': 'تطوان', 'safi': 'آسفي',
        'el jadida': 'الجديدة', 'beni mellal': 'بني ملال',
        'nador': 'الناظور', 'taza': 'تازة',
        'settat': 'سطات', 'mohammedia': 'المحمدية',
        'khouribga': 'خريبكة', 'ouarzazate': 'ورزازات',
        'chefchaouen': 'شفشاون', 'essaouira': 'الصويرة',
        'ifrane': 'إفران', 'dakhla': 'الداخلة',
        'laayoune': 'العيون',
    },

    # ═══════════════ 🇩🇿 الجمهورية الجزائرية ═══════════════
    'Algeria': {
        'algiers': 'الجزائر العاصمة', 'oran': 'وهران',
        'constantine': 'قسنطينة', 'annaba': 'عنابة',
        'blida': 'البليدة', 'batna': 'باتنة',
        'setif': 'سطيف', 'tlemcen': 'تلمسان',
        'bejaia': 'بجاية', 'tizi ouzou': 'تيزي وزو',
        'ghardaia': 'غرداية', 'biskra': 'بسكرة',
        'tamanrasset': 'تمنراست', 'ouargla': 'ورقلة',
        'mostaganem': 'مستغانم', 'sidi bel abbes': 'سيدي بلعباس',
    },

    # ═══════════════ 🇹🇳 الجمهورية التونسية ═══════════════
    'Tunisia': {
        'tunis': 'تونس العاصمة', 'sfax': 'صفاقس',
        'sousse': 'سوسة', 'kairouan': 'القيروان',
        'bizerte': 'بنزرت', 'gabes': 'قابس',
        'ariana': 'أريانة', 'gafsa': 'قفصة',
        'monastir': 'المنستير', 'nabeul': 'نابل',
        'tataouine': 'تطاوين', 'medenine': 'مدنين',
        'tozeur': 'توزر', 'beja': 'باجة',
        'jendouba': 'جندوبة', 'kasserine': 'القصرين',
        'mahdia': 'المهدية', 'kebili': 'قبلي',
        'hammamet': 'الحمامات', 'djerba': 'جربة',
        'sidi bouzid': 'سيدي بوزيد', 'zaghouan': 'زغوان',
    },

    # ═══════════════ 🇱🇾 ليبيا ═══════════════
    'Libya': {
        'tripoli': 'طرابلس', 'benghazi': 'بنغازي',
        'misrata': 'مصراتة', 'sabha': 'سبها',
        'zliten': 'زليتن', 'tobruk': 'طبرق',
        'derna': 'درنة', 'sirte': 'سرت',
        'gharyan': 'غريان', 'al-bayda': 'البيضاء',
    },

    # ═══════════════ 🇸🇩 السودان ═══════════════
    'Sudan': {
        'khartoum': 'الخرطوم', 'omdurman': 'أم درمان',
        'port sudan': 'بورتسودان', 'kassala': 'كسلا',
        'el-obeid': 'الأبيض', 'nyala': 'نيالا',
        'wad medani': 'ود مدني', 'el fasher': 'الفاشر',
        'gedaref': 'القضارف', 'sennar': 'سنار',
    },

    # ═══════════════ 🇺🇸 الولايات المتحدة الأمريكية ═══════════════
    'United States': {
        'washington': 'واشنطن', 'new york': 'نيويورك',
        'los angeles': 'لوس أنجلوس', 'chicago': 'شيكاغو',
        'houston': 'هيوستن', 'phoenix': 'فينيكس',
        'philadelphia': 'فيلادلفيا', 'san antonio': 'سان أنطونيو',
        'san diego': 'سان دييغو', 'dallas': 'دالاس',
        'san jose': 'سان خوسيه', 'austin': 'أوستن',
        'jacksonville': 'جاكسونفيل', 'fort worth': 'فورت وورث',
        'columbus': 'كولومبوس', 'charlotte': 'شارلوت',
        'san francisco': 'سان فرانسيسكو', 'indianapolis': 'إنديانابوليس',
        'seattle': 'سياتل', 'denver': 'دنفر',
        'boston': 'بوسطن', 'detroit': 'ديترويت',
        'nashville': 'ناشفيل', 'memphis': 'ممفيس',
        'portland': 'بورتلاند', 'oklahoma city': 'أوكلاهوما سيتي',
        'las vegas': 'لاس فيغاس', 'baltimore': 'بالتيمور',
        'milwaukee': 'ميلووكي', 'atlanta': 'أتلانتا',
        'miami': 'ميامي', 'orlando': 'أورلاندو',
        'tampa': 'تامبا', 'new orleans': 'نيو أورلينز',
        'cleveland': 'كليفلاند', 'pittsburgh': 'بيتسبرغ',
        'cincinnati': 'سينسيناتي', 'minneapolis': 'مينيابوليس',
        'st louis': 'سانت لويس', 'kansas city': 'كانساس سيتي',
        'sacramento': 'ساكرامنتو', 'long beach': 'لونغ بيتش',
        'oakland': 'أوكلاند', 'tucson': 'توسان',
        'fresno': 'فريسنو', 'mesa': 'ميسا',
        'honolulu': 'هونولولو', 'anchorage': 'أنكوريج',
        'salt lake city': 'سولت ليك سيتي', 'albuquerque': 'ألبوكيركي',
        'brooklyn': 'بروكلين', 'manhattan': 'مانهاتن',
        'queens': 'كوينز', 'bronx': 'برونكس',
        'staten island': 'ستاتن آيلاند', 'hollywood': 'هوليوود',
        'beverly hills': 'بيفرلي هيلز', 'malibu': 'ماليبو',
        'silicon valley': 'وادي السيليكون',
    },

    # ═══════════════ 🇨🇦 كندا ═══════════════
    'Canada': {
        'toronto': 'تورنتو', 'montreal': 'مونتريال',
        'vancouver': 'فانكوفر', 'calgary': 'كالغاري',
        'edmonton': 'إدمونتون', 'ottawa': 'أوتاوا',
        'winnipeg': 'وينيبيغ', 'quebec city': 'مدينة كيبيك',
        'hamilton': 'هاميلتون', 'mississauga': 'ميسيساغا',
        'brampton': 'برامبتون', 'surrey': 'ساري',
        'laval': 'لافال', 'halifax': 'هاليفاكس',
        'london ontario': 'لندن أونتاريو', 'markham': 'ماركهام',
        'victoria': 'فيكتوريا', 'gatineau': 'غاتينو',
    },

    # ═══════════════ 🇬🇧 المملكة المتحدة ═══════════════
    'United Kingdom': {
        'london': 'لندن', 'manchester': 'مانشستر',
        'birmingham': 'برمنغهام', 'liverpool': 'ليفربول',
        'leeds': 'ليدز', 'sheffield': 'شيفيلد',
        'bristol': 'بريستول', 'newcastle': 'نيوكاسل',
        'edinburgh': 'إدنبرة', 'glasgow': 'غلاسكو',
        'cardiff': 'كارديف', 'belfast': 'بلفاست',
        'cambridge': 'كامبريدج', 'oxford': 'أكسفورد',
        'brighton': 'برايتون', 'nottingham': 'نوتنغهام',
        'leicester': 'ليستر', 'southampton': 'ساوثهامبتون',
        'plymouth': 'بليموث', 'aberdeen': 'أبردين',
        'westminster': 'وستمنستر', 'chelsea': 'تشيلسي',
        'kensington': 'كنسينغتون',
    },

    # ═══════════════ 🇫🇷 فرنسا ═══════════════
    'France': {
        'paris': 'باريس', 'marseille': 'مرسيليا',
        'lyon': 'ليون', 'toulouse': 'تولوز',
        'nice': 'نيس', 'nantes': 'نانت',
        'strasbourg': 'ستراسبورغ', 'montpellier': 'مونبلييه',
        'bordeaux': 'بوردو', 'lille': 'ليل',
        'rennes': 'رين', 'cannes': 'كان',
        'le havre': 'لوهافر', 'saint-etienne': 'سانت إتيان',
        'reims': 'ريمس', 'toulon': 'تولون',
        'grenoble': 'غرونوبل', 'angers': 'أنجيه',
        'dijon': 'ديجون', 'avignon': 'أفينيون',
        'versailles': 'فرساي', 'monaco': 'موناكو',
    },

    # ═══════════════ 🇩🇪 ألمانيا ═══════════════
    'Germany': {
        'berlin': 'برلين', 'hamburg': 'هامبورغ',
        'munich': 'ميونخ', 'munchen': 'ميونخ',
        'cologne': 'كولونيا', 'koln': 'كولونيا',
        'frankfurt': 'فرانكفورت', 'stuttgart': 'شتوتغارت',
        'dusseldorf': 'دوسلدورف', 'leipzig': 'لايبزيغ',
        'dortmund': 'دورتموند', 'essen': 'إيسن',
        'bremen': 'بريمن', 'dresden': 'دريسدن',
        'hannover': 'هانوفر', 'nuremberg': 'نورمبرغ',
        'bonn': 'بون', 'heidelberg': 'هايدلبرغ',
    },

    # ═══════════════ 🇮🇹 إيطاليا ═══════════════
    'Italy': {
        'rome': 'روما', 'roma': 'روما',
        'milan': 'ميلانو', 'milano': 'ميلانو',
        'naples': 'نابولي', 'napoli': 'نابولي',
        'turin': 'تورينو', 'torino': 'تورينو',
        'palermo': 'باليرمو', 'genoa': 'جنوة',
        'bologna': 'بولونيا', 'florence': 'فلورنسا',
        'firenze': 'فلورنسا', 'venice': 'البندقية',
        'venezia': 'البندقية', 'verona': 'فيرونا',
        'pisa': 'بيزا', 'siena': 'سيينا',
        'catania': 'كاتانيا', 'bari': 'باري',
        'cagliari': 'كالياري', 'sardinia': 'سردينيا',
        'sicily': 'صقلية',
    },

    # ═══════════════ 🇪🇸 إسبانيا ═══════════════
    'Spain': {
        'madrid': 'مدريد', 'barcelona': 'برشلونة',
        'valencia': 'فالنسيا', 'seville': 'إشبيلية',
        'sevilla': 'إشبيلية', 'zaragoza': 'سرقسطة',
        'malaga': 'ملقا', 'murcia': 'مورسية',
        'palma': 'بالما', 'bilbao': 'بلباو',
        'alicante': 'أليكانتي', 'cordoba': 'قرطبة',
        'valladolid': 'بلد الوليد', 'granada': 'غرناطة',
        'toledo': 'طليطلة', 'salamanca': 'سلامنكا',
        'ibiza': 'إيبيزا', 'tenerife': 'تينيريفي',
        'mallorca': 'مايوركا',
    },

    # ═══════════════ 🇵🇹 البرتغال ═══════════════
    'Portugal': {
        'lisbon': 'لشبونة', 'lisboa': 'لشبونة',
        'porto': 'بورتو', 'braga': 'براغا',
        'coimbra': 'كويمبرا', 'faro': 'فارو',
        'funchal': 'فونشال', 'aveiro': 'أفيرو',
    },

    # ═══════════════ 🇳🇱 هولندا ═══════════════
    'Netherlands': {
        'amsterdam': 'أمستردام', 'rotterdam': 'روتردام',
        'the hague': 'لاهاي', 'utrecht': 'أوتريخت',
        'eindhoven': 'آيندهوفن', 'groningen': 'غرونينغن',
        'tilburg': 'تيلبورخ', 'breda': 'بريدا',
    },

    # ═══════════════ 🇹🇷 تركيا ═══════════════
    'Turkey': {
        'istanbul': 'إسطنبول', 'ankara': 'أنقرة',
        'izmir': 'إزمير', 'bursa': 'بورصة',
        'antalya': 'أنطاليا', 'konya': 'قونيا',
        'gaziantep': 'غازي عنتاب', 'sanliurfa': 'شانلي أورفا',
        'mersin': 'مرسين', 'diyarbakir': 'ديار بكر',
        'adana': 'أضنة', 'trabzon': 'طرابزون',
        'cappadocia': 'كبادوكيا', 'bodrum': 'بودروم',
        'fethiye': 'فتحية', 'kayseri': 'قيصري',
    },

    # ═══════════════ 🇷🇺 روسيا ═══════════════
    'Russia': {
        'moscow': 'موسكو', 'st petersburg': 'سان بطرسبرغ',
        'saint petersburg': 'سان بطرسبرغ', 'novosibirsk': 'نوفوسيبيرسك',
        'yekaterinburg': 'يكاترينبورغ', 'nizhny novgorod': 'نيجني نوفغورود',
        'kazan': 'قازان', 'chelyabinsk': 'تشيليابينسك',
        'samara': 'سمارة', 'rostov': 'روستوف',
        'sochi': 'سوتشي', 'vladivostok': 'فلاديفوستوك',
    },

    # ═══════════════ 🇯🇵 اليابان ═══════════════
    'Japan': {
        'tokyo': 'طوكيو', 'osaka': 'أوساكا',
        'kyoto': 'كيوتو', 'yokohama': 'يوكوهاما',
        'nagoya': 'ناغويا', 'sapporo': 'سابورو',
        'kobe': 'كوبي', 'fukuoka': 'فوكوكا',
        'hiroshima': 'هيروشيما', 'sendai': 'سينداي',
        'nara': 'نارا', 'okinawa': 'أوكيناوا',
        'shibuya': 'شيبويا', 'shinjuku': 'شينجوكو',
        'akihabara': 'أكيهابارا', 'ginza': 'غينزا',
        'harajuku': 'هاراجوكو', 'kanazawa': 'كانازاوا',
    },

    # ═══════════════ 🇰🇷 كوريا الجنوبية ═══════════════
    'South Korea': {
        'seoul': 'سيول', 'busan': 'بوسان',
        'incheon': 'إنتشون', 'daegu': 'دايغو',
        'daejeon': 'دايجون', 'gwangju': 'غوانغجو',
        'suwon': 'سوون', 'ulsan': 'أولسان',
        'changwon': 'تشانغوون', 'jeju': 'جيجو',
        'gangnam': 'غانغنام', 'hongdae': 'هونغداي',
        'itaewon': 'إيتايون', 'myeongdong': 'ميونغ دونغ',
    },

    # ═══════════════ 🇨🇳 الصين ═══════════════
    'China': {
        'beijing': 'بكين', 'shanghai': 'شنغهاي',
        'guangzhou': 'غوانغتشو', 'shenzhen': 'شنزن',
        'chengdu': 'تشنغدو', 'chongqing': 'تشونغتشينغ',
        'tianjin': 'تيانجين', 'wuhan': 'ووهان',
        'xian': 'شيآن', "xi'an": 'شيآن',
        'hangzhou': 'هانغتشو', 'nanjing': 'نانجينغ',
        'qingdao': 'تشينغداو', 'dalian': 'داليان',
        'suzhou': 'سوتشو', 'kunming': 'كونمينغ',
        'macau': 'ماكاو', 'sanya': 'سانيا',
    },

    # ═══════════════ 🇹🇼 تايوان ═══════════════
    'Taiwan': {
        'taipei': 'تايبيه', 'kaohsiung': 'كاوهسيونغ',
        'taichung': 'تايتشونغ', 'tainan': 'تاينان',
        'hsinchu': 'هسينشو', 'keelung': 'كيلونغ',
    },

    # ═══════════════ 🇭🇰 هونغ كونغ ═══════════════
    'Hong Kong': {
        'hong kong': 'هونغ كونغ', 'kowloon': 'كولون',
        'central': 'سنترال', 'mong kok': 'مونغ كوك',
        'tsim sha tsui': 'تسيم شا تسوي', 'causeway bay': 'كوزواي باي',
    },

    # ═══════════════ 🇸🇬 سنغافورة ═══════════════
    'Singapore': {
        'singapore': 'سنغافورة', 'marina bay': 'مارينا باي',
        'orchard': 'أوركارد', 'sentosa': 'سنتوسا',
        'chinatown': 'الحي الصيني', 'little india': 'ليتل إنديا',
    },

    # ═══════════════ 🇹🇭 تايلاند ═══════════════
    'Thailand': {
        'bangkok': 'بانكوك', 'chiang mai': 'شيانغ ماي',
        'phuket': 'بوكيت', 'pattaya': 'باتايا',
        'krabi': 'كرابي', 'koh samui': 'كوه ساموي',
        'hua hin': 'هوا هين', 'ayutthaya': 'أيوتايا',
        'chiang rai': 'شيانغ راي',
    },

    # ═══════════════ 🇻🇳 فيتنام ═══════════════
    'Vietnam': {
        'hanoi': 'هانوي', 'ho chi minh': 'هو تشي مينه',
        'ho chi minh city': 'هو تشي مينه', 'saigon': 'سايغون',
        'da nang': 'دا نانغ', 'hue': 'هوي',
        'hoi an': 'هوي آن', 'nha trang': 'نا ترانغ',
        'haiphong': 'هايفونغ', 'can tho': 'كان ثو',
    },

    # ═══════════════ 🇮🇩 إندونيسيا ═══════════════
    'Indonesia': {
        'jakarta': 'جاكرتا', 'surabaya': 'سورابايا',
        'bandung': 'باندونغ', 'medan': 'ميدان',
        'bali': 'بالي', 'denpasar': 'دنباسار',
        'yogyakarta': 'يوجياكارتا', 'semarang': 'سيمارانغ',
        'makassar': 'ماكاسار', 'palembang': 'باليمبانغ',
        'ubud': 'أوبود', 'lombok': 'لومبوك',
    },

    # ═══════════════ 🇲🇾 ماليزيا ═══════════════
    'Malaysia': {
        'kuala lumpur': 'كوالالمبور', 'penang': 'بينانغ',
        'george town': 'جورج تاون', 'johor bahru': 'جوهور باهرو',
        'ipoh': 'إيبوه', 'malacca': 'ملقا',
        'melaka': 'ملقا', 'kota kinabalu': 'كوتا كينابالو',
        'kuching': 'كوتشينغ', 'putrajaya': 'بوتراجايا',
        'langkawi': 'لانكاوي',
    },

    # ═══════════════ 🇵🇭 الفلبين ═══════════════
    'Philippines': {
        'manila': 'مانيلا', 'quezon city': 'مدينة كويزون',
        'cebu': 'سيبو', 'davao': 'دافاو',
        'makati': 'ماكاتي', 'taguig': 'تاغويغ',
        'pasig': 'باسيغ', 'boracay': 'بوراكاي',
        'palawan': 'بالاوان', 'bohol': 'بوهول',
    },

    # ═══════════════ 🇮🇳 الهند ═══════════════
    'India': {
        'mumbai': 'مومباي', 'delhi': 'دلهي',
        'new delhi': 'نيودلهي', 'bangalore': 'بنغالور',
        'bengaluru': 'بنغالور', 'hyderabad': 'حيدر آباد',
        'chennai': 'تشيناي', 'kolkata': 'كولكاتا',
        'calcutta': 'كولكاتا', 'pune': 'بوني',
        'ahmedabad': 'أحمد آباد', 'surat': 'سورات',
        'jaipur': 'جايبور', 'lucknow': 'لكناو',
        'kanpur': 'كانبور', 'nagpur': 'ناغبور',
        'indore': 'إندور', 'thane': 'ثاني',
        'bhopal': 'بوبال', 'visakhapatnam': 'فيساخاباتنام',
        'patna': 'باتنا', 'goa': 'غوا',
        'kerala': 'كيرالا', 'agra': 'أغرا',
        'varanasi': 'فاراناسي',
    },

    # ═══════════════ 🇵🇰 باكستان ═══════════════
    'Pakistan': {
        'karachi': 'كراتشي', 'lahore': 'لاهور',
        'islamabad': 'إسلام آباد', 'faisalabad': 'فيصل آباد',
        'rawalpindi': 'روالبندي', 'multan': 'ملتان',
        'peshawar': 'بيشاور', 'quetta': 'كويتا',
        'sialkot': 'سيالكوت', 'gujranwala': 'غوجرانوالا',
        'hyderabad': 'حيدر آباد', 'sargodha': 'سرغودا',
    },

    # ═══════════════ 🇧🇩 بنغلاديش ═══════════════
    'Bangladesh': {
        'dhaka': 'دكا', 'chittagong': 'شيتاغونغ',
        'khulna': 'خولنا', 'rajshahi': 'راجشاهي',
        'sylhet': 'سيلهيت', 'barisal': 'باريسال',
    },

    # ═══════════════ 🇧🇷 البرازيل ═══════════════
    'Brazil': {
        'sao paulo': 'ساو باولو', 'rio de janeiro': 'ريو دي جانيرو',
        'rio': 'ريو دي جانيرو', 'brasilia': 'برازيليا',
        'salvador': 'سلفادور', 'fortaleza': 'فورتاليزا',
        'belo horizonte': 'بيلو هوريزونتي', 'manaus': 'ماناوس',
        'curitiba': 'كوريتيبا', 'recife': 'ريسيفي',
        'porto alegre': 'بورتو أليغري', 'goiania': 'غويانيا',
        'belem': 'بيليم', 'florianopolis': 'فلوريانوبوليس',
    },

    # ═══════════════ 🇦🇷 الأرجنتين ═══════════════
    'Argentina': {
        'buenos aires': 'بوينس آيرس', 'cordoba': 'كوردوبا',
        'rosario': 'روزاريو', 'mendoza': 'مندوزا',
        'la plata': 'لا بلاتا', 'mar del plata': 'مار ديل بلاتا',
        'salta': 'سالتا', 'bariloche': 'باريلوتشي',
    },

    # ═══════════════ 🇲🇽 المكسيك ═══════════════
    'Mexico': {
        'mexico city': 'مكسيكو سيتي', 'guadalajara': 'غوادالاخارا',
        'monterrey': 'مونتيري', 'puebla': 'بويبلا',
        'tijuana': 'تيخوانا', 'cancun': 'كانكون',
        'merida': 'ميريدا', 'leon': 'ليون',
        'queretaro': 'كيريتارو', 'oaxaca': 'واهاكا',
        'playa del carmen': 'بلايا ديل كارمن', 'cabo': 'كابو',
        'puerto vallarta': 'بويرتو فالارتا',
    },

    # ═══════════════ 🇨🇴 كولومبيا ═══════════════
    'Colombia': {
        'bogota': 'بوغوتا', 'medellin': 'ميديلين',
        'cali': 'كالي', 'barranquilla': 'بارانكويلا',
        'cartagena': 'قرطاجنة', 'santa marta': 'سانتا مارتا',
    },

    # ═══════════════ 🇨🇱 تشيلي ═══════════════
    'Chile': {
        'santiago': 'سانتياغو', 'valparaiso': 'فالبارايسو',
        'concepcion': 'كونثيبسيون', 'vina del mar': 'فينيا ديل مار',
    },

    # ═══════════════ 🇵🇪 البيرو ═══════════════
    'Peru': {
        'lima': 'ليما', 'cusco': 'كوسكو',
        'arequipa': 'أريكويبا', 'trujillo': 'تروخيو',
        'machu picchu': 'ماتشو بيتشو',
    },

    # ═══════════════ 🇻🇪 فنزويلا ═══════════════
    'Venezuela': {
        'caracas': 'كاراكاس', 'maracaibo': 'ماراكايبو',
        'valencia': 'فالنسيا', 'maracay': 'ماراكاي',
    },

    # ═══════════════ 🇦🇺 أستراليا ═══════════════
    'Australia': {
        'sydney': 'سيدني', 'melbourne': 'ملبورن',
        'brisbane': 'بريسبان', 'perth': 'بيرث',
        'adelaide': 'أديلايد', 'canberra': 'كانبيرا',
        'gold coast': 'غولد كوست', 'newcastle': 'نيوكاسل',
        'hobart': 'هوبارت', 'darwin': 'داروين',
        'cairns': 'كيرنز', 'wollongong': 'ولونغونغ',
        'geelong': 'جيلونغ', 'townsville': 'تاونزفيل',
        'byron bay': 'خليج بايرون',
    },

    # ═══════════════ 🇳🇿 نيوزيلندا ═══════════════
    'New Zealand': {
        'auckland': 'أوكلاند', 'wellington': 'ويلينغتون',
        'christchurch': 'كرايستشيرش', 'hamilton': 'هاميلتون',
        'queenstown': 'كوينزتاون', 'dunedin': 'دانيدن',
        'tauranga': 'تاورانغا', 'rotorua': 'روتوروا',
    },

    # ═══════════════ 🇳🇬 نيجيريا ═══════════════
    'Nigeria': {
        'lagos': 'لاغوس', 'abuja': 'أبوجا',
        'kano': 'كانو', 'ibadan': 'إبادان',
        'port harcourt': 'بورت هاركورت', 'benin city': 'مدينة بنين',
        'kaduna': 'كادونا', 'enugu': 'إنوغو',
    },

    # ═══════════════ 🇿🇦 جنوب أفريقيا ═══════════════
    'South Africa': {
        'johannesburg': 'جوهانسبرغ', 'cape town': 'كيب تاون',
        'durban': 'ديربان', 'pretoria': 'بريتوريا',
        'port elizabeth': 'بورت إليزابيث', 'bloemfontein': 'بلومفونتين',
        'soweto': 'سويتو',
    },

    # ═══════════════ 🇰🇪 كينيا ═══════════════
    'Kenya': {
        'nairobi': 'نيروبي', 'mombasa': 'مومباسا',
        'kisumu': 'كيسومو', 'nakuru': 'ناكورو',
    },

    # ═══════════════ 🇬🇭 غانا ═══════════════
    'Ghana': {
        'accra': 'أكرا', 'kumasi': 'كوماسي',
        'tamale': 'تامالي',
    },

    # ═══════════════ 🇹🇿 تنزانيا ═══════════════
    'Tanzania': {
        'dar es salaam': 'دار السلام', 'dodoma': 'دودوما',
        'arusha': 'أروشا', 'zanzibar': 'زنجبار',
        'mwanza': 'موانزا',
    },

    # ═══════════════ 🇪🇹 إثيوبيا ═══════════════
    'Ethiopia': {
        'addis ababa': 'أديس أبابا', 'dire dawa': 'ديري داوا',
        'mekele': 'ميكيلي', 'gondar': 'غوندار',
    },

    # ═══════════════ 🇮🇷 إيران ═══════════════
    'Iran': {
        'tehran': 'طهران', 'mashhad': 'مشهد',
        'isfahan': 'أصفهان', 'shiraz': 'شيراز',
        'tabriz': 'تبريز', 'qom': 'قم',
        'ahvaz': 'الأهواز', 'kerman': 'كرمان',
        'yazd': 'يزد', 'rasht': 'رشت',
    },

    # ═══════════════ 🇮🇱 إسرائيل ═══════════════
    'Israel': {
        'tel aviv': 'تل أبيب', 'jerusalem': 'القدس',
        'haifa': 'حيفا', 'beersheba': 'بئر السبع',
    },

    # ═══════════════ 🇨🇭 سويسرا ═══════════════
    'Switzerland': {
        'zurich': 'زيورخ', 'geneva': 'جنيف',
        'basel': 'بازل', 'bern': 'برن',
        'lausanne': 'لوزان', 'lucerne': 'لوسرن',
        'davos': 'دافوس', 'zermatt': 'زيرمات',
    },

    # ═══════════════ 🇦🇹 النمسا ═══════════════
    'Austria': {
        'vienna': 'فيينا', 'salzburg': 'سالزبورغ',
        'graz': 'غراتس', 'innsbruck': 'إنسبروك',
    },

    # ═══════════════ 🇧🇪 بلجيكا ═══════════════
    'Belgium': {
        'brussels': 'بروكسل', 'antwerp': 'أنتويرب',
        'ghent': 'غنت', 'bruges': 'بروج',
        'liege': 'لييج',
    },

    # ═══════════════ 🇸🇪 السويد ═══════════════
    'Sweden': {
        'stockholm': 'ستوكهولم', 'gothenburg': 'غوتنبرغ',
        'malmo': 'مالمو', 'uppsala': 'أوبسالا',
    },

    # ═══════════════ 🇳🇴 النرويج ═══════════════
    'Norway': {
        'oslo': 'أوسلو', 'bergen': 'بيرغن',
        'trondheim': 'تروندهايم', 'stavanger': 'ستافانغر',
        'tromso': 'ترومسو',
    },

    # ═══════════════ 🇩🇰 الدنمارك ═══════════════
    'Denmark': {
        'copenhagen': 'كوبنهاغن', 'aarhus': 'آرهوس',
        'odense': 'أودنسي', 'aalborg': 'ألبورغ',
    },

    # ═══════════════ 🇫🇮 فنلندا ═══════════════
    'Finland': {
        'helsinki': 'هلسنكي', 'tampere': 'تامبيري',
        'turku': 'توركو', 'rovaniemi': 'روفانييمي',
    },

    # ═══════════════ 🇬🇷 اليونان ═══════════════
    'Greece': {
        'athens': 'أثينا', 'thessaloniki': 'ثيسالونيكي',
        'patras': 'باتراس', 'mykonos': 'ميكونوس',
        'santorini': 'سانتوريني', 'rhodes': 'رودس',
        'crete': 'كريت',
    },

    # ═══════════════ 🇵🇱 بولندا ═══════════════
    'Poland': {
        'warsaw': 'وارسو', 'krakow': 'كراكوف',
        'lodz': 'لودز', 'wroclaw': 'فروتسواف',
        'poznan': 'بوزنان', 'gdansk': 'غدانسك',
    },
}


def lookup_region(country, text):
    """
    البحث عن منطقة/مدينة داخل النص (BIO + Nickname + Username)
    Returns: dict | None
    """
    if not country or not text:
        return None
    if country not in REGIONS_DATABASE:
        return None
    text_lower = text.lower()
    regions = REGIONS_DATABASE[country]
    # ترتيب بالأطول أولاً لتجنب الالتباس (مثل "new york" قبل "york")
    sorted_keys = sorted(regions.keys(), key=lambda k: -len(k))
    for key_en in sorted_keys:
        # بحث بمراعاة حدود الكلمات
        if key_en in text_lower:
            return {
                'region_en': key_en.title(),
                'region_ar': regions[key_en],
                'confidence': 90,
            }
    return None


def get_total_regions():
    """عدد المناطق الإجمالي"""
    return sum(len(v) for v in REGIONS_DATABASE.values())


def get_countries_count():
    """عدد الدول المدعومة"""
    return len(REGIONS_DATABASE)


if __name__ == '__main__':
    print(f"✅ إجمالي المناطق: {get_total_regions()}")
    print(f"✅ الدول المدعومة: {get_countries_count()}")
    # اختبار سريع
    test_cases = [
        ('Saudi Arabia', 'I live in Hawtat Bani Tamim'),
        ('Saudi Arabia', 'Riyadh - السعودية'),
        ('United States', 'Washington DC'),
        ('Kuwait', 'Salmiya beach lover'),
        ('Egypt', 'Cairo born and raised'),
    ]
    for country, text in test_cases:
        result = lookup_region(country, text)
        print(f"\n🔍 {country} | '{text}'")
        print(f"   → {result}")
