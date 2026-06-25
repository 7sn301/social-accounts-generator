# ═══════════════════════════════════════════════════════════
# BSR-V2189-BOT-PARAMS-FIXED-AHMAD-20260613
# بوت بصير v2.1.8.9 - تصحيح معاملات record_user_start و record_search
# ═══════════════════════════════════════════════════════════
"""Baseer_Lookup_Bot v2.1.8.9 — تسجيل صحيح للمستخدمين والبحثات"""
import os
import logging
import httpx
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from tiktok_lookup import lookup_tiktok_user, clean_username
from analytics_db import record_user_start, record_search

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "Baseer_Lookup_Bot")
PRIVACY_POLICY_URL = os.getenv(
    "PRIVACY_POLICY_URL",
    "https://github.com/7sn301/social-accounts-generator/blob/main/PRIVACY.md"
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def get_ip_geolocation(ip):
    """جلب الموقع من IP عبر ipapi.co (مجاني)"""
    if not ip or ip in ("0.0.0.0", "127.0.0.1", "TELEGRAM_HIDDEN"):
        return {'country': None, 'city': None, 'isp': None}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"https://ipapi.co/{ip}/json/")
            if r.status_code == 200:
                d = r.json()
                return {
                    'country': d.get('country_name'),
                    'city': d.get('city'),
                    'isp': d.get('org'),
                }
    except Exception as e:
        logger.warning(f"ipapi failed: {e}")
    return {'country': None, 'city': None, 'isp': None}


async def extract_user_ip(update: Update):
    """Telegram لا يكشف IP الفعلي — placeholder"""
    return "TELEGRAM_HIDDEN"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    language_code = user.language_code or ""

    ip = await extract_user_ip(update)
    geo = await get_ip_geolocation(ip)

    # ✅ FIX: استخدم الأسماء الصحيحة من analytics_db.py
    try:
        record_user_start(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            ip=ip,                      # ✅ ip (not ip_address)
            country=geo.get('country'),
            city=geo.get('city'),
            # ❌ removed: isp=... (not supported)
        )
        logger.info(f"📊 سجّلت /start: {telegram_id} @{username} | {geo.get('country')}")
    except Exception as e:
        logger.error(f"❌ فشل تسجيل المستخدم: {e}")

    welcome = (
        f"👋 مرحبًا {first_name}!\n\n"
        f"🔍 *بوت بصير — TikTok Lookup*\n\n"
        f"أرسل اسم مستخدم TikTok أو رابط حساب وسأعرض لك:\n"
        f"  • 👤 معلومات الحساب\n"
        f"  • 🌍 دولة الحساب (220+ دولة)\n"
        f"  • 📊 الإحصائيات الكاملة\n\n"
        f"مثال: `@charlidamelio`"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def handle_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user
    progress = await update.message.reply_text("🔎 جاري البحث...")
    target_country_detected = None
    try:
        result = await lookup_tiktok_user(text)

        # ✅ محاولة استخراج رمز الدولة من النتيجة
        try:
            import re
            country_match = re.search(r'🌍\s*\*?الدولة\*?:?\s*([^\n]+)', result)
            if country_match:
                target_country_detected = country_match.group(1).strip()
        except Exception:
            pass

        # ✅ FIX: استخدم الأسماء الصحيحة من analytics_db.py
        try:
            target_username = clean_username(text)
            record_search(
                telegram_id=user.id,
                target_username=target_username,    # ✅ target_username (not search_query)
                target_country=target_country_detected,  # ✅ target_country (not result_country)
                target_region=None,
                followers=0,
            )
            logger.info(f"📊 سجّلت بحث: {user.id} → @{target_username} | {target_country_detected}")
        except Exception as e:
            logger.error(f"❌ فشل تسجيل البحث: {e}")

        await progress.edit_text(
            result, parse_mode="Markdown", disable_web_page_preview=False
        )
    except Exception as e:
        logger.error(f"Lookup error: {e}")
        await progress.edit_text("❌ حدث خطأ. حاول مرة أخرى.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 *قائمة الأوامر:*\n\n"
        "/start — بدء البوت\n"
        "/help — هذه القائمة\n"
        "/privacy — سياسة الخصوصية\n\n"
        "📌 لإجراء بحث: أرسل @username أو رابط TikTok",
        parse_mode="Markdown"
    )


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🔒 سياسة الخصوصية:\n{PRIVACY_POLICY_URL}"
    )


def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير مُعرّف!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_lookup))
    logger.info(f"🚀 بوت بصير {BOT_USERNAME} v2.1.8.9 بدأ التشغيل")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
