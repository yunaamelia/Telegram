"""
Midtrans API client for FRIENDS Store Telegram Bot.
"""

import base64
import aiohttp
from typing import Dict, Any, Optional
from dataclasses import dataclass

from config import config
from utils.logger import get_logger
from utils.security import generate_transaction_id

logger = get_logger("payment")


@dataclass
class QRISTransaction:
    """QRIS transaction result."""
    transaction_id: str
    order_id: str
    gross_amount: int
    qris_url: str
    checkout_url: Optional[str] = None
    expiry_time: Optional[str] = None
    status: str = "pending"


class MidtransClient:
    """Async Midtrans API client for QRIS payments."""

    def __init__(self):
        self.server_key = config.midtrans.server_key
        self.client_key = config.midtrans.client_key
        self.is_production = config.midtrans.is_production
        self.base_url = config.midtrans.base_url

        # Create auth header
        auth_string = f"{self.server_key}:"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        self.auth_header = f"Basic {auth_bytes}"

    async def create_qris_transaction(
        self,
        amount: int,
        customer_name: str,
        customer_email: Optional[str] = None,
        user_id: int = 0,
        product_name: str = ""
    ) -> Optional[QRISTransaction]:
        """
        Create a QRIS payment transaction.

        Args:
            amount: Transaction amount in IDR
            customer_name: Customer's name
            customer_email: Customer's email (optional)
            user_id: Telegram user ID
            product_name: Product being purchased

        Returns:
            QRISTransaction object or None if failed
        """
        order_id = generate_transaction_id()

        # Build request payload
        payload = {
            "payment_type": "qris",
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": amount
            },
            "customer_details": {
                "first_name": customer_name,
                "email": customer_email or f"user{user_id}@friendsstore.bot"
            },
            "qris": {
                "acquirer": "gopay"  # Can be gopay, airpay, etc.
            },
            "custom_expiry": {
                "expiry_duration": config.transaction.expiry_minutes,
                "unit": "minute"
            },
            "item_details": [
                {
                    "id": order_id,
                    "name": product_name[:50] if product_name else "Product",
                    "price": amount,
                    "quantity": 1
                }
            ]
        }

        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v2/charge",
                    json=payload,
                    headers=headers
                ) as response:
                    data = await response.json()

                    logger.debug(f"Midtrans response: {data}")

                    status_code = data.get("status_code", "")

                    if status_code in ["200", "201"]:
                        # Find QRIS URL in actions
                        qris_url = None
                        for action in data.get("actions", []):
                            if action.get("name") == "generate-qr-code":
                                qris_url = action.get("url")
                                break

                        if not qris_url:
                            # Alternative: check if qr_string exists
                            qr_string = data.get("qr_string")
                            if qr_string:
                                # QRIS string can be converted to QR code
                                qris_url = qr_string

                        return QRISTransaction(
                            transaction_id=data.get("transaction_id", ""),
                            order_id=order_id,
                            gross_amount=amount,
                            qris_url=qris_url or "",
                            expiry_time=data.get("expiry_time"),
                            status=data.get("transaction_status", "pending")
                        )
                    else:
                        logger.error(
                            f"Midtrans error: {data.get('status_message')} "
                            f"(code: {status_code})"
                        )
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"Midtrans API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating transaction: {e}")
            return None

    async def check_transaction_status(self, order_id: str) -> Dict[str, Any]:
        """
        Check transaction status from Midtrans.

        Args:
            order_id: The order ID to check

        Returns:
            Transaction status data
        """
        headers = {
            "Authorization": self.auth_header,
            "Accept": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v2/{order_id}/status",
                    headers=headers
                ) as response:
                    data = await response.json()

                    return {
                        "status_code": data.get("status_code"),
                        "transaction_status": data.get("transaction_status"),
                        "fraud_status": data.get("fraud_status"),
                        "payment_type": data.get("payment_type"),
                        "transaction_time": data.get("transaction_time"),
                        "settlement_time": data.get("settlement_time"),
                        "gross_amount": data.get("gross_amount"),
                        "order_id": data.get("order_id"),
                        "transaction_id": data.get("transaction_id")
                    }

        except aiohttp.ClientError as e:
            logger.error(f"Failed to check transaction status: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error checking status: {e}")
            return {"error": str(e)}

    async def cancel_transaction(self, order_id: str) -> bool:
        """
        Cancel a pending transaction.

        Args:
            order_id: The order ID to cancel

        Returns:
            True if cancelled successfully
        """
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v2/{order_id}/cancel",
                    headers=headers
                ) as response:
                    data = await response.json()

                    if data.get("status_code") in ["200", "201"]:
                        logger.info(f"Transaction {order_id} cancelled")
                        return True
                    else:
                        logger.error(
                            f"Failed to cancel transaction: {data.get('status_message')}"
                        )
                        return False

        except Exception as e:
            logger.error(f"Error cancelling transaction: {e}")
            return False

    def is_payment_success(self, status: str, fraud_status: str = "accept") -> bool:
        """Check if transaction status indicates successful payment."""
        return status in ["capture", "settlement"] and fraud_status == "accept"

    def is_payment_pending(self, status: str) -> bool:
        """Check if transaction is still pending."""
        return status == "pending"

    def is_payment_failed(self, status: str) -> bool:
        """Check if transaction has failed."""
        return status in ["deny", "cancel", "expire", "failure"]
