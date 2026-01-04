"""
Product management handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters
)

from database.db import Database
from utils.validators import validate_product_code, validate_product_name, validate_price
from utils.formatters import format_currency, escape_md
from utils.logger import get_logger

logger = get_logger("admin")

# Conversation states
NAME, DESCRIPTION, PRICE, CONFIRM = range(4)


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
        await update.message.reply_text(
            "🛍️ *Add Product Wizard*\n\n"
            "Masukkan product code (lowercase, underscore ok):\n"
            "Contoh: `github_student_fresh`\n\n"
            "Ketik /cancel untuk membatalkan.",
            parse_mode="MarkdownV2"
        )
        return NAME

    # Product code provided as argument
    product_code = args[0].lower()
    is_valid, error = validate_product_code(product_code)

    if not is_valid:
        await update.message.reply_text(f"❌ {error}")
        return ConversationHandler.END

    context.user_data["new_product"] = {"product_code": product_code}

    await update.message.reply_text(
        f"✅ Product code: `{product_code}`\n\n"
        "Masukkan nama produk:",
        parse_mode="MarkdownV2"
    )
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

    await update.message.reply_text(
        "Masukkan deskripsi produk (atau ketik `-` untuk skip):"
    )
    return PRICE


async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive description and ask for price."""
    description = update.message.text.strip()

    if description == "-":
        description = None

    context.user_data["new_product"]["description"] = description

    await update.message.reply_text(
        "Masukkan harga (dalam Rupiah):\n"
        "Contoh: `50000` atau `50.000`",
        parse_mode="MarkdownV2"
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
        await update.message.reply_text(
            f"❌ Product code `{product_data['product_code']}` sudah ada!",
            parse_mode="MarkdownV2"
        )
        context.user_data.clear()
        return ConversationHandler.END

    # Create product
    await db.add_product(
        product_code=product_data["product_code"],
        name=product_data["name"],
        description=product_data.get("description"),
        price=product_data["price"]
    )

    await update.message.reply_text(
        f"✅ *Produk Berhasil Ditambahkan\!*\n\n"
        f"📦 Code: `{escape_md(product_data['product_code'])}`\n"
        f"🏷️ Name: {escape_md(product_data['name'])}\n"
        f"💰 Price: `{escape_md(format_currency(product_data['price']))}`",
        parse_mode="MarkdownV2"
    )
    logger.info(f"Product added: code={product_data['product_code']}, name={product_data['name']}, by={update.effective_user.id}")

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
        await update.message.reply_text(
            "📝 *Edit Product*\n\n"
            "Usage: `/editproduct <product_code> <field> <value>`\n\n"
            "Fields: `name`, `description`, `price`, `active`\n\n"
            "Examples:\n"
            "`/editproduct github_student_fresh price 55000`\n"
            "`/editproduct github_student_fresh active false`",
            parse_mode="MarkdownV2"
        )
        return

    product_code = args[0].lower()
    field = args[1].lower()
    value = " ".join(args[2:])

    db: Database = context.bot_data["db"]

    product = await db.get_product(product_code)
    if not product:
        await update.message.reply_text(f"❌ Produk `{product_code}` tidak ditemukan.")
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
    logger.info(f"Product updated: code={product_code}, field={field}, value={value}, by={update.effective_user.id}")

    await update.message.reply_text(
        f"✅ Produk `{escape_md(product_code)}` berhasil diupdate\!\n"
        f"Field: {escape_md(field)} \= {escape_md(value)}",
        parse_mode="MarkdownV2"
    )


async def deleteproduct_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /deleteproduct command (soft delete)."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/deleteproduct <product_code>`", parse_mode="MarkdownV2")
        return

    product_code = args[0].lower()
    db: Database = context.bot_data["db"]

    product = await db.get_product(product_code)
    if not product:
        await update.message.reply_text(f"❌ Produk `{product_code}` tidak ditemukan.")
        return

    await db.delete_product(product_code)
    logger.info(f"Product deactivated: code={product_code}, by={update.effective_user.id}")

    await update.message.reply_text(
        f"✅ Produk `{escape_md(product_code)}` telah dinonaktifkan\.",
        parse_mode="MarkdownV2"
    )


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

    lines = ["🛍️ *Daftar Produk*\n"]

    for p in products:
        status = "🟢" if p["is_active"] else "🔴"
        name = escape_md(p['name'])
        code = escape_md(p['product_code'])
        price = escape_md(format_currency(p['price']))
        lines.append(
            f"{status} *{name}*\n"
            f"   `{code}` \| `{price}`\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


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
