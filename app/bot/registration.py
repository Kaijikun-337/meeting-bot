from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.services.user_service import activate_user, is_registered, get_user
from app.config import Config

# States
ENTERING_KEY = 0


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    chat_id = str(update.effective_chat.id)
    
    # Check if admin - no registration needed
    if str(chat_id) == str(Config.ADMIN_CHAT_ID):
        await update.message.reply_text(
            "👋 <b>Welcome, Admin!</b>\n\n"
            "<b>Admin Commands:</b>\n"
            "/new_student - Add new student\n"
            "/new_teacher - Add new teacher\n"
            "/users - List all users\n\n"
            "<b>Other Commands:</b>\n"
            "/schedule - View schedule\n"
            "/today - View today's lessons\n"
            "/help - Get help",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    # Check if already registered
    if is_registered(chat_id):
        user = get_user(chat_id)
        await update.message.reply_text(
            f"👋 Welcome back, <b>{user['name']}</b>!\n\n"
            "<b>Commands:</b>\n"
            "/schedule - View weekly schedule\n"
            "/today - View today's lessons\n"
            "/change - Postpone or cancel lesson\n"
            "/pay - Submit payment\n"
            "/status - Check your status\n"
            "/help - Get help",
            parse_mode='HTML'
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
    name = result['name']
    role = result['role']
    group = result.get('group_name', '')
    
    role_icon = "👨‍🏫" if role == "teacher" else "👨‍🎓"
    
    await update.message.reply_text(
        f"✅ <b>Registration Successful!</b>\n\n"
        f"{role_icon} Welcome, <b>{name}</b>!\n"
        f"Role: {role.capitalize()}\n"
        f"{'Group: ' + group if group else ''}\n\n"
        f"<b>Commands:</b>\n"
        f"/schedule - View weekly schedule\n"
        f"/today - View today's lessons\n"
        f"/change - Postpone or cancel lesson\n"
        f"/pay - Submit payment\n"
        f"/status - Check your status\n"
        f"/help - Get help",
        parse_mode='HTML'
    )
    
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration."""
    await update.message.reply_text(
        "❌ Registration cancelled.\n"
        "Use /start to try again."
    )
    return ConversationHandler.END