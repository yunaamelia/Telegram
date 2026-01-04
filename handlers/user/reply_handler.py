"""
Reply keyboard message handler for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from utils.reply_keyboards import UserReplyKeyboard, AdminReplyKeyboard
from utils.messages import safe_edit_or_send
from database.db import Database
from utils.logger import get_logger

logger = get_logger("bot")


async def handle_reply_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reply keyboard button presses."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    user = update.effective_user
    db: Database = context.bot_data["db"]

    # Check if admin for admin keyboard handling
    is_admin = await db.is_admin(user.id)

    # Handle navigation buttons
    if text == "◀️ Prev":
        if is_admin:
            current_page = context.user_data.get("admin_kb_page", 1)
            new_page = max(1, current_page - 1)
            context.user_data["admin_kb_page"] = new_page
            await update.message.reply_text(
                f"📋 Admin Menu (Page {new_page}/{AdminReplyKeyboard.get_total_pages()})",
                reply_markup=AdminReplyKeyboard.build(new_page)
            )
        return

    if text == "Next ▶️":
        if is_admin:
            current_page = context.user_data.get("admin_kb_page", 1)
            new_page = min(AdminReplyKeyboard.get_total_pages(), current_page + 1)
            context.user_data["admin_kb_page"] = new_page
            await update.message.reply_text(
                f"📋 Admin Menu (Page {new_page}/{AdminReplyKeyboard.get_total_pages()})",
                reply_markup=AdminReplyKeyboard.build(new_page)
            )
        return

    if text == "🏠 Menu":
        from handlers.user.start import start_command
        await start_command(update, context)
        return

    # User keyboard handlers
    if text in UserReplyKeyboard.HANDLERS:
        action = UserReplyKeyboard.HANDLERS[text]

        if action == "show_products":
            from handlers.user.buy import show_products_command
            await show_products_command(update, context)

        elif action == "show_history":
            from handlers.user.history import history_command
            await history_command(update, context)

        elif action == "show_help":
            from handlers.user.help import help_command
            await help_command(update, context)

        elif action == "check_payment":
            await update.message.reply_text(
                "💳 Untuk cek status pembayaran, gunakan:\n"
                "`/cekbayar <order_id>`",
                parse_mode="MarkdownV2"
            )

        elif action == "request_refund":
            await update.message.reply_text(
                "🔄 Untuk request refund, buka /history dan pilih transaksi."
            )

        elif action == "show_main_menu":
            from handlers.user.start import start_command
            await start_command(update, context)

        return

    # Admin keyboard handlers
    if is_admin and text in AdminReplyKeyboard.HANDLERS:
        action = AdminReplyKeyboard.HANDLERS[text]

        # New UI Handlers
        if action == "dashboard":
            from handlers.admin.ui.dashboard import show_dashboard
            await show_dashboard(update, context)
            return

        # Direct Menu Mappings using AdminKeyboards
        from utils.admin_keyboards import AdminKeyboards

        if action == "system":
            await update.message.reply_text(
                "*⚙️ System & Settings*\n━━━━━━━━━━━━━━━━━━━━\n\n_Select action:_",
                parse_mode="MarkdownV2",
                reply_markup=AdminKeyboards.system_menu()
            )
            return

        if action == "transactions":
            await update.message.reply_text(
                "*💰 Transactions*\n━━━━━━━━━━━━━━━━━━━━\n\n_Select action:_",
                parse_mode="MarkdownV2",
                reply_markup=AdminKeyboards.transaction_management_menu()
            )
            return

        if action == "checkstock":
            await update.message.reply_text(
                "*📦 Stock Management*\n━━━━━━━━━━━━━━━━━━━━\n\n_Select action:_",
                parse_mode="MarkdownV2",
                reply_markup=AdminKeyboards.stock_management_menu()
            )
            return

        if action == "users":
            await update.message.reply_text(
                "*👥 User Management*\n━━━━━━━━━━━━━━━━━━━━\n\n_Select action:_",
                parse_mode="MarkdownV2",
                reply_markup=AdminKeyboards.user_management_menu()
            )
            return

        # Legacy/Other Commands fallback
        admin_commands = {
            "stats": "/stats",
            "security": "/security",
            "addadmin": "/addadmin",
            "backup": "/backup",
            "deleteproduct": "/deleteproduct",
            "listproducts": "/listproducts",
            "search": "/search",
            "reports": "/reports",
            "config": "/config",
            "api": "/api"
        }

        if action in admin_commands:
            await update.message.reply_text(
                f"Gunakan perintah: `{admin_commands[action]}`",
                parse_mode="MarkdownV2"
            )


# Handler for filtering reply keyboard messages
def get_reply_keyboard_filter():
    """Create filter for reply keyboard buttons."""
    all_buttons = (
        [btn for row in UserReplyKeyboard.BUTTONS for btn in row] +
        [btn for page in AdminReplyKeyboard.PAGES for btn in page] +
        ["◀️ Prev", "Next ▶️", "🏠 Menu"]
    )
    return filters.TEXT & filters.Regex(f"^({'|'.join(map(lambda x: x.replace('|', '\\|'), all_buttons))})$")


# Export handler
reply_keyboard_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    handle_reply_keyboard
)
