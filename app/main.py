import sys
import asyncio
from app.config import Config
from app.database.db import init_database
from app.scheduler import setup_scheduler, run_meeting_now, list_meetings
from app.jitsi_meet import create_jitsi_meeting
from app.telegram_bot import meeting_bot
from app.bot.handlers import create_bot_application


def print_help():
    print("""
🤖 Meeting Bot - Commands
===========================

python -m app.main              Start bot + scheduler
python -m app.main bot          Start bot only
python -m app.main scheduler    Start scheduler only
python -m app.main list         List all meetings
python -m app.main run <id>     Run specific meeting now
python -m app.main test         Quick test
python -m app.main help         Show this help
""")


async def run_bot_only():
    """Run only the Telegram bot."""
    print("🤖 Starting Telegram bot...")
    app = create_bot_application()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("✅ Bot running! Press Ctrl+C to stop.")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


async def run_bot_and_scheduler():
    """Run both bot and scheduler."""
    print("🤖 Starting Meeting Bot...")
    
    # Initialize database
    init_database()
    
    # Start scheduler
    scheduler = setup_scheduler()
    scheduler.start()
    print("📅 Scheduler started!")
    
    # Start bot
    print("🤖 Starting Telegram bot...")
    app = create_bot_application()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("✅ Bot + Scheduler running! Press Ctrl+C to stop.")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n🛑 Shutting down...")
        scheduler.shutdown()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        print("👋 Goodbye!")


def main():
    print("🤖 Meeting Bot")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        asyncio.run(run_bot_and_scheduler())
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        print_help()
    
    elif command == "bot":
        asyncio.run(run_bot_only())
    
    elif command == "scheduler":
        init_database()
        scheduler = setup_scheduler()
        scheduler.start()
        print("📅 Scheduler running! Press Ctrl+C to stop.")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            scheduler.shutdown()
            print("\n👋 Stopped")
    
    elif command == "list":
        list_meetings()
    
    elif command == "run":
        if len(sys.argv) < 3:
            print("❌ Specify meeting ID")
            list_meetings()
        else:
            run_meeting_now(sys.argv[2])
    
    elif command == "test":
        print("🧪 Testing...")
        meeting = create_jitsi_meeting(title="Test Meeting")
        print(f"✅ Created: {meeting['meet_link']}")
        meeting_bot.send_meeting_link_sync(meeting)
        print("✅ Sent to Telegram!")
    
    else:
        print(f"❌ Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()