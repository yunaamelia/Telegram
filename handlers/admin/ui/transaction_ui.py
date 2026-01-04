"""
Transaction management UI handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from database.db import Database
from utils.admin_keyboards import AdminKeyboards
from utils.formatters import format_currency, format_datetime, escape_md
from utils.logger import get_logger

logger = get_logger("admin.trans_ui")


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
        await query.edit_message_text(
            "*📋 Transactions*\n\n_No transactions found\\._",
            parse_mode="MarkdownV2",
            reply_markup=AdminKeyboards.transaction_management_menu()
        )
        return
    
    lines = ["*📋 Recent Transactions*\n━━━━━━━━━━━━━━━━━━━━\n"]
    
    status_emoji = {
        "PAID": "✅",
        "UNPAID": "⏳",
        "EXPIRED": "❌",
        "CANCELLED": "🚫",
        "REFUND_REQUESTED": "💰",
        "REFUNDED": "💸"
    }
    
    for tx in transactions[:10]:
        emoji = status_emoji.get(tx["status"], "❓")
        tx_id = escape_md(tx["transaction_id"][:12])
        product = escape_md(tx.get("product_name", tx.get("product_code", "Unknown"))[:15])
        amount = escape_md(format_currency(tx["amount"]))
        
        lines.append(f"{emoji} `{tx_id}\\.\\.\\.*`")
        lines.append(f"   📦 {product}")
        lines.append(f"   💰 `{amount}`\n")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.transaction_management_menu()
    )


async def show_transactions_by_status(query, context: ContextTypes.DEFAULT_TYPE, status: str) -> None:
    """Show transactions filtered by status."""
    db: Database = context.bot_data["db"]
    transactions = await db.get_transactions_by_status(status, limit=20)
    
    status_titles = {
        "PAID": "✅ Paid Transactions",
        "UNPAID": "⏳ Unpaid Transactions",
        "EXPIRED": "❌ Expired Transactions"
    }
    
    title = status_titles.get(status, f"📋 {status} Transactions")
    
    if not transactions:
        await query.edit_message_text(
            f"*{title}*\n\n_No {status.lower()} transactions\\._",
            parse_mode="MarkdownV2",
            reply_markup=AdminKeyboards.transaction_management_menu()
        )
        return
    
    lines = [f"*{title}*\n━━━━━━━━━━━━━━━━━━━━\n"]
    lines.append(f"_Total: {len(transactions)}_\n")
    
    for tx in transactions[:10]:
        tx_id = escape_md(tx["transaction_id"][:12])
        product = escape_md(tx.get("product_name", tx.get("product_code", "Unknown"))[:15])
        amount = escape_md(format_currency(tx["amount"]))
        date = escape_md(format_datetime(tx["created_at"], include_time=False))
        
        lines.append(f"`{tx_id}\\.\\.\\.*`")
        lines.append(f"   📦 {product} \\| 💰 `{amount}`")
        lines.append(f"   📅 {date}\n")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.transaction_management_menu()
    )


async def show_refund_requests(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pending refund requests."""
    db: Database = context.bot_data["db"]
    refunds = await db.get_refund_requests()
    
    if not refunds:
        await query.edit_message_text(
            "*💸 Refund Requests*\n\n_No pending refund requests\\._",
            parse_mode="MarkdownV2",
            reply_markup=AdminKeyboards.transaction_management_menu()
        )
        return
    
    lines = ["*💸 Pending Refund Requests*\n━━━━━━━━━━━━━━━━━━━━\n"]
    lines.append(f"_Total: {len(refunds)}_\n")
    
    for tx in refunds[:10]:
        tx_id = escape_md(tx["transaction_id"][:12])
        amount = escape_md(format_currency(tx["amount"]))
        user_id = tx.get("user_id", "Unknown")
        
        lines.append(f"💰 `{tx_id}\\.\\.\\.*`")
        lines.append(f"   👤 User: `{user_id}`")
        lines.append(f"   💵 Amount: `{amount}`\n")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("\n*Commands:*")
    lines.append("`/approverefund <tx_id>`")
    lines.append("`/rejectrefund <tx_id> <reason>`")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.transaction_management_menu()
    )


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
        
        revenue_today = escape_md(format_currency(stats.get("revenue_today", 0)))
        revenue_total = escape_md(format_currency(stats.get("revenue_total", 0)))
        
        text = (
            "*📊 Transaction Summary*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "*By Status:*\n"
            f"✅ Paid: `{paid}`\n"
            f"⏳ Unpaid: `{unpaid}`\n"
            f"❌ Expired: `{expired}`\n"
            f"💸 Refunded: `{refunded}`\n"
            f"📊 Total: `{total}`\n\n"
            "*Revenue:*\n"
            f"📅 Today: `{revenue_today}`\n"
            f"💰 Total: `{revenue_total}`"
        )
    except Exception as e:
        logger.error(f"Failed to get transaction stats: {e}")
        text = "*📊 Transaction Summary*\n\n_Error loading statistics\\._"
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.transaction_management_menu()
    )


# Handler exports
transaction_ui_handlers = [
    CallbackQueryHandler(handle_trans_action, pattern=r"^admin:trans:"),
]
