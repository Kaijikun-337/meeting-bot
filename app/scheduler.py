import pytz
import logging
from datetime import datetime, timedelta
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

logger = logging.getLogger(__name__)

DAY_MAP = {
    'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
    'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'
}

def load_meetings():
    return Config.load_meetings()

async def send_meeting_to_recipients(app: Application, meeting_config: dict, meeting_data: dict, prefix_key: str = None):
    """Sends localized, rich formatted message to teacher and students."""
    group_name = meeting_config.get('group_name', 'Unknown')
    title = meeting_config.get('title', 'Lesson')
    desc = meeting_config.get('description', '')
    subject = meeting_config.get('subject', '')
    teacher_name = meeting_config.get('teacher_name', '')
    link = meeting_data.get('meet_link')
    
    sch = meeting_config.get('schedule', {})
    time_str = f"{sch.get('hour', 0):02d}:{sch.get('minute', 0):02d}"

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
            lang = get_user_language(chat_id)
            
            header = get_text('lesson_alert_title', lang)
            if prefix_key:
                header = get_text(prefix_key, lang) + header
                
            details = get_text('lesson_details', lang).format(
                title=title, time=time_str, group=group_name,
                desc=desc, subject=subject, teacher=teacher_name
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
    """Send lesson link at start time."""
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

async def job_ask_recording(app: Application, meeting_config: dict):
    """Remind teacher to upload recording after lesson."""
    teacher_name = meeting_config.get('teacher_name')
    group_name = meeting_config.get('group_name')
    teacher_id = None
    
    if group_name:
        teacher = get_teacher_for_group(group_name)
        if teacher:
            teacher_id = teacher.get('chat_id')
            
    if not teacher_id:
        teacher_id = meeting_config.get('teacher_chat_id') or meeting_config.get('chat_id')
    
    if not teacher_id:
        return 
        
    title = meeting_config.get('title')
    
    msg = (
        f"🎥 <b>Lesson Finished: {title}</b>\n\n"
        f"Please upload the video recording now.\n"
        f"⚠️ <b>Limit:</b> 2GB (Telegram)\n"
        f"💡 <b>Tip:</b> Use 720p resolution.\n\n"
        f"🚀 <b>To send it to students:</b>\n"
        f"1. Type /homework\n"
        f"2. Upload the video\n"
        f"3. Select the group"
    )
    
    try:
        await app.bot.send_message(chat_id=teacher_id, text=msg, parse_mode=ParseMode.HTML)
        logger.info(f"✅ Sent recording reminder to {teacher_name}")
    except Exception as e:
        logger.error(f"❌ Failed to send recording reminder: {e}")

async def job_check_and_schedule_postponed(app: Application, scheduler: AsyncIOScheduler):
    """Check daily for postponed lessons."""
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    today = now.strftime("%d-%m-%Y")
    
    postponed_today = get_all_postponed_to_date(today)
    if not postponed_today: return

    meetings = load_meetings()
    
    for override in postponed_today:
        meeting_id = override['meeting_id']
        new_hour = override['new_hour']
        new_minute = override['new_minute'] or 0
        
        meeting_config = next((m for m in meetings if m['id'] == meeting_id), None)
        if not meeting_config: continue
        
        # Temp config with new time
        temp_config = meeting_config.copy()
        temp_config['schedule'] = {'hour': new_hour, 'minute': new_minute}
        
        run_time = now.replace(hour=new_hour, minute=new_minute, second=0, microsecond=0)
        
        if run_time > now:
            job_id = f"postponed_{meeting_id}_{today}"
            if not scheduler.get_job(job_id):
                logger.info(f"📅 Scheduling postponed: {meeting_config['title']} at {new_hour}:{new_minute}")
                scheduler.add_job(
                    job_send_postponed,
                    'date',
                    run_date=run_time,
                    args=[app, temp_config],
                    id=job_id
                )

async def job_send_postponed(app: Application, meeting_config: dict):
    """Send link for postponed lesson."""
    logger.info(f"⏰ Creating POSTPONED meeting: {meeting_config['title']}")
    meeting_data = create_jitsi_meeting(title=meeting_config['title'])
    await send_meeting_to_recipients(app, meeting_config, meeting_data, prefix_key="rescheduled_prefix")

async def job_keep_db_alive():
    """Heartbeat."""
    try:
        conn = get_connection()
        conn.cursor().execute("SELECT 1")
        conn.close()
    except Exception as e:
        logger.error(f"❌ DB Heartbeat failed: {e}")

def start_scheduler(app: Application):
    """Initialize and start the scheduler."""
    tz = pytz.timezone(Config.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)
    
    meetings = load_meetings()
    if not meetings:
        print("⚠️ No meetings configured")
        return

    print(f"📅 Loading {len(meetings)} meetings into scheduler...")

    for m in meetings:
        schedule = m.get('schedule', {})
        days = schedule.get('days', [])
        hour = schedule.get('hour', 9)
        minute = schedule.get('minute', 0)
        
        cron_days = ",".join([DAY_MAP.get(d.lower(), d)[:3] for d in days])
        if not cron_days: continue

        # --- THE OVERLAP FIX IS HERE ---
        # We use dict(m) to create a COPY of the meeting data.
        # This prevents the "Reference Bug" where all jobs point to the last meeting.
        scheduler.add_job(
            job_send_lesson,
            CronTrigger(day_of_week=cron_days, hour=hour, minute=minute, timezone=tz),
            args=[app, dict(m)], 
            id=m['id'],
            replace_existing=True
        )

        # Recording Reminder Job
        duration = m.get('duration_minutes', 60)
        end_minute = minute + duration
        end_hour = hour + (end_minute // 60)
        end_minute = end_minute % 60
        end_hour = end_hour % 24
        
        scheduler.add_job(
            job_ask_recording,
            CronTrigger(day_of_week=cron_days, hour=end_hour, minute=end_minute, timezone=tz),
            args=[app, dict(m)],
            id=f"{m['id']}_rec",
            replace_existing=True
        )
        
        print(f"   ✅ {m['title']}: Link @ {hour:02d}:{minute:02d}")

    # Maintenance Jobs
    scheduler.add_job(job_check_and_schedule_postponed, 'interval', minutes=30, args=[app, scheduler], id='check_postponed_interval', replace_existing=True)
    scheduler.add_job(job_check_and_schedule_postponed, 'date', run_date=datetime.now(tz), args=[app, scheduler])
    scheduler.add_job(job_keep_db_alive, 'interval', minutes=4, id='db_heartbeat', replace_existing=True)

    scheduler.start()
    print(f"🚀 Scheduler started in timezone: {Config.TIMEZONE}")