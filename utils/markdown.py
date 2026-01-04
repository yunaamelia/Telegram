"""
MarkdownV2 formatter with auto-escaping for Telegram messages.
"""

import re
from typing import Union


class MarkdownV2Formatter:
    """MarkdownV2 formatter with auto-escaping for special characters."""

    # Characters that need escaping in MarkdownV2
    ESCAPE_CHARS = r'_*[]()~`>#+-=|{}.!'

    @staticmethod
    def escape(text: str) -> str:
        """Escape special characters for MarkdownV2."""
        if not text:
            return ""
        return re.sub(f'([{re.escape(MarkdownV2Formatter.ESCAPE_CHARS)}])', r'\\\1', str(text))

    @staticmethod
    def bold(text: str, escape: bool = True) -> str:
        """Format as **bold**."""
        content = MarkdownV2Formatter.escape(text) if escape else text
        return f"*{content}*"

    @staticmethod
    def italic(text: str, escape: bool = True) -> str:
        """Format as _italic_."""
        content = MarkdownV2Formatter.escape(text) if escape else text
        return f"_{content}_"

    @staticmethod
    def underline(text: str, escape: bool = True) -> str:
        """Format as __underline__."""
        content = MarkdownV2Formatter.escape(text) if escape else text
        return f"__{content}__"

    @staticmethod
    def strikethrough(text: str, escape: bool = True) -> str:
        """Format as ~strikethrough~."""
        content = MarkdownV2Formatter.escape(text) if escape else text
        return f"~{content}~"

    @staticmethod
    def spoiler(text: str, escape: bool = True) -> str:
        """Format as ||spoiler||."""
        content = MarkdownV2Formatter.escape(text) if escape else text
        return f"||{content}||"

    @staticmethod
    def code(text: str) -> str:
        """Format as `inline code`."""
        # Only escape backticks in code
        content = str(text).replace('`', '\\`')
        return f"`{content}`"

    @staticmethod
    def code_block(text: str, language: str = "") -> str:
        """Format as code block."""
        content = str(text).replace('`', '\\`')
        return f"```{language}\n{content}\n```"

    @staticmethod
    def link(text: str, url: str) -> str:
        """Format as [text](url)."""
        escaped_text = MarkdownV2Formatter.escape(text)
        # Only escape ) in URL
        escaped_url = url.replace(')', '\\)')
        return f"[{escaped_text}]({escaped_url})"

    @staticmethod
    def mention(user_id: int, name: str) -> str:
        """Format as user mention."""
        escaped_name = MarkdownV2Formatter.escape(name)
        return f"[{escaped_name}](tg://user?id={user_id})"

    @staticmethod
    def divider() -> str:
        """Return a visual divider line."""
        return "━━━━━━━━━━━━━━━━━━━━"

    @staticmethod
    def format_price(amount: Union[int, float]) -> str:
        """Format number as price: 50,000 -> 50.000."""
        return f"{int(amount):,}".replace(',', '.')

    @staticmethod
    def format_currency(amount: Union[int, float]) -> str:
        """Format as Indonesian Rupiah."""
        return f"Rp {MarkdownV2Formatter.format_price(amount)}"

    @staticmethod
    def number_emoji(num: int) -> str:
        """Convert number (1-9) to emoji."""
        emojis = {
            1: "1️⃣", 2: "2️⃣", 3: "3️⃣",
            4: "4️⃣", 5: "5️⃣", 6: "6️⃣",
            7: "7️⃣", 8: "8️⃣", 9: "9️⃣",
            0: "0️⃣"
        }
        return emojis.get(num, str(num))


# Convenient alias
md = MarkdownV2Formatter
