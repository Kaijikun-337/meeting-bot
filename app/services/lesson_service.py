from datetime import datetime, timedelta
from app.database.db import get_connection
from app.config import Config
import pytz


def add_lesson_override(
    meeting_id: str,
    original_date: str,
    override_type: str,
    new_date: str = None,
    new_hour: int = None,
    new_minute: int = None
) -> bool:
    """Add a lesson override (postpone or cancel)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO lesson_overrides 
            (meeting_id, original_date, override_type, new_date, new_hour, new_minute)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (meeting_id, original_date, override_type, new_date, new_hour, new_minute))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Override error: {e}")
        return False
    finally:
        conn.close()


def get_override(meeting_id: str, date: str) -> dict:
    """Get override for a specific meeting on a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM lesson_overrides 
        WHERE meeting_id = ? AND original_date = ?
    ''', (meeting_id, date))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def check_lesson_status(meeting_id: str, date: str) -> dict:
    """
    Check if lesson should run and when.
    Returns: {"status": "normal|cancelled|postponed", "new_time": {...}}
    """
    override = get_override(meeting_id, date)
    
    if not override:
        return {"status": "normal"}
    
    if override['override_type'] == 'cancel':
        return {"status": "cancelled"}
    
    if override['override_type'] == 'postpone':
        return {
            "status": "postponed",
            "new_date": override['new_date'],
            "new_hour": override['new_hour'],
            "new_minute": override['new_minute']
        }
    
    return {"status": "normal"}


def can_change_lesson(meeting_config: dict, target_date: str) -> tuple:
    """
    Check if lesson can be changed (must be 2+ hours before).
    Returns: (can_change: bool, reason: str)
    """
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Parse target date
    target = datetime.strptime(target_date, "%Y-%m-%d")
    target = tz.localize(target.replace(
        hour=meeting_config['schedule']['hour'],
        minute=meeting_config['schedule']['minute']
    ))
    
    # Check if 2+ hours before
    time_until = target - now
    hours_until = time_until.total_seconds() / 3600
    
    if hours_until < Config.MIN_HOURS_BEFORE_CHANGE:
        return (False, f"Less than {Config.MIN_HOURS_BEFORE_CHANGE} hours until lesson")
    
    if hours_until < 0:
        return (False, "Lesson already started or passed")
    
    return (True, "OK")


def get_upcoming_lessons(meeting_id: str, days_ahead: int = 14) -> list:
    """Get upcoming lesson dates for a meeting."""
    from app.config import Config
    
    meetings = Config.load_meetings()
    meeting = next((m for m in meetings if m['id'] == meeting_id), None)
    
    if not meeting:
        return []
    
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Day name to number mapping
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    schedule_days = [day_map[d.lower()] for d in meeting['schedule']['days']]
    
    upcoming = []
    for i in range(days_ahead):
        check_date = now + timedelta(days=i)
        if check_date.weekday() in schedule_days:
            date_str = check_date.strftime("%Y-%m-%d")
            override = get_override(meeting_id, date_str)
            
            if override:
                if override['override_type'] == 'cancel':
                    # Skip cancelled lessons - don't show them
                    continue
                elif override['override_type'] == 'postpone':
                    # Show postponed lesson with new time
                    upcoming.append({
                        "date": date_str,
                        "day_name": check_date.strftime("%A"),
                        "hour": override['new_hour'],
                        "minute": override['new_minute'],
                        "status": "postponed",
                        "new_date": override['new_date'],
                        "original_hour": meeting['schedule']['hour'],
                        "original_minute": meeting['schedule']['minute']
                    })
            else:
                # Normal lesson
                upcoming.append({
                    "date": date_str,
                    "day_name": check_date.strftime("%A"),
                    "hour": meeting['schedule']['hour'],
                    "minute": meeting['schedule']['minute'],
                    "status": "normal"
                })
    
    return upcoming