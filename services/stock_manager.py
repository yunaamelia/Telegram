"""
Stock management service for FRIENDS Store Telegram Bot.
"""

from typing import Dict, List, Optional, Tuple

from config import config
from database.db import Database
from utils.logger import get_logger

logger = get_logger("stock")


class StockManager:
    """Manages stock operations with alerts and thresholds."""

    def __init__(self, db: Database):
        self.db = db
        self.warning_threshold = config.stock.warning_threshold
        self.critical_threshold = config.stock.critical_threshold

    async def check_stock_levels(self) -> List[Dict]:
        """
        Check stock levels and return items needing attention.

        Returns:
            List of products with low/critical/out of stock status
        """
        alerts = []
        stock_summary = await self.db.get_stock_summary()

        for item in stock_summary:
            if not item["is_active"]:
                continue

            available = item["available"]
            total = item["total"]

            if total == 0:
                continue

            percent = available / total

            if available == 0:
                alerts.append({
                    "product_code": item["product_code"],
                    "name": item["name"],
                    "level": "OUT_OF_STOCK",
                    "count": 0,
                    "percent": 0
                })
            elif percent <= self.critical_threshold:
                alerts.append({
                    "product_code": item["product_code"],
                    "name": item["name"],
                    "level": "CRITICAL",
                    "count": available,
                    "percent": percent
                })
            elif percent <= self.warning_threshold:
                alerts.append({
                    "product_code": item["product_code"],
                    "name": item["name"],
                    "level": "WARNING",
                    "count": available,
                    "percent": percent
                })

        return alerts

    async def add_stock_bulk(
        self,
        product_code: str,
        entries: List[str],
        added_by: int
    ) -> Tuple[int, int, List[str]]:
        """
        Add multiple stock items from text entries.

        Args:
            product_code: Product code to add stock to
            entries: List of "email:password:2fa:notes" strings
            added_by: Admin user ID

        Returns:
            Tuple of (success_count, error_count, error_messages)
        """
        from utils.validators import validate_stock_entry

        success = 0
        errors = 0
        error_messages = []

        for i, entry in enumerate(entries, 1):
            entry = entry.strip()
            if not entry:
                continue

            is_valid, msg, data = validate_stock_entry(entry)

            if not is_valid:
                errors += 1
                error_messages.append(f"Line {i}: {msg}")
                continue

            try:
                await self.db.add_stock_item(
                    product_code=product_code,
                    email=data["email"],
                    password=data["password"],
                    two_fa_secret=data.get("two_fa_secret"),
                    notes=data.get("notes"),
                    added_by=added_by
                )
                success += 1
            except Exception as e:
                errors += 1
                error_messages.append(f"Line {i}: {str(e)}")
                logger.error(f"Failed to add stock item: {e}")

        logger.info(
            f"Bulk stock add: product={product_code}, success={success}, errors={errors}"
        )

        return success, errors, error_messages

    async def get_stock_for_product(self, product_code: str) -> Dict:
        """
        Get stock info for a specific product.

        Returns:
            Dict with available, sold, reserved, total counts
        """
        summary = await self.db.get_stock_summary()

        for item in summary:
            if item["product_code"] == product_code:
                return item

        return {
            "product_code": product_code,
            "available": 0,
            "sold": 0,
            "reserved": 0,
            "total": 0
        }

    async def auto_disable_empty_products(self) -> List[str]:
        """
        Automatically disable products with no stock.

        Returns:
            List of product codes that were disabled
        """
        disabled = []
        alerts = await self.check_stock_levels()

        for alert in alerts:
            if alert["level"] == "OUT_OF_STOCK":
                product = await self.db.get_product(alert["product_code"])
                if product and product["is_active"]:
                    await self.db.update_product(
                        product_code=alert["product_code"],
                        is_active=False
                    )
                    disabled.append(alert["product_code"])
                    logger.info(f"Auto-disabled empty product: {alert['product_code']}")

        return disabled

    def format_stock_alert(self, alert: Dict) -> str:
        """Format a stock alert as a message."""
        level = alert["level"]
        name = alert["name"]
        count = alert["count"]
        percent = int(alert["percent"] * 100)

        if level == "OUT_OF_STOCK":
            return f"❌ **Stok {name} HABIS!**\nProduk otomatis dinonaktifkan."
        elif level == "CRITICAL":
            return f"🚨 **URGENT:** Stok {name} hampir habis!\nTersisa: {count} ({percent}%)"
        else:  # WARNING
            return f"⚠️ Stok {name} tinggal {count} ({percent}%)"
