from datetime import datetime, timedelta
from app.database.db import get_connection

# Define the date format in ONE place
DATE_FORMAT = "%d-%m-%Y"  # 28-01-2026


def set_availability(teacher_chat_id: str, date_str: str, start: int, end: int):
    """Set availability for a specific date (Postgres Safe)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Check if row exists
        cursor.execute('''
            SELECT 1 FROM teacher_availability 
            WHERE teacher_chat_id = ? AND available_date = ?
        ''', (str(teacher_chat_id), date_str))
        
        exists = cursor.fetchone()
        
        if exists:
            # 2. Update
            cursor.execute('''
                UPDATE teacher_availability
                SET start_hour = ?, end_hour = ?
                WHERE teacher_chat_id = ? AND available_date = ?
            ''', (start, end, str(teacher_chat_id), date_str))
        else:
            # 3. Insert
            cursor.execute('''
                INSERT INTO teacher_availability (teacher_chat_id, available_date, start_hour, end_hour)
                VALUES (?, ?, ?, ?)
            ''', (str(teacher_chat_id), date_str, start, end))
            
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error setting availability: {e}")
        return False
    finally:
        conn.close()


def get_teacher_availability(teacher_chat_id: str) -> list:
    """
    Get all future availability for a teacher.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.now().strftime(DATE_FORMAT)
    
    try:
        cursor.execute('''
            SELECT available_date, start_hour, end_hour 
            FROM teacher_availability
            WHERE teacher_chat_id = ?
            ORDER BY available_date
        ''', (str(teacher_chat_id),))
        
        rows = cursor.fetchall()
        
        # Filter for future dates
        result = []
        today_obj = datetime.now().date()
        
        for row in rows:
            try:
                date_obj = datetime.strptime(row["available_date"], DATE_FORMAT).date()
                if date_obj >= today_obj:
                    result.append({
                        "date": row["available_date"],
                        "start_hour": row["start_hour"],
                        "end_hour": row["end_hour"]
                    })
            except ValueError:
                # Skip invalid date formats
                continue
        
        return result
    except Exception as e:
        print(f"❌ Error getting availability: {e}")
        return []
    finally:
        conn.close()


def get_available_slots_for_rescheduling(teacher_chat_id: str, exclude_date: str = None, group_name: str = None) -> list:
    """
    Get 30-minute slots available for student rescheduling.
    """
    from app.services.lesson_service import is_slot_available_for_group
    from app.config import Config
    
    availability = get_teacher_availability(teacher_chat_id)
    
    if not availability:
        return []
    
    # Load ALL regular meetings to check conflicts
    all_meetings = Config.load_meetings()
    
    slots = []
    now = datetime.now()
    
    # Pre-calculate busy slots from regular schedule
    # Format: "DD-MM-YYYY_HH_MM"
    busy_slots = set()
    
    for m in all_meetings:
        # If it's the SAME group, they can swap their own lesson (so don't mark busy)
        if group_name and m.get('group_name') == group_name:
            continue
            
        schedule = m.get('schedule', {})
        hour = schedule.get('hour')
        minute = schedule.get('minute')
        days = schedule.get('days', [])
        
        # We need to map days to dates for the next 2 weeks
        # This is complex, so let's simplify:
        # Just check inside the loop below
        pass

    for entry in availability:
        date_str = entry["date"]
        start_h = entry["start_hour"]
        end_h = entry["end_hour"]
        
        # Skip if this is the date we're rescheduling FROM
        if exclude_date and date_str == exclude_date:
            continue
        
        try:
            date_obj = datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            continue
        
        # Check if there is a REGULAR lesson on this day for ANOTHER group
        day_name = date_obj.strftime("%A").lower()
        regular_conflict = False
        
        for m in all_meetings:
            # Skip same group
            if group_name and m.get('group_name') == group_name:
                continue
            
            # Check if this meeting happens on this day
            m_days = [d.lower() for d in m.get('schedule', {}).get('days', [])]
            if day_name in m_days:
                m_hour = m['schedule']['hour']
                m_minute = m['schedule']['minute']
                
                # Mark this specific time as busy
                busy_slots.add(f"{date_str}_{m_hour}_{m_minute}")
        
        # Generate 30-minute slots
        current_h = start_h
        current_m = 0
        
        while current_h < end_h:
            slot_datetime = date_obj.replace(hour=current_h, minute=current_m)
            
            # Next slot time
            next_m = current_m + 30
            next_h = current_h
            if next_m >= 60:
                next_m = 0
                next_h += 1
            
            # Check 1: Future time
            if slot_datetime <= now + timedelta(hours=2):
                current_h, current_m = next_h, next_m
                continue
            
            # Check 2: Overrides (Postponements)
            if group_name and not is_slot_available_for_group(
                teacher_chat_id, 
                date_str, 
                current_h, 
                current_m, 
                group_name
            ):
                current_h, current_m = next_h, next_m
                continue
            
            # Check 3: Regular Schedule Conflict (NEW!)
            slot_key = f"{date_str}_{current_h}_{current_m}"
            if slot_key in busy_slots:
                current_h, current_m = next_h, next_m
                continue
            
            slots.append({
                "date": date_str,
                "hour": current_h,
                "minute": current_m,
                "display": date_obj.strftime("%a %d %b") + f" at {current_h:02d}:{current_m:02d}"
            })
            
            current_h, current_m = next_h, next_m
    
    return slots[:20]


def remove_availability(teacher_chat_id: str, date_str: str) -> bool:
    """Remove availability for a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM teacher_availability 
            WHERE teacher_chat_id = ? AND available_date = ?
        ''', (str(teacher_chat_id), date_str))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"❌ Error removing availability: {e}")
        return False
    finally:
        conn.close()


def clear_past_availability():
    """Clean up old availability entries. Call this from scheduler."""
    conn = get_connection()
    cursor = conn.cursor()
    
    today_obj = datetime.now().date()
    
    try:
        # Get all entries and filter by date
        cursor.execute("SELECT id, available_date FROM teacher_availability")
        rows = cursor.fetchall()
        
        deleted = 0
        for row in rows:
            try:
                date_obj = datetime.strptime(row["available_date"], DATE_FORMAT).date()
                if date_obj < today_obj:
                    cursor.execute("DELETE FROM teacher_availability WHERE id = ?", (row["id"],))
                    deleted += 1
            except ValueError:
                continue
        
        conn.commit()
        if deleted > 0:
            print(f"🧹 Cleaned up {deleted} old availability entries")
    except Exception as e:
        print(f"❌ Error cleaning availability: {e}")
    finally:
        conn.close()


def get_teacher_availability_summary(teacher_chat_id: str) -> str:
    """Get a formatted summary of teacher's availability for display."""
    availability = get_teacher_availability(teacher_chat_id)
    
    if not availability:
        return "No availability set yet."
    
    lines = []
    for entry in availability:
        try:
            date_obj = datetime.strptime(entry["date"], DATE_FORMAT)
            day_name = date_obj.strftime("%A %d %b")
            start = f"{entry['start_hour']:02d}:00"
            end = f"{entry['end_hour']:02d}:00"
            lines.append(f"• {day_name}: {start} - {end}")
        except ValueError:
            continue
    
    return "\n".join(lines) if lines else "No availability set yet."