import sys
from app.scheduler import start_scheduler, run_meeting_now, list_meetings
from app.google_meet import create_meeting, get_google_credentials
from app.telegram_bot import meeting_bot
from app.config import Config


def print_help():
    print("""
🤖 Meeting Bot - Commands
=========================

python -m app.main              Start scheduler (runs all meetings)
python -m app.main list         List all configured meetings
python -m app.main run <id>     Run specific meeting now
python -m app.main test         Quick test (creates test meeting)
python -m app.main auth         Authenticate with Google
python -m app.main help         Show this help

Examples:
  python -m app.main run english_class
  python -m app.main list
""")


def main():
    print("🤖 Meeting Bot")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        # Default: Start scheduler
        start_scheduler()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        print_help()
    
    elif command == "list":
        list_meetings()
    
    elif command == "run":
        if len(sys.argv) < 3:
            print("❌ Please specify meeting ID")
            print("Usage: python -m app.main run <meeting_id>")
            print("\nAvailable meetings:")
            list_meetings()
        else:
            meeting_id = sys.argv[2]
            run_meeting_now(meeting_id)
    
    elif command == "test":
        print("🧪 Testing...")
        meeting = create_meeting(
            title="Test Meeting",
            duration_minutes=30
        )
        print(f"✅ Created: {meeting['meet_link']}")
        meeting_bot.send_meeting_link_sync(meeting)
        print("✅ Sent to default chat!")
    
    elif command == "auth":
        print("🔐 Authenticating with Google...")
        get_google_credentials()
        print("✅ Authenticated!")
    
    else:
        print(f"❌ Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()