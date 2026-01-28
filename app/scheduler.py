from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime
from app.config import Config
from app.jitsi_meet import create_jitsi_meeting
from app.telegram_bot import meeting_bot
from app.services.lesson_service import check_lesson_status
from app.services.request_service import cleanup_expired_requests
from app.services.lesson_service import get_all_postponed_to_date, check_lesson_status


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
        print(f"⏭️ Skipping {meeting_config['title']} - POSTPONED to {status.get('new_date', 'unknown')}")
        return
    
    # Create meeting
    print(f"⏰ Creating meeting: {meeting_config['title']}")
    
    meeting = create_jitsi_meeting(title=meeting_config['title'])
    
    print(f"✅ Meeting created: {meeting['meet_link']}")
    
    chat_id = meeting_config.get('chat_id')
    meeting_bot.send_meeting_link_sync(meeting, chat_id)
    
    print(f"✅ Sent to chat: {chat_id}")
    
def check_and_schedule_postponed_lessons():
    """Check for lessons postponed to today and schedule them."""
    from app.services.lesson_service import get_all_postponed_to_date
    
    tz = pytz.timezone(Config.TIMEZONE)
    today = datetime.now(tz).strftime("%Y-%m-%d")
    
    postponed_today = get_all_postponed_to_date(today)
    
    for override in postponed_today:
        meeting_id = override['meeting_id']
        new_hour = override['new_hour']
        new_minute = override['new_minute'] or 0
        
        # Find the meeting config
        meeting_config = None
        for m in load_meetings():  # You'll need to have this function
            if m['id'] == meeting_id:
                meeting_config = m
                break
        
        if not meeting_config:
            print(f"⚠️ Meeting config not found for {meeting_id}")
            continue
        
        # Schedule at new time
        run_time = datetime.now(tz).replace(hour=new_hour, minute=new_minute, second=0, microsecond=0)
        
        if run_time > datetime.now(tz):
            print(f"📅 Scheduling postponed lesson: {meeting_config['title']} at {new_hour:02d}:{new_minute:02d}")
            scheduler.add_job(
                create_postponed_meeting_job,
                'date',
                run_date=run_time,
                args=[meeting_config],
                id=f"postponed_{meeting_id}_{today}",
                replace_existing=True
            )


def create_postponed_meeting_job(meeting_config: dict):
    """Send meeting link for a postponed lesson."""
    print(f"⏰ Creating POSTPONED meeting: {meeting_config['title']}")
    
    meeting = create_jitsi_meeting(title=meeting_config['title'])
    
    print(f"✅ Meeting created: {meeting['meet_link']}")
    
    chat_id = meeting_config.get('chat_id')
    meeting_bot.send_meeting_link_sync(meeting, chat_id)
    
    print(f"✅ Sent to chat: {chat_id}")


def load_meetings() -> list:
    """Load meetings from JSON file."""
    import json
    try:
        with open('meetings.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('meetings', [])
    except Exception as e:
        print(f"Error loading meetings: {e}")
        return []


def check_and_schedule_postponed_lessons():
    """Check for lessons postponed to today and schedule them."""
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    today = now.strftime("%Y-%m-%d")
    
    postponed_today = get_all_postponed_to_date(today)
    
    if not postponed_today:
        print(f"📅 No postponed lessons for today ({today})")
        return
    
    meetings = load_meetings()
    
    for override in postponed_today:
        meeting_id = override['meeting_id']
        new_hour = override['new_hour']
        new_minute = override['new_minute'] or 0
        
        # Find the meeting config
        meeting_config = None
        for m in meetings:
            if m['id'] == meeting_id:
                meeting_config = m
                break
        
        if not meeting_config:
            print(f"⚠️ Meeting config not found for {meeting_id}")
            continue
        
        # Check if the time has passed
        run_time = now.replace(hour=new_hour, minute=new_minute, second=0, microsecond=0)
        
        if run_time > now:
            print(f"📅 Scheduling postponed lesson: {meeting_config['title']} at {new_hour:02d}:{new_minute:02d}")
            
            global scheduler
            scheduler.add_job(
                create_postponed_meeting_job,
                'date',
                run_date=run_time,
                args=[meeting_config],
                id=f"postponed_{meeting_id}_{today}",
                replace_existing=True
            )
        else:
            print(f"⏭️ Postponed lesson time already passed: {meeting_config['title']} at {new_hour:02d}:{new_minute:02d}")


def create_postponed_meeting_job(meeting_config: dict):
    """Send meeting link for a postponed lesson."""
    print(f"⏰ Creating POSTPONED meeting: {meeting_config['title']}")
    
    meeting = create_jitsi_meeting(title=meeting_config['title'])
    
    print(f"✅ Meeting created: {meeting['meet_link']}")
    
    chat_id = meeting_config.get('chat_id')
    meeting_bot.send_meeting_link_sync(meeting, chat_id)
    
    print(f"✅ Sent POSTPONED meeting to chat: {chat_id}")

def setup_scheduler() -> BackgroundScheduler:
    """Create and configure scheduler."""
    scheduler = BackgroundScheduler(timezone=pytz.timezone(Config.TIMEZONE))
    
    meetings = Config.load_meetings()
    
    if not meetings:
        print("⚠️ No meetings configured!")
        return scheduler
    
    print(f"📅 Loading {len(meetings)} meetings...")
    print("=" * 50)
    
    scheduler.add_job(
        check_and_schedule_postponed_lessons,
        'cron',
        hour=0,
        minute=5,
        id='check_postponed_daily',
        replace_existing=True
    )
    
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