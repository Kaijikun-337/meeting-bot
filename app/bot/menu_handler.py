from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.config import Config
from app.utils.localization import get_text


def is_admin(chat_id: str) -> bool:
    return str(chat_id) == str(Config.ADMIN_CHAT_ID)


def is_button(text: str, button_key: str) -> bool:
    """Check if text matches a button in ANY language."""
    for lang in ['en', 'ru', 'uz']:
        if text == get_text(button_key, lang):
            return True
    return False


def is_menu_button(text: str) -> bool:
    """Check if text is any menu button in any language."""
    button_keys = [
        'btn_schedule', 'btn_today', 'btn_change_lesson', 'btn_pay',
        'btn_status', 'btn_help', 'btn_new_student', 'btn_new_teacher',
        'btn_users', 'btn_language', 'btn_availability', 'btn_homework'  # ← Added
    ]
    
    for key in button_keys:
        if is_button(text, key):
            return True
    return False


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
    from app.bot.language import language_command
    from app.bot.availability import availability_command
    
    # Route to correct handler based on button key
    if is_button(text, 'btn_schedule'):
        return await schedule_command(update, context)
    
    elif is_button(text, 'btn_today'):
        return await today_command(update, context)
    
    elif is_button(text, 'btn_status'):
        return await status_command(update, context)
    
    elif is_button(text, 'btn_help'):
        return await help_command(update, context)
    
    elif is_button(text, 'btn_users') and is_admin(chat_id):
        return await list_users_command(update, context)
    
    elif is_button(text, 'btn_change_lesson'):
        # Let ConversationHandler handle this
        return None
    
    elif is_button(text, 'btn_pay'):
        # Let ConversationHandler handle this
        return None
    
    elif is_button(text, 'btn_availability'):
        # Let ConversationHandler handle this
        return None

    elif is_button(text, 'btn_homework'):
    # Let ConversationHandler handle this
        return None
    
    elif is_button(text, 'btn_new_student') and is_admin(chat_id):
        return await new_student_command(update, context)
    
    elif is_button(text, 'btn_new_teacher') and is_admin(chat_id):
        return await new_teacher_command(update, context)
    
    elif is_button(text, 'btn_language'):
        return await language_command(update, context)
    
    return None


async def cancel_on_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current conversation when menu button is pressed."""
    from app.utils.localization import get_user_language
    
    text = update.message.text
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    
    if is_menu_button(text):
        await update.message.reply_text(get_text('cancelled', lang))
        # Handle the new menu button
        await handle_menu_buttons(update, context)
        return ConversationHandler.END
    
    return None