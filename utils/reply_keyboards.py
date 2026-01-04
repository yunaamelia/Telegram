"""
Reply keyboard builders for FRIENDS Store Telegram Bot.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton
from typing import List


class UserReplyKeyboard:
    """User reply keyboard - 2x3 layout (6 buttons)."""

    BUTTONS = [
        ["🛒 Beli Produk", "📜 Riwayat", "❓ Bantuan"],
        ["💳 Cek Bayar", "🔄 Refund", "🏠 Menu"]
    ]

    # Mapping button text to command/action
    HANDLERS = {
        "🛒 Beli Produk": "show_products",
        "📜 Riwayat": "show_history",
        "❓ Bantuan": "show_help",
        "💳 Cek Bayar": "check_payment",
        "🔄 Refund": "request_refund",
        "🏠 Menu": "show_main_menu"
    }

    @staticmethod
    def build() -> ReplyKeyboardMarkup:
        """Build user reply keyboard."""
        keyboard = [
            [KeyboardButton(btn) for btn in row]
            for row in UserReplyKeyboard.BUTTONS
        ]
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Pilih menu..."
        )


class AdminReplyKeyboard:
    """Admin reply keyboard - Paginated 2x3 + navigation (3 pages)."""

    PAGES = [
        # Page 1: Stock & Products
        ["📦 Add Stock", "➕ Produk", "✏️ Edit",
         "📋 Cek Stock", "💰 Transaksi", "💸 Refunds"],
        # Page 2: Management
        ["📊 Stats", "🔒 Security", "👥 Add Admin",
         "📢 Broadcast", "🔧 Logs", "💾 Backup"],
        # Page 3: Advanced
        ["🗑️ Delete", "📃 List", "🔍 Search",
         "📈 Reports", "⚙️ Config", "🌐 API"]
    ]

    # Mapping button text to command/action
    HANDLERS = {
        # Page 1
        "📦 Add Stock": "addstock",
        "➕ Produk": "addproduct",
        "✏️ Edit": "editproduct",
        "📋 Cek Stock": "checkstock",
        "💰 Transaksi": "transactions",
        "💸 Refunds": "refunds",
        # Page 2
        "📊 Stats": "stats",
        "🔒 Security": "security",
        "👥 Add Admin": "addadmin",
        "📢 Broadcast": "broadcast",
        "🔧 Logs": "logs",
        "💾 Backup": "backup",
        # Page 3
        "🗑️ Delete": "deleteproduct",
        "📃 List": "listproducts",
        "🔍 Search": "search",
        "📈 Reports": "reports",
        "⚙️ Config": "config",
        "🌐 API": "api",
        # Navigation
        "◀️ Prev": "admin_prev",
        "Next ▶️": "admin_next",
        "🏠 Menu": "show_main_menu"
    }

    @staticmethod
    def build(page: int = 1) -> ReplyKeyboardMarkup:
        """Build admin reply keyboard for specific page."""
        total_pages = len(AdminReplyKeyboard.PAGES)
        page = max(1, min(page, total_pages))

        buttons = AdminReplyKeyboard.PAGES[page - 1]

        keyboard = [
            [KeyboardButton(btn) for btn in buttons[0:3]],
            [KeyboardButton(btn) for btn in buttons[3:6]]
        ]

        # Navigation row
        nav_row = []
        if page > 1:
            nav_row.append(KeyboardButton("◀️ Prev"))
        nav_row.append(KeyboardButton("🏠 Menu"))
        if page < total_pages:
            nav_row.append(KeyboardButton("Next ▶️"))

        keyboard.append(nav_row)

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder=f"Admin Menu ({page}/{total_pages})"
        )

    @staticmethod
    def get_total_pages() -> int:
        """Get total number of pages."""
        return len(AdminReplyKeyboard.PAGES)
