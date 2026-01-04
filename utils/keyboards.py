"""
Inline keyboard layouts for FRIENDS Store Telegram Bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Optional


class Keyboards:
    """Collection of inline keyboard layouts."""

    # Callback data prefixes
    PREFIX_PRODUCT = "product:"
    PREFIX_BUY = "buy:"
    PREFIX_PAY = "pay:"
    PREFIX_HISTORY = "history:"
    PREFIX_HELP = "help:"
    PREFIX_ADMIN = "admin:"
    PREFIX_CONFIRM = "confirm:"
    PREFIX_CANCEL = "cancel:"
    PREFIX_NAV = "nav:"

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main menu keyboard."""
        keyboard = [
            [InlineKeyboardButton("🛒 Beli Produk", callback_data="nav:products")],
            [InlineKeyboardButton("📜 Riwayat Pembelian", callback_data="nav:history")],
            [InlineKeyboardButton("❓ Bantuan", callback_data="nav:help")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def navigation(show_back: bool = True, back_target: str = "main") -> InlineKeyboardMarkup:
        """Navigation buttons: Home, Help, Back."""
        buttons = [
            InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
            InlineKeyboardButton("❓ Help", callback_data="nav:help")
        ]
        if show_back:
            buttons.append(
                InlineKeyboardButton("🔙 Back", callback_data=f"nav:{back_target}")
            )
        return InlineKeyboardMarkup([buttons])

    @staticmethod
    def nav_row(back_target: str = "main") -> List[InlineKeyboardButton]:
        """Single navigation row for embedding in other keyboards."""
        return [
            InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
            InlineKeyboardButton("❓ Help", callback_data="nav:help"),
            InlineKeyboardButton("🔙 Back", callback_data=f"nav:{back_target}")
        ]

    @staticmethod
    def product_list(products: List[Dict]) -> InlineKeyboardMarkup:
        """Product selection keyboard."""
        keyboard = []
        for product in products:
            keyboard.append([
                InlineKeyboardButton(
                    f"📦 {product['name']}",
                    callback_data=f"product:{product['product_code']}"
                )
            ])
        keyboard.append(Keyboards.nav_row("main"))
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def product_detail(
        product_code: str,
        has_stock: bool,
        price: int
    ) -> InlineKeyboardMarkup:
        """Product detail keyboard with buy button."""
        keyboard = []

        if has_stock:
            keyboard.append([
                InlineKeyboardButton(
                    f"💳 Bayar Sekarang (Rp {price:,})",
                    callback_data=f"buy:{product_code}"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("❌ Stok Habis", callback_data="noop")
            ])

        keyboard.append(Keyboards.nav_row("products"))
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_pending(
        transaction_id: str,
        checkout_url: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """Pending payment keyboard."""
        keyboard = []

        if checkout_url:
            keyboard.append([
                InlineKeyboardButton("🔗 Buka Link Pembayaran", url=checkout_url)
            ])

        keyboard.append([
            InlineKeyboardButton("🔄 Cek Status", callback_data=f"pay:check:{transaction_id}"),
            InlineKeyboardButton("❌ Batalkan", callback_data=f"pay:cancel:{transaction_id}")
        ])

        keyboard.append(Keyboards.nav_row("main"))
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def history_filters() -> InlineKeyboardMarkup:
        """Transaction history filter keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📋 Semua", callback_data="history:filter:all"),
                InlineKeyboardButton("✅ Berhasil", callback_data="history:filter:PAID")
            ],
            [
                InlineKeyboardButton("⏳ Pending", callback_data="history:filter:UNPAID"),
                InlineKeyboardButton("❌ Expired", callback_data="history:filter:EXPIRED")
            ],
            Keyboards.nav_row("main")
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def transaction_actions(
        transaction_id: str,
        status: str
    ) -> InlineKeyboardMarkup:
        """Transaction action buttons based on status."""
        keyboard = []

        if status == "PAID":
            keyboard.append([
                InlineKeyboardButton(
                    "📥 Download Detail Akun",
                    callback_data=f"history:download:{transaction_id}"
                )
            ])
            keyboard.append([
                InlineKeyboardButton(
                    "🔄 Request Refund",
                    callback_data=f"history:refund:{transaction_id}"
                )
            ])
        elif status == "UNPAID":
            keyboard.append([
                InlineKeyboardButton(
                    "💳 Bayar Sekarang",
                    callback_data=f"pay:view:{transaction_id}"
                )
            ])
        elif status == "EXPIRED":
            keyboard.append([
                InlineKeyboardButton(
                    "🔄 Order Ulang",
                    callback_data=f"history:reorder:{transaction_id}"
                )
            ])

        keyboard.append(Keyboards.nav_row("history"))
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def help_categories() -> InlineKeyboardMarkup:
        """Help center category selection."""
        keyboard = [
            [InlineKeyboardButton("📖 Cara Order", callback_data="help:order")],
            [InlineKeyboardButton("💳 Cara Pembayaran", callback_data="help:payment")],
            [InlineKeyboardButton("❓ FAQ Produk", callback_data="help:faq")],
            [InlineKeyboardButton("📞 Contact Admin", callback_data="help:contact")],
            Keyboards.nav_row("main")
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def help_back() -> InlineKeyboardMarkup:
        """Back button for help pages."""
        keyboard = [Keyboards.nav_row("help")]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_cancel(action: str, item_id: str) -> InlineKeyboardMarkup:
        """Confirmation dialog."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Ya, Lanjutkan", callback_data=f"confirm:{action}:{item_id}"),
                InlineKeyboardButton("❌ Tidak, Batalkan", callback_data=f"cancel:{action}:{item_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== Admin Keyboards ====================

    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Admin main menu."""
        keyboard = [
            [
                InlineKeyboardButton("📦 Kelola Stock", callback_data="admin:stock"),
                InlineKeyboardButton("🛍️ Kelola Produk", callback_data="admin:products")
            ],
            [
                InlineKeyboardButton("💰 Transaksi", callback_data="admin:transactions"),
                InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast")
            ],
            [
                InlineKeyboardButton("👥 Users", callback_data="admin:users"),
                InlineKeyboardButton("📊 Stats", callback_data="admin:stats")
            ],
            [InlineKeyboardButton("⚙️ System", callback_data="admin:system")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def broadcast_targets() -> InlineKeyboardMarkup:
        """Broadcast target audience selection."""
        keyboard = [
            [InlineKeyboardButton("👥 Semua User", callback_data="admin:broadcast:all")],
            [InlineKeyboardButton("🛒 Buyers Only", callback_data="admin:broadcast:buyers")],
            [InlineKeyboardButton("📅 Active 7 Days", callback_data="admin:broadcast:active_7days")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def refund_actions(transaction_id: str) -> InlineKeyboardMarkup:
        """Refund approval/rejection buttons."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"admin:refund:approve:{transaction_id}"
                ),
                InlineKeyboardButton(
                    "❌ Reject",
                    callback_data=f"admin:refund:reject:{transaction_id}"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def pagination(
        current_page: int,
        total_pages: int,
        prefix: str
    ) -> List[InlineKeyboardButton]:
        """Pagination buttons."""
        buttons = []

        if current_page > 1:
            buttons.append(
                InlineKeyboardButton("◀️", callback_data=f"{prefix}:page:{current_page - 1}")
            )

        buttons.append(
            InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop")
        )

        if current_page < total_pages:
            buttons.append(
                InlineKeyboardButton("▶️", callback_data=f"{prefix}:page:{current_page + 1}")
            )

        return buttons
