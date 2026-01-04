"""
Midtrans webhook callback processor for FRIENDS Store Telegram Bot.
"""

from typing import Dict, Any

from telegram import Bot

from database.db import Database
from services.payment import PaymentService
from services.notification import NotificationService
from utils.formatters import format_payment_success
from utils.keyboards import Keyboards
from utils.logger import get_logger

logger = get_logger("webhook")


async def process_midtrans_callback(
    data: Dict[str, Any],
    bot: Bot,
    db: Database
) -> None:
    """
    Process Midtrans webhook callback.

    Args:
        data: Callback data from Midtrans
        bot: Telegram bot instance
        db: Database instance
    """
    order_id = data.get("order_id", "")
    transaction_status = data.get("transaction_status", "")
    fraud_status = data.get("fraud_status", "accept")

    logger.info(
        f"Processing callback: order={order_id}, "
        f"status={transaction_status}, fraud={fraud_status}"
    )

    payment_service = PaymentService(db)
    notification = NotificationService(bot, db)

    success, message, result = await payment_service.process_callback(
        order_id=order_id,
        transaction_status=transaction_status,
        fraud_status=fraud_status
    )

    if not success:
        logger.warning(f"Callback processing failed: {message}")
        return

    # Handle successful payment
    if transaction_status in ["capture", "settlement"] and result:
        tx = result.get("transaction", {})
        stock_item = result.get("stock_item", {})
        product = result.get("product", {})
        paid_at = result.get("paid_at")

        if tx and stock_item:
            # Send success message to user
            success_message = format_payment_success(
                transaction_id=tx.get("merchant_ref", ""),
                product_name=product.get("name", ""),
                amount=tx.get("amount", 0),
                paid_at=paid_at,
                stock_item=stock_item
            )

            await notification.notify_user(
                user_id=tx.get("user_id"),
                message=success_message,
                reply_markup=Keyboards.navigation(back_target="main")
            )

            # Notify admins
            await notification.notify_admins(
                f"💰 **Payment Received!**\n\n"
                f"Order: `{tx.get('merchant_ref')}`\n"
                f"User: {tx.get('user_id')}\n"
                f"Product: {product.get('name')}\n"
                f"Amount: Rp {tx.get('amount', 0):,}",
            )

            logger.info(f"Payment success notification sent: {order_id}")

    # Handle expired/failed payment
    elif transaction_status in ["expire", "cancel", "deny"]:
        tx = await db.get_transaction_by_merchant_ref(order_id)

        if tx:
            from utils.formatters import format_payment_expired

            product = await db.get_product(tx.get("product_code", ""))

            expired_message = format_payment_expired(
                transaction_id=tx.get("merchant_ref", ""),
                product_name=product.get("name", "") if product else "",
                amount=tx.get("amount", 0)
            )

            await notification.notify_user(
                user_id=tx.get("user_id"),
                message=expired_message,
                reply_markup=Keyboards.navigation(back_target="main")
            )

            logger.info(f"Payment expired notification sent: {order_id}")
