"""
Daily broadcast job for FRIENDS Store Telegram Bot.
"""

from datetime import datetime

from telegram.ext import ContextTypes

from database.db import Database
from services.notification import NotificationService
from utils.formatters import format_daily_broadcast
from utils.logger import get_logger

logger = get_logger("scheduler")


async def send_daily_broadcast(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send daily statistics broadcast to all users.
    Runs at 10:00 WIB.
    """
    db: Database = context.bot_data.get("db")
    if not db:
        logger.error("Database not available in job context")
        return

    try:
        logger.info("Starting daily broadcast...")

        # Get today's statistics
        stats = await db.get_stats()
        stock_summary = await db.get_stock_summary()

        # Calculate today's successful transactions
        transactions = stats.get("transactions", {})
        paid_count = transactions.get("PAID", 0)
        total_amount = stats.get("revenue_today", 0)

        # Format broadcast message
        message = format_daily_broadcast(
            date=datetime.now(),
            paid_count=paid_count,
            total_amount=total_amount,
            stock_list=stock_summary
        )

        # Send to all active users
        notification = NotificationService(context.bot, db)
        sent, failed = await notification.broadcast_message(
            message=message,
            target="all"
        )

        # Save broadcast record
        await db.create_broadcast(
            message_text=message,
            created_by=0,  # System broadcast
            target_audience="all"
        )
        await db.update_broadcast_stats(
            broadcast_id=1,  # Latest
            total_sent=sent,
            total_failed=failed
        )

        logger.info(f"Daily broadcast complete: sent={sent}, failed={failed}")

    except Exception as e:
        logger.error(f"Error in daily broadcast job: {e}")
