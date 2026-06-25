"""
analytics_db.py - Baseer v2.1.8.6
SQLite Analytics Database - Complete with all required functions
Compatible with pages/99_admin.py and bot.py
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager


# ─────────────────────────────────────
# Safe DB Path Handling
# ─────────────────────────────────────
DEFAULT_DB = Path(__file__).parent / "data" / "analytics.db"
DB_PATH = Path(os.getenv("ANALYTICS_DB_PATH", str(DEFAULT_DB)))

try:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
except (FileExistsError, PermissionError, OSError):
    DB_PATH = Path("/tmp/analytics.db")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────
# Database Connection
# ─────────────────────────────────────
@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """تهيئة جداول قاعدة البيانات"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT,
                ip_address TEXT,
                country TEXT,
                city TEXT,
                first_seen TEXT,
                last_seen TEXT,
                total_searches INTEGER DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                target_username TEXT,
                target_country TEXT,
                target_region TEXT,
                followers INTEGER DEFAULT 0,
                timestamp TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_searches_tid ON searches(telegram_id, timestamp DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_searches_country ON searches(target_country)")


# Initialize on import
try:
    init_db()
except Exception as e:
    print(f"Analytics DB init warning: {e}")


# ─────────────────────────────────────
# User Logging
# ─────────────────────────────────────
def log_user(telegram_id, username=None, first_name=None, last_name=None,
             language_code=None, ip=None, country=None, city=None):
    """تسجيل أو تحديث بيانات مستخدم"""
    now = datetime.utcnow().isoformat()
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT telegram_id FROM users WHERE telegram_id=?", (telegram_id,))
            exists = c.fetchone()
            if exists:
                c.execute("""
                    UPDATE users SET
                        username=COALESCE(?, username),
                        first_name=COALESCE(?, first_name),
                        last_name=COALESCE(?, last_name),
                        language_code=COALESCE(?, language_code),
                        ip_address=COALESCE(?, ip_address),
                        country=COALESCE(?, country),
                        city=COALESCE(?, city),
                        last_seen=?
                    WHERE telegram_id=?
                """, (username, first_name, last_name, language_code,
                      ip, country, city, now, telegram_id))
            else:
                c.execute("""
                    INSERT INTO users
                    (telegram_id, username, first_name, last_name, language_code,
                     ip_address, country, city, first_seen, last_seen, total_searches)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (telegram_id, username, first_name, last_name, language_code,
                      ip, country, city, now, now))
    except Exception as e:
        print(f"log_user error: {e}")


# ─────────────────────────────────────
# Search Logging
# ─────────────────────────────────────
def log_search(telegram_id, target_username, target_country=None,
               target_region=None, followers=0):
    """تسجيل عملية بحث"""
    now = datetime.utcnow().isoformat()
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO searches
                (telegram_id, target_username, target_country, target_region, followers, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (telegram_id, target_username, target_country, target_region, followers, now))
            c.execute("""
                UPDATE users SET total_searches = total_searches + 1, last_seen=?
                WHERE telegram_id=?
            """, (now, telegram_id))
    except Exception as e:
        print(f"log_search error: {e}")


# ─────────────────────────────────────
# Query Functions (used by 99_admin.py)
# ─────────────────────────────────────
def get_all_users(limit=100, offset=0):
    """جلب قائمة المستخدمين مع دعم limit/offset"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM users
                ORDER BY last_seen DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        print(f"get_all_users error: {e}")
        return []


def get_user_searches(telegram_id=None, limit=50, offset=0):
    """جلب سجلات البحث - لمستخدم محدد أو الكل"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            if telegram_id:
                c.execute("""
                    SELECT s.*, u.username as searcher_username, u.first_name as searcher_first_name
                    FROM searches s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    WHERE s.telegram_id=?
                    ORDER BY s.timestamp DESC
                    LIMIT ? OFFSET ?
                """, (telegram_id, limit, offset))
            else:
                c.execute("""
                    SELECT s.*, u.username as searcher_username, u.first_name as searcher_first_name
                    FROM searches s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    ORDER BY s.timestamp DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        print(f"get_user_searches error: {e}")
        return []


def get_all_searches(limit=100, offset=0):
    """جلب جميع عمليات البحث"""
    return get_user_searches(telegram_id=None, limit=limit, offset=offset)


def get_stats():
    """الإحصائيات العامة للوحة الإدارة"""
    try:
        with get_db() as conn:
            c = conn.cursor()

            c.execute("SELECT COUNT(*) as total FROM users")
            total_users = c.fetchone()["total"]

            c.execute("SELECT COUNT(*) as total FROM searches")
            total_searches = c.fetchone()["total"]

            c.execute("""
                SELECT COUNT(DISTINCT country) as total FROM users
                WHERE country IS NOT NULL AND country != ''
            """)
            total_countries = c.fetchone()["total"]

            c.execute("""
                SELECT target_country, COUNT(*) as count FROM searches
                WHERE target_country IS NOT NULL AND target_country != ''
                GROUP BY target_country
                ORDER BY count DESC
                LIMIT 10
            """)
            top_countries = [dict(row) for row in c.fetchall()]

            c.execute("""
                SELECT target_username, COUNT(*) as count FROM searches
                WHERE target_username IS NOT NULL
                GROUP BY target_username
                ORDER BY count DESC
                LIMIT 10
            """)
            top_targets = [dict(row) for row in c.fetchall()]

            today = datetime.utcnow().date().isoformat()
            c.execute("SELECT COUNT(*) as total FROM searches WHERE timestamp >= ?", (today,))
            today_searches = c.fetchone()["total"]

            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            c.execute("SELECT COUNT(DISTINCT telegram_id) as total FROM users WHERE last_seen >= ?", (week_ago,))
            active_week = c.fetchone()["total"]

            return {
                "total_users": total_users,
                "total_searches": total_searches,
                "total_countries": total_countries,
                "top_countries": top_countries,
                "top_targets": top_targets,
                "today_searches": today_searches,
                "active_week": active_week,
            }
    except Exception as e:
        print(f"get_stats error: {e}")
        return {
            "total_users": 0,
            "total_searches": 0,
            "total_countries": 0,
            "top_countries": [],
            "top_targets": [],
            "today_searches": 0,
            "active_week": 0,
        }


def get_user_by_id(telegram_id):
    """جلب بيانات مستخدم محدد"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
            row = c.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"get_user_by_id error: {e}")
        return None


def search_users(query, limit=50):
    """بحث في المستخدمين"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            q = f"%{query}%"
            c.execute("""
                SELECT * FROM users
                WHERE username LIKE ? OR first_name LIKE ?
                   OR last_name LIKE ? OR country LIKE ?
                ORDER BY last_seen DESC
                LIMIT ?
            """, (q, q, q, q, limit))
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        print(f"search_users error: {e}")
        return []


def delete_user(telegram_id):
    """حذف مستخدم وسجلاته (GDPR)"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM searches WHERE telegram_id=?", (telegram_id,))
            c.execute("DELETE FROM users WHERE telegram_id=?", (telegram_id,))
            return True
    except Exception as e:
        print(f"delete_user error: {e}")
        return False


def get_users_count():
    """عدد المستخدمين فقط"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM users")
            return c.fetchone()["total"]
    except Exception:
        return 0


def get_searches_count():
    """عدد عمليات البحث فقط"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM searches")
            return c.fetchone()["total"]
    except Exception:
        return 0


# ─────────────────────────────────────
# Explicit Exports
# ─────────────────────────────────────
__all__ = [
    'init_db',
    'log_user',
    'log_search',
    'get_all_users',
    'get_user_searches',
    'get_all_searches',
    'get_stats',
    'get_user_by_id',
    'search_users',
    'delete_user',
    'get_users_count',
    'get_searches_count',
    'DB_PATH',
]
