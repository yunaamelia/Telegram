"""Validate Message Templates implementation."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime


def validate_message_templates():
    """Validate MessageTemplates class."""
    issues = []

    try:
        from utils.message_templates import MessageTemplates as msg

        # Check required methods
        required_methods = [
            'welcome', 'quick_tour', 'product_card', 'product_list',
            'payment_summary', 'payment_pending', 'payment_success',
            'transaction_list', 'admin_dashboard', 'stock_summary',
            'error', 'maintenance'
        ]

        for method in required_methods:
            if not hasattr(msg, method):
                issues.append(f"Missing required method: {method}")

        print("Testing templates...")

        # Test welcome
        welcome = msg.welcome("John Doe", "FRIENDS Store")
        if not isinstance(welcome, str):
            issues.append("welcome() should return string")

        # Test quick_tour
        tour = msg.quick_tour()
        if not isinstance(tour, str):
            issues.append("quick_tour() should return string")

        # Test product_card
        product = {
            'name': 'Test Product',
            'description': 'Test description',
            'price': 50000
        }
        card = msg.product_card(product, stock_count=10)
        if not isinstance(card, str):
            issues.append("product_card() should return string")

        # Test product_list
        products = [
            {'name': 'Product 1', 'price': 50000, 'stock_count': 10},
            {'name': 'Product 2', 'price': 35000, 'stock_count': 5}
        ]
        plist = msg.product_list(products, page=1, total_pages=2)
        if not isinstance(plist, str):
            issues.append("product_list() should return string")

        # Test product_list empty state
        empty_list = msg.product_list([], page=1, total_pages=1)
        if not isinstance(empty_list, str):
            issues.append("product_list() empty state should return string")

        # Test payment_summary
        summary = msg.payment_summary("Test Product", 50000, discount=5000, voucher_code="SAVE10")
        if not isinstance(summary, str):
            issues.append("payment_summary() should return string")

        # Test payment_pending
        pending = msg.payment_pending("ORD123", "Test Product", 50000, datetime.now())
        if not isinstance(pending, str):
            issues.append("payment_pending() should return string")

        # Test payment_success
        account = {
            'email': 'test@example.com',
            'password': 'pass123',
            'two_fa_secret': '2FASECRET',
            'notes': 'Test notes'
        }
        success = msg.payment_success("ORD123", "Test Product", 50000, account, datetime.now())
        if not isinstance(success, str):
            issues.append("payment_success() should return string")

        # Test transaction_list
        transactions = [
            {'product_name': 'Product 1', 'amount': 50000, 'status': 'PAID', 'created_at': datetime.now()},
            {'product_name': 'Product 2', 'amount': 35000, 'status': 'UNPAID', 'created_at': datetime.now()}
        ]
        tlist = msg.transaction_list(transactions)
        if not isinstance(tlist, str):
            issues.append("transaction_list() should return string")

        # Test transaction_list empty state
        empty_tlist = msg.transaction_list([])
        if not isinstance(empty_tlist, str):
            issues.append("transaction_list() empty state should return string")

        # Test admin_dashboard
        stats = {
            'total_users': 100,
            'active_today': 50,
            'total_transactions': 200,
            'total_revenue': 10000000,
            'total_products': 15,
            'low_stock_count': 3
        }
        dashboard = msg.admin_dashboard(stats)
        if not isinstance(dashboard, str):
            issues.append("admin_dashboard() should return string")

        # Test stock_summary
        stock_products = [
            {'name': 'Product 1', 'available': 10, 'total': 20, 'price': 50000},
            {'name': 'Product 2', 'available': 0, 'total': 10, 'price': 35000}
        ]
        stock = msg.stock_summary(stock_products)
        if not isinstance(stock, str):
            issues.append("stock_summary() should return string")

        # Test error
        error = msg.error("Something went wrong", action="Try again")
        if not isinstance(error, str):
            issues.append("error() should return string")

        # Test maintenance
        maint = msg.maintenance()
        if not isinstance(maint, str):
            issues.append("maintenance() should return string")

        if not issues:
            print("✅ All template tests passed")

    except ImportError as e:
        issues.append(f"Failed to import MessageTemplates: {e}")
    except Exception as e:
        issues.append(f"Unexpected error: {e}")

    return issues


if __name__ == "__main__":
    print("🔍 Validating Message Templates...")
    print("=" * 50)

    issues = validate_message_templates()

    if issues:
        print("\n❌ VALIDATION FAILED\n")
        for issue in issues:
            print(f"  • {issue}")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        print("Message Templates are correctly implemented!")
        sys.exit(0)
