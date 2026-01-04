"""
Broadcast handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from database.db import Database
from services.notification import NotificationService
from utils.keyboards import Keyboards
from utils.formatters import escape_md
from utils.logger import get_logger

logger = get_logger("admin")

# Conversation states
SELECT_TARGET, INPUT_MESSAGE, CONFIRM = range(3)


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is an admin."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    return await db.is_admin(user.id)


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start broadcast wizard."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📢 *Broadcast Message*\n\n"
        "Pilih target audience:",
        parse_mode="MarkdownV2",
        reply_markup=Keyboards.broadcast_targets()
    )
    return SELECT_TARGET


async def select_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle target selection."""
    query = update.callback_query
    await query.answer()

    if query.data == "admin:cancel":
        await query.edit_message_text("❌ Broadcast dibatalkan.")
        return ConversationHandler.END

    # Extract target
    target = query.data.split(":")[-1]
    context.user_data["broadcast_target"] = target

    target_name = {
        "all": "Semua User",
        "buyers": "Buyers Only",
        "active_7days": "Active 7 Days"
    }.get(target, target)

    await query.edit_message_text(
        f"📢 Target: *{escape_md(target_name)}*\n\n"
        "Masukkan pesan broadcast:\n"
        "\(Bisa juga kirim foto/dokumen dengan caption\)\n\n"
        "Ketik /cancel untuk membatalkan\.",
        parse_mode="MarkdownV2"
    )
    return INPUT_MESSAGE


async def input_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive broadcast message."""
    media_type = "text"
    media_file_id = None
    message_text = ""

    if update.message.photo:
        media_type = "photo"
        media_file_id = update.message.photo[-1].file_id
        message_text = update.message.caption or ""
    elif update.message.document:
        media_type = "document"
        media_file_id = update.message.document.file_id
        message_text = update.message.caption or ""
    else:
        message_text = update.message.text

    context.user_data["broadcast_message"] = message_text
    context.user_data["broadcast_media_type"] = media_type
    context.user_data["broadcast_media_file_id"] = media_file_id

    target = context.user_data.get("broadcast_target", "all")

    db: Database = context.bot_data["db"]
    users = await db.get_users_by_filter(target)

    await update.message.reply_text(
        f"📢 *Preview Broadcast*\n\n"
        f"Target: {escape_md(target)} \({len(users)} users\)\n"
        f"Media: {escape_md(media_type)}\n\n"
        f"*Message:*\n{escape_md(message_text[:500])}\n\n"
        "Ketik `CONFIRM` untuk mengirim atau /cancel untuk batal\.",
        parse_mode="MarkdownV2"
    )
    return CONFIRM


async def confirm_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and send broadcast."""
    if update.message.text.upper() != "CONFIRM":
        await update.message.reply_text("Ketik `CONFIRM` untuk mengirim atau /cancel untuk batal.")
        return CONFIRM

    target = context.user_data.get("broadcast_target", "all")
    message = context.user_data.get("broadcast_message", "")
    media_type = context.user_data.get("broadcast_media_type", "text")
    media_file_id = context.user_data.get("broadcast_media_file_id")

    db: Database = context.bot_data["db"]
    notification = NotificationService(context.bot, db)

    await update.message.reply_text("⏳ Mengirim broadcast...")

    sent, failed = await notification.broadcast_message(
        message=message,
        target=target,
        media_type=media_type,
        media_file_id=media_file_id
    )

    # Save to database
    await db.create_broadcast(
        message_text=message,
        created_by=update.effective_user.id,
        media_type=media_type,
        media_file_id=media_file_id,
        target_audience=target
    )

    await update.message.reply_text(
        f"✅ *Broadcast Selesai\!*\n\n"
        f"📤 Terkirim: `{sent}`\n"
        f"❌ Gagal: `{failed}`",
        parse_mode="MarkdownV2"
    )
    logger.info(f"Broadcast sent: target={target}, sent={sent}, failed={failed}, by={update.effective_user.id}")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel broadcast."""
    context.user_data.clear()
    await update.message.reply_text("❌ Broadcast dibatalkan.")
    return ConversationHandler.END


# Conversation handler
broadcast_conversation = ConversationHandler(
    entry_points=[CommandHandler("broadcast", broadcast_start)],
    states={
        SELECT_TARGET: [CallbackQueryHandler(select_target, pattern=r"^admin:broadcast")],
        INPUT_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_message),
            MessageHandler(filters.PHOTO, input_message),
            MessageHandler(filters.Document.ALL, input_message),
        ],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_broadcast)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
    per_chat=False,
)

# Handler exports
broadcast_handlers = [broadcast_conversation]
