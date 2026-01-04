"""
Transaction management handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.db import Database
from services.notification import NotificationService
from utils.formatters import format_currency, escape_md
from utils.logger import get_logger

logger = get_logger("admin")


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is an admin."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    return await db.is_admin(user.id)


async def transactions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /transactions command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    status = args[0].upper() if args else None
    limit = int(args[1]) if len(args) > 1 else 20

    db: Database = context.bot_data["db"]

    if status:
        transactions = await db.get_transactions_by_status(status, limit=limit)
    else:
        # Get mixed transactions
        transactions = []
        for s in ["UNPAID", "PAID", "EXPIRED"]:
            txs = await db.get_transactions_by_status(s, limit=10)
            transactions.extend(txs)

    if not transactions:
        await update.message.reply_text("📋 Tidak ada transaksi.")
        return

    lines = ["📋 *Transaksi Terbaru*\n"]

    for tx in transactions[:20]:
        status_emoji = {
            "PAID": "✅",
            "UNPAID": "⏳",
            "EXPIRED": "❌",
            "CANCELLED": "🚫",
            "REFUND_REQUESTED": "💰",
            "REFUNDED": "💸"
        }.get(tx["status"], "❓")

        lines.append(
            f"{status_emoji} `{escape_md(tx['merchant_ref'][:20])}`\n"
            f"   @{escape_md(tx.get('username', 'N/A'))} \| `{escape_md(format_currency(tx['amount']))}`\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


async def refunds_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /refunds command - list pending refund requests."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    db: Database = context.bot_data["db"]

    refunds = await db.get_transactions_by_status("REFUND_REQUESTED", limit=50)

    if not refunds:
        await update.message.reply_text("💰 Tidak ada permintaan refund.")
        return

    lines = ["💰 *Pending Refund Requests*\n"]

    for tx in refunds:
        lines.append(
            f"🆔 `{escape_md(tx['transaction_id'])}`\n"
            f"   User: @{escape_md(tx.get('username', 'N/A'))} \(ID: `{tx['user_id']}`\)\n"
            f"   Product: {escape_md(tx.get('product_name', tx['product_code']))}\n"
            f"   Amount: `{escape_md(format_currency(tx['amount']))}`\n"
        )

    lines.append("\n*Commands:*")
    lines.append("`/approverefund <transaction_id>`")
    lines.append("`/rejectrefund <transaction_id> <reason>`")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


async def approverefund_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /approverefund command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/approverefund <transaction_id>`", parse_mode="MarkdownV2")
        return

    transaction_id = args[0]
    db: Database = context.bot_data["db"]

    tx = await db.get_transaction(transaction_id)
    if not tx:
        await update.message.reply_text("❌ Transaksi tidak ditemukan.")
        return

    if tx["status"] != "REFUND_REQUESTED":
        await update.message.reply_text(f"❌ Status bukan REFUND_REQUESTED: {tx['status']}")
        return

    # Update status
    await db.update_transaction_status(transaction_id, "REFUNDED")
    logger.info(f"Refund approved: tx={transaction_id}, user={tx['user_id']}, by={update.effective_user.id}")

    # Notify user
    notification = NotificationService(context.bot, db)
    await notification.send_refund_notification(tx["user_id"], approved=True)

    await update.message.reply_text(
        f"✅ Refund disetujui untuk transaksi `{escape_md(transaction_id)}`\n"
        f"User `{tx['user_id']}` telah dinotifikasi\.",
        parse_mode="MarkdownV2"
    )


async def rejectrefund_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /rejectrefund command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/rejectrefund <transaction_id> <reason>`",
            parse_mode="MarkdownV2"
        )
        return

    transaction_id = args[0]
    reason = " ".join(args[1:])

    db: Database = context.bot_data["db"]

    tx = await db.get_transaction(transaction_id)
    if not tx:
        await update.message.reply_text("❌ Transaksi tidak ditemukan.")
        return

    if tx["status"] != "REFUND_REQUESTED":
        await update.message.reply_text(f"❌ Status bukan REFUND_REQUESTED: {tx['status']}")
        return

    # Update back to PAID (refund rejected)
    await db.update_transaction_status(transaction_id, "PAID")
    logger.info(f"Refund rejected: tx={transaction_id}, reason={reason}, by={update.effective_user.id}")

    # Notify user
    notification = NotificationService(context.bot, db)
    await notification.send_refund_notification(tx["user_id"], approved=False, reason=reason)

    await update.message.reply_text(
        f"❌ Refund ditolak untuk transaksi `{escape_md(transaction_id)}`\n"
        f"Reason: {escape_md(reason)}\n"
        f"User `{tx['user_id']}` telah dinotifikasi\.",
        parse_mode="MarkdownV2"
    )


# Handler exports
transaction_handlers = [
    CommandHandler("transactions", transactions_command),
    CommandHandler("refunds", refunds_command),
    CommandHandler("approverefund", approverefund_command),
    CommandHandler("rejectrefund", rejectrefund_command),
]
