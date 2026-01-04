"""
Admin UI handlers package.
"""

from handlers.admin.ui.dashboard import dashboard_handlers
from handlers.admin.ui.stock_ui import stock_ui_handlers
from handlers.admin.ui.system_ui import system_ui_handlers
from handlers.admin.ui.transaction_ui import transaction_ui_handlers

__all__ = [
    "dashboard_handlers",
    "stock_ui_handlers",
    "system_ui_handlers",
    "transaction_ui_handlers",
]

# Combined handlers list for easy registration
all_admin_ui_handlers = (
    dashboard_handlers +
    stock_ui_handlers +
    system_ui_handlers +
    transaction_ui_handlers
)
