"""
Unicode font transformations for Telegram bot messages.
Provides multiple font styles using Unicode mathematical alphanumeric symbols.
"""


class UnicodeFonts:
    """
    Convert text to various Unicode font styles.

    Available styles:
    - Bold (Mathematical Bold)
    - Italic (Mathematical Italic)
    - Bold Italic
    - Monospace (Mathematical Monospace)
    - Sans-serif
    - Sans-serif Bold
    - Script/Cursive
    - Fraktur (Gothic)
    - Double-struck (Blackboard Bold)
    """

    # ==================== MATHEMATICAL BOLD ====================
    BOLD_UPPER = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄',
        'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈', 'J': '𝐉',
        'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎',
        'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓',
        'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘',
        'Z': '𝐙',
    }

    BOLD_LOWER = {
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞',
        'f': '𝐟', 'g': '𝐠', 'h': '𝐡', 'i': '𝐢', 'j': '𝐣',
        'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨',
        'p': '𝐩', 'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭',
        'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲',
        'z': '𝐳',
    }

    BOLD_DIGITS = {
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒',
        '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗',
    }

    # ==================== MATHEMATICAL ITALIC ====================
    ITALIC_UPPER = {
        'A': '𝐴', 'B': '𝐵', 'C': '𝐶', 'D': '𝐷', 'E': '𝐸',
        'F': '𝐹', 'G': '𝐺', 'H': '𝐻', 'I': '𝐼', 'J': '𝐽',
        'K': '𝐾', 'L': '𝐿', 'M': '𝑀', 'N': '𝑁', 'O': '𝑂',
        'P': '𝑃', 'Q': '𝑄', 'R': '𝑅', 'S': '𝑆', 'T': '𝑇',
        'U': '𝑈', 'V': '𝑉', 'W': '𝑊', 'X': '𝑋', 'Y': '𝑌',
        'Z': '𝑍',
    }

    ITALIC_LOWER = {
        'a': '𝑎', 'b': '𝑏', 'c': '𝑐', 'd': '𝑑', 'e': '𝑒',
        'f': '𝑓', 'g': '𝑔', 'h': 'ℎ', 'i': '𝑖', 'j': '𝑗',
        'k': '𝑘', 'l': '𝑙', 'm': '𝑚', 'n': '𝑛', 'o': '𝑜',
        'p': '𝑝', 'q': '𝑞', 'r': '𝑟', 's': '𝑠', 't': '𝑡',
        'u': '𝑢', 'v': '𝑣', 'w': '𝑤', 'x': '𝑥', 'y': '𝑦',
        'z': '𝑧',
    }

    # ==================== MATHEMATICAL BOLD ITALIC ====================
    BOLD_ITALIC_UPPER = {
        'A': '𝑨', 'B': '𝑩', 'C': '𝑪', 'D': '𝑫', 'E': '𝑬',
        'F': '𝑭', 'G': '𝑮', 'H': '𝑯', 'I': '𝑰', 'J': '𝑱',
        'K': '𝑲', 'L': '𝑳', 'M': '𝑴', 'N': '𝑵', 'O': '𝑶',
        'P': '𝑷', 'Q': '𝑸', 'R': '𝑹', 'S': '𝑺', 'T': '𝑻',
        'U': '𝑼', 'V': '𝑽', 'W': '𝑾', 'X': '𝑿', 'Y': '𝒀',
        'Z': '𝒁',
    }

    BOLD_ITALIC_LOWER = {
        'a': '𝒂', 'b': '𝒃', 'c': '𝒄', 'd': '𝒅', 'e': '𝒆',
        'f': '𝒇', 'g': '𝒈', 'h': '𝒉', 'i': '𝒊', 'j': '𝒋',
        'k': '𝒌', 'l': '𝒍', 'm': '𝒎', 'n': '𝒏', 'o': '𝒐',
        'p': '𝒑', 'q': '𝒒', 'r': '𝒓', 's': '𝒔', 't': '𝒕',
        'u': '𝒖', 'v': '𝒗', 'w': '𝒘', 'x': '𝒙', 'y': '𝒚',
        'z': '𝒛',
    }

    # ==================== MONOSPACE ====================
    MONOSPACE_UPPER = {
        'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴',
        'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸', 'J': '𝙹',
        'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾',
        'P': '𝙿', 'Q': '𝚀', 'R': '𝚁', 'S': '𝚂', 'T': '𝚃',
        'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈',
        'Z': '𝚉',
    }

    MONOSPACE_LOWER = {
        'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎',
        'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒', 'j': '𝚓',
        'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘',
        'p': '𝚙', 'q': '𝚚', 'r': '𝚛', 's': '𝚜', 't': '𝚝',
        'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢',
        'z': '𝚣',
    }

    MONOSPACE_DIGITS = {
        '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺',
        '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿',
    }

    # ==================== SANS-SERIF ====================
    SANS_UPPER = {
        'A': '𝖠', 'B': '𝖡', 'C': '𝖢', 'D': '𝖣', 'E': '𝖤',
        'F': '𝖥', 'G': '𝖦', 'H': '𝖧', 'I': '𝖨', 'J': '𝖩',
        'K': '𝖪', 'L': '𝖫', 'M': '𝖬', 'N': '𝖭', 'O': '𝖮',
        'P': '𝖯', 'Q': '𝖰', 'R': '𝖱', 'S': '𝖲', 'T': '𝖳',
        'U': '𝖴', 'V': '𝖵', 'W': '𝖶', 'X': '𝖷', 'Y': '𝖸',
        'Z': '𝖹',
    }

    SANS_LOWER = {
        'a': '𝖺', 'b': '𝖻', 'c': '𝖼', 'd': '𝖽', 'e': '𝖾',
        'f': '𝖿', 'g': '𝗀', 'h': '𝗁', 'i': '𝗂', 'j': '𝗃',
        'k': '𝗄', 'l': '𝗅', 'm': '𝗆', 'n': '𝗇', 'o': '𝗈',
        'p': '𝗉', 'q': '𝗊', 'r': '𝗋', 's': '𝗌', 't': '𝗍',
        'u': '𝗎', 'v': '𝗏', 'w': '𝗐', 'x': '𝗑', 'y': '𝗒',
        'z': '𝗓',
    }

    SANS_DIGITS = {
        '0': '𝟢', '1': '𝟣', '2': '𝟤', '3': '𝟥', '4': '𝟦',
        '5': '𝟧', '6': '𝟨', '7': '𝟩', '8': '𝟪', '9': '𝟫',
    }

    # ==================== SANS-SERIF BOLD ====================
    SANS_BOLD_UPPER = {
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘',
        'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝',
        'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢',
        'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧',
        'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬',
        'Z': '𝗭',
    }

    SANS_BOLD_LOWER = {
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲',
        'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷',
        'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼',
        'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁',
        'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆',
        'z': '𝘇',
    }

    SANS_BOLD_DIGITS = {
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵',
    }

    # ==================== SCRIPT / CURSIVE ====================
    SCRIPT_UPPER = {
        'A': '𝒜', 'B': 'ℬ', 'C': '𝒞', 'D': '𝒟', 'E': 'ℰ',
        'F': 'ℱ', 'G': '𝒢', 'H': 'ℋ', 'I': 'ℐ', 'J': '𝒥',
        'K': '𝒦', 'L': 'ℒ', 'M': 'ℳ', 'N': '𝒩', 'O': '𝒪',
        'P': '𝒫', 'Q': '𝒬', 'R': 'ℛ', 'S': '𝒮', 'T': '𝒯',
        'U': '𝒰', 'V': '𝒱', 'W': '𝒲', 'X': '𝒳', 'Y': '𝒴',
        'Z': '𝒵',
    }

    SCRIPT_LOWER = {
        'a': '𝒶', 'b': '𝒷', 'c': '𝒸', 'd': '𝒹', 'e': 'ℯ',
        'f': '𝒻', 'g': 'ℊ', 'h': '𝒽', 'i': '𝒾', 'j': '𝒿',
        'k': '𝓀', 'l': '𝓁', 'm': '𝓂', 'n': '𝓃', 'o': 'ℴ',
        'p': '𝓅', 'q': '𝓆', 'r': '𝓇', 's': '𝓈', 't': '𝓉',
        'u': '𝓊', 'v': '𝓋', 'w': '𝓌', 'x': '𝓍', 'y': '𝓎',
        'z': '𝓏',
    }

    # ==================== DOUBLE-STRUCK (BLACKBOARD BOLD) ====================
    DOUBLE_STRUCK_UPPER = {
        'A': '𝔸', 'B': '𝔹', 'C': 'ℂ', 'D': '𝔻', 'E': '𝔼',
        'F': '𝔽', 'G': '𝔾', 'H': 'ℍ', 'I': '𝕀', 'J': '𝕁',
        'K': '𝕂', 'L': '𝕃', 'M': '𝕄', 'N': 'ℕ', 'O': '𝕆',
        'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ', 'S': '𝕊', 'T': '𝕋',
        'U': '𝕌', 'V': '𝕍', 'W': '𝕎', 'X': '𝕏', 'Y': '𝕐',
        'Z': 'ℤ',
    }

    DOUBLE_STRUCK_LOWER = {
        'a': '𝕒', 'b': '𝕓', 'c': '𝕔', 'd': '𝕕', 'e': '𝕖',
        'f': '𝕗', 'g': '𝕘', 'h': '𝕙', 'i': '𝕚', 'j': '𝕛',
        'k': '𝕜', 'l': '𝕝', 'm': '𝕞', 'n': '𝕟', 'o': '𝕠',
        'p': '𝕡', 'q': '𝕢', 'r': '𝕣', 's': '𝕤', 't': '𝕥',
        'u': '𝕦', 'v': '𝕧', 'w': '𝕨', 'x': '𝕩', 'y': '𝕪',
        'z': '𝕫',
    }

    DOUBLE_STRUCK_DIGITS = {
        '0': '𝟘', '1': '𝟙', '2': '𝟚', '3': '𝟛', '4': '𝟜',
        '5': '𝟝', '6': '𝟞', '7': '𝟟', '8': '𝟠', '9': '𝟡',
    }

    # ==================== FRAKTUR (GOTHIC) ====================
    FRAKTUR_UPPER = {
        'A': '𝔄', 'B': '𝔅', 'C': 'ℭ', 'D': '𝔇', 'E': '𝔈',
        'F': '𝔉', 'G': '𝔊', 'H': 'ℌ', 'I': 'ℑ', 'J': '𝔍',
        'K': '𝔎', 'L': '𝔏', 'M': '𝔐', 'N': '𝔑', 'O': '𝔒',
        'P': '𝔓', 'Q': '𝔔', 'R': 'ℜ', 'S': '𝔖', 'T': '𝔗',
        'U': '𝔘', 'V': '𝔙', 'W': '𝔚', 'X': '𝔛', 'Y': '𝔜',
        'Z': 'ℨ',
    }

    FRAKTUR_LOWER = {
        'a': '𝔞', 'b': '𝔟', 'c': '𝔠', 'd': '𝔡', 'e': '𝔢',
        'f': '𝔣', 'g': '𝔤', 'h': '𝔥', 'i': '𝔦', 'j': '𝔧',
        'k': '𝔨', 'l': '𝔩', 'm': '𝔪', 'n': '𝔫', 'o': '𝔬',
        'p': '𝔭', 'q': '𝔮', 'r': '𝔯', 's': '𝔰', 't': '𝔱',
        'u': '𝔲', 'v': '𝔳', 'w': '𝔴', 'x': '𝔵', 'y': '𝔶',
        'z': '𝔷',
    }

    # ==================== SMALL CAPS ====================
    SMALL_CAPS = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ',
        'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
        'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ',
        'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ',
        'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ',
        'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ',
        'F': 'ғ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ',
        'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ',
        'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ',
        'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ',
        'Z': 'ᴢ',
    }

    # ==================== CONVERSION METHODS ====================

    @staticmethod
    def _convert(text: str, upper_map: dict, lower_map: dict, digit_map: dict = None) -> str:
        """Generic conversion method."""
        result = []
        for char in text:
            if char in upper_map:
                result.append(upper_map[char])
            elif char in lower_map:
                result.append(lower_map[char])
            elif digit_map and char in digit_map:
                result.append(digit_map[char])
            else:
                result.append(char)
        return ''.join(result)

    @classmethod
    def bold(cls, text: str) -> str:
        """
        Convert to mathematical bold.
        Example: "Hello 123" → "𝐇𝐞𝐥𝐥𝐨 𝟏𝟐𝟑"
        """
        return cls._convert(text, cls.BOLD_UPPER, cls.BOLD_LOWER, cls.BOLD_DIGITS)

    @classmethod
    def italic(cls, text: str) -> str:
        """
        Convert to mathematical italic.
        Example: "Hello" → "𝐻𝑒𝑙𝑙𝑜"
        """
        return cls._convert(text, cls.ITALIC_UPPER, cls.ITALIC_LOWER)

    @classmethod
    def bold_italic(cls, text: str) -> str:
        """
        Convert to mathematical bold italic.
        Example: "Hello" → "𝑯𝒆𝒍𝒍𝒐"
        """
        return cls._convert(text, cls.BOLD_ITALIC_UPPER, cls.BOLD_ITALIC_LOWER)

    @classmethod
    def monospace(cls, text: str) -> str:
        """
        Convert to monospace.
        Example: "Hello 123" → "𝙷𝚎𝚕𝚕𝚘 𝟷𝟸𝟹"
        """
        return cls._convert(text, cls.MONOSPACE_UPPER, cls.MONOSPACE_LOWER, cls.MONOSPACE_DIGITS)

    @classmethod
    def sans(cls, text: str) -> str:
        """
        Convert to sans-serif.
        Example: "Hello 123" → "𝖧𝖾𝗅𝗅𝗈 𝟣𝟤𝟥"
        """
        return cls._convert(text, cls.SANS_UPPER, cls.SANS_LOWER, cls.SANS_DIGITS)

    @classmethod
    def sans_bold(cls, text: str) -> str:
        """
        Convert to sans-serif bold.
        Example: "Hello 123" → "𝗛𝗲𝗹𝗹𝗼 𝟭𝟮𝟯"
        """
        return cls._convert(text, cls.SANS_BOLD_UPPER, cls.SANS_BOLD_LOWER, cls.SANS_BOLD_DIGITS)

    @classmethod
    def script(cls, text: str) -> str:
        """
        Convert to script/cursive.
        Example: "Hello" → "ℋℯ𝓁𝓁ℴ"
        """
        return cls._convert(text, cls.SCRIPT_UPPER, cls.SCRIPT_LOWER)

    @classmethod
    def double_struck(cls, text: str) -> str:
        """
        Convert to double-struck (blackboard bold).
        Example: "Hello 123" → "ℍ𝕖𝕝𝕝𝕠 𝟙𝟚𝟛"
        """
        return cls._convert(text, cls.DOUBLE_STRUCK_UPPER, cls.DOUBLE_STRUCK_LOWER, cls.DOUBLE_STRUCK_DIGITS)

    @classmethod
    def fraktur(cls, text: str) -> str:
        """
        Convert to Fraktur (Gothic).
        Example: "Hello" → "ℌ𝔢𝔩𝔩𝔬"
        """
        return cls._convert(text, cls.FRAKTUR_UPPER, cls.FRAKTUR_LOWER)

    @classmethod
    def small_caps(cls, text: str) -> str:
        """
        Convert to small caps.
        Example: "Hello" → "ʜᴇʟʟᴏ"
        """
        return ''.join(cls.SMALL_CAPS.get(c, c) for c in text)

    # ==================== UTILITY METHODS ====================

    @classmethod
    def get_available_styles(cls) -> list:
        """Get list of available font styles."""
        return [
            'bold',
            'italic',
            'bold_italic',
            'monospace',
            'sans',
            'sans_bold',
            'script',
            'double_struck',
            'fraktur',
            'small_caps',
        ]

    @classmethod
    def apply_style(cls, text: str, style: str) -> str:
        """
        Apply a style by name.

        Args:
            text: Text to convert
            style: Style name (see get_available_styles())

        Returns:
            Converted text
        """
        style_map = {
            'bold': cls.bold,
            'italic': cls.italic,
            'bold_italic': cls.bold_italic,
            'monospace': cls.monospace,
            'sans': cls.sans,
            'sans_bold': cls.sans_bold,
            'script': cls.script,
            'double_struck': cls.double_struck,
            'fraktur': cls.fraktur,
            'small_caps': cls.small_caps,
        }

        converter = style_map.get(style.lower())
        if converter:
            return converter(text)
        else:
            return text


# Convenience shorthand
uf = UnicodeFonts
