"""Generate visual preview of all templates for manual inspection."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime


def generate_preview():
    """Generate preview file with all templates."""
    from utils.message_templates import MessageTemplates as msg
    from utils.visual_system import VisualSystem as vs

    preview = []

    preview.append("=" * 60)
    preview.append("UI/UX VISUAL PREVIEW")
    preview.append("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    preview.append("=" * 60)
    preview.append("\n\n")

    # Welcome
    preview.append("--- WELCOME MESSAGE ---\n")
    preview.append(msg.welcome("John Doe", "FRIENDS Store"))
    preview.append("\n\n")

    # Quick Tour
    preview.append("--- QUICK TOUR ---\n")
    preview.append(msg.quick_tour())
    preview.append("\n\n")

    # Product Card
    preview.append("--- PRODUCT CARD ---\n")
    product = {
        'name': 'GitHub Student Fresh',
        'description': 'Perfect for students and developers.',
        'price': 50000,
        'is_bestseller': True,
        'is_new': False
    }
    preview.append(msg.product_card(product, stock_count=15, views=245, rating=4.8, reviews_count=67))
    preview.append("\n\n")

    # Product List
    preview.append("--- PRODUCT LIST ---\n")
    products = [
        {'name': 'GitHub Student Fresh', 'price': 50000, 'stock_count': 15, 'is_bestseller': True},
        {'name': 'Netflix Premium 1 Month', 'price': 35000, 'stock_count': 8, 'is_new': True},
        {'name': 'Spotify Premium Family', 'price': 25000, 'stock_count': 0}
    ]
    preview.append(msg.product_list(products, page=1, total_pages=2))
    preview.append("\n\n")

    # Empty Product List
    preview.append("--- EMPTY PRODUCT LIST ---\n")
    preview.append(msg.product_list([], page=1, total_pages=1))
    preview.append("\n\n")

    # Payment Summary
    preview.append("--- PAYMENT SUMMARY ---\n")
    preview.append(msg.payment_summary("GitHub Student Fresh", 50000, discount=5000, voucher_code="SAVE10"))
    preview.append("\n\n")

    # Payment Pending
    preview.append("--- PAYMENT PENDING ---\n")
    preview.append(msg.payment_pending("FRIENDS-20240105-ABC123", "GitHub Student Fresh", 45000, datetime.now()))
    preview.append("\n\n")

    # Payment Success
    preview.append("--- PAYMENT SUCCESS ---\n")
    account = {
        'email': 'user@example.com',
        'password': 'SecurePass123',
        'two_fa_secret': 'JBSWY3DPEHPK3PXP',
        'notes': 'Valid until December 2026'
    }
    preview.append(msg.payment_success("FRIENDS-20240105-ABC123", "GitHub Student Fresh", 45000, account, datetime.now()))
    preview.append("\n\n")

    # Transaction List
    preview.append("--- TRANSACTION LIST ---\n")
    transactions = [
        {'product_name': 'GitHub Student', 'amount': 50000, 'status': 'PAID', 'created_at': datetime.now()},
        {'product_name': 'Netflix Premium', 'amount': 35000, 'status': 'UNPAID', 'created_at': datetime.now()},
        {'product_name': 'Spotify Family', 'amount': 25000, 'status': 'EXPIRED', 'created_at': datetime.now()}
    ]
    preview.append(msg.transaction_list(transactions))
    preview.append("\n\n")

    # Admin Dashboard
    preview.append("--- ADMIN DASHBOARD ---\n")
    stats = {
        'total_users': 1247,
        'active_today': 423,
        'total_transactions': 3456,
        'total_revenue': 125500000,
        'total_products': 15,
        'low_stock_count': 3
    }
    preview.append(msg.admin_dashboard(stats))
    preview.append("\n\n")

    # Stock Summary
    preview.append("--- STOCK SUMMARY ---\n")
    stock_products = [
        {'name': 'GitHub Student', 'available': 15, 'total': 20, 'price': 50000},
        {'name': 'Netflix Premium', 'available': 2, 'total': 10, 'price': 35000},
        {'name': 'Spotify Family', 'available': 0, 'total': 10, 'price': 25000}
    ]
    preview.append(msg.stock_summary(stock_products))
    preview.append("\n\n")

    # Error Message
    preview.append("--- ERROR MESSAGE ---\n")
    preview.append(msg.error("Payment processing failed.", "Contact support if problem persists"))
    preview.append("\n\n")

    # Maintenance
    preview.append("--- MAINTENANCE MESSAGE ---\n")
    preview.append(msg.maintenance())
    preview.append("\n\n")

    # Visual System Components
    preview.append("=" * 60)
    preview.append("VISUAL SYSTEM COMPONENTS")
    preview.append("=" * 60)
    preview.append("\n\n")

    preview.append("--- PROGRESS BARS ---\n")
    for pct in [0, 25, 50, 75, 100]:
        preview.append(vs.progress_bar(pct, width=10))
        preview.append("\n")
    preview.append("\n")

    preview.append("--- TAGS ---\n")
    for style in ['default', 'success', 'warning', 'error', 'info']:
        preview.append(vs.tag(f"{style.title()} Tag", style))
        preview.append("\n")
    preview.append("\n")

    preview.append("--- ALERTS ---\n")
    for alert_type in ['success', 'warning', 'error', 'info']:
        preview.append(vs.alert(f"This is a {alert_type} message", alert_type, alert_type.title()))
        preview.append("\n\n")

    # Save to file
    output_path = Path('reports/ui_visual_preview.txt')
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(preview))

    print(f"✅ Visual preview generated: {output_path}")
    print(f"📄 Total length: {len(''.join(preview))} characters")

    return output_path


if __name__ == "__main__":
    print("🎨 Generating visual preview...")
    output_path = generate_preview()
    print(f"\n✅ Preview saved to: {output_path}")
    print("\n💡 Open the file to manually inspect all UI components")
