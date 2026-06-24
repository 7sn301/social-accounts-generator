# ═══════════════════════════════════════════════════════════
# BSR-V217L-COUNTRY-DETECTOR-AHMAD-20260613
# استنتاج الدولة من language_code (لا Geocoding خارجي - القيد #19)
# ═══════════════════════════════════════════════════════════
from typing import Optional

LANG_TO_COUNTRY = {
    "ar-SA": "SA", "ar-EG": "EG", "ar-AE": "AE", "ar-KW": "KW",
    "ar-QA": "QA", "ar-BH": "BH", "ar-OM": "OM", "ar-JO": "JO",
    "ar-LB": "LB", "ar-SY": "SY", "ar-IQ": "IQ", "ar-YE": "YE",
    "ar-PS": "PS", "ar-MA": "MA", "ar-DZ": "DZ", "ar-TN": "TN",
    "ar-LY": "LY", "ar-SD": "SD",
    "en-US": "US", "en-GB": "GB", "en-CA": "CA", "en-AU": "AU",
    "fr-FR": "FR", "fr-CA": "CA",
    "de-DE": "DE", "es-ES": "ES", "it-IT": "IT", "tr-TR": "TR",
    "ru-RU": "RU", "ja-JP": "JP", "ko-KR": "KR", "zh-CN": "CN",
    "ar": "SA", "en": "US", "fr": "FR", "de": "DE",
    "es": "ES", "it": "IT", "tr": "TR", "ru": "RU",
}


def detect_from_language(language_code: Optional[str]) -> str:
    if not language_code:
        return "—"
    code = language_code.strip()
    if code in LANG_TO_COUNTRY:
        return LANG_TO_COUNTRY[code]
    base = code.split("-")[0]
    return LANG_TO_COUNTRY.get(base, "—")
