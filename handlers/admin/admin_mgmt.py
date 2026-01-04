"""
Admin management handlers for FRIENDS Store Telegram Bot.
Super admin only commands.
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import config
from database.db import Database
from utils.formatters import escape_md
from utils.logger import get_logger

logger = get_logger("admin")


async def check_super_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is a super admin."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    return await db.is_super_admin(user.id)


async def addadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /addadmin command. Super admin only."""
    if not await check_super_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Super admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "👤 *Add Admin*\n\n"
            "Usage: `/addadmin <user_id>`\n\n"
            "User harus sudah memulai bot untuk bisa dijadikan admin.",
            parse_mode="MarkdownV2"
        )
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID harus berupa angka.")
        return

    db: Database = context.bot_data["db"]

    # Check if user exists
    user = await db.get_user(user_id)
    if not user:
        await update.message.reply_text(
            "❌ User tidak ditemukan.\n"
            "User harus memulai bot terlebih dahulu."
        )
        return

    # Check if already admin
    existing = await db.get_admin(user_id)
    if existing:
        await update.message.reply_text(
            f"ℹ️ User {user_id} sudah menjadi admin ({existing['role']})."
        )
        return

    # Add admin
    await db.add_admin(
        user_id=user_id,
        role="admin",
        added_by=update.effective_user.id
    )
    logger.info(f"Admin added: user_id={user_id}, by={update.effective_user.id}")

    await update.message.reply_text(
        f"✅ User `{user_id}` \(@{escape_md(user.get('username', 'N/A'))}\) "
        f"ditambahkan sebagai admin\.",
        parse_mode="MarkdownV2"
    )


async def removeadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /removeadmin command. Super admin only."""
    if not await check_super_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Super admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/removeadmin <user_id>`", parse_mode="MarkdownV2")
        return

    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID harus berupa angka.")
        return

    if user_id == config.bot.super_admin_id:
        await update.message.reply_text("❌ Tidak bisa menghapus super admin.")
        return

    db: Database = context.bot_data["db"]

    success = await db.remove_admin(user_id)
    if success:
        logger.info(f"Admin removed: user_id={user_id}, by={update.effective_user.id}")
        await update.message.reply_text(f"✅ Admin `{user_id}` dihapus\.", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ Gagal menghapus admin atau tidak ditemukan\.")


async def listadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /listadmin command."""
    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_admin(user.id):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    admins = await db.get_all_admins()

    if not admins:
        await update.message.reply_text("👤 Tidak ada admin terdaftar.")
        return

    lines = ["👥 *Daftar Admin*\n"]

    for admin in admins:
        role_emoji = "👑" if admin["role"] == "super_admin" else "👤"
        user_info = await db.get_user(admin["user_id"])
        username = user_info.get("username", "N/A") if user_info else "N/A"

        lines.append(
            f"{role_emoji} `{admin['user_id']}` @{escape_md(username)}\n"
            f"   Role: {escape_md(admin['role'])}\n"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")


# Handler exports
admin_mgmt_handlers = [
    CommandHandler("addadmin", addadmin_command),
    CommandHandler("removeadmin", removeadmin_command),
    CommandHandler("listadmin", listadmin_command),
]
