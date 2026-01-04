"""
Transaction expiry checker job for FRIENDS Store Telegram Bot.
"""

from telegram.ext import ContextTypes

from database.db import Database
from services.notification import NotificationService
from utils.formatters import format_payment_expired
from utils.keyboards import Keyboards
from utils.rate_limiter import purchase_limiter
from utils.logger import get_logger

logger = get_logger("scheduler")


async def check_expired_transactions(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Check for expired transactions and process them.
    Runs every minute.
    """
    db: Database = context.bot_data.get("db")
    if not db:
        logger.error("Database not available in job context")
        return

    try:
        expired = await db.get_expired_transactions()

        if not expired:
            return

        logger.info(f"Found {len(expired)} expired transactions")

        notification = NotificationService(context.bot, db)

        for tx in expired:
            try:
                # Update status
                await db.update_transaction_status(
                    transaction_id=tx["transaction_id"],
                    status="EXPIRED"
                )

                # Release reserved stock
                if tx.get("stock_id"):
                    await db.release_stock_item(tx["stock_id"])

                # Update purchase limiter
                purchase_limiter.record_purchase_complete(tx["user_id"])

                # Get product for message
                product = await db.get_product(tx["product_code"])

                # Notify user
                message = format_payment_expired(
                    transaction_id=tx["merchant_ref"],
                    product_name=product.get("name", "") if product else "",
                    amount=tx["amount"]
                )

                await notification.notify_user(
                    user_id=tx["user_id"],
                    message=message,
                    reply_markup=Keyboards.navigation(back_target="main")
                )

                logger.info(f"Expired transaction processed: {tx['merchant_ref']}")

            except Exception as e:
                logger.error(f"Error processing expired transaction {tx['merchant_ref']}: {e}")

    except Exception as e:
        logger.error(f"Error in expiry checker job: {e}")
