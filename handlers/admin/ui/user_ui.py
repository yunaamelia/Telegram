"""
User management UI handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from database.db import Database
from utils.admin_keyboards import AdminKeyboards
from utils.formatters import format_currency, format_datetime, escape_md
from utils.logger import get_logger

logger = get_logger("admin.user_ui")


async def handle_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Route user-related callback queries.
    Pattern: admin:user:<action>
    """
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db: Database = context.bot_data["db"]
    
    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    # Parse: admin:user:all
    parts = query.data.split(":")
    action = parts[2] if len(parts) > 2 else None
    
    if action == "all":
        await show_all_users(query, context)
    elif action == "buyers":
        await show_buyers(query, context)
    elif action == "banned":
        await show_banned_users(query, context)
    elif action == "ban":
        await show_ban_info(query, context)
    elif action == "unban":
        await show_unban_info(query, context)
    elif action == "search":
        await show_search_info(query, context)
    elif action == "view":
        # admin:user:view:user_id
        user_id = int(parts[3]) if len(parts) > 3 else None
        await show_user_detail(query, context, user_id)


async def show_all_users(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all users summary."""
    db: Database = context.bot_data["db"]
    
    total_users = await db.get_user_count()
    active_today = await db.get_active_users_count(days=1)
    active_week = await db.get_active_users_count(days=7)
    banned_count = await db.get_banned_user_count()
    
    # Get recent users
    recent_users = await db.get_recent_users(limit=5)
    
    lines = [
        "*👥 User Statistics*",
        "━━━━━━━━━━━━━━━━━━━━\n",
        f"📊 *Total Users:* `{total_users}`",
        f"🟢 *Active Today:* `{active_today}`",
        f"📈 *Active This Week:* `{active_week}`",
        f"🚫 *Banned:* `{banned_count}`\n",
        "*Recent Registrations:*"
    ]
    
    for user in recent_users:
        username = escape_md(user.get('username', 'N/A'))
        user_id = user.get('telegram_id', user.get('user_id'))
        lines.append(f"• @{username} \\(`{user_id}`\\)")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.user_management_menu()
    )


async def show_buyers(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users who have made purchases."""
    db: Database = context.bot_data["db"]
    
    buyers = await db.get_buyers(limit=10)
    
    if not buyers:
        await query.edit_message_text(
            "*💰 Buyers*\n\n_No buyers yet\\._",
            parse_mode="MarkdownV2",
            reply_markup=AdminKeyboards.user_management_menu()
        )
        return
    
    lines = [
        "*💰 Top Buyers*",
        "━━━━━━━━━━━━━━━━━━━━\n"
    ]
    
    for idx, buyer in enumerate(buyers, 1):
        username = escape_md(buyer.get('username', 'N/A'))
        user_id = buyer.get('telegram_id', buyer.get('user_id'))
        total_purchases = buyer.get('purchase_count', 0)
        total_spent = escape_md(format_currency(buyer.get('total_spent', 0)))
        
        lines.append(f"*{idx}\\.* @{username}")
        lines.append(f"   ID: `{user_id}`")
        lines.append(f"   🛒 `{total_purchases}` purchases \\| 💰 `{total_spent}`\n")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.user_management_menu()
    )


async def show_banned_users(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show banned users list."""
    db: Database = context.bot_data["db"]
    
    banned = await db.get_banned_users()
    
    if not banned:
        await query.edit_message_text(
            "*🚫 Banned Users*\n\n_No banned users\\._",
            parse_mode="MarkdownV2",
            reply_markup=AdminKeyboards.user_management_menu()
        )
        return
    
    lines = [
        "*🚫 Banned Users*",
        "━━━━━━━━━━━━━━━━━━━━\n",
        f"_Total: {len(banned)}_\n"
    ]
    
    for user in banned[:10]:
        username = escape_md(user.get('username', 'N/A'))
        user_id = user.get('telegram_id', user.get('user_id'))
        reason = escape_md(user.get('ban_reason', 'No reason'))
        
        lines.append(f"🚫 @{username} \\(`{user_id}`\\)")
        lines.append(f"   _Reason: {reason}_\n")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("\n`/unban <user_id>` to unban")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.user_management_menu()
    )


async def show_ban_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show ban command info."""
    text = (
        "*🔒 Ban User*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Use command to ban:_\n\n"
        "`/ban <user_id> [reason]`\n\n"
        "*Examples:*\n"
        "`/ban 123456789`\n"
        "`/ban 123456789 Spam`\n"
        "`/ban 123456789 Fraud attempt`"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.user_management_menu()
    )


async def show_unban_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show unban command info."""
    text = (
        "*🔓 Unban User*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Use command to unban:_\n\n"
        "`/unban <user_id>`\n\n"
        "*Example:*\n"
        "`/unban 123456789`"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.user_management_menu()
    )


async def show_search_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user search info."""
    text = (
        "*🔍 Search User*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Use command to search:_\n\n"
        "`/searchuser <query>`\n\n"
        "*Examples:*\n"
        "`/searchuser 123456789` \\- By ID\n"
        "`/searchuser @username` \\- By username"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.user_management_menu()
    )


async def show_user_detail(query, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Show user detail."""
    db: Database = context.bot_data["db"]
    
    user = await db.get_user(user_id)
    
    if not user:
        await query.edit_message_text(
            "❌ User not found\\.",
            parse_mode="MarkdownV2",
            reply_markup=AdminKeyboards.user_management_menu()
        )
        return
    
    username = escape_md(user.get('username', 'N/A'))
    first_name = escape_md(user.get('first_name', 'N/A'))
    created = escape_md(format_datetime(user.get('created_at')))
    is_banned = user.get('is_banned', False)
    status = "🚫 Banned" if is_banned else "✅ Active"
    
    # Get purchase history
    purchases = await db.get_user_transactions(user_id, limit=5)
    
    lines = [
        f"*👤 User Detail*",
        "━━━━━━━━━━━━━━━━━━━━\n",
        f"*ID:* `{user_id}`",
        f"*Username:* @{username}",
        f"*Name:* {first_name}",
        f"*Status:* {status}",
        f"*Registered:* {created}\n",
    ]
    
    if purchases:
        lines.append("*Recent Purchases:*")
        for tx in purchases[:5]:
            product = escape_md(tx.get('product_name', tx.get('product_code', 'Unknown')))
            amount = escape_md(format_currency(tx['amount']))
            lines.append(f"• {product} \\- `{amount}`")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.user_management_menu()
    )


# Handler exports
user_ui_handlers = [
    CallbackQueryHandler(handle_user_action, pattern=r"^admin:user:"),
]
