"""Admin handlers package initialization."""

from handlers.admin.stock import stock_handlers
from handlers.admin.products import product_handlers
from handlers.admin.transactions import transaction_handlers
from handlers.admin.broadcast import broadcast_handlers
from handlers.admin.admin_mgmt import admin_mgmt_handlers
from handlers.admin.system import system_handlers
from handlers.admin.security import security_handlers

__all__ = [
    "stock_handlers",
    "product_handlers",
    "transaction_handlers",
    "broadcast_handlers",
    "admin_mgmt_handlers",
    "system_handlers",
    "security_handlers"
]
