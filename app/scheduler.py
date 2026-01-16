from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from app.config import Config
from app.google_meet import create_meeting
from app.telegram_bot import meeting_bot


def scheduled_meeting_job():
    """Job that runs at scheduled time."""
    print(f"⏰ Running scheduled meeting job...")
    
    # Create meeting
    meeting = create_meeting(
        title="Daily Standup",
        duration_minutes=60,
        description="Daily team meeting"
    )
    
    print(f"✅ Meeting created: {meeting['meet_link']}")
    
    # Send to Telegram
    meeting_bot.send_meeting_link_sync(meeting)
    
    print("✅ Meeting link sent!")


def start_scheduler():
    """Start the scheduler."""
    scheduler = BlockingScheduler(timezone=pytz.timezone(Config.TIMEZONE))
    
    # Schedule daily meeting
    scheduler.add_job(
        scheduled_meeting_job,
        CronTrigger(
            hour=Config.MEETING_HOUR,
            minute=Config.MEETING_MINUTE,
            timezone=pytz.timezone(Config.TIMEZONE)
        ),
        id='daily_meeting',
        name='Create daily meeting'
    )
    
    print(f"📅 Scheduler started!")
    print(f"⏰ Meeting scheduled for {Config.MEETING_HOUR}:{Config.MEETING_MINUTE:02d} ({Config.TIMEZONE})")
    print("Press Ctrl+C to stop")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped")