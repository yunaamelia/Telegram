"""
Confirmation handler for admin actions.
"""

from database.db import Database
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from utils.admin_keyboards import AdminKeyboards
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf

logger = get_logger("admin.confirm")


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle confirmation callbacks.
    Pattern: admin:confirm:<action>:<item_id>
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return

    # Parse: admin:confirm:product:delete:product_code
    parts = query.data.split(":")
    action = parts[2] if len(parts) > 2 else None

    if action == "product:delete":
        product_code = parts[3] if len(parts) > 3 else None
        await execute_product_delete(query, context, product_code)
    elif action == "stock:delete":
        stock_id = int(parts[3]) if len(parts) > 3 else None
        await execute_stock_delete(query, context, stock_id)


async def execute_product_delete(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Execute product deletion (deactivation)."""
    db: Database = context.bot_data["db"]

    product = await db.get_product(product_code)
    if not product:
        await query.edit_message_text("❌ Product not found.")
        return

    try:
        await db.update_product(product_code, {"is_active": False})

        text = f"""
✅ {uf.bold('Product Deactivated')}

{uf.italic(product['name'])} has been deactivated.
Stock items are preserved.
"""
        await query.edit_message_text(text, reply_markup=AdminKeyboards.product_management_menu())

        logger.info(f"Product deactivated: {product_code} by {query.from_user.id}")

    except Exception as e:
        logger.error(f"Failed to delete product: {e}")
        await query.edit_message_text(f"❌ Error: {e}")


async def execute_stock_delete(query, context: ContextTypes.DEFAULT_TYPE, stock_id: int) -> None:
    """Execute stock deletion."""
    db: Database = context.bot_data["db"]

    try:
        stock = await db.get_stock_by_id(stock_id)
        if not stock:
            await query.edit_message_text("❌ Stock item not found.")
            return

        await db.delete_stock_item(stock_id)

        text = f"""
✅ {uf.bold('Stock Item Deleted')}

{uf.italic('The stock item has been removed.')}
"""
        await query.edit_message_text(text, reply_markup=AdminKeyboards.stock_management_menu())

        logger.info(f"Stock deleted: {stock_id} by {query.from_user.id}")

    except Exception as e:
        logger.error(f"Failed to delete stock: {e}")
        await query.edit_message_text(f"❌ Error: {e}")


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel callbacks."""
    query = update.callback_query
    await query.answer("Cancelled")

    # Return to dashboard
    from handlers.admin.ui.dashboard import show_dashboard

    await show_dashboard(update, context)


# Handler exports
confirmation_handlers = [
    CallbackQueryHandler(handle_confirmation, pattern=r"^admin:confirm:"),
    CallbackQueryHandler(handle_cancel, pattern=r"^admin:cancel:"),
]
