"""
Product management handlers for FRIENDS Store Telegram Bot.
"""

from database.db import Database
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.validators import (
    validate_price,
    validate_product_code,
    validate_product_name,
)
from utils.visual_system import VisualSystem as vs

logger = get_logger("admin")

# Conversation states
NAME, DESCRIPTION, PRICE, CONFIRM = range(4)


def format_currency_local(amount: int) -> str:
    """Format currency with dot separator."""
    return f"Rp {amount:,}".replace(",", ".")


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is an admin."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    return await db.is_admin(user.id)


async def addproduct_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start add product wizard."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return ConversationHandler.END

    args = context.args
    if not args:
        text = f"""
{vs.header('Add Product Wizard', '', icon='🛍️')}

Masukkan product code (lowercase, underscore ok):
Contoh: {uf.monospace('github_student_fresh')}

{uf.italic('Ketik /cancel untuk membatalkan.')}
"""
        await update.message.reply_text(text)
        return NAME

    # Product code provided as argument
    product_code = args[0].lower()
    is_valid, error = validate_product_code(product_code)

    if not is_valid:
        await update.message.reply_text(f"❌ {error}")
        return ConversationHandler.END

    context.user_data["new_product"] = {"product_code": product_code}

    await update.message.reply_text(f"✅ Product code: {uf.monospace(product_code)}\n\n" "Masukkan nama produk:")
    return DESCRIPTION


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive product code/name."""
    text = update.message.text.strip()

    if "new_product" not in context.user_data:
        # This is product code
        product_code = text.lower()
        is_valid, error = validate_product_code(product_code)

        if not is_valid:
            await update.message.reply_text(f"❌ {error}\nCoba lagi:")
            return NAME

        context.user_data["new_product"] = {"product_code": product_code}
        await update.message.reply_text("Masukkan nama produk:")
        return DESCRIPTION

    return DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive product name and ask for description."""
    name = update.message.text.strip()

    is_valid, error = validate_product_name(name)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}\nCoba lagi:")
        return DESCRIPTION

    context.user_data["new_product"]["name"] = name

    await update.message.reply_text(f"Masukkan deskripsi produk (atau ketik {uf.monospace('-')} untuk skip):")
    return PRICE


async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive description and ask for price."""
    description = update.message.text.strip()

    if description == "-":
        description = None

    context.user_data["new_product"]["description"] = description

    await update.message.reply_text(
        f"Masukkan harga (dalam Rupiah):\n" f"Contoh: {uf.monospace('50000')} atau {uf.monospace('50.000')}"
    )
    return CONFIRM


async def confirm_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create product."""
    price_text = update.message.text.strip()

    is_valid, error, price = validate_price(price_text)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}\nCoba lagi:")
        return CONFIRM

    product_data = context.user_data["new_product"]
    product_data["price"] = price

    db: Database = context.bot_data["db"]

    # Check if product code exists
    existing = await db.get_product(product_data["product_code"])
    if existing:
        await update.message.reply_text(f"❌ Product code {uf.monospace(product_data['product_code'])} sudah ada!")
        context.user_data.clear()
        return ConversationHandler.END

    # Create product
    await db.add_product(
        product_code=product_data["product_code"],
        name=product_data["name"],
        description=product_data.get("description"),
        price=product_data["price"],
    )

    text = f"""
✅ {uf.bold('Produk Berhasil Ditambahkan!')}

📦 {uf.bold('Code:')} {uf.monospace(product_data['product_code'])}
🏷️ {uf.bold('Name:')} {product_data['name']}
💰 {uf.bold('Price:')} {uf.monospace(format_currency_local(product_data['price']))}
"""
    await update.message.reply_text(text)
    logger.info(f"Product added: code={product_data['product_code']}, name={product_data['name']}")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation."""
    context.user_data.clear()
    await update.message.reply_text("❌ Dibatalkan.")
    return ConversationHandler.END


async def editproduct_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /editproduct command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if len(args) < 3:
        text = f"""
{vs.header('Edit Product', '', icon='📝')}

{uf.bold('Usage:')} {uf.monospace('/editproduct <product_code> <field> <value>')}

{uf.bold('Fields:')} name, description, price, active

{uf.bold('Examples:')}
{uf.monospace('/editproduct github_student_fresh price 55000')}
{uf.monospace('/editproduct github_student_fresh active false')}
"""
        await update.message.reply_text(text)
        return

    product_code = args[0].lower()
    field = args[1].lower()
    value = " ".join(args[2:])

    db: Database = context.bot_data["db"]

    product = await db.get_product(product_code)
    if not product:
        await update.message.reply_text(f"❌ Produk {uf.monospace(product_code)} tidak ditemukan.")
        return

    update_data = {}

    if field == "name":
        update_data["name"] = value
    elif field == "description":
        update_data["description"] = value if value != "-" else None
    elif field == "price":
        is_valid, error, price = validate_price(value)
        if not is_valid:
            await update.message.reply_text(f"❌ {error}")
            return
        update_data["price"] = price
    elif field == "active":
        update_data["is_active"] = value.lower() in ("true", "1", "yes")
    else:
        await update.message.reply_text(f"❌ Field tidak valid: {field}")
        return

    await db.update_product(product_code, **update_data)
    logger.info(f"Product updated: code={product_code}, field={field}, value={value}")

    text = f"""
✅ {uf.bold('Produk berhasil diupdate!')}

📦 {uf.bold('Product:')} {uf.monospace(product_code)}
📝 {uf.bold('Field:')} {field} = {value}
"""
    await update.message.reply_text(text)


async def deleteproduct_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /deleteproduct command (soft delete)."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(f"{uf.bold('Usage:')} /deleteproduct <product_code>")
        return

    product_code = args[0].lower()
    db: Database = context.bot_data["db"]

    product = await db.get_product(product_code)
    if not product:
        await update.message.reply_text(f"❌ Produk {uf.monospace(product_code)} tidak ditemukan.")
        return

    await db.delete_product(product_code)
    logger.info(f"Product deactivated: code={product_code}")

    await update.message.reply_text(f"✅ Produk {uf.monospace(product_code)} telah dinonaktifkan.")


async def listproducts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /listproducts command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    db: Database = context.bot_data["db"]
    products = await db.get_all_products()

    if not products:
        await update.message.reply_text("📦 Tidak ada produk.")
        return

    lines = [f"{vs.header('Daftar Produk', '', icon='🛍️')}"]

    for p in products:
        status = "🟢" if p["is_active"] else "🔴"
        lines.append(
            f"{status} {uf.bold(p['name'])}\n"
            f"   {uf.monospace(p['product_code'])} | {uf.monospace(format_currency_local(p['price']))}"
        )

    await update.message.reply_text("\n".join(lines))


# Conversation handler for add product
addproduct_handler = ConversationHandler(
    entry_points=[CommandHandler("addproduct", addproduct_start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_price)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_product)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# Handler exports
product_handlers = [
    addproduct_handler,
    CommandHandler("editproduct", editproduct_command),
    CommandHandler("deleteproduct", deleteproduct_command),
    CommandHandler("listproducts", listproducts_command),
]
