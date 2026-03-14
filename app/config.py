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
    
    # Price list
    PRICE_LIST_FILE = "price_list.json"
    
    # Google Sheets
    SHEETS_CREDENTIALS_FILE = "credentials.json"
    GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Rules
    MIN_HOURS_BEFORE_CHANGE = 2
    
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
    
    @staticmethod
    def load_support_schedule():
        """Load support availability from JSON."""
        import json, os
        path = os.path.join(os.path.dirname(__file__), '..', 'support_schedule.json')
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ support_schedule.json not found!")
            return None