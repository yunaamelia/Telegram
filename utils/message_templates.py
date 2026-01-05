"""
Professional message templates using the visual system.
"""

from typing import Dict, List, Optional
from datetime import datetime
from utils.visual_system import VisualSystem as vs
from utils.unicode_fonts import UnicodeFonts as uf
from utils.formatters import format_currency, format_datetime


class MessageTemplates:
    """Pre-built message templates for common scenarios."""

    # ==================== WELCOME & ONBOARDING ====================

    @staticmethod
    def welcome(user_name: str, store_name: str) -> str:
        """Enhanced welcome message."""
        return f"""{vs.header(f'{store_name}', 'Premium Digital Products', icon='🛍️')}

{uf.small_caps('Halo')}, {uf.bold(user_name)}! 👋

Selamat datang di platform premium digital terpercaya!

{vs.ICONS['sparkles']} {uf.bold('Mengapa Memilih Kami?')}

{vs.tag('Premium Quality', 'success')}
{vs.tag('Instant Delivery', 'success')}
{vs.tag('24/7 Support', 'success')}
{vs.tag('Secure Payment', 'success')}

{vs.alert('Dapatkan 10% OFF untuk pembelian pertama!', 'info', 'Special Offer')}

{uf.italic('Tap menu di bawah untuk mulai berbelanja →')}"""

    @staticmethod
    def quick_tour() -> str:
        """Quick tour for new users."""
        return f"""{vs.header('Quick Tour', 'Learn the basics in 30 seconds', icon='🎯')}

{vs.list_item(1, 'Browse Products', 'Lihat katalog lengkap kami', badge=vs.BADGES['new'])}
{vs.list_item(2, 'Select & Pay', 'Pilih produk, bayar via QRIS')}
{vs.list_item(3, 'Get Instantly', 'Terima akun langsung di chat')}

{vs.DIVIDERS['dotted']}
{uf.italic('Sudah siap? Mulai belanja sekarang!')}"""

    # ==================== PRODUCT DISPLAY ====================

    @staticmethod
    def product_card(
        product: Dict,
        stock_count: int,
        views: Optional[int] = None,
        rating: Optional[float] = None,
        reviews_count: Optional[int] = None
    ) -> str:
        """Enhanced product card with rich information."""
        # Status indicator
        if stock_count > 10:
            stock_status = vs.tag('In Stock', 'success')
        elif stock_count > 0:
            stock_status = vs.tag(f'Only {stock_count} left!', 'warning')
        else:
            stock_status = vs.tag('Out of Stock', 'error')

        # Badges
        badges = []
        if product.get('is_bestseller'):
            badges.append(vs.BADGES['bestseller'])
        if product.get('is_new'):
            badges.append(vs.BADGES['new'])
        if product.get('discount'):
            badges.append(vs.BADGES['sale'])

        badge_str = ' '.join(badges) if badges else ''

        # Build card
        card = f"""{vs.DIVIDERS['medium']}
{vs.ICONS['product']} {uf.bold(product['name'])} {badge_str}
{vs.DIVIDERS['light']}

{product.get('description', 'Premium digital product')}

"""

        # Pricing
        if product.get('discount_price'):
            card += vs.pricing(
                product['price'],
                product['discount_price'],
                product.get('discount_percent')
            )
        else:
            card += vs.pricing(product['price'])

        card += "\n\n"

        # Stats row
        stats = []
        if rating:
            stars = '⭐' * int(rating)
            stats.append(f"{stars} {rating}/5")
        if reviews_count:
            stats.append(f"{reviews_count} reviews")
        if views:
            stats.append(f"{vs.ICONS['view']} {views} views")

        if stats:
            card += f"{uf.italic(' • '.join(stats))}\n\n"

        # Stock status
        card += f"{stock_status}\n"
        card += vs.DIVIDERS['medium']

        return card

    @staticmethod
    def product_list(products: List[Dict], page: int = 1, total_pages: int = 1) -> str:
        """Enhanced product list."""
        header = vs.header(
            'Katalog Produk',
            f'Halaman {page}/{total_pages}',
            icon=vs.ICONS['product']
        )

        if not products:
            empty = vs.empty_state(
                icon='📦',
                title='Belum Ada Produk',
                description='Produk akan segera hadir. Stay tuned!',
                action_text='[🔔 Notify Me]'
            )
            return f"{header}\n\n{empty}"

        items = []
        for idx, product in enumerate(products, 1):
            stock = product.get('stock_count', 0)
            status = '✅' if stock > 5 else '⚠️' if stock > 0 else '❌'

            badge = ''
            if product.get('is_bestseller'):
                badge = vs.BADGES['bestseller']
            elif product.get('is_new'):
                badge = vs.BADGES['new']

            item = vs.list_item(
                number=idx,
                title=product['name'],
                price=format_currency(product['price']),
                status=f"{status} {stock} stok",
                badge=badge
            )
            items.append(item)

        return f"{header}\n\n" + "\n".join(items)

    # ==================== PAYMENT & CHECKOUT ====================

    @staticmethod
    def payment_summary(
        product_name: str,
        price: int,
        discount: Optional[int] = None,
        voucher_code: Optional[str] = None
    ) -> str:
        """Payment summary before checkout."""
        total = price - (discount or 0)

        summary = f"""{vs.header('Payment Summary', icon=vs.ICONS['card'])}

{vs.ICONS['product']} {uf.bold('Product')}
{product_name}

{vs.ICONS['money']} {uf.bold('Price Details')}
"""

        summary += f"{'Subtotal:'.ljust(20)} {format_currency(price)}\n"

        if discount:
            summary += f"{'Discount:'.ljust(20)} {uf.bold('-' + format_currency(discount))}\n"
            if voucher_code:
                summary += f"{uf.italic(f'  (Code: {voucher_code})')}\n"

        summary += f"{vs.DIVIDERS['light']}\n"
        summary += f"{'TOTAL:'.ljust(20)} {uf.bold(format_currency(total))}\n"
        summary += vs.DIVIDERS['medium']

        return summary

    @staticmethod
    def payment_pending(
        order_id: str,
        product_name: str,
        amount: int,
        expired_at: datetime
    ) -> str:
        """Payment pending with QRIS."""
        return f"""{vs.header('Pembayaran QRIS', icon=vs.ICONS['card'])}

{vs.list_item(1, 'Scan QR Code', 'Gunakan aplikasi e-wallet favorit')}
{vs.list_item(2, 'Confirm Payment', 'Pembayaran akan terverifikasi otomatis')}
{vs.list_item(3, 'Get Account', 'Terima detail akun via chat')}

{vs.DIVIDERS['medium']}
{vs.ICONS['product']} {uf.bold('Product')}: {product_name}
{vs.ICONS['money']} {uf.bold('Amount')}: {uf.monospace(format_currency(amount))}
{vs.ICONS['key']} {uf.bold('Order ID')}: {uf.monospace(order_id)}
{vs.ICONS['clock']} {uf.bold('Expires')}: {uf.monospace(format_datetime(expired_at))}
{vs.DIVIDERS['medium']}

{vs.alert('Pembayaran otomatis dibatalkan jika melewati batas waktu.', 'warning', 'Perhatian')}

{uf.italic('Supported: GoPay • OVO • Dana • ShopeePay • LinkAja')}"""

    @staticmethod
    def payment_success(
        order_id: str,
        product_name: str,
        amount: int,
        account_details: Dict,
        paid_at: datetime
    ) -> str:
        """Payment success with account delivery."""
        result = f"""{vs.header('Pembayaran Berhasil!', icon='🎉')}

{vs.alert('Terima kasih atas pembelian Anda!', 'success', 'Success')}

{vs.DIVIDERS['medium']}
📦 {uf.bold('Order Details')}
{vs.DIVIDERS['light']}

{vs.stat_row('Order ID', order_id)}
{vs.stat_row('Product', product_name)}
{vs.stat_row('Amount', format_currency(amount), vs.ICONS['money'])}
{vs.stat_row('Date', format_datetime(paid_at), vs.ICONS['calendar'])}

{vs.DIVIDERS['medium']}
🔑 {uf.bold('Account Details')}
{vs.DIVIDERS['light']}

{vs.ICONS['email']} {uf.bold('Email')}
{uf.monospace(account_details['email'])}

{vs.ICONS['lock']} {uf.bold('Password')}
{uf.monospace(account_details['password'])}"""

        if account_details.get('two_fa_secret'):
            result += f"""

{vs.ICONS['key']} {uf.bold('2FA Secret')}
{uf.monospace(account_details['two_fa_secret'])}"""

        if account_details.get('notes'):
            result += f"""

{vs.ICONS['info']} {uf.bold('Notes')}
{account_details['notes']}"""

        result += f"""

{vs.DIVIDERS['medium']}

{vs.alert('Simpan informasi ini dengan aman! Jangan bagikan ke siapapun.', 'warning', 'PENTING')}

{uf.italic('Butuh bantuan? Hubungi support 24/7')}"""

        return result

    # ==================== TRANSACTION HISTORY ====================

    @staticmethod
    def transaction_list(transactions: List[Dict]) -> str:
        """Enhanced transaction history."""
        header = vs.header('Riwayat Transaksi', icon=vs.ICONS['calendar'])

        if not transactions:
            empty = vs.empty_state(
                icon=vs.ICONS['cart'],
                title='Belum Ada Transaksi',
                description='Transaksi Anda akan muncul di sini',
                action_text='[🛒 Mulai Belanja]'
            )
            return f"{header}\n\n{empty}"

        status_styles = {
            'PAID': 'success',
            'UNPAID': 'warning',
            'EXPIRED': 'error',
            'CANCELLED': 'error',
            'REFUND_REQUESTED': 'warning',
            'REFUNDED': 'info'
        }

        items = []
        for idx, trx in enumerate(transactions, 1):
            style = status_styles.get(trx['status'], 'default')
            status_tag = vs.tag(trx['status'], style)

            item = vs.list_item(
                number=idx,
                title=trx.get('product_name', 'Product'),
                subtitle=format_datetime(trx.get('created_at')),
                price=format_currency(trx['amount']),
                status=status_tag
            )
            items.append(item)

        return f"{header}\n\n" + "\n".join(items)

    # ==================== ADMIN DASHBOARD ====================

    @staticmethod
    def admin_dashboard(stats: Dict) -> str:
        """Enhanced admin dashboard."""
        return f"""{vs.header('Admin Dashboard', 'Real-time Statistics', icon=vs.ICONS['lock'])}

{vs.ICONS['stats']} {uf.bold('Overview')}
{vs.DIVIDERS['light']}

{vs.stat_row('Total Users', str(stats.get('total_users', 0)), vs.ICONS['users'])}
{vs.stat_row('Active Today', str(stats.get('active_today', 0)), vs.INDICATORS['green'])}
{vs.stat_row('Transactions', str(stats.get('total_transactions', 0)), vs.ICONS['money'])}
{vs.stat_row('Revenue', format_currency(stats.get('total_revenue', 0)), vs.ICONS['chart'])}
{vs.stat_row('Products', str(stats.get('total_products', 0)), vs.ICONS['product'])}
{vs.stat_row('Low Stock', str(stats.get('low_stock_count', 0)), vs.ICONS['warning'])}

{vs.DIVIDERS['medium']}
{uf.italic('Select category below to manage →')}"""

    @staticmethod
    def stock_summary(products: List[Dict]) -> str:
        """Enhanced stock summary."""
        header = vs.header('Stock Summary', icon=vs.ICONS['product'])

        if not products:
            return f"{header}\n\n{vs.empty_state(vs.ICONS['product'], 'No Products', 'Add products first')}"

        items = []
        for product in products:
            available = product.get('available', 0)
            total = product.get('total', 0)

            # Progress bar for stock level
            percentage = int((available / total * 100)) if total > 0 else 0
            progress = vs.progress_bar(percentage)

            # Status indicator
            if available == 0:
                indicator = vs.INDICATORS['red']
            elif available < 5:
                indicator = vs.INDICATORS['yellow']
            else:
                indicator = vs.INDICATORS['green']

            item = f"""{uf.bold(product['name'])} {indicator}
{progress}
{vs.stat_row('Available', f"{available}/{total}")}
{vs.stat_row('Price', format_currency(product['price']))}
"""
            items.append(item)

        return f"{header}\n\n" + "\n".join(items)

    # ==================== ERROR STATES ====================

    @staticmethod
    def error(message: str, action: Optional[str] = None) -> str:
        """User-friendly error message."""
        error_msg = vs.alert(message, 'error', 'Oops!')

        if action:
            error_msg += f"\n\n{uf.italic(f'💡 {action}')}"

        return error_msg

    @staticmethod
    def maintenance() -> str:
        """Maintenance mode message."""
        return f"""{vs.ICONS['settings']} {uf.bold('Under Maintenance')}

{uf.italic('We are currently upgrading our system to serve you better.')}

{vs.ICONS['clock']} Estimated time: 30 minutes

{uf.italic('Thank you for your patience! 🙏')}"""

    @staticmethod
    def not_found(item_type: str = "Item") -> str:
        """Item not found message."""
        return vs.empty_state(
            icon='🔍',
            title=f'{item_type} Not Found',
            description=f'The {item_type.lower()} you are looking for does not exist.',
            action_text='[🔙 Go Back]'
        )

    @staticmethod
    def access_denied() -> str:
        """Access denied message."""
        return vs.alert(
            'You do not have permission to access this feature.',
            'error',
            'Access Denied'
        )


# Shorthand alias
msg = MessageTemplates
