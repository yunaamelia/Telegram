"""
Reply keyboard message handler for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from utils.reply_keyboards import UserReplyKeyboard
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
                "`/cekbayar order_id`",
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

    # Admin keyboard handlers (AdminKeyboards.admin_reply_keyboard)
    if is_admin:
        # Mapping for Admin Quick Actions
        admin_actions = {
            "📦 +Stock": "addstock",
            "📊 Stats": "stats",
            "🔧 Logs": "logs",
            "💰 Trans": "transactions",
            "📢 BC": "broadcast",
            "🏠 Menu": "start" # Handled above, but kept for completeness in mapping thought
        }

        if text in admin_actions:
            action = admin_actions[text]

            # Direct Menu Mappings using AdminKeyboards
            from utils.admin_keyboards import AdminKeyboards

            if action == "addstock":
                 # Trigger Add Stock Wizard
                 from handlers.admin.wizards.stock_wizard import StockWizard
                 await StockWizard.start(update, context)
                 return

            if action == "stats":
                # Show stats using system menu logic or direct message
                from handlers.admin.ui.system_ui import show_statistics
                # show_statistics expects query, so we mimic message behavior
                # or just direct to system menu
                await update.message.reply_text(
                     "*📊 Statistics*\n━━━━━━━━━━━━━━━━━━━━\n\n_Use inline menu for details:_",
                     parse_mode="MarkdownV2",
                     reply_markup=AdminKeyboards.system_menu()
                )
                return

            if action == "logs":
                 await update.message.reply_text(
                    "*🔧 System Logs*\n━━━━━━━━━━━━━━━━━━━━\n\n"
                    "_Use `/logs` command to view logs\\._\n"
                    "_Use `/logs error` for error logs\\._",
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

            if action == "broadcast":
                 await update.message.reply_text(
                    "*📢 Broadcast Message*\n━━━━━━━━━━━━━━━━━━━━\n\n_Select target:_",
                    parse_mode="MarkdownV2",
                    reply_markup=AdminKeyboards.broadcast_targets()
                 )
                 return

            return


# Handler for filtering reply keyboard messages
def get_reply_keyboard_filter():
    """Create filter for reply keyboard buttons."""
    # User buttons
    user_buttons = [btn for row in UserReplyKeyboard.BUTTONS for btn in row]

    # Admin buttons (Hardcoded to match AdminKeyboards.admin_reply_keyboard)
    admin_buttons = [
        "📦 +Stock", "📊 Stats", "🔧 Logs",
        "💰 Trans", "📢 BC", "🏠 Menu"
    ]

    all_buttons = user_buttons + admin_buttons
    # Unique buttons only
    all_buttons = list(set(all_buttons))

    return filters.TEXT & filters.Regex(f"^({'|'.join(map(lambda x: x.replace('|', '\\|'), all_buttons))})$")


# Export handler
reply_keyboard_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    handle_reply_keyboard
)
