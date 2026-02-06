from telegram import Update
from telegram.ext import ContextTypes
from app.services.user_service import get_user
from app.bot.keyboards import schedule_keyboard
from telegram.constants import ChatAction
from app.config import Config
from app.services.lesson_service import get_override, get_postponed_to_date
from app.utils.localization import get_text, get_user_language  # ← Add this import at top


def is_admin(chat_id: str) -> bool:
    """Check if user is admin."""
    return str(chat_id) == str(Config.ADMIN_CHAT_ID)


def get_user_meetings(chat_id: str) -> list:
    from app.config import Config
    from app.services.user_service import get_teacher_groups, get_user
    
    if is_admin(chat_id):
        return Config.load_meetings()
    
    user = get_user(chat_id)
    if not user:
        return []
    
    all_meetings = Config.load_meetings()
    
    if user['role'] == 'student':
        # Split "Group A, Group B" -> ["group a", "group b"]
        raw_groups = user.get('group_name') or ""
        user_groups = [g.strip().lower() for g in raw_groups.split(',')]
        
        return [
            m for m in all_meetings 
            if (m.get('group_name') or "").strip().lower() in user_groups
        ]
    else:
        # Teacher Logic (Already supports multiple rows in DB)
        teacher_groups = get_teacher_groups(chat_id)
        if not teacher_groups:
            return []
            
        group_names = [(g['group_name'] or "").strip().lower() for g in teacher_groups]
        
        return [
            m for m in all_meetings 
            if (m.get('group_name') or "").strip().lower() in group_names
        ]

def get_weekly_schedule(chat_id: str, weeks_ahead: int = 0) -> dict:
    from datetime import datetime, timedelta
    import pytz
    # IMPORT THE NEW FUNCTION
    from app.services.lesson_service import get_all_overrides_for_period 
    from app.utils.localization import get_user_language, format_date_localized, get_day_name
    
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    lang = get_user_language(chat_id)
    
    days_since_monday = now.weekday()
    week_start = now - timedelta(days=days_since_monday) + timedelta(weeks=weeks_ahead)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6)
    
    # Formats for query
    start_str = week_start.strftime("%d-%m-%Y")
    end_str = week_end.strftime("%d-%m-%Y")
    
    # === BULK FETCH ===
    # Get all overrides for this week in ONE go
    overrides_data = get_all_overrides_for_period(start_str, end_str)
    # ==================
    
    meetings = get_user_meetings(chat_id)
    
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    days = []
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        date_str = current_date.strftime("%d-%m-%Y")
        day_name_en = current_date.strftime("%A")
        day_num = current_date.weekday()
        
        day_name = get_day_name(day_name_en, lang)
        day_short = format_date_localized(current_date, lang, 'short')
        
        lessons = []
        
        for meeting in meetings:
            schedule = meeting.get('schedule', {})
            meeting_days = [day_map.get(d.lower(), -1) for d in schedule.get('days', [])]
            
            hour = schedule.get('hour', 0)
            minute = schedule.get('minute', 0)
            
            # --- USE PRE-FETCHED DATA ---
            # Check if this meeting has an override on this date
            override = overrides_data['by_original_date'].get(date_str, {}).get(meeting['id'])
            
            # Check if any meeting was postponed TO this date
            # We filter the list of postponed lessons to find ones for this specific meeting
            postponed_list = overrides_data['by_new_date'].get(date_str, [])
            postponed_here = next((p for p in postponed_list if p['meeting_id'] == meeting['id']), None)
            # -----------------------------
            
            if day_num in meeting_days:
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
                    if override['override_type'] in ['cancel', 'cancelled']:
                        lesson_info['status'] = 'cancelled'
                    elif override['override_type'] in ['postpone', 'postponed']:
                        lesson_info['status'] = 'postponed'
                        lesson_info['new_date'] = override['new_date']
                        if override['new_hour'] is not None:
                            lesson_info['new_time'] = f"{override['new_hour']:02d}:{override['new_minute']:02d}"
                        else:
                            lesson_info['new_time'] = "TBD"
                
                lessons.append(lesson_info)
            
            if postponed_here:
                new_hour = postponed_here['new_hour']
                new_minute = postponed_here['new_minute'] or 0
                
                lesson_info = {
                    'time': f"{new_hour:02d}:{new_minute:02d}",
                    'hour': new_hour,
                    'minute': new_minute,
                    'title': meeting.get('title', 'Lesson'),
                    'group': meeting.get('group_name', ''),
                    'teacher': meeting.get('teacher_name', ''),
                    'meeting_id': meeting['id'],
                    'status': 'rescheduled',
                    'original_date': postponed_here['original_date']
                }
                lessons.append(lesson_info)
        
        lessons.sort(key=lambda x: (x['hour'], x['minute']))
        
        days.append({
            'date': date_str,
            'day_name': day_name,
            'day_short': day_short,
            'is_today': current_date.date() == now.date(),
            'lessons': lessons
        })
    
    week_start_str = format_date_localized(week_start, lang, 'month_day')
    week_end_str = format_date_localized(week_end, lang, 'month_day')
    
    return {
        'week_start': week_start_str,
        'week_end': week_end_str,
        'days': days,
        'lang': lang
    }


def format_schedule_message(schedule: dict, lang: str = 'en') -> str:
    """Format schedule with simple line separators."""
    
    LINE = "─" * 26
    
    lines = []
    lines.append(f"📅 <b>{get_text('your_schedule', lang)}</b>")
    lines.append(f"{get_text('week_of', lang)} {schedule['week_start']} - {schedule['week_end']}")
    lines.append("")
    
    for day in schedule['days']:
        today_marker = f" 👈 {get_text('today', lang)}" if day['is_today'] else ""
        
        lines.append(f"📆 <b>{day['day_name']}, {day['day_short']}</b>{today_marker}")
        lines.append(LINE)
        
        if day['lessons']:
            for lesson in day['lessons']:
                time_str = f"{lesson['hour']:02d}:{lesson['minute']:02d}"
                title = lesson.get('title', 'Lesson')
                group = lesson.get('group', '')
                teacher = lesson.get('teacher', '')
                
                info_parts = []
                if group:
                    info_parts.append(group)
                if teacher:
                    info_parts.append(teacher)
                info_str = f" ({', '.join(info_parts)})" if info_parts else ""
                
                if lesson['status'] == 'cancelled':
                    lines.append(f"  ❌ <s>{time_str} {title}{info_str}</s>")
                    lines.append(f"       ↳ <i>{get_text('cancelled_lesson', lang)}</i>")
                    
                elif lesson['status'] == 'postponed':
                    new_date = lesson.get('new_date', '?')
                    new_time = lesson.get('new_time', '?')
                    lines.append(f"  📅 <s>{time_str}</s> {title}{info_str}")
                    lines.append(f"       ↳ <i>{get_text('moved_to', lang)} {new_date} {new_time}</i>")
                    
                elif lesson['status'] == 'rescheduled':
                    original = lesson.get('original_date', '?')
                    lines.append(f"  🔄 {time_str} {title}{info_str}")
                    lines.append(f"       ↳ <i>{get_text('rescheduled_from', lang)} {original}</i>")
                    
                else:
                    lines.append(f"  🕐 {time_str} {title}{info_str}")
        else:
            lines.append(f"  <i>{get_text('no_lessons', lang)}</i>")
        
        lines.append("")
    
    return "\n".join(lines)


def format_daily_schedule(chat_id: str) -> str:
    """Get today's schedule with simple line separators."""
    from datetime import datetime
    import pytz
    from app.config import Config
    
    LINE = "─" * 26
    
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # ✅ CORRECT - get language CODE, not text
    lang = get_user_language(chat_id)
    
    schedule = get_weekly_schedule(chat_id)
    
    today = None
    for day in schedule['days']:
        if day['is_today']:
            today = day
            break
    
    if not today:
        return "❌ Could not get today's schedule."
    
    lines = []
    lines.append(f"📅 <b>{get_text('today_schedule', lang)}</b>")
    lines.append("")
    lines.append(f"📆 <b>{today['day_name']}, {today['day_short']}</b>")
    lines.append(LINE)
    
    if today['lessons']:
        for lesson in today['lessons']:
            time_str = f"{lesson['hour']:02d}:{lesson['minute']:02d}"
            title = lesson.get('title', 'Lesson')
            group = lesson.get('group', '')
            teacher = lesson.get('teacher', '')
            
            info_parts = []
            if group:
                info_parts.append(group)
            if teacher:
                info_parts.append(teacher)
            info_str = f" ({', '.join(info_parts)})" if info_parts else ""
            
            if lesson['status'] == 'cancelled':
                lines.append(f"  ❌ <s>{time_str} {title}{info_str}</s>")
                lines.append(f"       ↳ <i>{get_text('cancelled_lesson', lang)}</i>")
                
            elif lesson['status'] == 'postponed':
                new_date = lesson.get('new_date', '?')
                new_time = lesson.get('new_time', '?')
                lines.append(f"  📅 <s>{time_str}</s> {title}{info_str}")
                lines.append(f"       ↳ <i>{get_text('moved_to', lang)} {new_date} {new_time}</i>")
                
            elif lesson['status'] == 'rescheduled':
                original = lesson.get('original_date', '?')
                lines.append(f"  🔄 {time_str} {title}{info_str}")
                lines.append(f"       ↳ <i>{get_text('rescheduled_from', lang)} {original}</i>")
                
            else:
                lines.append(f"  🕐 {time_str} {title}{info_str}")
    else:
        lines.append(f"  🎉 <i>{get_text('no_lessons_today', lang)}</i>")
    
    lines.append(LINE)
    
    return "\n".join(lines)


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show weekly schedule."""
    chat_id = str(update.effective_user.id)
    
    from app.utils.localization import get_user_language
    from app.bot.keyboards import schedule_keyboard
    
    lang = get_user_language(chat_id)
    
    schedule = get_weekly_schedule(chat_id)
    message = format_schedule_message(schedule, lang)
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=schedule_keyboard(lang)  # ← Pass lang
    )


async def schedule_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = str(update.effective_chat.id)
    action = query.data
    
    from app.utils.localization import get_user_language
    from app.bot.keyboards import schedule_keyboard
    
    lang = get_user_language(chat_id)
    
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
            reply_markup=schedule_keyboard(lang)  # ← Pass lang
        )
        return
    
    context.user_data['schedule_week_offset'] = offset
    
    schedule = get_weekly_schedule(chat_id, weeks_ahead=offset)
    message = format_schedule_message(schedule, lang)
    
    await query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=schedule_keyboard(lang)  # ← Pass lang
    )



async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /today command."""
    chat_id = str(update.effective_chat.id)
    
    from app.utils.localization import get_user_language
    from app.bot.keyboards import schedule_keyboard
    
    lang = get_user_language(chat_id)
    
    if not is_admin(chat_id):
        user = get_user(chat_id)
        if not user:
            await update.message.reply_text(get_text('not_registered', lang))
            return
    
    message = format_daily_schedule(chat_id)
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=schedule_keyboard(lang)  # ← Pass lang
    )