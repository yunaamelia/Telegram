"""
Loading states and animation helpers for better UX.
"""

import asyncio
from typing import Optional, Callable, Any
from telegram import Update, Message
from telegram.ext import ContextTypes


class LoadingStates:
    """Handle loading states and animations."""

    LOADING_FRAMES = [
        "⏳ Loading.",
        "⏳ Loading..",
        "⏳ Loading...",
    ]

    PROCESSING_FRAMES = [
        "🔄 Processing.",
        "🔄 Processing..",
        "🔄 Processing...",
    ]

    SAVING_FRAMES = [
        "💾 Saving.",
        "💾 Saving..",
        "💾 Saving...",
    ]

    @staticmethod
    async def show_loading(
        message: Message,
        text: str = "Loading",
        duration: float = 1.5
    ) -> Message:
        """
        Show animated loading indicator.

        Args:
            message: Message to edit
            text: Loading text
            duration: How long to show (seconds)

        Returns:
            Final message object
        """
        frames = LoadingStates.LOADING_FRAMES
        frame_duration = duration / len(frames)

        for frame in frames:
            try:
                await message.edit_text(f"{frame}")
                await asyncio.sleep(frame_duration)
            except Exception:
                pass

        return message

    @staticmethod
    async def with_loading(
        query,
        async_func: Callable,
        loading_text: str = "Loading",
        *args,
        **kwargs
    ) -> Any:
        """
        Execute async function with loading indicator.

        Usage:
            result = await LoadingStates.with_loading(
                query,
                database.get_products,
                "Fetching products"
            )
        """
        # Show loading
        await query.edit_message_text(f"⏳ {loading_text}...")

        # Execute function
        result = await async_func(*args, **kwargs)
        return result

    @staticmethod
    async def typing_indicator(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show typing indicator (native Telegram feature)."""
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

    @staticmethod
    async def upload_indicator(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show upload indicator for file operations."""
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="upload_document"
        )

    @staticmethod
    def simple_loading(text: str = "Loading") -> str:
        """Return simple loading text (no animation)."""
        return f"⏳ {text}..."

    @staticmethod
    def simple_processing(text: str = "Processing") -> str:
        """Return simple processing text."""
        return f"🔄 {text}..."

    @staticmethod
    def simple_saving(text: str = "Saving") -> str:
        """Return simple saving text."""
        return f"💾 {text}..."

    @staticmethod
    async def show_progress(
        message: Message,
        current: int,
        total: int,
        text: str = "Processing"
    ) -> Message:
        """
        Show progress indicator.

        Args:
            message: Message to edit
            current: Current item number
            total: Total items
            text: Progress text

        Returns:
            Updated message object
        """
        percentage = int((current / total) * 100) if total > 0 else 0
        bar_width = 10
        filled = int((percentage / 100) * bar_width)
        empty = bar_width - filled
        bar = '█' * filled + '░' * empty

        progress_text = f"🔄 {text}\n[{bar}] {percentage}%\n{current}/{total}"

        try:
            await message.edit_text(progress_text)
        except Exception:
            pass

        return message


class LoadingContext:
    """Context manager for loading states."""

    def __init__(
        self,
        query,
        loading_text: str = "Loading",
        success_callback: Optional[Callable] = None
    ):
        self.query = query
        self.loading_text = loading_text
        self.success_callback = success_callback

    async def __aenter__(self):
        """Show loading on enter."""
        await self.query.edit_message_text(f"⏳ {self.loading_text}...")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Handle exit - success callback if no exception."""
        if exc_type is None and self.success_callback:
            await self.success_callback()
        return False


# Shorthand alias
loading = LoadingStates
