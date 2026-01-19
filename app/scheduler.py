from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime
from app.config import Config
from app.jitsi_meet import create_jitsi_meeting
from app.telegram_bot import meeting_bot
from app.services.lesson_service import check_lesson_status
from app.services.request_service import cleanup_expired_requests


DAY_MAP = {
    'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
    'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat', 'sunday': 'sun'
}


def create_meeting_job(meeting_config: dict):
    """Job function that checks overrides before creating meeting."""
    tz = pytz.timezone(Config.TIMEZONE)
    today = datetime.now(tz).strftime("%Y-%m-%d")
    
    meeting_id = meeting_config['id']
    
    # Check for overrides
    status = check_lesson_status(meeting_id, today)
    
    if status['status'] == 'cancelled':
        print(f"⏭️ Skipping {meeting_config['title']} - CANCELLED")
        return
    
    if status['status'] == 'postponed':
        print(f"⏭️ Skipping {meeting_config['title']} - POSTPONED to {status['new_date']}")
        return
    
    # Create meeting
    print(f"⏰ Creating meeting: {meeting_config['title']}")
    
    meeting = create_jitsi_meeting(title=meeting_config['title'])
    
    print(f"✅ Meeting created: {meeting['meet_link']}")
    
    chat_id = meeting_config.get('chat_id')
    meeting_bot.send_meeting_link_sync(meeting, chat_id)
    
    print(f"✅ Sent to chat: {chat_id}")


def setup_scheduler() -> BackgroundScheduler:
    """Create and configure scheduler."""
    scheduler = BackgroundScheduler(timezone=pytz.timezone(Config.TIMEZONE))
    
    meetings = Config.load_meetings()
    
    if not meetings:
        print("⚠️ No meetings configured!")
        return scheduler
    
    print(f"📅 Loading {len(meetings)} meetings...")
    print("=" * 50)
    
    for meeting_config in meetings:
        schedule = meeting_config.get('schedule', {})
        days = schedule.get('days', [])
        hour = schedule.get('hour', 9)
        minute = schedule.get('minute', 0)
        
        cron_days = ','.join([DAY_MAP.get(d.lower(), d) for d in days])
        
        if not cron_days:
            continue
        
        scheduler.add_job(
            create_meeting_job,
            CronTrigger(
                day_of_week=cron_days,
                hour=hour,
                minute=minute,
                timezone=pytz.timezone(Config.TIMEZONE)
            ),
            args=[meeting_config],
            id=meeting_config['id'],
            name=meeting_config['title']
        )
        
        print(f"✅ {meeting_config['title']}")
        print(f"   📆 Days: {', '.join(days)}")
        print(f"   ⏰ Time: {hour:02d}:{minute:02d}")
    
    # Cleanup expired requests daily
    scheduler.add_job(
        cleanup_expired_requests,
        CronTrigger(hour=0, minute=0),
        id='cleanup_requests',
        name='Cleanup expired requests'
    )
    
    print("=" * 50)
    return scheduler


def run_meeting_now(meeting_id: str):
    """Run a specific meeting immediately."""
    meetings = Config.load_meetings()
    
    for meeting_config in meetings:
        if meeting_config['id'] == meeting_id:
            print(f"🚀 Running: {meeting_config['title']}")
            create_meeting_job(meeting_config)
            return True
    
    print(f"❌ Meeting not found: {meeting_id}")
    return False


def list_meetings():
    """List all configured meetings."""
    meetings = Config.load_meetings()
    
    if not meetings:
        print("No meetings configured.")
        return
    
    print(f"\n📋 Configured Meetings ({len(meetings)})")
    print("=" * 50)
    
    for m in meetings:
        schedule = m.get('schedule', {})
        days = ', '.join(schedule.get('days', []))
        time = f"{schedule.get('hour', 0):02d}:{schedule.get('minute', 0):02d}"
        
        print(f"""
🆔 {m['id']}
   📌 Title: {m['title']}
   📆 Days: {days}
   ⏰ Time: {time}
   💬 Chat ID: {m.get('chat_id')}
""")