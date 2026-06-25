"""
analytics_db.py - Baseer v2.2.0 CTO-Approved
PostgreSQL/Supabase Cloud Database - Production Ready
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

# ============================================
# CRITICAL: Print to stdout for Railway logs
# ============================================
print("=" * 60, flush=True)
print("[analytics_db] v2.2.0 - Starting module import", flush=True)
print("=" * 60, flush=True)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
    POSTGRES_AVAILABLE = True
    print("[analytics_db] psycopg2 imported successfully", flush=True)
except ImportError as e:
    POSTGRES_AVAILABLE = False
    print(f"[analytics_db] CRITICAL: psycopg2 NOT installed: {e}", flush=True)

logger = logging.getLogger(__name__)

# ============================================
# Read DATABASE_URL with diagnostics
# ============================================
DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL:
    safe_url = DATABASE_URL[:30] + "..." + DATABASE_URL[-20:]
    print(f"[analytics_db] DATABASE_URL found: {safe_url}", flush=True)
    print(f"[analytics_db] URL length: {len(DATABASE_URL)} chars", flush=True)
else:
    print("[analytics_db] CRITICAL: DATABASE_URL is EMPTY or NOT SET!", flush=True)
    print(f"[analytics_db] Available env vars: {[k for k in os.environ.keys() if 'DB' in k or 'DATABASE' in k or 'POSTGRES' in k]}", flush=True)

_pool = None


def get_pool():
    global _pool
    if _pool is not None:
        return _pool

    if not POSTGRES_AVAILABLE:
        print("[get_pool] FAIL: psycopg2 not available", flush=True)
        return None

    if not DATABASE_URL:
        print("[get_pool] FAIL: DATABASE_URL empty", flush=True)
        return None

    try:
        print("[get_pool] Attempting pool creation...", flush=True)
        _pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        print("[get_pool] SUCCESS: PostgreSQL connection pool initialized", flush=True)
        logger.info("PostgreSQL connection pool initialized")

        # Test connection immediately
        test_conn = _pool.getconn()
        test_cur = test_conn.cursor()
        test_cur.execute("SELECT version();")
        version = test_cur.fetchone()
        print(f"[get_pool] DB version: {str(version)[:80]}", flush=True)
        _pool.putconn(test_conn)

        return _pool
    except Exception as e:
        print(f"[get_pool] FAIL: {type(e).__name__}: {e}", flush=True)
        logger.error(f"Failed to init pool: {e}")
        return None


@contextmanager
def get_db():
    p = get_pool()
    if not p:
        raise RuntimeError("Database pool not available - check DATABASE_URL and psycopg2")
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"DB error: {e}")
        print(f"[get_db] error: {e}", flush=True)
        raise
    finally:
        p.putconn(conn)


def init_db():
    if not POSTGRES_AVAILABLE or not DATABASE_URL:
        print("[init_db] Skipped (no psycopg2 or DATABASE_URL)", flush=True)
        return
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    ip_address TEXT,
                    country TEXT,
                    city TEXT,
                    first_seen TIMESTAMP DEFAULT NOW(),
                    last_seen TIMESTAMP DEFAULT NOW(),
                    total_searches INTEGER DEFAULT 0
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS searches (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    target_username TEXT,
                    target_country TEXT,
                    target_region TEXT,
                    followers INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen DESC)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_searches_tid ON searches(telegram_id, timestamp DESC)")
            print("[init_db] SUCCESS: DB tables initialized", flush=True)
            logger.info("DB tables initialized")
    except Exception as e:
        print(f"[init_db] FAIL: {e}", flush=True)
        logger.error(f"init_db error: {e}")


# Initialize on import
print("[analytics_db] Calling init_db()...", flush=True)
try:
    init_db()
    print("[analytics_db] Module ready", flush=True)
except Exception as e:
    print(f"[analytics_db] init_db failed: {e}", flush=True)


def log_user(telegram_id, username=None, first_name=None, last_name=None,
             language_code=None, ip=None, country=None, city=None):
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO users
                (telegram_id, username, first_name, last_name, language_code,
                 ip_address, country, city, first_seen, last_seen, total_searches)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), 0)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    username = COALESCE(EXCLUDED.username, users.username),
                    first_name = COALESCE(EXCLUDED.first_name, users.first_name),
                    last_name = COALESCE(EXCLUDED.last_name, users.last_name),
                    language_code = COALESCE(EXCLUDED.language_code, users.language_code),
                    ip_address = COALESCE(EXCLUDED.ip_address, users.ip_address),
                    country = COALESCE(EXCLUDED.country, users.country),
                    city = COALESCE(EXCLUDED.city, users.city),
                    last_seen = NOW()
            """, (telegram_id, username, first_name, last_name,
                  language_code, ip, country, city))
            print(f"[log_user] SUCCESS: user {telegram_id} saved", flush=True)
            logger.info(f"logged user {telegram_id}")
    except Exception as e:
        print(f"[log_user] FAIL: {e}", flush=True)
        logger.error(f"log_user error: {e}")


def log_search(telegram_id, target_username, target_country=None,
               target_region=None, followers=0):
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO searches
                (telegram_id, target_username, target_country, target_region, followers, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (telegram_id, target_username, target_country, target_region, followers))
            c.execute("""
                UPDATE users SET total_searches = total_searches + 1, last_seen = NOW()
                WHERE telegram_id = %s
            """, (telegram_id,))
            print(f"[log_search] SUCCESS: {telegram_id} -> @{target_username}", flush=True)
            logger.info(f"logged search by {telegram_id} -> @{target_username}")
    except Exception as e:
        print(f"[log_search] FAIL: {e}", flush=True)
        logger.error(f"log_search error: {e}")


def record_user_start(telegram_id, username=None, first_name=None, last_name=None,
                     language_code=None, ip=None, country=None, city=None, **kwargs):
    return log_user(telegram_id, username, first_name, last_name,
                   language_code, ip, country, city)


def record_search(telegram_id, target_username=None, target_country=None,
                 target_region=None, followers=0, **kwargs):
    return log_search(telegram_id, target_username, target_country,
                     target_region, followers)


def record_user(telegram_id, username=None, **kwargs):
    return log_user(telegram_id, username=username, **kwargs)


def get_all_users(limit=100, offset=0):
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users ORDER BY last_seen DESC LIMIT %s OFFSET %s",
                     (limit, offset))
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        print(f"[get_all_users] FAIL: {e}", flush=True)
        return []


def get_user_searches(telegram_id=None, limit=50, offset=0):
    try:
        with get_db() as conn:
            c = conn.cursor()
            if telegram_id:
                c.execute("""
                    SELECT s.*, u.username as searcher_username,
                           u.first_name as searcher_first_name
                    FROM searches s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    WHERE s.telegram_id = %s
                    ORDER BY s.timestamp DESC LIMIT %s OFFSET %s
                """, (telegram_id, limit, offset))
            else:
                c.execute("""
                    SELECT s.*, u.username as searcher_username,
                           u.first_name as searcher_first_name
                    FROM searches s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    ORDER BY s.timestamp DESC LIMIT %s OFFSET %s
                """, (limit, offset))
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        print(f"[get_user_searches] FAIL: {e}", flush=True)
        return []


def get_all_searches(limit=100, offset=0):
    return get_user_searches(telegram_id=None, limit=limit, offset=offset)


def get_stats():
    try:
        with get_db() as conn:
            c = conn.cursor()

            c.execute("SELECT COUNT(*) as total FROM users")
            total_users = c.fetchone()["total"]

            c.execute("SELECT COUNT(*) as total FROM searches")
            total_searches = c.fetchone()["total"]

            c.execute("SELECT COUNT(DISTINCT country) as total FROM users WHERE country IS NOT NULL AND country != ''")
            total_countries = c.fetchone()["total"]

            c.execute("""
                SELECT target_country, COUNT(*) as count FROM searches
                WHERE target_country IS NOT NULL AND target_country != ''
                GROUP BY target_country ORDER BY count DESC LIMIT 10
            """)
            top_countries = [dict(row) for row in c.fetchall()]

            c.execute("""
                SELECT target_username, COUNT(*) as count FROM searches
                WHERE target_username IS NOT NULL
                GROUP BY target_username ORDER BY count DESC LIMIT 10
            """)
            top_targets = [dict(row) for row in c.fetchall()]

            c.execute("SELECT COUNT(*) as total FROM searches WHERE timestamp >= CURRENT_DATE")
            today_searches = c.fetchone()["total"]

            c.execute("""
                SELECT COUNT(DISTINCT telegram_id) as total FROM users
                WHERE last_seen >= NOW() - INTERVAL '7 days'
            """)
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
        print(f"[get_stats] FAIL: {e}", flush=True)
        return {
            "total_users": 0, "total_searches": 0, "total_countries": 0,
            "top_countries": [], "top_targets": [],
            "today_searches": 0, "active_week": 0,
        }


def get_user_by_id(telegram_id):
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
            row = c.fetchone()
            return dict(row) if row else None
    except Exception:
        return None


def search_users(query, limit=50):
    try:
        with get_db() as conn:
            c = conn.cursor()
            q = f"%{query}%"
            c.execute("""
                SELECT * FROM users
                WHERE username ILIKE %s OR first_name ILIKE %s
                   OR last_name ILIKE %s OR country ILIKE %s
                ORDER BY last_seen DESC LIMIT %s
            """, (q, q, q, q, limit))
            return [dict(row) for row in c.fetchall()]
    except Exception:
        return []


def delete_user(telegram_id):
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM searches WHERE telegram_id = %s", (telegram_id,))
            c.execute("DELETE FROM users WHERE telegram_id = %s", (telegram_id,))
            return True
    except Exception:
        return False


def get_users_count():
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM users")
            return c.fetchone()["total"]
    except Exception:
        return 0


def get_searches_count():
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM searches")
            return c.fetchone()["total"]
    except Exception:
        return 0


__all__ = [
    'init_db',
    'log_user', 'log_search',
    'record_user_start', 'record_search', 'record_user',
    'get_all_users', 'get_user_searches', 'get_all_searches',
    'get_stats', 'get_user_by_id', 'search_users', 'delete_user',
    'get_users_count', 'get_searches_count',
    'DATABASE_URL',
]
