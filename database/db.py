"""
Async SQLite database operations for FRIENDS Store Telegram Bot.
"""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import get_logger

logger = get_logger("database")


class Database:
    """Async SQLite database wrapper with CRUD operations."""

    def __init__(self, db_path: str = "./data/bot.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Establish database connection."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA foreign_keys = ON")
        logger.info(f"Connected to database: {self.db_path}")

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    async def init(self) -> None:
        """Initialize database with schema."""
        await self.connect()
        await self._create_tables()
        logger.info("Database initialized successfully")

    async def _create_tables(self) -> None:
        """Create all database tables."""
        schema = """
        -- Users Table
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_banned BOOLEAN DEFAULT 0,
            ban_reason TEXT,
            last_activity TIMESTAMP
        );

        -- Admins Table (Role-based)
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            role TEXT CHECK(role IN ('super_admin', 'admin')),
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (added_by) REFERENCES admins(user_id)
        );

        -- Products Table
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Stock Table (with 2FA support)
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            two_fa_secret TEXT,
            notes TEXT,
            status TEXT CHECK(status IN ('available', 'sold', 'reserved')) DEFAULT 'available',
            sold_to_user_id INTEGER,
            sold_at TIMESTAMP,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_code) REFERENCES products(product_code),
            FOREIGN KEY (sold_to_user_id) REFERENCES users(user_id)
        );

        -- Transactions Table
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            merchant_ref TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            product_code TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT CHECK(status IN ('UNPAID', 'PAID', 'FAILED', 'EXPIRED', 'CANCELLED', 'REFUND_REQUESTED', 'REFUNDED')) DEFAULT 'UNPAID',
            payment_method TEXT DEFAULT 'QRIS',
            checkout_url TEXT,
            qris_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP,
            expired_at TIMESTAMP,
            stock_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (product_code) REFERENCES products(product_code),
            FOREIGN KEY (stock_id) REFERENCES stock(id)
        );

        -- Broadcast Messages Table
        CREATE TABLE IF NOT EXISTS broadcast_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_text TEXT NOT NULL,
            media_type TEXT CHECK(media_type IN ('text', 'photo', 'document')),
            media_file_id TEXT,
            target_audience TEXT CHECK(target_audience IN ('all', 'buyers', 'active_7days')) DEFAULT 'all',
            scheduled_at TIMESTAMP,
            sent_at TIMESTAMP,
            total_sent INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES admins(user_id)
        );

        -- Security Logs Table
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            ip_address TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        -- Rate Limiting Table
        CREATE TABLE IF NOT EXISTS rate_limits (
            user_id INTEGER PRIMARY KEY,
            request_count INTEGER DEFAULT 0,
            window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_command_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_stock_product_status ON stock(product_code, status);
        CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
        CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned);
        """
        await self._connection.executescript(schema)
        await self._connection.commit()

    # ==================== User Operations ====================

    async def upsert_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> None:
        """Insert or update a user."""
        await self._connection.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, last_activity)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = COALESCE(excluded.username, users.username),
                first_name = COALESCE(excluded.first_name, users.first_name),
                last_name = COALESCE(excluded.last_name, users.last_name),
                last_activity = CURRENT_TIMESTAMP
            """,
            (user_id, username, first_name, last_name)
        )
        await self._connection.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        async with self._connection.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def is_user_banned(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """Check if user is banned and return reason."""
        user = await self.get_user(user_id)
        if user and user["is_banned"]:
            return True, user.get("ban_reason")
        return False, None

    async def ban_user(self, user_id: int, reason: str) -> None:
        """Ban a user."""
        await self._connection.execute(
            "UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?",
            (reason, user_id)
        )
        await self._connection.commit()

    async def unban_user(self, user_id: int) -> None:
        """Unban a user."""
        await self._connection.execute(
            "UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?",
            (user_id,)
        )
        await self._connection.commit()

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        async with self._connection.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_users_by_filter(self, filter_type: str) -> List[Dict[str, Any]]:
        """Get users by filter: all, buyers, active_7days."""
        if filter_type == "buyers":
            query = """
                SELECT DISTINCT u.* FROM users u
                JOIN transactions t ON u.user_id = t.user_id
                WHERE t.status = 'PAID'
            """
        elif filter_type == "active_7days":
            query = """
                SELECT * FROM users
                WHERE last_activity >= datetime('now', '-7 days')
            """
        else:
            query = "SELECT * FROM users WHERE is_banned = 0"

        async with self._connection.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_banned_users(self) -> List[Dict[str, Any]]:
        """Get all banned users."""
        async with self._connection.execute(
            "SELECT * FROM users WHERE is_banned = 1"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== Admin Operations ====================

    async def add_admin(self, user_id: int, role: str, added_by: int) -> None:
        """Add a new admin."""
        await self._connection.execute(
            """
            INSERT INTO admins (user_id, role, added_by)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET role = excluded.role
            """,
            (user_id, role, added_by)
        )
        await self._connection.commit()

    async def remove_admin(self, user_id: int) -> bool:
        """Remove an admin. Returns False if user is super_admin."""
        async with self._connection.execute(
            "SELECT role FROM admins WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row["role"] == "super_admin":
                return False

        await self._connection.execute(
            "DELETE FROM admins WHERE user_id = ?", (user_id,)
        )
        await self._connection.commit()
        return True

    async def get_admin(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get admin by user ID."""
        async with self._connection.execute(
            "SELECT * FROM admins WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        admin = await self.get_admin(user_id)
        return admin is not None

    async def is_super_admin(self, user_id: int) -> bool:
        """Check if user is a super admin."""
        admin = await self.get_admin(user_id)
        return admin is not None and admin["role"] == "super_admin"

    async def get_all_admins(self) -> List[Dict[str, Any]]:
        """Get all admins."""
        async with self._connection.execute("SELECT * FROM admins") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== Product Operations ====================

    async def add_product(
        self,
        product_code: str,
        name: str,
        price: int,
        description: Optional[str] = None
    ) -> int:
        """Add a new product. Returns product ID."""
        cursor = await self._connection.execute(
            """
            INSERT INTO products (product_code, name, description, price)
            VALUES (?, ?, ?, ?)
            """,
            (product_code, name, description, price)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def update_product(
        self,
        product_code: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update a product."""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if price is not None:
            updates.append("price = ?")
            params.append(price)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(product_code)

        await self._connection.execute(
            f"UPDATE products SET {', '.join(updates)} WHERE product_code = ?",
            params
        )
        await self._connection.commit()
        return True

    async def delete_product(self, product_code: str) -> bool:
        """Delete a product (soft delete by deactivating)."""
        await self._connection.execute(
            "UPDATE products SET is_active = 0 WHERE product_code = ?",
            (product_code,)
        )
        await self._connection.commit()
        return True

    async def get_product(self, product_code: str) -> Optional[Dict[str, Any]]:
        """Get product by code."""
        async with self._connection.execute(
            "SELECT * FROM products WHERE product_code = ?", (product_code,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_active_products(self) -> List[Dict[str, Any]]:
        """Get all active products."""
        async with self._connection.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY name"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products including inactive."""
        async with self._connection.execute(
            "SELECT * FROM products ORDER BY name"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== Stock Operations ====================

    async def add_stock_item(
        self,
        product_code: str,
        email: str,
        password: str,
        two_fa_secret: Optional[str] = None,
        notes: Optional[str] = None,
        added_by: Optional[int] = None
    ) -> int:
        """Add a stock item. Returns stock ID."""
        cursor = await self._connection.execute(
            """
            INSERT INTO stock (product_code, email, password, two_fa_secret, notes, added_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (product_code, email, password, two_fa_secret, notes, added_by)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def get_available_stock_count(self, product_code: str) -> int:
        """Get count of available stock for a product."""
        async with self._connection.execute(
            "SELECT COUNT(*) as count FROM stock WHERE product_code = ? AND status = 'available'",
            (product_code,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def get_stock_summary(self) -> List[Dict[str, Any]]:
        """Get stock summary per product."""
        query = """
            SELECT
                p.product_code,
                p.name,
                p.price,
                p.is_active,
                COUNT(CASE WHEN s.status = 'available' THEN 1 END) as available,
                COUNT(CASE WHEN s.status = 'sold' THEN 1 END) as sold,
                COUNT(CASE WHEN s.status = 'reserved' THEN 1 END) as reserved,
                COUNT(s.id) as total
            FROM products p
            LEFT JOIN stock s ON p.product_code = s.product_code
            GROUP BY p.product_code
            ORDER BY p.name
        """
        async with self._connection.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def reserve_stock_item(self, product_code: str) -> Optional[Dict[str, Any]]:
        """Reserve a stock item for purchase. Returns the stock item."""
        async with self._connection.execute(
            """
            SELECT id FROM stock
            WHERE product_code = ? AND status = 'available'
            LIMIT 1
            """,
            (product_code,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

        stock_id = row["id"]
        await self._connection.execute(
            "UPDATE stock SET status = 'reserved' WHERE id = ?",
            (stock_id,)
        )
        await self._connection.commit()

        async with self._connection.execute(
            "SELECT * FROM stock WHERE id = ?", (stock_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def mark_stock_sold(self, stock_id: int, user_id: int) -> None:
        """Mark a stock item as sold."""
        await self._connection.execute(
            """
            UPDATE stock SET
                status = 'sold',
                sold_to_user_id = ?,
                sold_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (user_id, stock_id)
        )
        await self._connection.commit()

    async def release_stock_item(self, stock_id: int) -> None:
        """Release a reserved stock item back to available."""
        await self._connection.execute(
            "UPDATE stock SET status = 'available' WHERE id = ? AND status = 'reserved'",
            (stock_id,)
        )
        await self._connection.commit()

    async def get_stock_item(self, stock_id: int) -> Optional[Dict[str, Any]]:
        """Get stock item by ID."""
        async with self._connection.execute(
            "SELECT * FROM stock WHERE id = ?", (stock_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_available_stock(self, product_code: str) -> List[Dict[str, Any]]:
        """Get all available stock for a product."""
        async with self._connection.execute(
            "SELECT * FROM stock WHERE product_code = ? AND status = 'available'",
            (product_code,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== Transaction Operations ====================

    async def create_transaction(
        self,
        transaction_id: str,
        merchant_ref: str,
        user_id: int,
        product_code: str,
        amount: int,
        checkout_url: Optional[str] = None,
        qris_url: Optional[str] = None,
        expired_at: Optional[datetime] = None,
        stock_id: Optional[int] = None
    ) -> int:
        """Create a new transaction. Returns transaction ID."""
        cursor = await self._connection.execute(
            """
            INSERT INTO transactions (
                transaction_id, merchant_ref, user_id, product_code,
                amount, checkout_url, qris_url, expired_at, stock_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (transaction_id, merchant_ref, user_id, product_code,
             amount, checkout_url, qris_url, expired_at, stock_id)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get transaction by Midtrans transaction ID."""
        async with self._connection.execute(
            "SELECT * FROM transactions WHERE transaction_id = ?",
            (transaction_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_transaction_by_merchant_ref(self, merchant_ref: str) -> Optional[Dict[str, Any]]:
        """Get transaction by merchant reference (order_id)."""
        async with self._connection.execute(
            "SELECT * FROM transactions WHERE merchant_ref = ?",
            (merchant_ref,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_transaction_status(
        self,
        transaction_id: str,
        status: str,
        paid_at: Optional[datetime] = None
    ) -> None:
        """Update transaction status."""
        await self._connection.execute(
            """
            UPDATE transactions SET
                status = ?,
                paid_at = COALESCE(?, paid_at)
            WHERE transaction_id = ?
            """,
            (status, paid_at, transaction_id)
        )
        await self._connection.commit()

    async def get_user_transactions(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's transactions with optional status filter."""
        if status:
            query = """
                SELECT t.*, p.name as product_name
                FROM transactions t
                JOIN products p ON t.product_code = p.product_code
                WHERE t.user_id = ? AND t.status = ?
                ORDER BY t.created_at DESC
                LIMIT ?
            """
            params = (user_id, status, limit)
        else:
            query = """
                SELECT t.*, p.name as product_name
                FROM transactions t
                JOIN products p ON t.product_code = p.product_code
                WHERE t.user_id = ?
                ORDER BY t.created_at DESC
                LIMIT ?
            """
            params = (user_id, limit)

        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_pending_transactions_count(self, user_id: int) -> int:
        """Get count of pending transactions for a user."""
        async with self._connection.execute(
            "SELECT COUNT(*) as count FROM transactions WHERE user_id = ? AND status = 'UNPAID'",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def get_daily_purchases_count(self, user_id: int, product_code: str) -> int:
        """Get count of purchases for a product today."""
        async with self._connection.execute(
            """
            SELECT COUNT(*) as count FROM transactions
            WHERE user_id = ? AND product_code = ?
            AND date(created_at) = date('now')
            AND status IN ('PAID', 'UNPAID')
            """,
            (user_id, product_code)
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def get_expired_transactions(self) -> List[Dict[str, Any]]:
        """Get all expired unpaid transactions."""
        async with self._connection.execute(
            """
            SELECT * FROM transactions
            WHERE status = 'UNPAID' AND expired_at < CURRENT_TIMESTAMP
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_transactions_by_status(
        self,
        status: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get transactions by status."""
        async with self._connection.execute(
            """
            SELECT t.*, p.name as product_name, u.username
            FROM transactions t
            JOIN products p ON t.product_code = p.product_code
            JOIN users u ON t.user_id = u.user_id
            WHERE t.status = ?
            ORDER BY t.created_at DESC
            LIMIT ?
            """,
            (status, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== Statistics Operations ====================

    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        stats = {}

        # User stats
        async with self._connection.execute(
            "SELECT COUNT(*) as total FROM users"
        ) as cursor:
            row = await cursor.fetchone()
            stats["total_users"] = row["total"]

        async with self._connection.execute(
            "SELECT COUNT(*) as today FROM users WHERE date(join_date) = date('now')"
        ) as cursor:
            row = await cursor.fetchone()
            stats["new_users_today"] = row["today"]

        # Revenue stats
        async with self._connection.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE status = 'PAID'"
        ) as cursor:
            row = await cursor.fetchone()
            stats["total_revenue"] = row["total"]

        async with self._connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) as today
            FROM transactions
            WHERE status = 'PAID' AND date(paid_at) = date('now')
            """
        ) as cursor:
            row = await cursor.fetchone()
            stats["revenue_today"] = row["today"]

        # Transaction counts by status
        async with self._connection.execute(
            """
            SELECT status, COUNT(*) as count
            FROM transactions
            GROUP BY status
            """
        ) as cursor:
            rows = await cursor.fetchall()
            stats["transactions"] = {row["status"]: row["count"] for row in rows}

        return stats

    # ==================== Security Log Operations ====================

    async def log_security_event(
        self,
        action: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[str] = None
    ) -> None:
        """Log a security event."""
        await self._connection.execute(
            """
            INSERT INTO security_logs (user_id, action, ip_address, details)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, action, ip_address, details)
        )
        await self._connection.commit()

    async def get_security_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security logs."""
        async with self._connection.execute(
            "SELECT * FROM security_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== Rate Limit Operations ====================

    async def check_rate_limit(self, user_id: int, max_requests: int, window: int) -> bool:
        """
        Check if user has exceeded rate limit.
        Returns True if rate limited, False otherwise.
        """
        async with self._connection.execute(
            "SELECT * FROM rate_limits WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

        now = datetime.now()

        if not row:
            # First request
            await self._connection.execute(
                """
                INSERT INTO rate_limits (user_id, request_count, window_start, last_command_at)
                VALUES (?, 1, ?, ?)
                """,
                (user_id, now, now)
            )
            await self._connection.commit()
            return False

        window_start = datetime.fromisoformat(row["window_start"])
        elapsed = (now - window_start).total_seconds()

        if elapsed > window:
            # Reset window
            await self._connection.execute(
                """
                UPDATE rate_limits
                SET request_count = 1, window_start = ?, last_command_at = ?
                WHERE user_id = ?
                """,
                (now, now, user_id)
            )
            await self._connection.commit()
            return False

        if row["request_count"] >= max_requests:
            return True

        # Increment counter
        await self._connection.execute(
            """
            UPDATE rate_limits
            SET request_count = request_count + 1, last_command_at = ?
            WHERE user_id = ?
            """,
            (now, user_id)
        )
        await self._connection.commit()
        return False

    async def check_cooldown(self, user_id: int, cooldown: int) -> bool:
        """
        Check if user is in cooldown period.
        Returns True if in cooldown, False otherwise.
        """
        async with self._connection.execute(
            "SELECT last_command_at FROM rate_limits WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

        if not row or not row["last_command_at"]:
            return False

        last_command = datetime.fromisoformat(row["last_command_at"])
        elapsed = (datetime.now() - last_command).total_seconds()
        return elapsed < cooldown

    # ==================== Broadcast Operations ====================

    async def create_broadcast(
        self,
        message_text: str,
        created_by: int,
        media_type: str = "text",
        media_file_id: Optional[str] = None,
        target_audience: str = "all"
    ) -> int:
        """Create a broadcast message."""
        cursor = await self._connection.execute(
            """
            INSERT INTO broadcast_messages
            (message_text, media_type, media_file_id, target_audience, created_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message_text, media_type, media_file_id, target_audience, created_by)
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def update_broadcast_stats(
        self,
        broadcast_id: int,
        total_sent: int,
        total_failed: int
    ) -> None:
        """Update broadcast delivery statistics."""
        await self._connection.execute(
            """
            UPDATE broadcast_messages
            SET sent_at = CURRENT_TIMESTAMP, total_sent = ?, total_failed = ?
            WHERE id = ?
            """,
            (total_sent, total_failed, broadcast_id)
        )
        await self._connection.commit()

    # ==================== Admin UI Helper Operations ====================

    async def get_user_count(self) -> int:
        """Get total user count."""
        async with self._connection.execute(
            "SELECT COUNT(*) as count FROM users"
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def get_admins(self) -> List[Dict[str, Any]]:
        """Get all admins (alias for get_all_admins)."""
        return await self.get_all_admins()

    async def get_banned_user_count(self) -> int:
        """Get count of banned users."""
        async with self._connection.execute(
            "SELECT COUNT(*) as count FROM users WHERE is_banned = 1"
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def get_active_users_count(self, days: int = 7) -> int:
        """Get count of users active within N days."""
        async with self._connection.execute(
            f"SELECT COUNT(*) as count FROM users WHERE last_activity >= datetime('now', '-{days} days')"
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently registered users."""
        async with self._connection.execute(
            "SELECT * FROM users ORDER BY join_date DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_buyers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top buyers with purchase stats."""
        async with self._connection.execute(
            """
            SELECT 
                u.*,
                COUNT(t.id) as purchase_count,
                COALESCE(SUM(t.amount), 0) as total_spent
            FROM users u
            JOIN transactions t ON u.user_id = t.user_id
            WHERE t.status = 'PAID'
            GROUP BY u.user_id
            ORDER BY total_spent DESC
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_stock_items(self, product_code: str) -> List[Dict[str, Any]]:
        """Get all stock items for a product."""
        async with self._connection.execute(
            "SELECT * FROM stock WHERE product_code = ? ORDER BY added_at DESC",
            (product_code,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_stock_by_id(self, stock_id: int) -> Optional[Dict[str, Any]]:
        """Get stock item by ID (alias for get_stock_item)."""
        return await self.get_stock_item(stock_id)

    async def get_sold_stock_count(self, product_code: str) -> int:
        """Get count of sold stock for a product."""
        async with self._connection.execute(
            "SELECT COUNT(*) as count FROM stock WHERE product_code = ? AND status = 'sold'",
            (product_code,)
        ) as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def delete_stock_item(self, stock_id: int) -> bool:
        """Delete a stock item."""
        await self._connection.execute(
            "DELETE FROM stock WHERE id = ?",
            (stock_id,)
        )
        await self._connection.commit()
        return True

    async def get_all_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all transactions."""
        async with self._connection.execute(
            """
            SELECT t.*, p.name as product_name, u.username
            FROM transactions t
            JOIN products p ON t.product_code = p.product_code
            JOIN users u ON t.user_id = u.user_id
            ORDER BY t.created_at DESC
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_refund_requests(self) -> List[Dict[str, Any]]:
        """Get pending refund requests."""
        return await self.get_transactions_by_status("REFUND_REQUESTED", limit=100)

    async def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics."""
        stats = {}
        
        # Count by status
        async with self._connection.execute(
            """
            SELECT status, COUNT(*) as count
            FROM transactions
            GROUP BY status
            """
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                stats[row["status"]] = row["count"]
        
        # Revenue today
        async with self._connection.execute(
            """
            SELECT COALESCE(SUM(amount), 0) as revenue
            FROM transactions
            WHERE status = 'PAID' AND date(paid_at) = date('now')
            """
        ) as cursor:
            row = await cursor.fetchone()
            stats["revenue_today"] = row["revenue"] if row else 0
        
        # Total revenue
        async with self._connection.execute(
            "SELECT COALESCE(SUM(amount), 0) as revenue FROM transactions WHERE status = 'PAID'"
        ) as cursor:
            row = await cursor.fetchone()
            stats["revenue_total"] = row["revenue"] if row else 0
        
        return stats

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics (alias for get_stats)."""
        return await self.get_stats()

