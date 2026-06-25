# ═══════════════════════════════════════════════════════════
# BSR-V217L-ANALYTICS-PII-AWARE-AHMAD-20260613
# تحليلات شهرية/ربعية/سنوية لتوزيع المستخدمين حسب الدولة
# ═══════════════════════════════════════════════════════════
from collections import Counter
from datetime import datetime
import user_storage


def monthly_country_distribution(year: int, month: int):
    users = user_storage.all_users().values()
    counter = Counter()
    for u in users:
        ts = u.get("last_seen", "")
        if ts.startswith(f"{year}-{month:02d}"):
            counter[u.get("country", "—")] += 1
    return dict(counter)


def quarterly_summary(year: int, quarter: int):
    months = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}[quarter]
    combined = Counter()
    for m in months:
        for k, v in monthly_country_distribution(year, m).items():
            combined[k] += v
    return dict(combined)


def yearly_summary(year: int):
    combined = Counter()
    for m in range(1, 13):
        for k, v in monthly_country_distribution(year, m).items():
            combined[k] += v
    return dict(combined)


def total_consented_users() -> int:
    return sum(1 for u in user_storage.all_users().values() if u.get("consent_given"))


def total_queries() -> int:
    return sum(u.get("total_queries", 0) for u in user_storage.all_users().values())
ADMIN_USERNAME = "your_admin_username"
ADMIN_PASSWORD = "your_super_strong_password_24_chars"
ADMIN_PASSWORD_SALT = "64_hex_random_chars"
SESSION_SECRET = "32_byte_url_safe_token"
ANALYTICS_DB_PATH = "./data/analytics.db"
