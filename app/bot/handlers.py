from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
from app.bot.registration import (
    start_command, role_chosen, name_entered, 
    group_chosen_student, group_chosen_teacher,
    done_adding_groups, cancel_registration,
    CHOOSING_ROLE, ENTERING_NAME, CHOOSING_GROUP, ADDING_GROUPS
)
from app.bot.change_lesson import (
    change_command, lesson_selected, change_type_selected,
    day_selected, hour_selected, minute_selected,
    confirm_action, handle_approval, cancel_change,
    SELECTING_LESSON, SELECTING_CHANGE_TYPE, SELECTING_DAY,
    SELECTING_HOUR, SELECTING_MINUTE, CONFIRMING
)
from app.services.user_service import get_user
from app.config import Config


async def status_command(update: Update, context):
    """Show user status."""
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    
    if not user:
        await update.message.reply_text(
            "❌ You're not registered.\n"
            "Use /start to register."
        )
        return
    
    # Build status message
    role = user['role'].capitalize()
    name = user['name']
    
    if user['role'] == 'teacher':
        # Get teacher's groups
        groups = get_teacher_groups(chat_id)
        if groups:
            group_names = [g['group_name'] for g in groups]
            group_text = ", ".join(group_names)
        else:
            group_text = "No groups assigned"
        
        await update.message.reply_text(
            f"📋 <b>Your Status</b>\n\n"
            f"👤 Name: {name}\n"
            f"🎭 Role: {role}\n"
            f"📚 Groups: {group_text}\n",
            parse_mode='HTML'
        )
    else:
        # Student
        group = user.get('group_name', 'Not assigned')
        
        await update.message.reply_text(
            f"📋 <b>Your Status</b>\n\n"
            f"👤 Name: {name}\n"
            f"🎭 Role: {role}\n"
            f"📚 Group: {group}\n",
            parse_mode='HTML'
        )


async def help_command(update: Update, context):
    """Show help."""
    await update.message.reply_text(
        "🤖 <b>Meeting Bot Help</b>\n\n"
        "<b>Commands:</b>\n"
        "/start - Register or restart\n"
        "/change - Postpone or cancel a lesson\n"
        "/status - View your status\n"
        "/help - Show this help\n\n"
        "<b>How it works:</b>\n"
        "1. Register as teacher or student\n"
        "2. Use /change to request lesson changes\n"
        "3. Approve or reject requests when asked\n"
        "4. Changes take effect after mutual approval",
        parse_mode='HTML'
    )


def create_bot_application() -> Application:
    """Create and configure the bot application."""
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Registration conversation
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            CHOOSING_ROLE: [CallbackQueryHandler(role_chosen, pattern=r'^role_')],
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_entered)],
            CHOOSING_GROUP: [CallbackQueryHandler(group_chosen_student, pattern=r'^group_')],
            ADDING_GROUPS: [
                CallbackQueryHandler(group_chosen_teacher, pattern=r'^group_'),
                CommandHandler('done', done_adding_groups)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_registration)],
        per_message=False  # Add this
    )
    
    # Change lesson conversation
    change_handler = ConversationHandler(
        entry_points=[CommandHandler('change', change_command)],
        states={
            SELECTING_LESSON: [CallbackQueryHandler(lesson_selected)],
            SELECTING_CHANGE_TYPE: [CallbackQueryHandler(change_type_selected)],
            SELECTING_DAY: [CallbackQueryHandler(day_selected)],
            SELECTING_HOUR: [CallbackQueryHandler(hour_selected)],
            SELECTING_MINUTE: [CallbackQueryHandler(minute_selected)],
            CONFIRMING: [CallbackQueryHandler(confirm_action)]
        },
        fallbacks=[CommandHandler('cancel', cancel_change)],
        per_message=False  # Add this
    )
    
    # Add handlers
    app.add_handler(registration_handler)
    app.add_handler(change_handler)
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('help', help_command))
    
    # Approval handler (works globally)
    app.add_handler(CallbackQueryHandler(handle_approval, pattern=r'^(approve_|reject_)'))
    
    return app