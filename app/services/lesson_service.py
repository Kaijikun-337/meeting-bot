from datetime import datetime, timedelta
import pytz
from app.database.db import get_connection
from app.config import Config
from app.services.availability_service import get_teacher_availability

# Standard override types
OVERRIDE_CANCELLED = 'cancelled'
OVERRIDE_POSTPONED = 'postponed'

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


def get_postponed_to_date(meeting_id: str, date: str) -> dict:
    """Check if any lesson was postponed TO this date."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM lesson_overrides 
        WHERE meeting_id = ? AND new_date = ? AND override_type = 'postponed'
    ''', (meeting_id, date))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_all_postponed_to_date(date: str) -> list:
    """Get ALL lessons postponed to a specific date (for scheduler)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM lesson_overrides 
        WHERE new_date = ? AND override_type = 'postponed'
    ''', (date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def check_lesson_status(meeting_id: str, date: str) -> dict:
    """Check if a lesson is cancelled or postponed."""
    override = get_override(meeting_id, date)
    
    if not override:
        return {'status': 'normal'}
    
    override_type = override['override_type']
    
    # Handle both naming conventions
    if override_type in ['cancel', 'cancelled']:
        return {'status': 'cancelled'}
    elif override_type in ['postpone', 'postponed']:
        return {
            'status': 'postponed',
            'new_date': override.get('new_date'),
            'new_hour': override.get('new_hour'),
            'new_minute': override.get('new_minute')
        }
    
    return {'status': 'normal'}


def is_slot_available_for_group(teacher_chat_id: str, target_date: str, target_hour: int, target_minute: int, group_name: str) -> bool:
    """
    Check if a slot is available.
    Returns True only if NO lesson overrides exist at this time.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if ANY lesson is postponed to this time
        cursor.execute('''
            SELECT count(*) FROM lesson_overrides
            WHERE new_date = ? 
              AND new_hour = ? 
              AND new_minute = ? 
              AND override_type = 'postponed'
        ''', (target_date, target_hour, target_minute))
        
        # Handle different cursor types (tuple vs dict)
        row = cursor.fetchone()
        
        if isinstance(row, dict):
            # Postgres RealDictCursor
            count = row.get('count', 0)
        elif row:
            # SQLite Tuple
            count = row[0]
        else:
            count = 0
        
        # If count > 0, the slot is taken
        return count == 0
        
    except Exception as e:
        print(f"Error checking slot availability: {e}")
        return True
    finally:
        conn.close()


def create_lesson_override(meeting_id: str, original_date: str, override_type: str, 
                           new_date: str = None, new_hour: int = None, new_minute: int = None) -> bool:
    """Create or update a lesson override (Postgres Safe)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Check if exists
        cursor.execute('''
            SELECT 1 FROM lesson_overrides 
            WHERE meeting_id = ? AND original_date = ?
        ''', (meeting_id, original_date))
        
        exists = cursor.fetchone()
        
        if exists:
            # 2. Update
            cursor.execute('''
                UPDATE lesson_overrides
                SET override_type = ?, new_date = ?, new_hour = ?, new_minute = ?, status = ?
                WHERE meeting_id = ? AND original_date = ?
            ''', (override_type, new_date, new_hour, new_minute, override_type, meeting_id, original_date))
        else:
            # 3. Insert
            cursor.execute('''
                INSERT INTO lesson_overrides 
                (meeting_id, original_date, override_type, new_date, new_hour, new_minute, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (meeting_id, original_date, override_type, new_date, new_hour, new_minute, override_type))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error creating override: {e}")
        return False
    finally:
        conn.close()


def delete_lesson_override(meeting_id: str, original_date: str) -> bool:
    """
    Deletes an override, effectively restoring the lesson to its original schedule.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM lesson_overrides 
            WHERE meeting_id = ? AND original_date = ?
        ''', (meeting_id, original_date))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error deleting override: {e}")
        return False
    finally:
        conn.close()


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
            
            # Check for overrides
            override = get_override(meeting_id, date_str)
            
            status = "normal"
            if override:
                if override['override_type'] in ['cancel', 'cancelled']:
                    status = "cancelled"
                elif override['override_type'] in ['postpone', 'postponed']:
                    status = "postponed"
            
            upcoming.append({
                "date": date_str,
                "day_name": day_name,
                "hour": meeting['schedule']['hour'],
                "minute": meeting['schedule']['minute'],
                "status": status,
                "override_info": override
            })
    
    return upcoming


def get_all_overrides_for_period(start_date_str: str, end_date_str: str) -> dict:
    """
    Fetch ALL overrides (cancelled/postponed) for a date range in one query.
    Returns a dictionary for fast lookup.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM lesson_overrides 
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    result = {
        'by_original_date': {},
        'by_new_date': {}
    }
    
    try:
        start_dt = datetime.strptime(start_date_str, "%d-%m-%Y")
        end_dt = datetime.strptime(end_date_str, "%d-%m-%Y")
    except:
        return result

    for row in rows:
        data = dict(row)
        
        # 1. Organize by Original Date
        orig_date = data['original_date']
        meeting_id = data['meeting_id']
        
        try:
            orig_dt = datetime.strptime(orig_date, "%d-%m-%Y")
            if start_dt <= orig_dt <= end_dt:
                if orig_date not in result['by_original_date']:
                    result['by_original_date'][orig_date] = {}
                result['by_original_date'][orig_date][meeting_id] = data
        except:
            pass

        # 2. Organize by New Date
        if data['override_type'] in ['postpone', 'postponed'] and data['new_date']:
            new_date = data['new_date']
            try:
                new_dt = datetime.strptime(new_date, "%d-%m-%Y")
                if start_dt <= new_dt <= end_dt:
                    if new_date not in result['by_new_date']:
                        result['by_new_date'][new_date] = []
                    result['by_new_date'][new_date].append(data)
            except:
                pass
                
    return result


def get_available_slots_for_rescheduling(teacher_chat_id: str, exclude_date: str, group_name: str, days_ahead: int = 7) -> list:
    """
    Get available time slots for rescheduling based on teacher's availability.
    """
    
    available_dates = []
    
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Get teacher's availability patterns from DB
    teacher_avail = get_teacher_availability(teacher_chat_id)
    
    if not teacher_avail:
        return []

    # Convert DB availability to a lookup dict
    avail_map = {entry['date']: entry for entry in teacher_avail}
    
    for i in range(1, days_ahead + 1):
        check_date = now + timedelta(days=i)
        date_str = check_date.strftime("%d-%m-%Y")
        
        # Skip the original date
        if date_str == exclude_date:
            continue
            
        # Check if teacher marked this day as available
        if date_str not in avail_map:
            continue
            
        settings = avail_map[date_str]
        start_h = settings['start_hour']
        end_h = settings['end_hour']
        
        day_slots = []
        
        # Generate 30-minute slots
        current_h = start_h
        current_m = 0
        
        while current_h < end_h:
            # Check strict availability
            if is_slot_available_for_group(teacher_chat_id, date_str, current_h, current_m, group_name):
                time_str = f"{current_h:02d}:{current_m:02d}"
                day_slots.append(time_str)
            
            # Increment 30 mins
            current_m += 30
            if current_m >= 60:
                current_m = 0
                current_h += 1
        
        if day_slots:
            available_dates.append({
                'date': date_str,
                'display': date_str,
                'slots': day_slots
            })
            
    return available_dates