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

    # 1. Add Teacher
    if group_name:
        teacher = get_teacher_for_group(group_name)
        if teacher and teacher.get('chat_id'):
            recipients.add(str(teacher['chat_id']))

        # 2. Add Students
        students = get_students_in_group(group_name)
        for student in students:
            if student.get('chat_id'):
                recipients.add(str(student['chat_id']))

    # 3. Fallback to manual chat_id in JSON
    if meeting_config.get('chat_id'):
        recipients.add(str(meeting_config['chat_id']))

    if not recipients:
        logger.warning(f"⚠️ No recipients found for group {group_name}")
        return

    # Send to all
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
    """
    The main job that runs at the scheduled time.
    Checks for cancellations/postponements before sending.
    """
    tz = pytz.timezone(Config.TIMEZONE)
    today = datetime.now(tz).strftime("%d-%m-%Y")
    meeting_id = meeting_config['id']

    # 1. Check Status (Cancelled/Postponed?)
    status = check_lesson_status(meeting_id, today)

    if status['status'] == 'cancelled':
        logger.info(f"⏭️ Skipping {meeting_config['title']} - CANCELLED today.")
        return

    if status['status'] == 'postponed':
        logger.info(f"⏭️ Skipping {meeting_config['title']} - POSTPONED to {status.get('new_date')}")
        return

    # 2. Create Jitsi
    logger.info(f"⏰ Creating meeting: {meeting_config['title']}")
    meeting_data = create_jitsi_meeting(title=meeting_config['title'])

    # 3. Send
    await send_meeting_to_recipients(app, meeting_config, meeting_data)


async def job_check_and_schedule_postponed(app: Application, scheduler: AsyncIOScheduler):
    """
    Runs periodically to check if any postponed lessons are due TODAY.
    """
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
        
        # Find config
        meeting_config = next((m for m in meetings if m['id'] == meeting_id), None)
        if not meeting_config:
            continue
        
        # Calculate run time
        run_time = now.replace(hour=new_hour, minute=new_minute, second=0, microsecond=0)
        
        # If the time is in the future (and hasn't been scheduled yet), schedule it
        if run_time > now:
            job_id = f"postponed_{meeting_id}_{today}"
            
            # Avoid duplicates
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
    
    # Send with a prefix to indicate it's the rescheduled one
    await send_meeting_to_recipients(app, meeting_config, meeting_data, prefix="🔄 <b>(Rescheduled)</b> ")


def start_scheduler(app: Application):
    """
    Initialize and start the scheduler.
    """
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(Config.TIMEZONE))
    
    meetings = load_meetings()
    if not meetings:
        print("⚠️ No meetings configured in meetings.json")
        return

    print(f"📅 Loading {len(meetings)} meetings into scheduler...")

    # 1. Schedule Standard Lessons
    for m in meetings:
        schedule = m.get('schedule', {})
        days = schedule.get('days', []) # ['monday', 'wednesday']
        hour = schedule.get('hour', 9)
        minute = schedule.get('minute', 0)
        
        # Convert ['monday', 'friday'] -> 'mon,fri'
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
        print(f"   ✅ Added: {m['title']} ({cron_days} at {hour:02d}:{minute:02d})")

    # 2. Schedule "Check for Postponed" Job (Runs every 30 mins)
    scheduler.add_job(
        job_check_and_schedule_postponed,
        'interval',
        minutes=30,
        args=[app, scheduler],
        id='check_postponed_interval',
        replace_existing=True
    )
    
    # 3. Also run "Check Postponed" once immediately on startup
    scheduler.add_job(
        job_check_and_schedule_postponed,
        'date',
        run_date=datetime.now(pytz.timezone(Config.TIMEZONE)),
        args=[app, scheduler]
    )

    scheduler.start()
    print("🚀 Scheduler started.")