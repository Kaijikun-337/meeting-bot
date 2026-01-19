import os
import json
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DEFAULT_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
    
    # Meetings config
    MEETINGS_FILE = "meetings.json"
    
    # Database
    DATABASE_FILE = "data.db"
    
    # Rules
    MIN_HOURS_BEFORE_CHANGE = 2
    
    @staticmethod
    def load_meetings() -> list:
        try:
            with open(Config.MEETINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('meetings', [])
        except FileNotFoundError:
            print(f"⚠️ {Config.MEETINGS_FILE} not found")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return []