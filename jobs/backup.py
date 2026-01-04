"""
Database backup job for FRIENDS Store Telegram Bot.
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from telegram.ext import ContextTypes

from config import config
from utils.logger import get_logger

logger = get_logger("scheduler")


async def run_daily_backup(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Create daily database backup.
    Runs at 03:00 WIB.
    """
    try:
        logger.info("Starting daily backup...")

        db_path = config.database.path
        backup_dir = "./backups"

        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/backup_{timestamp}.db"

        # Create backup
        shutil.copy2(db_path, backup_path)

        # Verify backup
        if os.path.exists(backup_path):
            backup_size = os.path.getsize(backup_path)
            logger.info(f"Backup created: {backup_path} ({backup_size} bytes)")

            # Send to backup channel or super admin
            if config.backup.channel_id:
                try:
                    with open(backup_path, "rb") as f:
                        await context.bot.send_document(
                            chat_id=config.backup.channel_id,
                            document=f,
                            filename=f"backup_{timestamp}.db",
                            caption=f"📦 Auto Backup - {timestamp}"
                        )
                except Exception as e:
                    logger.error(f"Failed to send backup to channel: {e}")

            # Also send to super admin
            try:
                with open(backup_path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=config.bot.super_admin_id,
                        document=f,
                        filename=f"backup_{timestamp}.db",
                        caption=f"📦 Auto Backup - {timestamp}"
                    )
            except Exception as e:
                logger.error(f"Failed to send backup to super admin: {e}")

        # Cleanup old backups
        await cleanup_old_backups(backup_dir)

        logger.info("Daily backup complete")

    except Exception as e:
        logger.error(f"Error in backup job: {e}")


async def cleanup_old_backups(backup_dir: str) -> None:
    """Remove backups older than retention period."""
    retention_days = config.backup.retention_days
    cutoff = datetime.now() - timedelta(days=retention_days)

    try:
        for filename in os.listdir(backup_dir):
            if not filename.startswith("backup_") or not filename.endswith(".db"):
                continue

            filepath = os.path.join(backup_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_time < cutoff:
                os.remove(filepath)
                logger.info(f"Deleted old backup: {filename}")

    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
