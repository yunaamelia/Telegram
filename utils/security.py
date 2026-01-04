"""
Security utilities for FRIENDS Store Telegram Bot.
"""

import hashlib
import hmac
import ipaddress
from typing import Optional, List

from config import config
from utils.logger import get_logger

logger = get_logger("security")


def validate_midtrans_signature(
    order_id: str,
    status_code: str,
    gross_amount: str,
    signature: str
) -> bool:
    """
    Validate Midtrans webhook signature.

    Signature formula: SHA512(order_id + status_code + gross_amount + server_key)
    """
    server_key = config.midtrans.server_key

    # Build the signature string
    signature_string = f"{order_id}{status_code}{gross_amount}{server_key}"

    # Calculate expected signature
    expected_signature = hashlib.sha512(signature_string.encode()).hexdigest()

    # Compare signatures
    is_valid = hmac.compare_digest(expected_signature, signature)

    if not is_valid:
        logger.warning(
            f"Invalid Midtrans signature for order {order_id}. "
            f"Expected: {expected_signature[:20]}..., Got: {signature[:20]}..."
        )

    return is_valid


def validate_webhook_token(token: Optional[str]) -> bool:
    """Validate webhook secret token from query parameter."""
    if not config.webhook.secret:
        # No secret configured, skip validation
        return True

    if not token:
        logger.warning("Missing webhook token")
        return False

    is_valid = hmac.compare_digest(config.webhook.secret, token)

    if not is_valid:
        logger.warning("Invalid webhook token")

    return is_valid


def is_ip_allowed(client_ip: str) -> bool:
    """
    Check if client IP is in the whitelist.

    Supports both individual IPs and CIDR notation.
    """
    whitelist = config.security.ip_whitelist

    if not whitelist:
        # No whitelist configured, allow all
        return True

    try:
        client = ipaddress.ip_address(client_ip)

        for allowed in whitelist:
            allowed = allowed.strip()
            if not allowed:
                continue

            try:
                if "/" in allowed:
                    # CIDR notation
                    network = ipaddress.ip_network(allowed, strict=False)
                    if client in network:
                        return True
                else:
                    # Single IP
                    if client == ipaddress.ip_address(allowed):
                        return True
            except ValueError:
                logger.warning(f"Invalid IP/network in whitelist: {allowed}")
                continue

        logger.warning(f"IP not in whitelist: {client_ip}")
        return False

    except ValueError:
        logger.warning(f"Invalid client IP: {client_ip}")
        return False


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.

    - Truncates to max length
    - Removes potentially dangerous characters
    """
    if not text:
        return ""

    # Truncate
    text = text[:max_length]

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove control characters except newlines and tabs
    text = "".join(
        char for char in text
        if char >= " " or char in "\n\t\r"
    )

    return text.strip()


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data (passwords, emails, etc.) for logging.

    Example: "password123" -> "pass****"
    """
    if not data or len(data) <= visible_chars:
        return "*" * len(data) if data else ""

    return data[:visible_chars] + "*" * (len(data) - visible_chars)


def generate_transaction_id(prefix: str = "FRIENDS") -> str:
    """Generate a unique transaction/order ID."""
    import time
    import secrets

    timestamp = int(time.time() * 1000)
    random_part = secrets.token_hex(4).upper()

    return f"{prefix}-{timestamp}-{random_part}"


def hash_password(password: str) -> str:
    """
    Hash a password for storage (if needed for additional security).

    Note: This is for our own purposes, not for the stock credentials.
    """
    salt = config.webhook.secret[:16] if config.webhook.secret else "default_salt_key"
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000
    ).hex()


class SecurityChecker:
    """Centralized security checking."""

    def __init__(self):
        self._failed_attempts: dict = {}  # ip -> count
        self._suspicious_users: set = set()

    def record_failed_attempt(self, ip: str) -> int:
        """Record a failed auth attempt. Returns current count."""
        count = self._failed_attempts.get(ip, 0) + 1
        self._failed_attempts[ip] = count

        if count >= 5:
            logger.warning(f"Multiple failed attempts from IP: {ip} (count: {count})")

        return count

    def is_ip_blocked(self, ip: str, threshold: int = 10) -> bool:
        """Check if IP should be temporarily blocked."""
        return self._failed_attempts.get(ip, 0) >= threshold

    def reset_failed_attempts(self, ip: str) -> None:
        """Reset failed attempts for an IP."""
        self._failed_attempts.pop(ip, None)

    def mark_user_suspicious(self, user_id: int, reason: str) -> None:
        """Mark a user as suspicious."""
        self._suspicious_users.add(user_id)
        logger.warning(f"User {user_id} marked suspicious: {reason}")

    def is_user_suspicious(self, user_id: int) -> bool:
        """Check if user is marked as suspicious."""
        return user_id in self._suspicious_users


# Global instance
security_checker = SecurityChecker()
