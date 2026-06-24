# ═══════════════════════════════════════════════════════════
# BSR-V217L-BOT-MAIN-AHMAD-20260613
# بوت بصير الرئيسي — مع كسر القيد #21 (موافقة صريحة)
# ═══════════════════════════════════════════════════════════
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config
import user_storage
import country_detector
from consent_message import CONSENT_TEXT, WELCOME_AFTER_CONSENT, CONSENT_DENIED

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("baseer_bot")


# ────────────────────── /start ──────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user_storage.has_consented(user.id):
        country = country_detector.detect_from_language(user.language_code or "")
        user_storage.update_activity(user.id, country)
        await update.message.reply_text(
            WELCOME_AFTER_CONSENT.format(name=user.first_name or "—"),
            parse_mode="HTML",
        )
        return

    keyboard = [
        [InlineKeyboardButton("✅ أوافق وأكمل", callback_data="consent_yes")],
        [InlineKeyboardButton("❌ أرفض",        callback_data="consent_no")],
        [InlineKeyboardButton("📄 سياسة الخصوصية", url=config.PRIVACY_POLICY_URL)],
    ]
    await update.message.reply_text(
        CONSENT_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


# ────────────────────── Consent Callback ──────────────────────
async def consent_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "consent_yes":
        country = country_detector.detect_from_language(user.language_code or "")
        user_storage.record_consent(user.id, user.username, user.language_code)
        user_storage.update_activity(user.id, country)
        await query.edit_message_text(
            WELCOME_AFTER_CONSENT.format(name=user.first_name or "—"),
            parse_mode="HTML",
        )
        logger.info(f"CONSENT_GIVEN user_id={user.id} country={country}")
    else:
        await query.edit_message_text(CONSENT_DENIED)
        logger.info(f"CONSENT_DENIED user_id={user.id}")


# ────────────────────── /forget_me (GDPR Article 17) ──────────────────────
async def forget_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ok = user_storage.forget_user(user.id)
    msg = "✅ تمّ حذف بياناتك بالكامل." if ok else "ℹ️ لا توجد بيانات مخزّنة."
    await update.message.reply_text(msg)
    logger.info(f"FORGET_ME user_id={user.id} ok={ok}")


# ────────────────────── /my_data (GDPR Article 15) ──────────────────────
async def my_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = user_storage.get_user(user.id)
    if not data:
        await update.message.reply_text("ℹ️ لا توجد بيانات مخزّنة.")
        return
    msg = (
        f"<b>📋 بياناتك المُخزَّنة:</b>\n\n"
        f"• المعرّف: <code>{data['user_id']}</code>\n"
        f"• اسم المستخدم: {data.get('username', '—')}\n"
        f"• الدولة: {data.get('country', '—')}\n"
        f"• الاستعلامات: {data.get('total_queries', 0)}\n"
        f"• تاريخ الموافقة: {data.get('consent_timestamp', '—')}\n"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


# ────────────────────── /help ──────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>📘 أوامر بوت بصير:</b>\n\n"
        "• <code>/start</code> — البدء + شاشة الموافقة\n"
        "• <code>/help</code> — هذه القائمة\n"
        "• <code>/my_data</code> — عرض بياناتك (GDPR Art.15)\n"
        "• <code>/forget_me</code> — حذف بياناتك (GDPR Art.17)\n"
        "• <code>/privacy</code> — رابط سياسة الخصوصية\n"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def privacy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📄 سياسة الخصوصية:\n{config.PRIVACY_POLICY_URL}"
    )


# ────────────────────── Main ──────────────────────
def main():
    token = config.BOT_TOKEN
    if not token or token == "TEST_TOKEN":
        logger.error("❌ BOT_TOKEN غير مُعرَّف في .env")
        raise SystemExit(1)

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("forget_me", forget_me))
    app.add_handler(CommandHandler("my_data", my_data))
    app.add_handler(CommandHandler("privacy", privacy_cmd))
    app.add_handler(CallbackQueryHandler(consent_callback, pattern="^consent_"))

    logger.info(f"🚀 بوت بصير {config.BOT_USERNAME} بدأ التشغيل")
    app.run_polling()


if __name__ == "__main__":
    main()
