from __future__ import annotations

import json
import re
import time
import random
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
    "SE": ("🇸🇪", "السويد"), "NO": ("🇳🇴", "النرويج"), "PL": ("🇵🇱", "بولندا"),
    "UA": ("🇺🇦", "أوكرانيا"), "RO": ("🇷🇴", "رومانيا"), "GR": ("🇬🇷", "اليونان"),
    "PT": ("🇵🇹", "البرتغال"), "BE": ("🇧🇪", "بلجيكا"), "CZ": ("🇨🇿", "التشيك"),
    "HU": ("🇭🇺", "المجر"), "AT": ("🇦🇹", "النمسا"), "CH": ("🇨🇭", "سويسرا"),
    "IL": ("🇮🇱", "إسرائيل"), "IR": ("🇮🇷", "إيران"), "AF": ("🇦🇫", "أفغانستان"),
    "BD": ("🇧🇩", "بنغلاديش"), "MM": ("🇲🇲", "ميانمار"), "KH": ("🇰🇭", "كمبوديا"),
    "NP": ("🇳🇵", "نيبال"), "LK": ("🇱🇰", "سريلانكا"), "ET": ("🇪🇹", "إثيوبيا"),
    "GH": ("🇬🇭", "غانا"), "KE": ("🇰🇪", "كينيا"), "TZ": ("🇹🇿", "تنزانيا"),
    "UG": ("🇺🇬", "أوغندا"), "CM": ("🇨🇲", "الكاميرون"), "SD": ("🇸🇩", "السودان"),
    "SO": ("🇸🇴", "الصومال"), "DK": ("🇩🇰", "الدنمارك"), "FI": ("🇫🇮", "فنلندا"),
    "SK": ("🇸🇰", "سلوفاكيا"), "HR": ("🇭🇷", "كرواتيا"), "RS": ("🇷🇸", "صربيا"),
    "BG": ("🇧🇬", "بلغاريا"), "LT": ("🇱🇹", "ليتوانيا"), "LV": ("🇱🇻", "لاتفيا"),
    "EE": ("🇪🇪", "إستونيا"), "SI": ("🇸🇮", "سلوفينيا"), "MK": ("🇲🇰", "مقدونيا"),
    "AL": ("🇦🇱", "ألبانيا"), "BA": ("🇧🇦", "البوسنة"), "MN": ("🇲🇳", "منغوليا"),
    "KZ": ("🇰🇿", "كازاخستان"), "UZ": ("🇺🇿", "أوزبكستان"), "AZ": ("🇦🇿", "أذربيجان"),
    "GE": ("🇬🇪", "جورجيا"), "AM": ("🇦🇲", "أرمينيا"), "MD": ("🇲🇩", "مولدوفا"),
    "BY": ("🇧🇾", "بيلاروس"), "MO": ("🇲🇴", "ماكاو"), "TW": ("🇹🇼", "تايوان"),
    "HK": ("🇭🇰", "هونغ كونغ"), "CL": ("🇨🇱", "تشيلي"), "PE": ("🇵🇪", "بيرو"),
    "EC": ("🇪🇨", "الإكوادور"), "BO": ("🇧🇴", "بوليفيا"), "PY": ("🇵🇾", "باراغواي"),
    "UY": ("🇺🇾", "أوروغواي"), "VE": ("🇻🇪", "فنزويلا"), "CU": ("🇨🇺", "كوبا"),
    "DO": ("🇩🇴", "جمهورية الدومينيكان"), "GT": ("🇬🇹", "غواتيمالا"),
    "HN": ("🇭🇳", "هندوراس"), "SV": ("🇸🇻", "السلفادور"), "NI": ("🇳🇮", "نيكاراغوا"),
    "CR": ("🇨🇷", "كوستاريكا"), "PA": ("🇵🇦", "بنما"), "PR": ("🇵🇷", "بورتوريكو"),
    "NZ": ("🇳🇿", "نيوزيلندا"), "IE": ("🇮🇪", "أيرلندا"), "LU": ("🇱🇺", "لوكسمبورغ"),
    "IS": ("🇮🇸", "آيسلندا"), "CY": ("🇨🇾", "قبرص"), "MT": ("🇲🇹", "مالطا"),
}

# User-Agent pool for rotation
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
]

def _get_headers(mobile: bool = False) -> dict:
    ua = random.choice(UA_POOL)
    if mobile:
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
    return {
        "User-Agent": ua,
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Upgrade-Insecure-Requests": "1",
    }


def _safe_region(code: Any) -> str:
    if not code or not isinstance(code, str):
        return ""
    code = code.strip().upper()
    return code if code in TIKTOK_REGION_MAP else ""


def _parse_script_json(html: str, script_id: str) -> Optional[dict]:
    """Extract JSON from a named script tag."""
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
    scores: Counter = Counter()
    evidence: Dict[str, List[str]] = {}
    for country, source, weight, detail in votes:
        scores[country] += weight
        evidence.setdefault(country, []).append(f"{source}: {detail}")
    best_country, best_score = scores.most_common(1)[0]
    second_score = scores.most_common(2)[1][1] if len(scores) > 1 else 0
    confidence = max(25, min(97, int(best_score - second_score * 0.3)))
    source = "ensemble_v13" if len(scores) > 1 or len(votes) > 1 else votes[0][1]
    return {
        "region": best_country,
        "source": source,
        "confidence": confidence,
        "method": "ensemble_v13",
        "evidence": evidence.get(best_country, []),
        "votes": [{"country": c, "source": s, "weight": w, "detail": d} for c, s, w, d in votes],
    }


# ==================== LAYER 1: Profile Page Direct Scrape ====================
def _layer1_profile_page(username: str) -> Tuple[str, dict, str, List[Tuple[str, str, int, str]]]:
    """
    Scrape TikTok profile page and extract region from __UNIVERSAL_DATA_FOR_REHYDRATION__
    Returns: (html, profile_user_dict, sec_uid, votes)
    """
    votes: List[Tuple[str, str, int, str]] = []
    profile_user: dict = {}
    sec_uid: str = ""
    html: str = ""
    
    url = f"https://www.tiktok.com/@{username}"
    
    for attempt, mobile in enumerate([False, True]):
        try:
            headers = _get_headers(mobile=mobile)
            if attempt > 0:
                headers["Referer"] = "https://www.tiktok.com/foryou"
                time.sleep(1.5)
            
            resp = requests.get(url, headers=headers, timeout=22, allow_redirects=True)
            
            if resp.status_code == 200 and len(resp.text) > 5000:
                html = resp.text
                break
            elif resp.status_code in (403, 429):
                time.sleep(2)
                continue
        except Exception:
            continue
    
    if not html:
        return html, profile_user, sec_uid, votes
    
    # Parse __UNIVERSAL_DATA_FOR_REHYDRATION__
    universal = _parse_script_json(html, "__UNIVERSAL_DATA_FOR_REHYDRATION__")
    if universal:
        try:
            user_detail = universal.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
            user_info = user_detail.get("userInfo", {})
            profile_user = user_info.get("user", {}) or {}
            sec_uid = profile_user.get("secUid", "")
            
            # Primary: user.region
            region = _safe_region(profile_user.get("region"))
            if region:
                votes.append((region, "L1_UNIVERSAL_user_region", 95, f"user.region={region}"))
            
            # Secondary: stats.region (sometimes different)
            stats_region = _safe_region(user_info.get("stats", {}).get("region", ""))
            if stats_region and stats_region != region:
                votes.append((stats_region, "L1_UNIVERSAL_stats_region", 70, f"stats.region={stats_region}"))
                
        except Exception:
            pass
    
    # Parse SIGI_STATE fallback
    sigi = _parse_script_json(html, "SIGI_STATE")
    if sigi:
        try:
            users = sigi.get("UserModule", {}).get("users", {}) or {}
            for key, user in users.items():
                unique = str(user.get("uniqueId") or "").lower()
                if unique == username.lower() or key.lower() == username.lower():
                    region = _safe_region(user.get("region"))
                    if region:
                        votes.append((region, "L1_SIGI_user_region", 90, f"SIGI.users[{key}].region={region}"))
                    break
        except Exception:
            pass
    
    # Fallback: precise JSON regex (only structured data)
    if not votes:
        # Look for "region":"XX" near username
        pattern = rf'"uniqueId"\s*:\s*"{re.escape(username)}"[^}}]{{0,200}}"region"\s*:\s*"([A-Z]{{2}})"'
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            region = _safe_region(m.group(1))
            if region:
                votes.append((region, "L1_regex_near_username", 75, f"regex near uniqueId"))
    
    return html, profile_user, sec_uid, votes


# ==================== LAYER 2: TikTok Internal API (item_list) ====================
def _layer2_internal_api(sec_uid: str, username: str) -> List[Tuple[str, str, int, str]]:
    """Use TikTok's internal API to get user's video list with locationCreated."""
    votes: List[Tuple[str, str, int, str]] = []
    if not sec_uid:
        return votes
    
    api_url = (
        f"https://www.tiktok.com/api/post/item_list/?aid=1988&count=6"
        f"&secUid={sec_uid}&cursor=0&sourceType=8&appId=1233&region=US&language=en"
    )
    headers = {
        "User-Agent": random.choice(UA_POOL),
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://www.tiktok.com/@{username}",
        "Origin": "https://www.tiktok.com",
    }
    
    try:
        resp = requests.get(api_url, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json() or {}
            for item in (data.get("itemList") or [])[:6]:
                vid_id = str(item.get("id", "?"))
                loc = _safe_region(item.get("locationCreated"))
                if loc:
                    votes.append((loc, "L2_api_locationCreated", 92, f"video {vid_id}"))
                ar = _safe_region((item.get("author") or {}).get("region"))
                if ar:
                    votes.append((ar, "L2_api_author_region", 90, f"video {vid_id}"))
    except Exception:
        pass
    
    return votes


# ==================== LAYER 3: Video Page Signals ====================
def _layer3_video_pages(username: str, html_profile: str) -> List[Tuple[str, str, int, str]]:
    """Visit individual video pages to extract locationCreated."""
    votes: List[Tuple[str, str, int, str]] = []
    
    # Extract video IDs from profile page
    video_ids = list(dict.fromkeys(re.findall(r'/video/(\d{15,20})', html_profile)))[:3]
    
    for vid in video_ids:
        try:
            url = f"https://www.tiktok.com/@{username}/video/{vid}"
            resp = requests.get(url, headers=_get_headers(), timeout=20)
            if resp.status_code != 200:
                continue
            vhtml = resp.text
            
            # Parse UNIVERSAL_DATA
            universal = _parse_script_json(vhtml, "__UNIVERSAL_DATA_FOR_REHYDRATION__")
            if universal:
                scope = universal.get("__DEFAULT_SCOPE__", {})
                item_struct = scope.get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct", {})
                if item_struct:
                    loc = _safe_region(item_struct.get("locationCreated"))
                    if loc:
                        votes.append((loc, "L3_video_locationCreated", 88, vid))
                    ar = _safe_region((item_struct.get("author") or {}).get("region"))
                    if ar:
                        votes.append((ar, "L3_video_author_region", 87, vid))
            
            # Parse SIGI_STATE
            sigi = _parse_script_json(vhtml, "SIGI_STATE")
            if sigi:
                items = sigi.get("ItemModule", {}) or {}
                for _, item in list(items.items())[:2]:
                    loc = _safe_region(item.get("locationCreated"))
                    if loc:
                        votes.append((loc, "L3_sigi_locationCreated", 85, vid))
                    author = item.get("author")
                    if isinstance(author, dict):
                        ar = _safe_region(author.get("region"))
                        if ar:
                            votes.append((ar, "L3_sigi_author_region", 86, vid))
            
            time.sleep(0.5)
        except Exception:
            continue
    
    return votes


# ==================== LAYER 4: TikWM API ====================
def _layer4_tikwm(username: str) -> List[Tuple[str, str, int, str]]:
    """Query TikWM third-party API for user info."""
    votes: List[Tuple[str, str, int, str]] = []
    
    try:
        resp = requests.get(
            f"https://www.tikwm.com/api/user/info?unique_id={username}",
            headers={"User-Agent": random.choice(UA_POOL), "Accept": "application/json"},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json() or {}
            user_obj = (
                data.get("data", {}).get("user") or
                data.get("data", {}).get("user_info") or
                data.get("data") or {}
            )
            if isinstance(user_obj, dict):
                for key in ("region", "country", "create_region", "createRegion"):
                    code = _safe_region(user_obj.get(key))
                    if code:
                        votes.append((code, "L4_tikwm_user", 78, f"{key}={code}"))
                        break
    except Exception:
        pass
    
    # TikWM video list
    try:
        resp = requests.post(
            "https://www.tikwm.com/api/user/posts",
            data={"unique_id": username, "count": "5", "cursor": "0"},
            headers={"User-Agent": random.choice(UA_POOL), "Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json() or {}
            videos = data.get("data", {}).get("videos", []) or []
            for v in videos[:5]:
                loc = _safe_region(v.get("locationCreated") or v.get("location_created"))
                if loc:
                    votes.append((loc, "L4_tikwm_video_location", 82, str(v.get("video_id", "?"))))
                ar = _safe_region((v.get("author") or {}).get("region"))
                if ar:
                    votes.append((ar, "L4_tikwm_video_author", 80, str(v.get("video_id", "?"))))
    except Exception:
        pass
    
    return votes


# ==================== LAYER 5: Bio & Language Inference ====================
def _layer5_bio_inference(signature: str, language: str, nickname: str = "") -> Optional[Tuple[str, str, int, str]]:
    """Infer region from bio text, language code, and nickname."""
    text = (f"{signature} {nickname}").lower()
    language = (language or "").lower().strip()
    
    hints: Dict[str, List[str]] = {
        "SA": ["السعودية", "سعودي", "الرياض", "جدة", "مكة", "ksa", "saudi", "riyadh", "jeddah"],
        "EG": ["مصر", "مصري", "القاهرة", "الإسكندرية", "egypt", "cairo", "egyptian"],
        "AE": ["الإمارات", "دبي", "أبوظبي", "uae", "dubai", "emirates", "abudhabi"],
        "IQ": ["العراق", "عراقي", "بغداد", "البصرة", "iraq", "baghdad", "basra"],
        "JO": ["الأردن", "أردني", "عمّان", "jordan", "amman"],
        "KW": ["الكويت", "كويتي", "kuwait"],
        "QA": ["قطر", "قطري", "الدوحة", "qatar", "doha"],
        "SY": ["سوريا", "سوري", "دمشق", "syria", "damascus"],
        "LB": ["لبنان", "لبناني", "بيروت", "lebanon", "beirut"],
        "MA": ["المغرب", "مغربي", "الرباط", "morocco", "rabat"],
        "DZ": ["الجزائر", "جزائري", "algeria"],
        "TN": ["تونس", "تونسي", "tunisia"],
        "TR": ["تركيا", "istanbul", "ankara", "turkey"],
        "GB": ["uk", "england", "london", "scotland", "wales", "britain"],
        "US": ["usa", "america", "new york", "california", "texas", "florida"],
        "FR": ["france", "paris", "française"],
        "DE": ["germany", "deutschland", "berlin"],
        "IN": ["india", "mumbai", "delhi", "bangalore", "hindi"],
        "PK": ["pakistan", "karachi", "lahore", "islamabad"],
        "ID": ["indonesia", "jakarta", "bandung"],
        "MY": ["malaysia", "kuala lumpur", "kl malaysia"],
        "PH": ["philippines", "manila", "pilipinas"],
        "NG": ["nigeria", "lagos", "abuja"],
        "RU": ["russia", "moscow", "русский"],
        "JP": ["japan", "tokyo", "osaka", "japanese"],
        "KR": ["korea", "seoul", "korean", "한국"],
        "CN": ["china", "beijing", "shanghai", "chinese"],
        "BR": ["brazil", "brasil", "são paulo"],
        "SD": ["السودان", "سوداني", "الخرطوم", "sudan", "khartoum"],
        "SO": ["الصومال", "صومالي", "مقديشو", "somalia"],
        "YE": ["اليمن", "يمني", "صنعاء", "yemen", "sanaa"],
        "LY": ["ليبيا", "ليبي", "طرابلس", "libya", "tripoli"],
    }
    
    best_code = ""
    best_score = 0
    for code, terms in hints.items():
        score = sum(1 for t in terms if t in text)
        if score > best_score:
            best_code, best_score = code, score
    
    if best_code and best_score >= 1:
        return (best_code, "L5_bio_hints", 45 + min(best_score * 5, 25), f"text_match={best_score}")
    
    lang_map = {
        "tr": "TR", "ja": "JP", "ko": "KR", "th": "TH", "vi": "VN",
        "id": "ID", "hi": "IN", "ur": "PK", "ms": "MY", "tl": "PH",
        "ru": "RU", "de": "DE", "fr": "FR", "pt": "BR", "zh": "CN",
    }
    if language in lang_map:
        return (lang_map[language], "L5_language_hint", 40, f"language={language}")
    
    return None


# ==================== MAIN FUNCTION ====================
def fetch_region_from_video_page(username: str) -> Dict[str, Any]:
    """
    Multi-layer TikTok region detection engine v13.
    Combines 5 independent signal sources with weighted voting.
    """
    result = {"region": "", "source": "unknown", "confidence": 0, "method": "", "evidence": [], "votes": []}
    if not username:
        return result
    username = username.strip().lstrip("@")
    
    all_votes: List[Tuple[str, str, int, str]] = []
    
    # Layer 1: Profile page scrape (highest priority)
    html, profile_user, sec_uid, l1_votes = _layer1_profile_page(username)
    all_votes.extend(l1_votes)
    
    # Layer 2: Internal API (requires sec_uid from L1)
    if sec_uid:
        all_votes.extend(_layer2_internal_api(sec_uid, username))
    
    # Layer 3: Video pages (only if we got profile HTML)
    if html:
        all_votes.extend(_layer3_video_pages(username, html))
    
    # Layer 4: TikWM third-party API (always run)
    all_votes.extend(_layer4_tikwm(username))
    
    # Layer 5: Bio inference (low confidence fallback)
    bio_vote = _layer5_bio_inference(
        profile_user.get("signature", ""),
        profile_user.get("language", ""),
        profile_user.get("nickname", ""),
    )
    if bio_vote:
        all_votes.append(bio_vote)
    
    # Compute final result via weighted voting
    final = _vote(all_votes)
    
    if final["region"] in TIKTOK_REGION_MAP:
        flag, ar = TIKTOK_REGION_MAP[final["region"]]
        final["region_flag"] = flag
        final["region_name_ar"] = ar
    else:
        final["region_flag"] = ""
        final["region_name_ar"] = ""
    
    final["debug_signal_count"] = len(all_votes)
    final["debug_layers"] = {
        "L1_profile": len(l1_votes),
        "L2_api": len([v for v in all_votes if v[1].startswith("L2")]),
        "L3_video": len([v for v in all_votes if v[1].startswith("L3")]),
        "L4_tikwm": len([v for v in all_votes if v[1].startswith("L4")]),
        "L5_bio": 1 if bio_vote else 0,
    }
    
    return final
