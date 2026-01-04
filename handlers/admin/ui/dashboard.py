"""
Admin dashboard UI handler.
Main entry point for admin interface.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler

from database.db import Database
from utils.admin_keyboards import AdminKeyboards
from utils.logger import get_logger

logger = get_logger("admin.ui")


async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show admin dashboard.
    
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
    
    # Check admin permission
    if not await db.is_admin(user.id):
        text = "⛔ Access denied\\. Admin only\\."
        if query:
            await query.edit_message_text(text, parse_mode="MarkdownV2")
        else:
            await update.message.reply_text(text, parse_mode="MarkdownV2")
        return
    
    # Get quick stats
    stats = await get_quick_stats(db)
    
    text = (
        "*🔐 Admin Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*📊 Quick Stats:*\n"
        f"👥 Users: `{stats.get('total_users', 0)}`\n"
        f"💰 Transactions: `{stats.get('total_transactions', 0)}`\n"
        f"📦 Products: `{stats.get('total_products', 0)}`\n"
        f"⚠️ Low Stock: `{stats.get('low_stock_count', 0)}`\n\n"
        "_Select category below:_"
    )
    
    keyboard = AdminKeyboards.main_dashboard()
    
    if query:
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard
        )


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
        "stock": (AdminKeyboards.stock_management_menu, "*📦 Stock Management*"),
        "products": (AdminKeyboards.product_management_menu, "*🛍️ Product Management*"),
        "transactions": (AdminKeyboards.transaction_management_menu, "*💰 Transactions*"),
        "users": (AdminKeyboards.user_management_menu, "*👥 User Management*"),
        "reports": (AdminKeyboards.reports_menu, "*📊 Reports \\& Analytics*"),
        "system": (AdminKeyboards.system_menu, "*⚙️ System \\& Settings*"),
    }
    
    if category not in menu_map:
        await query.answer("❌ Invalid category", show_alert=True)
        return
    
    keyboard_func, title = menu_map[category]
    
    text = f"{title}\n━━━━━━━━━━━━━━━━━━━━\n\n_Select action:_"
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard_func()
    )


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
    
    # Route to appropriate handler
    action_map = {
        "addstock": "admin:stock:add",
        "stats": "admin:system:stats",
        "trans": "admin:trans:all",
        "logs": "admin:system:logs",
        "backup": "admin:system:backup",
        "broadcast": "admin:system:broadcast",
        "toggle": "noop"  # Toggle quick actions visibility
    }
    
    if action == "toggle":
        # Just refresh dashboard for now
        await show_dashboard(update, context)
        return
    
    target = action_map.get(action)
    if target:
        # Update callback data and re-route
        query.data = target
        # Route to the appropriate handler based on target
        if target.startswith("admin:stock:"):
            from handlers.admin.ui.stock_ui import handle_stock_action
            await handle_stock_action(update, context)
        elif target.startswith("admin:system:"):
            from handlers.admin.ui.system_ui import handle_system_action
            await handle_system_action(update, context)
        elif target.startswith("admin:trans:"):
            from handlers.admin.ui.transaction_ui import handle_trans_action
            await handle_trans_action(update, context)


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
        "🏠 Menu": "admin:dashboard"
    }
    
    target = button_map.get(text)
    
    if target == "admin:dashboard":
        await show_dashboard(update, context)
    elif target:
        # Send message with appropriate menu
        await update.message.reply_text(
            "_Loading\\.\\.\\._",
            parse_mode="MarkdownV2"
        )
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
            "low_stock_count": low_stock_count
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
    CallbackQueryHandler(handle_noop, pattern=r"^noop$"),
]
