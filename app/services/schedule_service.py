from datetime import datetime, timedelta
import pytz
from app.config import Config
from app.services.user_service import get_user, get_teacher_groups


def get_user_meetings(chat_id: str) -> list:
    """Get all meetings for a user based on their role."""
    user = get_user(chat_id)
    if not user:
        return []
    
    meetings = Config.load_meetings()
    
    if user['role'] == 'student':
        # Filter by student's group
        return [m for m in meetings if m.get('group_name') == user.get('group_name')]
    else:
        # Teacher - get meetings for their groups
        teacher_groups = get_teacher_groups(chat_id)
        group_names = [g['group_name'] for g in teacher_groups]
        return [m for m in meetings if m.get('group_name') in group_names]


def get_weekly_schedule(chat_id: str, weeks_ahead: int = 0) -> dict:
    """
    Get schedule for a specific week.
    
    Returns:
    {
        'week_start': '2024-01-15',
        'week_end': '2024-01-21',
        'days': [
            {
                'date': '2024-01-15',
                'day_name': 'Monday',
                'lessons': [
                    {
                        'time': '18:00',
                        'title': 'Math Lesson',
                        'status': 'normal',
                        'group': 'Group A'
                    }
                ]
            },
            ...
        ]
    }
    """
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Calculate week start (Monday)
    days_since_monday = now.weekday()
    week_start = now - timedelta(days=days_since_monday) + timedelta(weeks=weeks_ahead)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6)
    
    # Get user's meetings
    meetings = get_user_meetings(chat_id)
    
    # Day name to number
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    # Build schedule for each day
    days = []
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        date_str = current_date.strftime("%d-%m-%Y")
        day_name = current_date.strftime("%A")
        day_num = current_date.weekday()
        
        lessons = []
        
        for meeting in meetings:
            schedule = meeting.get('schedule', {})
            meeting_days = [day_map.get(d.lower(), -1) for d in schedule.get('days', [])]
            
            if day_num in meeting_days:
                
                hour = schedule.get('hour', 0)
                minute = schedule.get('minute', 0)
                
                lesson_info = {
                    'time': f"{hour:02d}:{minute:02d}",
                    'hour': hour,
                    'minute': minute,
                    'title': meeting.get('title', 'Lesson'),
                    'group': meeting.get('group_name', ''),
                    'meeting_id': meeting['id'],
                    'status': 'normal'
                }
                
                lessons.append(lesson_info)
        
        # Sort lessons by time
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
        'week_start_date': week_start.strftime("%d-%m-%Y"),
        'days': days
    }


def format_schedule_message(schedule: dict) -> str:
    """Format schedule as a beautiful text calendar."""
    
    lines = []
    lines.append(f"📅 <b>Your Schedule</b>")
    lines.append(f"Week of {schedule['week_start']} - {schedule['week_end']}")
    lines.append("")
    
    for day in schedule['days']:
        # Day header
        today_marker = " 👈 TODAY" if day['is_today'] else ""
        lines.append(f"┌{'─' * 36}┐")
        lines.append(f"│ 📆 <b>{day['day_name']}, {day['day_short']}</b>{today_marker}")
        lines.append(f"├{'─' * 36}┤")
        
        if day['lessons']:
            for lesson in day['lessons']:
                if lesson['status'] == 'cancelled':
                    # Crossed out cancelled lesson
                    lines.append(f"│ ❌ <s>{lesson['time']} │ {lesson['title']}</s>")
                elif lesson['status'] == 'postponed':
                    # Show postponed with new time
                    lines.append(f"│ 📅 {lesson['time']} │ {lesson['title']}")
                    lines.append(f"│    ↳ Moved to {lesson['new_date']} at {lesson['new_time']}")
                else:
                    # Normal lesson
                    lines.append(f"│ 🕐 {lesson['time']} │ {lesson['title']}")
        else:
            lines.append(f"│    <i>No lessons</i>")
        
        lines.append(f"└{'─' * 36}┘")
        lines.append("")
    
    return "\n".join(lines)


def format_daily_schedule(chat_id: str) -> str:
    """Get today's schedule only."""
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    schedule = get_weekly_schedule(chat_id)
    
    # Find today
    today = None
    for day in schedule['days']:
        if day['is_today']:
            today = day
            break
    
    if not today:
        return "❌ Could not get today's schedule."
    
    lines = []
    lines.append(f"📅 <b>Today's Schedule</b>")
    lines.append(f"{today['day_name']}, {today['day_short']}")
    lines.append("")
    
    if today['lessons']:
        for lesson in today['lessons']:
            if lesson['status'] == 'cancelled':
                lines.append(f"❌ <s>{lesson['time']} - {lesson['title']}</s>")
            elif lesson['status'] == 'postponed':
                lines.append(f"📅 {lesson['time']} - {lesson['title']}")
                lines.append(f"   ↳ Moved to {lesson['new_date']} at {lesson['new_time']}")
            else:
                lines.append(f"🕐 {lesson['time']} - {lesson['title']}")
    else:
        lines.append("🎉 No lessons today!")
    
    return "\n".join(lines)