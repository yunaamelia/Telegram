"""
Payment orchestration service for FRIENDS Store Telegram Bot.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from config import config
from database.db import Database
from services.midtrans import MidtransClient, QRISTransaction
from services.stock_manager import StockManager
from utils.logger import get_logger

logger = get_logger("payment")


class PaymentService:
    """Orchestrates payment flow between Midtrans, database, and stock."""

    def __init__(self, db: Database):
        self.db = db
        self.midtrans = MidtransClient()
        self.stock_manager = StockManager(db)

    async def create_payment(
        self,
        user_id: int,
        product_code: str,
        customer_name: str
    ) -> Tuple[bool, str, Optional[QRISTransaction]]:
        """
        Create a new payment for a product.

        Returns:
            Tuple of (success, message, transaction)
        """
        # Get product
        product = await self.db.get_product(product_code)
        if not product:
            return False, "Produk tidak ditemukan", None

        if not product["is_active"]:
            return False, "Produk tidak tersedia", None

        # Check stock
        stock_count = await self.db.get_available_stock_count(product_code)
        if stock_count == 0:
            return False, "Stok habis", None

        # Reserve stock
        stock_item = await self.db.reserve_stock_item(product_code)
        if not stock_item:
            return False, "Gagal reserve stok", None

        # Create Midtrans transaction
        qris_tx = await self.midtrans.create_qris_transaction(
            amount=product["price"],
            customer_name=customer_name,
            user_id=user_id,
            product_name=product["name"]
        )

        if not qris_tx:
            # Release stock on payment creation failure
            await self.db.release_stock_item(stock_item["id"])
            return False, "Gagal membuat transaksi pembayaran", None

        # Calculate expiry time
        expired_at = datetime.now() + timedelta(minutes=config.transaction.expiry_minutes)

        # Save transaction to database
        await self.db.create_transaction(
            transaction_id=qris_tx.transaction_id,
            merchant_ref=qris_tx.order_id,
            user_id=user_id,
            product_code=product_code,
            amount=product["price"],
            checkout_url=None,  # QRIS doesn't have checkout URL
            qris_url=qris_tx.qris_url,
            expired_at=expired_at,
            stock_id=stock_item["id"]
        )

        logger.info(
            f"Payment created: user={user_id}, product={product_code}, "
            f"order={qris_tx.order_id}, amount={product['price']}"
        )

        return True, "Transaksi berhasil dibuat", qris_tx

    async def process_callback(
        self,
        order_id: str,
        transaction_status: str,
        fraud_status: str = "accept"
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process Midtrans callback notification.

        Returns:
            Tuple of (success, message, transaction_data)
        """
        # Get transaction from database
        tx = await self.db.get_transaction_by_merchant_ref(order_id)
        if not tx:
            logger.warning(f"Transaction not found for callback: {order_id}")
            return False, "Transaksi tidak ditemukan", None

        # Skip if already processed
        if tx["status"] != "UNPAID":
            logger.info(f"Transaction {order_id} already processed: {tx['status']}")
            return True, f"Already {tx['status']}", tx

        if self.midtrans.is_payment_success(transaction_status, fraud_status):
            # Payment successful
            return await self._handle_payment_success(tx)

        elif self.midtrans.is_payment_failed(transaction_status):
            # Payment failed/expired/cancelled
            return await self._handle_payment_failed(tx, transaction_status)

        else:
            # Still pending
            return True, "Menunggu pembayaran", tx

    async def _handle_payment_success(
        self,
        tx: Dict
    ) -> Tuple[bool, str, Dict]:
        """Handle successful payment."""
        now = datetime.now()

        # Update transaction status
        await self.db.update_transaction_status(
            transaction_id=tx["transaction_id"],
            status="PAID",
            paid_at=now
        )

        # Mark stock as sold
        if tx.get("stock_id"):
            await self.db.mark_stock_sold(tx["stock_id"], tx["user_id"])

        # Get stock details for delivery
        stock_item = None
        if tx.get("stock_id"):
            stock_item = await self.db.get_stock_item(tx["stock_id"])

        # Get product details
        product = await self.db.get_product(tx["product_code"])

        logger.info(
            f"Payment successful: order={tx['merchant_ref']}, "
            f"user={tx['user_id']}, product={tx['product_code']}"
        )

        return True, "Pembayaran berhasil", {
            "transaction": tx,
            "stock_item": stock_item,
            "product": product,
            "paid_at": now
        }

    async def _handle_payment_failed(
        self,
        tx: Dict,
        status: str
    ) -> Tuple[bool, str, Dict]:
        """Handle failed/expired payment."""
        new_status = "EXPIRED" if status == "expire" else "CANCELLED"

        # Update transaction status
        await self.db.update_transaction_status(
            transaction_id=tx["transaction_id"],
            status=new_status
        )

        # Release reserved stock
        if tx.get("stock_id"):
            await self.db.release_stock_item(tx["stock_id"])

        logger.info(
            f"Payment {status}: order={tx['merchant_ref']}, user={tx['user_id']}"
        )

        return True, f"Transaksi {new_status.lower()}", tx

    async def cancel_payment(
        self,
        transaction_id: str,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        Cancel a pending payment.

        Returns:
            Tuple of (success, message)
        """
        tx = await self.db.get_transaction(transaction_id)

        if not tx:
            return False, "Transaksi tidak ditemukan"

        if tx["user_id"] != user_id:
            return False, "Bukan transaksi milikmu"

        if tx["status"] != "UNPAID":
            return False, f"Transaksi tidak bisa dibatalkan (status: {tx['status']})"

        # Cancel on Midtrans
        cancelled = await self.midtrans.cancel_transaction(tx["merchant_ref"])

        # Update database regardless (might be already expired)
        await self.db.update_transaction_status(
            transaction_id=transaction_id,
            status="CANCELLED"
        )

        # Release stock
        if tx.get("stock_id"):
            await self.db.release_stock_item(tx["stock_id"])

        return True, "Transaksi dibatalkan"

    async def check_payment_status(
        self,
        transaction_id: str
    ) -> Tuple[str, Optional[Dict]]:
        """
        Check and update payment status.

        Returns:
            Tuple of (status, transaction_data)
        """
        tx = await self.db.get_transaction(transaction_id)

        if not tx:
            return "NOT_FOUND", None

        if tx["status"] != "UNPAID":
            return tx["status"], tx

        # Check with Midtrans
        status_data = await self.midtrans.check_transaction_status(tx["merchant_ref"])

        if "error" in status_data:
            return tx["status"], tx

        transaction_status = status_data.get("transaction_status", "")

        if self.midtrans.is_payment_success(
            transaction_status,
            status_data.get("fraud_status", "accept")
        ):
            # Process as callback
            success, msg, result = await self.process_callback(
                tx["merchant_ref"],
                transaction_status,
                status_data.get("fraud_status", "accept")
            )
            return "PAID" if success else tx["status"], result

        elif self.midtrans.is_payment_failed(transaction_status):
            await self.process_callback(
                tx["merchant_ref"],
                transaction_status
            )
            return "EXPIRED" if transaction_status == "expire" else "CANCELLED", tx

        return "UNPAID", tx

    async def request_refund(
        self,
        transaction_id: str,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        Request a refund for a paid transaction.

        Returns:
            Tuple of (success, message)
        """
        tx = await self.db.get_transaction(transaction_id)

        if not tx:
            return False, "Transaksi tidak ditemukan"

        if tx["user_id"] != user_id:
            return False, "Bukan transaksi milikmu"

        if tx["status"] != "PAID":
            return False, "Hanya transaksi yang sudah dibayar yang bisa di-refund"

        # Check time window (24 hours)
        if tx.get("paid_at"):
            paid_at = datetime.fromisoformat(tx["paid_at"])
            if datetime.now() - paid_at > timedelta(hours=24):
                return False, "Waktu refund sudah lewat (maksimal 24 jam)"

        await self.db.update_transaction_status(
            transaction_id=transaction_id,
            status="REFUND_REQUESTED"
        )

        return True, "Permintaan refund dikirim. Admin akan memproses dalam 1-24 jam."
