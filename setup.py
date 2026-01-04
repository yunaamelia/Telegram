"""
FRIENDS Store Telegram Bot - Setup Script

First-time setup: database initialization, connectivity tests, etc.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from database.db import Database
from database.seed import seed_database
from utils.logger import get_logger

logger = get_logger("setup")


async def test_database():
    """Test database connection."""
    print("\n📦 Testing Database...")

    try:
        db = Database(config.database.path)
        await db.init()

        # Test query
        products = await db.get_all_products()
        print(f"   ✅ Database connected: {len(products)} products found")

        await db.close()
        return True
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False


async def test_bot_token():
    """Test Telegram bot token."""
    print("\n🤖 Testing Bot Token...")

    try:
        from telegram import Bot

        bot = Bot(token=config.bot.token)
        me = await bot.get_me()

        print(f"   ✅ Bot connected: @{me.username}")
        return True
    except Exception as e:
        print(f"   ❌ Bot token error: {e}")
        return False


async def test_midtrans():
    """Test Midtrans connection."""
    print("\n💳 Testing Midtrans...")

    try:
        from services.midtrans import MidtransClient

        client = MidtransClient()

        # Just verify we can create client
        print(f"   ✅ Midtrans configured")
        print(f"      Environment: {'Production' if config.midtrans.is_production else 'Sandbox'}")
        print(f"      API URL: {config.midtrans.base_url}")

        return True
    except Exception as e:
        print(f"   ❌ Midtrans error: {e}")
        return False


async def initialize_database():
    """Initialize and seed database."""
    print("\n📦 Initializing Database...")

    try:
        db = Database(config.database.path)
        await db.init()
        await seed_database(db)
        await db.close()

        print("   ✅ Database initialized and seeded")
        return True
    except Exception as e:
        print(f"   ❌ Database initialization error: {e}")
        return False


def check_environment():
    """Check environment configuration."""
    print("\n⚙️ Checking Environment...")

    errors = []

    if not config.bot.token or config.bot.token.startswith("123456"):
        errors.append("BOT_TOKEN not configured properly")

    if not config.bot.super_admin_id:
        errors.append("SUPER_ADMIN_ID not configured")

    if not config.midtrans.server_key or config.midtrans.server_key.startswith("your"):
        errors.append("MIDTRANS_SERVER_KEY not configured")

    if errors:
        for error in errors:
            print(f"   ⚠️ {error}")
        return False

    print("   ✅ Environment configured")
    return True


def create_directories():
    """Create required directories."""
    print("\n📁 Creating Directories...")

    dirs = ["logs", "backups", "data", "assets"]

    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"   ✅ {d}/")

    return True


async def main():
    """Run setup."""
    print("=" * 50)
    print("FRIENDS Store Telegram Bot - Setup")
    print("=" * 50)

    # Check .env file
    if not os.path.exists(".env"):
        print("\n⚠️ .env file not found!")
        print("   Please copy .env.example to .env and configure it.")
        print("\n   cp .env.example .env")
        print("   nano .env")
        sys.exit(1)

    results = []

    # Create directories
    results.append(create_directories())

    # Check environment
    results.append(check_environment())

    # Initialize database
    results.append(await initialize_database())

    # Test components
    results.append(await test_database())
    results.append(await test_bot_token())
    results.append(await test_midtrans())

    # Summary
    print("\n" + "=" * 50)
    if all(results):
        print("✅ Setup Complete! All tests passed.")
        print("\nTo start the bot:")
        print("   python main.py")
    else:
        print("⚠️ Setup completed with warnings.")
        print("   Please fix the issues above before starting the bot.")

    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
