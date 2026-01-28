import traceback
import html
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from app.config import Config


# Your Telegram chat ID (admin who receives error reports)
ADMIN_CHAT_ID = Config.ADMIN_CHAT_ID  # Add this to your config


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all errors and send report to admin."""
    
    # Get error details
    error = context.error
    error_message = str(error)
    error_traceback = ''.join(traceback.format_exception(None, error, error.__traceback__))
    
    # Get user info if available
    user_info = "Unknown"
    chat_info = "Unknown"
    update_info = "No update"
    
    if update:
        if update.effective_user:
            user_info = f"{update.effective_user.full_name} (ID: {update.effective_user.id})"
        if update.effective_chat:
            chat_info = f"{update.effective_chat.type} (ID: {update.effective_chat.id})"
        
        # Get the update that caused the error
        if update.message:
            update_info = f"Message: {update.message.text[:100] if update.message.text else 'No text'}"
        elif update.callback_query:
            update_info = f"Callback: {update.callback_query.data}"
    
    # Build error report
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
        f"<pre>{html.escape(error_traceback[-3000:])}</pre>"  # Limit traceback length
    )
    
    # Send to admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=report,
            parse_mode='HTML'
        )
    except Exception as e:
        # If can't send to admin, at least log it
        print(f"Failed to send error report: {e}")
        print(f"Original error: {error_message}")
        print(error_traceback)
    
    # Also log to console
    print(f"🚨 ERROR: {error_message}")
    print(error_traceback)
    
    # Optionally notify user that something went wrong
    if update and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="😕 Oops! Something went wrong. The admin has been notified."
            )
        except:
            pass