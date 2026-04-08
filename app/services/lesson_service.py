from datetime import datetime, timedelta
import pytz
from app.database.db import get_connection
from app.config import Config

def get_upcoming_lessons(meeting_id: str, days_ahead: int = 14, lang: str = 'en') -> list:
    """Get upcoming lesson dates, INCLUDING modified ones (so we can restore them)."""
    from app.utils.localization import get_text
    
    meetings = Config.load_meetings()
    meeting = next((m for m in meetings if m['id'] == meeting_id), None)
    
    if not meeting:
        return []
    
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    day_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2,
        'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    num_to_day_key = {
        0: 'monday', 1: 'tuesday', 2: 'wednesday',
        3: 'thursday', 4: 'friday', 5: 'saturday', 6: 'sunday'
    }
    
    schedule_days = [day_map[d.lower()] for d in meeting['schedule']['days']]
    
    upcoming = []
    for i in range(days_ahead):
        check_date = now + timedelta(days=i)
        
        # Simple check: ignore lessons that finished more than 2 hours ago
        lesson_time = check_date.replace(
            hour=meeting['schedule']['hour'], 
            minute=meeting['schedule']['minute']
        )
        if lesson_time < now - timedelta(hours=2):
            continue
            
        if check_date.weekday() in schedule_days:
            date_str = check_date.strftime("%d-%m-%Y")
            day_key = num_to_day_key[check_date.weekday()]
            day_name = get_text(day_key, lang)
    
    return upcoming