import sys
from app.scheduler import start_scheduler, scheduled_meeting_job
from app.google_meet import create_meeting
from app.telegram_bot import meeting_bot


def main():
    print("🤖 Meeting Bot")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # Test: Create meeting and send immediately
            print("🧪 Testing...")
            meeting = create_meeting(
                title="Test Meeting",
                duration_minutes=30
            )
            print(f"✅ Created: {meeting['meet_link']}")
            meeting_bot.send_meeting_link_sync(meeting)
            print("✅ Sent to Telegram!")
        
        elif command == "auth":
            # Just authenticate Google
            print("🔐 Authenticating with Google...")
            from app.google_meet import get_google_credentials
            get_google_credentials()
            print("✅ Authenticated! Token saved.")
        
        elif command == "now":
            # Create and send meeting now
            print("📹 Creating meeting now...")
            scheduled_meeting_job()
        
        else:
            print(f"Unknown command: {command}")
            print("Commands: test, auth, now")
    
    else:
        # Default: Start scheduler
        start_scheduler()


if __name__ == "__main__":
    main()