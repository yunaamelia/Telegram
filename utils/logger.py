"""
Logging configuration for FRIENDS Store Telegram Bot.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str = "bot",
    log_dir: str = "./logs",
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level
        max_bytes: Max file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Main log file (rotating by size)
    main_log_path = os.path.join(log_dir, f"{name}.log")
    file_handler = RotatingFileHandler(
        main_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Error log file (separate for easy access)
    error_log_path = os.path.join(log_dir, "error.log")
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    return logger


def get_logger(name: str = "bot") -> logging.Logger:
    """Get or create a logger with the given name."""
    return logging.getLogger(name)


# Pre-configured loggers
bot_logger = setup_logger("bot")
webhook_logger = setup_logger("webhook", log_dir="./logs")
db_logger = setup_logger("database", log_dir="./logs")
payment_logger = setup_logger("payment", log_dir="./logs")
