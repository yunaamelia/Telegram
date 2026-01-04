"""
Help center handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler

from config import config
from utils.keyboards import Keyboards
from utils.formatters import (
    format_help_order,
    format_help_payment,
    format_help_faq,
    format_help_contact
)
from utils.messages import safe_edit_or_send
from utils.logger import get_logger

logger = get_logger("bot")


HELP_MAIN = """
❓ *Pusat Bantuan*

Pilih kategori bantuan yang kamu butuhkan:
"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        text=HELP_MAIN,
        parse_mode="MarkdownV2",
        reply_markup=Keyboards.help_categories()
    )


async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help menu (callback)."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=HELP_MAIN,
        parse_mode="MarkdownV2",
        reply_markup=Keyboards.help_categories()
    )


async def show_help_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show order guide."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=format_help_order(),
        parse_mode="MarkdownV2",
        reply_markup=Keyboards.help_back()
    )


async def show_help_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show payment guide."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=format_help_payment(),
        parse_mode="MarkdownV2",
        reply_markup=Keyboards.help_back()
    )


async def show_help_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FAQ."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=format_help_faq(),
        parse_mode="MarkdownV2",
        reply_markup=Keyboards.help_back()
    )


async def show_help_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show contact info."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    await safe_edit_or_send(
        query, context, user.id,
        text=format_help_contact(config.bot.support_username),
        parse_mode="MarkdownV2",
        reply_markup=Keyboards.help_back()
    )


# Handler exports
help_handlers = [
    CommandHandler("help", help_command),
    CallbackQueryHandler(show_help_menu, pattern=r"^nav:help$"),
    CallbackQueryHandler(show_help_order, pattern=r"^help:order$"),
    CallbackQueryHandler(show_help_payment, pattern=r"^help:payment$"),
    CallbackQueryHandler(show_help_faq, pattern=r"^help:faq$"),
    CallbackQueryHandler(show_help_contact, pattern=r"^help:contact$"),
]

