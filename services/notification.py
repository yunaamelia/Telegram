"""
Notification service for FRIENDS Store Telegram Bot.
"""

from typing import List, Optional

from telegram import Bot
from telegram.error import TelegramError

from config import config
from database.db import Database
from utils.logger import get_logger

logger = get_logger("notification")


class NotificationService:
    """Handles notifications to users and admins."""

    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db

    async def notify_user(
        self,
        user_id: int,
        message: str,
        parse_mode: str = "Markdown",
        reply_markup=None
    ) -> bool:
        """
        Send notification to a user.

        Returns:
            True if sent successfully
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except TelegramError as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            return False

    async def notify_admins(
        self,
        message: str,
        parse_mode: str = "Markdown",
        exclude: Optional[List[int]] = None
    ) -> int:
        """
        Send notification to all admins.

        Returns:
            Number of admins successfully notified
        """
        admins = await self.db.get_all_admins()
        sent = 0
        exclude = exclude or []

        for admin in admins:
            if admin["user_id"] in exclude:
                continue

            try:
                await self.bot.send_message(
                    chat_id=admin["user_id"],
                    text=message,
                    parse_mode=parse_mode
                )
                sent += 1
            except TelegramError as e:
                logger.error(f"Failed to notify admin {admin['user_id']}: {e}")

        return sent

    async def notify_super_admin(
        self,
        message: str,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Send notification to super admin.

        Returns:
            True if sent successfully
        """
        return await self.notify_user(
            config.bot.super_admin_id,
            message,
            parse_mode
        )

    async def send_payment_success(
        self,
        user_id: int,
        message: str,
        reply_markup=None
    ) -> bool:
        """Send payment success notification with account details."""
        return await self.notify_user(
            user_id,
            message,
            reply_markup=reply_markup
        )

    async def send_payment_expired(
        self,
        user_id: int,
        message: str,
        reply_markup=None
    ) -> bool:
        """Send payment expired notification."""
        return await self.notify_user(
            user_id,
            message,
            reply_markup=reply_markup
        )

    async def send_stock_alert(
        self,
        alert_message: str
    ) -> int:
        """
        Send stock alert to all admins.

        Returns:
            Number of admins notified
        """
        return await self.notify_admins(
            f"📦 **Stock Alert**\n\n{alert_message}"
        )

    async def broadcast_message(
        self,
        message: str,
        target: str = "all",
        media_type: str = "text",
        media_file_id: Optional[str] = None
    ) -> tuple:
        """
        Broadcast message to target audience.

        Args:
            message: Message text
            target: "all", "buyers", or "active_7days"
            media_type: "text", "photo", or "document"
            media_file_id: File ID for photo/document

        Returns:
            Tuple of (sent_count, failed_count)
        """
        users = await self.db.get_users_by_filter(target)

        sent = 0
        failed = 0

        for user in users:
            try:
                if media_type == "photo" and media_file_id:
                    await self.bot.send_photo(
                        chat_id=user["user_id"],
                        photo=media_file_id,
                        caption=message,
                        parse_mode="Markdown"
                    )
                elif media_type == "document" and media_file_id:
                    await self.bot.send_document(
                        chat_id=user["user_id"],
                        document=media_file_id,
                        caption=message,
                        parse_mode="Markdown"
                    )
                else:
                    await self.bot.send_message(
                        chat_id=user["user_id"],
                        text=message,
                        parse_mode="Markdown"
                    )
                sent += 1

            except TelegramError as e:
                logger.debug(f"Failed to send broadcast to {user['user_id']}: {e}")
                failed += 1

        logger.info(f"Broadcast completed: sent={sent}, failed={failed}")
        return sent, failed

    async def send_refund_notification(
        self,
        user_id: int,
        approved: bool,
        reason: Optional[str] = None
    ) -> bool:
        """Send refund status notification to user."""
        if approved:
            message = (
                "✅ **Refund Approved!**\n\n"
                "Permintaan refund kamu telah disetujui. "
                "Dana akan dikembalikan dalam 1-3 hari kerja."
            )
        else:
            message = (
                "❌ **Refund Ditolak**\n\n"
                f"Alasan: {reason or 'Tidak memenuhi syarat refund.'}\n\n"
                f"Jika ada pertanyaan, hubungi @{config.bot.support_username}"
            )

        return await self.notify_user(user_id, message)
