from __future__ import annotations
import json, re, time, random
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple
import requests

TIKTOK_REGION_MAP = {
    "US":("🇺🇸","الولايات المتحدة"),"GB":("🇬🇧","المملكة المتحدة"),
    "SA":("🇸🇦","السعودية"),"AE":("🇦🇪","الإمارات"),"EG":("🇪🇬","مصر"),
    "IQ":("🇮🇶","العراق"),"JO":("🇯🇴","الأردن"),"KW":("🇰🇼","الكويت"),
    "QA":("🇶🇦","قطر"),"BH":("🇧🇭","البحرين"),"OM":("🇴🇲","عُمان"),
    "SY":("🇸🇾","سوريا"),"LB":("🇱🇧","لبنان"),"MA":("🇲🇦","المغرب"),
    "TN":("🇹🇳","تونس"),"DZ":("🇩🇿","الجزائر"),"LY":("🇱🇾","ليبيا"),
    "YE":("🇾🇪","اليمن"),"SD":("🇸🇩","السودان"),"SO":("🇸🇴","الصومال"),
    "TR":("🇹🇷","تركيا"),"IN":("🇮🇳","الهند"),"PK":("🇵🇰","باكستان"),
    "ID":("🇮🇩","إندونيسيا"),"PH":("🇵🇭","الفلبين"),"TH":("🇹🇭","تايلاند"),
    "VN":("🇻🇳","فيتنام"),"MY":("🇲🇾","ماليزيا"),"SG":("🇸🇬","سنغافورة"),
    "JP":("🇯🇵","اليابان"),"KR":("🇰🇷","كوريا الجنوبية"),"CN":("🇨🇳","الصين"),
    "RU":("🇷🇺","روسيا"),"DE":("🇩🇪","ألمانيا"),"FR":("🇫🇷","فرنسا"),
    "IT":("🇮🇹","إيطاليا"),"ES":("🇪🇸","إسبانيا"),"BR":("🇧🇷","البرازيل"),
    "MX":("🇲🇽","المكسيك"),"CA":("🇨🇦","كندا"),"AU":("🇦🇺","أستراليا"),
    "NG":("🇳🇬","نيجيريا"),"ZA":("🇿🇦","جنوب أفريقيا"),"NL":("🇳🇱","هولندا"),
    "SE":("🇸🇪","السويد"),"NO":("🇳🇴","النرويج"),"PL":("🇵🇱","بولندا"),
    "UA":("🇺🇦","أوكرانيا"),"GR":("🇬🇷","اليونان"),"PT":("🇵🇹","البرتغال"),
    "BE":("🇧🇪","بلجيكا"),"AT":("🇦🇹","النمسا"),"CH":("🇨🇭","سويسرا"),
    "IL":("🇮🇱","إسرائيل"),"IR":("🇮🇷","إيران"),"BD":("🇧🇩","بنغلاديش"),
    "MM":("🇲🇲","ميانمار"),"NP":("🇳🇵","نيبال"),"LK":("🇱🇰","سريلانكا"),
    "ET":("🇪🇹","إثيوبيا"),"GH":("🇬🇭","غانا"),"KE":("🇰🇪","كينيا"),
    "TZ":("🇹🇿","تنزانيا"),"CM":("🇨🇲","الكاميرون"),"DK":("🇩🇰","الدنمارك"),
    "FI":("🇫🇮","فنلندا"),"RO":("🇷🇴","رومانيا"),"HU":("🇭🇺","المجر"),
    "CZ":("🇨🇿","التشيك"),"SK":("🇸🇰","سلوفاكيا"),"BG":("🇧🇬","بلغاريا"),
    "HR":("🇭🇷","كرواتيا"),"RS":("🇷🇸","صربيا"),"KZ":("🇰🇿","كازاخستان"),
    "TW":("🇹🇼","تايوان"),"HK":("🇭🇰","هونغ كونغ"),"MO":("🇲🇴","ماكاو"),
    "CL":("🇨🇱","تشيلي"),"PE":("🇵🇪","بيرو"),"AR":("🇦🇷","الأرجنتين"),
    "CO":("🇨🇴","كولومبيا"),"VE":("🇻🇪","فنزويلا"),"EC":("🇪🇨","الإكوادور"),
    "NZ":("🇳🇿","نيوزيلندا"),"IE":("🇮🇪","أيرلندا"),"MK":("🇲🇰","مقدونيا"),
    "AF":("🇦🇫","أفغانستان"),"UZ":("🇺🇿","أوزبكستان"),"AZ":("🇦🇿","أذربيجان"),
    "GE":("🇬🇪","جورجيا"),"AM":("🇦🇲","أرمينيا"),
}

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.52 Mobile Safari/537.36",
]

def _hdr(mobile=False):
    ua = _UA_POOL[2] if mobile else random.choice(_UA_POOL[:2])
    return {
        "User-Agent": ua,
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Upgrade-Insecure-Requests": "1",
    }

def _safe(code):
    if not code or not isinstance(code, str): return ""
    c = code.strip().upper()
    return c if c in TIKTOK_REGION_MAP else ""

def _parse_json_script(html, script_id):
    m = re.search(rf'<script id="{re.escape(script_id)}"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m: return None
    try: return json.loads(m.group(1))
    except: return None

def _vote(votes):
    if not votes:
        return {"region":"","source":"none","confidence":0,"method":"","evidence":[],"votes":[]}
    scores = Counter()
    evid = {}
    for country, src, w, detail in votes:
        scores[country] += w
        evid.setdefault(country,[]).append(f"{src}: {detail}")
    best, bscore = scores.most_common(1)[0]
    second = scores.most_common(2)[1][1] if len(scores)>1 else 0
    conf = max(25, min(97, int(bscore - second*0.3)))
    return {
        "region": best,
        "source": "ensemble_v14" if len(votes)>1 else votes[0][1],
        "confidence": conf,
        "method": "ensemble_v14",
        "evidence": evid.get(best,[]),
        "votes": [{"country":c,"source":s,"weight":w,"detail":d} for c,s,w,d in votes],
    }

# ── Layer 1: Profile Page (new structure 2025) ──
def _L1_profile(username):
    votes, profile_user, sec_uid, html = [], {}, "", ""
    for mobile in [False, True]:
        try:
            r = requests.get(f"https://www.tiktok.com/@{username}", headers=_hdr(mobile), timeout=22, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 5000:
                html = r.text
                break
            time.sleep(1)
        except: continue
    if not html: return votes, profile_user, sec_uid, html

    uni = _parse_json_script(html, "__UNIVERSAL_DATA_FOR_REHYDRATION__")
    if uni:
        scope = uni.get("__DEFAULT_SCOPE__", {})
        # New structure 2025
        user_detail = scope.get("webapp.user-detail", {})
        user_info = user_detail.get("userInfo", {})
        profile_user = user_info.get("user", {}) or {}
        sec_uid = profile_user.get("secUid", "")
        
        # Try region in user object
        region = _safe(profile_user.get("region"))
        if region:
            votes.append((region, "L1_profile_user_region", 94, f"user.region"))
        
        # Try stats object
        stats = user_info.get("stats", {})
        sr = _safe(stats.get("region",""))
        if sr: votes.append((sr,"L1_profile_stats_region",72,f"stats.region"))
        
        # Try reflow shareUser structure (if present)
        share_user = scope.get("webapp.reflow.global.shareUser", {})
        u2 = share_user.get("user", {})
        if isinstance(u2, dict):
            r2 = _safe(u2.get("region",""))
            if r2: votes.append((r2,"L1_shareUser_region",85,f"shareUser.user.region"))
    
    return votes, profile_user, sec_uid, html

# ── Layer 2: Video Pages with NEW reflow structure ──
def _L2_video_pages(username, html_profile):
    votes = []
    # Extract video IDs — from href patterns and data-video-id
    vids = list(dict.fromkeys(
        re.findall(r'(?:/video/|"id"\s*:\s*")(\d{15,20})', html_profile)
    ))[:4]
    
    if not vids:
        # Try to get from profile's JSON
        uni = _parse_json_script(html_profile, "__UNIVERSAL_DATA_FOR_REHYDRATION__")
        if uni:
            scope = uni.get("__DEFAULT_SCOPE__",{})
            # Try itemList in any key
            raw = json.dumps(scope)
            vids = list(dict.fromkeys(re.findall(r'"id"\s*:\s*"(\d{15,20})"', raw)))[:4]
    
    for vid in vids[:3]:
        try:
            url = f"https://www.tiktok.com/@{username}/video/{vid}"
            r = requests.get(url, headers=_hdr(mobile=True), timeout=20)
            if r.status_code != 200: continue
            
            uni = _parse_json_script(r.text, "__UNIVERSAL_DATA_FOR_REHYDRATION__")
            if not uni: continue
            scope = uni.get("__DEFAULT_SCOPE__",{})
            
            # NEW structure: webapp.reflow.video.detail (2025)
            reflow = scope.get("webapp.reflow.video.detail", {})
            item_struct = reflow.get("itemInfo", {}).get("itemStruct", {})
            if item_struct:
                lc = _safe(item_struct.get("locationCreated",""))
                if lc: votes.append((lc,"L2_reflow_locationCreated",92,vid))
                author = item_struct.get("author",{})
                if isinstance(author,dict):
                    ar = _safe(author.get("region",""))
                    if ar: votes.append((ar,"L2_reflow_author_region",90,vid))
            
            # OLD structure: webapp.video-detail (fallback)
            old_struct = scope.get("webapp.video-detail",{}).get("itemInfo",{}).get("itemStruct",{})
            if old_struct:
                lc = _safe(old_struct.get("locationCreated",""))
                if lc: votes.append((lc,"L2_old_locationCreated",88,vid))
                author = old_struct.get("author",{})
                if isinstance(author,dict):
                    ar = _safe(author.get("region",""))
                    if ar: votes.append((ar,"L2_old_author_region",87,vid))
            
            # Regex fallback on raw video page JSON
            raw = r.text
            lc_matches = re.findall(r'"locationCreated"\s*:\s*"([A-Z]{2})"', raw)
            for lc in lc_matches[:3]:
                code = _safe(lc)
                if code: votes.append((code,"L2_regex_locationCreated",82,vid))
            
            ar_matches = re.findall(r'"region"\s*:\s*"([A-Z]{2})"', raw)
            # Only use the first few matches (to avoid UI text)
            for ar in ar_matches[:2]:
                code = _safe(ar)
                if code: votes.append((code,"L2_regex_region",78,vid))
            
            time.sleep(0.6)
        except: continue
    
    return votes

# ── Layer 3: Internal TikTok API ──
def _L3_internal_api(sec_uid, username):
    votes = []
    if not sec_uid: return votes
    try:
        url = (f"https://www.tiktok.com/api/post/item_list/?aid=1988&count=6"
               f"&secUid={sec_uid}&cursor=0&sourceType=8&appId=1233&region=US&language=en")
        r = requests.get(url, headers={
            "User-Agent": random.choice(_UA_POOL),
            "Accept":"application/json, */*",
            "Referer":f"https://www.tiktok.com/@{username}",
            "Origin":"https://www.tiktok.com",
        }, timeout=18)
        if r.status_code == 200:
            data = r.json() or {}
            for item in (data.get("itemList") or [])[:6]:
                vid = str(item.get("id","?"))
                lc = _safe(item.get("locationCreated",""))
                if lc: votes.append((lc,"L3_api_locationCreated",93,vid))
                ar = _safe((item.get("author") or {}).get("region",""))
                if ar: votes.append((ar,"L3_api_author_region",91,vid))
    except: pass
    return votes

# ── Layer 4: TikWM API ──
def _L4_tikwm(username):
    votes = []
    try:
        r = requests.post(
            "https://www.tikwm.com/api/user/posts",
            data={"unique_id": username, "count":"5","cursor":"0"},
            headers={"User-Agent":random.choice(_UA_POOL),"Content-Type":"application/x-www-form-urlencoded"},
            timeout=15
        )
        if r.status_code == 200:
            data = r.json() or {}
            for v in (data.get("data",{}).get("videos",[]) or [])[:5]:
                lc = _safe(v.get("locationCreated","") or v.get("location_created",""))
                if lc: votes.append((lc,"L4_tikwm_locationCreated",85,str(v.get("video_id","?"))))
                ar = _safe((v.get("author") or {}).get("region",""))
                if ar: votes.append((ar,"L4_tikwm_author_region",83,str(v.get("video_id","?"))))
    except: pass
    
    # User info endpoint
    try:
        r = requests.get(
            f"https://www.tikwm.com/api/user/info?unique_id={username}",
            headers={"User-Agent":random.choice(_UA_POOL),"Accept":"application/json"},
            timeout=12
        )
        if r.status_code == 200:
            data = r.json() or {}
            user_obj = data.get("data",{}).get("user") or data.get("data",{}) or {}
            if isinstance(user_obj, dict):
                for k in ("region","country","createRegion","create_region"):
                    code = _safe(user_obj.get(k,""))
                    if code:
                        votes.append((code,"L4_tikwm_user_region",78,f"field={k}"))
                        break
    except: pass
    return votes

# ── Layer 5: Bio + Language inference ──
def _L5_bio(signature, language, nickname=""):
    text = f"{signature or ''} {nickname or ''}".lower()
    lang = (language or "").lower().strip()
    HINTS = {
        "SA":["السعودية","سعودي","الرياض","جدة","مكة","ksa","saudi","riyadh","jeddah"],
        "EG":["مصر","مصري","القاهرة","الإسكندرية","egypt","cairo","egyptian"],
        "AE":["الإمارات","دبي","أبوظبي","uae","dubai","emirates","abu dhabi"],
        "IQ":["العراق","عراقي","بغداد","البصرة","iraq","baghdad","basra"],
        "JO":["الأردن","أردني","عمّان","jordan","amman"],
        "KW":["الكويت","كويتي","kuwait"],"QA":["قطر","قطري","الدوحة","qatar","doha"],
        "SY":["سوريا","سوري","دمشق","syria","damascus"],
        "LB":["لبنان","لبناني","بيروت","lebanon","beirut"],
        "MA":["المغرب","مغربي","الرباط","morocco","rabat"],
        "DZ":["الجزائر","جزائري","algeria"],"TN":["تونس","تونسي","tunisia"],
        "TR":["تركيا","istanbul","ankara","turkey"],
        "GB":["uk","england","london","britain","scotland"],
        "US":["usa","america","new york","california","texas","florida"],
        "FR":["france","paris","française"],"DE":["germany","berlin","deutschland"],
        "IN":["india","mumbai","delhi","bangalore"],"PK":["pakistan","karachi","lahore"],
        "ID":["indonesia","jakarta"],"MY":["malaysia","kuala lumpur"],
        "PH":["philippines","manila"],"NG":["nigeria","lagos","abuja"],
        "RU":["russia","moscow","русский"],"JP":["japan","tokyo","osaka"],
        "KR":["korea","seoul","korean","한국"],"CN":["china","beijing","shanghai"],
        "BR":["brazil","brasil","são paulo"],"SD":["السودان","سوداني","الخرطوم","sudan"],
        "SO":["الصومال","صومالي","مقديشو","somalia"],"YE":["اليمن","يمني","صنعاء","yemen"],
        "LY":["ليبيا","ليبي","طرابلس","libya"],"IT":["italy","roma","milan","italian"],
    }
    best_code, best_score = "", 0
    for code, terms in HINTS.items():
        score = sum(1 for t in terms if t in text)
        if score > best_score: best_code, best_score = code, score
    if best_code and best_score >= 1:
        return (best_code, "L5_bio_hints", 48+min(best_score*5,22), f"matches={best_score}")
    lang_map = {"tr":"TR","ja":"JP","ko":"KR","th":"TH","vi":"VN","id":"ID",
                "hi":"IN","ur":"PK","ms":"MY","tl":"PH","ru":"RU","de":"DE",
                "fr":"FR","pt":"BR","zh":"CN","ar":"SA"}
    if lang in lang_map:
        return (lang_map[lang], "L5_language_hint", 38, f"lang={lang}")
    return None

# ── MAIN ──
def fetch_region_from_video_page(username: str) -> Dict[str, Any]:
    """محرك كشف دولة TikTok v14 - 5 طبقات مستقلة + تصويت موزون"""
    empty = {"region":"","source":"none","confidence":0,"method":"","evidence":[],"votes":[],
             "region_flag":"","region_name_ar":"","debug_layers":{}}
    if not username: return empty
    username = username.strip().lstrip("@")
    
    all_votes: List[Tuple[str,str,int,str]] = []
    
    # L1: Profile page
    l1v, profile_user, sec_uid, html = _L1_profile(username)
    all_votes.extend(l1v)
    
    # L2: Video pages (critical - has locationCreated)
    l2v = _L2_video_pages(username, html)
    all_votes.extend(l2v)
    
    # L3: Internal API
    l3v = _L3_internal_api(sec_uid, username)
    all_votes.extend(l3v)
    
    # L4: TikWM
    l4v = _L4_tikwm(username)
    all_votes.extend(l4v)
    
    # L5: Bio inference
    bio = _L5_bio(profile_user.get("signature",""), profile_user.get("language",""), profile_user.get("nickname",""))
    if bio: all_votes.append(bio)
    
    final = _vote(all_votes)
    if final["region"] in TIKTOK_REGION_MAP:
        flag, name = TIKTOK_REGION_MAP[final["region"]]
        final["region_flag"] = flag
        final["region_name_ar"] = name
    else:
        final["region_flag"] = ""
        final["region_name_ar"] = ""
    
    final["debug_signal_count"] = len(all_votes)
    final["debug_layers"] = {
        "L1_profile": len(l1v),
        "L2_video_pages": len(l2v),
        "L3_internal_api": len(l3v),
        "L4_tikwm": len(l4v),
        "L5_bio": 1 if bio else 0,
    }
    return final
