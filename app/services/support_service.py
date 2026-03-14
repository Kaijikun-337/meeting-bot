# app/services/support_service.py

import logging
from datetime import datetime, timedelta
import pytz
from app.database.db import get_connection
from app.config import Config

logger = logging.getLogger(__name__)


def get_available_support_staff():
    """Find first active user with role='support'."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if Config.DATABASE_URL:
            cur.execute(
                "SELECT chat_id, name FROM users "
                "WHERE role = 'support' AND is_active = 1 LIMIT 1"
            )
        else:
            cur.execute(
                "SELECT chat_id, name FROM users "
                "WHERE role = 'support' AND is_active = 1 LIMIT 1"
            )

        row = cur.fetchone()
        if row:
            if isinstance(row, dict):
                return {'chat_id': row['chat_id'], 'name': row['name']}
            else:
                return {'chat_id': row[0], 'name': row[1]}
        return None
    except Exception as e:
        logger.error(f"❌ get_available_support_staff failed: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def get_weekly_booking_count(student_id: str) -> int:
    """Count how many support sessions student booked THIS week (Mon-Sun)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Calculate Monday 00:00 of current week
        tz = pytz.timezone(Config.TIMEZONE)
        now = datetime.now(tz)
        monday = now - timedelta(days=now.weekday())
        monday_str = monday.strftime("%d-%m-%Y")
        sunday = monday + timedelta(days=6)
        sunday_str = sunday.strftime("%d-%m-%Y")

        if Config.DATABASE_URL:
            cur.execute("""
                SELECT COUNT(*) as count FROM support_bookings
                WHERE student_chat_id = %s
                AND week_start = %s
            """, (str(student_id), monday_str))
        else:
            cur.execute("""
                SELECT COUNT(*) as count FROM support_bookings
                WHERE student_chat_id = ?
                AND week_start = ?
            """, (str(student_id), monday_str))

        row = cur.fetchone()
        if row:
            if isinstance(row, dict):
                return row.get('count', 0)
            else:
                return row[0]
        return 0
    except Exception as e:
        logger.error(f"❌ get_weekly_booking_count failed: {e}")
        return 0
    finally:
        cur.close()
        conn.close()


def can_book_support(student_id: str) -> bool:
    """Check if student is under the weekly booking limit."""
    schedule = Config.load_support_schedule()
    max_per_week = 2  # default
    if schedule:
        max_per_week = schedule.get('max_bookings_per_week', 2)

    count = get_weekly_booking_count(student_id)
    logger.info(f"📊 Student {student_id}: {count}/{max_per_week} bookings this week")
    return count < max_per_week


def create_booking(student_id: str, support_id: str, 
                   date_str: str, time_str: str, link: str) -> bool:
    """Save a complete support booking."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Calculate week_start for easy weekly counting
        tz = pytz.timezone(Config.TIMEZONE)
        now = datetime.now(tz)
        monday = now - timedelta(days=now.weekday())
        week_start = monday.strftime("%d-%m-%Y")

        if Config.DATABASE_URL:
            cur.execute("""
                INSERT INTO support_bookings 
                (student_chat_id, support_chat_id, booking_date, 
                 booking_time, jitsi_link, week_start, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'scheduled')
            """, (str(student_id), str(support_id), 
                  date_str, time_str, link, week_start))
        else:
            cur.execute("""
                INSERT INTO support_bookings 
                (student_chat_id, support_chat_id, booking_date, 
                 booking_time, jitsi_link, week_start, status)
                VALUES (?, ?, ?, ?, ?, ?, 'scheduled')
            """, (str(student_id), str(support_id), 
                  date_str, time_str, link, week_start))

        conn.commit()
        logger.info(
            f"✅ Booking saved: student={student_id} "
            f"date={date_str} time={time_str}"
        )
        return True
    except Exception as e:
        logger.error(f"❌ create_booking failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_booked_slots(support_id: str, date_str: str) -> list:
    """Get all booked time slots for a support staff on a given date."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if Config.DATABASE_URL:
            cur.execute("""
                SELECT booking_time FROM support_bookings
                WHERE support_chat_id = %s 
                AND booking_date = %s
                AND status = 'scheduled'
            """, (str(support_id), date_str))
        else:
            cur.execute("""
                SELECT booking_time FROM support_bookings
                WHERE support_chat_id = ? 
                AND booking_date = ?
                AND status = 'scheduled'
            """, (str(support_id), date_str))

        rows = cur.fetchall()
        booked = []
        for row in rows:
            if isinstance(row, dict):
                booked.append(row['booking_time'])
            else:
                booked.append(row[0])
        return booked
    except Exception as e:
        logger.error(f"❌ get_booked_slots failed: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_available_slots(support_id: str) -> list:
    """
    Generate available 30-min slots for the next 7 days
    based on support_schedule.json minus already booked slots.
    """
    schedule = Config.load_support_schedule()
    if not schedule:
        logger.warning("⚠️ No support_schedule.json found")
        return []

    duration = schedule.get('session_duration_minutes', 30)
    week_schedule = schedule.get('schedule', {})

    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    slots = []

    # Generate slots for next 7 days
    day_names = [
        'monday', 'tuesday', 'wednesday', 'thursday',
        'friday', 'saturday', 'sunday'
    ]

    for day_offset in range(7):
        check_date = now + timedelta(days=day_offset)
        day_name = day_names[check_date.weekday()]

        # Is this day in the schedule?
        if day_name not in week_schedule:
            continue

        day_config = week_schedule[day_name]
        start_h, start_m = map(int, day_config['start'].split(':'))
        end_h, end_m = map(int, day_config['end'].split(':'))

        date_str = check_date.strftime("%d-%m-%Y")
        display_date = check_date.strftime("%A %d %B")

        # Get already booked slots for this date
        booked = get_booked_slots(support_id, date_str)

        # Generate time blocks
        slot_time = check_date.replace(
            hour=start_h, minute=start_m, second=0, microsecond=0
        )
        end_time = check_date.replace(
            hour=end_h, minute=end_m, second=0, microsecond=0
        )

        while slot_time + timedelta(minutes=duration) <= end_time:
            time_str = slot_time.strftime("%H:%M")

            # Skip if in the past
            if day_offset == 0 and slot_time <= now:
                slot_time += timedelta(minutes=duration)
                continue

            # Skip if already booked
            if time_str in booked:
                slot_time += timedelta(minutes=duration)
                continue

            slots.append({
                'date': date_str,
                'display': f"{display_date} at {time_str}",
                'hour': slot_time.hour,
                'minute': slot_time.minute
            })

            slot_time += timedelta(minutes=duration)

    logger.info(f"📅 Generated {len(slots)} available support slots")
    return slots