import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Schedule
    MEETING_HOUR = int(os.getenv("MEETING_HOUR", 19))
    MEETING_MINUTE = int(os.getenv("MEETING_MINUTE", 0))
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
    
    # Google
    CREDENTIALS_FILE = "credentials.json"
    TOKEN_FILE = "token.json"