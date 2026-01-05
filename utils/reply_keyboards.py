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
