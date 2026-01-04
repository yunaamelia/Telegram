"""
System management UI handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from database.db import Database
from utils.admin_keyboards import AdminKeyboards
from utils.formatters import format_currency, format_stats, escape_md
from utils.logger import get_logger

logger = get_logger("admin.system_ui")


async def handle_system_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Route system-related callback queries.
    Pattern: admin:system:<action>
    """
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    db: Database = context.bot_data["db"]
    
    if not await db.is_admin(user.id):
        await query.answer("⛔ Access denied", show_alert=True)
        return
    
    # Parse: admin:system:stats
    parts = query.data.split(":")
    action = parts[2] if len(parts) > 2 else None
    
    if action == "stats":
        await show_statistics(query, context)
    elif action == "logs":
        await show_logs(query, context)
    elif action == "backup":
        await show_backup_options(query, context)
    elif action == "broadcast":
        await show_broadcast_menu(query, context)
    elif action == "admins":
        await show_admin_list(query, context)
    elif action == "security":
        await show_security_dashboard(query, context)


async def show_statistics(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics."""
    db: Database = context.bot_data["db"]
    
    try:
        stats = await db.get_statistics()
        text = format_stats(stats)
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        text = "*📊 Statistics*\n\n_Error loading statistics\\._"
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.system_menu()
    )


async def show_logs(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent logs."""
    text = (
        "*🔧 Recent Logs*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Use `/logs` command for full log access\\._\n\n"
        "*Quick Commands:*\n"
        "`/logs 20` \\- Last 20 lines\n"
        "`/logs error` \\- Error logs only"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.system_menu()
    )


async def show_backup_options(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show backup options."""
    text = (
        "*💾 Database Backup*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "*Commands:*\n"
        "`/backup` \\- Create backup now\n"
        "`/restore` \\- Restore from backup\n\n"
        "_Automatic backups run daily at 3:00 AM WIB\\._"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.system_menu()
    )


async def show_broadcast_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show broadcast menu."""
    text = (
        "*📢 Broadcast Message*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "_Use `/broadcast` command to send messages\\._\n\n"
        "*Targets:*\n"
        "• All users\n"
        "• Active buyers only\n"
        "• New users \\(7 days\\)\n"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.system_menu()
    )


async def show_admin_list(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin list."""
    db: Database = context.bot_data["db"]
    admins = await db.get_admins()
    
    lines = ["*👥 Admin List*\n━━━━━━━━━━━━━━━━━━━━\n"]
    
    for idx, admin in enumerate(admins, 1):
        user_id = admin.get('user_id', admin.get('telegram_id'))
        username = escape_md(admin.get('username', 'N/A'))
        role = "👑 Super" if admin.get('is_super') else "👤 Admin"
        
        lines.append(f"*{idx}\\.* {role}")
        lines.append(f"   ID: `{user_id}`")
        lines.append(f"   @{username}\n")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"\n*Total:* `{len(admins)}` admins")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.system_menu()
    )


async def show_security_dashboard(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show security dashboard."""
    db: Database = context.bot_data["db"]
    
    banned_count = await db.get_banned_user_count()
    
    text = (
        "*🔒 Security Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🚫 *Banned Users:* `{banned_count}`\n\n"
        "*Commands:*\n"
        "`/ban <user_id>` \\- Ban user\n"
        "`/unban <user_id>` \\- Unban user\n"
        "`/listbanned` \\- Show banned users"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=AdminKeyboards.system_menu()
    )


# Handler exports
system_ui_handlers = [
    CallbackQueryHandler(handle_system_action, pattern=r"^admin:system:"),
]
