from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from app.bot.registration import (
    start_command, key_entered, cancel_registration,
    ENTERING_KEY
)
from app.bot.schedule import (
    schedule_command, schedule_navigation, today_command
)
from app.bot.admin import (
    new_student_command, new_teacher_command, name_entered_admin,
    group_entered_admin, list_users_command, cancel_admin,
    delete_user_command, delete_user_chat_entered, delete_user_confirm,
    edit_student_command, edit_user_chat_entered, edit_student_name, edit_student_group,
    edit_teacher_command, edit_teacher_chat_entered, edit_teacher_name_step,
    edit_teacher_group_step, edit_teacher_subject_step,
    ENTERING_GROUP as ADMIN_ENTERING_GROUP,
    EDIT_USER_CHAT, EDIT_STUDENT_NAME, EDIT_STUDENT_GROUP,
    EDIT_TEACHER_NAME, EDIT_TEACHER_GROUP, EDIT_TEACHER_SUBJECT,
    DELETE_USER_CHAT, DELETE_USER_CONFIRM, ENTERING_NAME_STUDENT,
    ENTERING_NAME_TEACHER
)

from app.bot.menu_handler import handle_menu_buttons, cancel_on_menu_button, is_button
from app.bot.keyboards import MENU_BUTTONS
from app.services.user_service import get_user, get_teacher_groups
from app.config import Config
from app.bot.language import register_language_handlers
from app.bot.error_handler import error_handler
from app.utils.localization import get_text, get_user_language
from app.bot.homework import get_homework_conversation_handler
from app.bot.attendance import start_attendance, toggle_student, submit_attendance
from app.bot.admin import check_attendance_command

# ═══════════════════════════════════════════════════════════
# MULTILINGUAL BUTTON FILTERS
# ═══════════════════════════════════════════════════════════

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

# Create filter instances
pay_button = PayButtonFilter()
status_button = StatusButtonFilter()

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
    
    # ✅ Handle all three roles
    if user['role'] == 'teacher':
        role_key = 'role_teacher'
    else:
        role_key = 'role_student'
    
    role_icon = ("👨‍🏫" if user['role'] == 'teacher' else "👨‍🎓")
    
    lines = [
        f"<b>{get_text('your_status', lang)}</b>",
        "",
        f"👤 {get_text('status_name', lang)}: {user['name']}",
        f"{role_icon} {get_text('status_role', lang)}: {get_text(role_key, lang)}",
    ]
    
    # Teacher-specific info
    if user['role'] == 'teacher':
        from app.services.user_service import get_teacher_groups
        groups = get_teacher_groups(chat_id)
        if groups:
            groups_str = ", ".join([g['group_name'] for g in groups])
            lines.append(f"📚 {get_text('status_teaching_groups', lang)}: {groups_str}")
    
    # Student-specific info
    elif user['role'] == 'student':
        if user.get('group_name'):
            lines.append(f"👥 {get_text('status_group', lang)}: {user['group_name']}")
    
    # Registration date (all roles)
    if user.get('activated_at'):
        try:
            from datetime import datetime
            date_obj = user['activated_at']
            if isinstance(date_obj, str):
                date_obj = datetime.fromisoformat(date_obj)
            date_str = date_obj.strftime("%d %B %Y")
            lines.append(f"📅 {get_text('status_registered', lang)}: {date_str}")
        except:
            pass
    
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML"
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
        get_text('help_pay', lang),
        get_text('help_status', lang),
        get_text('help_language', lang),
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
            ENTERING_NAME_STUDENT: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~menu_button_filter, name_entered_admin)],
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
            ENTERING_NAME_TEACHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_entered_admin)],
            ADMIN_ENTERING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, group_entered_admin)]
        },
        fallbacks=common_fallbacks + [CommandHandler('cancel', cancel_admin)],
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
    app.add_handler(CommandHandler('attendance', check_attendance_command))
    
    # Language handlers
    register_language_handlers(app)
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(schedule_navigation, pattern=r'^schedule_'))
    app.add_handler(CallbackQueryHandler(start_attendance, pattern=r"^attend_"))
    app.add_handler(CallbackQueryHandler(toggle_student, pattern=r"^att_toggle_"))
    app.add_handler(CallbackQueryHandler(submit_attendance, pattern=r"^att_submit"))
    
    # Menu button handler (catches remaining menu buttons)
    app.add_handler(MessageHandler(menu_button_filter, handle_menu_buttons))
    
    # Error handler (always last)
    app.add_error_handler(error_handler)


# Legacy support if main.py wasn't updated to use register_handlers directly
def create_bot_application() -> Application:
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    register_handlers(app)
    return app