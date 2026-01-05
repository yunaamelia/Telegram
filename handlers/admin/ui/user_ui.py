"""
User management UI handlers.
"""

from database.db import Database
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from utils.admin_keyboards import AdminKeyboards
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

logger = get_logger("admin.user_ui")


def format_currency_local(amount: int) -> str:
    """Format currency with dot separator."""
    return f"Rp {amount:,}".replace(",", ".")


def format_datetime_local(dt) -> str:
    """Format datetime for display."""
    if hasattr(dt, "strftime"):
        return dt.strftime("%d/%m/%Y %H:%M")
    return str(dt)[:16] if dt else "N/A"


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

    lines = [f"{vs.header('User Statistics', '', icon='👥')}"]
    lines.append(f"📊 {uf.bold('Total Users:')} {uf.monospace(str(total_users))}")
    lines.append(f"🟢 {uf.bold('Active Today:')} {uf.monospace(str(active_today))}")
    lines.append(f"📈 {uf.bold('Active This Week:')} {uf.monospace(str(active_week))}")
    lines.append(f"🚫 {uf.bold('Banned:')} {uf.monospace(str(banned_count))}")
    lines.append(f"\n{uf.bold('Recent Registrations:')}")

    for user in recent_users:
        username = user.get("username", "N/A")
        user_id = user.get("telegram_id", user.get("user_id"))
        lines.append(f"• @{username} ({uf.monospace(str(user_id))})")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())


async def show_buyers(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show users who have made purchases."""
    db: Database = context.bot_data["db"]

    buyers = await db.get_buyers(limit=10)

    if not buyers:
        text = f"{vs.header('Buyers', '', icon='💰')}\n\n{uf.italic('No buyers yet.')}"
        await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())
        return

    lines = [f"{vs.header('Top Buyers', '', icon='💰')}"]

    for idx, buyer in enumerate(buyers, 1):
        username = buyer.get("username", "N/A")
        user_id = buyer.get("telegram_id", buyer.get("user_id"))
        total_purchases = buyer.get("purchase_count", 0)
        total_spent = format_currency_local(buyer.get("total_spent", 0))

        lines.append(f"{uf.bold(f'{idx}.')} @{username}")
        lines.append(f"   ID: {uf.monospace(str(user_id))}")
        lines.append(f"   🛒 {uf.monospace(str(total_purchases))} purchases | 💰 {uf.monospace(total_spent)}")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())


async def show_banned_users(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show banned users list."""
    db: Database = context.bot_data["db"]

    banned = await db.get_banned_users()

    if not banned:
        text = f"{vs.header('Banned Users', '', icon='🚫')}\n\n{uf.italic('No banned users.')}"
        await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())
        return

    lines = [f"{vs.header('Banned Users', '', icon='🚫')}"]
    lines.append(f"{uf.italic(f'Total: {len(banned)}')}")

    for user in banned[:10]:
        username = user.get("username", "N/A")
        user_id = user.get("telegram_id", user.get("user_id"))
        reason = user.get("ban_reason", "No reason")

        lines.append(f"🚫 @{username} ({uf.monospace(str(user_id))})")
        lines.append(f"   {uf.italic(f'Reason: {reason}')}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"\n{uf.monospace('/unban <user_id>')} to unban")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())


async def show_ban_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show ban command info."""
    text = f"{vs.header('Ban User', '', icon='🔒')}\n\n"
    text += f"{uf.italic('Use command to ban:')}\n\n"
    text += f"{uf.monospace('/ban <user_id> [reason]')}\n\n"
    text += f"{uf.bold('Examples:')}\n"
    text += f"{uf.monospace('/ban 123456789')}\n"
    text += f"{uf.monospace('/ban 123456789 Spam')}\n"
    text += f"{uf.monospace('/ban 123456789 Fraud attempt')}"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())


async def show_unban_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show unban command info."""
    text = f"{vs.header('Unban User', '', icon='🔓')}\n\n"
    text += f"{uf.italic('Use command to unban:')}\n\n"
    text += f"{uf.monospace('/unban <user_id>')}\n\n"
    text += f"{uf.bold('Example:')}\n"
    text += f"{uf.monospace('/unban 123456789')}"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())


async def show_search_info(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user search info."""
    text = f"{vs.header('Search User', '', icon='🔍')}\n\n"
    text += f"{uf.italic('Use command to search:')}\n\n"
    text += f"{uf.monospace('/searchuser <query>')}\n\n"
    text += f"{uf.bold('Examples:')}\n"
    text += f"{uf.monospace('/searchuser 123456789')} - By ID\n"
    text += f"{uf.monospace('/searchuser @username')} - By username"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())


async def show_user_detail(query, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Show user detail."""
    db: Database = context.bot_data["db"]

    user = await db.get_user(user_id)

    if not user:
        await query.edit_message_text("❌ User not found.", reply_markup=AdminKeyboards.user_management_menu())
        return

    username = user.get("username", "N/A")
    first_name = user.get("first_name", "N/A")
    created = format_datetime_local(user.get("created_at"))
    is_banned = user.get("is_banned", False)
    status = "🚫 Banned" if is_banned else "✅ Active"

    # Get purchase history
    purchases = await db.get_user_transactions(user_id, limit=5)

    lines = [f"{vs.header('User Detail', '', icon='👤')}"]
    lines.append(f"{uf.bold('ID:')} {uf.monospace(str(user_id))}")
    lines.append(f"{uf.bold('Username:')} @{username}")
    lines.append(f"{uf.bold('Name:')} {first_name}")
    lines.append(f"{uf.bold('Status:')} {status}")
    lines.append(f"{uf.bold('Registered:')} {created}")

    if purchases:
        lines.append(f"\n{uf.bold('Recent Purchases:')}")
        for tx in purchases[:5]:
            product = tx.get("product_name", tx.get("product_code", "Unknown"))
            amount = format_currency_local(tx["amount"])
            lines.append(f"• {product} - {uf.monospace(amount)}")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.user_management_menu())


# Handler exports
user_ui_handlers = [
    CallbackQueryHandler(handle_user_action, pattern=r"^admin:user:"),
]
