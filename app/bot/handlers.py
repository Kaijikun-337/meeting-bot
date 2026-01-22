from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
from app.bot.registration import (
    start_command, key_entered, cancel_registration,
    ENTERING_KEY
)
from app.bot.change_lesson import (
    change_command, lesson_selected, change_type_selected,
    day_selected, hour_selected, minute_selected,
    confirm_action, handle_approval, cancel_change,
    SELECTING_LESSON, SELECTING_CHANGE_TYPE, SELECTING_DAY,
    SELECTING_HOUR, SELECTING_MINUTE, CONFIRMING
)
from app.bot.schedule import (
    schedule_command, schedule_navigation, today_command
)
from app.bot.payment import (
    pay_command, course_selected, amount_entered, photo_uploaded,
    payment_confirm, admin_payment_decision, cancel_payment,
    SELECTING_COURSE, ENTERING_AMOUNT, UPLOADING_PHOTO, CONFIRMING as PAYMENT_CONFIRMING
)
from app.bot.admin import (
    new_student_command, new_teacher_command, name_entered_admin,
    group_entered_admin, subject_entered_admin, admin_group_decision,
    list_users_command, cancel_admin,
    ENTERING_NAME, ENTERING_GROUP as ADMIN_ENTERING_GROUP,
    ADDING_MORE_GROUPS, ENTERING_SUBJECT as ADMIN_ENTERING_SUBJECT
)
from app.bot.menu_handler import handle_menu_buttons, cancel_on_menu_button
from app.bot.keyboards import main_menu_keyboard, MENU_BUTTONS
from app.services.user_service import get_user, get_teacher_groups
from app.config import Config


# Filter for menu buttons
menu_button_filter = filters.TEXT & filters.Regex(f'^({"|".join(MENU_BUTTONS)})$')


async def status_command(update: Update, context):
    """Show user status."""
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    is_admin_user = str(chat_id) == str(Config.ADMIN_CHAT_ID)
    
    if not user and not is_admin_user:
        await update.message.reply_text(
            "❌ You're not registered.\n"
            "Use /start to register."
        )
        return
    
    if is_admin_user and not user:
        await update.message.reply_text(
            "📋 <b>Admin Status</b>\n\n"
            "You are the administrator.",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(is_admin=True)
        )
        return
    
    role = user['role'].capitalize()
    name = user['name']
    
    if user['role'] == 'teacher':
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
            f"📚 Groups: {group_text}",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(is_admin=is_admin_user)
        )
    else:
        group = user.get('group_name', 'Not assigned')
        
        await update.message.reply_text(
            f"📋 <b>Your Status</b>\n\n"
            f"👤 Name: {name}\n"
            f"🎭 Role: {role}\n"
            f"📚 Group: {group}",
            parse_mode='HTML',
            reply_markup=main_menu_keyboard(is_admin=is_admin_user)
        )


async def help_command(update: Update, context):
    """Show help."""
    chat_id = str(update.effective_chat.id)
    is_admin_user = str(chat_id) == str(Config.ADMIN_CHAT_ID)
    
    admin_commands = ""
    if is_admin_user:
        admin_commands = (
            "\n<b>Admin Commands:</b>\n"
            "👤 New Student - Add student\n"
            "👤 New Teacher - Add teacher\n"
            "👥 Users - List all users\n"
        )
    
    await update.message.reply_text(
        "🤖 <b>Meeting Bot Help</b>\n\n"
        "<b>Menu Buttons:</b>\n"
        "📅 Schedule - View weekly schedule\n"
        "📅 Today - View today's lessons\n"
        "✏️ Change Lesson - Postpone or cancel\n"
        "💰 Pay - Submit payment\n"
        "📋 Status - View your status\n"
        "❓ Help - Show this help"
        f"{admin_commands}",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard(is_admin=is_admin_user)
    )


def create_bot_application() -> Application:
    """Create and configure the bot application."""
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Common fallbacks for all conversations
    common_fallbacks = [
        CommandHandler('cancel', cancel_registration),
        MessageHandler(menu_button_filter, cancel_on_menu_button)
    ]
    
    # Registration conversation
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            ENTERING_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, key_entered)]
        },
        fallbacks=common_fallbacks,
        per_message=False
    )
    
    # Admin: New student
    new_student_handler = ConversationHandler(
        entry_points=[
            CommandHandler('new_student', new_student_command),
            MessageHandler(filters.Regex('^👤 New Student$'), new_student_command)
        ],
        states={
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, name_entered_admin)],
            ADMIN_ENTERING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, group_entered_admin)]
        },
        fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_admin)],
        per_message=False
    )
    
    # Admin: New teacher
    new_teacher_handler = ConversationHandler(
        entry_points=[
            CommandHandler('new_teacher', new_teacher_command),
            MessageHandler(filters.Regex('^👤 New Teacher$'), new_teacher_command)
        ],
        states={
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, name_entered_admin)],
            ADMIN_ENTERING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, group_entered_admin)],
            ADMIN_ENTERING_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, subject_entered_admin)],
            ADDING_MORE_GROUPS: [CallbackQueryHandler(admin_group_decision, pattern=r'^admin_')]
        },
        fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_admin)],
        per_message=False
    )
    
    # Change lesson conversation
    change_handler = ConversationHandler(
        entry_points=[
            CommandHandler('change', change_command),
            MessageHandler(filters.Regex('^✏️ Change Lesson$'), change_command)
        ],
        states={
            SELECTING_LESSON: [CallbackQueryHandler(lesson_selected)],
            SELECTING_CHANGE_TYPE: [CallbackQueryHandler(change_type_selected)],
            SELECTING_DAY: [CallbackQueryHandler(day_selected)],
            SELECTING_HOUR: [CallbackQueryHandler(hour_selected)],
            SELECTING_MINUTE: [CallbackQueryHandler(minute_selected)],
            CONFIRMING: [CallbackQueryHandler(confirm_action)]
        },
        fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_change)],
        per_message=False
    )
    
    # Payment conversation
    payment_handler = ConversationHandler(
        entry_points=[
            CommandHandler('pay', pay_command),
            MessageHandler(filters.Regex('^💰 Pay$'), pay_command)
        ],
        states={
            SELECTING_COURSE: [CallbackQueryHandler(course_selected, pattern=r'^(course_|payment_)')],
            ENTERING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, amount_entered)],
            UPLOADING_PHOTO: [MessageHandler(filters.PHOTO, photo_uploaded)],
            PAYMENT_CONFIRMING: [CallbackQueryHandler(payment_confirm, pattern=r'^payment_')]
        },
        fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_payment)],
        per_message=False
    )
    
    # Add handlers (order matters!)
    app.add_handler(registration_handler)
    app.add_handler(new_student_handler)
    app.add_handler(new_teacher_handler)
    app.add_handler(change_handler)
    app.add_handler(payment_handler)
    
    # Simple command handlers
    app.add_handler(CommandHandler('schedule', schedule_command))
    app.add_handler(CommandHandler('today', today_command))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('users', list_users_command))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(handle_approval, pattern=r'^(approve_|reject_)'))
    app.add_handler(CallbackQueryHandler(schedule_navigation, pattern=r'^schedule_'))
    app.add_handler(CallbackQueryHandler(admin_payment_decision, pattern=r'^admin_(confirm|reject)_'))
    
    # Menu button handler (catches remaining menu buttons)
    app.add_handler(MessageHandler(menu_button_filter, handle_menu_buttons))
    
    return app