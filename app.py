"""
مولد معلومات حسابات التواصل الاجتماعي - النسخة المحسّنة
Social Accounts Info Generator - Enhanced Version
"""

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import io
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# ============ إعدادات الصفحة ============
st.set_page_config(
    page_title="مولد معلومات حسابات التواصل الاجتماعي",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ CSS مخصص لدعم RTL والتصميم العربي ============
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Tajawal:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', 'Tajawal', sans-serif !important;
        direction: rtl;
        text-align: right;
    }

    .main .block-container {
        direction: rtl;
        text-align: right;
        padding-top: 2rem;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif !important;
        text-align: right;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 700;
        font-family: 'Cairo', sans-serif;
        transition: all 0.3s ease;
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    .stTextArea textarea {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', monospace;
        font-size: 14px;
    }

    .stTextInput input {
        direction: ltr;
        text-align: left;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
        padding: 1rem;
        border-radius: 12px;
        border-right: 4px solid #667eea;
        margin: 0.5rem 0;
    }

    .platform-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
        margin: 2px;
    }

    [data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }

    .stDataFrame {
        direction: ltr;
    }

    .success-box {
        background: #d1fae5;
        border-right: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    .error-box {
        background: #fee2e2;
        border-right: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    .info-box {
        background: #dbeafe;
        border-right: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }

    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============ ثوابت المنصات ============
PLATFORMS = {
    "x": {"name": "X (Twitter)", "icon": "🐦", "url": "https://x.com/{}", "color": "#000000"},
    "twitter": {"name": "Twitter", "icon": "🐦", "url": "https://twitter.com/{}", "color": "#1DA1F2"},
    "instagram": {"name": "Instagram", "icon": "📷", "url": "https://www.instagram.com/{}/", "color": "#E1306C"},
    "youtube": {"name": "YouTube", "icon": "▶️", "url": "https://www.youtube.com/@{}", "color": "#FF0000"},
    "facebook": {"name": "Facebook", "icon": "👥", "url": "https://www.facebook.com/{}", "color": "#1877F2"},
    "snapchat": {"name": "Snapchat", "icon": "👻", "url": "https://www.snapchat.com/add/{}", "color": "#FFFC00"},
    "tiktok": {"name": "TikTok", "icon": "🎵", "url": "https://www.tiktok.com/@{}", "color": "#000000"},
    "linkedin": {"name": "LinkedIn", "icon": "💼", "url": "https://www.linkedin.com/in/{}", "color": "#0A66C2"},
    "threads": {"name": "Threads", "icon": "🧵", "url": "https://www.threads.net/@{}", "color": "#000000"},
    "reddit": {"name": "Reddit", "icon": "🤖", "url": "https://www.reddit.com/user/{}", "color": "#FF4500"},
    "pinterest": {"name": "Pinterest", "icon": "📌", "url": "https://www.pinterest.com/{}/", "color": "#E60023"},
    "telegram": {"name": "Telegram", "icon": "✈️", "url": "https://t.me/{}", "color": "#0088cc"},
    "twitch": {"name": "Twitch", "icon": "🎮", "url": "https://www.twitch.tv/{}", "color": "#9146FF"},
    "github": {"name": "GitHub", "icon": "💻", "url": "https://github.com/{}", "color": "#181717"},
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}


# ============ دوال مساعدة ============
def parse_url_to_platform(url: str):
    """استخراج المنصة واسم المستخدم من رابط."""
    url = url.strip()
    if not url:
        return None, None

    # إذا لم يبدأ بـ http، أضفها
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.strip("/")

        mapping = {
            "x.com": "x",
            "twitter.com": "twitter",
            "instagram.com": "instagram",
            "youtube.com": "youtube",
            "youtu.be": "youtube",
            "facebook.com": "facebook",
            "fb.com": "facebook",
            "snapchat.com": "snapchat",
            "tiktok.com": "tiktok",
            "linkedin.com": "linkedin",
            "threads.net": "threads",
            "reddit.com": "reddit",
            "pinterest.com": "pinterest",
            "t.me": "telegram",
            "telegram.me": "telegram",
            "twitch.tv": "twitch",
            "github.com": "github",
        }

        platform = mapping.get(host)
        if not platform:
            return None, None

        # استخراج اسم المستخدم
        username = path.split("/")[0] if path else ""
        username = username.replace("@", "")

        # حالات خاصة
        if platform == "youtube" and "channel/" in parsed.path:
            username = parsed.path.split("channel/")[-1].strip("/")
        elif platform == "linkedin" and "in/" in parsed.path:
            username = parsed.path.split("in/")[-1].strip("/").split("/")[0]
        elif platform == "reddit" and ("user/" in parsed.path or "u/" in parsed.path):
            for prefix in ["user/", "u/"]:
                if prefix in parsed.path:
                    username = parsed.path.split(prefix)[-1].strip("/").split("/")[0]
                    break
        elif platform == "snapchat" and "add/" in parsed.path:
            username = parsed.path.split("add/")[-1].strip("/").split("/")[0]

        return platform, username if username else None
    except Exception:
        return None, None


def parse_manual_input(text: str):
    """تحليل الإدخال اليدوي - يدعم الأسطر بصيغ متعددة."""
    entries = []
    seen = set()
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        # تجاهل التعليقات
        if line.startswith("#"):
            continue

        platform, username = None, None

        # إذا كان رابطاً
        if "http" in line or any(d in line for d in [".com", ".net", ".tv", "t.me"]):
            platform, username = parse_url_to_platform(line)
        else:
            # صيغة: platform,username  أو  platform:username  أو  platform username
            for sep in [",", ":", "\t", "|", " "]:
                if sep in line:
                    parts = [p.strip() for p in line.split(sep, 1)]
                    if len(parts) == 2 and parts[0].lower() in PLATFORMS:
                        platform = parts[0].lower()
                        username = parts[1].replace("@", "").strip()
                        break

        if platform and username:
            key = (platform, username.lower())
            if key not in seen:
                seen.add(key)
                entries.append({"platform": platform, "username": username})

    return entries


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_account_info(platform: str, username: str):
    """سحب معلومات الحساب من المنصة (مع تخزين مؤقت لساعة)."""
    result = {
        "platform": platform,
        "username": username,
        "profile_url": "",
        "display_name": "",
        "bio": "",
        "followers": "",
        "verified": False,
        "profile_image": "",
        "status": "❌ فشل",
        "error": "",
    }

    if platform not in PLATFORMS:
        result["error"] = "منصة غير مدعومة"
        return result

    profile_url = PLATFORMS[platform]["url"].format(username)
    result["profile_url"] = profile_url

    try:
        response = requests.get(profile_url, headers=HEADERS, timeout=10, allow_redirects=True)

        if response.status_code == 404:
            result["error"] = "الحساب غير موجود"
            return result

        if response.status_code != 200:
            result["error"] = f"كود الاستجابة: {response.status_code}"
            # حتى مع فشل السحب، الرابط نفسه قد يكون صحيحاً
            result["status"] = "⚠️ الرابط فقط"
            return result

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # استخراج الميتا تاجز العامة
        def get_meta(prop):
            tag = soup.find("meta", {"property": prop}) or soup.find("meta", {"name": prop})
            return tag.get("content", "") if tag else ""

        result["display_name"] = (
            get_meta("og:title")
            or get_meta("twitter:title")
            or (soup.title.string if soup.title else "")
        ).strip()

        result["bio"] = (
            get_meta("og:description") or get_meta("description") or get_meta("twitter:description")
        ).strip()

        result["profile_image"] = get_meta("og:image") or get_meta("twitter:image")

        # محاولة استخراج عدد المتابعين من الوصف (للمنصات التي تذكره)
        bio_text = result["bio"]
        followers_match = re.search(
            r"([\d,.]+\s*[KMB]?)\s*(?:Followers|متابع|subscribers|مشترك)",
            bio_text,
            re.IGNORECASE,
        )
        if followers_match:
            result["followers"] = followers_match.group(1).strip()

        # التحقق من التوثيق (مؤشرات شائعة)
        if "verified" in html.lower()[:50000] or "✓" in result["display_name"]:
            result["verified"] = True

        if result["display_name"] or result["bio"]:
            result["status"] = "✅ نجح"
        else:
            result["status"] = "⚠️ معلومات محدودة"

    except requests.Timeout:
        result["error"] = "انتهت مهلة الاتصال"
    except requests.ConnectionError:
        result["error"] = "خطأ في الاتصال"
    except Exception as e:
        result["error"] = str(e)[:100]

    return result


def fetch_batch(entries, max_workers=10, progress_callback=None):
    """سحب معلومات دفعة من الحسابات بالتوازي."""
    results = []
    total = len(entries)
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_account_info, e["platform"], e["username"]): e
            for e in entries
        }
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                entry = futures[future]
                results.append({
                    "platform": entry["platform"],
                    "username": entry["username"],
                    "status": "❌ فشل",
                    "error": str(e)[:100],
                    "profile_url": "",
                    "display_name": "",
                    "bio": "",
                    "followers": "",
                    "verified": False,
                    "profile_image": "",
                })
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    return results


def create_sample_excel():
    """إنشاء ملف Excel نموذجي."""
    sample_data = {
        "platform": ["x", "instagram", "youtube", "facebook", "tiktok", "linkedin", "github", "twitch"],
        "username": ["nasa", "natgeo", "MrBeast", "Meta", "khaby.lame", "billgates", "torvalds", "shroud"],
    }
    df = pd.DataFrame(sample_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="accounts")
    return output.getvalue()


def results_to_excel(results):
    """تصدير النتائج إلى Excel."""
    df = pd.DataFrame(results)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="results")
    return output.getvalue()


# ============ الواجهة الرئيسية ============
st.markdown(
    """
    <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 15px; margin-bottom: 2rem; color: white;">
        <h1 style="color: white; margin: 0;">🌐 مولد معلومات حسابات التواصل الاجتماعي</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.95;">
            سحب معلومات الحسابات من 14+ منصة • دعم أكثر من 300 حساب دفعة واحدة
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============ الشريط الجانبي ============
with st.sidebar:
    st.markdown("### ⚙️ الإعدادات")

    max_workers = st.slider(
        "عدد العمليات المتوازية",
        min_value=1,
        max_value=20,
        value=10,
        help="كلما زاد العدد، كان السحب أسرع ولكن قد يسبب حظراً مؤقتاً",
    )

    st.markdown("---")
    st.markdown("### 📊 المنصات المدعومة")
    cols = st.columns(2)
    for i, (key, info) in enumerate(PLATFORMS.items()):
        cols[i % 2].markdown(f"{info['icon']} **{info['name']}**")

    st.markdown("---")
    st.markdown("### 📥 ملف نموذجي")
    st.download_button(
        label="⬇️ تحميل ملف Excel نموذجي",
        data=create_sample_excel(),
        file_name="sample_accounts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.markdown("---")
    st.caption("💡 يستخدم التطبيق scraping للبيانات العامة فقط. لا يجمع معلومات خاصة.")

# ============ التبويبات الرئيسية ============
tab1, tab2, tab3 = st.tabs(["📝 الإدخال اليدوي", "📂 رفع ملف Excel", "ℹ️ التعليمات"])

# ============ التبويب 1: الإدخال اليدوي ============
with tab1:
    st.markdown("### 📝 الإدخال اليدوي - يدعم أكثر من 300 حساب")

    st.markdown(
        """
        <div class="info-box">
        <strong>الصيغ المدعومة (يمكن خلطها معاً):</strong><br>
        • <code>platform,username</code> مثال: <code>instagram,natgeo</code><br>
        • <code>platform:username</code> مثال: <code>youtube:MrBeast</code><br>
        • <code>platform username</code> مثال: <code>tiktok khaby.lame</code><br>
        • <strong>رابط مباشر</strong> مثال: <code>https://x.com/nasa</code><br>
        • أسطر تبدأ بـ <code>#</code> تُعتبر تعليقات وتُتجاهل
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_text = """# يمكنك لصق ما يصل إلى 300+ حساب أو رابط هنا
# أمثلة بصيغ مختلفة:
x,nasa
instagram,natgeo
youtube:MrBeast
facebook Meta
https://www.tiktok.com/@khaby.lame
https://www.linkedin.com/in/billgates
github,torvalds
twitch,shroud
threads,zuck
reddit,spez
pinterest,pinterest
t.me/durov
"""

    col_input, col_actions = st.columns([4, 1])

    with col_input:
        manual_input = st.text_area(
            "الصق الحسابات أو الروابط (سطر لكل حساب):",
            value=default_text,
            height=400,
            key="manual_input",
            help="يمكن لصق أكثر من 300 سطر دفعة واحدة",
        )

    with col_actions:
        st.markdown("#### 🛠️ أدوات")

        if st.button("🔍 معاينة المدخلات", use_container_width=True):
            entries = parse_manual_input(manual_input)
            st.session_state["preview_entries"] = entries

        if st.button("🧹 مسح", use_container_width=True):
            st.session_state["manual_input"] = ""
            st.rerun()

        # عداد فوري
        live_count = len([l for l in manual_input.splitlines() if l.strip() and not l.strip().startswith("#")])
        st.metric("📊 الأسطر النشطة", live_count)

    # عرض المعاينة
    if "preview_entries" in st.session_state:
        entries = st.session_state["preview_entries"]
        if entries:
            st.success(f"✅ تم التعرف على **{len(entries)}** حساب صحيح")
            with st.expander(f"عرض الحسابات المُحلّلة ({len(entries)})", expanded=False):
                preview_df = pd.DataFrame(entries)
                st.dataframe(preview_df, use_container_width=True, height=300)
        else:
            st.warning("⚠️ لم يتم التعرف على أي حساب صحيح. تحقق من الصيغة.")

    st.markdown("---")

    if st.button("🚀 ابدأ سحب المعلومات", type="primary", use_container_width=True, key="manual_fetch"):
        entries = parse_manual_input(manual_input)

        if not entries:
            st.error("❌ لم يتم العثور على حسابات صحيحة. راجع الصيغة في صندوق الإدخال.")
        else:
            st.info(f"🔄 جارٍ سحب معلومات **{len(entries)}** حساب...")

            progress_bar = st.progress(0)
            status_text = st.empty()
            start_time = time.time()

            def update_progress(done, total):
                progress_bar.progress(done / total)
                status_text.text(f"⏳ تمت معالجة {done}/{total} حساب...")

            results = fetch_batch(entries, max_workers=max_workers, progress_callback=update_progress)
            elapsed = time.time() - start_time

            progress_bar.empty()
            status_text.empty()

            st.session_state["results"] = results
            st.session_state["elapsed"] = elapsed
            st.success(f"✅ تم الانتهاء في **{elapsed:.1f}** ثانية!")

# ============ التبويب 2: رفع ملف Excel ============
with tab2:
    st.markdown("### 📂 رفع ملف Excel")

    st.markdown(
        """
        <div class="info-box">
        يجب أن يحتوي الملف على عمودين: <code>platform</code> و <code>username</code><br>
        💡 يمكنك تحميل <strong>ملف نموذجي</strong> من الشريط الجانبي للتجربة.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "اختر ملف Excel (.xlsx)",
        type=["xlsx", "xls", "csv"],
        help="حد أقصى 200MB - يدعم Excel و CSV",
    )

    if uploaded:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)

            df.columns = [c.lower().strip() for c in df.columns]

            if "platform" not in df.columns or "username" not in df.columns:
                st.error("❌ الملف يجب أن يحتوي على عمودي `platform` و `username`")
            else:
                df = df[["platform", "username"]].dropna()
                df["platform"] = df["platform"].astype(str).str.lower().str.strip()
                df["username"] = df["username"].astype(str).str.replace("@", "").str.strip()

                st.success(f"✅ تم تحميل **{len(df)}** حساب من الملف")
                with st.expander("معاينة البيانات", expanded=True):
                    st.dataframe(df.head(20), use_container_width=True)

                if st.button("🚀 ابدأ سحب المعلومات", type="primary", use_container_width=True, key="excel_fetch"):
                    entries = df.to_dict("records")
                    st.info(f"🔄 جارٍ سحب معلومات **{len(entries)}** حساب...")

                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    start_time = time.time()

                    def update_progress(done, total):
                        progress_bar.progress(done / total)
                        status_text.text(f"⏳ تمت معالجة {done}/{total} حساب...")

                    results = fetch_batch(entries, max_workers=max_workers, progress_callback=update_progress)
                    elapsed = time.time() - start_time

                    progress_bar.empty()
                    status_text.empty()

                    st.session_state["results"] = results
                    st.session_state["elapsed"] = elapsed
                    st.success(f"✅ تم الانتهاء في **{elapsed:.1f}** ثانية!")
        except Exception as e:
            st.error(f"❌ خطأ في قراءة الملف: {e}")

# ============ التبويب 3: التعليمات ============
with tab3:
    st.markdown(
        """
    ### ℹ️ كيفية استخدام التطبيق

    #### 1️⃣ اختر طريقة الإدخال:
    - **الإدخال اليدوي**: لصق الحسابات مباشرة (يدعم 300+ حساب)
    - **رفع ملف Excel**: لقوائم كبيرة مُعدّة مسبقاً

    #### 2️⃣ المنصات المدعومة (14 منصة):
    X (Twitter)، Instagram، YouTube، Facebook، Snapchat، TikTok، LinkedIn، Threads، Reddit، Pinterest، Telegram، Twitch، GitHub.

    #### 3️⃣ الصيغ المقبولة في الإدخال اليدوي:
    | الصيغة | مثال |
    |--------|------|
    | فاصلة | `instagram,natgeo` |
    | نقطتان | `youtube:MrBeast` |
    | مسافة | `tiktok khaby.lame` |
    | رابط مباشر | `https://x.com/nasa` |

    #### 4️⃣ المعلومات المسحوبة:
    - 🔗 رابط الحساب
    - 👤 الاسم الظاهر
    - 📝 النبذة (Bio)
    - 👥 عدد المتابعين (إن أمكن)
    - ✅ حالة التوثيق
    - 🖼️ صورة الملف الشخصي

    #### 5️⃣ تصدير النتائج:
    يمكن تنزيل النتائج بصيغة **CSV** أو **JSON** أو **Excel** بعد الانتهاء.

    #### ⚠️ ملاحظات مهمة:
    - التطبيق يجمع **البيانات العامة فقط** المتاحة على الصفحات الشخصية.
    - بعض المنصات (مثل Instagram, Facebook) تقيّد scraping بشكل صارم - النتائج قد تكون محدودة.
    - استخدام عدد عمليات متوازية كبير قد يسبب حظراً مؤقتاً من المنصة.
    - النتائج مخزنة مؤقتاً لمدة ساعة لتسريع الاستعلامات المتكررة.
    """
    )

# ============ عرض النتائج ============
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    df_results = pd.DataFrame(results)

    st.markdown("---")
    st.markdown("## 📊 النتائج")

    # ============ الإحصائيات ============
    total = len(results)
    success = sum(1 for r in results if r["status"] == "✅ نجح")
    partial = sum(1 for r in results if r["status"] == "⚠️ معلومات محدودة")
    link_only = sum(1 for r in results if r["status"] == "⚠️ الرابط فقط")
    failed = sum(1 for r in results if r["status"] == "❌ فشل")
    verified = sum(1 for r in results if r.get("verified"))

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📋 الإجمالي", total)
    col2.metric("✅ ناجح", success, delta=f"{success/total*100:.1f}%" if total else "0%")
    col3.metric("⚠️ جزئي", partial + link_only)
    col4.metric("❌ فشل", failed)
    col5.metric("✓ موثّق", verified)

    if "elapsed" in st.session_state:
        st.caption(f"⏱️ زمن المعالجة: {st.session_state['elapsed']:.1f} ثانية")

    # ============ توزيع المنصات ============
    if total > 0:
        platform_counts = df_results["platform"].value_counts()
        st.markdown("#### 📈 توزيع المنصات")
        st.bar_chart(platform_counts)

    # ============ فلترة العرض ============
    st.markdown("#### 🔍 فلترة النتائج")
    col_f1, col_f2 = st.columns(2)
    status_filter = col_f1.multiselect(
        "حسب الحالة",
        options=df_results["status"].unique().tolist(),
        default=df_results["status"].unique().tolist(),
    )
    platform_filter = col_f2.multiselect(
        "حسب المنصة",
        options=df_results["platform"].unique().tolist(),
        default=df_results["platform"].unique().tolist(),
    )

    filtered = df_results[
        df_results["status"].isin(status_filter) & df_results["platform"].isin(platform_filter)
    ]

    # ============ جدول النتائج ============
    st.markdown(f"#### 📋 جدول النتائج ({len(filtered)} سجل)")
    display_cols = [
        "platform", "username", "display_name", "bio",
        "followers", "verified", "status", "profile_url", "error",
    ]
    display_cols = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        height=400,
        column_config={
            "profile_url": st.column_config.LinkColumn("الرابط"),
            "verified": st.column_config.CheckboxColumn("موثّق"),
        },
    )

    # ============ خيارات التصدير ============
    st.markdown("#### 📥 تصدير النتائج")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    col_e1, col_e2, col_e3 = st.columns(3)

    csv_data = filtered.to_csv(index=False).encode("utf-8-sig")
    col_e1.download_button(
        "⬇️ تحميل CSV",
        data=csv_data,
        file_name=f"social_results_{timestamp}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    json_data = filtered.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
    col_e2.download_button(
        "⬇️ تحميل JSON",
        data=json_data,
        file_name=f"social_results_{timestamp}.json",
        mime="application/json",
        use_container_width=True,
    )

    excel_data = results_to_excel(filtered.to_dict("records"))
    col_e3.download_button(
        "⬇️ تحميل Excel",
        data=excel_data,
        file_name=f"social_results_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # ============ عرض البطاقات (للأول 12 نتيجة ناجحة) ============
    successful = [r for r in results if r["status"] in ("✅ نجح", "⚠️ معلومات محدودة")][:12]
    if successful:
        st.markdown("#### 🎴 بطاقات الحسابات (أول 12)")
        cols = st.columns(3)
        for i, r in enumerate(successful):
            with cols[i % 3]:
                platform_info = PLATFORMS.get(r["platform"], {"icon": "🌐", "color": "#667eea"})
                with st.container(border=True):
                    if r.get("profile_image"):
                        st.image(r["profile_image"], width=80)
                    st.markdown(f"**{platform_info['icon']} {r.get('display_name') or r['username']}**")
                    st.caption(f"@{r['username']} • {r['platform']}")
                    if r.get("bio"):
                        st.caption(r["bio"][:120] + ("..." if len(r["bio"]) > 120 else ""))
                    if r.get("verified"):
                        st.caption("✓ موثّق")
                    st.markdown(f"[🔗 فتح الحساب]({r['profile_url']})")
