from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)


def main_menu_keyboard(is_admin: bool = False):
    """Persistent main menu keyboard."""
    
    if is_admin:
        keyboard = [
            [KeyboardButton("📅 Schedule"), KeyboardButton("📅 Today")],
            [KeyboardButton("👤 New Student"), KeyboardButton("👤 New Teacher")],
            [KeyboardButton("👥 Users"), KeyboardButton("❓ Help")]
        ]
    else:
        keyboard = [
            [KeyboardButton("📅 Schedule"), KeyboardButton("📅 Today")],
            [KeyboardButton("✏️ Change Lesson"), KeyboardButton("💰 Pay")],
            [KeyboardButton("📋 Status"), KeyboardButton("❓ Help")]
        ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )


# Menu button texts (for detection)
MENU_BUTTONS = [
    "📅 Schedule", "📅 Today", "✏️ Change Lesson", "💰 Pay",
    "📋 Status", "❓ Help", "👤 New Student", "👤 New Teacher", "👥 Users"
]

def role_keyboard():
    """Choose teacher or student."""
    keyboard = [
        [InlineKeyboardButton("👨‍🏫 Teacher", callback_data="role_teacher")],
        [InlineKeyboardButton("👨‍🎓 Student", callback_data="role_student")]
    ]
    return InlineKeyboardMarkup(keyboard)


def groups_keyboard(groups: list):
    """Select a group."""
    keyboard = []
    for group in groups:
        keyboard.append([InlineKeyboardButton(
            f"📚 {group}", 
            callback_data=f"group_{group}"
        )])
    return InlineKeyboardMarkup(keyboard)


def change_type_keyboard():
    """Postpone or cancel."""
    keyboard = [
        [InlineKeyboardButton("📅 Postpone", callback_data="change_postpone")],
        [InlineKeyboardButton("❌ Cancel", callback_data="change_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def lessons_keyboard(lessons: list):
    """Select a lesson date."""
    keyboard = []
    for lesson in lessons:
        hour = lesson['hour']
        minute = lesson['minute']
        
        if lesson['status'] == 'postponed':
            text = f"📅 {lesson['day_name']} {lesson['date']} → {lesson['new_date']} at {hour:02d}:{minute:02d}"
        else:
            text = f"📚 {lesson['day_name']} {lesson['date']} at {hour:02d}:{minute:02d}"
        
        keyboard.append([InlineKeyboardButton(
            text,
            callback_data=f"lesson_{lesson['date']}"
        )])
    
    if not keyboard:
        keyboard.append([InlineKeyboardButton("No lessons available", callback_data="no_lessons")])
    
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="cancel_action")])
    return InlineKeyboardMarkup(keyboard)


def days_keyboard():
    """Select a day for postponement."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    keyboard = []
    for day in days:
        keyboard.append([InlineKeyboardButton(day, callback_data=f"newday_{day.lower()}")])
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="cancel_action")])
    return InlineKeyboardMarkup(keyboard)


def hours_keyboard():
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
    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="cancel_action")])
    return InlineKeyboardMarkup(keyboard)


def minutes_keyboard():
    """Select minutes."""
    keyboard = [
        [
            InlineKeyboardButton("00", callback_data="minute_0"),
            InlineKeyboardButton("15", callback_data="minute_15"),
            InlineKeyboardButton("30", callback_data="minute_30"),
            InlineKeyboardButton("45", callback_data="minute_45")
        ],
        [InlineKeyboardButton("🔙 Cancel", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(keyboard)


def approval_keyboard(request_id: str):
    """Approve or reject request."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{request_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{request_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_keyboard():
    """Confirm action."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def schedule_keyboard():
    """Navigation for schedule weeks."""
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Previous Week", callback_data="schedule_prev"),
            InlineKeyboardButton("Next Week ➡️", callback_data="schedule_next")
        ],
        [
            InlineKeyboardButton("📍 This Week", callback_data="schedule_current")
        ],
        [
            InlineKeyboardButton("📅 Today Only", callback_data="schedule_today")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)