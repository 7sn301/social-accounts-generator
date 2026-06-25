📘 دليل إعداد لوحة التحليلات الآمنة — بصير v2.1.8
🆔 المعرّف: BSR-V218-SETUP-GUIDE-AHMAD-20260613
📅 التاريخ: 2026-06-13
👨‍💼 القائد: د. أحمد الفنّي
📌 الإصدار: v2.1.8-Admin-Secure-Analytics
---
🎯 ما يفعله النظام الجديد
✅ يُخفي صفحة `📊 Analytics` القديمة من الـ sidebar
✅ يُتيح الوصول للوحة فقط عبر `baseer1.streamlit.app/admin`
✅ يحمي اللوحة بـ `bcrypt` (12 rounds) + session tokens
✅ يقفل IP بعد 5 محاولات فاشلة لمدّة 30 دقيقة
✅ يُسجّل كل مستخدم يضغط `/start` على البوت:
🆔 Telegram ID
👤 Username
🪪 الاسم الأوّل + الأخير
🌐 IP Address
🌍 الدولة + المدينة (من IP)
🌐 ISP
🕒 أوّل ظهور + آخر ظهور
🔍 عدد البحثات الكلّي
✅ يُسجّل كل بحث مع نتيجة الدولة
---
📂 ملفّات الحزمة (7 ملفّات)
```
baseer_admin_v218/
├── analytics_db.py         # قاعدة بيانات SQLite
├── admin_auth.py           # نظام المصادقة الآمن
├── bot_v218.py             # البوت مع تسجيل المستخدمين
├── hide_pages.py           # إخفاء الـ sidebar
├── requirements.txt        # المكتبات (مع bcrypt)
├── .env.example            # قالب المتغيّرات
├── .streamlit/config.toml  # إعدادات Streamlit
├── pages/99_admin.py       # صفحة /admin المحميّة
└── SETUP_GUIDE.md          # هذا الدليل
```
---
🚀 خطوات التطبيق على GitHub (10 دقائق)
1️⃣ رفع الملفّات على المستودع
الملف	المسار في GitHub
`analytics_db.py`	`/analytics_db.py`
`admin_auth.py`	`/admin_auth.py`
`bot_v218.py`	استبدل `/bot.py`
`hide_pages.py`	`/hide_pages.py`
`requirements.txt`	حدّث الموجود
`pages/99_admin.py`	`/pages/99_admin.py`
2️⃣ حذف الصفحة القديمة من GitHub
🔗 https://github.com/7sn301/social-accounts-generator/blob/main/pages/02_📊_Analytics.py
اضغط 🗑️ ثم Commit: `feat: Hide old analytics page, replace with secure /admin`
3️⃣ إضافة `hide_streamlit_pages()` في `app.py`
في أوّل سطور `app.py`، أضف:
```python
from hide_pages import hide_streamlit_pages
hide_streamlit_pages()
```
---
🔑 إعداد المتغيّرات على Streamlit Cloud
افتح: share.streamlit.io → Manage app → Settings → Secrets
أضف هذه القيم:
```toml
BOT_TOKEN = "PUT_YOUR_REAL_TOKEN"
BOT_USERNAME = "Baseer_Lookup_Bot"
ADMIN_USERNAME = "your_admin_username"
ADMIN_PASSWORD = "your_super_strong_password_24_chars_min"
ADMIN_PASSWORD_SALT = "your_64_hex_random_salt"
SESSION_SECRET = "your_random_url_safe_token_32_bytes"
ANALYTICS_DB_PATH = "./data/analytics.db"
TIMEZONE = "Asia/Riyadh"
MODE = "production"
PRIVACY_POLICY_URL = "https://github.com/7sn301/social-accounts-generator/blob/main/PRIVACY.md"
ADMIN_SESSION_TIMEOUT = "60"
MAX_LOGIN_ATTEMPTS = "5"
LOCKOUT_DURATION = "30"
```
🔐 توليد قيم آمنة بـ Python:
```python
import secrets, bcrypt
print("ADMIN_PASSWORD_SALT =", secrets.token_hex(32))
print("SESSION_SECRET =", secrets.token_urlsafe(32))
# لتشفير كلمة المرور:
pwd = b"my_super_strong_password"
print("ADMIN_PASSWORD_HASH =", bcrypt.hashpw(pwd, bcrypt.gensalt(rounds=12)).decode())
```
---
🚂 إعداد المتغيّرات على Railway (للبوت)
افتح Railway → Project → Variables وأضف:
المتغيّر	القيمة
`BOT_TOKEN`	توكن BotFather
`BOT_USERNAME`	Baseer_Lookup_Bot
`ANALYTICS_DB_PATH`	`/app/data/analytics.db`
`TIMEZONE`	Asia/Riyadh
`MODE`	production
`MISE_PYTHON_GITHUB_ATTESTATIONS`	false
---
🔐 الوصول للوحة الإدارية
🌐 الرابط الجديد:
```
https://baseer1.streamlit.app/admin
```
🚪 الدخول:
أدخل `ADMIN_USERNAME` و `ADMIN_PASSWORD`
سيُمنح لك token صالح لـ 60 دقيقة
بعد 5 محاولات فاشلة → IP مقفول 30 دقيقة
---
📊 ما ستراه في اللوحة
📈 إحصائيات عامة
إجمالي المستخدمين الذين ضغطوا /start
إجمالي البحثات
عدد الدول المختلفة
👥 جدول المستخدمين
العمود	الوصف
🆔 Telegram ID	المعرّف الفريد للمستخدم
👤 Username	اسم Telegram (@username)
🪪 الاسم	الاسم الأوّل + الأخير
🌐 IP	عنوان IP
🌍 الدولة	من ipapi.co
🏙️ المدينة	من ipapi.co
🌐 ISP	مزوّد الخدمة
🔍 عدد البحثات	إجمالي البحثات
🕒 آخر ظهور	UTC timestamp
🔍 جدول البحثات لكل مستخدم
اختر `Telegram ID` → اعرض جميع بحثاته
الاستعلام + الوقت + الدولة المُكتشفة
🌍 أعلى الدول
ترتيب الدول حسب عدد المستخدمين
---
⚠️ ملاحظة مهمة عن IP
<div dir="rtl">
Telegram لا يُرسل IP الحقيقي للمستخدم! هذا قيد على المنصّة لحماية الخصوصية.
ما يمكن جلبه فعلياً:
✅ Telegram ID (دقيق 100%)
✅ Username (إذا متاح)
✅ First/Last name
✅ Language code
⚠️ IP — placeholder (`TELEGRAM_HIDDEN`) لأنّ Telegram يخفيه
حلّ بديل لاستخراج IP:
يمكنك إنشاء Web App داخل البوت يطلب موقع المستخدم بإذنه — هذا الحل الوحيد لكشف IP.
</div>
---
🛡️ مستويات الأمان المُطبَّقة
الميزة	الحالة
bcrypt 12 rounds	✅
Session tokens (32 bytes)	✅
IP lockout بعد 5 محاولات فاشلة	✅
Session timeout 60 دقيقة	✅
HttpOnly cookies	✅
إخفاء الـ sidebar	✅
URL مخصّص `/admin`	✅
Audit log لمحاولات الدخول	✅
---
🆘 استكشاف الأخطاء
المشكلة 1: لوحة التحكّم تطلب كلمة مرور لكنّها ترفض الصحيحة
الحل: تأكّد أنّ `ADMIN_PASSWORD_HASH` فارغ في البداية (سيتمّ تشفير `ADMIN_PASSWORD` تلقائياً عند أوّل دخول)
المشكلة 2: لا يظهر أي مستخدم في الجدول
الحل: تأكّد أنّ المستخدمين فعلاً ضغطوا `/start`. إذا كان البوت يعمل لكن DB فارغة، تحقّق من:
`ANALYTICS_DB_PATH` يشير لنفس المسار في كل من البوت + الموقع
مجلّد `data/` موجود مع صلاحيات كتابة
المشكلة 3: bcrypt مفقود
الحل: أضف في requirements.txt:
```
bcrypt>=4.1.0
```
المشكلة 4: صفحة Analytics القديمة لا تزال تظهر
الحل:
احذف `pages/02_📊_Analytics.py` من GitHub
أعد نشر التطبيق
تأكّد من `hide_streamlit_pages()` في `app.py`
---
📦 ملخّص الإنجاز
المتطلّب	الحالة
🔒 قفل بتشفير عالٍ (bcrypt)	✅
🚪 إخفاء Analytics القديمة	✅
🌐 رابط `/admin` مخصّص	✅
📊 تسجيل /start كاملاً	✅
🆔 Telegram ID	✅
👤 Username	✅
🌐 IP (placeholder)	⚠️
🌍 الدولة + المدينة	✅
🔍 جميع البحثات	✅
---
🦅 صنع بحبّ على يد د. أحمد الفنّي — 2026-06-13
🎨 RTL + Noto Sans Arabic / Tajawal
