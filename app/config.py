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
    
    # Google
    CREDENTIALS_FILE = "credentials.json"
    TOKEN_FILE = "token.json"
    
    # Meetings config
    MEETINGS_FILE = "meetings.json"
    
    @staticmethod
    def load_meetings() -> list:
        """Load meetings from JSON file."""
        try:
            with open(Config.MEETINGS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('meetings', [])
        except FileNotFoundError:
            print(f"⚠️ {Config.MEETINGS_FILE} not found. Using empty list.")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {Config.MEETINGS_FILE}: {e}")
            return []