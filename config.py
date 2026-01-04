"""
Configuration module for FRIENDS Store Telegram Bot.
Loads environment variables and provides typed configuration access.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.getenv(key, default)


def get_env_int(key: str, default: int = 0) -> int:
    """Get environment variable as integer."""
    return int(os.getenv(key, str(default)))


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get environment variable as float."""
    return float(os.getenv(key, str(default)))


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_list(key: str, default: str = "", separator: str = ",") -> List[str]:
    """Get environment variable as list."""
    value = os.getenv(key, default)
    if not value:
        return []
    return [item.strip() for item in value.split(separator) if item.strip()]


@dataclass
class BotConfig:
    """Bot configuration settings."""
    token: str = get_env("BOT_TOKEN")
    super_admin_id: int = get_env_int("SUPER_ADMIN_ID")
    support_username: str = get_env("SUPPORT_USERNAME", "support")


@dataclass
class StoreConfig:
    """Store branding configuration."""
    name: str = get_env("STORE_NAME", "FRIENDS Store")
    logo_path: str = get_env("LOGO_PATH", "./assets/logo.png")


@dataclass
class MidtransConfig:
    """Midtrans payment gateway configuration."""
    server_key: str = get_env("MIDTRANS_SERVER_KEY")
    client_key: str = get_env("MIDTRANS_CLIENT_KEY")
    merchant_id: str = get_env("MIDTRANS_MERCHANT_ID")
    is_production: bool = get_env_bool("MIDTRANS_IS_PRODUCTION", False)

    @property
    def base_url(self) -> str:
        """Get API base URL based on environment."""
        if self.is_production:
            return "https://api.midtrans.com"
        return "https://api.sandbox.midtrans.com"


@dataclass
class WebhookConfig:
    """Webhook server configuration."""
    url: str = get_env("WEBHOOK_URL")
    secret: str = get_env("WEBHOOK_SECRET")
    port: int = get_env_int("WEBHOOK_PORT", 8000)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    path: str = get_env("DATABASE_PATH", "./data/bot.db")

    def ensure_directory(self) -> None:
        """Ensure database directory exists."""
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)


@dataclass
class SecurityConfig:
    """Security configuration."""
    ip_whitelist: List[str] = None

    def __post_init__(self):
        self.ip_whitelist = get_env_list("IP_WHITELIST")


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = get_env("LOG_LEVEL", "INFO")
    retention_days: int = get_env_int("LOG_RETENTION_DAYS", 30)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests: int = get_env_int("RATE_LIMIT_REQUESTS", 10)
    window: int = get_env_int("RATE_LIMIT_WINDOW", 60)
    cooldown: int = get_env_int("COMMAND_COOLDOWN", 5)


@dataclass
class TransactionConfig:
    """Transaction configuration."""
    expiry_minutes: int = get_env_int("TRANSACTION_EXPIRY_MINUTES", 15)
    max_pending: int = get_env_int("MAX_PENDING_TRANSACTIONS", 3)
    max_daily_per_product: int = get_env_int("MAX_DAILY_PURCHASES_PER_PRODUCT", 5)


@dataclass
class BackupConfig:
    """Backup configuration."""
    channel_id: Optional[int] = None
    retention_days: int = get_env_int("BACKUP_RETENTION_DAYS", 30)

    def __post_init__(self):
        channel_str = get_env("BACKUP_CHANNEL_ID")
        if channel_str:
            self.channel_id = int(channel_str)


@dataclass
class BroadcastConfig:
    """Broadcast configuration."""
    time: str = get_env("DAILY_BROADCAST_TIME", "10:00")
    enabled: bool = get_env_bool("DAILY_BROADCAST_ENABLED", True)


@dataclass
class StockConfig:
    """Stock alert thresholds."""
    warning_threshold: float = get_env_float("STOCK_WARNING_THRESHOLD", 0.30)
    critical_threshold: float = get_env_float("STOCK_CRITICAL_THRESHOLD", 0.10)


class Config:
    """Main configuration container."""

    DEBUG: bool = get_env_bool("DEBUG", False)

    bot = BotConfig()
    store = StoreConfig()
    midtrans = MidtransConfig()
    webhook = WebhookConfig()
    database = DatabaseConfig()
    security = SecurityConfig()
    logging = LoggingConfig()
    rate_limit = RateLimitConfig()
    transaction = TransactionConfig()
    backup = BackupConfig()
    broadcast = BroadcastConfig()
    stock = StockConfig()

    @classmethod
    def validate(cls) -> List[str]:
        """Validate required configuration. Returns list of errors."""
        errors = []

        if not cls.bot.token:
            errors.append("BOT_TOKEN is required")
        if not cls.bot.super_admin_id:
            errors.append("SUPER_ADMIN_ID is required")
        if not cls.midtrans.server_key:
            errors.append("MIDTRANS_SERVER_KEY is required")

        return errors


# Global config instance
config = Config()
