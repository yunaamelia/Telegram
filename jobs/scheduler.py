"""
Scheduler configuration for FRIENDS Store Telegram Bot.
"""

from datetime import datetime
from telegram.ext import Application

from config import config
from utils.logger import get_logger

logger = get_logger("scheduler")


async def setup_scheduler(app: Application) -> None:
    """
    Set up scheduled jobs using python-telegram-bot's job queue.

    Args:
        app: Telegram application instance
    """
    job_queue = app.job_queue

    if not job_queue:
        logger.error("Job queue not available")
        return

    from jobs.expiry_checker import check_expired_transactions
    from jobs.daily_broadcast import send_daily_broadcast
    from jobs.backup import run_daily_backup
    from jobs.stock_alerts import check_stock_levels

    # Transaction expiry checker - every minute
    job_queue.run_repeating(
        check_expired_transactions,
        interval=60,
        first=10,
        name="expiry_checker"
    )
    logger.info("Scheduled: expiry_checker (every 60s)")

    # Stock level checker - every 30 minutes
    job_queue.run_repeating(
        check_stock_levels,
        interval=1800,  # 30 minutes
        first=30,
        name="stock_checker"
    )
    logger.info("Scheduled: stock_checker (every 30m)")

    # Daily broadcast - 10:00 WIB (03:00 UTC)
    if config.broadcast.enabled:
        from datetime import time
        import pytz

        wib = pytz.timezone("Asia/Jakarta")

        # Parse broadcast time
        broadcast_time = config.broadcast.time
        hour, minute = map(int, broadcast_time.split(":"))

        job_queue.run_daily(
            send_daily_broadcast,
            time=time(hour=hour, minute=minute, tzinfo=wib),
            name="daily_broadcast"
        )
        logger.info(f"Scheduled: daily_broadcast ({broadcast_time} WIB)")

    # Daily backup - 03:00 WIB (20:00 UTC previous day)
    from datetime import time
    import pytz

    wib = pytz.timezone("Asia/Jakarta")

    job_queue.run_daily(
        run_daily_backup,
        time=time(hour=3, minute=0, tzinfo=wib),
        name="daily_backup"
    )
    logger.info("Scheduled: daily_backup (03:00 WIB)")

    logger.info("All scheduled jobs configured successfully")
