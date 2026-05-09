import os
import json
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DEFAULT_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Almaty")
    
    # Meetings config
    MEETINGS_FILE = "meetings.json"
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    @staticmethod
    def load_meetings() -> list:
        full_path = Config.MEETINGS_FILE
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('meetings', [])
        except FileNotFoundError:
            print(f"⚠️ {full_path} not found")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {full_path}: {e}")
            return []