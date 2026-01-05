"""Validate message outputs for visual consistency."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime


def validate_message_outputs():
    """Test actual message outputs."""
    issues = []

    try:
        from utils.message_templates import MessageTemplates as msg

        print("Testing message outputs...\n")

        # Test 1: Welcome message length
        welcome = msg.welcome("John Doe", "FRIENDS Store")
        if len(welcome) > 4096:
            issues.append(f"Welcome message too long: {len(welcome)} chars (max 4096)")
        print(f"  ✓ Welcome message: {len(welcome)} chars")

        # Test 2: Product card length
        product = {
            'name': 'Test Product with a Very Long Name That Should Still Fit',
            'description': 'A' * 200,
            'price': 50000
        }
        card = msg.product_card(product, stock_count=10)
        if len(card) > 4096:
            issues.append(f"Product card too long: {len(card)} chars")
        print(f"  ✓ Product card: {len(card)} chars")

        # Test 3: Product list with many products
        products = [{'name': f'Product {i}', 'price': 50000, 'stock_count': 10} for i in range(20)]
        plist = msg.product_list(products, page=1, total_pages=3)
        if len(plist) > 4096:
            issues.append(f"Product list too long: {len(plist)} chars")
        print(f"  ✓ Product list (20 items): {len(plist)} chars")

        # Test 4: Transaction list
        transactions = [
            {
                'product_name': f'Product {i}',
                'amount': 50000,
                'status': 'PAID',
                'created_at': datetime.now()
            }
            for i in range(10)
        ]
        tlist = msg.transaction_list(transactions)
        if len(tlist) > 4096:
            issues.append(f"Transaction list too long: {len(tlist)} chars")
        print(f"  ✓ Transaction list (10 items): {len(tlist)} chars")

        # Test 5: Admin dashboard
        stats = {
            'total_users': 1234567,
            'active_today': 12345,
            'total_transactions': 123456,
            'total_revenue': 1234567890,
            'total_products': 123,
            'low_stock_count': 12
        }
        dashboard = msg.admin_dashboard(stats)
        if len(dashboard) > 4096:
            issues.append(f"Admin dashboard too long: {len(dashboard)} chars")
        print(f"  ✓ Admin dashboard: {len(dashboard)} chars")

        # Test 6: Check for broken Unicode
        test_messages = [welcome, card, plist, tlist, dashboard]
        for idx, msg_text in enumerate(test_messages, 1):
            try:
                msg_text.encode('utf-8')
            except UnicodeEncodeError:
                issues.append(f"Message {idx} contains invalid Unicode characters")

        print("  ✓ All Unicode valid")

        if not issues:
            print("\n✅ All message output tests passed")

    except Exception as e:
        issues.append(f"Error during testing: {e}")

    return issues


if __name__ == "__main__":
    print("🔍 Validating message outputs...")
    print("=" * 50)

    issues = validate_message_outputs()

    if issues:
        print("\n❌ VALIDATION FAILED\n")
        for issue in issues:
            print(f"  • {issue}")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        print("All message outputs are within limits!")
        sys.exit(0)
