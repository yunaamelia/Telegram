"""
Test Unicode font transformations.
"""

import pytest
from utils.unicode_fonts import UnicodeFonts as uf


class TestUnicodeFonts:
    """Test Unicode font conversions."""

    def test_bold_conversion(self):
        """Test bold conversion."""
        input_text = "Hello 123"
        output = uf.bold(input_text)

        # Should contain Unicode bold characters
        assert output != input_text
        assert '𝐇' in output  # Bold H
        assert '𝟏' in output  # Bold 1

    def test_monospace_conversion(self):
        """Test monospace conversion."""
        input_text = "Code 456"
        output = uf.monospace(input_text)

        assert output != input_text
        assert '𝙲' in output  # Monospace C
        assert '𝟺' in output  # Monospace 4

    def test_small_caps_conversion(self):
        """Test small caps conversion."""
        input_text = "Hello"
        output = uf.small_caps(input_text)

        assert output != input_text
        assert 'ʜ' in output.lower()  # Small caps h

    def test_preserves_spaces(self):
        """Test that spaces are preserved."""
        input_text = "Hello World"
        output = uf.bold(input_text)

        assert ' ' in output
        assert output.count(' ') == input_text.count(' ')

    def test_preserves_emojis(self):
        """Test that emojis are preserved."""
        input_text = "Hello 👋 World"
        output = uf.bold(input_text)

        assert '👋' in output

    def test_preserves_punctuation(self):
        """Test that punctuation is preserved."""
        input_text = "Hello, World!"
        output = uf.bold(input_text)

        assert ',' in output
        assert '!' in output

    def test_apply_style_method(self):
        """Test apply_style method."""
        input_text = "Test"

        bold_output = uf.apply_style(input_text, 'bold')
        mono_output = uf.apply_style(input_text, 'monospace')

        assert bold_output != mono_output
        assert bold_output != input_text

    def test_get_available_styles(self):
        """Test getting available styles."""
        styles = uf.get_available_styles()

        assert 'bold' in styles
        assert 'monospace' in styles
        assert 'italic' in styles
        assert len(styles) >= 8

    def test_indonesian_text(self):
        """Test Indonesian text support."""
        input_text = "Selamat datang"
        output = uf.bold(input_text)

        # Should convert all letters
        assert output != input_text
        assert len(output) == len(input_text)

    def test_italic_conversion(self):
        """Test italic conversion."""
        input_text = "Hello"
        output = uf.italic(input_text)

        assert output != input_text
        assert '𝐻' in output  # Italic H

    def test_bold_italic_conversion(self):
        """Test bold italic conversion."""
        input_text = "Hello"
        output = uf.bold_italic(input_text)

        assert output != input_text
        assert '𝑯' in output  # Bold Italic H

    def test_sans_conversion(self):
        """Test sans-serif conversion."""
        input_text = "Hello 123"
        output = uf.sans(input_text)

        assert output != input_text
        assert '𝖧' in output  # Sans H

    def test_sans_bold_conversion(self):
        """Test sans-serif bold conversion."""
        input_text = "Hello 123"
        output = uf.sans_bold(input_text)

        assert output != input_text
        assert '𝗛' in output  # Sans Bold H
        assert '𝟭' in output  # Sans Bold 1

    def test_script_conversion(self):
        """Test script conversion."""
        input_text = "Hello"
        output = uf.script(input_text)

        assert output != input_text

    def test_double_struck_conversion(self):
        """Test double-struck conversion."""
        input_text = "Hello 123"
        output = uf.double_struck(input_text)

        assert output != input_text
        assert 'ℍ' in output  # Double-struck H
        assert '𝟙' in output  # Double-struck 1

    def test_fraktur_conversion(self):
        """Test fraktur conversion."""
        input_text = "Hello"
        output = uf.fraktur(input_text)

        assert output != input_text
        assert 'ℌ' in output  # Fraktur H

    def test_apply_style_invalid(self):
        """Test apply_style with invalid style returns original."""
        input_text = "Test"
        output = uf.apply_style(input_text, 'invalid_style')

        assert output == input_text

    def test_empty_string(self):
        """Test empty string handling."""
        output = uf.bold("")
        assert output == ""

    def test_numbers_only(self):
        """Test numbers only."""
        input_text = "12345"
        output = uf.bold(input_text)

        assert output != input_text
        assert '𝟏' in output
        assert '𝟐' in output


class TestFormatterIntegration:
    """Test integration with formatters."""

    def test_format_currency_with_monospace(self):
        """Test currency formatting with monospace."""
        from utils.formatters import format_currency

        price = 50000
        formatted = uf.monospace(format_currency(price))

        assert '𝟻𝟶' in formatted  # 50 in monospace

    def test_welcome_message_format(self):
        """Test complete welcome message."""
        name = "FRIENDS Store"
        styled = uf.bold(name)

        # Should contain styled text
        assert '𝐅' in styled  # Bold F
        assert '𝐑' in styled  # Bold R
