"""
System management handlers for FRIENDS Store Telegram Bot.
"""

import os
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import config
from database.db import Database
from utils.formatters import format_stats
from utils.logger import get_logger

logger = get_logger("admin")


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is an admin."""
    user = update.effective_user
    db: Database = context.bot_data["db"]
    return await db.is_admin(user.id)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command - show bot statistics."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    db: Database = context.bot_data["db"]

    stats = await db.get_stats()

    # Add uptime
    if "start_time" in context.bot_data:
        uptime = datetime.now() - context.bot_data["start_time"]
        stats["uptime_hours"] = int(uptime.total_seconds() / 3600)
    else:
        stats["uptime_hours"] = 0

    text = format_stats(stats)

    await update.message.reply_text(text, parse_mode="Markdown")


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /logs command - view recent logs."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    args = context.args
    lines = int(args[0]) if args else 30

    log_file = "./logs/bot.log"

    if not os.path.exists(log_file):
        await update.message.reply_text("📝 No logs available.")
        return

    try:
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:]

        log_text = "".join(recent)

        if len(log_text) > 4000:
            log_text = log_text[-4000:]

        await update.message.reply_text(
            f"📝 **Recent Logs** (last {len(recent)} lines)\n\n"
            f"```\n{log_text}\n```",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error reading logs: {e}")


async def backupdb_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /backupdb command - manual database backup."""
    if not await check_admin(update, context):
        await update.message.reply_text("⛔ Akses ditolak. Admin only.")
        return

    import shutil
    from pathlib import Path

    db_path = config.database.path
    backup_dir = "./backups"

    Path(backup_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/backup_{timestamp}.db"

    try:
        shutil.copy2(db_path, backup_path)

        # Send to admin
        with open(backup_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"backup_{timestamp}.db",
                caption=f"📦 Database backup created: {timestamp}"
            )

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        await update.message.reply_text(f"❌ Backup failed: {e}")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset command - reset database (DEBUG only)."""
    if not config.DEBUG:
        await update.message.reply_text("⛔ Command disabled in production.")
        return

    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_super_admin(user.id):
        await update.message.reply_text("⛔ Super admin only.")
        return

    # Require double confirmation
    if context.user_data.get("reset_confirm") != "RESET":
        context.user_data["reset_confirm"] = "pending"
        await update.message.reply_text(
            "⚠️ **WARNING: This will delete ALL data!**\n\n"
            "Type `/reset CONFIRM` to proceed.",
            parse_mode="Markdown"
        )
        return

    # Actually reset
    import os
    db_path = config.database.path

    await db.close()

    if os.path.exists(db_path):
        os.remove(db_path)

    await db.init()

    # Re-seed
    from database.seed import seed_database
    await seed_database(db)

    context.user_data.clear()
    await update.message.reply_text("🔄 Database reset complete!")


async def reset_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reset confirmation."""
    if update.message.text == "/reset CONFIRM":
        context.user_data["reset_confirm"] = "RESET"
        await reset_command(update, context)


async def testpayment_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /testpayment command - simulate payment success (DEBUG only)."""
    if not config.DEBUG:
        await update.message.reply_text("⛔ Command disabled in production.")
        return

    user = update.effective_user
    db: Database = context.bot_data["db"]

    if not await db.is_admin(user.id):
        await update.message.reply_text("⛔ Admin only.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: `/testpayment <transaction_id>`", parse_mode="Markdown")
        return

    transaction_id = args[0]

    from services.payment import PaymentService
    payment_service = PaymentService(db)

    success, message, result = await payment_service.process_callback(
        order_id=transaction_id,
        transaction_status="settlement",
        fraud_status="accept"
    )

    if success and result:
        await update.message.reply_text(
            f"✅ Payment simulated for `{transaction_id}`\n"
            f"Status: PAID",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"❌ {message}")


# Handler exports
system_handlers = [
    CommandHandler("stats", stats_command),
    CommandHandler("logs", logs_command),
    CommandHandler("backupdb", backupdb_command),
    CommandHandler("reset", reset_command),
    CommandHandler("testpayment", testpayment_command),
]
