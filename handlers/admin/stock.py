"""
Stock management handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from database.db import Database
from services.stock_manager import StockManager
from utils.formatters import format_stock_summary, escape_md
from utils.validators import validate_stock_entry
from utils.logger import get_logger

logger = get_logger("admin")


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is an admin."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    return await db.is_admin(user.id)


async def addstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /addstock command.
    Usage: /addstock <product_code> <email:password:2fa:notes>
    """
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args

    if not args or len(args) < 2:
        await update.message.reply_text(
            "📦 *Add Stock*\n\n"
            "*Usage:*\n"
            "`/addstock <product_code> <email:password[:2fa][:notes]>`\n\n"
            "*Example:*\n"
            "`/addstock github_student_fresh user@mail.com:pass123:JBSWY3DP:Valid Dec 2026`\n\n"
            "*Bulk Upload:*\n"
            "Upload a `.txt` file with entries (one per line) with product code as caption.",
            parse_mode="MarkdownV2"
        )
        return

    product_code = args[0].lower()
    stock_entry = " ".join(args[1:])

    db: Database = context.bot_data["db"]

    # Check product exists
    product = await db.get_product(product_code)
    if not product:
        await update.message.reply_text(f"❌ Produk `{escape_md(product_code)}` tidak ditemukan\.", parse_mode="MarkdownV2")
        return

    # Validate entry
    is_valid, error_msg, data = validate_stock_entry(stock_entry)
    if not is_valid:
        await update.message.reply_text(f"❌ Format salah: {error_msg}")
        return

    # Add stock
    try:
        await db.add_stock_item(
            product_code=product_code,
            email=data["email"],
            password=data["password"],
            two_fa_secret=data.get("two_fa_secret"),
            notes=data.get("notes"),
            added_by=update.effective_user.id
        )

        stock_count = await db.get_available_stock_count(product_code)

        await update.message.reply_text(
            f"✅ Stock ditambahkan\!\n\n"
            f"📦 Produk: {escape_md(product['name'])}\n"
            f"📧 Email: `{escape_md(data['email'][:10])}\.\.\.*`\n"
            f"📊 Total Stock: `{stock_count}`",
            parse_mode="MarkdownV2"
        )
        logger.info(f"Stock added: product={product_code}, email={data['email']}, by={update.effective_user.id}")
    except Exception as e:
        logger.error(f"Failed to add stock: {e}")
        await update.message.reply_text(f"❌ Gagal menambah stock: {e}")


async def handle_stock_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bulk stock upload via file."""
    if not await check_admin(update, context):
        return

    document = update.message.document

    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Hanya file .txt yang didukung")
        return

    # Get product code from caption
    caption = update.message.caption or ""
    if not caption:
        await update.message.reply_text(
            "❌ Caption harus berisi product_code\n"
            "Contoh: `github_student_fresh`",
            parse_mode="MarkdownV2"
        )
        return

    product_code = caption.strip().lower()

    db: Database = context.bot_data["db"]

    # Check product exists
    product = await db.get_product(product_code)
    if not product:
        await update.message.reply_text(f"❌ Produk `{escape_md(product_code)}` tidak ditemukan\.", parse_mode="MarkdownV2")
        return

    # Download file
    file = await document.get_file()
    file_content = await file.download_as_bytearray()
    text = file_content.decode("utf-8")
    lines = text.strip().split("\n")

    await update.message.reply_text(f"⏳ Memproses {len(lines)} entries...")

    # Add stock bulk
    stock_manager = StockManager(db)
    success, errors, error_msgs = await stock_manager.add_stock_bulk(
        product_code=product_code,
        entries=lines,
        added_by=update.effective_user.id
    )

    result_text = (
        f"📦 *Bulk Stock Upload Complete*\n\n"
        f"📊 Produk: {escape_md(product['name'])}\n"
        f"✅ Berhasil: `{success}`\n"
        f"❌ Gagal: `{errors}`\n"
    )
    logger.info(f"Bulk stock upload: product={product_code}, success={success}, errors={errors}, by={update.effective_user.id}")

    if error_msgs and len(error_msgs) <= 5:
        result_text += "\n*Errors:*\n" + "\n".join(error_msgs[:5])

    await update.message.reply_text(result_text, parse_mode="MarkdownV2")


async def checkstock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /checkstock command - show stock summary."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    db: Database = context.bot_data["db"]

    stock_summary = await db.get_stock_summary()

    if not stock_summary:
        await update.message.reply_text("📦 Tidak ada produk.")
        return

    text = format_stock_summary(stock_summary)

    await update.message.reply_text(text, parse_mode="MarkdownV2")


async def stockdetails_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stockdetails <product_code> - show stock details."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/stockdetails <product_code>`", parse_mode="MarkdownV2")
        return

    product_code = args[0].lower()
    db: Database = context.bot_data["db"]

    stock_items = await db.get_available_stock(product_code)

    if not stock_items:
        await update.message.reply_text(f"📦 Tidak ada stock tersedia untuk `{product_code}`")
        return

    lines = [f"📦 *Stock Details: {escape_md(product_code)}*\n", f"Total: `{len(stock_items)}` items\n"]

    for i, item in enumerate(stock_items[:20], 1):
        email = item["email"]
        if len(email) > 20:
            email = email[:17] + "..."
        lines.append(f"{i}. `{email}`")

    if len(stock_items) > 20:
        lines.append(f"\n_...dan {len(stock_items) - 20} lainnya_")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


# Handler exports
stock_handlers = [
    CommandHandler("addstock", addstock_command),
    CommandHandler("checkstock", checkstock_command),
    CommandHandler("stockdetails", stockdetails_command),
    MessageHandler(
        filters.Document.TXT & filters.Caption(r".*"),
        handle_stock_file
    ),
]
