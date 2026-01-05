"""
Stock management handlers for FRIENDS Store Telegram Bot.
"""

from database.db import Database
from services.stock_manager import StockManager
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.validators import validate_stock_entry
from utils.visual_system import VisualSystem as vs

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
        text = f"""
{vs.header('Add Stock', 'Tambah stock produk', icon='📦')}

{uf.bold('Usage:')}
{uf.monospace('/addstock <product_code> <email:password[:2fa][:notes]>')}

{uf.bold('Example:')}
{uf.monospace('/addstock github_student_fresh user@mail.com:pass123:JBSWY3DP:Valid Dec 2026')}

{uf.bold('Bulk Upload:')}
Upload a {uf.monospace('.txt')} file with entries (one per line) with product code as caption.
"""
        await update.message.reply_text(text)
        return

    product_code = args[0].lower()
    stock_entry = " ".join(args[1:])

    db: Database = context.bot_data["db"]

    # Check product exists
    product = await db.get_product(product_code)
    if not product:
        await update.message.reply_text(f"❌ Produk {uf.monospace(product_code)} tidak ditemukan.")
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
            added_by=update.effective_user.id,
        )

        stock_count = await db.get_available_stock_count(product_code)

        text = f"""
✅ {uf.bold('Stock ditambahkan!')}

📦 {uf.bold('Produk:')} {product['name']}
📧 {uf.bold('Email:')} {uf.monospace(data['email'][:10] + '...')}
📊 {uf.bold('Total Stock:')} {uf.monospace(str(stock_count))}
"""
        await update.message.reply_text(text)
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
            f"❌ Caption harus berisi product_code\n" f"Contoh: {uf.monospace('github_student_fresh')}"
        )
        return

    product_code = caption.strip().lower()

    db: Database = context.bot_data["db"]

    # Check product exists
    product = await db.get_product(product_code)
    if not product:
        await update.message.reply_text(f"❌ Produk {uf.monospace(product_code)} tidak ditemukan.")
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
        product_code=product_code, entries=lines, added_by=update.effective_user.id
    )

    result_text = f"""
{vs.header('Bulk Stock Upload Complete', '', icon='📦')}

📊 {uf.bold('Produk:')} {product['name']}
✅ {uf.bold('Berhasil:')} {uf.monospace(str(success))}
❌ {uf.bold('Gagal:')} {uf.monospace(str(errors))}
"""
    logger.info(f"Bulk stock upload: product={product_code}, success={success}, errors={errors}")

    if error_msgs and len(error_msgs) <= 5:
        result_text += f"\n{uf.bold('Errors:')}\n" + "\n".join(error_msgs[:5])

    await update.message.reply_text(result_text)


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

    lines = [f"{vs.header('Stock Summary', f'{len(stock_summary)} produk', icon='📦')}"]

    for item in stock_summary:
        indicator = "🟢" if item.get("available", 0) > 5 else "🟡" if item.get("available", 0) > 0 else "🔴"
        lines.append(
            f"{indicator} {uf.bold(item.get('name', item.get('product_code', '-'))[:20])}: "
            f"{uf.monospace(str(item.get('available', 0)))} / {item.get('total', 0)}"
        )

    await update.message.reply_text("\n".join(lines))


async def stockdetails_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stockdetails <product_code> - show stock details."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(f"{uf.bold('Usage:')} /stockdetails <product_code>")
        return

    product_code = args[0].lower()
    db: Database = context.bot_data["db"]

    stock_items = await db.get_available_stock(product_code)

    if not stock_items:
        await update.message.reply_text(f"📦 Tidak ada stock tersedia untuk {uf.monospace(product_code)}")
        return

    lines = [
        f"{vs.header('Stock Details', product_code, icon='📦')}",
        f"Total: {uf.monospace(str(len(stock_items)))} items\n",
    ]

    for i, item in enumerate(stock_items[:20], 1):
        email = item["email"]
        if len(email) > 20:
            email = email[:17] + "..."
        lines.append(f"{i}. {uf.monospace(email)}")

    if len(stock_items) > 20:
        lines.append(f"\n{uf.italic(f'...dan {len(stock_items) - 20} lainnya')}")

    await update.message.reply_text("\n".join(lines))


# Handler exports
stock_handlers = [
    CommandHandler("addstock", addstock_command),
    CommandHandler("checkstock", checkstock_command),
    CommandHandler("stockdetails", stockdetails_command),
    MessageHandler(filters.Document.TXT & filters.Caption(r".*"), handle_stock_file),
]
