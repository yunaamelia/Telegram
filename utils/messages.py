"""
Message utilities for FRIENDS Store Telegram Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest


async def safe_edit_or_send(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    text: str,
    **kwargs
) -> None:
    """
    Safely edit message or send new one if edit fails.
    
    This handles the case where the original message was a photo
    (e.g., QRIS code) which cannot be edited to text.
    """
    try:
        await query.edit_message_text(text=text, **kwargs)
    except BadRequest as e:
        error_msg = str(e).lower()
        if "no text" in error_msg or "message to edit" in error_msg or "can't be edited" in error_msg:
            # Message is a photo or was deleted, delete and send new
            try:
                await query.message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                **kwargs
            )
        else:
            raise
