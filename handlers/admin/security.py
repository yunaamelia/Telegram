"""
Security handlers for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from database.db import Database
from utils.logger import get_logger

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
        await update.message.reply_text(
            "🚫 **Ban User**\n\n"
            "Usage: `/ban <user_id> <reason>`",
            parse_mode="Markdown"
        )
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

    # Log security event
    await db.log_security_event(
        action="USER_BANNED",
        user_id=user_id,
        details=f"Banned by {update.effective_user.id}. Reason: {reason}"
    )

    await update.message.reply_text(
        f"🚫 User `{user_id}` (@{user.get('username', 'N/A')}) diblokir.\n"
        f"Alasan: {reason}",
        parse_mode="Markdown"
    )


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unban command."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/unban <user_id>`", parse_mode="Markdown")
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

    # Log security event
    await db.log_security_event(
        action="USER_UNBANNED",
        user_id=user_id,
        details=f"Unbanned by {update.effective_user.id}"
    )

    await update.message.reply_text(f"✅ User `{user_id}` berhasil di-unban.", parse_mode="Markdown")


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

    lines = ["🚫 **Banned Users**\n"]

    for user in banned_users:
        lines.append(
            f"• `{user['user_id']}` @{user.get('username', 'N/A')}\n"
            f"  Reason: {user.get('ban_reason', 'N/A')}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


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
        "🔒 **Security Dashboard**\n",
        f"🚫 Banned Users: {len(banned)}\n",
        "📋 **Recent Events:**\n"
    ]

    if logs:
        for log in logs[:10]:
            lines.append(
                f"• {log['action']} - User {log.get('user_id', 'N/A')}\n"
                f"  {log.get('details', '')[:50]}\n"
            )
    else:
        lines.append("_No recent events_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def userstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /userstats command - view user statistics."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/userstats <user_id>`", parse_mode="Markdown")
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

    text = (
        f"👤 **User Statistics**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Username: @{user.get('username', 'N/A')}\n"
        f"📛 Name: {user.get('first_name', '')} {user.get('last_name', '')}\n"
        f"📅 Joined: {user.get('join_date', 'N/A')}\n"
        f"🚫 Banned: {'Yes' if is_banned else 'No'}\n"
    )

    if is_banned:
        text += f"📝 Ban Reason: {ban_reason}\n"

    text += (
        f"\n📊 **Transaction Stats:**\n"
        f"✅ Total Paid: {paid_count}\n"
        f"💰 Total Spent: Rp {total_spent:,}\n"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


# Handler exports
security_handlers = [
    CommandHandler("ban", ban_command),
    CommandHandler("unban", unban_command),
    CommandHandler("banlist", banlist_command),
    CommandHandler("security", security_command),
    CommandHandler("userstats", userstats_command),
]
