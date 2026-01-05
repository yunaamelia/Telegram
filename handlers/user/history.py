"""
Transaction history handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from database.db import Database
from services.payment import PaymentService
from utils.keyboards import Keyboards
from utils.message_templates import MessageTemplates as msg
from utils.messages import safe_edit_or_send
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs


def format_tx_detail(tx: dict) -> str:
    """Format transaction detail with Unicode fonts."""
    status_icon = {"PAID": "✅", "UNPAID": "⏳", "EXPIRED": "❌", "REFUNDED": "💸"}.get(tx.get("status"), "❓")

    return f"""
{vs.header('Detail Transaksi', tx.get('merchant_ref', ''), icon='📋')}

{uf.bold('Produk:')} {tx.get('product_name', tx.get('product_code', '-'))}
{uf.bold('Jumlah:')} {uf.monospace(f"Rp {tx.get('amount', 0):,}".replace(',', '.'))}
{uf.bold('Status:')} {status_icon} {tx.get('status', '-')}

{uf.italic('ID: ' + tx.get('transaction_id', '-')[:20] + '...')}
"""


def format_tx_success(tx: dict, stock_item: dict, product_name: str) -> str:
    """Format payment success with account details."""
    return f"""
{vs.header('Pembayaran Berhasil!', 'Terima kasih!', icon='✅')}

{vs.card('Detail Pembelian', f'''
{uf.bold('Produk:')} {product_name}
{uf.bold('Harga:')} {uf.monospace(f"Rp {tx.get('amount', 0):,}".replace(',', '.'))}
''', icon='🧾')}

{vs.card('Akun Anda', f'''
{uf.bold('Email:')} {uf.monospace(stock_item.get('email', '-'))}
{uf.bold('Password:')} {uf.monospace(stock_item.get('password', '-'))}
''' + (f"\\n{uf.bold('2FA:')} {uf.monospace(stock_item.get('two_fa_secret', ''))}"
       if stock_item.get('two_fa_secret') else '')
    + (f"\\n{uf.italic(stock_item.get('notes', ''))}"
       if stock_item.get('notes') else ''), icon='🔑')}

{vs.alert('Simpan data ini dengan aman!', 'warning')}
"""


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command."""
    await show_history(update, context, is_command=True)


async def show_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_command: bool = False
) -> None:
    """Show transaction history."""
    user = update.effective_user
    db: Database = context.bot_data["db"]

    # Get user transactions
    transactions = await db.get_user_transactions(user.id, limit=10)

    # Convert to list of dicts for template
    tx_list = [
        {
            "product_name": tx.get("product_name", tx.get("product_code", "Unknown")),
            "amount": tx.get("amount", 0),
            "status": tx.get("status", "UNKNOWN"),
            "created_at": tx.get("created_at")
        }
        for tx in transactions
    ]

    text = msg.transaction_list(tx_list)

    if is_command:
        await update.message.reply_text(
            text=text,
            reply_markup=Keyboards.history_filters()
        )
    else:
        query = update.callback_query
        await query.answer()
        await safe_edit_or_send(
            query, context, user.id,
            text=text,
            reply_markup=Keyboards.history_filters()
        )


async def filter_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Filter transaction history by status."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Extract filter
    parts = query.data.split(":")
    status_filter = parts[2] if len(parts) > 2 else "all"

    db: Database = context.bot_data["db"]

    # Get filtered transactions
    if status_filter == "all":
        transactions = await db.get_user_transactions(user.id, limit=10)
    else:
        transactions = await db.get_user_transactions(
            user.id,
            status=status_filter,
            limit=10
        )

    # Convert to list of dicts for template
    tx_list = [
        {
            "product_name": tx.get("product_name", tx.get("product_code", "Unknown")),
            "amount": tx.get("amount", 0),
            "status": tx.get("status", "UNKNOWN"),
            "created_at": tx.get("created_at")
        }
        for tx in transactions
    ]

    if not transactions:
        text = f"""
{vs.header('Riwayat Transaksi', f'Filter: {status_filter}', icon='📜')}

{vs.empty_state('📋', 'Tidak Ada Transaksi', f'Tidak ada transaksi dengan status: {status_filter}')}
"""
    else:
        text = msg.transaction_list(tx_list)

    await safe_edit_or_send(
        query, context, user.id,
        text=text,
        reply_markup=Keyboards.history_filters()
    )


async def show_transaction_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show single transaction detail."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    # Extract transaction ID
    parts = query.data.split(":")
    transaction_id = parts[2] if len(parts) > 2 else ""

    db: Database = context.bot_data["db"]

    tx = await db.get_transaction(transaction_id)

    if not tx:
        await safe_edit_or_send(
            query, context, user.id,
            text=msg.error("Transaksi tidak ditemukan"),
            reply_markup=Keyboards.navigation(back_target="history")
        )
        return

    # Get product name
    product = await db.get_product(tx["product_code"])
    if product:
        tx["product_name"] = product["name"]

    text = format_tx_detail(tx)

    await safe_edit_or_send(
        query, context, user.id,
        text=text,
        reply_markup=Keyboards.transaction_actions(transaction_id, tx["status"])
    )


async def download_account_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download account details for paid transaction."""
    query = update.callback_query
    user = update.effective_user

    # Extract transaction ID
    parts = query.data.split(":")
    transaction_id = parts[2] if len(parts) > 2 else ""

    db: Database = context.bot_data["db"]

    tx = await db.get_transaction(transaction_id)

    if not tx:
        await query.answer("❌ Transaksi tidak ditemukan", show_alert=True)
        return

    if tx["user_id"] != user.id:
        await query.answer("❌ Bukan transaksi milikmu", show_alert=True)
        return

    if tx["status"] != "PAID":
        await query.answer("❌ Transaksi belum dibayar", show_alert=True)
        return

    # Get stock item
    stock_item = await db.get_stock_item(tx["stock_id"]) if tx.get("stock_id") else None

    if not stock_item:
        await query.answer("❌ Data akun tidak ditemukan", show_alert=True)
        return

    product = await db.get_product(tx["product_code"])

    await query.answer()
    await safe_edit_or_send(
        query, context, user.id,
        text=format_tx_success(tx, stock_item, product.get("name", "") if product else ""),
        reply_markup=Keyboards.navigation(back_target="history")
    )


async def request_refund(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Request refund for a transaction."""
    query = update.callback_query
    user = update.effective_user

    # Extract transaction ID
    parts = query.data.split(":")
    transaction_id = parts[2] if len(parts) > 2 else ""

    db: Database = context.bot_data["db"]
    payment_service = PaymentService(db)

    success, message = await payment_service.request_refund(transaction_id, user.id)

    await query.answer(message, show_alert=True)

    if success:
        text = f"""
{vs.header('Refund Requested', transaction_id[:20], icon='💰')}

{message}
"""
        await safe_edit_or_send(
            query, context, user.id,
            text=text,
            reply_markup=Keyboards.navigation(back_target="history")
        )


async def reorder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reorder an expired transaction."""
    query = update.callback_query

    # Extract transaction ID
    parts = query.data.split(":")
    transaction_id = parts[2] if len(parts) > 2 else ""

    db: Database = context.bot_data["db"]

    tx = await db.get_transaction(transaction_id)

    if not tx:
        await query.answer("❌ Transaksi tidak ditemukan", show_alert=True)
        return

    # Redirect to product page
    query.data = f"product:{tx['product_code']}"
    from handlers.user.buy import show_product_detail
    await show_product_detail(update, context)


# Handler exports
history_handlers = [
    CommandHandler("history", history_command),
    CallbackQueryHandler(show_history, pattern=r"^nav:history$"),
    CallbackQueryHandler(filter_history, pattern=r"^history:filter:"),
    CallbackQueryHandler(show_transaction_detail, pattern=r"^history:view:"),
    CallbackQueryHandler(download_account_details, pattern=r"^history:download:"),
    CallbackQueryHandler(request_refund, pattern=r"^history:refund:"),
    CallbackQueryHandler(reorder, pattern=r"^history:reorder:"),
]
