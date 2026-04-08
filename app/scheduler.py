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
    """Sends localized message to teacher and students with auto-healing DB logic."""
    group_name = meeting_config.get('group_name', 'Unknown')
    title = meeting_config.get('title', 'Lesson')
    desc = meeting_config.get('description', '')
    subject = meeting_config.get('subject', '')
    link = meeting_data.get('meet_link')
    
    json_teacher_name = meeting_config.get('teacher_name')
    
    sch = meeting_config.get('schedule', {})
    time_str = f"{sch.get('hour', 0):02d}:{sch.get('minute', 0):02d}"

    recipients = set()
    db_teacher_found = False
    current_teacher_name = json_teacher_name
    teacher = None  # ← Initialize here so it always exists!

    # --- PHASE 1: SMART TEACHER ROUTING (AUTO-HEALING) ---
    if group_name and group_name != 'Unknown':
        from app.services.user_service import (
            get_teacher_for_group, 
            get_user_by_name, 
            update_teacher_group_assignment,
            get_students_in_group
        )
        
        teacher = get_teacher_for_group(group_name)
        
        # MISMATCH CHECK
        if teacher and json_teacher_name and teacher.get('name') != json_teacher_name:
            logger.info(f"🔄 Mismatch for {group_name}. DB: {teacher.get('name')} | JSON: {json_teacher_name}")
            teacher = None

        # AUTO-HEAL (inside the if block!)
        if not teacher and json_teacher_name:
            teacher = get_user_by_name(json_teacher_name)
            if teacher:
                logger.info(
                    f"✅ Found {json_teacher_name} (ID: {teacher['chat_id']}). "
                    f"Auto-healing DB..."
                )
                update_teacher_group_assignment(
                    group_name, 
                    teacher['chat_id'],
                    subject=meeting_config.get('subject')
                )
            else:
                logger.warning(
                    f"❌ Teacher '{json_teacher_name}' not found in users table. "
                    f"Has this teacher registered with the bot?"
                )

        # ADD TEACHER TO RECIPIENTS (inside the if block!)
        if teacher and teacher.get('chat_id'):
            teacher_id = str(teacher['chat_id'])
            recipients.add(teacher_id)
            current_teacher_name = teacher.get('name', json_teacher_name)
            db_teacher_found = True

    # --- PHASE 2: FALLBACKS ---
    if not db_teacher_found:
        json_id = meeting_config.get('teacher_chat_id') or meeting_config.get('chat_id')
        if json_id:
            recipients.add(str(json_id))
            logger.warning(f"⚠️ FALLBACK: Using manual JSON ID: {json_id}")

    # --- PHASE 3: STUDENTS ---
    if group_name and group_name != 'Unknown':
        from app.services.user_service import get_students_in_group
        students = get_students_in_group(group_name)
        for student in students:
            if student.get('chat_id'):
                recipients.add(str(student['chat_id']))

    # --- PHASE 4: FINAL CHECK ---
    if not recipients:
        logger.warning(f"⚠️ No recipients found for group {group_name}")
        return

    logger.info(f"📨 Sending to {len(recipients)} recipients for {title}")

    # --- PHASE 5: SENDING ---
    for chat_id in recipients:
        try:
            lang = get_user_language(chat_id)
            
            header = get_text('lesson_alert_title', lang)
            if prefix_key:
                header = get_text(prefix_key, lang) + header
                
            details = get_text('lesson_details', lang).format(
                title=title, time=time_str, group=group_name,
                desc=desc, subject=subject, teacher=current_teacher_name
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
    """Remind teacher to upload recording AND mark attendance."""
    group_name = meeting_config.get('group_name')
    
    # --- SMART TEACHER LOOKUP (mirrors send_meeting_to_recipients) ---
    json_teacher_name = meeting_config.get('teacher_name')
    teacher = None
    teacher_id = None
    teacher_name = json_teacher_name or 'Teacher'

    if group_name:
        from app.services.user_service import (
            get_teacher_for_group,
            get_user_by_name,
            update_teacher_group_assignment
        )
        
        teacher = get_teacher_for_group(group_name)
        
        # Mismatch check: JSON is authority
        if teacher and json_teacher_name and teacher.get('name') != json_teacher_name:
            logger.info(f"🔄 Recording reminder: teacher mismatch for {group_name}")
            teacher = None
        
        # Auto-heal if needed
        if not teacher and json_teacher_name:
            teacher = get_user_by_name(json_teacher_name)
            if teacher:
                update_teacher_group_assignment(group_name, teacher['chat_id'])
        
        if teacher and teacher.get('chat_id'):
            teacher_id = teacher['chat_id']
            teacher_name = teacher.get('name', json_teacher_name)
    
    # Fallback
    if not teacher_id:
        teacher_id = meeting_config.get('teacher_chat_id') or meeting_config.get('chat_id')
    
    if not teacher_id:
        logger.warning(f"⚠️ No teacher for recording reminder: {group_name}")
        return 
        
    title = meeting_config.get('title')
    
    # --- VIDEO REMINDER ---
    msg_video = (
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
        await app.bot.send_message(
            chat_id=teacher_id, 
            text=msg_video, 
            parse_mode=ParseMode.HTML
        )
        logger.info(f"✅ Sent recording reminder to {teacher_name}")
    except Exception as e:
        logger.error(f"❌ Failed to send recording reminder: {e}")
    
    # --- ATTENDANCE REMINDER (NO kb - just text) ---
    msg_attend = (
        f"📋 Please mark who was present for "
        f"<b>{group_name}</b> in CRM."
    )
    
    try:
        await app.bot.send_message(
            chat_id=teacher_id, 
            text=msg_attend, 
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"❌ Failed to send attendance reminder: {e}")

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
        
# Helper to freeze data
def create_job_args(app, meeting):
    return [app, dict(meeting)]

async def job_cleanup_expired_keys():
    """Daily cleanup of unactivated registrations."""
    from app.services.user_service import cleanup_expired_keys
    deleted = cleanup_expired_keys(hours=24)
    if deleted > 0:
        logger.info(f"🧹 Auto-cleanup removed {deleted} ghost user(s)")

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

        # 1. SEND LINK JOB (Start Time)
        # Use factory to freeze 'm' and add grace time
        scheduler.add_job(
            job_send_lesson,
            CronTrigger(day_of_week=cron_days, hour=hour, minute=minute, timezone=tz),
            args=create_job_args(app, m), 
            id=m['id'],
            replace_existing=True,
            misfire_grace_time=60 # Allow 60s delay if CPU busy
        )

        # 2. ASK RECORDING JOB (End Time)
        duration = m.get('duration_minutes', 60)
        end_minute = minute + duration
        end_hour = hour + (end_minute // 60)
        end_minute = end_minute % 60
        end_hour = end_hour % 24
        
        scheduler.add_job(
            job_ask_recording,
            CronTrigger(day_of_week=cron_days, hour=end_hour, minute=end_minute, timezone=tz),
            args=create_job_args(app, m),
            id=f"{m['id']}_rec",
            replace_existing=True,
            misfire_grace_time=60
        )

        scheduler.add_job(
            job_check_and_schedule_postponed, 'interval', 
            minutes=30, args=[app, scheduler], 
            id='check_postponed_interval', replace_existing=True
        )
        scheduler.add_job(
            job_check_and_schedule_postponed, 'date', 
            run_date=datetime.now(tz), args=[app, scheduler]
        )
    
        # NEW: Daily cleanup at 3:00 AM
        scheduler.add_job(
            job_cleanup_expired_keys,
            CronTrigger(hour=3, minute=0, timezone=tz),
            id='cleanup_expired_keys',
            replace_existing=True
        )
        
        print(f"   ✅ {m['title']}: Link @ {hour:02d}:{minute:02d}")

    # Maintenance Jobs
    scheduler.add_job(job_check_and_schedule_postponed, 'interval', minutes=30, args=[app, scheduler], id='check_postponed_interval', replace_existing=True)
    scheduler.add_job(job_check_and_schedule_postponed, 'date', run_date=datetime.now(tz), args=[app, scheduler])
    # Note: Heartbeat removed for free tier

    scheduler.start()
    print(f"🚀 Scheduler started in timezone: {Config.TIMEZONE}")