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
# NEW IMPORT
from app.database.db import get_connection

# Set up logging
logger = logging.getLogger(__name__)

DAY_MAP = {
    'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
    'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'
}

def load_meetings():
    """Load meetings using Config helper."""
    return Config.load_meetings()

async def send_meeting_to_recipients(app: Application, meeting_config: dict, meeting_data: dict, prefix: str = ""):
    """Helper to send the link to teacher and students."""
    group_name = meeting_config.get('group_name')
    title = meeting_config.get('title')
    link = meeting_data.get('meet_link')
    
    # Message Text
    msg_text = (
        f"{prefix}<b>{title}</b>\n"
        f"👥 Group: {group_name}\n"
        f"🔗 <a href='{link}'>Click to Join Class</a>"
    )

    recipients = set()

    if group_name:
        teacher = get_teacher_for_group(group_name)
        if teacher and teacher.get('chat_id'):
            recipients.add(str(teacher['chat_id']))

        students = get_students_in_group(group_name)
        for student in students:
            if student.get('chat_id'):
                recipients.add(str(student['chat_id']))

    if meeting_config.get('chat_id'):
        recipients.add(str(meeting_config['chat_id']))

    if not recipients:
        logger.warning(f"⚠️ No recipients found for group {group_name}")
        return

    for chat_id in recipients:
        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text=msg_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info(f"✅ Sent link to {chat_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send to {chat_id}: {e}")

async def job_send_lesson(app: Application, meeting_config: dict):
    """The main job that runs at the scheduled time."""
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
        
        run_time = now.replace(hour=new_hour, minute=new_minute, second=0, microsecond=0)
        
        if run_time > now:
            job_id = f"postponed_{meeting_id}_{today}"
            if not scheduler.get_job(job_id):
                logger.info(f"📅 Scheduling postponed lesson: {meeting_config['title']} at {new_hour}:{new_minute}")
                scheduler.add_job(
                    job_send_postponed,
                    'date',
                    run_date=run_time,
                    args=[app, meeting_config],
                    id=job_id
                )

async def job_send_postponed(app: Application, meeting_config: dict):
    """Sends the link for a POSTPONED lesson."""
    logger.info(f"⏰ Creating POSTPONED meeting: {meeting_config['title']}")
    meeting_data = create_jitsi_meeting(title=meeting_config['title'])
    await send_meeting_to_recipients(app, meeting_config, meeting_data, prefix="🔄 <b>(Rescheduled)</b> ")

# === NEW FUNCTION ===
async def job_keep_db_alive():
    """Pings the database to prevent Neon from sleeping (Free Tier Fix)."""
    try:
        # get_connection() opens a connection. 
        # cursor.execute runs a tiny query.
        # close() ensures we don't leak connections.
        conn = get_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
        # logger.info("💓 DB Heartbeat sent") # Uncomment to see in logs
    except Exception as e:
        logger.error(f"❌ DB Heartbeat failed: {e}")

def start_scheduler(app: Application):
    """Initialize and start the scheduler."""
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(Config.TIMEZONE))
    
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

        scheduler.add_job(
            job_send_lesson,
            CronTrigger(day_of_week=cron_days, hour=hour, minute=minute),
            args=[app, m],
            id=m['id'],
            replace_existing=True
        )

    # Check for postponed lessons every 30 mins
    scheduler.add_job(
        job_check_and_schedule_postponed,
        'interval',
        minutes=30,
        args=[app, scheduler],
        id='check_postponed_interval',
        replace_existing=True
    )
    
    # Run once at startup
    scheduler.add_job(
        job_check_and_schedule_postponed,
        'date',
        run_date=datetime.now(pytz.timezone(Config.TIMEZONE)),
        args=[app, scheduler]
    )

    # === NEW HEARTBEAT JOB ===
    # Run every 4 minutes (Neon sleeps after 5 mins)
    scheduler.add_job(
        job_keep_db_alive,
        'interval',
        minutes=4,
        id='db_heartbeat',
        replace_existing=True
    )

    scheduler.start()
    print("🚀 Scheduler started.")