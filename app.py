import re
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


MAX_WORKERS = 20
TIMEOUT = 10

PLATFORM_URLS = {
    "x": "https://x.com/{username}",
    "twitter": "https://x.com/{username}",
    "instagram": "https://www.instagram.com/{username}/",
    "youtube": "https://www.youtube.com/@{username}",
    "facebook": "https://www.facebook.com/{username}",
    "snapchat": "https://www.snapchat.com/add/{username}",
}

HEADERS = {"User-Agent": "Mozilla/5.0"}


def clean_username(username: str) -> str:
    username = str(username).strip()
    username = username.replace("@", "")
    username = username.rstrip("/")
    return username


def normalize_platform(platform: str) -> str:
    platform = str(platform).strip().lower()
    replacements = {
        "اكس": "x",
        "تويتر": "x",
        "انستغرام": "instagram",
        "انستقرام": "instagram",
        "يوتيوب": "youtube",
        "فيسبوك": "facebook",
        "سناب": "snapchat",
        "سناب شات": "snapchat",
    }
    return replacements.get(platform, platform)


def extract_name(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for prop in ["og:title", "twitter:title"]:
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        if tag and tag.get("content"):
            title = tag["content"].strip()
            title = re.sub(r"\s*[\(@|•-].*$", "", title).strip()
            return title

    if soup.title and soup.title.string:
        return soup.title.string.strip()

    return ""


def extract_canonical(html: str, fallback_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        return canonical["href"].strip()
    return fallback_url


def fetch_account(row):
    platform = normalize_platform(row.get("platform", ""))
    username = clean_username(row.get("username", ""))

    result = {
        "platform": platform,
        "input_username": username,
        "account_name": "",
        "permanent_identifier": username,
        "account_url": "",
        "status": "",
        "error": "",
    }

    if not platform or not username:
        result["status"] = "missing_data"
        return result

    if platform not in PLATFORM_URLS:
        result["status"] = "unsupported_platform"
        result["error"] = "المنصة غير مدعومة"
        return result

    url = PLATFORM_URLS[platform].format(username=username)
    result["account_url"] = url

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        result["account_url"] = response.url

        if response.status_code == 200:
            result["account_name"] = extract_name(response.text)
            result["account_url"] = extract_canonical(response.text, response.url)
            result["status"] = "ok"
        elif response.status_code == 404:
            result["status"] = "not_found"
        else:
            result["status"] = f"http_{response.status_code}"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


st.set_page_config(page_title="مولد حسابات التواصل", layout="wide")

st.title("مولد معلومات حسابات التواصل الاجتماعي")
st.write("ارفع ملف Excel يحتوي على عمودين: platform و username. الحد الأقصى 500 مدخل.")

sample_df = pd.DataFrame({
    "platform": ["x", "instagram", "youtube", "facebook", "snapchat"],
    "username": ["nasa", "natgeo", "MrBeast", "Meta", "snapchat"],
})

sample_output = BytesIO()
with pd.ExcelWriter(sample_output, engine="openpyxl") as writer:
    sample_df.to_excel(writer, index=False)
sample_output.seek(0)

st.download_button(
    "تحميل قالب Excel للمدخلات",
    sample_output,
    "input_template.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

uploaded_file = st.file_uploader("ارفع ملف Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("معاينة الملف")
    st.dataframe(df.head(20), use_container_width=True)

    required = {"platform", "username"}
    missing = required - set(df.columns)

    if missing:
        st.error(f"الأعمدة الناقصة: {', '.join(missing)}")
    else:
        if st.button("بدء المعالجة"):
            rows = df.head(500).to_dict("records")
            results = []
            progress = st.progress(0)

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(fetch_account, row) for row in rows]
                total = len(futures)

                for i, future in enumerate(as_completed(futures), start=1):
                    results.append(future.result())
                    progress.progress(i / total)

            output_df = pd.DataFrame(results)
            st.success("تمت المعالجة بنجاح")
            st.dataframe(output_df, use_container_width=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                output_df.to_excel(writer, index=False)
            output.seek(0)

            st.download_button(
                "تحميل ملف Excel النهائي",
                output,
                "social_accounts_output.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )