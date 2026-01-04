"""
Admin wizards package - Conversation handlers for step-by-step operations.
"""

from handlers.admin.wizards.stock_wizard import stock_wizard_handler, StockWizard
from handlers.admin.wizards.product_wizard import product_wizard_handler, ProductWizard

__all__ = [
    "stock_wizard_handler",
    "product_wizard_handler",
    "StockWizard",
    "ProductWizard",
]

# Combined list for easy registration
all_admin_wizards = [
    stock_wizard_handler,
    product_wizard_handler,
]
