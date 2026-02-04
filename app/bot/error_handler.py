import logging
import traceback
import html
import json
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
# Import specific error types to filter them out
from telegram.error import Conflict, NetworkError, BadRequest, TimedOut

from app.config import Config

# Setup professional logging
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all errors, filter noise, and report critical bugs to admin."""
    
    # 1. FILTER OUT NOISE (Don't spam Admin for these)
    # ------------------------------------------------
    if isinstance(context.error, Conflict):
        # Happens during Render deployment (Old bot vs New bot fighting)
        logger.warning("⚠️ Conflict Error: Deployment overlap detected. Ignoring.")
        return
    
    if isinstance(context.error, NetworkError):
        # Happens if Render loses connection to Telegram momentarily
        logger.warning(f"⚠️ Network Error: {context.error}")
        return

    if isinstance(context.error, TimedOut):
        # Telegram API was slow to respond
        logger.warning("⚠️ Telegram TimedOut. Ignoring.")
        return

    # 2. LOG CRITICAL ERRORS
    # ------------------------------------------------
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # 3. GATHER DEBUG INFO
    # ------------------------------------------------
    error = context.error
    error_message = str(error)
    # Limit traceback to last 3000 chars to fit in Telegram message
    tb_list = traceback.format_exception(None, error, error.__traceback__)
    tb_string = ''.join(tb_list)[-3000:]
    
    user_info = "Unknown"
    chat_info = "Unknown"
    update_info = "No update object"
    
    # Check if update exists (JobQueue errors don't have an update)
    if isinstance(update, Update):
        if update.effective_user:
            user_info = f"{update.effective_user.full_name} (ID: {update.effective_user.id})"
        if update.effective_chat:
            chat_info = f"{update.effective_chat.type} (ID: {update.effective_chat.id})"
        
        if update.message:
            update_info = f"Message: {update.message.text}"
        elif update.callback_query:
            update_info = f"Callback: {update.callback_query.data}"
        elif update.inline_query:
            update_info = f"Inline: {update.inline_query.query}"

    # 4. SEND REPORT TO ADMIN
    # ------------------------------------------------
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = (
        f"🚨 <b>Error Report</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🕐 <b>Time:</b> {timestamp}\n"
        f"👤 <b>User:</b> {html.escape(user_info)}\n"
        f"💬 <b>Chat:</b> {chat_info}\n"
        f"📝 <b>Update:</b> {html.escape(update_info)}\n\n"
        f"❌ <b>Error:</b>\n"
        f"<code>{html.escape(error_message)}</code>\n\n"
        f"📋 <b>Traceback:</b>\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    
    if Config.ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=Config.ADMIN_CHAT_ID,
                text=report,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send error report to Admin: {e}")

    # 5. NOTIFY USER (Politely)
    # ------------------------------------------------
    if isinstance(update, Update) and update.effective_chat:
        user_message = "😕 Oops! Something went wrong. The developers have been notified."
        
        try:
            # If the error happened on a Button Click, stop the spinner!
            if update.callback_query:
                await update.callback_query.answer(user_message, show_alert=True)
            # Otherwise send a text message
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=user_message
                )
        except Exception:
            # If we can't even tell the user (e.g., they blocked the bot), just ignore it.
            pass
        