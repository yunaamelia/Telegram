"""
Start command and main menu handler for FRIENDS Store Telegram Bot.
"""

import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import config
from database.db import Database
from utils.keyboards import Keyboards
from utils.formatters import format_welcome
from utils.messages import safe_edit_or_send
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger("bot")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    db: Database = context.bot_data["db"]

    # Check rate limit
    is_limited, wait_time = rate_limiter.check_rate_limit(user.id)
    if is_limited:
        await update.message.reply_text(
            f"⏳ Terlalu banyak request. Coba lagi dalam {wait_time} detik."
        )
        return

    # Check if banned
    is_banned, reason = await db.is_user_banned(user.id)
    if is_banned:
        await update.message.reply_text(
            f"⛔ Kamu diblokir dari menggunakan bot ini.\n"
            f"Alasan: {reason or 'Tidak disebutkan'}\n\n"
            f"Hubungi: @{config.bot.support_username}"
        )
        return

    # Upsert user
    await db.upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # Send welcome message
    welcome_text = format_welcome(config.store.name, user.first_name)

    # Try to send logo if exists
    logo_path = config.store.logo_path
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=welcome_text,
                    parse_mode="Markdown",
                    reply_markup=Keyboards.main_menu()
                )
                return
        except Exception as e:
            logger.warning(f"Failed to send logo: {e}")

    # Fallback to text only
    await update.message.reply_text(
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=Keyboards.main_menu()
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu (for callback query)."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    welcome_text = format_welcome(config.store.name, user.first_name)

    await safe_edit_or_send(
        query, context, user.id,
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=Keyboards.main_menu()
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command."""
    # Clear any conversation state
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Operasi dibatalkan.\n\n"
        "Gunakan /start untuk kembali ke menu utama.",
        parse_mode="Markdown"
    )


# Handler exports
start_handler = CommandHandler("start", start_command)
main_menu_handler = CommandHandler("cancel", cancel_command)

