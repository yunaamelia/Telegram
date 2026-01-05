"""
Admin-specific keyboard builders.
All keyboards use 3-column layout for consistency.
"""

import math
from typing import Dict, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from utils.unicode_fonts import UnicodeFonts as uf


class AdminKeyboards:
    """Admin keyboard builders with hierarchical navigation."""

    # Emoji constants for consistency
    NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    # ==================== Main Dashboard ====================

    @staticmethod
    def main_dashboard(expanded: bool = False) -> InlineKeyboardMarkup:
        """
        Main admin dashboard - hierarchical navigation.

        Args:
            expanded: If True, show all quick actions. If False, show collapsed view.
        """
        keyboard = []

        if expanded:
            # Expanded view - show all quick actions
            keyboard.append([
                InlineKeyboardButton(f"⭐ {uf.sans('Quick Actions')} ▲", callback_data="admin:quick:collapse")
            ])
            keyboard.append([
                InlineKeyboardButton(f"📦 {uf.sans('Add Stock')}", callback_data="admin:quick:addstock"),
                InlineKeyboardButton(f"📊 {uf.sans('Stats')}", callback_data="admin:quick:stats"),
                InlineKeyboardButton(f"💰 {uf.sans('Trans')}", callback_data="admin:quick:trans")
            ])
            keyboard.append([
                InlineKeyboardButton(f"🔧 {uf.sans('Logs')}", callback_data="admin:quick:logs"),
                InlineKeyboardButton(f"💾 {uf.sans('Backup')}", callback_data="admin:quick:backup"),
                InlineKeyboardButton(f"📢 {uf.sans('BC')}", callback_data="admin:quick:broadcast")
            ])
            keyboard.append([
                InlineKeyboardButton(f"➕ {uf.sans('Add Product')}", callback_data="admin:product:add"),
                InlineKeyboardButton(f"📋 {uf.sans('Products')}", callback_data="admin:menu:products"),
                InlineKeyboardButton(f"👥 {uf.sans('Users')}", callback_data="admin:menu:users")
            ])
        else:
            # Collapsed view - minimal quick actions
            keyboard.append([
                InlineKeyboardButton(f"⭐ {uf.sans('Quick Actions')} ▼", callback_data="admin:quick:expand")
            ])
            keyboard.append([
                InlineKeyboardButton(f"📦 {uf.sans('+Stock')}", callback_data="admin:quick:addstock"),
                InlineKeyboardButton(f"📊 {uf.sans('Stats')}", callback_data="admin:quick:stats"),
                InlineKeyboardButton(f"💰 {uf.sans('Trans')}", callback_data="admin:quick:trans")
            ])

        # Divider
        keyboard.append([InlineKeyboardButton("───────────────", callback_data="noop")])

        # Full Menu Header - Clickable
        keyboard.append([
            InlineKeyboardButton(f"📂 {uf.sans('Full Menu')} ▶", callback_data="admin:fullmenu:toggle")
        ])

        # Category buttons
        keyboard.append([InlineKeyboardButton(
            f"📦 {uf.sans('Stock Management')}", callback_data="admin:menu:stock")])
        keyboard.append([InlineKeyboardButton(
            f"🛍️ {uf.sans('Product Management')}", callback_data="admin:menu:products")])
        keyboard.append([InlineKeyboardButton(
            f"💰 {uf.sans('Transactions')}", callback_data="admin:menu:transactions")])
        keyboard.append([InlineKeyboardButton(
            f"👥 {uf.sans('User Management')}", callback_data="admin:menu:users")])
        keyboard.append([InlineKeyboardButton(
            f"📊 {uf.sans('Reports & Analytics')}", callback_data="admin:menu:reports")])
        keyboard.append([InlineKeyboardButton(
            f"⚙️ {uf.sans('System & Settings')}", callback_data="admin:menu:system")])
        # Bottom navigation
        keyboard.append([
            InlineKeyboardButton(f"🏠 {uf.sans('Home')}", callback_data="nav:main"),
            InlineKeyboardButton(f"❓ {uf.sans('Help')}", callback_data="admin:help"),
            InlineKeyboardButton(f"🔄 {uf.sans('Refresh')}", callback_data="admin:dashboard")
        ])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def main_dashboard_full() -> InlineKeyboardMarkup:
        """Full menu view - all categories expanded inline."""
        keyboard = [
            # Header
            [InlineKeyboardButton("📂 Full Menu ✓", callback_data="admin:dashboard")],

            # Stock
            [InlineKeyboardButton("─── 📦 Stock ───", callback_data="noop")],
            [
                InlineKeyboardButton("➕ Add", callback_data="admin:stock:add"),
                InlineKeyboardButton("📋 Check", callback_data="admin:stock:check"),
                InlineKeyboardButton("⚠️ Low", callback_data="admin:stock:lowstock")
            ],

            # Products
            [InlineKeyboardButton("─── 🛍️ Products ───", callback_data="noop")],
            [
                InlineKeyboardButton("➕ Add", callback_data="admin:product:add"),
                InlineKeyboardButton("📃 List", callback_data="admin:product:list"),
                InlineKeyboardButton("✏️ Edit", callback_data="admin:product:edit")
            ],

            # Transactions
            [InlineKeyboardButton("─── 💰 Trans ───", callback_data="noop")],
            [
                InlineKeyboardButton("📋 All", callback_data="admin:trans:all"),
                InlineKeyboardButton("⏳ Unpaid", callback_data="admin:trans:unpaid"),
                InlineKeyboardButton("✅ Paid", callback_data="admin:trans:paid")
            ],

            # Users
            [InlineKeyboardButton("─── 👥 Users ───", callback_data="noop")],
            [
                InlineKeyboardButton("👥 All", callback_data="admin:user:all"),
                InlineKeyboardButton("🚫 Banned", callback_data="admin:user:banned"),
                InlineKeyboardButton("🔍 Search", callback_data="admin:user:search")
            ],

            # System
            [InlineKeyboardButton("─── ⚙️ System ───", callback_data="noop")],
            [
                InlineKeyboardButton("📊 Stats", callback_data="admin:system:stats"),
                InlineKeyboardButton("💾 Backup", callback_data="admin:system:backup"),
                InlineKeyboardButton("📢 BC", callback_data="admin:system:broadcast")
            ],

            # Back
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin:dashboard")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== Category Menus ====================

    @staticmethod
    def stock_management_menu() -> InlineKeyboardMarkup:
        """Stock management submenu - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Stock", callback_data="admin:stock:add"),
                InlineKeyboardButton("📋 Check Stock", callback_data="admin:stock:check"),
                InlineKeyboardButton("📊 Details", callback_data="admin:stock:details")
            ],
            [
                InlineKeyboardButton("⚠️ Low Stock", callback_data="admin:stock:lowstock"),
                InlineKeyboardButton("📤 Bulk Upload", callback_data="admin:stock:bulk"),
                InlineKeyboardButton("📥 Export", callback_data="admin:stock:export")
            ],
            [
                InlineKeyboardButton("🔙 Dashboard", callback_data="admin:dashboard"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help:stock")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def product_management_menu() -> InlineKeyboardMarkup:
        """Product management submenu - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Product", callback_data="admin:product:add"),
                InlineKeyboardButton("📃 List All", callback_data="admin:product:list"),
                InlineKeyboardButton("✏️ Edit", callback_data="admin:product:edit")
            ],
            [
                InlineKeyboardButton("🗑️ Delete", callback_data="admin:product:delete"),
                InlineKeyboardButton("🔄 Toggle Active", callback_data="admin:product:toggle"),
                InlineKeyboardButton("💰 Bulk Price", callback_data="admin:product:bulkprice")
            ],
            [
                InlineKeyboardButton("🔙 Dashboard", callback_data="admin:dashboard"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help:product")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def transaction_management_menu() -> InlineKeyboardMarkup:
        """Transaction management submenu - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("📋 All Trans", callback_data="admin:trans:all"),
                InlineKeyboardButton("⏳ Unpaid", callback_data="admin:trans:unpaid"),
                InlineKeyboardButton("✅ Paid", callback_data="admin:trans:paid")
            ],
            [
                InlineKeyboardButton("❌ Expired", callback_data="admin:trans:expired"),
                InlineKeyboardButton("💸 Refunds", callback_data="admin:trans:refunds"),
                InlineKeyboardButton("📊 Summary", callback_data="admin:trans:summary")
            ],
            [
                InlineKeyboardButton("🔙 Dashboard", callback_data="admin:dashboard"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help:trans")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def user_management_menu() -> InlineKeyboardMarkup:
        """User management submenu - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("👥 All Users", callback_data="admin:user:all"),
                InlineKeyboardButton("💰 Buyers", callback_data="admin:user:buyers"),
                InlineKeyboardButton("🚫 Banned", callback_data="admin:user:banned")
            ],
            [
                InlineKeyboardButton("🔒 Ban User", callback_data="admin:user:ban"),
                InlineKeyboardButton("🔓 Unban", callback_data="admin:user:unban"),
                InlineKeyboardButton("🔍 Search", callback_data="admin:user:search")
            ],
            [
                InlineKeyboardButton("🔙 Dashboard", callback_data="admin:dashboard"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help:user")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def system_menu() -> InlineKeyboardMarkup:
        """System & settings submenu - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Statistics", callback_data="admin:system:stats"),
                InlineKeyboardButton("🔧 View Logs", callback_data="admin:system:logs"),
                InlineKeyboardButton("💾 Backup DB", callback_data="admin:system:backup")
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin:system:broadcast"),
                InlineKeyboardButton("👥 Admins", callback_data="admin:system:admins"),
                InlineKeyboardButton("🔒 Security", callback_data="admin:system:security")
            ],
            [
                InlineKeyboardButton("🔙 Dashboard", callback_data="admin:dashboard"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help:system")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def reports_menu() -> InlineKeyboardMarkup:
        """Reports & Analytics submenu - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Daily Report", callback_data="admin:reports:daily"),
                InlineKeyboardButton("📈 Weekly", callback_data="admin:reports:weekly"),
                InlineKeyboardButton("📉 Monthly", callback_data="admin:reports:monthly")
            ],
            [
                InlineKeyboardButton("💰 Revenue", callback_data="admin:reports:revenue"),
                InlineKeyboardButton("📦 Stock Report", callback_data="admin:reports:stock"),
                InlineKeyboardButton("👥 User Stats", callback_data="admin:reports:users")
            ],
            [
                InlineKeyboardButton("🔙 Dashboard", callback_data="admin:dashboard"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help:reports")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== List Display Keyboards ====================

    @staticmethod
    def product_list(
        products: List[Dict],
        page: int = 1,
        items_per_page: int = 6,
        context: str = "view"
    ) -> InlineKeyboardMarkup:
        """
        Product list with numbered buttons (3 columns).

        Args:
            products: List of product dicts
            page: Current page number
            items_per_page: Items to show per page
            context: 'view', 'edit', 'delete', 'addstock'
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
                            AdminKeyboards.NUMBER_EMOJIS[idx],
                            callback_data=f"admin:product:{context}:{product['product_code']}:{page}"
                        )
                    )
            if row:
                keyboard.append(row)

        # Navigation row (always 3 buttons)
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin:product:list:{page-1}:{context}"))
        else:
            nav_row.append(InlineKeyboardButton(" ", callback_data="noop"))

        if context == "view":
            nav_row.append(InlineKeyboardButton("🏠 Menu", callback_data="admin:menu:products"))
        else:
            nav_row.append(InlineKeyboardButton("❌ Cancel", callback_data="admin:menu:products"))

        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"admin:product:list:{page+1}:{context}"))
        else:
            nav_row.append(InlineKeyboardButton(" ", callback_data="noop"))

        keyboard.append(nav_row)

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def stock_list(
        stock_items: List[Dict],
        product_code: str,
        page: int = 1,
        items_per_page: int = 6
    ) -> InlineKeyboardMarkup:
        """Stock list with numbered buttons (3 columns)."""
        total_pages = max(1, math.ceil(len(stock_items) / items_per_page))
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = stock_items[start_idx:end_idx]

        keyboard = []

        # Number buttons - 3 per row
        for i in range(0, len(page_items), 3):
            row = []
            for j in range(3):
                idx = i + j
                if idx < len(page_items):
                    item = page_items[idx]
                    row.append(
                        InlineKeyboardButton(
                            AdminKeyboards.NUMBER_EMOJIS[idx],
                            callback_data=f"admin:stock:view:{item['id']}:{page}"
                        )
                    )
            if row:
                keyboard.append(row)

        # Navigation row
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"admin:stock:list:{product_code}:{page-1}"))
        else:
            nav_row.append(InlineKeyboardButton(" ", callback_data="noop"))

        nav_row.append(InlineKeyboardButton("🔙 Back", callback_data=f"admin:product:view:{product_code}:1"))

        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"admin:stock:list:{product_code}:{page+1}"))
        else:
            nav_row.append(InlineKeyboardButton(" ", callback_data="noop"))

        keyboard.append(nav_row)

        return InlineKeyboardMarkup(keyboard)

    # ==================== Detail View Keyboards ====================

    @staticmethod
    def product_detail(product_code: str, has_stock: bool = True) -> InlineKeyboardMarkup:
        """Product detail actions - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Stock", callback_data=f"admin:stock:add:{product_code}"),
                InlineKeyboardButton("✏️ Edit", callback_data=f"admin:product:edit:{product_code}"),
                InlineKeyboardButton("📊 Details", callback_data=f"admin:product:details:{product_code}")
            ],
            [
                InlineKeyboardButton("🗑️ Delete", callback_data=f"admin:product:delete:{product_code}"),
                InlineKeyboardButton("🔄 Toggle", callback_data=f"admin:product:toggle:{product_code}"),
                InlineKeyboardButton("📋 Stock List", callback_data=f"admin:stock:list:{product_code}:1")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="admin:product:list:1:view"),
                InlineKeyboardButton("🏠 Menu", callback_data="admin:menu:products"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help:product")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def stock_detail(stock_id: int, product_code: str) -> InlineKeyboardMarkup:
        """Stock item detail actions - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit", callback_data=f"admin:stock:edit:{stock_id}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"admin:stock:delete:{stock_id}"),
                InlineKeyboardButton("📋 Copy", callback_data=f"admin:stock:copy:{stock_id}")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data=f"admin:stock:list:{product_code}:1"),
                InlineKeyboardButton("🏠 Menu", callback_data="admin:menu:stock"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help:stock")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== Confirmation Keyboards ====================

    @staticmethod
    def confirmation(
        action: str,
        item_id: str,
        cancel_callback: str = "admin:dashboard"
    ) -> InlineKeyboardMarkup:
        """Simple confirmation keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"admin:confirm:{action}:{item_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=cancel_callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirmation_two_step(
        action: str,
        item_id: str,
        item_name: str = ""
    ) -> InlineKeyboardMarkup:
        """
        Two-step confirmation for critical actions.
        First shows warning, then requires typing confirmation.
        """
        keyboard = [
            [InlineKeyboardButton(
                f"⚠️ Confirm {action.title()}",
                callback_data=f"admin:confirm:step2:{action}:{item_id}"
            )],
            [
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin:cancel:{action}"),
                InlineKeyboardButton("ℹ️ Info", callback_data=f"admin:info:{action}:{item_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def bulk_preview(
        action: str,
        total: int,
        valid: int,
        invalid: int
    ) -> InlineKeyboardMarkup:
        """Bulk operation preview confirmation - 3 columns."""
        keyboard = [
            [
                InlineKeyboardButton(f"📥 Import All ({valid})", callback_data=f"admin:bulk:confirm:{action}"),
                InlineKeyboardButton(f"📋 Review Errors ({invalid})", callback_data=f"admin:bulk:errors:{action}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin:bulk:cancel:{action}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== Wizard Keyboards ====================

    @staticmethod
    def wizard_confirm_cancel() -> InlineKeyboardMarkup:
        """Simple confirm/cancel for wizards."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data="admin:wizard:confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin:wizard:cancel")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def wizard_navigation(
        back_callback: str = None,
        next_callback: str = None,
        cancel: bool = True
    ) -> InlineKeyboardMarkup:
        """Wizard navigation with back/next/cancel."""
        row = []

        if back_callback:
            row.append(InlineKeyboardButton("◀️ Back", callback_data=back_callback))

        if cancel:
            row.append(InlineKeyboardButton("❌ Cancel", callback_data="admin:wizard:cancel"))

        if next_callback:
            row.append(InlineKeyboardButton("Next ▶️", callback_data=next_callback))

        return InlineKeyboardMarkup([row])

    # ==================== Reply Keyboard (Quick Actions) ====================

    @staticmethod
    def admin_reply_keyboard() -> ReplyKeyboardMarkup:
        """
        Admin reply keyboard - always visible quick actions.

        Layout (2x3):
        [📦 +Stock] [📊 Stats] [🔧 Logs]
        [💰 Trans]  [📢 BC]    [🏠 Menu]
        """
        keyboard = [
            [
                KeyboardButton(f"📦 {uf.sans('+Stock')}"),
                KeyboardButton(f"📊 {uf.sans('Stats')}"),
                KeyboardButton(f"🔧 {uf.sans('Logs')}")
            ],
            [
                KeyboardButton(f"💰 {uf.sans('Trans')}"),
                KeyboardButton(f"📢 {uf.sans('BC')}"),
                KeyboardButton(f"🏠 {uf.sans('Menu')}")
            ]
        ]
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Admin Quick Actions"
        )

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
                InlineKeyboardButton("❌ Cancel", callback_data="admin:dashboard"),
                InlineKeyboardButton("🏠 Home", callback_data="nav:main"),
                InlineKeyboardButton("❓ Help", callback_data="admin:help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ==================== After Action Keyboards ====================

    @staticmethod
    def after_stock_added(product_code: str) -> InlineKeyboardMarkup:
        """Options after successfully adding stock."""
        keyboard = [
            [
                InlineKeyboardButton("➕ Add More", callback_data=f"admin:stock:add:{product_code}"),
                InlineKeyboardButton("📋 View Stock", callback_data=f"admin:stock:list:{product_code}:1"),
                InlineKeyboardButton("🏠 Dashboard", callback_data="admin:dashboard")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def after_product_added(product_code: str) -> InlineKeyboardMarkup:
        """Options after successfully adding product."""
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Stock", callback_data=f"admin:stock:add:{product_code}"),
                InlineKeyboardButton("📋 View Details", callback_data=f"admin:product:view:{product_code}:1"),
                InlineKeyboardButton("🏠 Dashboard", callback_data="admin:dashboard")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
