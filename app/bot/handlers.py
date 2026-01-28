from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from app.bot.registration import (
    start_command, key_entered, cancel_registration,
    ENTERING_KEY
)
from app.bot.change_lesson import (
    change_command, lesson_selected, change_type_selected,
    confirm_action, handle_approval, cancel_change, slot_selected,
    SELECTING_LESSON, SELECTING_CHANGE_TYPE, SELECTING_SLOT,
    CONFIRMING
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
from app.bot.menu_handler import handle_menu_buttons, cancel_on_menu_button, is_button
from app.bot.keyboards import main_menu_keyboard, MENU_BUTTONS
from app.services.user_service import get_user, get_teacher_groups
from app.config import Config
from app.bot.availability import get_availability_conversation_handler
from app.bot.language import register_language_handlers
from app.bot.error_handler import error_handler
from app.utils.localization import get_text, get_user_language
from app.bot.homework import get_homework_conversation_handler


# ═══════════════════════════════════════════════════════════
# MULTILINGUAL BUTTON FILTERS
# ═══════════════════════════════════════════════════════════

class ChangeLessonButtonFilter(filters.MessageFilter):
    """Matches Change Lesson button in any language."""
    def filter(self, message):
        if message.text:
            return is_button(message.text, 'btn_change_lesson')
        return False


class PayButtonFilter(filters.MessageFilter):
    """Matches Pay button in any language."""
    def filter(self, message):
        if message.text:
            return is_button(message.text, 'btn_pay')
        return False

class StatusButtonFilter(filters.MessageFilter):
    """Matches Status button in any language."""
    def filter(self, message):
        if message.text:
            return is_button(message.text, 'btn_status')
        return False


class AvailabilityButtonFilter(filters.MessageFilter):
    """Matches Availability button in any language."""
    def filter(self, message):
        if message.text:
            return is_button(message.text, 'btn_availability')
        return False

# Create filter instances
change_lesson_button = ChangeLessonButtonFilter()
pay_button = PayButtonFilter()
status_button = StatusButtonFilter()
availability_button = AvailabilityButtonFilter()

# Filter for menu buttons
menu_button_filter = filters.TEXT & filters.Regex(f'^({"|".join(MENU_BUTTONS)})$')


# ═══════════════════════════════════════════════════════════
# SIMPLE COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user status."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    user = get_user(chat_id)
    
    if not user:
        await update.message.reply_text(get_text('not_registered', lang))
        return
    
    role_key = 'role_teacher' if user['role'] == 'teacher' else 'role_student'
    
    lines = [
        f"<b>{get_text('your_status', lang)}</b>",
        "",
        f"👤 {get_text('status_name', lang)}: {user['name']}",
        f"🎭 {get_text('status_role', lang)}: {get_text(role_key, lang)}",
    ]
    
    if user.get('group_name'):
        lines.append(f"👥 {get_text('status_group', lang)}: {user['group_name']}")
    
    if user.get('activated_at'):
        lines.append(f"📅 {get_text('status_registered', lang)}: {user['activated_at'][:10]}")
    
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    chat_id = str(update.effective_user.id)
    lang = get_user_language(chat_id)
    
    lines = [
        f"<b>{get_text('help_title', lang)}</b>",
        "",
        get_text('help_schedule', lang),
        get_text('help_today', lang),
        get_text('help_change', lang),
        get_text('help_pay', lang),
        get_text('help_status', lang),
        get_text('help_language', lang),
        get_text('help_availability', lang),
    ]
    
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode='HTML'
    )


# ═══════════════════════════════════════════════════════════
# CREATE BOT APPLICATION
# ═══════════════════════════════════════════════════════════

def create_bot_application() -> Application:
    """Create and configure the bot application."""
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Common fallbacks for all conversations
    common_fallbacks = [
        CommandHandler('cancel', cancel_registration),
        MessageHandler(menu_button_filter, cancel_on_menu_button)
    ]
    
    # ═══════════════════════════════════════════════════════════
    # CONVERSATION HANDLERS
    # ═══════════════════════════════════════════════════════════
    
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
            MessageHandler(change_lesson_button, change_command)
        ],
        states={
            SELECTING_LESSON: [CallbackQueryHandler(lesson_selected)],
            SELECTING_CHANGE_TYPE: [CallbackQueryHandler(change_type_selected)],
            SELECTING_SLOT: [CallbackQueryHandler(slot_selected)],
            CONFIRMING: [CallbackQueryHandler(confirm_action)]
        },
        fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_change)],
        per_message=False
    )
    
    # Payment conversation
    payment_handler = ConversationHandler(
        entry_points=[
            CommandHandler('pay', pay_command),
            MessageHandler(pay_button, pay_command)
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
    
    # ═══════════════════════════════════════════════════════════
    # REGISTER HANDLERS (order matters!)
    # ═══════════════════════════════════════════════════════════
    
    # Conversation handlers first
    app.add_handler(registration_handler)
    app.add_handler(new_student_handler)
    app.add_handler(new_teacher_handler)
    app.add_handler(change_handler)
    app.add_handler(payment_handler)
    app.add_handler(get_availability_conversation_handler())
    app.add_handler(get_homework_conversation_handler())
    
    # Simple command handlers
    app.add_handler(CommandHandler('schedule', schedule_command))
    app.add_handler(CommandHandler('today', today_command))
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('users', list_users_command))
    
    # Language handlers
    register_language_handlers(app)
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(handle_approval, pattern=r'^(approve_|reject_)'))
    app.add_handler(CallbackQueryHandler(schedule_navigation, pattern=r'^schedule_'))
    app.add_handler(CallbackQueryHandler(admin_payment_decision, pattern=r'^admin_(confirm|reject)_'))
    
    # Menu button handler (catches remaining menu buttons)
    app.add_handler(MessageHandler(menu_button_filter, handle_menu_buttons))
    
    # Error handler (always last)
    app.add_error_handler(error_handler)
    
    return app