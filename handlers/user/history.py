"""
Transaction history handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler

from database.db import Database
from services.payment import PaymentService
from utils.keyboards import Keyboards
from utils.formatters import (
    format_transaction_list,
    format_transaction_detail,
    format_payment_success
)
from utils.messages import safe_edit_or_send
from utils.logger import get_logger

logger = get_logger("bot")


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
    text = format_transaction_list(transactions)

    if is_command:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=Keyboards.history_filters()
        )
    else:
        query = update.callback_query
        await query.answer()
        await safe_edit_or_send(
            query, context, user.id,
            text=text,
            parse_mode="Markdown",
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

    text = format_transaction_list(transactions)

    if not transactions:
        text = f"📜 Tidak ada transaksi dengan status: {status_filter}"

    await safe_edit_or_send(
        query, context, user.id,
        text=text,
        parse_mode="Markdown",
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
            text="❌ Transaksi tidak ditemukan.",
            reply_markup=Keyboards.navigation(back_target="history")
        )
        return

    # Get product name
    product = await db.get_product(tx["product_code"])
    if product:
        tx["product_name"] = product["name"]

    text = format_transaction_detail(tx)

    await safe_edit_or_send(
        query, context, user.id,
        text=text,
        parse_mode="Markdown",
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
        text=format_payment_success(
            transaction_id=tx["merchant_ref"],
            product_name=product.get("name", "") if product else "",
            amount=tx["amount"],
            paid_at=tx.get("paid_at"),
            stock_item=stock_item
        ),
        parse_mode="Markdown",
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
        await safe_edit_or_send(
            query, context, user.id,
            text=f"💰 **Refund Requested**\n\n"
            f"Order ID: `{transaction_id}`\n\n"
            f"{message}",
            parse_mode="Markdown",
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

