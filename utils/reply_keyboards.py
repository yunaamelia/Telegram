"""
Reply keyboard builders for FRIENDS Store Telegram Bot.
"""

from telegram import KeyboardButton, ReplyKeyboardMarkup

from utils.unicode_fonts import UnicodeFonts as uf


class UserReplyKeyboard:
    """User reply keyboard - 2x3 layout (6 buttons)."""

    # Styled button text with Unicode fonts
    BUTTONS = [
        [f"🛒 {uf.sans('Beli')}", f"📜 {uf.sans('Riwayat')}", f"❓ {uf.sans('Bantuan')}"],
        [f"💳 {uf.sans('Cek Bayar')}", f"🔄 {uf.sans('Refund')}", f"🏠 {uf.sans('Menu')}"]
    ]

    # Mapping button text to command/action
    HANDLERS = {
        f"🛒 {uf.sans('Beli')}": "show_products",
        f"📜 {uf.sans('Riwayat')}": "show_history",
        f"❓ {uf.sans('Bantuan')}": "show_help",
        f"💳 {uf.sans('Cek Bayar')}": "check_payment",
        f"🔄 {uf.sans('Refund')}": "request_refund",
        f"🏠 {uf.sans('Menu')}": "show_main_menu"
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
