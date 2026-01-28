from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from app.utils.localization import (
    LANGUAGES, 
    get_text, 
    get_user_language, 
    set_user_language
)
from app.bot.keyboards import main_menu_keyboard, language_keyboard


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    await update.message.reply_text(
        get_text('choose_language', lang),
        reply_markup=language_keyboard()
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection."""
    # Import HERE at the top of function
    from app.services.user_service import get_user
    from app.config import Config
    from app.bot.keyboards import main_menu_keyboard
    
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    new_lang = query.data.replace("setlang_", "")
    
    if set_user_language(chat_id, new_lang):
        # Send confirmation
        await query.edit_message_text(
            get_text('language_changed', new_lang)
        )
        
        # Get user info for menu
        user = get_user(chat_id)
        is_admin = str(chat_id) == str(Config.ADMIN_CHAT_ID)
        is_teacher = (user['role'] == 'teacher') if user else False
        
        # Refresh the menu
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅",
            reply_markup=main_menu_keyboard(is_admin=is_admin, is_teacher=is_teacher, lang=new_lang)
        )
    else:
        await query.edit_message_text("❌ Failed to change language.")


def register_language_handlers(app):
    """Register language handlers."""
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^setlang_"))