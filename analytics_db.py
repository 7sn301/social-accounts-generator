"""
analytics_db.py - Baseer v2.1.9
PostgreSQL/Supabase Cloud Database
Backward compatible with bot.py and 99_admin.py
"""
import os
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("⚠️ psycopg2 not installed. Run: pip install psycopg2-binary")

logger = logging.getLogger(__name__)

# ─────────────────────────────────────
# Supabase PostgreSQL Configuration
# ─────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    logger.warning("⚠️ DATABASE_URL not set. Falling back to SQLite for local dev.")

# Connection pool (lazy init)
_pool = None


def get_pool():
    """Lazy-initialize connection pool"""
    global _pool
    if _pool is None and DATABASE_URL and POSTGRES_AVAILABLE:
        try:
            _pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            logger.info("✅ PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"❌ Failed to init pool: {e}")
    return _pool


@contextmanager
def get_db():
    """Context manager for DB connections"""
    pool = get_pool()
    if not pool:
        raise RuntimeError("Database pool not available - check DATABASE_URL")
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"DB error: {e}")
        raise
    finally:
        pool.putconn(conn)


def init_db():
    """Initialize tables (idempotent)"""
    if not POSTGRES_AVAILABLE or not DATABASE_URL:
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
            logger.info("✅ DB tables initialized")
    except Exception as e:
        logger.error(f"init_db error: {e}")


# Try init on import
try:
    init_db()
except Exception as e:
    logger.warning(f"DB init deferred: {e}")


# ─────────────────────────────────────
# User Logging
# ─────────────────────────────────────
def log_user(telegram_id, username=None, first_name=None, last_name=None,
             language_code=None, ip=None, country=None, city=None):
    """Insert or update user"""
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
            logger.info(f"📊 logged user {telegram_id}")
    except Exception as e:
        logger.error(f"log_user error: {e}")


def log_search(telegram_id, target_username, target_country=None,
               target_region=None, followers=0):
    """Log a search"""
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
            logger.info(f"📊 logged search by {telegram_id} → @{target_username}")
    except Exception as e:
        logger.error(f"log_search error: {e}")


# ─────────────────────────────────────
# Backward Compatibility Aliases (for bot.py)
# ─────────────────────────────────────
def record_user_start(telegram_id, username=None, first_name=None, last_name=None,
                     language_code=None, ip=None, country=None, city=None, **kwargs):
    """Alias for log_user() - tolerates extra kwargs"""
    return log_user(telegram_id, username, first_name, last_name,
                   language_code, ip, country, city)


def record_search(telegram_id, target_username=None, target_country=None,
                 target_region=None, followers=0, **kwargs):
    """Alias for log_search() - tolerates extra kwargs"""
    return log_search(telegram_id, target_username, target_country,
                     target_region, followers)


def record_user(telegram_id, username=None, **kwargs):
    """Alternative alias"""
    return log_user(telegram_id, username=username, **kwargs)


# ─────────────────────────────────────
# Query Functions
# ─────────────────────────────────────
def get_all_users(limit=100, offset=0):
    """Get all users with pagination"""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT * FROM users
                ORDER BY last_seen DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"get_all_users error: {e}")
        return []


def get_user_searches(telegram_id=None, limit=50, offset=0):
    """Get searches (filtered by user or all)"""
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
                    ORDER BY s.timestamp DESC
                    LIMIT %s OFFSET %s
                """, (telegram_id, limit, offset))
            else:
                c.execute("""
                    SELECT s.*, u.username as searcher_username,
                           u.first_name as searcher_first_name
                    FROM searches s
                    LEFT JOIN users u ON s.telegram_id = u.telegram_id
                    ORDER BY s.timestamp DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"get_user_searches error: {e}")
        return []


def get_all_searches(limit=100, offset=0):
    return get_user_searches(telegram_id=None, limit=limit, offset=offset)


def get_stats():
    """Comprehensive stats"""
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
                ORDER BY count DESC LIMIT 10
            """)
            top_countries = [dict(row) for row in c.fetchall()]

            c.execute("""
                SELECT target_username, COUNT(*) as count FROM searches
                WHERE target_username IS NOT NULL
                GROUP BY target_username
                ORDER BY count DESC LIMIT 10
            """)
            top_targets = [dict(row) for row in c.fetchall()]

            c.execute("""
                SELECT COUNT(*) as total FROM searches
                WHERE timestamp >= CURRENT_DATE
            """)
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
        logger.error(f"get_stats error: {e}")
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
    except Exception as e:
        logger.error(f"get_user_by_id error: {e}")
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
    except Exception as e:
        logger.error(f"search_users error: {e}")
        return []


def delete_user(telegram_id):
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM searches WHERE telegram_id = %s", (telegram_id,))
            c.execute("DELETE FROM users WHERE telegram_id = %s", (telegram_id,))
            return True
    except Exception as e:
        logger.error(f"delete_user error: {e}")
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
