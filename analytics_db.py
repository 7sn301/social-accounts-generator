"""
analytics_db.py - Baseer v2.1.8.1
SQLite Analytics Database - Safe Path Handling
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager


# مسار آمن للقاعدة
DEFAULT_DB = Path(__file__).parent / "data" / "analytics.db"
DB_PATH = Path(os.getenv("ANALYTICS_DB_PATH", str(DEFAULT_DB)))

# إنشاء المجلد بأمان
try:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
except (FileExistsError, PermissionError):
    DB_PATH = Path("/tmp/analytics.db")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
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
                timestamp TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            )
        """)


def log_user(telegram_id, username, first_name, last_name, ip, country, city):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT telegram_id FROM users WHERE telegram_id=?", (telegram_id,))
        exists = c.fetchone()
        if exists:
            c.execute("""
                UPDATE users SET username=?, first_name=?, last_name=?,
                ip_address=?, country=?, city=?, last_seen=?
                WHERE telegram_id=?
            """, (username, first_name, last_name, ip, country, city, now, telegram_id))
        else:
            c.execute("""
                INSERT INTO users
                (telegram_id, username, first_name, last_name, ip_address,
                country, city, first_seen, last_seen, total_searches)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (telegram_id, username, first_name, last_name, ip,
                  country, city, now, now))


def log_search(telegram_id, target_username, target_country):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO searches (telegram_id, target_username, target_country, timestamp)
            VALUES (?, ?, ?, ?)
        """, (telegram_id, target_username, target_country, now))
        c.execute("""
            UPDATE users SET total_searches = total_searches + 1, last_seen=?
            WHERE telegram_id=?
        """, (now, telegram_id))


def get_all_users():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY last_seen DESC")
        return [dict(row) for row in c.fetchall()]


def get_user_searches(telegram_id, limit=50):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM searches WHERE telegram_id=?
            ORDER BY timestamp DESC LIMIT ?
        """, (telegram_id, limit))
        return [dict(row) for row in c.fetchall()]


def get_stats():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM users")
        total_users = c.fetchone()["total"]
        c.execute("SELECT COUNT(*) as total FROM searches")
        total_searches = c.fetchone()["total"]
        c.execute("""
            SELECT target_country, COUNT(*) as count FROM searches
            GROUP BY target_country ORDER BY count DESC LIMIT 10
        """)
        top_countries = [dict(row) for row in c.fetchall()]
        return {
            "total_users": total_users,
            "total_searches": total_searches,
            "top_countries": top_countries,
        }


# تهيئة القاعدة عند الاستيراد
init_db()
