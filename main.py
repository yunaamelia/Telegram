"""
FRIENDS Store Telegram Bot - Main Entry Point

A fully automated Telegram bot for selling premium digital accounts
with integrated Midtrans QRIS payment system.
"""

import asyncio
from datetime import datetime
from warnings import filterwarnings

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes
from telegram.warnings import PTBUserWarning

# Suppress PTB per_message warning (intentional setting)
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

from config import config
from database.db import Database
from database.seed import seed_database
from webhook.server import WebhookServer
from webhook.midtrans import process_midtrans_callback
from jobs.scheduler import setup_scheduler
from utils.logger import get_logger

# Import handlers
from handlers.user.start import start_handler, main_menu_handler
from handlers.user import (
    start_handler,
    main_menu_handler,
    buy_handlers,
    history_handlers,
    help_handlers,
    callback_query_handler,
    reply_keyboard_handler
)
from handlers.user.callbacks import noop_handler
from handlers.admin import (
    stock_handlers,
    product_handlers,
    transaction_handlers,
    broadcast_handlers,
    admin_mgmt_handlers,
    system_handlers
)
from handlers.admin.security import security_handlers

# Admin UI handlers and wizards
from handlers.admin.ui import all_admin_ui_handlers
from handlers.admin.wizards import all_admin_wizards

logger = get_logger("bot")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error(f"Exception while handling an update: {context.error}")

    # Send error to super admin in debug mode
    if config.DEBUG and config.bot.super_admin_id:
        try:
            error_message = f"❌ Bot Error:\n\n`{context.error}`"
            await context.bot.send_message(
                chat_id=config.bot.super_admin_id,
                text=error_message[:4000],
                parse_mode="Markdown"
            )
        except Exception:
            pass


def create_application(db: Database) -> Application:
    """Create and configure the Telegram application."""
    # Validate config
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"Config error: {error}")
        raise ValueError("Invalid configuration")

    # Build application
    app = (
        ApplicationBuilder()
        .token(config.bot.token)
        .build()
    )

    # Store database in bot_data immediately
    app.bot_data["db"] = db
    app.bot_data["start_time"] = datetime.now()

    # Add error handler
    app.add_error_handler(error_handler)

    # Register user handlers
    app.add_handler(start_handler)
    app.add_handler(main_menu_handler)

    for handler in buy_handlers:
        app.add_handler(handler)

    for handler in history_handlers:
        app.add_handler(handler)

    for handler in help_handlers:
        app.add_handler(handler)

    app.add_handler(callback_query_handler)
    app.add_handler(noop_handler)
    
    # Reply keyboard handler (must be after all command handlers)
    app.add_handler(reply_keyboard_handler)

    # Register admin handlers
    for handler in stock_handlers:
        app.add_handler(handler)

    for handler in product_handlers:
        app.add_handler(handler)

    for handler in transaction_handlers:
        app.add_handler(handler)

    for handler in broadcast_handlers:
        app.add_handler(handler)

    for handler in admin_mgmt_handlers:
        app.add_handler(handler)

    for handler in system_handlers:
        app.add_handler(handler)

    for handler in security_handlers:
        app.add_handler(handler)

    # Register admin UI handlers (inline keyboard navigation)
    for handler in all_admin_ui_handlers:
        app.add_handler(handler)

    # Register admin wizards (conversation handlers - must be after UI handlers)
    for handler in all_admin_wizards:
        app.add_handler(handler)

    logger.info("All handlers registered")

    return app


async def run_webhook_server(app: Application) -> WebhookServer:
    """Start the webhook server."""
    server = WebhookServer()
    server.set_dependencies(app.bot, app.bot_data.get("db"))

    # Set callback handler
    async def handle_callback(data):
        await process_midtrans_callback(data, app.bot, app.bot_data["db"])

    server.set_midtrans_handler(handle_callback)

    await server.start()
    return server


async def main():
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("FRIENDS Store Telegram Bot")
    logger.info("=" * 50)

    # Initialize database FIRST
    logger.info("Initializing database...")
    db = Database(config.database.path)
    await db.init()
    await seed_database(db)
    logger.info("Database ready")

    # Create application with database
    app = create_application(db)

    # Initialize the application
    await app.initialize()

    # Setup scheduled jobs
    await setup_scheduler(app)

    await app.start()

    # Start webhook server
    webhook_server = await run_webhook_server(app)

    # Start polling
    logger.info("Starting bot polling...")

    try:
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

        # Keep running
        logger.info("Bot is running. Press Ctrl+C to stop.")

        # Wait forever
        while True:
            await asyncio.sleep(3600)

    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup
        logger.info("Stopping bot...")
        await app.updater.stop()
        await webhook_server.stop()
        await app.stop()
        await app.shutdown()
        await db.close()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise


