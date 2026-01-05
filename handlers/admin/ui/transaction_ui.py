"""
Transaction management UI handlers.
"""

from database.db import Database
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from utils.admin_keyboards import AdminKeyboards
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

logger = get_logger("admin.trans_ui")


def format_currency_local(amount: int) -> str:
    """Format currency with dot separator."""
    return f"Rp {amount:,}".replace(",", ".")


def format_datetime_local(dt) -> str:
    """Format datetime for display."""
    if hasattr(dt, "strftime"):
        return dt.strftime("%d/%m/%Y")
    return str(dt)[:10] if dt else "N/A"


async def handle_trans_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Route transaction-related callback queries.
    Pattern: admin:trans:<action>
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return

    # Parse: admin:trans:all
    parts = query.data.split(":")
    action = parts[2] if len(parts) > 2 else None

    if action == "all":
        await show_all_transactions(query, context)
    elif action == "unpaid":
        await show_transactions_by_status(query, context, "UNPAID")
    elif action == "paid":
        await show_transactions_by_status(query, context, "PAID")
    elif action == "expired":
        await show_transactions_by_status(query, context, "EXPIRED")
    elif action == "refunds":
        await show_refund_requests(query, context)
    elif action == "summary":
        await show_transaction_summary(query, context)


async def show_all_transactions(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all recent transactions."""
    db: Database = context.bot_data["db"]
    transactions = await db.get_all_transactions(limit=20)

    if not transactions:
        text = f"{vs.header('Transactions', '', icon='📋')}\n\n"
        text += f"{uf.italic('No transactions found.')}"
        await query.edit_message_text(text, reply_markup=AdminKeyboards.transaction_management_menu())
        return

    lines = [f"{vs.header('Recent Transactions', '', icon='📋')}"]

    status_emoji = {
        "PAID": "✅",
        "UNPAID": "⏳",
        "EXPIRED": "❌",
        "CANCELLED": "🚫",
        "REFUND_REQUESTED": "💰",
        "REFUNDED": "💸",
    }

    for tx in transactions[:10]:
        emoji = status_emoji.get(tx["status"], "❓")
        tx_id = tx["transaction_id"][:12]
        product = tx.get("product_name", tx.get("product_code", "Unknown"))[:15]
        amount = format_currency_local(tx["amount"])

        lines.append(f"{emoji} {uf.monospace(tx_id + '...')}")
        lines.append(f"   📦 {product}")
        lines.append(f"   💰 {uf.monospace(amount)}")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.transaction_management_menu())


async def show_transactions_by_status(query, context: ContextTypes.DEFAULT_TYPE, status: str) -> None:
    """Show transactions filtered by status."""
    db: Database = context.bot_data["db"]
    transactions = await db.get_transactions_by_status(status, limit=20)

    status_titles = {
        "PAID": "✅ Paid Transactions",
        "UNPAID": "⏳ Unpaid Transactions",
        "EXPIRED": "❌ Expired Transactions",
    }

    title = status_titles.get(status, f"📋 {status} Transactions")

    if not transactions:
        text = f"{vs.header(title, '', icon='')}\n\n"
        text += f"{uf.italic(f'No {status.lower()} transactions.')}"
        await query.edit_message_text(text, reply_markup=AdminKeyboards.transaction_management_menu())
        return

    lines = [f"{vs.header(title, '', icon='')}"]
    lines.append(f"{uf.italic(f'Total: {len(transactions)}')}")

    for tx in transactions[:10]:
        tx_id = tx["transaction_id"][:12]
        product = tx.get("product_name", tx.get("product_code", "Unknown"))[:15]
        amount = format_currency_local(tx["amount"])
        date = format_datetime_local(tx.get("created_at"))

        lines.append(f"{uf.monospace(tx_id + '...')}")
        lines.append(f"   📦 {product} | 💰 {uf.monospace(amount)}")
        lines.append(f"   📅 {date}")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.transaction_management_menu())


async def show_refund_requests(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pending refund requests."""
    db: Database = context.bot_data["db"]
    refunds = await db.get_refund_requests()

    if not refunds:
        text = f"{vs.header('Refund Requests', '', icon='💸')}\n\n"
        text += f"{uf.italic('No pending refund requests.')}"
        await query.edit_message_text(text, reply_markup=AdminKeyboards.transaction_management_menu())
        return

    lines = [f"{vs.header('Pending Refund Requests', '', icon='💸')}"]
    lines.append(f"{uf.italic(f'Total: {len(refunds)}')}")

    for tx in refunds[:10]:
        tx_id = tx["transaction_id"][:12]
        amount = format_currency_local(tx["amount"])
        user_id = tx.get("user_id", "Unknown")

        lines.append(f"💰 {uf.monospace(tx_id + '...')}")
        lines.append(f"   👤 User: {uf.monospace(str(user_id))}")
        lines.append(f"   💵 Amount: {uf.monospace(amount)}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"\n{uf.bold('Commands:')}")
    lines.append(f"{uf.monospace('/approverefund <tx_id>')}")
    lines.append(f"{uf.monospace('/rejectrefund <tx_id> <reason>')}")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.transaction_management_menu())


async def show_transaction_summary(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show transaction summary/statistics."""
    db: Database = context.bot_data["db"]

    try:
        stats = await db.get_transaction_stats()

        paid = stats.get("PAID", 0)
        unpaid = stats.get("UNPAID", 0)
        expired = stats.get("EXPIRED", 0)
        refunded = stats.get("REFUNDED", 0)
        total = paid + unpaid + expired + refunded

        revenue_today = format_currency_local(stats.get("revenue_today", 0))
        revenue_total = format_currency_local(stats.get("revenue_total", 0))

        text = f"{vs.header('Transaction Summary', '', icon='📊')}\n\n"
        text += f"{uf.bold('By Status:')}\n"
        text += f"✅ Paid: {uf.monospace(str(paid))}\n"
        text += f"⏳ Unpaid: {uf.monospace(str(unpaid))}\n"
        text += f"❌ Expired: {uf.monospace(str(expired))}\n"
        text += f"💸 Refunded: {uf.monospace(str(refunded))}\n"
        text += f"📊 Total: {uf.monospace(str(total))}\n\n"
        text += f"{uf.bold('Revenue:')}\n"
        text += f"📅 Today: {uf.monospace(revenue_today)}\n"
        text += f"💰 Total: {uf.monospace(revenue_total)}"
    except Exception as e:
        logger.error(f"Failed to get transaction stats: {e}")
        text = f"{vs.header('Transaction Summary', '', icon='📊')}\n\n"
        text += f"{uf.italic('Error loading statistics.')}"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.transaction_management_menu())


# Handler exports
transaction_ui_handlers = [
    CallbackQueryHandler(handle_trans_action, pattern=r"^admin:trans:"),
]
