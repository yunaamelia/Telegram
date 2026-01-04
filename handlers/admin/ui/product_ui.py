"""
Product management UI handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from database.db import Database
from utils.admin_keyboards import AdminKeyboards
from utils.formatters import format_currency, escape_md
from utils.logger import get_logger

logger = get_logger("admin.product_ui")


async def handle_product_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Route product-related callback queries.
    Pattern: admin:product:<action>
    """
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db: Database = context.bot_data["db"]
    
    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    # Parse: admin:product:list or admin:product:view:code:page
    parts = query.data.split(":")
    action = parts[2] if len(parts) > 2 else None
    
    if action == "list":
        # admin:product:list:page:context
        page = int(parts[3]) if len(parts) > 3 else 1
        ctx = parts[4] if len(parts) > 4 else "view"
        await show_product_list(query, context, page, ctx)
    elif action == "view":
        # admin:product:view:product_code:page
        product_code = parts[3] if len(parts) > 3 else None
        await show_product_detail(query, context, product_code)
    elif action == "edit":
        product_code = parts[3] if len(parts) > 3 else None
        await show_edit_options(query, context, product_code)
    elif action == "delete":
        product_code = parts[3] if len(parts) > 3 else None
        await confirm_delete_product(query, context, product_code)
    elif action == "toggle":
        product_code = parts[3] if len(parts) > 3 else None
        await toggle_product_active(query, context, product_code)
    elif action == "details":
        product_code = parts[3] if len(parts) > 3 else None
        await show_product_stats(query, context, product_code)
    elif action == "bulkprice":
        await show_bulk_price_info(query, context)
    elif action == "add":
        # Redirect to wizard - this is handled by product_wizard
        pass
    elif action == "addstock":
        # Redirect to stock wizard with product code
        product_code = parts[3] if len(parts) > 3 else None
        from handlers.admin.ui.stock_ui import show_add_stock_form
        await show_add_stock_form(query, context, product_code)


async def show_product_list(query, context: ContextTypes.DEFAULT_TYPE, page: int = 1, ctx: str = "view") -> None:
    """Show paginated product list."""
    db: Database = context.bot_data["db"]
    products = await db.get_all_products()
    
    if not products:
        await query.edit_message_text(
            "*🛍️ Product List*\n\n_No products found\\._",
            parse_mode="MarkdownV2",
            reply_markup=AdminKeyboards.product_management_menu()
        )
        return
    
    # Paginate
    items_per_page = 6
    total_pages = max(1, (len(products) + items_per_page - 1) // items_per_page)
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_products = products[start_idx:end_idx]
    
    ctx_titles = {
        "view": "📋 View",
        "edit": "✏️ Edit",
        "delete": "🗑️ Delete",
        "addstock": "📦 Add Stock"
    }
    title = ctx_titles.get(ctx, "📋 View")
    
    lines = [
        f"*🛍️ Product List* \\- {title}",
        f"_Page {page}/{total_pages} \\| Total: {len(products)}_\n"
    ]
    
    for idx, product in enumerate(page_products, 1):
        name = escape_md(product['name'])
        code = escape_md(product['product_code'])
        price = escape_md(format_currency(product['price']))
        status = "🟢" if product.get('is_active', True) else "🔴"
        
        stock_count = await db.get_available_stock_count(product['product_code'])
        stock_indicator = "⚠️" if stock_count < 5 else ""
        
        lines.append(f"*{idx}\\.* {status} __{name}__")
        lines.append(f"   `{code}` \\| 💰 `{price}`")
        lines.append(f"   📊 Stock: *{stock_count}* {stock_indicator}\n")
    
    text = "\n".join(lines)
    keyboard = AdminKeyboards.product_list(products, page, items_per_page, ctx)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )


async def show_product_detail(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Show product detail with actions."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)
    
    if not product:
        await query.edit_message_text(
            "❌ Product not found\\.",
            parse_mode="MarkdownV2",
            reply_markup=AdminKeyboards.product_management_menu()
        )
        return
    
    stock_count = await db.get_available_stock_count(product_code)
    
    name = escape_md(product['name'])
    code = escape_md(product['product_code'])
    price = escape_md(format_currency(product['price']))
    desc = escape_md(product.get('description', 'No description'))
    status = "🟢 Active" if product.get('is_active', True) else "🔴 Inactive"
    stock_status = "⚠️" if stock_count < 5 else "✅" if stock_count > 0 else "❌"
    
    text = (
        f"*🛍️ {name}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*Code:* `{code}`\n"
        f"*Price:* `{price}`\n"
        f"*Status:* {status}\n"
        f"*Stock:* `{stock_count}` {stock_status}\n\n"
        f"*Description:*\n_{desc}_"
    )
    
    keyboard = AdminKeyboards.product_detail(product_code, stock_count > 0)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )


async def show_edit_options(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Show edit options for a product."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)
    
    if not product:
        await query.edit_message_text("❌ Product not found\\.", parse_mode="MarkdownV2")
        return
    
    name = escape_md(product['name'])
    
    text = (
        f"*✏️ Edit Product: {name}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Use commands to edit:_\n\n"
        f"`/editproduct {product_code} name <new_name>`\n"
        f"`/editproduct {product_code} price <amount>`\n"
        f"`/editproduct {product_code} description <text>`\n"
        f"`/editproduct {product_code} active true/false`"
    )
    
    keyboard = AdminKeyboards.product_detail(product_code)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )


async def confirm_delete_product(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Confirm product deletion."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)
    
    if not product:
        await query.edit_message_text("❌ Product not found\\.", parse_mode="MarkdownV2")
        return
    
    name = escape_md(product['name'])
    stock_count = await db.get_available_stock_count(product_code)
    
    text = (
        f"*⚠️ Delete Product: {name}?*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 *Stock items:* `{stock_count}`\n\n"
        "_This will deactivate the product\\._\n"
        "_Stock items will be preserved\\._"
    )
    
    keyboard = AdminKeyboards.confirmation("product:delete", product_code, f"admin:product:view:{product_code}:1")
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )


async def toggle_product_active(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Toggle product active status."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)
    
    if not product:
        await query.edit_message_text("❌ Product not found\\.", parse_mode="MarkdownV2")
        return
    
    # Toggle status
    new_status = not product.get('is_active', True)
    await db.update_product(product_code, {"is_active": new_status})
    
    status_text = "diaktifkan ✅" if new_status else "dinonaktifkan 🔴"
    name = escape_md(product['name'])
    
    await query.answer(f"Product {status_text}", show_alert=True)
    
    # Refresh detail view
    await show_product_detail(query, context, product_code)


async def show_product_stats(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Show product statistics."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)
    
    if not product:
        await query.edit_message_text("❌ Product not found\\.", parse_mode="MarkdownV2")
        return
    
    # Get stats
    stock_count = await db.get_available_stock_count(product_code)
    sold_count = await db.get_sold_stock_count(product_code)
    total_stock = stock_count + sold_count
    
    name = escape_md(product['name'])
    price = product['price']
    revenue = sold_count * price
    
    text = (
        f"*📊 Stats: {name}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 *Total Stock Added:* `{total_stock}`\n"
        f"✅ *Available:* `{stock_count}`\n"
        f"💰 *Sold:* `{sold_count}`\n\n"
        f"💵 *Revenue:* `{escape_md(format_currency(revenue))}`\n"
        f"📈 *Sell Rate:* `{(sold_count/total_stock*100):.1f}%`" if total_stock > 0 else ""
    )
    
    keyboard = AdminKeyboards.product_detail(product_code)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )


async def show_bulk_price_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bulk price update info."""
    text = (
        "*💰 Bulk Price Update*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Use command to update prices:_\n\n"
        "`/bulkprice +10%` \\- Increase all by 10%\n"
        "`/bulkprice -5000` \\- Decrease all by 5000\n"
        "`/bulkprice set 50000` \\- Set all to 50000"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.product_management_menu()
    )


# Handler exports
product_ui_handlers = [
    CallbackQueryHandler(handle_product_action, pattern=r"^admin:product:"),
]
