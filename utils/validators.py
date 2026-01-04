"""
Input validators for FRIENDS Store Telegram Bot.
"""

import re
from typing import Tuple, Optional


def validate_product_code(code: str) -> Tuple[bool, str]:
    """
    Validate product code format.
    Must be lowercase alphanumeric with underscores, 3-50 chars.
    """
    if not code:
        return False, "Product code cannot be empty"

    if len(code) < 3:
        return False, "Product code must be at least 3 characters"

    if len(code) > 50:
        return False, "Product code must be at most 50 characters"

    if not re.match(r"^[a-z0-9_]+$", code):
        return False, "Product code must be lowercase alphanumeric with underscores only"

    return True, ""


def validate_product_name(name: str) -> Tuple[bool, str]:
    """Validate product name."""
    if not name:
        return False, "Product name cannot be empty"

    if len(name) > 100:
        return False, "Product name must be at most 100 characters"

    return True, ""


def validate_price(price_str: str) -> Tuple[bool, str, int]:
    """
    Validate and parse price.
    Returns (is_valid, error_message, parsed_price)
    """
    try:
        # Remove common formatting
        price_str = price_str.replace(".", "").replace(",", "").replace("Rp", "").strip()
        price = int(price_str)

        if price <= 0:
            return False, "Price must be positive", 0

        if price > 100000000:  # 100 million
            return False, "Price seems too high", 0

        return True, "", price

    except ValueError:
        return False, "Invalid price format", 0


def validate_stock_entry(entry: str) -> Tuple[bool, str, dict]:
    """
    Validate stock entry format: email:password:2fa_secret:notes
    2fa_secret and notes are optional.

    Returns (is_valid, error_message, parsed_data)
    """
    if not entry:
        return False, "Stock entry cannot be empty", {}

    parts = entry.split(":")

    if len(parts) < 2:
        return False, "Format: email:password[:2fa_secret][:notes]", {}

    email = parts[0].strip()
    password = parts[1].strip()
    two_fa_secret = parts[2].strip() if len(parts) > 2 else None
    notes = parts[3].strip() if len(parts) > 3 else None

    # Validate email (basic check)
    if not email or len(email) < 3:
        return False, "Invalid email", {}

    # Validate password
    if not password:
        return False, "Password cannot be empty", {}

    result = {
        "email": email,
        "password": password,
        "two_fa_secret": two_fa_secret if two_fa_secret else None,
        "notes": notes if notes else None
    }

    return True, "", result


def validate_user_id(user_id_str: str) -> Tuple[bool, str, int]:
    """
    Validate and parse Telegram user ID.
    Returns (is_valid, error_message, parsed_id)
    """
    try:
        user_id = int(user_id_str.strip())

        if user_id <= 0:
            return False, "Invalid user ID", 0

        return True, "", user_id

    except ValueError:
        return False, "User ID must be a number", 0


def validate_transaction_id(tx_id: str) -> Tuple[bool, str]:
    """Validate transaction ID format."""
    if not tx_id:
        return False, "Transaction ID cannot be empty"

    # Our format: FRIENDS-{timestamp}-{random}
    if not tx_id.startswith("FRIENDS-"):
        return False, "Invalid transaction ID format"

    if len(tx_id) < 15:
        return False, "Transaction ID too short"

    return True, ""


def parse_admin_command(text: str) -> Tuple[str, list]:
    """
    Parse admin command text.
    Returns (command, args)
    """
    if not text:
        return "", []

    parts = text.strip().split(maxsplit=1)
    command = parts[0].lower()

    if len(parts) == 1:
        return command, []

    # Handle remaining args
    remaining = parts[1]
    args = remaining.split()

    return command, args


def validate_broadcast_message(message: str) -> Tuple[bool, str]:
    """Validate broadcast message."""
    if not message:
        return False, "Broadcast message cannot be empty"

    if len(message) > 4000:
        return False, "Broadcast message too long (max 4000 characters)"

    return True, ""


def extract_callback_data(data: str) -> Tuple[str, list]:
    """
    Extract prefix and parts from callback data.
    Format: prefix:part1:part2:...

    Returns (prefix, parts_list)
    """
    if not data:
        return "", []

    parts = data.split(":")
    prefix = parts[0]
    remaining = parts[1:] if len(parts) > 1 else []

    return prefix, remaining


def is_valid_2fa_secret(secret: str) -> bool:
    """
    Validate 2FA secret format (base32).
    """
    if not secret:
        return True  # Optional field

    # Base32 alphabet
    base32_pattern = r"^[A-Z2-7]+=*$"
    return bool(re.match(base32_pattern, secret.upper()))
