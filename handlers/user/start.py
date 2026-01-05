"""
Start command and main menu handler for FRIENDS Store Telegram Bot.
"""

import os
from telegram import Update, BotCommand, BotCommandScopeChat
from telegram.ext import ContextTypes, CommandHandler

from config import config
from database.db import Database
from utils.keyboards import Keyboards
from utils.reply_keyboards import UserReplyKeyboard
from utils.admin_keyboards import AdminKeyboards
from utils.messages import safe_edit_or_send
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter
from utils.message_templates import MessageTemplates as msg
from utils.loading_states import loading

logger = get_logger("bot")


# User commands (5)
USER_COMMANDS = [
    BotCommand("start", "🏠 Menu Utama"),
    BotCommand("beli", "🛒 Beli Produk"),
    BotCommand("history", "📜 Riwayat Transaksi"),
    BotCommand("cekbayar", "💳 Cek Pembayaran"),
    BotCommand("help", "❓ Bantuan"),
]

# Admin commands (12)
ADMIN_COMMANDS = [
    BotCommand("addstock", "📦 Tambah Stock"),
    BotCommand("addproduct", "➕ Tambah Produk"),
    BotCommand("editproduct", "✏️ Edit Produk"),
    BotCommand("checkstock", "📋 Cek Stock"),
    BotCommand("deleteproduct", "🗑️ Hapus Produk"),
    BotCommand("listproducts", "📃 Daftar Produk"),
    BotCommand("transactions", "💰 Transaksi"),
    BotCommand("refunds", "💸 Refunds"),
    BotCommand("stats", "📊 Statistik"),
    BotCommand("security", "🔒 Keamanan"),
    BotCommand("addadmin", "👥 Tambah Admin"),
    BotCommand("broadcast", "📢 Broadcast"),
]


async def set_dynamic_commands(
    bot,
    user_id: int,
    is_admin: bool = False
) -> None:
    """Set dynamic commands for a specific user based on role."""
    try:
        scope = BotCommandScopeChat(chat_id=user_id)

        if is_admin:
            # Admin gets both user and admin commands
            commands = USER_COMMANDS + ADMIN_COMMANDS
        else:
            commands = USER_COMMANDS

        await bot.set_my_commands(commands, scope=scope)
        logger.debug(f"Set commands for user {user_id}, admin={is_admin}")
    except Exception as e:
        logger.warning(f"Failed to set commands for user {user_id}: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    db: Database = context.bot_data["db"]

    # Show typing indicator
    await loading.typing_indicator(update, context)

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
            msg.error(
                f"Kamu diblokir dari menggunakan bot ini.\nAlasan: {reason or 'Tidak disebutkan'}",
                f"Hubungi: @{config.bot.support_username}"
            )
        )
        return

    # Upsert user
    await db.upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # Check if admin
    is_admin = await db.is_admin(user.id)

    # Set dynamic commands based on role
    await set_dynamic_commands(context.bot, user.id, is_admin)

    # Choose reply keyboard based on role
    if is_admin:
        # New: Use AdminKeyboards for single-page admin menu
        reply_kb = AdminKeyboards.admin_reply_keyboard()
        role_text = "👑 𝐀𝐝𝐦𝐢𝐧 𝐌𝐨𝐝𝐞\n\n"
        # No more page tracking needed for admin reply keyboard
        context.user_data.pop("admin_kb_page", None)
    else:
        reply_kb = UserReplyKeyboard.build()
        role_text = ""

    # Send welcome message using new UI/UX templates
    welcome_text = msg.welcome(user.first_name, config.store.name)

    # Try to send logo if exists
    logo_path = config.store.logo_path
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"{role_text}{welcome_text}",
                    reply_markup=Keyboards.main_menu()  # Inline keyboard
                )
        except Exception as e:
            logger.warning(f"Failed to send logo: {e}")
            # Fallback to text with inline keyboard
            await update.message.reply_text(
                text=f"{role_text}{welcome_text}",
                reply_markup=Keyboards.main_menu()  # Inline keyboard
            )
    else:
        # Text only with inline keyboard
        await update.message.reply_text(
            text=f"{role_text}{welcome_text}",
            reply_markup=Keyboards.main_menu()  # Inline keyboard
        )

    # Send reply keyboard in separate message
    await update.message.reply_text(
        "⬇️ Gunakan menu di bawah untuk navigasi cepat:",
        reply_markup=reply_kb
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu (for callback query)."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    welcome_text = msg.welcome(user.first_name, config.store.name)

    await safe_edit_or_send(
        query, context, user.id,
        text=welcome_text,
        reply_markup=Keyboards.main_menu()
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command."""
    # Clear any conversation state
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Operasi dibatalkan.\n\n"
        "Gunakan /start untuk kembali ke menu utama.",
        parse_mode="MarkdownV2"
    )


# Handler exports
start_handler = CommandHandler("start", start_command)
main_menu_handler = CommandHandler("cancel", cancel_command)
