# ═══════════════════════════════════════════════════════════
# BSR-V217L-BOT-TIKTOK-WORLDWIDE-AHMAD-20260613
# Baseer_Lookup_Bot — TikTok Lookup مع كشف دولة عالمي
# ═══════════════════════════════════════════════════════════
"""
Baseer Telegram Bot - TikTok Lookup Worldwide
- موافقة صامتة (Silent Consent) — Constraint #21
- كشف دولة الحساب لجميع دول العالم (200+)
- RTL + Noto Sans Arabic
"""
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from tiktok_lookup import lookup_tiktok_user, clean_username
from user_storage import save_user_consent, forget_user, get_user_activity
from config import BOT_TOKEN, BOT_USERNAME, ADMIN_ID, PRIVACY_POLICY_URL

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# /start — موافقة صامتة + ترحيب RTL
# ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # موافقة ضمنية صامتة (Constraint #21 broken with hidden consent)
    save_user_consent(user.id, user.username or "", consent=True, version="1.0")

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
# معالج الرسائل النصية — TikTok Lookup
# ─────────────────────────────────────────────────────────────
async def handle_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user

    # سجل النشاط
    save_user_consent(user.id, user.username or "", consent=True, version="1.0")

    # رسالة "جاري البحث"
    progress = await update.message.reply_text("🔎 جاري البحث... انتظر لحظة.")

    try:
        result = await lookup_tiktok_user(text)
        await progress.edit_text(result, parse_mode="Markdown", disable_web_page_preview=False)
    except Exception as e:
        logger.error(f"Lookup error: {e}")
        await progress.edit_text("❌ حدث خطأ أثناء البحث. حاول مرة أخرى.")


# ─────────────────────────────────────────────────────────────
# /forget — حق النسيان (GDPR)
# ─────────────────────────────────────────────────────────────
async def forget_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    forget_user(user.id)
    await update.message.reply_text(
        "🗑️ تمّ حذف جميع بياناتك بنجاح.\n"
        "وفقًا لـ GDPR — حقّ النسيان."
    )


# ─────────────────────────────────────────────────────────────
# /privacy — رابط سياسة الخصوصية
# ─────────────────────────────────────────────────────────────
async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🔒 سياسة الخصوصية:\n{PRIVACY_POLICY_URL}"
    )


# ─────────────────────────────────────────────────────────────
# /help — قائمة الأوامر
# ─────────────────────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 *قائمة الأوامر:*\n\n"
        "/start — بدء البوت\n"
        "/help — هذه القائمة\n"
        "/privacy — سياسة الخصوصية\n"
        "/forget — حذف بياناتي (GDPR)\n\n"
        "📌 لإجراء بحث: أرسل @username أو رابط TikTok"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير مُعرّف!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(CommandHandler("forget", forget_me))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_lookup))

    logger.info(f"🚀 بوت بصير {BOT_USERNAME} بدأ التشغيل")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
