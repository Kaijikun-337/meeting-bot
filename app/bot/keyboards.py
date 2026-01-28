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
            [KeyboardButton(get_text('btn_users', lang)), KeyboardButton(get_text('btn_status', lang))],
            [KeyboardButton(get_text('btn_language', lang)), KeyboardButton(get_text('btn_help', lang))]
        ]
    elif is_teacher:
        keyboard = [
            [KeyboardButton(get_text('btn_schedule', lang)), KeyboardButton(get_text('btn_today', lang))],
            [KeyboardButton(get_text('btn_change_lesson', lang)), KeyboardButton(get_text('btn_homework', lang))],
            [KeyboardButton(get_text('btn_status', lang)), KeyboardButton(get_text('btn_availability', lang))],
            [KeyboardButton(get_text('btn_language', lang)), KeyboardButton(get_text('btn_help', lang))]
        ]
    else:
        # Student menu
        keyboard = [
            [KeyboardButton(get_text('btn_schedule', lang)), KeyboardButton(get_text('btn_today', lang))],
            [KeyboardButton(get_text('btn_change_lesson', lang)), KeyboardButton(get_text('btn_pay', lang))],
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
        get_text('btn_change_lesson', lang),
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


# Legacy - keep for backward compatibility
# Legacy - keep for backward compatibility and menu_button_filter
MENU_BUTTONS = [
    # English
    "📅 Schedule", "📅 Today", "✏️ Change Lesson", "💰 Pay",
    "📋 Status", "❓ Help", "👤 New Student", "👤 New Teacher", 
    "👥 Users", "🌐 Language", "📅 Availability", "📚 Homework",
    # Russian
    "📅 Расписание", "📅 Сегодня", "✏️ Изменить урок", "💰 Оплата",
    "📋 Статус", "❓ Помощь", "👤 Новый ученик", "👤 Новый учитель",
    "👥 Пользователи", "🌐 Язык", "📅 Доступность", "📚 Домашнее задание",
    # Uzbek
    "📅 Jadval", "📅 Bugun", "✏️ Darsni o'zgartirish", "💰 To'lov",
    "📋 Holat", "❓ Yordam", "👤 Yangi o'quvchi", "👤 Yangi o'qituvchi",
    "👥 Foydalanuvchilar", "🌐 Til", "📅 Bo'sh vaqt", "📚 Uy vazifasi"
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
# CHANGE LESSON KEYBOARDS
# ═══════════════════════════════════════════════════════════

def change_type_keyboard(lang: str = 'en'):
    """Postpone or cancel."""
    keyboard = [
        [InlineKeyboardButton(get_text('postpone', lang), callback_data="change_postpone")],
        [InlineKeyboardButton(get_text('cancel_lesson', lang), callback_data="change_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def lessons_keyboard(lessons: list, lang: str = 'en'):
    """Select a lesson date."""
    keyboard = []
    for lesson in lessons:
        hour = lesson['hour']
        minute = lesson['minute']
        
        if lesson['status'] == 'postponed':
            text = f"📅 {lesson['day_name']} {lesson['date']} → {lesson['new_date']} {hour:02d}:{minute:02d}"
        else:
            text = f"📚 {lesson['day_name']} {lesson['date']} {hour:02d}:{minute:02d}"
        
        keyboard.append([InlineKeyboardButton(
            text,
            callback_data=f"lesson_{lesson['date']}"
        )])
    
    if not keyboard:
        keyboard.append([InlineKeyboardButton(get_text('no_lessons_to_change', lang), callback_data="no_lessons")])
    
    keyboard.append([InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="cancel_action")])
    return InlineKeyboardMarkup(keyboard)


def days_keyboard(lang: str = 'en'):
    """Select a day for postponement."""
    day_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    keyboard = []
    for day_key in day_keys:
        day_name = get_text(day_key, lang)
        keyboard.append([InlineKeyboardButton(day_name, callback_data=f"newday_{day_key}")])
    keyboard.append([InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="cancel_action")])
    return InlineKeyboardMarkup(keyboard)


def hours_keyboard(lang: str = 'en'):
    """Select hour."""
    keyboard = []
    row = []
    for hour in range(8, 22):
        row.append(InlineKeyboardButton(f"{hour:02d}", callback_data=f"hour_{hour}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="cancel_action")])
    return InlineKeyboardMarkup(keyboard)


def minutes_keyboard(lang: str = 'en'):
    """Select minutes."""
    keyboard = [
        [
            InlineKeyboardButton("00", callback_data="minute_0"),
            InlineKeyboardButton("30", callback_data="minute_30")
        ],
        [InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="cancel_action")]
    ]
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
# AVAILABILITY KEYBOARDS
# ═══════════════════════════════════════════════════════════

def availability_days_keyboard(days_list: list, lang: str = 'en'):
    """Select a day to set availability."""
    buttons = []
    
    for day in days_list:
        buttons.append([
            InlineKeyboardButton(
                f"📅 {day['display']}", 
                callback_data=f"avail_day_{day['date_str']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(get_text('view_schedule', lang), callback_data="avail_view")])
    buttons.append([InlineKeyboardButton(get_text('clear_all', lang), callback_data="avail_clear_all")])
    buttons.append([InlineKeyboardButton(get_text('btn_close', lang), callback_data="avail_close")])
    
    return InlineKeyboardMarkup(buttons)


def availability_start_hour_keyboard(start_hour: int = 8, end_hour: int = 21, lang: str = 'en'):
    """Select start hour for availability."""
    buttons = []
    row = []
    
    for hour in range(start_hour, end_hour):
        row.append(InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"avail_start_{hour}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(get_text('btn_back', lang), callback_data="avail_back")])
    
    return InlineKeyboardMarkup(buttons)


def availability_end_hour_keyboard(after_hour: int, max_hour: int = 22, lang: str = 'en'):
    """Select end hour for availability (must be after start)."""
    buttons = []
    row = []
    
    for hour in range(after_hour + 1, max_hour):
        row.append(InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"avail_end_{hour}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(get_text('btn_back', lang), callback_data="avail_back")])
    
    return InlineKeyboardMarkup(buttons)


def availability_view_keyboard(availability_list: list, lang: str = 'en'):
    """View current availability with remove buttons."""
    buttons = []
    
    for entry in availability_list:
        buttons.append([
            InlineKeyboardButton(
                f"🗑 {get_text('remove', lang)} {entry['display']}",
                callback_data=f"avail_remove_{entry['date']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(get_text('add_more', lang), callback_data="avail_add_more")])
    buttons.append([InlineKeyboardButton(get_text('btn_close', lang), callback_data="avail_close")])
    
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════
# RESCHEDULE SLOTS KEYBOARD
# ═══════════════════════════════════════════════════════════

def reschedule_slots_keyboard(slots: list, lang: str = 'en'):
    """Show available slots for student rescheduling."""
    buttons = []
    
    for slot in slots:
        buttons.append([
            InlineKeyboardButton(
                f"📅 {slot['display']}",
                callback_data=f"reschedule_{slot['date']}_{slot['hour']}_{slot['minute']}"
            )
        ])
    
    if not buttons:
        buttons.append([InlineKeyboardButton(get_text('no_available_slots', lang), callback_data="no_slots")])
    
    buttons.append([InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="cancel_action")])
    
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════
# PAYMENT KEYBOARDS
# ═══════════════════════════════════════════════════════════

def payment_confirm_keyboard(lang: str = 'en'):
    """Submit or cancel payment."""
    keyboard = [
        [
            InlineKeyboardButton(get_text('btn_submit', lang), callback_data="payment_submit"),
            InlineKeyboardButton(get_text('btn_cancel', lang), callback_data="payment_cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


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