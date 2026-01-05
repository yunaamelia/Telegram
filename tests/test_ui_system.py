"""
Test UI/UX visual system and message templates.
"""

import pytest
from utils.visual_system import VisualSystem as vs
from utils.unicode_fonts import UnicodeFonts as uf
from utils.message_templates import MessageTemplates as msg


class TestVisualSystem:
    """Test visual system components."""

    def test_header_basic(self):
        """Test basic header."""
        result = vs.header('Test Title')
        assert '𝐓𝐞𝐬𝐭' in result  # Bold text
        assert '━' in result  # Divider

    def test_header_with_subtitle(self):
        """Test header with subtitle."""
        result = vs.header('Title', 'Subtitle', icon='🔥')
        assert '🔥' in result
        assert '𝐓𝐢𝐭𝐥𝐞' in result

    def test_list_item(self):
        """Test list item formatting."""
        result = vs.list_item(
            number=1,
            title='Product Name',
            price='Rp 50.000',
            status='✅ In Stock'
        )
        assert '𝟏.' in result  # Bold number
        assert 'Product Name' in result
        assert '✅' in result

    def test_progress_bar(self):
        """Test progress bar."""
        result = vs.progress_bar(80)
        assert '█' in result
        assert '░' in result
        assert '80%' in result

    def test_progress_bar_zero(self):
        """Test progress bar at 0%."""
        result = vs.progress_bar(0)
        assert '░░░░░░░░░░' in result
        assert '0%' in result

    def test_progress_bar_full(self):
        """Test progress bar at 100%."""
        result = vs.progress_bar(100)
        assert '██████████' in result
        assert '100%' in result

    def test_tag_styles(self):
        """Test different tag styles."""
        success = vs.tag('Active', 'success')
        warning = vs.tag('Low', 'warning')
        error = vs.tag('Out', 'error')

        assert '🟢' in success
        assert '🟡' in warning
        assert '🔴' in error

    def test_alert_types(self):
        """Test alert types."""
        info = vs.alert('Info message', 'info')
        warning = vs.alert('Warning message', 'warning')
        error = vs.alert('Error message', 'error')
        success = vs.alert('Success message', 'success')

        assert 'ℹ️' in info
        assert '⚠️' in warning
        assert '❌' in error
        assert '✅' in success

    def test_empty_state(self):
        """Test empty state component."""
        result = vs.empty_state(
            icon='📦',
            title='No Products',
            description='Add your first product'
        )
        assert '📦' in result
        assert '𝐍𝐨' in result  # Bold "No"

    def test_stat_row(self):
        """Test stat row formatting."""
        result = vs.stat_row('Users', '1,247', '👥')
        assert '👥' in result
        assert '𝟏' in result  # Bold number

    def test_dividers(self):
        """Test divider constants."""
        assert len(vs.DIVIDERS['light']) == 20
        assert len(vs.DIVIDERS['medium']) == 20
        assert '─' in vs.DIVIDERS['light']
        assert '━' in vs.DIVIDERS['medium']

    def test_icons(self):
        """Test icon constants."""
        assert vs.ICONS['success'] == '✅'
        assert vs.ICONS['error'] == '❌'
        assert vs.ICONS['product'] == '📦'

    def test_badges(self):
        """Test badge constants."""
        assert vs.BADGES['new'] == '🆕'
        assert vs.BADGES['hot'] == '🔥'
        assert vs.BADGES['premium'] == '👑'


class TestMessageTemplates:
    """Test message templates."""

    def test_welcome_message(self):
        """Test welcome message."""
        result = msg.welcome('John', 'FRIENDS Store')
        assert '𝐉𝐨𝐡𝐧' in result  # Bold John
        assert '𝐅𝐑𝐈𝐄𝐍𝐃𝐒' in result  # Bold FRIENDS
        assert '👋' in result

    def test_quick_tour(self):
        """Test quick tour message."""
        result = msg.quick_tour()
        assert '🎯' in result
        assert 'Browse Products' in result  # Title contains Browse Products

    def test_product_card(self):
        """Test product card."""
        product = {
            'name': 'Netflix Premium',
            'description': 'Best streaming service',
            'price': 50000
        }
        result = msg.product_card(product, stock_count=10)
        assert '𝐍𝐞𝐭𝐟𝐥𝐢𝐱' in result  # Bold Netflix
        assert '𝟓𝟎' in result  # Bold 50

    def test_product_card_low_stock(self):
        """Test product card with low stock."""
        product = {'name': 'Test', 'price': 10000}
        result = msg.product_card(product, stock_count=3)
        assert 'Only 3 left' in result or '🟡' in result

    def test_product_card_out_of_stock(self):
        """Test product card out of stock."""
        product = {'name': 'Test', 'price': 10000}
        result = msg.product_card(product, stock_count=0)
        assert 'Out of Stock' in result or '🔴' in result

    def test_product_list_empty(self):
        """Test empty product list."""
        result = msg.product_list([])
        assert '📦' in result

    def test_transaction_list_empty(self):
        """Test empty transaction list."""
        result = msg.transaction_list([])
        assert '🛒' in result  # Empty state icon

    def test_admin_dashboard(self):
        """Test admin dashboard."""
        stats = {
            'total_users': 100,
            'total_transactions': 50,
            'total_products': 10,
            'low_stock_count': 2
        }
        result = msg.admin_dashboard(stats)
        assert '𝟏𝟎𝟎' in result  # Bold 100
        assert '𝐃𝐚𝐬𝐡𝐛𝐨𝐚𝐫𝐝' in result  # Bold Dashboard

    def test_error_message(self):
        """Test error message."""
        result = msg.error('Something went wrong', 'Try again later')
        assert '❌' in result
        assert 'wrong' in result

    def test_maintenance_message(self):
        """Test maintenance message."""
        result = msg.maintenance()
        assert '⚙️' in result

    def test_not_found(self):
        """Test not found message."""
        result = msg.not_found('Product')
        assert '𝐏𝐫𝐨𝐝𝐮𝐜𝐭' in result  # Bold Product
        assert '🔍' in result

    def test_access_denied(self):
        """Test access denied message."""
        result = msg.access_denied()
        assert '❌' in result


class TestLoadingStates:
    """Test loading states."""

    def test_simple_loading(self):
        """Test simple loading text."""
        from utils.loading_states import loading

        result = loading.simple_loading('Fetching data')
        assert '⏳' in result
        assert 'Fetching data' in result

    def test_simple_processing(self):
        """Test simple processing text."""
        from utils.loading_states import loading

        result = loading.simple_processing('Updating')
        assert '🔄' in result
        assert 'Updating' in result

    def test_simple_saving(self):
        """Test simple saving text."""
        from utils.loading_states import loading

        result = loading.simple_saving('Changes')
        assert '💾' in result
        assert 'Changes' in result

    def test_loading_frames(self):
        """Test loading frames constant."""
        from utils.loading_states import LoadingStates

        assert len(LoadingStates.LOADING_FRAMES) >= 3
        assert '⏳' in LoadingStates.LOADING_FRAMES[0]
