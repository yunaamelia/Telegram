"""
Security handlers for FRIENDS Store Telegram Bot.
"""

from database.db import Database
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from utils.logger import get_logger
from utils.unicode_fonts import UnicodeFonts as uf
from utils.visual_system import VisualSystem as vs

logger = get_logger("admin")


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is an admin."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    return await db.is_admin(user.id)


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ban command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if len(args) < 2:
        text = f"""
{vs.header('Ban User', '', icon='🚫')}

{uf.bold('Usage:')} {uf.monospace('/ban <user_id> <reason>')}
"""
        await update.message.reply_text(text)
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID harus berupa angka.")
        return

    reason = " ".join(args[1:])

    db: Database = context.bot_data["db"]

    # Check if user exists
    user = await db.get_user(user_id)
    if not user:
        await update.message.reply_text("❌ User tidak ditemukan.")
        return

    # Check if already banned
    is_banned, _ = await db.is_user_banned(user_id)
    if is_banned:
        await update.message.reply_text(f"ℹ️ User {user_id} sudah diblokir.")
        return

    # Ban user
    await db.ban_user(user_id, reason)
    logger.info(f"User banned: user_id={user_id}, reason={reason}, by={update.effective_user.id}")

    # Log security event
    await db.log_security_event(
        action="USER_BANNED", user_id=user_id, details=f"Banned by {update.effective_user.id}. Reason: {reason}"
    )

    text = f"""
🚫 {uf.bold('User diblokir!')}

👤 {uf.bold('User:')} {uf.monospace(str(user_id))} (@{user.get('username', 'N/A')})
📝 {uf.bold('Alasan:')} {reason}
"""
    await update.message.reply_text(text)


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unban command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(f"{uf.bold('Usage:')} /unban <user_id>")
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID harus berupa angka.")
        return

    db: Database = context.bot_data["db"]

    # Check if banned
    is_banned, _ = await db.is_user_banned(user_id)
    if not is_banned:
        await update.message.reply_text(f"ℹ️ User {user_id} tidak diblokir.")
        return

    await db.unban_user(user_id)
    logger.info(f"User unbanned: user_id={user_id}, by={update.effective_user.id}")

    # Log security event
    await db.log_security_event(
        action="USER_UNBANNED", user_id=user_id, details=f"Unbanned by {update.effective_user.id}"
    )

    await update.message.reply_text(f"✅ User {uf.monospace(str(user_id))} berhasil di-unban.")


async def banlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /banlist command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    db: Database = context.bot_data["db"]

    banned_users = await db.get_banned_users()

    if not banned_users:
        await update.message.reply_text("🚫 Tidak ada user yang diblokir.")
        return

    lines = [f"{vs.header('Banned Users', '', icon='🚫')}"]

    for user in banned_users:
        lines.append(
            f"• {uf.monospace(str(user['user_id']))} @{user.get('username', 'N/A')}\n"
            f"  {uf.bold('Reason:')} {user.get('ban_reason', 'N/A')}"
        )

    await update.message.reply_text("\n".join(lines))


async def security_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /security command - show security dashboard."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    db: Database = context.bot_data["db"]

    # Get recent security logs
    logs = await db.get_security_logs(limit=10)
    banned = await db.get_banned_users()

    lines = [
        f"{vs.header('Security Dashboard', '', icon='🔒')}",
        f"🚫 {uf.bold('Banned Users:')} {len(banned)}",
        f"\n{uf.bold('📋 Recent Events:')}",
    ]

    if logs:
        for log in logs[:10]:
            lines.append(
                f"• {log['action']} - User {uf.monospace(str(log.get('user_id', 'N/A')))}\n"
                f"  {log.get('details', '')[:50]}"
            )
    else:
        lines.append(f"{uf.italic('No recent events')}")

    await update.message.reply_text("\n".join(lines))


async def userstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /userstats command - view user statistics."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(f"{uf.bold('Usage:')} /userstats <user_id>")
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID harus berupa angka.")
        return

    db: Database = context.bot_data["db"]

    user = await db.get_user(user_id)
    if not user:
        await update.message.reply_text("❌ User tidak ditemukan.")
        return

    transactions = await db.get_user_transactions(user_id, limit=50)

    paid_count = sum(1 for t in transactions if t["status"] == "PAID")
    total_spent = sum(t["amount"] for t in transactions if t["status"] == "PAID")

    is_banned, ban_reason = await db.is_user_banned(user_id)

    text = f"""
{vs.header('User Statistics', '', icon='👤')}

🆔 {uf.bold('ID:')} {uf.monospace(str(user_id))}
👤 {uf.bold('Username:')} @{user.get('username', 'N/A')}
📛 {uf.bold('Name:')} {user.get('first_name', '')} {user.get('last_name', '')}
📅 {uf.bold('Joined:')} {user.get('join_date', 'N/A')}
🚫 {uf.bold('Banned:')} {'Yes' if is_banned else 'No'}
"""

    if is_banned:
        text += f"📝 {uf.bold('Ban Reason:')} {ban_reason}\n"

    text += f"""
{uf.bold('📊 Transaction Stats:')}
✅ {uf.bold('Total Paid:')} {uf.monospace(str(paid_count))}
💰 {uf.bold('Total Spent:')} {uf.monospace(f"Rp {total_spent:,}".replace(',', '.'))}
"""

    await update.message.reply_text(text)


# Handler exports
security_handlers = [
    CommandHandler("ban", ban_command),
    CommandHandler("unban", unban_command),
    CommandHandler("banlist", banlist_command),
    CommandHandler("security", security_command),
    CommandHandler("userstats", userstats_command),
]
