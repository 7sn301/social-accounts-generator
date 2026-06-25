# ═══════════════════════════════════════════════════════════
# BSR-V218-ANALYTICS-DB-AHMAD-20260613
# قاعدة بيانات التحليلات (SQLite — يمكن الترقية لـ Supabase)
# ═══════════════════════════════════════════════════════════
"""Analytics DB - تسجيل وقراءة المستخدمين الذين ضغطوا /start"""
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

DB_PATH = os.getenv("ANALYTICS_DB_PATH", "./data/analytics.db")
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def init_db():
    """إنشاء الجداول"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT,
            ip_address TEXT,
            country TEXT,
            city TEXT,
            isp TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            total_searches INTEGER DEFAULT 0,
            UNIQUE(telegram_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT NOT NULL,
            search_query TEXT NOT NULL,
            result_country TEXT,
            result_username TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            username TEXT,
            success INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def record_user_start(telegram_id, username, first_name, last_name,
                       language_code, ip_address, country, city, isp):
    """تسجيل/تحديث مستخدم عند /start"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute('''
        INSERT INTO users (telegram_id, username, first_name, last_name,
                           language_code, ip_address, country, city, isp,
                           first_seen, last_seen, total_searches)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            language_code = excluded.language_code,
            ip_address = excluded.ip_address,
            country = excluded.country,
            city = excluded.city,
            isp = excluded.isp,
            last_seen = excluded.last_seen
    ''', (str(telegram_id), username, first_name, last_name,
          language_code, ip_address, country, city, isp, now, now))
    conn.commit()
    conn.close()


def record_search(telegram_id, search_query, result_country=None, result_username=None):
    """تسجيل عملية بحث"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute('''
        INSERT INTO searches (telegram_id, search_query, result_country,
                              result_username, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(telegram_id), search_query, result_country, result_username, now))
    c.execute('''
        UPDATE users SET total_searches = total_searches + 1,
                         last_seen = ?
        WHERE telegram_id = ?
    ''', (now, str(telegram_id)))
    conn.commit()
    conn.close()


def get_all_users(limit=100):
    """جلب جميع المستخدمين"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT telegram_id, username, first_name, last_name, language_code,
               ip_address, country, city, isp, first_seen, last_seen,
               total_searches
        FROM users
        ORDER BY last_seen DESC
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return [{
        'telegram_id': r[0], 'username': r[1], 'first_name': r[2],
        'last_name': r[3], 'language_code': r[4], 'ip_address': r[5],
        'country': r[6], 'city': r[7], 'isp': r[8],
        'first_seen': r[9], 'last_seen': r[10], 'total_searches': r[11],
    } for r in rows]


def get_user_searches(telegram_id, limit=50):
    """جلب آخر بحثات مستخدم"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT search_query, result_country, result_username, timestamp
        FROM searches
        WHERE telegram_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (str(telegram_id), limit))
    rows = c.fetchall()
    conn.close()
    return [{'query': r[0], 'country': r[1], 'username': r[2], 'timestamp': r[3]}
            for r in rows]


def get_stats():
    """إحصائيات عامة"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM searches')
    total_searches = c.fetchone()[0]
    c.execute('''
        SELECT country, COUNT(*) FROM users
        WHERE country IS NOT NULL
        GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10
    ''')
    countries = dict(c.fetchall())
    conn.close()
    return {
        'total_users': total_users,
        'total_searches': total_searches,
        'top_countries': countries,
    }
