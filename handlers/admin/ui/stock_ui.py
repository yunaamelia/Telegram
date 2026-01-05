"""
Stock management UI handlers.
"""

from database.db import Database
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from utils.admin_keyboards import AdminKeyboards
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

logger = get_logger("admin.stock_ui")


def format_currency_local(amount: int) -> str:
    """Format currency with dot separator."""
    return f"Rp {amount:,}".replace(",", ".")


async def handle_stock_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Route stock-related callback queries.
    Pattern: admin:stock:<action>
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return

    # Parse: admin:stock:add or admin:stock:add:product_code
    parts = query.data.split(":")
    action = parts[2] if len(parts) > 2 else None

    if action == "add":
        # Check if product_code is specified
        if len(parts) > 3:
            product_code = parts[3]
            await show_add_stock_form(query, context, product_code)
        else:
            await show_product_selection(query, context)
    elif action == "check":
        await show_stock_summary(query, context)
    elif action == "details":
        await show_stock_details(query, context)
    elif action == "lowstock":
        await show_low_stock(query, context)
    elif action == "list":
        # admin:stock:list:product_code:page
        product_code = parts[3] if len(parts) > 3 else None
        page = int(parts[4]) if len(parts) > 4 else 1
        await show_stock_list(query, context, product_code, page)
    elif action == "view":
        # admin:stock:view:stock_id:page
        stock_id = int(parts[3]) if len(parts) > 3 else None
        await show_stock_item_detail(query, context, stock_id)
    elif action == "delete":
        stock_id = int(parts[3]) if len(parts) > 3 else None
        await confirm_delete_stock(query, context, stock_id)
    elif action == "bulk":
        await show_bulk_upload_info(query, context)
    elif action == "export":
        await export_stock(query, context)


async def show_product_selection(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show product list for stock selection."""
    db: Database = context.bot_data["db"]
    products = await db.get_active_products()

    if not products:
        text = f"❌ {uf.bold('No products available')}\n\n{uf.italic('Add a product first.')}"
        await query.edit_message_text(text, reply_markup=AdminKeyboards.stock_management_menu())
        return

    # Build product list with stock counts
    lines = [f"{vs.header('Select Product to Add Stock', '', icon='📦')}"]

    for idx, product in enumerate(products[:6], 1):
        stock_count = await db.get_available_stock_count(product["product_code"])
        status = "⚠️" if stock_count < 5 else "✅" if stock_count > 0 else "❌"

        lines.append(f"{uf.bold(f'{idx}.')} {product['name']}")
        lines.append(f"   📊 Stock: {uf.bold(str(stock_count))} {status}")

    text = "\n".join(lines)
    keyboard = AdminKeyboards.product_list(products, page=1, items_per_page=6, context="addstock")

    await query.edit_message_text(text, reply_markup=keyboard)


async def show_add_stock_form(query, context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """Show form instructions for adding stock."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)

    if not product:
        await query.edit_message_text("❌ Product not found.")
        return

    name = product["name"]
    text = f"{vs.header(f'Add Stock - {name}', '', icon='📦')}\n\n"
    text += f"{uf.bold('Format:')}\n"
    text += f"{uf.monospace('email:password:2fa_secret:notes')}\n\n"
    text += f"{uf.bold('Example:')}\n"
    text += f"{uf.monospace('user@mail.com:pass123:JBSWY3DP:Valid Dec 2026')}\n\n"
    text += f"{uf.italic('2FA and notes are optional. Use : as separator.')}\n\n"
    text += "Type /cancel to abort."

    # Store product code for wizard
    context.user_data["add_stock_product"] = product_code

    await query.edit_message_text(text)


async def show_stock_summary(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show overall stock summary."""
    db: Database = context.bot_data["db"]
    products = await db.get_all_products()

    lines = [f"{vs.header('Stock Summary', '', icon='📦')}"]

    total_stock = 0
    low_stock_products = []

    for product in products:
        if not product.get("is_active"):
            continue

        stock_count = await db.get_available_stock_count(product["product_code"])
        total_stock += stock_count

        if stock_count < 5:
            low_stock_products.append((product["name"], stock_count))

        status = "⚠️" if stock_count < 5 else "✅" if stock_count > 0 else "❌"

        lines.append(f"{status} {uf.bold(product['name'])}")
        price_str = format_currency_local(product["price"])
        lines.append(f"   📊 {uf.monospace(str(stock_count))} | 💰 {uf.monospace(price_str)}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"\n📦 {uf.bold('Total Stock:')} {uf.monospace(str(total_stock))}")

    if low_stock_products:
        lines.append(f"⚠️ {uf.bold('Low Stock:')} {uf.monospace(f'{len(low_stock_products)} products')}")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.stock_management_menu())


async def show_low_stock(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show low stock warning list."""
    db: Database = context.bot_data["db"]
    products = await db.get_active_products()

    lines = [f"{vs.header('Low Stock Warning', '', icon='⚠️')}"]

    low_stock = []
    for product in products:
        stock_count = await db.get_available_stock_count(product["product_code"])
        if stock_count < 5:
            low_stock.append((product, stock_count))

    if not low_stock:
        lines.append(f"{uf.italic('All products have sufficient stock!')} ✅")
    else:
        for idx, (product, count) in enumerate(low_stock, 1):
            status = "🚨" if count == 0 else "⚠️"
            lines.append(f"{status} {uf.bold(f'{idx}.')} {product['name']}")
            lines.append(f"   📊 Stock: {uf.bold(str(count))}")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.stock_management_menu())


async def show_stock_list(query, context: ContextTypes.DEFAULT_TYPE, product_code: str, page: int) -> None:
    """Show stock items for a product."""
    db: Database = context.bot_data["db"]
    product = await db.get_product(product_code)

    if not product:
        await query.edit_message_text("❌ Product not found.")
        return

    stock_items = await db.get_stock_items(product_code)
    name = product["name"]

    if not stock_items:
        text = f"{vs.header(f'Stock: {name}', '', icon='📦')}\n\n"
        text += f"{uf.italic('No stock items available.')}"
        await query.edit_message_text(text, reply_markup=AdminKeyboards.product_detail(product_code))
        return

    # Paginate
    items_per_page = 6
    total_pages = max(1, (len(stock_items) + items_per_page - 1) // items_per_page)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = stock_items[start_idx:end_idx]

    lines = [f"{vs.header(f'Stock: {name}', '', icon='📦')}"]
    lines.append(f"{uf.italic(f'Page {page}/{total_pages} | Total: {len(stock_items)}')}")

    for idx, item in enumerate(page_items, 1):
        email = item["email"][:20] + "..." if len(item["email"]) > 20 else item["email"]
        status = "✅" if item.get("is_available", True) else "❌ SOLD"

        lines.append(f"{uf.bold(f'{idx}.')} {uf.monospace(email)}")
        lines.append(f"   {status}")

    text = "\n".join(lines)
    keyboard = AdminKeyboards.stock_list(stock_items, product_code, page)

    await query.edit_message_text(text, reply_markup=keyboard)


async def show_stock_item_detail(query, context: ContextTypes.DEFAULT_TYPE, stock_id: int) -> None:
    """Show single stock item details."""
    db: Database = context.bot_data["db"]

    # Get stock item
    stock = await db.get_stock_by_id(stock_id)

    if not stock:
        await query.edit_message_text("❌ Stock item not found.")
        return

    text = f"{vs.header('Stock Item Detail', '', icon='📦')}\n\n"
    text += f"📧 {uf.bold('Email:')} {uf.monospace(stock['email'])}\n"
    text += f"🔒 {uf.bold('Password:')} {uf.monospace(stock['password'][:4] + '****')}\n"

    if stock.get("two_fa_secret"):
        text += f"🔐 {uf.bold('2FA:')} {uf.monospace(stock['two_fa_secret'][:6] + '...')}\n"

    if stock.get("notes"):
        text += f"📝 {uf.bold('Notes:')} {uf.italic(stock['notes'])}\n"

    status = "✅ Available" if stock.get("is_available", True) else "❌ Sold"
    text += f"\n{uf.bold('Status:')} {status}"

    keyboard = AdminKeyboards.stock_detail(stock_id, stock["product_code"])

    await query.edit_message_text(text, reply_markup=keyboard)


async def confirm_delete_stock(query, context: ContextTypes.DEFAULT_TYPE, stock_id: int) -> None:
    """Confirm stock deletion."""
    text = f"{vs.alert('Delete Stock Item?', 'warning')}\n\n"
    text += "This action cannot be undone."

    keyboard = AdminKeyboards.confirmation("stock:delete", str(stock_id), "admin:menu:stock")

    await query.edit_message_text(text, reply_markup=keyboard)


async def show_stock_details(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Redirect to stock summary."""
    await show_stock_summary(query, context)


async def show_bulk_upload_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bulk upload instructions."""
    text = f"{vs.header('Bulk Stock Upload', '', icon='📤')}\n\n"
    text += f"{uf.bold('Format:')} One item per line\n"
    text += f"{uf.monospace('email:password:2fa:notes')}\n\n"
    text += f"{uf.bold('Example:')}\n"
    text += f"{uf.monospace('user1@mail.com:pass1:ABC:Note1')}\n"
    text += f"{uf.monospace('user2@mail.com:pass2::Note2')}\n"
    text += f"{uf.monospace('user3@mail.com:pass3')}\n\n"
    text += f"{uf.italic('Send the file or paste the text after selecting a product.')}"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.stock_management_menu())


async def export_stock(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export stock to file."""
    text = f"{vs.header('Export Stock', '', icon='📥')}\n\n"
    text += f"{uf.italic('Feature coming soon...')}"
    await query.edit_message_text(text, reply_markup=AdminKeyboards.stock_management_menu())


# Handler exports
stock_ui_handlers = [
    CallbackQueryHandler(handle_stock_action, pattern=r"^admin:stock:"),
]
