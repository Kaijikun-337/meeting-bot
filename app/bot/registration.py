from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.services.user_service import activate_user, is_registered, get_user
from app.config import Config
from app.bot.keyboards import main_menu_keyboard
from app.utils.localization import get_user_language, get_text

# States
ENTERING_KEY = 0


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = str(update.effective_chat.id)
    lang = get_user_language(chat_id)
    
    # Check if admin
    if str(chat_id) == str(Config.ADMIN_CHAT_ID):
        await update.message.reply_text(
            get_text('admin_welcome', lang),
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(is_admin=True)
        )
        return ConversationHandler.END
    
    # Check if already registered
    if is_registered(chat_id):
        user = get_user(chat_id)
        is_teacher = (user['role'] == 'teacher')
        await update.message.reply_text(
            get_text('already_registered', lang),
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(is_admin=False, is_teacher=is_teacher, lang=lang)
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        get_text('start_welcome', lang),
        parse_mode='HTML'
    )
    
    return ENTERING_KEY


async def key_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle registration key input."""
    text = update.message.text.strip()
    lang = get_user_language(str(update.effective_chat.id))
    
    # Ignore if it looks like a command
    if text.startswith('/'):
        await update.message.reply_text(get_text('registration_cancelled', lang))
        return ConversationHandler.END
    
    key = text.upper()
    chat_id = str(update.effective_chat.id)
    
    # Validate key format
    if not (key.startswith("STU-") or key.startswith("TCH-")):
        await update.message.reply_text(
            get_text('invalid_key_format', lang),
            parse_mode='HTML'
        )
        return ENTERING_KEY
    
    # Try to activate
    result = activate_user(chat_id, key)
    
    if result.get("error"):
        error = result["error"]
        
        if error == "invalid_key":
            await update.message.reply_text(
                get_text('invalid_key', lang),
                parse_mode='HTML'
            )
            return ENTERING_KEY
        
        elif error == "key_already_used":
            await update.message.reply_text(
                get_text('key_already_used', lang),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        elif error == "already_registered":
            await update.message.reply_text(
                get_text('already_registered', lang),
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        else:
            await update.message.reply_text(f"❌ Error: {error}")
            return ConversationHandler.END
    
    # Success!
    name = result['name']
    role = result['role']
    group = result.get('group_name', '')
    
    role_text = get_text('role_teacher', lang) if role == 'teacher' else get_text('role_student', lang)
    role_icon = "👨‍🏫" if role == "teacher" else "👨‍🎓"
    
    group_text = f"\n{get_text('status_group', lang)}: {group}" if group else ""
    
    msg = get_text('registration_success', lang).format(
        icon=role_icon,
        name=name,
        role=role_text,
        group=group_text
    )
    
    is_teacher = (role == 'teacher')  # Check role

    await update.message.reply_text(
        msg,
        parse_mode='HTML',
        reply_markup=main_menu_keyboard(is_admin=False, is_teacher=is_teacher, lang=lang)
    )
    
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration."""
    lang = get_user_language(str(update.effective_chat.id))
    await update.message.reply_text(get_text('registration_cancelled', lang))
    return ConversationHandler.END