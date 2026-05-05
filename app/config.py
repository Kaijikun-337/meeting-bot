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
    
    # Google Sheets
    SHEETS_CREDENTIALS_FILE = "credentials.json"
    #GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Teacher Colors
    TEACHER_COLORS = {
        "Timur": {"red": 0.85, "green": 0.92, "blue": 0.98},
        "Amir": {"red": 0.98, "green": 0.85, "blue": 0.85},
        "Sardor": {"red": 0.85, "green": 0.98, "blue": 0.85},
        "Ms. Davis": {"red": 0.98, "green": 0.95, "blue": 0.85},
        "Mr. Wilson": {"red": 0.95, "green": 0.85, "blue": 0.98},
        "Default": {"red": 0.95, "green": 0.95, "blue": 0.95}
    }
    
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