"""
Rate limiting utilities for FRIENDS Store Telegram Bot.
"""

from datetime import datetime
from typing import Dict, Tuple

from config import config


class RateLimiter:
    """In-memory rate limiter for quick checks (backed by database for persistence)."""

    def __init__(self):
        # In-memory cache: user_id -> (request_count, window_start, last_command)
        self._cache: Dict[int, Tuple[int, datetime, datetime]] = {}

    def check_rate_limit(self, user_id: int) -> Tuple[bool, int]:
        """
        Check if user has exceeded rate limit.

        Returns:
            Tuple of (is_limited, seconds_until_reset)
        """
        now = datetime.now()
        max_requests = config.rate_limit.requests
        window = config.rate_limit.window

        if user_id not in self._cache:
            self._cache[user_id] = (1, now, now)
            return False, 0

        count, window_start, _ = self._cache[user_id]
        elapsed = (now - window_start).total_seconds()

        if elapsed > window:
            # Reset window
            self._cache[user_id] = (1, now, now)
            return False, 0

        if count >= max_requests:
            seconds_until_reset = int(window - elapsed)
            return True, seconds_until_reset

        # Increment counter
        self._cache[user_id] = (count + 1, window_start, now)
        return False, 0

    def check_cooldown(self, user_id: int) -> Tuple[bool, int]:
        """
        Check if user is in command cooldown.

        Returns:
            Tuple of (is_in_cooldown, seconds_remaining)
        """
        now = datetime.now()
        cooldown = config.rate_limit.cooldown

        if user_id not in self._cache:
            return False, 0

        _, _, last_command = self._cache[user_id]
        elapsed = (now - last_command).total_seconds()

        if elapsed < cooldown:
            return True, int(cooldown - elapsed)

        return False, 0

    def update_last_command(self, user_id: int) -> None:
        """Update last command time for user."""
        now = datetime.now()

        if user_id in self._cache:
            count, window_start, _ = self._cache[user_id]
            self._cache[user_id] = (count, window_start, now)
        else:
            self._cache[user_id] = (1, now, now)

    def clear_user(self, user_id: int) -> None:
        """Clear rate limit cache for a user."""
        self._cache.pop(user_id, None)


class PurchaseLimiter:
    """Purchase-specific limits."""

    def __init__(self):
        # user_id -> {product_code: [(date, count)]}
        self._daily_purchases: Dict[int, Dict[str, int]] = {}
        # user_id -> pending_count
        self._pending_transactions: Dict[int, int] = {}
        self._last_reset_date: str = datetime.now().strftime("%Y-%m-%d")

    def _check_date_reset(self) -> None:
        """Reset counters if date has changed."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._last_reset_date:
            self._daily_purchases.clear()
            self._last_reset_date = today

    def can_purchase(self, user_id: int, product_code: str) -> Tuple[bool, str]:
        """
        Check if user can make a purchase.

        Returns:
            Tuple of (can_purchase, error_message)
        """
        self._check_date_reset()

        # Check pending transactions limit
        max_pending = config.transaction.max_pending
        pending = self._pending_transactions.get(user_id, 0)

        if pending >= max_pending:
            return False, f"Kamu memiliki {pending} transaksi pending. Selesaikan atau batalkan dulu."

        # Check daily purchase limit per product
        max_daily = config.transaction.max_daily_per_product
        user_purchases = self._daily_purchases.get(user_id, {})
        product_purchases = user_purchases.get(product_code, 0)

        if product_purchases >= max_daily:
            return False, f"Kamu sudah mencapai batas {max_daily} pembelian per hari untuk produk ini."

        return True, ""

    def record_purchase_start(self, user_id: int, product_code: str) -> None:
        """Record a new pending purchase."""
        self._check_date_reset()

        # Increment pending
        self._pending_transactions[user_id] = self._pending_transactions.get(user_id, 0) + 1

        # Increment daily count
        if user_id not in self._daily_purchases:
            self._daily_purchases[user_id] = {}
        self._daily_purchases[user_id][product_code] = (
            self._daily_purchases[user_id].get(product_code, 0) + 1
        )

    def record_purchase_complete(self, user_id: int) -> None:
        """Record purchase completion (paid or expired)."""
        pending = self._pending_transactions.get(user_id, 0)
        if pending > 0:
            self._pending_transactions[user_id] = pending - 1

    def get_pending_count(self, user_id: int) -> int:
        """Get pending transaction count for user."""
        return self._pending_transactions.get(user_id, 0)

    def sync_pending_from_db(self, user_id: int, count: int) -> None:
        """Sync pending count from database."""
        self._pending_transactions[user_id] = count


# Global instances
rate_limiter = RateLimiter()
purchase_limiter = PurchaseLimiter()
