"""
Admin UI handlers package.
"""

from handlers.admin.ui.dashboard import dashboard_handlers
from handlers.admin.ui.stock_ui import stock_ui_handlers
from handlers.admin.ui.system_ui import system_ui_handlers
from handlers.admin.ui.transaction_ui import transaction_ui_handlers
from handlers.admin.ui.product_ui import product_ui_handlers
from handlers.admin.ui.user_ui import user_ui_handlers
from handlers.admin.ui.confirmation import confirmation_handlers

__all__ = [
    "dashboard_handlers",
    "stock_ui_handlers",
    "system_ui_handlers",
    "transaction_ui_handlers",
    "product_ui_handlers",
    "user_ui_handlers",
    "confirmation_handlers",
]

# Combined handlers list for easy registration
# Order matters: confirmation handlers should be last
all_admin_ui_handlers = (
    dashboard_handlers +
    stock_ui_handlers +
    system_ui_handlers +
    transaction_ui_handlers +
    product_ui_handlers +
    user_ui_handlers +
    confirmation_handlers
)
