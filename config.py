# ═══════════════════════════════════════════════════════════
# BSR-V217L-CONFIG-PII-FLAG-AHMAD-20260613
# كسر القيد #21 — معتمَد بموافقة المالك (2026-06-13)
# ═══════════════════════════════════════════════════════════
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "TEST_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "BaseerBot")
TIMEZONE = "Asia/Riyadh"
MODE = "production"

# ⚠️ كسر القيد #21
STORE_RAW_USER_ID = True
REQUIRE_EXPLICIT_CONSENT = True
CONSENT_VERSION = "1.0"
PRIVACY_POLICY_URL = "https://github.com/7sn301/social-accounts-generator/blob/main/PRIVACY.md"

# الاحتفاظ بالبيانات
DATA_RETENTION_DAYS = 365
ENABLE_RIGHT_TO_BE_FORGOTTEN = True

# سجلّ التدقيق
CONSENT_LOG_FILE = "./data/consent_log.jsonl"
