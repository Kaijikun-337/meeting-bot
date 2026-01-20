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
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
    
    # Meetings config
    MEETINGS_FILE = "meetings.json"
    
    # Price list
    PRICE_LIST_FILE = "price_list.json"
    
    # Database
    DATABASE_FILE = "data.db"
    
    # Google Sheets
    SHEETS_CREDENTIALS_FILE = "sheets_credentials.json"
    GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
    
    # Rules
    MIN_HOURS_BEFORE_CHANGE = 2
    
    # Teacher Colors
    TEACHER_COLORS = {
        "Mr. Smith": {"red": 0.85, "green": 0.92, "blue": 0.98},
        "Ms. Johnson": {"red": 0.98, "green": 0.85, "blue": 0.85},
        "Mr. Brown": {"red": 0.85, "green": 0.98, "blue": 0.85},
        "Ms. Davis": {"red": 0.98, "green": 0.95, "blue": 0.85},
        "Mr. Wilson": {"red": 0.95, "green": 0.85, "blue": 0.98},
        "Default": {"red": 0.95, "green": 0.95, "blue": 0.95}
    }
    
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
    
    @staticmethod
    def load_price_list() -> dict:
        try:
            with open(Config.PRICE_LIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ {Config.PRICE_LIST_FILE} not found")
            return {"courses": [], "default_price": 100.00, "currency": "USD"}
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return {"courses": [], "default_price": 100.00, "currency": "USD"}
    
    @staticmethod
    def get_course_price(subject: str, teacher: str, group: str) -> float:
        """Get price for a specific course."""
        price_list = Config.load_price_list()
        
        for course in price_list.get('courses', []):
            if (course.get('subject', '').lower() == subject.lower() and
                course.get('teacher', '').lower() == teacher.lower() and
                course.get('group', '').lower() == group.lower()):
                return course.get('price', price_list.get('default_price', 100.00))
        
        # Try matching just subject and teacher
        for course in price_list.get('courses', []):
            if (course.get('subject', '').lower() == subject.lower() and
                course.get('teacher', '').lower() == teacher.lower()):
                return course.get('price', price_list.get('default_price', 100.00))
        
        return price_list.get('default_price', 100.00)