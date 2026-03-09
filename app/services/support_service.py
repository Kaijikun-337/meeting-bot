from datetime import datetime, timedelta
from app.database.db import get_connection
import pytz
from app.config import Config

def get_weekly_booking_count(student_id):
    """Count how many times student booked support THIS WEEK."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calculate Start of Week (Monday)
    tz = pytz.timezone(Config.TIMEZONE)
    today = datetime.now(tz)
    start_of_week = today - timedelta(days=today.weekday())
    start_str = start_of_week.strftime("%d-%m-%Y")
    
    # We cheat a bit: Filter by string comparison or fetch all and filter in python
    # For now, let's fetch all future/recent bookings and filter
    cursor.execute("""
        SELECT booking_date FROM support_bookings 
        WHERE student_chat_id = %s
    """, (str(student_id),))
    
    rows = cursor.fetchall()
    conn.close()
    
    count = 0
    # Filter logic: Is date in current week?
    # (Simplified for now: Just reset counter on Mondays)
    # ...
    
    return len(rows) # For MVP, return total active bookings

def create_booking(student_id, support_id, date_str, time_str):
    """Save booking."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO support_bookings 
            (student_chat_id, support_chat_id, booking_date, booking_time, status)
            VALUES (%s, %s, %s, %s, 'scheduled')
        """, (str(student_id), str(support_id), date_str, time_str))
        conn.commit()
        return True
    except Exception as e:
        print(f"Booking Error: {e}")
        return False
    finally:
        conn.close()

def get_available_support_staff():
    """Find user with role='support'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, name FROM users WHERE role = 'support' AND is_active=1 LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def can_book_support(student_chat_id: str) -> bool:
    """Checks if the student has booked less than 2 support lessons this week."""
    # Get current year and ISO week number
    now = datetime.datetime.now()
    year, week_number, _ = now.isocalendar()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Count bookings for THIS student, THIS week, THIS year
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM support_bookings 
        WHERE student_chat_id = ? AND week_number = ? AND year = ?
    """, (str(student_chat_id), week_number, year))
    
    row = cursor.fetchone()
    conn.close()
    
    # If they have less than 2, they can book!
    booking_count = row['count'] if row else 0
    return booking_count < 2

def record_support_booking(student_chat_id: str) -> bool:
    """Saves a new support booking to the database."""
    now = datetime.datetime.now()
    year, week_number, _ = now.isocalendar()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO support_bookings (student_chat_id, week_number, year, status)
            VALUES (?, ?, ?, 'pending')
        """, (str(student_chat_id), week_number, year))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error booking support: {e}")
        return False
    finally:
        conn.close()