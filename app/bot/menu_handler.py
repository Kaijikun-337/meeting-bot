from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.config import Config
from app.bot.keyboards import MENU_BUTTONS


def is_admin(chat_id: str) -> bool:
    return str(chat_id) == str(Config.ADMIN_CHAT_ID)


def is_menu_button(text: str) -> bool:
    """Check if text is a menu button."""
    return text in MENU_BUTTONS


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from menu buttons."""
    text = update.message.text
    chat_id = str(update.effective_chat.id)
    
    # Not a menu button - ignore
    if not is_menu_button(text):
        return None
    
    # Import handlers here to avoid circular imports
    from app.bot.schedule import schedule_command, today_command
    from app.bot.handlers import status_command, help_command
    from app.bot.admin import list_users_command, new_student_command, new_teacher_command
    from app.bot.payment import pay_command
    from app.bot.change_lesson import change_command
    
    # Route to correct handler
    if text == "📅 Schedule":
        return await schedule_command(update, context)
    
    elif text == "📅 Today":
        return await today_command(update, context)
    
    elif text == "📋 Status":
        return await status_command(update, context)
    
    elif text == "❓ Help":
        return await help_command(update, context)
    
    elif text == "👥 Users" and is_admin(chat_id):
        return await list_users_command(update, context)
    
    elif text == "✏️ Change Lesson":
        return await change_command(update, context)
    
    elif text == "💰 Pay":
        return await pay_command(update, context)
    
    elif text == "👤 New Student" and is_admin(chat_id):
        return await new_student_command(update, context)
    
    elif text == "👤 New Teacher" and is_admin(chat_id):
        return await new_teacher_command(update, context)
    
    return None


async def cancel_on_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current conversation when menu button is pressed."""
    text = update.message.text
    
    if is_menu_button(text):
        await update.message.reply_text("❌ Previous action cancelled.")
        # Handle the new menu button
        await handle_menu_buttons(update, context)
        return ConversationHandler.END
    
    return None