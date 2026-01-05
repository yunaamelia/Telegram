"""
Admin dashboard UI handler.
Main entry point for admin interface.
"""

from database.db import Database
from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from utils.admin_keyboards import AdminKeyboards
from utils.loading_states import loading
from utils.logger import get_logger
from utils.message_templates import MessageTemplates as msg
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

logger = get_logger("admin.ui")


async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, expanded: bool = False) -> None:
    """
    Show admin dashboard.

    Args:
        expanded: If True, show expanded quick actions

    Entry points:
    - Callback: admin:dashboard
    - Reply keyboard: 🏠 Menu
    - Command: /admin (fallback)
    """
    query = update.callback_query
    if query:
        await query.answer()

    user = update.effective_user
    db: Database = context.bot_data["db"]

    # Show typing indicator for command
    if not query:
        await loading.typing_indicator(update, context)

    # Check admin permission
    if not await db.is_admin(user.id):
        error_text = msg.error("Access denied", "Admin only")
        if query:
            await query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)
        return

    # Get quick stats
    stats = await get_quick_stats(db)

    # Use new UI/UX template
    text = msg.admin_dashboard(stats)

    keyboard = AdminKeyboards.main_dashboard(expanded=expanded)

    if query:
        await query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


async def show_category_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show specific category menu.
    Callback: admin:menu:<category>
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db: Database = context.bot_data["db"]

    # Check admin permission
    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return

    # Parse callback: admin:menu:stock
    category = query.data.split(":")[-1]

    menu_map = {
        "stock": (AdminKeyboards.stock_management_menu, "📦 Stock Management"),
        "products": (AdminKeyboards.product_management_menu, "🛍️ Product Management"),
        "transactions": (AdminKeyboards.transaction_management_menu, "💰 Transactions"),
        "users": (AdminKeyboards.user_management_menu, "👥 User Management"),
        "reports": (AdminKeyboards.reports_menu, "📊 Reports & Analytics"),
        "system": (AdminKeyboards.system_menu, "⚙️ System & Settings"),
    }

    if category not in menu_map:
        await query.answer("❌ Invalid category", show_alert=True)
        return

    keyboard_func, title = menu_map[category]

    text = f"{vs.header(title, '', icon='')}"
    text += f"\n{uf.italic('Select action:')}"

    await query.edit_message_text(text, reply_markup=keyboard_func())


async def handle_quick_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle quick action buttons.
    Callback: admin:quick:<action>
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return

    # Parse callback: admin:quick:addstock
    action = query.data.split(":")[-1]

    # Handle expand/collapse
    if action == "expand":
        await show_dashboard(update, context, expanded=True)
        return

    if action == "collapse":
        await show_dashboard(update, context, expanded=False)
        return

    # Route to appropriate handler
    action_map = {
        "addstock": "admin:stock:add",
        "stats": "admin:system:stats",
        "trans": "admin:trans:all",
        "logs": "admin:system:logs",
        "backup": "admin:system:backup",
        "broadcast": "admin:system:broadcast",
    }

    target = action_map.get(action)
    if target:
        # Store target action in context for routing
        context.user_data["_quick_action_target"] = target

        # Route to the appropriate handler based on target
        if target.startswith("admin:stock:"):
            from handlers.admin.ui.stock_ui import show_add_stock_form

            await show_add_stock_form(update, context)
        elif target.startswith("admin:system:"):
            from handlers.admin.ui.system_ui import handle_system_action

            # Create a mock data for the handler
            context.user_data["_callback_data"] = target
            await handle_system_action(update, context)
        elif target.startswith("admin:trans:"):
            from handlers.admin.ui.transaction_ui import show_all_transactions

            await show_all_transactions(update, context)

        # Clean up
        context.user_data.pop("_quick_action_target", None)
        context.user_data.pop("_callback_data", None)


async def handle_fullmenu_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle full menu toggle - show all categories inline."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return

    keyboard = AdminKeyboards.main_dashboard_full()

    text = f"{vs.header('Full Menu', '', icon='📂')}"
    text += f"\n{uf.italic('All categories:')}"
    await query.edit_message_text(text, reply_markup=keyboard)


async def handle_noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle noop callbacks (dividers, headers)."""
    query = update.callback_query
    await query.answer()


async def handle_admin_reply_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle admin reply keyboard button presses.
    Maps button text to appropriate action.
    """
    text = update.message.text
    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_admin(user.id):
        return  # Silently ignore non-admin

    button_map = {
        "📦 +Stock": "admin:stock:add",
        "📊 Stats": "admin:system:stats",
        "🔧 Logs": "admin:system:logs",
        "💰 Trans": "admin:trans:all",
        "📢 BC": "admin:system:broadcast",
        "🏠 Menu": "admin:dashboard",
    }

    target = button_map.get(text)

    if target == "admin:dashboard":
        await show_dashboard(update, context)
    elif target:
        # Send message with appropriate menu
        await update.message.reply_text(f"{uf.italic('Loading...')}")
        # The actual handler will be called via callback


async def get_quick_stats(db: Database) -> dict:
    """Get quick statistics for dashboard."""
    try:
        total_users = await db.get_user_count()
        total_products = len(await db.get_all_products())

        # Count transactions by status
        transactions = await db.get_all_transactions(limit=1000)
        total_transactions = len(transactions)

        # Count low stock products
        products = await db.get_active_products()
        low_stock_count = 0
        for product in products:
            stock_count = await db.get_available_stock_count(product["product_code"])
            if stock_count < 5:
                low_stock_count += 1

        return {
            "total_users": total_users,
            "total_products": total_products,
            "total_transactions": total_transactions,
            "low_stock_count": low_stock_count,
        }
    except Exception as e:
        logger.error(f"Failed to get quick stats: {e}")
        return {}


# Command handler for /admin
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command - show dashboard."""
    await show_dashboard(update, context)


# Handler exports
dashboard_handlers = [
    CommandHandler("admin", admin_command),
    CallbackQueryHandler(show_dashboard, pattern=r"^admin:dashboard$"),
    CallbackQueryHandler(show_category_menu, pattern=r"^admin:menu:"),
    CallbackQueryHandler(handle_quick_action, pattern=r"^admin:quick:"),
    CallbackQueryHandler(handle_fullmenu_toggle, pattern=r"^admin:fullmenu:toggle$"),
    CallbackQueryHandler(handle_noop, pattern=r"^noop$"),
]
