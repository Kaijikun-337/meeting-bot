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
from app.services.user_service import get_user, get_teacher_groups
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
            f"📚 Groups: {group_text}\n\n"
            f"<b>Commands:</b>\n"
            f"/schedule - View weekly schedule\n"
            f"/today - View today's lessons\n"
            f"/change - Postpone or cancel lesson",
            parse_mode='HTML'
        )
    else:
        group = user.get('group_name', 'Not assigned')
        
        await update.message.reply_text(
            f"📋 <b>Your Status</b>\n\n"
            f"👤 Name: {name}\n"
            f"🎭 Role: {role}\n"
            f"📚 Group: {group}\n\n"
            f"<b>Commands:</b>\n"
            f"/schedule - View weekly schedule\n"
            f"/today - View today's lessons\n"
            f"/change - Request lesson change\n"
            f"/pay - Submit payment",
            parse_mode='HTML'
        )


async def help_command(update: Update, context):
    """Show help."""
    chat_id = str(update.effective_chat.id)
    
    admin_commands = ""
    if str(chat_id) == str(Config.ADMIN_CHAT_ID):
        admin_commands = (
            "\n<b>Admin Commands:</b>\n"
            "/new_student - Add new student\n"
            "/new_teacher - Add new teacher\n"
            "/users - List all users\n"
        )
    
    await update.message.reply_text(
        "🤖 <b>Meeting Bot Help</b>\n\n"
        "<b>Commands:</b>\n"
        "/start - Register with key\n"
        "/schedule - View weekly schedule 📅\n"
        "/today - View today's lessons\n"
        "/change - Postpone or cancel a lesson\n"
        "/pay - Submit a payment 💰\n"
        "/status - View your status\n"
        "/help - Show this help"
        f"{admin_commands}",
        parse_mode='HTML'
    )


def create_bot_application() -> Application:
    """Create and configure the bot application."""
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Registration conversation (key-based)
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
        ENTERING_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, key_entered)]
    },
    fallbacks=[
        CommandHandler('cancel', cancel_registration),
        CommandHandler('new_student', cancel_registration),
        CommandHandler('new_teacher', cancel_registration),
        CommandHandler('users', cancel_registration),
        CommandHandler('schedule', cancel_registration),
        CommandHandler('today', cancel_registration),
        CommandHandler('change', cancel_registration),
        CommandHandler('pay', cancel_registration),
        CommandHandler('status', cancel_registration),
        CommandHandler('help', cancel_registration),
    ],
    per_message=False
)
    
    # Admin: New student
    new_student_handler = ConversationHandler(
        entry_points=[CommandHandler('new_student', new_student_command)],
        states={
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_entered_admin)],
            ADMIN_ENTERING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_entered_admin)]
        },
        fallbacks=[CommandHandler('cancel', cancel_admin)],
        per_message=False
    )
    
    # Admin: New teacher
    new_teacher_handler = ConversationHandler(
        entry_points=[CommandHandler('new_teacher', new_teacher_command)],
        states={
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_entered_admin)],
            ADMIN_ENTERING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_entered_admin)],
            ADMIN_ENTERING_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, subject_entered_admin)],
            ADDING_MORE_GROUPS: [CallbackQueryHandler(admin_group_decision, pattern=r'^admin_')]
        },
        fallbacks=[CommandHandler('cancel', cancel_admin)],
        per_message=False
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
        per_message=False
    )
    
    # Payment conversation
    # Payment conversation
    payment_handler = ConversationHandler(
        entry_points=[CommandHandler('pay', pay_command)],
        states={
            SELECTING_COURSE: [CallbackQueryHandler(course_selected, pattern=r'^(course_|payment_)')],
            ENTERING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_entered)],
            UPLOADING_PHOTO: [MessageHandler(filters.PHOTO, photo_uploaded)],
            PAYMENT_CONFIRMING: [CallbackQueryHandler(payment_confirm, pattern=r'^payment_')]
        },
    fallbacks=[
        CommandHandler('cancel', cancel_payment),
        MessageHandler(filters.COMMAND, cancel_payment)
    ],
    per_message=False
)
    
    # Add handlers
    app.add_handler(registration_handler)
    app.add_handler(new_student_handler)
    app.add_handler(new_teacher_handler)
    app.add_handler(change_handler)
    app.add_handler(payment_handler)
    app.add_handler(CommandHandler('schedule', schedule_command))
    app.add_handler(CommandHandler('today', today_command))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('users', list_users_command))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(handle_approval, pattern=r'^(approve_|reject_)'))
    app.add_handler(CallbackQueryHandler(schedule_navigation, pattern=r'^schedule_'))
    app.add_handler(CallbackQueryHandler(admin_payment_decision, pattern=r'^admin_(confirm|reject)_'))
    
    return app