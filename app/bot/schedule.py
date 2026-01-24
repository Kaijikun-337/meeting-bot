from telegram import Update
from telegram.ext import ContextTypes
from app.services.user_service import get_user
from app.bot.keyboards import schedule_keyboard
from telegram.constants import ChatAction
from app.config import Config


def is_admin(chat_id: str) -> bool:
    """Check if user is admin."""
    return str(chat_id) == str(Config.ADMIN_CHAT_ID)


def get_user_meetings(chat_id: str) -> list:
    from app.config import Config
    from app.services.user_service import get_teacher_groups, get_user
    
    # Admin sees all meetings
    if is_admin(chat_id):
        return Config.load_meetings()
    
    user = get_user(chat_id)
    if not user:
        return []
    
    meetings = Config.load_meetings()
    
    if user['role'] == 'student':
        return [m for m in meetings if m.get('group_name') == user.get('group_name')]
    else:
        teacher_groups = get_teacher_groups(chat_id)
        group_names = [g['group_name'] for g in teacher_groups]
        return [m for m in meetings if m.get('group_name') in group_names]


def get_weekly_schedule(chat_id: str, weeks_ahead: int = 0) -> dict:
    from datetime import datetime, timedelta
    import pytz
    from app.config import Config
    from app.services.lesson_service import get_override
    
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    days_since_monday = now.weekday()
    week_start = now - timedelta(days=days_since_monday) + timedelta(weeks=weeks_ahead)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6)
    
    meetings = get_user_meetings(chat_id)
    
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    days = []
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        day_name = current_date.strftime("%A")
        day_num = current_date.weekday()
        
        lessons = []
        
        for meeting in meetings:
            schedule = meeting.get('schedule', {})
            meeting_days = [day_map.get(d.lower(), -1) for d in schedule.get('days', [])]
            
            if day_num in meeting_days:
                override = get_override(meeting['id'], date_str)
                
                hour = schedule.get('hour', 0)
                minute = schedule.get('minute', 0)
                
                lesson_info = {
                    'time': f"{hour:02d}:{minute:02d}",
                    'hour': hour,
                    'minute': minute,
                    'title': meeting.get('title', 'Lesson'),
                    'group': meeting.get('group_name', ''),
                    'teacher': meeting.get('teacher_name', ''),
                    'meeting_id': meeting['id'],
                    'status': 'normal'
                }
                
                if override:
                    if override['override_type'] == 'cancel':
                        lesson_info['status'] = 'cancelled'
                    elif override['override_type'] == 'postpone':
                        lesson_info['status'] = 'postponed'
                        lesson_info['new_date'] = override['new_date']
                        lesson_info['new_time'] = f"{override['new_hour']:02d}:{override['new_minute']:02d}"
                
                lessons.append(lesson_info)
        
        lessons.sort(key=lambda x: (x['hour'], x['minute']))
        
        days.append({
            'date': date_str,
            'day_name': day_name,
            'day_short': current_date.strftime("%b %d"),
            'is_today': current_date.date() == now.date(),
            'lessons': lessons
        })
    
    return {
        'week_start': week_start.strftime("%B %d"),
        'week_end': week_end.strftime("%B %d"),
        'days': days
    }


def format_schedule_message(schedule: dict) -> str:
    """Format schedule as a beautiful text calendar."""
    
    lines = []
    lines.append("📅 <b>Your Schedule</b>")
    lines.append(f"Week of {schedule['week_start']} - {schedule['week_end']}")
    lines.append("")
    
    for day in schedule['days']:
        today_marker = " 👈 TODAY" if day['is_today'] else ""
        lines.append(f"┌{'─' * 40}┐")
        lines.append(f"│ 📆 <b>{day['day_name']}, {day['day_short']}</b>{today_marker}")
        lines.append(f"├{'─' * 40}┤")
        
        if day['lessons']:
            for lesson in day['lessons']:
                time_str = f"{lesson['hour']:02d}:{lesson['minute']:02d}"
                group = lesson.get('group', '')
                teacher = lesson.get('teacher', '')
                
                # Build info string
                info_parts = []
                if group:
                    info_parts.append(group)
                if teacher:
                    info_parts.append(teacher)
                info_str = f" ({', '.join(info_parts)})" if info_parts else ""
                
                if lesson['status'] == 'cancelled':
                    lines.append(f"│ ❌ <s>{time_str} │ {lesson['title']}{info_str}</s>")
                elif lesson['status'] == 'postponed':
                    lines.append(f"│ 📅 {time_str} │ {lesson['title']}{info_str}")
                    lines.append(f"│    ↳ Moved to {lesson['new_date']} at {lesson['new_time']}")
                else:
                    lines.append(f"│ 🕐 {time_str} │ {lesson['title']}{info_str}")
        else:
            lines.append("│    <i>No lessons</i>")
        
        lines.append(f"└{'─' * 40}┘")
        lines.append("")
    
    return "\n".join(lines)


def format_daily_schedule(chat_id: str) -> str:
    """Get today's schedule only."""
    from datetime import datetime
    import pytz
    from app.config import Config
    
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    schedule = get_weekly_schedule(chat_id)
    
    today = None
    for day in schedule['days']:
        if day['is_today']:
            today = day
            break
    
    if not today:
        return "❌ Could not get today's schedule."
    
    lines = []
    lines.append("📅 <b>Today's Schedule</b>")
    lines.append(f"{today['day_name']}, {today['day_short']}")
    lines.append("")
    
    if today['lessons']:
        for lesson in today['lessons']:
            time_str = f"{lesson['hour']:02d}:{lesson['minute']:02d}"
            group = lesson.get('group', '')
            teacher = lesson.get('teacher', '')
            
            # Build info string
            info_parts = []
            if group:
                info_parts.append(group)
            if teacher:
                info_parts.append(teacher)
            info_str = f"\n   👥 {', '.join(info_parts)}" if info_parts else ""
            
            if lesson['status'] == 'cancelled':
                lines.append(f"❌ <s>{time_str} - {lesson['title']}</s>")
            elif lesson['status'] == 'postponed':
                lines.append(f"📅 {time_str} - {lesson['title']}{info_str}")
                lines.append(f"   ↳ Moved to {lesson['new_date']} at {lesson['new_time']}")
            else:
                lines.append(f"🕐 {time_str} - {lesson['title']}{info_str}")
        
        lines.append("")
    else:
        lines.append("🎉 No lessons today!")
    
    return "\n".join(lines)


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command."""
    chat_id = str(update.effective_chat.id)
    
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    # Check if admin or registered user
    if not is_admin(chat_id):
        user = get_user(chat_id)
        if not user:
            await update.message.reply_text(
                "❌ You're not registered!\nUse /start to register first."
            )
            return
    
    context.user_data['schedule_week_offset'] = 0
    
    schedule = get_weekly_schedule(chat_id, weeks_ahead=0)
    message = format_schedule_message(schedule)
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=schedule_keyboard()
    )


async def schedule_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_chat.id)
    action = query.data
    
    offset = context.user_data.get('schedule_week_offset', 0)
    
    if action == "schedule_prev":
        offset -= 1
    elif action == "schedule_next":
        offset += 1
    elif action == "schedule_current":
        offset = 0
    elif action == "schedule_today":
        message = format_daily_schedule(chat_id)
        await query.edit_message_text(
            message,
            parse_mode='HTML',
            reply_markup=schedule_keyboard()
        )
        return
    
    context.user_data['schedule_week_offset'] = offset
    
    schedule = get_weekly_schedule(chat_id, weeks_ahead=offset)
    message = format_schedule_message(schedule)
    
    await query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=schedule_keyboard()
    )


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /today command."""
    chat_id = str(update.effective_chat.id)
    
    # Check if admin or registered user
    if not is_admin(chat_id):
        user = get_user(chat_id)
        if not user:
            await update.message.reply_text(
                "❌ You're not registered!\nUse /start to register first."
            )
            return
    
    message = format_daily_schedule(chat_id)
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=schedule_keyboard()
    )