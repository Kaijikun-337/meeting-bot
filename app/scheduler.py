from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from app.config import Config
from app.google_meet import create_meeting
from app.telegram_bot import meeting_bot


# Map day names to cron format
DAY_MAP = {
    'monday': 'mon',
    'tuesday': 'tue',
    'wednesday': 'wed',
    'thursday': 'thu',
    'friday': 'fri',
    'saturday': 'sat',
    'sunday': 'sun'
}


def create_meeting_job(meeting_config: dict):
    """Job function for a specific meeting."""
    print(f"⏰ Creating meeting: {meeting_config['title']}")
    
    # Create meeting
    meeting = create_meeting(
        title=meeting_config['title'],
        duration_minutes=meeting_config.get('duration_minutes', 60),
        description=meeting_config.get('description', '')
    )
    
    print(f"✅ Meeting created: {meeting['meet_link']}")
    
    # Send to specific chat ID
    chat_id = meeting_config.get('chat_id')
    meeting_bot.send_meeting_link_sync(meeting, chat_id)
    
    print(f"✅ Sent to chat: {chat_id}")


def start_scheduler():
    """Start the scheduler with all meetings."""
    scheduler = BlockingScheduler(timezone=pytz.timezone(Config.TIMEZONE))
    
    # Load meetings from config
    meetings = Config.load_meetings()
    
    if not meetings:
        print("⚠️ No meetings configured!")
        print(f"Add meetings to {Config.MEETINGS_FILE}")
        return
    
    print(f"📅 Loading {len(meetings)} meetings...")
    print("=" * 50)
    
    for meeting_config in meetings:
        schedule = meeting_config.get('schedule', {})
        days = schedule.get('days', [])
        hour = schedule.get('hour', 9)
        minute = schedule.get('minute', 0)
        
        # Convert day names to cron format
        cron_days = ','.join([DAY_MAP.get(d.lower(), d) for d in days])
        
        if not cron_days:
            print(f"⚠️ Skipping {meeting_config['id']}: No days specified")
            continue
        
        # Add job
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
        print(f"   💬 Chat: {meeting_config.get('chat_id')}")
        print()
    
    print("=" * 50)
    print(f"🚀 Scheduler running! ({Config.TIMEZONE})")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped")


def run_meeting_now(meeting_id: str):
    """Run a specific meeting immediately."""
    meetings = Config.load_meetings()
    
    for meeting_config in meetings:
        if meeting_config['id'] == meeting_id:
            print(f"🚀 Running: {meeting_config['title']}")
            create_meeting_job(meeting_config)
            return True
    
    print(f"❌ Meeting not found: {meeting_id}")
    print(f"Available meetings: {[m['id'] for m in meetings]}")
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
   ⏱️ Duration: {m.get('duration_minutes', 60)} min
""")