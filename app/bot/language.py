from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from app.utils.localization import (
    LANGUAGES, 
    get_text, 
    get_user_language, 
    set_user_language
)
from app.bot.keyboards import main_menu_keyboard, language_keyboard, unregistered_menu_keyboard


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
    from app.services.user_service import get_user
    from app.config import Config

    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_user.id)
    new_lang = query.data.replace("setlang_", "")
    
    if not set_user_language(chat_id, new_lang):
        await query.edit_message_text("❌ Failed to change language.")
        return

    # Send confirmation in the new language
    await query.edit_message_text(get_text('language_changed', new_lang))

    # Decide which keyboard to show
    user = get_user(chat_id)
    is_admin = (str(chat_id) == str(Config.ADMIN_CHAT_ID))
    
    if is_admin:
        # Admin full menu
        kb = main_menu_keyboard(is_admin=True, is_teacher=False, lang=new_lang)
    elif user:
        # Registered user: teacher or student
        is_teacher = (user['role'] == 'teacher')
        kb = main_menu_keyboard(is_admin=False, is_teacher=is_teacher, lang=new_lang)
    else:
        # Unregistered user: only Language button
        kb = unregistered_menu_keyboard(new_lang)

    # Refresh their reply keyboard
    await context.bot.send_message(
        chat_id=chat_id,
        text="⬇️",  
        reply_markup=kb
    )


def register_language_handlers(app):
    """Register language handlers."""
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^setlang_"))