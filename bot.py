"""
╔══════════════════════════════════════════════════════════════════╗
║  BSR-V240-CTO-NUCLEAR-FIX-BOT-AHMAD-20260726                     ║
║  bot.py v2.4.0 - NUCLEAR FIX (HTML + Robust Error Handling)      ║
║  Date: 2026-07-26 | Leader: Dr. Ahmad Al-Fanni (CTO)             ║
╚══════════════════════════════════════════════════════════════════╝

🏆 v2.4.0 FIXES:
  1. load_dotenv() FIRST before any other import (env priority)
  2. HTML parse mode (safer than Markdown, no _ escape needed)
  3. DB failures don't stop the bot (analytics is optional)
  4. Error handler registered (no unhandled Conflict 409)
  5. Detailed logging for every step

Public Commands:
  /start   - Welcome message + register user (best-effort)
  /help    - Command list
  /privacy - Privacy policy URL
  <text>   - TikTok lookup for @username
"""

# ═══════════════════════════════════════════════════════════
# 🔥 STEP 1: Load .env BEFORE any other import (critical!)
# ═══════════════════════════════════════════════════════════
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import Conflict, NetworkError, TelegramError

# ═══════════════════════════════════════════════════════════
# 📦 STEP 2: Import our modules (env is loaded now)
# ═══════════════════════════════════════════════════════════
from tiktok_lookup import lookup_tiktok_user, clean_username

# ═══════════════════════════════════════════════════════════
# 🚀 v2.6.0 - Cache Layer + Rate Limiter integration
# BSR-V260-CTO-ULTIMATE-EDITION-AHMAD-20260727
# ═══════════════════════════════════════════════════════════
try:
    from cache_layer import get_cached_lookup, cache_lookup, cache_stats
    CACHE_AVAILABLE = True
except Exception as _e:
    CACHE_AVAILABLE = False
    def get_cached_lookup(u): return None
    def cache_lookup(u, r, ttl=None): pass
    def cache_stats(): return {}

try:
    from rate_limiter import check_rate_limit, format_rate_limit_message, add_admin, rate_limit_stats
    RATE_LIMIT_AVAILABLE = True
except Exception as _e:
    RATE_LIMIT_AVAILABLE = False
    def check_rate_limit(uid): return (True, None)
    def format_rate_limit_message(retry, remaining=0): return "⏳ يرجى الانتظار قليلاً"
    def add_admin(uid): pass
    def rate_limit_stats(): return {}

# Register admins (bypass rate limit) - configurable via env
_ADMIN_IDS = os.getenv("ADMIN_USER_IDS", "").strip()
if _ADMIN_IDS and RATE_LIMIT_AVAILABLE:
    for _aid in _ADMIN_IDS.split(","):
        _aid = _aid.strip()
        if _aid.isdigit():
            add_admin(_aid)

# Analytics DB is OPTIONAL - bot works without it
try:
    from analytics_db import record_user_start, record_search
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

    def record_user_start(*args, **kwargs):
        pass

    def record_search(*args, **kwargs):
        pass

# ═══════════════════════════════════════════════════════════
# ⚙️ Configuration
# ═══════════════════════════════════════════════════════════
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "Baseer_Lookup_Bot").strip()
PRIVACY_POLICY_URL = os.getenv(
    "PRIVACY_POLICY_URL",
    "https://github.com/7sn301/social-accounts-generator/blob/main/PRIVACY.md"
).strip()

# Verbose logging for diagnostics
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# 🔎 Environment sanity check (v2.4.0 diagnostic)
# ═══════════════════════════════════════════════════════════
def _env_sanity_check():
    """Print env status at startup for diagnostics."""
    logger.info("=" * 60)
    logger.info("🔎 BSR v2.4.0 Environment Sanity Check")
    logger.info("=" * 60)

    checks = [
        ("BOT_TOKEN", bool(BOT_TOKEN), f"({len(BOT_TOKEN)} chars)" if BOT_TOKEN else "MISSING"),
        ("BOT_USERNAME", bool(BOT_USERNAME), BOT_USERNAME),
        ("RAPIDAPI_KEY", bool(os.getenv("RAPIDAPI_KEY", "").strip()),
         f"({len(os.getenv('RAPIDAPI_KEY', '').strip())} chars)"),
        ("RAPIDAPI_HOST", bool(os.getenv("RAPIDAPI_HOST", "").strip()),
         os.getenv("RAPIDAPI_HOST", "MISSING")),
        ("DATABASE_URL", bool(os.getenv("DATABASE_URL", "").strip()),
         f"({len(os.getenv('DATABASE_URL', '').strip())} chars)"),
        ("ANALYTICS_MODULE", ANALYTICS_AVAILABLE,
         "loaded" if ANALYTICS_AVAILABLE else "not loaded"),
    ]

    for name, ok, detail in checks:
        icon = "✅" if ok else "⚠️ "
        logger.info(f"{icon} {name}: {detail}")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════
# 🎯 Command handlers
# ═══════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    telegram_id = user.id
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    language_code = user.language_code or ""

    # Best-effort DB recording (never blocks)
    if ANALYTICS_AVAILABLE:
        try:
            record_user_start(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                ip="TELEGRAM_HIDDEN",
                country=None,
                city=None,
            )
            logger.info(f"📊 recorded /start: {telegram_id} @{username}")
        except Exception as e:
            logger.warning(f"📊 DB record_user_start skipped: {e}")

    welcome = (
        f"👋 مرحبًا <b>{_html_escape(first_name)}</b>!\n\n"
        f"🔍 <b>بوت بصير — TikTok Lookup</b>\n\n"
        f"أرسل اسم مستخدم TikTok أو رابط حساب وسأعرض لك:\n"
        f"  • 👤 معلومات الحساب\n"
        f"  • 🌍 دولة الحساب (249+ دولة)\n"
        f"  • 🎯 كشف VPN تلقائي\n"
        f"  • 📊 الإحصائيات الكاملة"
    )
    await update.message.reply_text(welcome, parse_mode="HTML")


async def handle_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any text message as a TikTok lookup — with rate limit + cache."""
    text = update.message.text.strip()
    user = update.effective_user

    # 🔒 v2.6.0: Rate limit check FIRST
    if RATE_LIMIT_AVAILABLE:
        allowed, retry_after = check_rate_limit(user.id)
        if not allowed:
            cooldown_msg = format_rate_limit_message(retry_after or 60)
            await update.message.reply_text(cooldown_msg, parse_mode="HTML")
            logger.info(f"🔒 Rate limit blocked user {user.id} for {retry_after}s")
            return

    progress = await update.message.reply_text("🔎 جاري البحث...")

    try:
        # 💾 v2.6.0: Check cache FIRST
        cached = get_cached_lookup(text) if CACHE_AVAILABLE else None
        if cached:
            logger.info(f"💾 Cache HIT for '{text}'")
            result_html = cached + "\n\n<i>⚡ نتيجة محفوظة (تسريع فوري)</i>"
        else:
            # Perform lookup (returns HTML string ready for Telegram)
            result_html = await lookup_tiktok_user(text)
            # 💾 Cache successful results (30 min)
            if CACHE_AVAILABLE and result_html and "فشل البحث" not in result_html:
                cache_lookup(text, result_html)
                logger.info(f"💾 Cache STORE for '{text}'")

        # Extract country name from HTML for DB logging
        country_detected = None
        try:
            import re
            m = re.search(r'الدولة:.*?<b>([^<]+)</b>', result_html)
            if m:
                country_detected = m.group(1).strip()
        except Exception:
            pass

        # Best-effort DB log (never blocks)
        if ANALYTICS_AVAILABLE:
            try:
                target_username = clean_username(text)
                record_search(
                    telegram_id=user.id,
                    target_username=target_username,
                    target_country=country_detected,
                    target_region=None,
                    followers=0,
                )
                logger.info(f"📊 recorded search: {user.id} → @{target_username} | {country_detected}")
            except Exception as e:
                logger.warning(f"📊 DB record_search skipped: {e}")

        # Send result as HTML (safer than Markdown - no _ escaping needed)
        try:
            await progress.edit_text(
                result_html,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except TelegramError as te:
            # If HTML fails, retry as plain text
            logger.warning(f"HTML parse failed, retrying as plain: {te}")
            plain = re.sub(r'<[^>]+>', '', result_html)
            await progress.edit_text(plain, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Lookup error for '{text}': {e}", exc_info=True)
        error_msg = (
            f"❌ <b>حدث خطأ أثناء البحث</b>\n\n"
            f"<code>{_html_escape(str(e)[:200])}</code>\n\n"
            f"💡 حاول مرة أخرى بعد قليل."
        )
        try:
            await progress.edit_text(error_msg, parse_mode="HTML")
        except Exception:
            await progress.edit_text("❌ حدث خطأ. حاول مرة أخرى.")


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only /stats command — show cache + rate limit statistics."""
    user = update.effective_user
    admin_env = os.getenv("ADMIN_USER_IDS", "").strip()
    admin_ids = [x.strip() for x in admin_env.split(",") if x.strip().isdigit()]

    if str(user.id) not in admin_ids:
        await update.message.reply_text("⛔ هذا الأمر للمشرفين فقط.")
        return

    cs = cache_stats() if CACHE_AVAILABLE else {"note": "cache disabled"}
    rls = rate_limit_stats() if RATE_LIMIT_AVAILABLE else {"note": "rate limit disabled"}

    msg = (
        "📊 <b>إحصائيات البوت v2.6.0</b>\n\n"
        "<b>💾 Cache Layer:</b>\n"
        f"  • الطلبات: <code>{cs.get('total_requests', 0)}</code>\n"
        f"  • Hits: <code>{cs.get('hits', 0)}</code>\n"
        f"  • Misses: <code>{cs.get('misses', 0)}</code>\n"
        f"  • معدل النجاح: <code>{cs.get('hit_rate_pct', 0)}%</code>\n"
        f"  • الحجم الحالي: <code>{cs.get('size', 0)}/{cs.get('max_size', 500)}</code>\n"
        f"  • TTL: <code>{cs.get('ttl_seconds', 1800)}s</code>\n\n"
        "<b>🔒 Rate Limiter:</b>\n"
        f"  • الطلبات الكلية: <code>{rls.get('total', 0)}</code>\n"
        f"  • مسموح: <code>{rls.get('allowed', 0)}</code>\n"
        f"  • محظور: <code>{rls.get('blocked', 0)}</code>\n"
        f"  • معدل الحظر: <code>{rls.get('block_rate_pct', 0)}%</code>\n"
        f"  • المستخدمون النشطون: <code>{rls.get('active_users', 0)}</code>\n"
        f"  • المشرفون: <code>{rls.get('admin_users', 0)}</code>\n"
        f"  • الحد: <code>{rls.get('max_requests_per_window', 10)}/{rls.get('window_seconds', 60)}s</code>\n"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    text = (
        "🆘 <b>قائمة الأوامر:</b>\n\n"
        "/start — بدء البوت\n"
        "/help — هذه القائمة\n"
        "/privacy — سياسة الخصوصية\n\n"
        "📌 <b>لإجراء بحث:</b>\n"
        "أرسل <code>@username</code> أو رابط TikTok"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /privacy command."""
    await update.message.reply_text(
        f"🔒 سياسة الخصوصية:\n{PRIVACY_POLICY_URL}"
    )


# ═══════════════════════════════════════════════════════════
# 🛡️ Global error handler (v2.4.0)
# ═══════════════════════════════════════════════════════════
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle uncaught exceptions gracefully."""
    err = context.error
    if isinstance(err, Conflict):
        logger.warning(f"⚠️ Telegram Conflict 409 - another instance running: {err}")
    elif isinstance(err, NetworkError):
        logger.warning(f"⚠️ Network error: {err}")
    else:
        logger.error(f"Unhandled error: {err}", exc_info=err)


# ═══════════════════════════════════════════════════════════
# 🔧 Helpers
# ═══════════════════════════════════════════════════════════
def _html_escape(text: str) -> str:
    if text is None:
        return ""
    import html
    return html.escape(str(text), quote=False)


# ═══════════════════════════════════════════════════════════
# 🚀 Main
# ═══════════════════════════════════════════════════════════
def main():
    _env_sanity_check()

    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير مُعرّف! توقف.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_lookup))

    # Global error handler (fixes Conflict 409 unhandled)
    app.add_error_handler(error_handler)

    logger.info(f"🚀 بوت بصير {BOT_USERNAME} v2.4.0 بدأ التشغيل")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,  # v2.4.0: prevent Conflict 409
    )


if __name__ == "__main__":
    main()
