"""
Inline keyboard layouts for FRIENDS Store Telegram Bot.
3-column fixed layout with pagination support.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Optional
import math


class Keyboards:
    """Collection of inline keyboard layouts - 3 columns fixed."""

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

    # Items per page for lists
    ITEMS_PER_PAGE = 6

    # Number emojis for buttons
    NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main menu keyboard - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("🛒 Beli", callback_data="nav:products"),
                InlineKeyboardButton("📜 Riwayat", callback_data="nav:history"),
                InlineKeyboardButton("❓ Bantuan", callback_data="nav:help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def nav_row_3col(
        back_target: str = "main",
        page: Optional[int] = None,
        total_pages: Optional[int] = None,
        prefix: str = ""
    ) -> List[InlineKeyboardButton]:
        """3-column navigation row with optional pagination."""
        buttons = []

        # Left button: Prev or Back
        if page and page > 1:
            buttons.append(
                InlineKeyboardButton("◀️ Prev", callback_data=f"{prefix}:page:{page - 1}")
            )
        else:
            buttons.append(
                InlineKeyboardButton("🔙 Back", callback_data=f"nav:{back_target}")
            )

        # Center: Home
        buttons.append(
            InlineKeyboardButton("🏠 Home", callback_data="nav:main")
        )

        # Right button: Next or Help
        if page and total_pages and page < total_pages:
            buttons.append(
                InlineKeyboardButton("Next ▶️", callback_data=f"{prefix}:page:{page + 1}")
            )
        else:
            buttons.append(
                InlineKeyboardButton("❓ Help", callback_data="nav:help")
            )

        return buttons

    @staticmethod
    def product_list(
        products: List[Dict],
        page: int = 1,
        items_per_page: int = 6
    ) -> InlineKeyboardMarkup:
        """
        Product list with 3-column numbered buttons and pagination.
        
        Layout:
        [1️⃣] [2️⃣] [3️⃣]
        [4️⃣] [5️⃣] [6️⃣]
        [◀️ Prev] [🏠 Home] [Next ▶️]
        """
        total_pages = max(1, math.ceil(len(products) / items_per_page))
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_products = products[start_idx:end_idx]

        keyboard = []

        # Number buttons - 3 per row
        for i in range(0, len(page_products), 3):
            row = []
            for j in range(3):
                idx = i + j
                if idx < len(page_products):
                    product = page_products[idx]
                    row.append(
                        InlineKeyboardButton(
                            Keyboards.NUMBER_EMOJIS[idx],
                            callback_data=f"product:{product['product_code']}"
                        )
                    )
            keyboard.append(row)

        # Navigation row
        keyboard.append(
            Keyboards.nav_row_3col(
                back_target="main",
                page=page,
                total_pages=total_pages,
                prefix="prodlist"
            )
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def product_detail(
        product_code: str,
        has_stock: bool,
        price: int
    ) -> InlineKeyboardMarkup:
        """
        Product detail keyboard.
        
        Layout:
        [💳 Buy Now (Rp XX.XXX)]
        [🔙 Back] [🏠 Home] [❓ Help]
        """
        keyboard = []

        if has_stock:
            price_formatted = f"{price:,}".replace(',', '.')
            keyboard.append([
                InlineKeyboardButton(
                    f"💳 Bayar Sekarang (Rp {price_formatted})",
                    callback_data=f"buy:{product_code}"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("❌ Stok Habis", callback_data="noop")
            ])

        keyboard.append([
            InlineKeyboardButton("🔙 Back", callback_data="nav:products"),
            InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
            InlineKeyboardButton("❓ Help", callback_data="nav:help")
        ])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_pending(
        transaction_id: str,
        checkout_url: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """
        Pending payment keyboard.
        
        Layout:
        [✅ Sudah Bayar] [❌ Batal] [ℹ️ Info]
        """
        keyboard = []

        if checkout_url:
            keyboard.append([
                InlineKeyboardButton("🔗 Buka Link", url=checkout_url)
            ])

        keyboard.append([
            InlineKeyboardButton("✅ Sudah Bayar", callback_data=f"pay:check:{transaction_id}"),
            InlineKeyboardButton("❌ Batal", callback_data=f"pay:cancel:{transaction_id}"),
            InlineKeyboardButton("ℹ️ Info", callback_data="help:payment")
        ])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def history_list(
        transactions: List[Dict],
        page: int = 1,
        items_per_page: int = 6
    ) -> InlineKeyboardMarkup:
        """
        Transaction history with 3-column numbered buttons.
        
        Layout:
        [1️⃣] [2️⃣] [3️⃣]
        [4️⃣] [5️⃣] [6️⃣]
        [◀️ Prev] [🏠 Home] [Next ▶️]
        """
        total_pages = max(1, math.ceil(len(transactions) / items_per_page))
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_transactions = transactions[start_idx:end_idx]

        keyboard = []

        # Number buttons - 3 per row
        for i in range(0, len(page_transactions), 3):
            row = []
            for j in range(3):
                idx = i + j
                if idx < len(page_transactions):
                    tx = page_transactions[idx]
                    row.append(
                        InlineKeyboardButton(
                            Keyboards.NUMBER_EMOJIS[idx],
                            callback_data=f"history:view:{tx['transaction_id']}"
                        )
                    )
            keyboard.append(row)

        # Navigation row
        keyboard.append(
            Keyboards.nav_row_3col(
                back_target="main",
                page=page,
                total_pages=total_pages,
                prefix="history"
            )
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def history_filters() -> InlineKeyboardMarkup:
        """
        Transaction history filter keyboard - 3 columns.
        
        Layout:
        [📋 Semua] [✅ Paid] [⏳ Pending]
        [🔙 Back] [🏠 Home] [❓ Help]
        """
        keyboard = [
            [
                InlineKeyboardButton("📋 Semua", callback_data="history:filter:all"),
                InlineKeyboardButton("✅ Paid", callback_data="history:filter:PAID"),
                InlineKeyboardButton("⏳ Pending", callback_data="history:filter:UNPAID")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="nav:main"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="nav:help")
            ]
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
                InlineKeyboardButton("📥 Download", callback_data=f"history:download:{transaction_id}"),
                InlineKeyboardButton("🔄 Refund", callback_data=f"history:refund:{transaction_id}"),
                InlineKeyboardButton("📋 Detail", callback_data="noop")
            ])
        elif status == "UNPAID":
            keyboard.append([
                InlineKeyboardButton("💳 Bayar", callback_data=f"pay:view:{transaction_id}"),
                InlineKeyboardButton("❌ Batal", callback_data=f"pay:cancel:{transaction_id}"),
                InlineKeyboardButton("📋 Detail", callback_data="noop")
            ])
        elif status == "EXPIRED":
            keyboard.append([
                InlineKeyboardButton("🔄 Order Ulang", callback_data=f"history:reorder:{transaction_id}")
            ])

        keyboard.append([
            InlineKeyboardButton("🔙 Back", callback_data="nav:history"),
            InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
            InlineKeyboardButton("❓ Help", callback_data="nav:help")
        ])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def help_categories() -> InlineKeyboardMarkup:
        """
        Help center - 3 columns.
        
        Layout:
        [📖 Order] [💳 Bayar] [❓ FAQ]
        [📞 Contact] [🏠 Home] [🔙 Back]
        """
        keyboard = [
            [
                InlineKeyboardButton("📖 Order", callback_data="help:order"),
                InlineKeyboardButton("💳 Bayar", callback_data="help:payment"),
                InlineKeyboardButton("❓ FAQ", callback_data="help:faq")
            ],
            [
                InlineKeyboardButton("📞 Contact", callback_data="help:contact"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("🔙 Back", callback_data="nav:main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def help_back() -> InlineKeyboardMarkup:
        """Back navigation for help pages - 3 columns."""
        keyboard = [[
            InlineKeyboardButton("🔙 Back", callback_data="nav:help"),
            InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
            InlineKeyboardButton("❓ More", callback_data="nav:help")
        ]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_cancel(action: str, item_id: str) -> InlineKeyboardMarkup:
        """Confirmation dialog - 3 columns."""
        keyboard = [[
            InlineKeyboardButton("✅ Ya", callback_data=f"confirm:{action}:{item_id}"),
            InlineKeyboardButton("❌ Tidak", callback_data=f"cancel:{action}:{item_id}"),
            InlineKeyboardButton("ℹ️ Info", callback_data="noop")
        ]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def navigation(show_back: bool = True, back_target: str = "main") -> InlineKeyboardMarkup:
        """Simple navigation - 3 columns."""
        buttons = [
            InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
            InlineKeyboardButton("❓ Help", callback_data="nav:help")
        ]
        if show_back:
            buttons.append(
                InlineKeyboardButton("🔙 Back", callback_data=f"nav:{back_target}")
            )
        return InlineKeyboardMarkup([buttons])

    # ==================== Admin Keyboards ====================

    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """
        Admin main menu - 3 columns.
        
        Layout:
        [📦 Stock] [🛍️ Produk] [💰 Trans]
        [📢 Broadcast] [👥 Users] [📊 Stats]
        [⚙️ System] [🏠 Home] [❓ Help]
        """
        keyboard = [
            [
                InlineKeyboardButton("📦 Stock", callback_data="admin:stock"),
                InlineKeyboardButton("🛍️ Produk", callback_data="admin:products"),
                InlineKeyboardButton("💰 Trans", callback_data="admin:transactions")
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast"),
                InlineKeyboardButton("👥 Users", callback_data="admin:users"),
                InlineKeyboardButton("📊 Stats", callback_data="admin:stats")
            ],
            [
                InlineKeyboardButton("⚙️ System", callback_data="admin:system"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="nav:help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_stock_list(
        products: List[Dict],
        page: int = 1,
        items_per_page: int = 6
    ) -> InlineKeyboardMarkup:
        """Admin stock list with 3-column numbered buttons."""
        total_pages = max(1, math.ceil(len(products) / items_per_page))
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_products = products[start_idx:end_idx]

        keyboard = []

        # Number buttons - 3 per row
        for i in range(0, len(page_products), 3):
            row = []
            for j in range(3):
                idx = i + j
                if idx < len(page_products):
                    product = page_products[idx]
                    row.append(
                        InlineKeyboardButton(
                            Keyboards.NUMBER_EMOJIS[idx],
                            callback_data=f"admin:stock:{product['product_code']}"
                        )
                    )
            keyboard.append(row)

        # Navigation row
        keyboard.append(
            Keyboards.nav_row_3col(
                back_target="admin:menu",
                page=page,
                total_pages=total_pages,
                prefix="admin:stocklist"
            )
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def broadcast_targets() -> InlineKeyboardMarkup:
        """Broadcast target selection - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("👥 Semua", callback_data="admin:broadcast:all"),
                InlineKeyboardButton("🛒 Buyers", callback_data="admin:broadcast:buyers"),
                InlineKeyboardButton("📅 Active", callback_data="admin:broadcast:active_7days")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="admin:cancel"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="nav:help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def refund_actions(transaction_id: str) -> InlineKeyboardMarkup:
        """Refund approval/rejection - 3 columns."""
        keyboard = [[
            InlineKeyboardButton("✅ Approve", callback_data=f"admin:refund:approve:{transaction_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin:refund:reject:{transaction_id}"),
            InlineKeyboardButton("📋 Detail", callback_data=f"history:view:{transaction_id}")
        ]]
        return InlineKeyboardMarkup(keyboard)

