"""
Stock alert job for FRIENDS Store Telegram Bot.
"""

from telegram.ext import ContextTypes

from database.db import Database
from services.stock_manager import StockManager
from services.notification import NotificationService
from utils.logger import get_logger

logger = get_logger("scheduler")


async def check_stock_levels(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Check stock levels and send alerts.
    Runs every 30 minutes.
    """
    db: Database = context.bot_data.get("db")
    if not db:
        logger.error("Database not available in job context")
        return

    try:
        stock_manager = StockManager(db)
        notification = NotificationService(context.bot, db)

        # Check stock levels
        alerts = await stock_manager.check_stock_levels()

        if not alerts:
            return

        # Send alerts for critical items
        for alert in alerts:
            if alert["level"] in ("CRITICAL", "OUT_OF_STOCK"):
                message = stock_manager.format_stock_alert(alert)
                await notification.send_stock_alert(message)

                logger.info(f"Stock alert sent: {alert['product_code']} ({alert['level']})")

        # Auto-disable empty products
        disabled = await stock_manager.auto_disable_empty_products()
        if disabled:
            await notification.notify_admins(
                f"⚠️ **Products Auto-Disabled (No Stock):**\n\n"
                f"• " + "\n• ".join(disabled)
            )

    except Exception as e:
        logger.error(f"Error in stock alert job: {e}")
