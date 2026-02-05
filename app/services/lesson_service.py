from datetime import datetime, timedelta
from app.database.db import get_connection
from app.config import Config
import pytz

# Standard override types
OVERRIDE_CANCELLED = 'cancelled'
OVERRIDE_POSTPONED = 'postponed'

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

def get_conflicting_postponements(teacher_chat_id: str, target_date: str, target_hour: int, exclude_group: str = None) -> list:
    """
    Check if there are other lessons already postponed to this date/time.
    Returns list of conflicting overrides (from different groups).
    
    Args:
        teacher_chat_id: Teacher's chat ID
        target_date: Date to check (format: DD-MM-YYYY)
        target_hour: Hour to check
        exclude_group: Group name to exclude (same group can use same slot)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get all postponements to this date and hour
        cursor.execute('''
            SELECT lo.*, m.group_name 
            FROM lesson_overrides lo
            LEFT JOIN (
                SELECT id, group_name FROM meetings_cache
            ) m ON lo.meeting_id = m.id
            WHERE lo.new_date = ? 
              AND lo.new_hour = ? 
              AND lo.override_type = 'postponed'
        ''', (target_date, target_hour))
        
        rows = cursor.fetchall()
        
        # Filter out same group
        conflicts = []
        for row in rows:
            row_dict = dict(row)
            # We need to get group from meeting config
            if exclude_group and row_dict.get('group_name') == exclude_group:
                continue
            conflicts.append(row_dict)
        
        return conflicts
    except Exception as e:
        print(f"Error checking conflicts: {e}")
        return []
    finally:
        conn.close()


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
        
        # Safe extraction
        if isinstance(row, dict):
            # Postgres RealDictCursor returns {'count': 0}
            count = row.get('count', 0)
        elif row:
            # SQLite returns (0,)
            count = row[0]
        else:
            count = 0
        
        # If count > 0, the slot is taken
        return count == 0
        
    except Exception as e:
        # Only print real errors, not "0"
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

def can_change_lesson(meeting_config: dict, target_date: str) -> tuple:
    """
    Check if lesson can be changed (must be 2+ hours before).
    Returns: (can_change: bool, reason: str)
    """
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Parse target date
    target = datetime.strptime(target_date, "%d-%m-%Y")
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


def get_upcoming_lessons(meeting_id: str, days_ahead: int = 14, lang: str = 'en') -> list:
    """Get upcoming lesson dates, INCLUDING modified ones (so we can restore them)."""
    from app.config import Config
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
                "status": status,  # <--- Now returns status instead of skipping
                "override_info": override # Pass details if needed
            })
    
    return upcoming

def get_all_overrides_for_period(start_date_str: str, end_date_str: str) -> dict:
    """
    Fetch ALL overrides (cancelled/postponed) for a date range in one query.
    Returns a dictionary:
    {
        'DD-MM-YYYY': {
            'meeting_id': { ...override_data... }
        },
        'postponed_to': {
            'DD-MM-YYYY': [ ...list of postponed lessons landing here... ]
        }
    }
    """
    from datetime import datetime
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # We need to convert string dates to compare them, but SQLite stores as TEXT
    # For simplicity in this specific project, we will just fetch all active overrides
    # because the dataset is small. A truly optimized SQL range query depends on DB type.
    
    cursor.execute('''
        SELECT * FROM lesson_overrides 
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    result = {
        'by_original_date': {},
        'by_new_date': {}
    }
    
    # Parse range for filtering in Python
    try:
        start_dt = datetime.strptime(start_date_str, "%d-%m-%Y")
        end_dt = datetime.strptime(end_date_str, "%d-%m-%Y")
    except:
        return result

    for row in rows:
        data = dict(row)
        
        # 1. Organize by Original Date (Cancellations / Moves FROM here)
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

        # 2. Organize by New Date (Moves TO here)
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