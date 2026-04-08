from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from app.utils.localization import get_text, get_user_language


# ═══════════════════════════════════════════════════════════
# MAIN MENU (Reply Keyboard)
# ═══════════════════════════════════════════════════════════

def main_menu_keyboard(is_admin: bool = False, is_teacher: bool = False, lang: str = 'en'):
    """Persistent main menu keyboard - localized."""
    
    if is_admin:
        keyboard = [
            [KeyboardButton(get_text('btn_schedule', lang)), KeyboardButton(get_text('btn_today', lang))],
            [KeyboardButton(get_text('btn_new_student', lang)), KeyboardButton(get_text('btn_new_teacher', lang))],
            [KeyboardButton(get_text('btn_users', lang))],
            [KeyboardButton(get_text('btn_language', lang)), KeyboardButton(get_text('btn_help', lang))]
        ]
    elif is_teacher:
        keyboard = [
            [KeyboardButton(get_text('btn_schedule', lang)), KeyboardButton(get_text('btn_today', lang))],
            [KeyboardButton(get_text('btn_homework', lang))],
            [KeyboardButton(get_text('btn_status', lang))],
            [KeyboardButton(get_text('btn_language', lang)), KeyboardButton(get_text('btn_help', lang))]
        ]
    else:
        # Student menu
        keyboard = [
            [KeyboardButton(get_text('btn_schedule', lang)), KeyboardButton(get_text('btn_today', lang))],
            [KeyboardButton(get_text('btn_status', lang)), KeyboardButton(get_text('btn_language', lang))],
            [KeyboardButton(get_text('btn_help', lang))]
        ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )


def get_menu_buttons(lang: str = 'en') -> list:
    """Get list of menu button texts for detection - localized."""
    return [
        get_text('btn_schedule', lang),
        get_text('btn_today', lang),
        get_text('btn_pay', lang),
        get_text('btn_status', lang),
        get_text('btn_help', lang),
        get_text('btn_new_student', lang),
        get_text('btn_new_teacher', lang),
        get_text('btn_users', lang),
        get_text('btn_language', lang)
    ]


def get_all_menu_buttons() -> list:
    """Get ALL possible menu button texts across all languages."""
    all_buttons = []
    for lang in ['en', 'ru', 'uz']:
        all_buttons.extend(get_menu_buttons(lang))
    return list(set(all_buttons))  # Remove duplicates


# Legacy - keep for backward compatibility and menu_button_filter
MENU_BUTTONS = [
    # English
    "📅 Schedule", "📅 Today", "💰 Pay",
    "📋 Status", "❓ Help", "👤 New Student", "👤 New Teacher", 
    "👥 Users", "🌐 Language", "📚 Homework",
    
    # Russian
    "📅 Расписание", "📅 Сегодня", "💰 Оплата",
    "📋 Статус", "❓ Помощь", "👤 Новый ученик", "👤 Новый учитель",
    "👥 Пользователи", "🌐 Язык", "📚 Домашнее задание",
    
    # Uzbek
    "📅 Jadval", "📅 Bugun", "💰 To'lov",
    "📋 Holat", "❓ Yordam", "👤 Yangi o'quvchi", "👤 Yangi o'qituvchi",
    "👥 Foydalanuvchilar", "🌐 Til", "📚 Uy vazifasi",
    
]

# ═══════════════════════════════════════════════════════════
# ROLE & GROUP SELECTION
# ═══════════════════════════════════════════════════════════

def role_keyboard(lang: str = 'en'):
    """Choose teacher or student."""
    keyboard = [
        [InlineKeyboardButton(f"👨‍🏫 {get_text('role_teacher', lang)}", callback_data="role_teacher")],
        [InlineKeyboardButton(f"👨‍🎓 {get_text('role_student', lang)}", callback_data="role_student")]
    ]
    return InlineKeyboardMarkup(keyboard)


def groups_keyboard(groups: list, lang: str = 'en'):
    """Select a group."""
    keyboard = []
    for group in groups:
        keyboard.append([InlineKeyboardButton(
            f"📚 {group}", 
            callback_data=f"group_{group}"
        )])
    keyboard.append([InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="cancel_action")])
    return InlineKeyboardMarkup(keyboard)


# ═══════════════════════════════════════════════════════════
# APPROVAL & CONFIRMATION KEYBOARDS
# ═══════════════════════════════════════════════════════════

def approval_keyboard(request_id: str, lang: str = 'en'):
    """Approve or reject request."""
    keyboard = [
        [
            InlineKeyboardButton(get_text('btn_approve', lang), callback_data=f"approve_{request_id}"),
            InlineKeyboardButton(get_text('btn_reject', lang), callback_data=f"reject_{request_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(lang: str = 'en'):
    """Confirm action."""
    keyboard = [
        [
            InlineKeyboardButton(get_text('btn_confirm', lang), callback_data="confirm_yes"),
            InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ═══════════════════════════════════════════════════════════
# SCHEDULE KEYBOARDS
# ═══════════════════════════════════════════════════════════

def schedule_keyboard(lang: str = 'en'):
    """Navigation for schedule weeks - localized."""
    keyboard = [
        [
            InlineKeyboardButton(get_text('prev_week', lang), callback_data="schedule_prev"),
            InlineKeyboardButton(get_text('next_week', lang), callback_data="schedule_next")
        ],
        [
            InlineKeyboardButton(get_text('this_week', lang), callback_data="schedule_current")
        ],
        [
            InlineKeyboardButton(get_text('today_only', lang), callback_data="schedule_today")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def schedule_keyboard_localized(chat_id: str):
    """Navigation for schedule weeks - gets lang from chat_id."""
    lang = get_user_language(chat_id)
    return schedule_keyboard(lang)


# ═══════════════════════════════════════════════════════════
# LANGUAGE KEYBOARD
# ═══════════════════════════════════════════════════════════

def language_keyboard():
    """Language selection keyboard."""
    from app.utils.localization import LANGUAGES
    
    buttons = []
    for code, name in LANGUAGES.items():
        buttons.append([InlineKeyboardButton(name, callback_data=f"setlang_{code}")])
    return InlineKeyboardMarkup(buttons)

def unregistered_menu_keyboard(lang: str = 'en'):
    """Menu for users who are not registered yet: only Language button."""
    keyboard = [
        [KeyboardButton(get_text('btn_language', lang))]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )
    
def confirm_keyboard_localized(lang: str = 'en'):
    """Keyboard for confirming an action (Yes/No)."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text('btn_yes', lang), callback_data="confirm_yes"),
            InlineKeyboardButton(get_text('btn_no', lang), callback_data="confirm_no")
        ]
    ])