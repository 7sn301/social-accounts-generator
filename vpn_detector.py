"""
🛡️ Advanced VPN Detector & Precise User Location  v1.0
=========================================================
يجمع 8 إشارات مستقلة من حساب X لتحديد:
  • هل الحساب يستخدم VPN؟  (نسبة قطعية مع أدلة)
  • أين يقع المستخدم فعلياً؟  (دولة / مدينة / حي)

المصادر (كلها مجانية بدون cookies):
  S1. fxtwitter Profile location field          (الموقع المعلن)
  S2. Geocoding للموقع المعلن                    (تحويل لإحداثيات)
  S3. Twitter Syndication API last 20 tweets    (لغة + أوقات)
  S4. تحليل المنطقة الزمنية من أوقات النشر     (← الدولة الفعلية)
  S5. Gemini Vision على آخر صورة منشورة         (← الموقع الفعلي)
  S6. EXIF GPS من الصور (نادر لكنه قاطع)
  S7. تحليل لهجة/لغة التغريدات                  (إشارة ضعيفة)
  S8. mentions / hashtags جغرافية                (إشارة داعمة)

→ تصويت موزون → نسبة VPN قطعية + موقع فعلي محدّد
"""

from __future__ import annotations
import os, re, json, time, math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter
from urllib.parse import quote_plus

import requests

# Reuse our existing modules
try:
    from twitter_osint import (
        geocode_place, reverse_geocode as osm_reverse,
        analyze_timezone_from_tweets, build_map_verification_links,
        haversine_km,
    )
    from geo_engine import (
        analyze_image_full,
        flag as ge_flag, country_ar as ge_country_ar, ISO_TO_AR,
    )
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    DEPS_ERROR = str(e)

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0")
HTTP_TIMEOUT = 25

# ─────────────────────── Country / Timezone tables ───────────────────
# Map ISO country code → main UTC offset (DST ignored — heuristic)
COUNTRY_TO_TZ_OFFSET = {
    "GB": 0,  "PT": 0,  "IE": 0,  "IS": 0,
    "DE": 1,  "FR": 1,  "ES": 1,  "IT": 1,  "NL": 1,  "BE": 1, "CH": 1,
    "AT": 1,  "SE": 1,  "NO": 1,  "DK": 1,  "PL": 1,  "CZ": 1, "HU": 1,
    "TN": 1,  "DZ": 1,  "MA": 1,
    "EG": 2,  "LB": 2,  "SY": 2,  "JO": 2,  "PS": 2,  "RO": 2, "BG": 2,
    "GR": 2,  "ZA": 2,  "FI": 2,  "TR": 3,
    "SA": 3,  "KW": 3,  "QA": 3,  "BH": 3,  "IQ": 3,  "YE": 3, "RU": 3,
    "IR": 3,  # 3.5 actually but close enough
    "AE": 4,  "OM": 4,  "AZ": 4,  "GE": 4,
    "PK": 5,  "IN": 5,  "AF": 4,
    "BD": 6,  "TH": 7,  "VN": 7,  "ID": 7,
    "CN": 8,  "MY": 8,  "SG": 8,  "PH": 8,  "AU": 10,
    "JP": 9,  "KR": 9,
    "US": -5, "CA": -5,  # Eastern
    "MX": -6, "BR": -3,  "AR": -3,
}

# Reverse map: offset → likely ISO codes
def offsets_to_isos(off: int) -> List[str]:
    return [iso for iso, o in COUNTRY_TO_TZ_OFFSET.items() if o == off]


# ════════════════════════════════════════════════════════════════════
# S1 + S3:  Fetch profile + recent tweets (no auth)
# ════════════════════════════════════════════════════════════════════
def fetch_user_profile(username: str) -> Optional[Dict[str, Any]]:
    """Get profile via fxtwitter (no auth needed)."""
    try:
        r = requests.get(
            f"https://api.fxtwitter.com/{username}",
            headers={"User-Agent": USER_AGENT},
            timeout=HTTP_TIMEOUT,
        )
        if r.status_code == 200:
            return (r.json() or {}).get("user")
    except Exception:
        pass
    return None


def fetch_recent_tweet_timestamps(username: str, max_count: int = 30
                                  ) -> List[Dict[str, Any]]:
    """
    Get recent tweets with timestamps using publicly accessible methods.

    Strategy:
      1. Try Nitter mirrors RSS feed (no auth, includes pubDate).
      2. Fallback to syndication.twimg.com profile timeline.
      3. Return list of {timestamp_utc, text, lang, media_urls}.
    """
    out: List[Dict[str, Any]] = []

    # ── Try 1: Nitter RSS (multiple mirrors) ────────────────────────
    nitter_hosts = [
        "nitter.privacydev.net", "nitter.poast.org",
        "nitter.tiekoetter.com", "nitter.net",
    ]
    for host in nitter_hosts:
        try:
            r = requests.get(
                f"https://{host}/{username}/rss",
                headers={"User-Agent": USER_AGENT},
                timeout=10,
            )
            if r.status_code != 200 or len(r.text) < 200:
                continue
            # Parse <item> blocks
            items = re.findall(r"<item>(.*?)</item>", r.text, re.S)
            for it in items[:max_count]:
                pub = re.search(r"<pubDate>(.*?)</pubDate>", it)
                desc = re.search(r"<description>(.*?)</description>", it, re.S)
                link = re.search(r"<link>(.*?)</link>", it)
                imgs = re.findall(
                    r'<img[^>]+src="([^"]+)"', desc.group(1) if desc else "")
                if pub:
                    try:
                        dt = datetime.strptime(
                            pub.group(1).strip(),
                            "%a, %d %b %Y %H:%M:%S %Z")
                        dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        try:
                            dt = datetime.strptime(
                                pub.group(1).strip(),
                                "%a, %d %b %Y %H:%M:%S %z")
                            dt = dt.astimezone(timezone.utc)
                        except Exception:
                            continue
                    out.append({
                        "timestamp_utc": dt,
                        "text": re.sub(r"<[^>]+>", "",
                                       desc.group(1) if desc else "")[:280],
                        "url": link.group(1).strip() if link else None,
                        "media_urls": imgs[:4],
                        "source": f"nitter/{host}",
                    })
            if out:
                return out
        except Exception:
            continue

    # ── Try 2: syndication.twimg.com (fallback) ─────────────────────
    try:
        r = requests.get(
            "https://syndication.twimg.com/srv/timeline-profile/screen-name/"
            + quote_plus(username),
            headers={"User-Agent": USER_AGENT}, timeout=HTTP_TIMEOUT,
        )
        if r.status_code == 200:
            # Look for embedded JSON
            m = re.search(r'<script[^>]+type="application/json"[^>]*>'
                          r'(.*?)</script>', r.text, re.S)
            if m:
                data = json.loads(m.group(1))
                tweets = (data.get("props", {}).get("pageProps", {})
                              .get("timeline", {}).get("entries", []))
                for t in tweets[:max_count]:
                    cd = t.get("content", {}).get("tweet")
                    if not cd: continue
                    ts = cd.get("created_at")
                    if ts:
                        try:
                            dt = datetime.strptime(
                                ts, "%a %b %d %H:%M:%S %z %Y"
                            ).astimezone(timezone.utc)
                            out.append({
                                "timestamp_utc": dt,
                                "text": cd.get("full_text", "")[:280],
                                "url": cd.get("permalink"),
                                "media_urls": [
                                    p.get("media_url_https")
                                    for p in cd.get("mediaDetails", []) or []
                                ][:4],
                                "lang": cd.get("lang"),
                                "source": "syndication",
                            })
                        except Exception:
                            pass
    except Exception:
        pass
    return out


# ════════════════════════════════════════════════════════════════════
# S7: Language / dialect signal
# ════════════════════════════════════════════════════════════════════
ARAB_DIALECT_KEYWORDS = {
    "SA": ["والله", "تو", "وش", "بكره", "حنا", "ابي", "هلابك"],
    "EG": ["ازاي", "كده", "إيه", "كويس", "خالص", "يعني"],
    "IQ": ["شلون", "هواية", "اكو", "ماكو", "هسة", "بعد", "لك"],
    "MA": ["بزاف", "دابا", "بصح", "واخا", "كيداير"],
    "LB": ["كيفك", "شو", "هلق", "متل"],
    "GULF": ["شخبارك", "تو", "زين", "عيل", "بس", "حلو"],
}

def detect_dialect(texts: List[str]) -> Dict[str, Any]:
    """Score Arabic dialect by keyword frequency."""
    if not texts:
        return {"dominant": None, "scores": {}}
    joined = " ".join(texts).lower()
    scores: Dict[str, int] = {}
    for dialect, kws in ARAB_DIALECT_KEYWORDS.items():
        scores[dialect] = sum(joined.count(kw) for kw in kws)
    nonzero = {k: v for k, v in scores.items() if v > 0}
    dominant = max(nonzero, key=nonzero.get) if nonzero else None
    return {"dominant": dominant, "scores": scores}


# ════════════════════════════════════════════════════════════════════
# S8: Geographic mentions in hashtags / text
# ════════════════════════════════════════════════════════════════════
GEO_KEYWORDS_AR = {
    "SA": ["السعودية", "الرياض", "جدة", "مكة", "المدينة", "الدمام", "الخبر",
           "أبها", "الطائف", "تبوك", "حائل"],
    "AE": ["الإمارات", "دبي", "أبوظبي", "الشارقة", "عجمان", "الفجيرة"],
    "EG": ["مصر", "القاهرة", "الإسكندرية", "الجيزة", "الأقصر", "أسوان"],
    "IQ": ["العراق", "بغداد", "البصرة", "الموصل", "أربيل", "كركوك", "النجف"],
    "QA": ["قطر", "الدوحة"],
    "KW": ["الكويت"],
    "BH": ["البحرين", "المنامة"],
    "OM": ["عُمان", "مسقط", "صلالة"],
    "JO": ["الأردن", "عمّان", "الزرقاء"],
    "SY": ["سوريا", "دمشق", "حلب"],
    "LB": ["لبنان", "بيروت", "صيدا"],
    "PS": ["فلسطين", "غزة", "القدس", "الضفة"],
    "YE": ["اليمن", "صنعاء", "عدن"],
    "MA": ["المغرب", "الرباط", "الدار البيضاء", "مراكش"],
    "TN": ["تونس"],
    "DZ": ["الجزائر"],
    "LY": ["ليبيا", "طرابلس", "بنغازي"],
    "SD": ["السودان", "الخرطوم"],
    "TR": ["تركيا", "اسطنبول", "أنقرة"],
    "IR": ["إيران", "طهران"],
}


def score_geo_mentions(texts: List[str]) -> Dict[str, int]:
    if not texts: return {}
    joined = " ".join(texts)
    scores = {}
    for iso, kws in GEO_KEYWORDS_AR.items():
        c = sum(joined.count(kw) for kw in kws)
        if c > 0: scores[iso] = c
    return dict(sorted(scores.items(), key=lambda x: -x[1]))


# ════════════════════════════════════════════════════════════════════
# Main investigator
# ════════════════════════════════════════════════════════════════════
def investigate(username: str,
                gemini_api_key: Optional[str] = None,
                analyze_images: bool = True,
                max_images: int = 2,
                ) -> Dict[str, Any]:
    """
    Full multi-source investigation of an X account.

    Returns a dict with:
      • profile             — basic info from fxtwitter
      • declared_location   — string + geocoded coordinates + ISO
      • timezone_analysis   — UTC offset inferred from posting hours
      • image_locations     — AI-extracted location from recent images
      • geo_mentions        — country mentions in tweets
      • dialect             — Arabic dialect detected
      • final_verdict       — VPN risk score 0-100 + actual location
    """
    if not DEPS_OK:
        return {"error": f"missing dependencies: {DEPS_ERROR}"}

    username = username.strip().lstrip("@")
    report: Dict[str, Any] = {"username": username,
                              "timestamp_utc": datetime.now(timezone.utc).isoformat()}

    # ── S1: Profile ──────────────────────────────────────────────────
    user = fetch_user_profile(username)
    if not user:
        return {"error": "account not found or protected", **report}
    report["profile"] = {
        "name":         user.get("name"),
        "screen_name":  user.get("screen_name"),
        "id":           user.get("id"),
        "joined":       user.get("joined"),
        "followers":    user.get("followers"),
        "following":    user.get("following"),
        "location_raw": user.get("location"),
        "description":  user.get("description"),
        "avatar_url":   user.get("avatar_url"),
        "verified":     user.get("verification") not in (None, "", "none"),
    }

    # ── S2: Geocode declared location ───────────────────────────────
    declared_iso = None
    declared_coords = None
    declared_geocoded = None
    if user.get("location"):
        g = geocode_place(user["location"])
        if g:
            declared_iso = g.get("country_code")
            declared_coords = (g["lat"], g["lon"])
            declared_geocoded = g
    report["declared_location"] = {
        "raw":      user.get("location"),
        "iso":      declared_iso,
        "coords":   declared_coords,
        "geocoded": declared_geocoded,
        "flag":     ge_flag(declared_iso) if declared_iso else "🏳️",
    }

    # ── S3: Recent tweets ────────────────────────────────────────────
    tweets = fetch_recent_tweet_timestamps(username, max_count=30)
    report["tweets_fetched"] = len(tweets)

    # ── S4: Timezone inference ──────────────────────────────────────
    tz_analysis = None
    if tweets:
        timestamps = [t["timestamp_utc"] for t in tweets if t.get("timestamp_utc")]
        if len(timestamps) >= 5:
            tz_analysis = analyze_timezone_from_tweets(timestamps)
    report["timezone_analysis"] = tz_analysis

    # ── S5: Image analysis (Gemini Vision) ──────────────────────────
    image_results: List[Dict[str, Any]] = []
    if analyze_images and gemini_api_key and tweets:
        # Pick latest images across tweets
        candidate_imgs = []
        for t in tweets:
            for u in (t.get("media_urls") or []):
                if u and u not in candidate_imgs:
                    candidate_imgs.append(u)
                if len(candidate_imgs) >= max_images: break
            if len(candidate_imgs) >= max_images: break

        for url in candidate_imgs:
            try:
                ar = analyze_image_full(
                    image_url=url,
                    gemini_api_key=gemini_api_key,
                    account_iso=declared_iso,
                    tweet_lang="ar",
                )
                tri = ar.get("triangulation", {}) if ar else {}
                image_results.append({
                    "url": url,
                    "country_iso": tri.get("final_iso"),
                    "city":        tri.get("city"),
                    "lat":         tri.get("lat"),
                    "lon":         tri.get("lon"),
                    "confidence":  tri.get("confidence", 0),
                    "method":      tri.get("method"),
                })
            except Exception as e:
                image_results.append({"url": url, "error": str(e)})
    report["image_locations"] = image_results

    # ── S7+S8: Linguistic + geo-mention analysis ────────────────────
    texts = [t.get("text", "") for t in tweets]
    dialect_full = detect_dialect(texts)
    report["dialect"]          = dialect_full["dominant"]   # str or None
    report["dialect_scores"]   = dialect_full["scores"]
    report["geo_mentions"]     = score_geo_mentions(texts)

    # ════════════════════════════════════════════════════════════════
    # FINAL VERDICT — combine all signals into one decisive answer
    # ════════════════════════════════════════════════════════════════
    verdict = build_final_verdict(report)
    report["final_verdict"] = verdict
    return report


def build_final_verdict(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Weighted multi-signal voting for:
      • Real country (where the user actually is)
      • VPN probability (0-100)
      • Confidence in the diagnosis
    """
    declared_iso  = (report.get("declared_location") or {}).get("iso")
    tz            = report.get("timezone_analysis") or {}
    images        = report.get("image_locations") or []
    geo_mentions  = report.get("geo_mentions") or {}
    dialect       = report.get("dialect")  # str | None

    # Build weighted votes for ACTUAL country
    votes: Dict[str, float] = {}
    voter_log: List[Dict[str, Any]] = []

    # Vote A: Image locations (strongest = ground truth)
    for ir in images:
        iso = ir.get("country_iso")
        if iso:
            w = (ir.get("confidence", 0) / 100.0) * 90  # max 90
            votes[iso] = votes.get(iso, 0) + w
            voter_log.append({"source": "image_ai", "iso": iso,
                              "weight": round(w, 1),
                              "evidence": ir.get("method")})

    # Vote B: Timezone (strong if confidence high)
    if tz.get("best_offset") is not None:
        for iso in tz.get("candidate_countries", []):
            iso = iso[:2] if len(iso) >= 2 else iso  # trim "US-East" → "US"
            w = (tz.get("confidence", 0) / 100.0) * 60  # max 60
            votes[iso] = votes.get(iso, 0) + w
            voter_log.append({"source": "timezone", "iso": iso,
                              "weight": round(w, 1),
                              "evidence": f"UTC{tz['best_offset']:+d} "
                                          f"({tz.get('confidence',0)}%)"})

    # Vote C: Geo mentions in text — VERY WEAK because mentions tell us
    # what the user TALKS ABOUT, not where they LIVE.
    # Cap at 15 to avoid overwhelming TZ + image evidence.
    for iso, count in list(geo_mentions.items())[:3]:  # only top-3
        w = min(15, count * 3)
        votes[iso] = votes.get(iso, 0) + w
        voter_log.append({"source": "geo_mentions", "iso": iso,
                          "weight": w,
                          "evidence": f"mentioned {count} times (topic, not residence)"})

    # Vote D: Dialect — weak because diaspora keep their dialect
    if dialect and isinstance(dialect, str):
        dialect_to_iso = {"SA": "SA", "EG": "EG", "IQ": "IQ",
                          "MA": "MA", "LB": "LB", "GULF": "SA"}
        if dialect in dialect_to_iso:
            iso = dialect_to_iso[dialect]
            votes[iso] = votes.get(iso, 0) + 10
            voter_log.append({"source": "dialect", "iso": iso,
                              "weight": 10, "evidence": f"dialect={dialect}"})

    # ─── Decide ACTUAL country ────────────────────────────────────────
    if votes:
        actual_iso = max(votes, key=votes.get)
        total = sum(votes.values())
        actual_confidence = min(99, int(votes[actual_iso] / total * 100))
    else:
        actual_iso = None
        actual_confidence = 0

    # ─── VPN probability ──────────────────────────────────────────────
    vpn_score = 0
    vpn_reasons: List[str] = []

    if declared_iso and actual_iso:
        if declared_iso == actual_iso:
            vpn_score = 5
            vpn_reasons.append(
                f"✅ الموقع المعلن ({declared_iso}) يطابق الموقع الفعلي")
        else:
            # Big mismatch
            base = 60
            # Boost if declared is West-of-Arab and actual is Arab + Arabic content
            ARAB = {"SA","AE","KW","QA","BH","OM","YE","IQ","SY","JO","LB",
                    "PS","EG","SD","LY","TN","DZ","MA","MR","SO"}
            WEST = {"GB","US","CA","DE","FR","IT","ES","NL","BE","SE","NO",
                    "DK","CH","AT","IE","PT","AU","NZ","FI"}
            if declared_iso in WEST and actual_iso in ARAB:
                base = 90
                vpn_reasons.append(
                    f"🚨 نمط VPN كلاسيكي: حساب يدّعي {declared_iso} "
                    f"لكن كل الإشارات تشير إلى {actual_iso}")
            else:
                vpn_reasons.append(
                    f"⚠️ تعارض: المعلن {declared_iso} ≠ الفعلي {actual_iso}")
            vpn_score = base
    elif declared_iso and not actual_iso:
        vpn_score = 10
        vpn_reasons.append("لم تكفِ الإشارات لتحديد الموقع الفعلي")
    elif not declared_iso and actual_iso:
        vpn_score = 30
        vpn_reasons.append(
            f"الحساب يخفي موقعه لكن الإشارات تشير إلى {actual_iso}")
    else:
        vpn_score = 15
        vpn_reasons.append("بيانات غير كافية للحكم")

    # Boost if timezone DOESN'T match declared country
    if declared_iso and tz.get("best_offset") is not None:
        expected_off = COUNTRY_TO_TZ_OFFSET.get(declared_iso)
        actual_off   = tz.get("best_offset")
        if expected_off is not None and abs(expected_off - actual_off) >= 2:
            vpn_score = min(99, vpn_score + 15)
            vpn_reasons.append(
                f"⏰ المنطقة الزمنية للنشر (UTC{actual_off:+d}) "
                f"لا تطابق الدولة المُعلنة (المتوقع UTC{expected_off:+d})")

    # ─── Verdict label & color ────────────────────────────────────────
    if vpn_score >= 80:
        verdict_label, verdict_color = "🔴 VPN محتمل جداً", "#c62828"
    elif vpn_score >= 50:
        verdict_label, verdict_color = "🟠 احتمال VPN قوي", "#ef6c00"
    elif vpn_score >= 25:
        verdict_label, verdict_color = "🟡 شك معتدل (سفر/مغترب؟)", "#f9a825"
    else:
        verdict_label, verdict_color = "🟢 لا توجد علامات VPN", "#2e7d32"

    # ─── Best estimate of actual location coords ────────────────────
    actual_city, actual_coords = None, None
    if images:
        # Use image with highest confidence matching actual_iso
        best_img = max(
            (i for i in images if i.get("country_iso") == actual_iso),
            key=lambda x: x.get("confidence", 0), default=None)
        if best_img:
            actual_city = best_img.get("city")
            if best_img.get("lat") and best_img.get("lon"):
                actual_coords = (best_img["lat"], best_img["lon"])

    return {
        "actual_iso":         actual_iso,
        "actual_flag":        ge_flag(actual_iso) if actual_iso else "❓",
        "actual_country_ar":  ge_country_ar(actual_iso) if actual_iso else "غير محدد",
        "actual_city":        actual_city,
        "actual_coords":      actual_coords,
        "actual_confidence":  actual_confidence,
        "vpn_score":          vpn_score,
        "vpn_label":          verdict_label,
        "vpn_color":          verdict_color,
        "vpn_reasons":        vpn_reasons,
        "vote_breakdown":     dict(sorted(votes.items(),
                                          key=lambda x: -x[1])),
        "all_voters":         voter_log,
        "maps_links":         (build_map_verification_links(*actual_coords)
                               if actual_coords else None),
    }


# ════════════════════════════════════════════════════════════════════
# Self-test
# ════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else "salim_Aljomaili"
    print(f"🛡️ Investigating @{user}\n" + "═" * 55)

    rep = investigate(user,
                      gemini_api_key=os.environ.get("GEMINI_API_KEY"),
                      analyze_images=False,  # keep fast for local test
                      max_images=0)

    if "error" in rep:
        print(f"❌ {rep['error']}"); sys.exit(1)

    p = rep["profile"]
    print(f"\n👤 {p['name']} (@{p['screen_name']})")
    print(f"   ID: {p['id']}, joined: {p['joined']}, "
          f"followers: {p['followers']:,}")

    d = rep["declared_location"]
    print(f"\n📍 Declared: {d['flag']} {d['iso']} — {d['raw']}")

    tz = rep.get("timezone_analysis")
    if tz:
        print(f"\n⏰ Timezone (from {rep['tweets_fetched']} tweets): "
              f"{tz['best_offset_str']} ({tz['confidence']}%)")
        print(f"   Likely countries: {tz.get('candidate_countries', [])[:5]}")
    else:
        print(f"\n⏰ Timezone: not enough data ({rep['tweets_fetched']} tweets)")

    print(f"\n🌍 Geo mentions: {rep['geo_mentions']}")
    print(f"🗣️  Dialect: {rep['dialect']}")

    v = rep["final_verdict"]
    print("\n" + "═" * 55)
    print(f"🎯 FINAL VERDICT")
    print("═" * 55)
    print(f"📍 Actual location:  {v['actual_flag']} {v['actual_country_ar']} "
          f"({v['actual_iso']}) - confidence {v['actual_confidence']}%")
    if v["actual_city"]:
        print(f"   City: {v['actual_city']}")
    if v["actual_coords"]:
        print(f"   Coords: {v['actual_coords']}")
    print(f"\n🛡️  VPN status: {v['vpn_label']}  ({v['vpn_score']}/100)")
    for r in v["vpn_reasons"]:
        print(f"   • {r}")
    print(f"\n📊 Vote breakdown: {v['vote_breakdown']}")
