import pandas as pd
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from io import BytesIO

MAX_WORKERS = 20

PLATFORM_URLS = {
    "x": "https://x.com/{}",
    "instagram": "https://www.instagram.com/{}/",
    "youtube": "https://www.youtube.com/@{}",
    "facebook": "https://www.facebook.com/{}",
    "snapchat": "https://www.snapchat.com/add/{}",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def استخراج_اسم_الحساب(html):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("meta", property="og:title")

    if title and title.get("content"):
        return title["content"]

    if soup.title:
        return soup.title.text

    return ""


def استخراج_عدد_المتابعين(html):
    soup = BeautifulSoup(html, "html.parser")

    metas = soup.find_all("meta")

    for meta in metas:
        content = str(meta.get("content", ""))

        if "followers" in content.lower():
            return content

    return ""


def معالجة_الحساب(row):

    المنصة = str(row["platform"]).strip().lower()
    المستخدم = str(row["username"]).replace("@", "").strip()

    result = {
        "المنصة": المنصة,
        "اسم المستخدم": المستخدم,
        "اسم الحساب": "",
        "رابط الحساب": "",
        "الدولة": "",
        "تاريخ إنشاء الحساب": "",
        "عدد المتابعين": "",
        "الحالة": "",
    }

    if المنصة not in PLATFORM_URLS:
        result["الحالة"] = "منصة غير مدعومة"
        return result

    الرابط = PLATFORM_URLS[المنصة].format(المستخدم)

    try:

        response = requests.get(
            الرابط,
            headers=HEADERS,
            timeout=10
        )

        result["رابط الحساب"] = response.url

        if response.status_code == 200:

            html = response.text

            result["اسم الحساب"] = استخراج_اسم_الحساب(html)
            result["عدد المتابعين"] = استخراج_عدد_المتابعين(html)
            result["الحالة"] = "تم"

        else:
            result["الحالة"] = f"خطأ {response.status_code}"

    except Exception as e:
        result["الحالة"] = str(e)

    return result


st.set_page_config(
    page_title="مولد معلومات حسابات التواصل",
    layout="wide"
)

st.title("مولد معلومات حسابات التواصل الاجتماعي")

st.markdown("""
### صيغة ملف Excel المطلوبة

| platform | username |
|---|---|
| x | nasa |
| instagram | natgeo |
| youtube | MrBeast |
| facebook | Meta |
| snapchat | snapchat |
""")

template_df = pd.DataFrame([
    {"platform": "x", "username": "nasa"},
    {"platform": "instagram", "username": "natgeo"},
])

template_output = BytesIO()

with pd.ExcelWriter(template_output, engine="openpyxl") as writer:
    template_df.to_excel(writer, index=False)

template_output.seek(0)

st.download_button(
    label="تحميل قالب Excel",
    data=template_output,
    file_name="template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uploaded_file = st.file_uploader(
    "ارفع ملف Excel",
    type=["xlsx"]
)

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    st.write("### معاينة البيانات")
    st.dataframe(df.head())

    if st.button("بدء المعالجة"):

        rows = df.head(500).to_dict("records")

        النتائج = []

        progress = st.progress(0)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

            futures = [
                executor.submit(معالجة_الحساب, row)
                for row in rows
            ]

            completed = 0

            for future in as_completed(futures):

                النتائج.append(future.result())

                completed += 1

                progress.progress(completed / len(futures))

        output_df = pd.DataFrame(النتائج)

        st.success("تم استخراج البيانات")

        st.dataframe(output_df)

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            output_df.to_excel(writer, index=False)

        output.seek(0)

        st.download_button(
            label="تحميل ملف Excel النهائي",
            data=output,
            file_name="نتائج_الحسابات.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
