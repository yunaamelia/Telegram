"""
Visual Design System for FRIENDS Store Telegram Bot.
Provides consistent UI components, spacing, colors (via emojis), and layouts.
"""

from typing import List, Optional
from utils.unicode_fonts import UnicodeFonts as uf


class VisualSystem:
    """Centralized visual design system."""

    # ==================== SPACING ====================
    SPACING = {
        'xs': '\n',           # 1 line
        'sm': '\n\n',         # 2 lines
        'md': '\n\n\n',       # 3 lines
        'lg': '\n\n\n\n',     # 4 lines
    }

    # ==================== DIVIDERS ====================
    DIVIDERS = {
        'light': '─' * 20,
        'medium': '━' * 20,
        'heavy': '═' * 20,
        'dotted': '·' * 20,
        'dashed': '- ' * 10,
    }

    # ==================== ICONS ====================
    ICONS = {
        # Status
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'pending': '⏳',

        # Actions
        'add': '➕',
        'edit': '✏️',
        'delete': '🗑️',
        'view': '👁️',
        'search': '🔍',
        'filter': '🔎',
        'settings': '⚙️',
        'refresh': '🔄',
        'download': '📥',
        'upload': '📤',

        # Navigation
        'home': '🏠',
        'back': '🔙',
        'next': '▶️',
        'prev': '◀️',
        'up': '🔼',
        'down': '🔽',
        'close': '❌',

        # Content
        'product': '📦',
        'cart': '🛒',
        'money': '💰',
        'card': '💳',
        'user': '👤',
        'users': '👥',
        'stats': '📊',
        'bell': '🔔',
        'star': '⭐',
        'heart': '❤️',
        'fire': '🔥',
        'gift': '🎁',
        'lock': '🔒',
        'unlock': '🔓',
        'key': '🔑',
        'email': '📧',
        'phone': '📱',
        'calendar': '📅',
        'clock': '🕐',
        'pin': '📌',
        'tag': '🏷️',
        'bookmark': '🔖',
        'flag': '🚩',
        'trophy': '🏆',
        'medal': '🏅',
        'crown': '👑',
        'sparkles': '✨',
        'rocket': '🚀',
        'chart': '📈',
        'target': '🎯',
    }

    # ==================== COLOR INDICATORS (via emojis) ====================
    INDICATORS = {
        'green': '🟢',
        'red': '🔴',
        'yellow': '🟡',
        'blue': '🔵',
        'purple': '🟣',
        'orange': '🟠',
        'black': '⚫',
        'white': '⚪',
    }

    # ==================== BADGES ====================
    BADGES = {
        'new': '🆕',
        'hot': '🔥',
        'sale': '💸',
        'premium': '👑',
        'verified': '✓',
        'bestseller': '⭐',
        'limited': '⏰',
        'exclusive': '💎',
    }

    # ==================== COMPONENT BUILDERS ====================

    @staticmethod
    def header(
        title: str,
        subtitle: Optional[str] = None,
        icon: Optional[str] = None,
        divider: bool = True
    ) -> str:
        """
        Create a styled header.

        Args:
            title: Main title text
            subtitle: Optional subtitle
            icon: Optional icon emoji
            divider: Show divider line

        Returns:
            Formatted header string
        """
        icon_str = f"{icon} " if icon else ""
        header_text = f"{icon_str}{uf.bold(title)}"

        if subtitle:
            header_text += f"\n{uf.italic(subtitle)}"

        if divider:
            header_text += f"\n{VisualSystem.DIVIDERS['medium']}"

        return header_text

    @staticmethod
    def card(
        title: str,
        content: str,
        footer: Optional[str] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None
    ) -> str:
        """
        Create a card-style component.

        Example:
        ┌──────────────────┐
        │ 🎁 Title   [NEW] │
        │ Content here...   │
        │ Footer info      │
        └──────────────────┘
        """
        top_border = "┌" + "─" * 18 + "┐"
        bottom_border = "└" + "─" * 18 + "┘"

        icon_str = f"{icon} " if icon else ""
        badge_str = f" {badge}" if badge else ""

        card_text = f"{top_border}\n"
        card_text += f"│ {icon_str}{uf.bold(title)}{badge_str}\n"
        card_text += f"│ {content}\n"

        if footer:
            card_text += f"│ {uf.italic(footer)}\n"

        card_text += bottom_border

        return card_text

    @staticmethod
    def list_item(
        number: int,
        title: str,
        subtitle: Optional[str] = None,
        price: Optional[str] = None,
        status: Optional[str] = None,
        badge: Optional[str] = None
    ) -> str:
        """
        Create a list item with consistent formatting.

        Example:
        1. Product Name [HOT]
           Rp 50,000 • ✅ In Stock
           Brief description...
        """
        badge_str = f" {badge}" if badge else ""
        item_text = f"{uf.bold(f'{number}.')} {title}{badge_str}\n"

        # Second line: price and status
        second_line = []
        if price:
            second_line.append(uf.monospace(price))
        if status:
            second_line.append(status)

        if second_line:
            item_text += f"   {' • '.join(second_line)}\n"

        # Third line: subtitle
        if subtitle:
            item_text += f"   {uf.italic(subtitle)}\n"

        return item_text

    @staticmethod
    def stat_row(label: str, value: str, icon: Optional[str] = None) -> str:
        """
        Create a statistics row.

        Example:
        👥 Users:         1,247
        """
        icon_str = f"{icon} " if icon else ""
        padded_label = f"{label}:".ljust(15)
        return f"{icon_str}{uf.monospace(padded_label)} {uf.bold(value)}"

    @staticmethod
    def progress_bar(percentage: int, width: int = 10) -> str:
        """
        Create a visual progress bar.

        Example:
        [████████░░] 80%
        """
        filled = int((percentage / 100) * width)
        empty = width - filled
        bar = '█' * filled + '░' * empty
        return f"[{bar}] {percentage}%"

    @staticmethod
    def tag(text: str, style: str = 'default') -> str:
        """
        Create a styled tag.

        Styles: default, success, warning, error, info
        """
        styles = {
            'default': ('⚪', ''),
            'success': ('🟢', ''),
            'warning': ('🟡', ''),
            'error': ('🔴', ''),
            'info': ('🔵', ''),
        }

        icon, _ = styles.get(style, styles['default'])
        return f"{icon} {uf.monospace(text)}"

    @staticmethod
    def alert(
        message: str,
        alert_type: str = 'info',
        title: Optional[str] = None
    ) -> str:
        """
        Create an alert box.

        Types: success, warning, error, info
        """
        icons = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'info': 'ℹ️',
        }

        icon = icons.get(alert_type, icons['info'])
        alert_text = f"{icon} {uf.bold(title or alert_type.upper())}\n"
        alert_text += f"{message}"

        return alert_text

    @staticmethod
    def loading(text: str = "Loading") -> str:
        """
        Create loading indicator.

        Example:
        ⏳ Loading...
        """
        return f"⏳ {uf.italic(text)}..."

    @staticmethod
    def empty_state(
        icon: str,
        title: str,
        description: str,
        action_text: Optional[str] = None
    ) -> str:
        """
        Create an empty state message.

        Example:
        📦
        No products yet
        Start by adding your first product
        [+ Add Product]
        """
        empty_text = f"{icon}\n"
        empty_text += f"{uf.bold(title)}\n"
        empty_text += f"{uf.italic(description)}"

        if action_text:
            empty_text += f"\n\n{action_text}"

        return empty_text

    @staticmethod
    def table(headers: List[str], rows: List[List[str]]) -> str:
        """
        Create a simple table.

        Example:
        Product    | Price   | Stock
        ───────────┼─────────┼──────
        Netflix    | Rp 35K  | ✅ 12
        Spotify    | Rp 25K  | ⚠️ 2
        """
        if not headers or not rows:
            return ""

        # Calculate column widths
        col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

        # Create header
        header_row = " │ ".join(
            str(headers[i]).ljust(col_widths[i])
            for i in range(len(headers))
        )

        # Create separator
        separator = "─" * (sum(col_widths) + len(headers) * 3 - 2)

        # Create rows
        table_rows = []
        for row in rows:
            table_row = " │ ".join(
                str(row[i]).ljust(col_widths[i])
                for i in range(len(row))
            )
            table_rows.append(table_row)

        return f"{header_row}\n{separator}\n" + "\n".join(table_rows)

    @staticmethod
    def pricing(
        original_price: int,
        discount_price: Optional[int] = None,
        discount_percent: Optional[int] = None
    ) -> str:
        """
        Create a pricing display with optional discount.

        Example:
        💰 Rp 50,000  ~~Rp 75,000~~
        💸 SAVE 33%
        """
        from utils.formatters import format_currency

        if discount_price:
            price_text = f"💰 {uf.bold(format_currency(discount_price))} "
            price_text += f"{uf.italic('~' + format_currency(original_price) + '~')}"

            if discount_percent:
                price_text += f"\n💸 {uf.bold(f'SAVE {discount_percent}%')}"
        else:
            price_text = f"💰 {uf.bold(format_currency(original_price))}"

        return price_text

    @staticmethod
    def button_row(buttons: List[str], cols: int = 3) -> str:
        """
        Format button labels for preview (not actual buttons).
        Shows how buttons will appear visually.

        Example:
        [Button 1] [Button 2] [Button 3]
        """
        rows = []
        for i in range(0, len(buttons), cols):
            row = buttons[i:i+cols]
            rows.append(" ".join(f"[{btn}]" for btn in row))

        return "\n".join(rows)


# Shorthand alias
vs = VisualSystem
