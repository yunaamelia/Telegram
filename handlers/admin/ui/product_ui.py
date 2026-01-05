"""
Product management UI handlers.
"""

from database.db import Database
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from utils.admin_keyboards import AdminKeyboards
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

logger = get_logger("admin.product_ui")


def format_currency_local(amount: int) -> str:
    """Format currency with dot separator."""
    return f"Rp {amount:,}".replace(",", ".")


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
        page = int(parts[3]) if len(parts) > 3 else 1
        ctx = parts[4] if len(parts) > 4 else "view"
        await show_product_list(query, context, page, ctx)
    elif action == "view":
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
        pass
    elif action == "addstock":
        product_code = parts[3] if len(parts) > 3 else None
        from handlers.admin.ui.stock_ui import show_add_stock_form

        await show_add_stock_form(query, context, product_code)


async def show_product_list(query, context: ContextTypes.DEFAULT_TYPE, page: int = 1, ctx: str = "view") -> None:
    """Show paginated product list."""
    db: Database = context.bot_data["db"]
    products = await db.get_all_products()

    if not products:
        text = f"{vs.header('Product List', '', icon='🛍️')}\n\n"
        text += f"{uf.italic('No products found.')}"
        await query.edit_message_text(text, reply_markup=AdminKeyboards.product_management_menu())
        return

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
        "addstock": "📦 Add Stock",
    }
    title = ctx_titles.get(ctx, "📋 View")

    lines = [f"{vs.header('Product List - ' + title, '', icon='🛍️')}"]
    lines.append(f"{uf.italic(f'Page {page}/{total_pages} | Total: {len(products)}')}")

    for idx, product in enumerate(page_products, 1):
        status = "🟢" if product.get("is_active", True) else "🔴"
        stock_count = await db.get_available_stock_count(product["product_code"])
        stock_indicator = "⚠️" if stock_count < 5 else ""

        lines.append(f"{uf.bold(f'{idx}.')} {status} {product['name']}")
        price_str = format_currency_local(product["price"])
        lines.append(f"   {uf.monospace(product['product_code'])} | 💰 {uf.monospace(price_str)}")
        lines.append(f"   📊 Stock: {uf.bold(str(stock_count))} {stock_indicator}")

    text = "\n".join(lines)
    keyboard = AdminKeyboards.product_list(products, page, items_per_page, ctx)

    await query.edit_message_text(text, reply_markup=keyboard)


async def show_product_detail(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Show product detail with actions."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)

    if not product:
        await query.edit_message_text(
            "❌ Product not found.",
            reply_markup=AdminKeyboards.product_management_menu(),
        )
        return

    stock_count = await db.get_available_stock_count(product_code)
    status = "🟢 Active" if product.get("is_active", True) else "🔴 Inactive"
    stock_status = "⚠️" if stock_count < 5 else "✅" if stock_count > 0 else "❌"
    desc = product.get("description", "No description")

    name = product["name"]
    text = f"{vs.header(name, '', icon='🛍️')}\n\n"
    text += f"{uf.bold('Code:')} {uf.monospace(product['product_code'])}\n"
    text += f"{uf.bold('Price:')} {uf.monospace(format_currency_local(product['price']))}\n"
    text += f"{uf.bold('Status:')} {status}\n"
    text += f"{uf.bold('Stock:')} {uf.monospace(str(stock_count))} {stock_status}\n\n"
    text += f"{uf.bold('Description:')}\n{uf.italic(desc)}"

    keyboard = AdminKeyboards.product_detail(product_code, stock_count > 0)

    await query.edit_message_text(text, reply_markup=keyboard)


async def show_edit_options(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Show edit options for a product."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)

    if not product:
        await query.edit_message_text("❌ Product not found.")
        return

    name = product["name"]
    header = f"Edit Product: {name}"
    text = f"{vs.header(header, '', icon='✏️')}\n\n"
    text += f"{uf.italic('Use commands to edit:')}\n\n"
    text += f"{uf.monospace('/editproduct ' + product_code + ' name <new_name>')}\n"
    text += f"{uf.monospace('/editproduct ' + product_code + ' price <amount>')}\n"
    text += f"{uf.monospace('/editproduct ' + product_code + ' description <text>')}\n"
    text += f"{uf.monospace('/editproduct ' + product_code + ' active true/false')}"

    keyboard = AdminKeyboards.product_detail(product_code)

    await query.edit_message_text(text, reply_markup=keyboard)


async def confirm_delete_product(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Confirm product deletion."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)

    if not product:
        await query.edit_message_text("❌ Product not found.")
        return

    stock_count = await db.get_available_stock_count(product_code)
    name = product["name"]
    header = f"Delete Product: {name}?"

    text = f"{vs.alert(header, 'warning')}\n\n"
    text += f"📦 {uf.bold('Stock items:')} {uf.monospace(str(stock_count))}\n\n"
    text += f"{uf.italic('This will deactivate the product.')}\n"
    text += f"{uf.italic('Stock items will be preserved.')}"

    cancel_target = f"admin:product:view:{product_code}:1"
    keyboard = AdminKeyboards.confirmation("product:delete", product_code, cancel_target)

    await query.edit_message_text(text, reply_markup=keyboard)


async def toggle_product_active(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Toggle product active status."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)

    if not product:
        await query.edit_message_text("❌ Product not found.")
        return

    new_status = not product.get("is_active", True)
    await db.update_product(product_code, {"is_active": new_status})

    status_text = "diaktifkan ✅" if new_status else "dinonaktifkan 🔴"

    await query.answer(f"Product {status_text}", show_alert=True)
    await show_product_detail(query, context, product_code)


async def show_product_stats(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Show product statistics."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)

    if not product:
        await query.edit_message_text("❌ Product not found.")
        return

    stock_count = await db.get_available_stock_count(product_code)
    sold_count = await db.get_sold_stock_count(product_code)
    total_stock = stock_count + sold_count

    price = product["price"]
    revenue = sold_count * price
    name = product["name"]
    header = f"Stats: {name}"

    text = f"{vs.header(header, '', icon='📊')}\n\n"
    text += f"📦 {uf.bold('Total Stock Added:')} {uf.monospace(str(total_stock))}\n"
    text += f"✅ {uf.bold('Available:')} {uf.monospace(str(stock_count))}\n"
    text += f"💰 {uf.bold('Sold:')} {uf.monospace(str(sold_count))}\n\n"
    text += f"💵 {uf.bold('Revenue:')} {uf.monospace(format_currency_local(revenue))}\n"
    if total_stock > 0:
        rate = sold_count / total_stock * 100
        text += f"📈 {uf.bold('Sell Rate:')} {uf.monospace(f'{rate:.1f}%')}"

    keyboard = AdminKeyboards.product_detail(product_code)

    await query.edit_message_text(text, reply_markup=keyboard)


async def show_bulk_price_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bulk price update info."""
    text = f"{vs.header('Bulk Price Update', '', icon='💰')}\n\n"
    text += f"{uf.italic('Use command to update prices:')}\n\n"
    text += f"{uf.monospace('/bulkprice +10%')} - Increase all by 10%\n"
    text += f"{uf.monospace('/bulkprice -5000')} - Decrease all by 5000\n"
    text += f"{uf.monospace('/bulkprice set 50000')} - Set all to 50000"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.product_management_menu())


# Handler exports
product_ui_handlers = [
    CallbackQueryHandler(handle_product_action, pattern=r"^admin:product:"),
]
