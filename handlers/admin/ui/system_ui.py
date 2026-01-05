"""
System management UI handlers.
"""

from database.db import Database
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from utils.admin_keyboards import AdminKeyboards
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

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
        text = f"{vs.header('Statistics', '', icon='📊')}\n\n"
        text += f"👥 {uf.bold('Users:')} {uf.monospace(str(stats.get('total_users', 0)))}\n"
        text += f"📦 {uf.bold('Products:')} {uf.monospace(str(stats.get('total_products', 0)))}\n"
        text += f"💰 {uf.bold('Transactions:')} {uf.monospace(str(stats.get('total_transactions', 0)))}\n"
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        text = f"{vs.header('Statistics', '', icon='📊')}\n\n{uf.italic('Error loading statistics.')}"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.system_menu())


async def show_logs(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent logs."""
    text = f"{vs.header('Recent Logs', '', icon='🔧')}\n\n"
    text += f"{uf.italic('Use')} {uf.monospace('/logs')} {uf.italic('command for full log access.')}\n\n"
    text += f"{uf.bold('Quick Commands:')}\n"
    text += f"{uf.monospace('/logs 20')} - Last 20 lines\n"
    text += f"{uf.monospace('/logs error')} - Error logs only"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.system_menu())


async def show_backup_options(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show backup options."""
    text = f"{vs.header('Database Backup', '', icon='💾')}\n\n"
    text += f"{uf.bold('Commands:')}\n"
    text += f"{uf.monospace('/backup')} - Create backup now\n"
    text += f"{uf.monospace('/restore')} - Restore from backup\n\n"
    text += f"{uf.italic('Automatic backups run daily at 3:00 AM WIB.')}"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.system_menu())


async def show_broadcast_menu(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show broadcast menu."""
    text = f"{vs.header('Broadcast Message', '', icon='📢')}\n\n"
    text += f"{uf.italic('Use')} {uf.monospace('/broadcast')} {uf.italic('command to send messages.')}\n\n"
    text += f"{uf.bold('Targets:')}\n"
    text += "• All users\n"
    text += "• Active buyers only\n"
    text += "• New users (7 days)"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.system_menu())


async def show_admin_list(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin list."""
    db: Database = context.bot_data["db"]
    admins = await db.get_admins()

    lines = [f"{vs.header('Admin List', '', icon='👥')}"]

    for idx, admin in enumerate(admins, 1):
        user_id = admin.get("user_id", admin.get("telegram_id"))
        username = admin.get("username", "N/A")
        role = "👑 Super" if admin.get("is_super") else "👤 Admin"

        lines.append(f"{uf.bold(f'{idx}.')} {role}")
        lines.append(f"   ID: {uf.monospace(str(user_id))}")
        lines.append(f"   @{username}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"\n{uf.bold('Total:')} {uf.monospace(str(len(admins)))} admins")

    text = "\n".join(lines)

    await query.edit_message_text(text, reply_markup=AdminKeyboards.system_menu())


async def show_security_dashboard(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show security dashboard."""
    db: Database = context.bot_data["db"]

    banned_count = await db.get_banned_user_count()

    text = f"{vs.header('Security Dashboard', '', icon='🔒')}\n\n"
    text += f"🚫 {uf.bold('Banned Users:')} {uf.monospace(str(banned_count))}\n\n"
    text += f"{uf.bold('Commands:')}\n"
    text += f"{uf.monospace('/ban <user_id>')} - Ban user\n"
    text += f"{uf.monospace('/unban <user_id>')} - Unban user\n"
    text += f"{uf.monospace('/listbanned')} - Show banned users"

    await query.edit_message_text(text, reply_markup=AdminKeyboards.system_menu())


# Handler exports
system_ui_handlers = [
    CallbackQueryHandler(handle_system_action, pattern=r"^admin:system:"),
]
