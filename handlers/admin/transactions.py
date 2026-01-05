"""
Transaction management handlers for FRIENDS Store Telegram Bot.
"""

from database.db import Database
from services.notification import NotificationService
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

logger = get_logger("admin")


def format_currency_local(amount: int) -> str:
    """Format currency with dot separator."""
    return f"Rp {amount:,}".replace(",", ".")


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

    lines = [f"{vs.header('Transaksi Terbaru', '', icon='📋')}"]

    for tx in transactions[:20]:
        status_emoji = {
            "PAID": "✅",
            "UNPAID": "⏳",
            "EXPIRED": "❌",
            "CANCELLED": "🚫",
            "REFUND_REQUESTED": "💰",
            "REFUNDED": "💸",
        }.get(tx["status"], "❓")

        lines.append(
            f"{status_emoji} {uf.monospace(tx['merchant_ref'][:20])}\n"
            f"   @{tx.get('username', 'N/A')} | {uf.monospace(format_currency_local(tx['amount']))}"
        )

    await update.message.reply_text("\n".join(lines))


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

    lines = [f"{vs.header('Pending Refund Requests', '', icon='💰')}"]

    for tx in refunds:
        lines.append(
            f"🆔 {uf.monospace(tx['transaction_id'])}\n"
            f"   {uf.bold('User:')} @{tx.get('username', 'N/A')} (ID: {tx['user_id']})\n"
            f"   {uf.bold('Product:')} {tx.get('product_name', tx['product_code'])}\n"
            f"   {uf.bold('Amount:')} {uf.monospace(format_currency_local(tx['amount']))}"
        )

    lines.append(f"\n{uf.bold('Commands:')}")
    lines.append(f"{uf.monospace('/approverefund <transaction_id>')}")
    lines.append(f"{uf.monospace('/rejectrefund <transaction_id> <reason>')}")

    await update.message.reply_text("\n".join(lines))


async def approverefund_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /approverefund command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(f"{uf.bold('Usage:')} /approverefund <transaction_id>")
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

    text = f"""
✅ {uf.bold('Refund disetujui!')}

🆔 {uf.bold('Transaksi:')} {uf.monospace(transaction_id)}
👤 {uf.bold('User:')} {tx['user_id']} telah dinotifikasi.
"""
    await update.message.reply_text(text)


async def rejectrefund_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /rejectrefund command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(f"{uf.bold('Usage:')} /rejectrefund <transaction_id> <reason>")
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

    text = f"""
❌ {uf.bold('Refund ditolak!')}

🆔 {uf.bold('Transaksi:')} {uf.monospace(transaction_id)}
📝 {uf.bold('Reason:')} {reason}
👤 {uf.bold('User:')} {tx['user_id']} telah dinotifikasi.
"""
    await update.message.reply_text(text)


# Handler exports
transaction_handlers = [
    CommandHandler("transactions", transactions_command),
    CommandHandler("refunds", refunds_command),
    CommandHandler("approverefund", approverefund_command),
    CommandHandler("rejectrefund", rejectrefund_command),
]
