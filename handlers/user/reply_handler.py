"""
Reply keyboard message handler for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from database.db import Database
from utils.logger import get_logger
from utils.reply_keyboards import UserReplyKeyboard
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

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
                f"💳 Untuk cek status pembayaran, gunakan:\n"
                f"{uf.monospace('/cekbayar order_id')}"
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
            "🏠 Menu": "start"  # Handled above, but kept for completeness
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
                text_msg = f"{vs.header('Statistics', '', icon='📊')}"
                text_msg += f"\n{uf.italic('Use inline menu for details:')}"
                await update.message.reply_text(
                    text_msg,
                    reply_markup=AdminKeyboards.system_menu()
                )
                return

            if action == "logs":
                text_msg = f"{vs.header('System Logs', '', icon='🔧')}"
                text_msg += f"\n{uf.italic('Use')} {uf.monospace('/logs')} {uf.italic('command to view logs.')}"
                text_msg += f"\n{uf.italic('Use')} {uf.monospace('/logs error')} {uf.italic('for error logs.')}"
                await update.message.reply_text(
                    text_msg,
                    reply_markup=AdminKeyboards.system_menu()
                )
                return

            if action == "transactions":
                text_msg = f"{vs.header('Transactions', '', icon='💰')}"
                text_msg += f"\n{uf.italic('Select action:')}"
                await update.message.reply_text(
                    text_msg,
                    reply_markup=AdminKeyboards.transaction_management_menu()
                )
                return

            if action == "broadcast":
                text_msg = f"{vs.header('Broadcast Message', '', icon='📢')}"
                text_msg += f"\n{uf.italic('Select target:')}"
                await update.message.reply_text(
                    text_msg,
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
