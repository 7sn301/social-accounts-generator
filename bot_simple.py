# ═══════════════════════════════════════════════════════════
# BSR-V217L-BOT-SIMPLE-NO-CRASH-AHMAD-20260613
# نسخة مبسّطة بدون استيرادات معقّدة — تتجاوز مشاكل Runtime
# ═══════════════════════════════════════════════════════════
"""
Baseer_Lookup_Bot — Simplified Version
- بدون user_storage / config المعقّدة
- يقرأ المتغيّرات مباشرة من البيئة (Railway env vars)
- TikTok lookup مع كشف 200+ دولة
- RTL + Noto Sans Arabic في المخرجات
"""
import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from tiktok_lookup import lookup_tiktok_user

# ─────────────────────────────────────────────────────────────
# قراءة متغيّرات البيئة مباشرة (لا حاجة لـ config.py)
# ─────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────
# /start — ترحيب RTL بدون شاشة موافقة
# ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome = (
        f"👋 مرحبًا {user.first_name}!\n\n"
        f"🔍 *بوت بصير — TikTok Lookup*\n\n"
        f"أرسل اسم مستخدم TikTok أو رابط حساب وسأعرض لك:\n"
        f"  • 👤 معلومات الحساب\n"
        f"  • 🌍 دولة الحساب (200+ دولة)\n"
        f"  • 📊 الإحصائيات الكاملة\n\n"
        f"مثال: `@charlidamelio` أو `https://www.tiktok.com/@charlidamelio`"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────
# معالج الرسائل النصية — TikTok Lookup مباشر
# ─────────────────────────────────────────────────────────────
async def handle_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    progress = await update.message.reply_text("🔎 جاري البحث... انتظر لحظة.")
    try:
        result = await lookup_tiktok_user(text)
        await progress.edit_text(
            result,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
    except Exception as e:
        logger.error(f"Lookup error: {e}")
        await progress.edit_text("❌ حدث خطأ أثناء البحث. حاول مرة أخرى.")


# ─────────────────────────────────────────────────────────────
# /help — قائمة مختصرة
# ─────────────────────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 *قائمة الأوامر:*\n\n"
        "/start — بدء البوت\n"
        "/help — هذه القائمة\n"
        "/privacy — سياسة الخصوصية\n\n"
        "📌 لإجراء بحث: أرسل @username أو رابط TikTok"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────
# /privacy
# ─────────────────────────────────────────────────────────────
async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🔒 سياسة الخصوصية:\n{PRIVACY_POLICY_URL}"
    )


def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير مُعرّف! أوقفت التشغيل.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_lookup))

    logger.info(f"🚀 بوت بصير {BOT_USERNAME} بدأ التشغيل")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
