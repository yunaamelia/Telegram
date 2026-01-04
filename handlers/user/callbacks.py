"""
Central callback query handler for FRIENDS Store Telegram Bot.
Routes callbacks to appropriate handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from config import config
from utils.keyboards import Keyboards
from utils.formatters import format_welcome
from utils.messages import safe_edit_or_send
from utils.logger import get_logger

logger = get_logger("bot")


async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle navigation callbacks."""
    query = update.callback_query
    await query.answer()

    target = query.data.split(":")[1] if ":" in query.data else "main"
    user = update.effective_user

    if target == "main":
        await safe_edit_or_send(
            query, context, user.id,
            text=format_welcome(config.store.name, user.first_name),
            parse_mode="Markdown",
            reply_markup=Keyboards.main_menu()
        )
    # Other nav targets handled by their respective handlers


async def handle_noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle no-operation callbacks (like disabled buttons)."""
    query = update.callback_query
    await query.answer()


async def handle_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown callback queries."""
    query = update.callback_query
    logger.warning(f"Unknown callback: {query.data}")
    await query.answer("❓ Perintah tidak dikenal")


# Main navigation callback handler
callback_query_handler = CallbackQueryHandler(handle_navigation, pattern=r"^nav:main$")
noop_handler = CallbackQueryHandler(handle_noop, pattern=r"^noop$")

