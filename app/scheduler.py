import pytz
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.constants import ParseMode
from telegram.ext import Application

from app.config import Config
from app.jitsi_meet import create_jitsi_meeting
from app.services.lesson_service import (
    check_lesson_status, 
    get_all_postponed_to_date
)
from app.services.user_service import (
    get_teacher_for_group, 
    get_students_in_group
)
from app.database.db import get_connection
from app.utils.localization import get_text, get_user_language

# Set up logging
logger = logging.getLogger(__name__)

DAY_MAP = {
    'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
    'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'
}

def load_meetings():
    """Load meetings using Config helper."""
    return Config.load_meetings()

async def send_meeting_to_recipients(app: Application, meeting_config: dict, meeting_data: dict, prefix_key: str = None):
    """
    Sends localized, rich formatted message to teacher and students.
    """
    # 1. Gather Data
    group_name = meeting_config.get('group_name', 'Unknown')
    title = meeting_config.get('title', 'Lesson')
    desc = meeting_config.get('description', '')
    subject = meeting_config.get('subject', '')
    teacher_name = meeting_config.get('teacher_name', '')
    link = meeting_data.get('meet_link')
    
    # Format time (e.g., 19:00)
    # We use the schedule from config to show the "Official" time
    sch = meeting_config.get('schedule', {})
    time_str = f"{sch.get('hour', 0):02d}:{sch.get('minute', 0):02d}"

    # 2. Gather Recipients (Set of IDs)
    recipients = set()

    if group_name:
        teacher = get_teacher_for_group(group_name)
        if teacher and teacher.get('chat_id'):
            recipients.add(str(teacher['chat_id']))

        students = get_students_in_group(group_name)
        for student in students:
            if student.get('chat_id'):
                recipients.add(str(student['chat_id']))

    # Fallback to manual chat_id in JSON
    if meeting_config.get('chat_id'):
        recipients.add(str(meeting_config['chat_id']))

    if not recipients:
        logger.warning(f"⚠️ No recipients found for group {group_name}")
        return

    # 3. Send Localized Message to Each Person
    for chat_id in recipients:
        try:
            lang = get_user_language(chat_id)
            
            # Build Message Parts
            header = get_text('lesson_alert_title', lang)
            if prefix_key:
                header = get_text(prefix_key, lang) + header
                
            details = get_text('lesson_details', lang).format(
                title=title,
                time=time_str,
                group=group_name,
                desc=desc,
                subject=subject,
                teacher=teacher_name
            )
            
            join_section = get_text('lesson_join', lang).format(link=link)
            footer = get_text('lesson_click_hint', lang)
            
            full_text = f"{header}\n\n{details}\n\n{join_section}\n\n{footer}"

            await app.bot.send_message(
                chat_id=chat_id,
                text=full_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info(f"✅ Sent link to {chat_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send to {chat_id}: {e}")


async def job_send_lesson(app: Application, meeting_config: dict):
    """The main job that runs at the scheduled time."""
    # Ensure we use Tashkent time for checking "Today"
    tz = pytz.timezone(Config.TIMEZONE)
    today = datetime.now(tz).strftime("%d-%m-%Y")
    meeting_id = meeting_config['id']

    status = check_lesson_status(meeting_id, today)

    if status['status'] == 'cancelled':
        logger.info(f"⏭️ Skipping {meeting_config['title']} - CANCELLED today.")
        return

    if status['status'] == 'postponed':
        logger.info(f"⏭️ Skipping {meeting_config['title']} - POSTPONED to {status.get('new_date')}")
        return

    logger.info(f"⏰ Creating meeting: {meeting_config['title']}")
    meeting_data = create_jitsi_meeting(title=meeting_config['title'])
    await send_meeting_to_recipients(app, meeting_config, meeting_data)


async def job_check_and_schedule_postponed(app: Application, scheduler: AsyncIOScheduler):
    """Runs periodically to check if any postponed lessons are due TODAY."""
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    today = now.strftime("%d-%m-%Y")
    
    postponed_today = get_all_postponed_to_date(today)
    
    if not postponed_today:
        return

    meetings = load_meetings()
    
    for override in postponed_today:
        meeting_id = override['meeting_id']
        new_hour = override['new_hour']
        new_minute = override['new_minute'] or 0
        
        meeting_config = next((m for m in meetings if m['id'] == meeting_id), None)
        if not meeting_config:
            continue
        
        # Create a temp config with the NEW time for display purposes
        temp_config = meeting_config.copy()
        temp_config['schedule'] = {'hour': new_hour, 'minute': new_minute}
        
        run_time = now.replace(hour=new_hour, minute=new_minute, second=0, microsecond=0)
        
        if run_time > now:
            job_id = f"postponed_{meeting_id}_{today}"
            if not scheduler.get_job(job_id):
                logger.info(f"📅 Scheduling postponed lesson: {meeting_config['title']} at {new_hour}:{new_minute}")
                scheduler.add_job(
                    job_send_postponed,
                    'date',
                    run_date=run_time,
                    args=[app, temp_config], # Pass temp config with new time
                    id=job_id
                )

async def job_send_postponed(app: Application, meeting_config: dict):
    """Sends the link for a POSTPONED lesson."""
    logger.info(f"⏰ Creating POSTPONED meeting: {meeting_config['title']}")
    meeting_data = create_jitsi_meeting(title=meeting_config['title'])
    await send_meeting_to_recipients(app, meeting_config, meeting_data, prefix_key="rescheduled_prefix")

async def job_keep_db_alive():
    """Pings the database to prevent Neon from sleeping."""
    try:
        conn = get_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
    except Exception as e:
        logger.error(f"❌ DB Heartbeat failed: {e}")

def start_scheduler(app: Application):
    """Initialize and start the scheduler."""
    # 1. FORCE TIMEZONE HERE
    tz = pytz.timezone(Config.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)
    
    meetings = load_meetings()
    if not meetings:
        print("⚠️ No meetings configured in meetings.json")
        return

    print(f"📅 Loading {len(meetings)} meetings into scheduler...")

    for m in meetings:
        schedule = m.get('schedule', {})
        days = schedule.get('days', [])
        hour = schedule.get('hour', 9)
        minute = schedule.get('minute', 0)
        
        cron_days = ",".join([DAY_MAP.get(d.lower(), d)[:3] for d in days])
        
        if not cron_days: 
            continue

        # 2. FORCE TIMEZONE IN CRON TRIGGER
        # This tells scheduler: "19:00 means 19:00 IN TASHKENT", not UTC.
        scheduler.add_job(
            job_send_lesson,
            CronTrigger(day_of_week=cron_days, hour=hour, minute=minute, timezone=tz),
            args=[app, m],
            id=m['id'],
            replace_existing=True
        )
        print(f"   ✅ Added: {m['title']} ({cron_days} at {hour:02d}:{minute:02d} {Config.TIMEZONE})")

    scheduler.add_job(
        job_check_and_schedule_postponed,
        'interval',
        minutes=30,
        args=[app, scheduler],
        id='check_postponed_interval',
        replace_existing=True
    )
    
    # Run check immediately on start
    scheduler.add_job(
        job_check_and_schedule_postponed,
        'date',
        run_date=datetime.now(tz),
        args=[app, scheduler]
    )

    scheduler.add_job(
        job_keep_db_alive,
        'interval',
        minutes=4,
        id='db_heartbeat',
        replace_existing=True
    )

    scheduler.start()
    print(f"🚀 Scheduler started in timezone: {Config.TIMEZONE}")