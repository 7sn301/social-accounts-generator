from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import requests

TIKTOK_REGION_MAP = {
    "US": ("🇺🇸", "الولايات المتحدة"), "GB": ("🇬🇧", "المملكة المتحدة"),
    "SA": ("🇸🇦", "السعودية"), "AE": ("🇦🇪", "الإمارات"), "EG": ("🇪🇬", "مصر"),
    "IQ": ("🇮🇶", "العراق"), "JO": ("🇯🇴", "الأردن"), "KW": ("🇰🇼", "الكويت"),
    "QA": ("🇶🇦", "قطر"), "BH": ("🇧🇭", "البحرين"), "OM": ("🇴🇲", "عُمان"),
    "SY": ("🇸🇾", "سوريا"), "LB": ("🇱🇧", "لبنان"), "MA": ("🇲🇦", "المغرب"),
    "TN": ("🇹🇳", "تونس"), "DZ": ("🇩🇿", "الجزائر"), "LY": ("🇱🇾", "ليبيا"),
    "YE": ("🇾🇪", "اليمن"), "TR": ("🇹🇷", "تركيا"), "IN": ("🇮🇳", "الهند"),
    "PK": ("🇵🇰", "باكستان"), "ID": ("🇮🇩", "إندونيسيا"), "PH": ("🇵🇭", "الفلبين"),
    "TH": ("🇹🇭", "تايلاند"), "VN": ("🇻🇳", "فيتنام"), "MY": ("🇲🇾", "ماليزيا"),
    "SG": ("🇸🇬", "سنغافورة"), "JP": ("🇯🇵", "اليابان"), "KR": ("🇰🇷", "كوريا الجنوبية"),
    "CN": ("🇨🇳", "الصين"), "RU": ("🇷🇺", "روسيا"), "DE": ("🇩🇪", "ألمانيا"),
    "FR": ("🇫🇷", "فرنسا"), "IT": ("🇮🇹", "إيطاليا"), "ES": ("🇪🇸", "إسبانيا"),
    "BR": ("🇧🇷", "البرازيل"), "MX": ("🇲🇽", "المكسيك"), "CA": ("🇨🇦", "كندا"),
    "AU": ("🇦🇺", "أستراليا"), "NG": ("🇳🇬", "نيجيريا"), "ZA": ("🇿🇦", "جنوب أفريقيا"),
    "CO": ("🇨🇴", "كولومبيا"), "AR": ("🇦🇷", "الأرجنتين"), "NL": ("🇳🇱", "هولندا"),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}
HEADERS_JSON = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.tiktok.com/",
    "Origin": "https://www.tiktok.com",
}


def _safe_region(code: Any) -> str:
    if not code or not isinstance(code, str):
        return ""
    code = code.strip().upper()
    return code if code in TIKTOK_REGION_MAP else ""


def _parse_script_json(html: str, script_id: str) -> Optional[dict]:
    m = re.search(rf'<script id="{re.escape(script_id)}"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _vote(votes: List[Tuple[str, str, int, str]]) -> Dict[str, Any]:
    if not votes:
        return {"region": "", "source": "unknown", "confidence": 0, "method": "", "evidence": [], "votes": []}
    scores = Counter()
    evidence = {}
    for country, source, weight, detail in votes:
        scores[country] += weight
        evidence.setdefault(country, []).append(f"{source}: {detail}")
    best_country, best_score = scores.most_common(1)[0]
    second_score = scores.most_common(2)[1][1] if len(scores) > 1 else 0
    confidence = max(25, min(97, int(best_score - second_score * 0.3)))
    source = "ensemble_v12" if len(scores) > 1 or len(votes) > 1 else votes[0][1]
    return {
        "region": best_country,
        "source": source,
        "confidence": confidence,
        "method": "ensemble_v12",
        "evidence": evidence.get(best_country, []),
        "votes": [{"country": c, "source": s, "weight": w, "detail": d} for c, s, w, d in votes],
    }


def _get_profile_direct_signals(username: str) -> Tuple[Dict[str, Any], str, List[Tuple[str, str, int, str]], Dict[str, Any]]:
    profile_user: Dict[str, Any] = {}
    sec_uid = ""
    votes: List[Tuple[str, str, int, str]] = []
    debug: Dict[str, Any] = {"profile_status": None, "profile_signals": []}
    html = ""
    try:
        resp = requests.get(f"https://www.tiktok.com/@{username}", headers=HEADERS, timeout=20, allow_redirects=True)
        debug["profile_status"] = resp.status_code
        if resp.status_code != 200:
            return profile_user, sec_uid, votes, debug
        html = resp.text
        universal = _parse_script_json(html, "__UNIVERSAL_DATA_FOR_REHYDRATION__")
        if universal:
            user_info = universal.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {}).get("userInfo", {})
            profile_user = user_info.get("user", {}) or user_info
            sec_uid = profile_user.get("secUid", "")
            region = _safe_region(profile_user.get("region"))
            if region:
                votes.append((region, "profile_user_region", 92, "UNIVERSAL.user.region"))
                debug["profile_signals"].append({"source": "UNIVERSAL.user.region", "region": region})
        sigi = _parse_script_json(html, "SIGI_STATE")
        if sigi:
            users = sigi.get("UserModule", {}).get("users", {}) or {}
            for key, user in users.items():
                unique = str(user.get("uniqueId") or "").lower()
                if unique == username.lower() or key == username:
                    region = _safe_region(user.get("region"))
                    if region:
                        votes.append((region, "profile_sigi_user", 88, f"SIGI.UserModule.users[{key}].region"))
                        debug["profile_signals"].append({"source": "SIGI matched user", "region": region})
                        break
    except Exception as e:
        debug["profile_error"] = str(e)
    return profile_user, sec_uid, votes, debug | {"profile_html": html}


def _get_internal_api_signals(sec_uid: str) -> List[Tuple[str, str, int, str]]:
    votes: List[Tuple[str, str, int, str]] = []
    if not sec_uid:
        return votes
    try:
        api_url = (
            f"https://www.tiktok.com/api/post/item_list/?aid=1988&count=6&secUid={sec_uid}&cursor=0"
            f"&sourceType=8&appId=1233&region=US&language=en"
        )
        api_resp = requests.get(api_url, headers=HEADERS_JSON, timeout=18)
        if api_resp.status_code != 200:
            return votes
        data = api_resp.json() or {}
        for item in (data.get("itemList") or [])[:6]:
            item_id = str(item.get("id", "item"))
            loc = _safe_region(item.get("locationCreated"))
            if loc:
                votes.append((loc, "internal_api_locationCreated", 91, item_id))
            author = item.get("author") or {}
            ar = _safe_region(author.get("region"))
            if ar:
                votes.append((ar, "internal_api_author_region", 89, item_id))
    except Exception:
        pass
    return votes


def _extract_video_signals_from_json(data: dict, username: str, video_id: str) -> List[Tuple[str, str, int, str]]:
    votes: List[Tuple[str, str, int, str]] = []
    scope = data.get("__DEFAULT_SCOPE__", {}) if isinstance(data, dict) else {}
    item_struct = scope.get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct", {})
    if item_struct:
        for field, weight in (("locationCreated", 87),):
            code = _safe_region(item_struct.get(field))
            if code:
                votes.append((code, f"video_universal_{field}", weight, video_id))
        code = _safe_region((item_struct.get("author") or {}).get("region"))
        if code:
            votes.append((code, "video_universal_author_region", 88, video_id))
    user_detail = scope.get("webapp.user-detail", {}).get("userInfo", {})
    user_obj = user_detail.get("user", {}) or user_detail
    if str(user_obj.get("uniqueId") or "").lower() == username.lower():
        code = _safe_region(user_obj.get("region"))
        if code:
            votes.append((code, "video_page_user_region", 86, video_id))
    return votes


def _extract_video_signals_from_sigi(data: dict, username: str, video_id: str) -> List[Tuple[str, str, int, str]]:
    votes: List[Tuple[str, str, int, str]] = []
    if not isinstance(data, dict):
        return votes
    users = data.get("UserModule", {}).get("users", {}) or {}
    matched_keys = []
    for key, user in users.items():
        if str(user.get("uniqueId") or "").lower() == username.lower() or key == username:
            matched_keys.append(key)
            code = _safe_region(user.get("region"))
            if code:
                votes.append((code, "video_sigi_user_region", 86, f"{video_id}:{key}"))
    items = data.get("ItemModule", {}) or {}
    for _, item in list(items.items())[:4]:
        code = _safe_region(item.get("locationCreated"))
        if code:
            votes.append((code, "video_sigi_locationCreated", 85, video_id))
        author = item.get("author")
        if isinstance(author, dict):
            code = _safe_region(author.get("region"))
            if code:
                votes.append((code, "video_sigi_author_region", 86, video_id))
        elif isinstance(author, str) and author in users:
            code = _safe_region((users.get(author) or {}).get("region"))
            if code:
                votes.append((code, "video_sigi_author_lookup", 85, f"{video_id}:{author}"))
    return votes


def _get_video_page_signals(username: str, profile_html: str) -> List[Tuple[str, str, int, str]]:
    votes: List[Tuple[str, str, int, str]] = []
    if not profile_html:
        return votes
    video_ids = list(dict.fromkeys(re.findall(r'/video/(\d{15,20})', profile_html)))[:3]
    for vid in video_ids:
        try:
            vresp = requests.get(f"https://www.tiktok.com/@{username}/video/{vid}", headers=HEADERS, timeout=18)
            if vresp.status_code != 200:
                continue
            universal = _parse_script_json(vresp.text, "__UNIVERSAL_DATA_FOR_REHYDRATION__")
            if universal:
                votes.extend(_extract_video_signals_from_json(universal, username, vid))
            sigi = _parse_script_json(vresp.text, "SIGI_STATE")
            if sigi:
                votes.extend(_extract_video_signals_from_sigi(sigi, username, vid))
        except Exception:
            continue
    return votes


def _get_tikwm_signal(username: str) -> List[Tuple[str, str, int, str]]:
    votes: List[Tuple[str, str, int, str]] = []
    try:
        tm_resp = requests.get(
            f"https://www.tikwm.com/api/user/info?unique_id={username}",
            headers={"User-Agent": HEADERS["User-Agent"]}, timeout=12
        )
        if tm_resp.status_code != 200:
            return votes
        data = tm_resp.json() or {}
        user_obj = data.get("data", {}).get("user", {}) or data.get("data", {}).get("user_info", {}) or data.get("data", {})
        for key in ("region", "country", "location", "createRegion", "create_region"):
            code = _safe_region(user_obj.get(key))
            if code:
                votes.append((code, "tikwm_api", 76, key))
                break
    except Exception:
        pass
    return votes


def _infer_from_bio(signature: str, language: str) -> Optional[Tuple[str, str, int, str]]:
    signature = (signature or "").lower()
    language = (language or "").lower().strip()
    hints = {
        "SA": ["السعودية", "سعودي", "الرياض", "جدة", "ksa", "riyadh", "saudi"],
        "EG": ["مصر", "مصري", "القاهرة", "egypt", "cairo"],
        "AE": ["الإمارات", "دبي", "uae", "dubai"],
        "IQ": ["العراق", "بغداد", "iraq", "baghdad"],
        "JO": ["الأردن", "عمان", "jordan", "amman"],
        "TR": ["تركيا", "istanbul", "turkey"],
        "GB": ["uk", "england", "london"],
        "US": ["usa", "america", "new york", "california"],
        "IT": ["italy", "italia", "rome", "milan"],
    }
    best_code = ""
    best_score = 0
    for code, terms in hints.items():
        score = sum(1 for t in terms if t in signature)
        if score > best_score:
            best_code, best_score = code, score
    if best_code and best_score >= 1:
        return (best_code, "bio_hints", 42 + best_score * 4, f"signature={signature[:120]}")
    lang_map = {"tr": "TR", "ja": "JP", "ko": "KR", "th": "TH", "vi": "VN", "id": "ID", "hi": "IN"}
    if language in lang_map:
        return (lang_map[language], "language_hint", 38, f"language={language}")
    return None


def fetch_region_from_video_page(username: str) -> Dict[str, Any]:
    result = {"region": "", "source": "unknown", "confidence": 0, "method": "", "evidence": [], "votes": []}
    if not username:
        return result
    username = username.strip().lstrip("@")

    profile_user, sec_uid, votes, debug = _get_profile_direct_signals(username)
    votes.extend(_get_internal_api_signals(sec_uid))
    votes.extend(_get_video_page_signals(username, debug.get("profile_html", "")))
    votes.extend(_get_tikwm_signal(username))
    bio_vote = _infer_from_bio(profile_user.get("signature", ""), profile_user.get("language", ""))
    if bio_vote:
        votes.append(bio_vote)

    final = _vote(votes)
    if final["region"] in TIKTOK_REGION_MAP:
        flag, ar = TIKTOK_REGION_MAP[final["region"]]
        final["region_flag"] = flag
        final["region_name_ar"] = ar
    else:
        final["region_flag"] = ""
        final["region_name_ar"] = ""
    final["debug_signal_count"] = len(votes)
    return final
