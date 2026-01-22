from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.services.user_service import activate_user, is_registered, get_user
from app.config import Config
from app.bot.keyboards import main_menu_keyboard

# States
ENTERING_KEY = 0


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = str(update.effective_chat.id)
    
    # Check if admin
    if str(chat_id) == str(Config.ADMIN_CHAT_ID):
        await update.message.reply_text(
            "👋 <b>Welcome, Admin!</b>\n\n"
            "Use the menu below to navigate.",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(is_admin=True)
        )
        return ConversationHandler.END
    
    # Check if already registered
    if is_registered(chat_id):
        user = get_user(chat_id)
        await update.message.reply_text(
            f"👋 Welcome back, <b>{user['name']}</b>!\n\n"
            "Use the menu below to navigate.",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(is_admin=False)
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "👋 <b>Welcome to Meeting Bot!</b>\n\n"
        "Please enter your <b>registration key</b>:\n\n"
        "<i>Format: STU-XXXXXX or TCH-XXXXXX</i>\n\n"
        "Don't have a key? Contact your administrator.",
        parse_mode='HTML'
    )
    
    return ENTERING_KEY


async def key_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle registration key input."""
    text = update.message.text.strip()
    
    # Ignore if it looks like a command
    if text.startswith('/'):
        await update.message.reply_text(
            "❌ Registration cancelled.\n\n"
            "Use /start to try again."
        )
        return ConversationHandler.END
    
    key = text.upper()
    chat_id = str(update.effective_chat.id)
    
    # Validate key format
    if not (key.startswith("STU-") or key.startswith("TCH-")):
        await update.message.reply_text(
            "❌ Invalid key format.\n\n"
            "Keys look like: <code>STU-ABC123</code> or <code>TCH-XYZ789</code>\n\n"
            "Please try again or /cancel:",
            parse_mode='HTML'
        )
        return ENTERING_KEY
    
    # Try to activate
    result = activate_user(chat_id, key)
    
    if result.get("error"):
        error = result["error"]
        
        if error == "invalid_key":
            await update.message.reply_text(
                "❌ <b>Invalid key.</b>\n\n"
                "This key doesn't exist.\n"
                "Please check and try again:",
                parse_mode='HTML'
            )
            return ENTERING_KEY
        
        elif error == "key_already_used":
            await update.message.reply_text(
                "❌ <b>Key already used.</b>\n\n"
                "This key has been used by another account.\n"
                "Contact your administrator for a new key.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        elif error == "already_registered":
            await update.message.reply_text(
                "❌ <b>Already registered.</b>\n\n"
                "You already have an active account.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        else:
            await update.message.reply_text(f"❌ Error: {error}")
            return ConversationHandler.END
    
    # Success!
    # Find the success part and update:

    # Success!
    name = result['name']
    role = result['role']
    group = result.get('group_name', '')
    
    role_icon = "👨‍🏫" if role == "teacher" else "👨‍🎓"
    
    await update.message.reply_text(
        f"✅ <b>Registration Successful!</b>\n\n"
        f"{role_icon} Welcome, <b>{name}</b>!\n"
        f"Role: {role.capitalize()}\n"
        f"{'Group: ' + group if group else ''}\n\n"
        f"Use the menu below to navigate.",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard(is_admin=False)
    )
    
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration."""
    await update.message.reply_text(
        "❌ Registration cancelled.\n"
        "Use /start to try again."
    )
    return ConversationHandler.END