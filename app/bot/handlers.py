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
    date_selected, back_to_dates,
    SELECTING_LESSON, SELECTING_CHANGE_TYPE, 
    CONFIRMING, SELECTING_NEW_DATE, SELECTING_NEW_TIME
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
    group_entered_admin, list_users_command, cancel_admin,
    delete_user_command, delete_user_chat_entered, delete_user_confirm,
    edit_student_command, edit_user_chat_entered, edit_student_name, edit_student_group,
    edit_teacher_command, edit_teacher_chat_entered, edit_teacher_name_step,
    edit_teacher_group_step, edit_teacher_subject_step,
    ENTERING_NAME, ENTERING_GROUP as ADMIN_ENTERING_GROUP,
    EDIT_USER_CHAT, EDIT_STUDENT_NAME, EDIT_STUDENT_GROUP,
    EDIT_TEACHER_NAME, EDIT_TEACHER_GROUP, EDIT_TEACHER_SUBJECT,
    DELETE_USER_CHAT, DELETE_USER_CONFIRM
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

admin_text_filter = (
    filters.TEXT
    & ~filters.Regex('^/cancel')
    & ~menu_button_filter
)


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
    
    # NEW: If teacher, show list of groups from the separate table
    if user['role'] == 'teacher':
        groups = get_teacher_groups(chat_id)
        if groups:
            # Format: "Group A (Math), Group B (Physics)"
            group_list = []
            for g in groups:
                g_name = g['group_name']
                subj = g.get('subject')
                if subj:
                    group_list.append(f"{g_name} ({subj})")
                else:
                    group_list.append(g_name)
            
            groups_str = ", ".join(group_list)
            lines.append(f"📚 {get_text('status_teaching_groups', lang)}: {groups_str}")
            
    # If student, show their single group
    elif user.get('group_name'):
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
# REGISTER HANDLERS FUNCTION
# ═══════════════════════════════════════════════════════════

def register_handlers(app: Application):
    """Register all handlers to the bot application."""
    
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
            SELECTING_CHANGE_TYPE: [CallbackQueryHandler(change_type_selected),
                                    CallbackQueryHandler(cancel_change, pattern=r'^cancel_action$')
                                    ],
            
            SELECTING_NEW_TIME: [CallbackQueryHandler(back_to_dates, pattern=r'^resched_back$'),
                                 CallbackQueryHandler(slot_selected, pattern=r'^reschedule_'),
                                 CallbackQueryHandler(cancel_change, pattern=r'^cancel_action$')],
            
            SELECTING_NEW_DATE: [CallbackQueryHandler(date_selected, pattern=r'^resched_date_'),
                                 CallbackQueryHandler(cancel_change, pattern=r'^cancel_action$')],
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
    
    edit_student_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_student', edit_student_command)],
        states={
            EDIT_USER_CHAT: [
                MessageHandler(admin_text_filter, edit_user_chat_entered)
            ],
            EDIT_STUDENT_NAME: [
                MessageHandler(admin_text_filter, edit_student_name)
            ],
            EDIT_STUDENT_GROUP: [
                MessageHandler(admin_text_filter, edit_student_group)
            ],
        },
        fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_admin)],
        per_message=False
    )

    # Edit teacher conversation
    edit_teacher_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_teacher', edit_teacher_command)],
        states={
            EDIT_USER_CHAT: [
                MessageHandler(admin_text_filter, edit_teacher_chat_entered)
            ],
            EDIT_TEACHER_NAME: [
                MessageHandler(admin_text_filter, edit_teacher_name_step)
            ],
            EDIT_TEACHER_GROUP: [
                MessageHandler(admin_text_filter, edit_teacher_group_step)
            ],
            EDIT_TEACHER_SUBJECT: [
                MessageHandler(admin_text_filter, edit_teacher_subject_step)
            ],
        },
        fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_admin)],
        per_message=False
    )

    # Delete user conversation
    delete_user_handler = ConversationHandler(
            entry_points=[CommandHandler('delete_user', delete_user_command)],
            states={
                DELETE_USER_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, delete_user_chat_entered)],
                DELETE_USER_CONFIRM: [CallbackQueryHandler(delete_user_confirm, pattern=r'^deluser_')]
            },
            fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_admin)],
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
    app.add_handler(edit_student_handler)
    app.add_handler(edit_teacher_handler)
    app.add_handler(delete_user_handler)
    
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


# Legacy support if main.py wasn't updated to use register_handlers directly
def create_bot_application() -> Application:
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    register_handlers(app)
    return app