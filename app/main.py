import logging
import os
import threading
from telegram.ext import Application
from app.config import Config
from app.bot.handlers import register_handlers
from app.database.db import init_database
from app.scheduler import start_scheduler

# 1. Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Silence noisy libraries
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

def main():
    print("🚀 Starting Demy Academy Bot (Render/Postgres Edition)...")

    # 2. Initialize Database (Hybrid: SQLite locally, Postgres on Render)
    init_database()
    
    # 3. Start Keep-Alive Server in a BACKGROUND THREAD
    # This prevents Flask from blocking the Telegram bot from starting
    if os.getenv("RENDER") or os.getenv("DATABASE_URL"):
        try:
            from app.keep_alive import keep_alive
            # Run Flask in a daemon thread so it doesn't block the main thread
            flask_thread = threading.Thread(target=keep_alive, daemon=True)
            flask_thread.start()
            print("🌍 Keep-Alive Server started in background thread.")
        except Exception as e:
            print(f"⚠️ Could not start keep-alive: {e}")

    # 4. Build Bot Application
    print("🤖 Building Bot Application...")
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # 5. Register Handlers (Commands, Messages, etc.)
    register_handlers(app)
    
    # 6. Start Scheduler (Async)
    # This automatically starts the checking loop for lessons
    start_scheduler(app)
    
    # 7. Run Bot (Blocks until Ctrl+C)
    print("✅ Bot is running! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == '__main__':
    main()