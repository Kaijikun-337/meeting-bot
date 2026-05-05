# 📚 Meeting Bot

A Telegram bot for managing online lessons, meetings, and student attendance for educational institutions.

## 📋 Overview

Meeting Bot is a comprehensive Telegram bot designed for academies and educational institutions to manage online lessons. It automatically generates Jitsi Meet video conference links, sends notifications to teachers and students, tracks attendance, handles homework submissions, and provides an admin panel for management.

## ✨ Features

- 🎥 **Automatic Meeting Links** - Generates Jitsi Meet links for scheduled lessons
- 📅 **Smart Scheduling** - Configurable lesson schedules with cron-based automation
- 👨‍🏫 **Teacher Management** - Auto-healing database for teacher assignments
- 👨‍🎓 **Student Groups** - Manage students by groups with targeted notifications
- 📝 **Attendance Tracking** - Mark and track student attendance
- 📚 **Homework Management** - Teachers can upload recordings and materials
- 🔔 **Automated Reminders** - Notifications before lessons and recording reminders after
- 🌐 **Multi-language Support** - Localized messages for users
- 👤 **Admin Panel** - Full administrative controls
- 📊 **Google Sheets Integration** - Sync data with spreadsheets
- 💰 **Price List Management** - Course pricing configuration
- 🔄 **Keep-Alive Server** - Supports Render deployment

## 🛠️ Tech Stack

- **Python 3.8+** - Main programming language
- **python-telegram-bot 20.7** - Telegram Bot API wrapper
- **Jitsi Meet** - Free video conferencing (no account required)
- **PostgreSQL / SQLite** - Database (hybrid support)
- **APScheduler** - Task scheduling for lessons
- **Google Sheets API** - Spreadsheet integration
- **Flask** - Keep-alive server for cloud deployment

## 📁 Project Structure

```
meeting-bot/
├── app/
│   ├── __init__.py
│   ├── main.py              # Bot entry point
│   ├── config.py            # Configuration management
│   ├── jitsi_meet.py        # Jitsi Meet link generation
│   ├── scheduler.py         # Lesson scheduling & reminders
│   ├── keep_alive.py        # Flask server for Render
│   ├── telegram_bot.py      # Bot initialization
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py      # Command handlers
│   │   ├── admin.py         # Admin panel commands
│   │   ├── attendance.py    # Attendance tracking
│   │   ├── homework.py      # Homework management
│   │   ├── registration.py  # User registration
│   │   ├── menu_handler.py  # Menu navigation
│   │   ├── keyboards.py     # Inline keyboards
│   │   ├── language.py      # Language selection
│   │   └── error_handler.py # Error handling
│   ├── database/
│   │   └── db.py            # Database operations
│   ├── services/
│   │   └── user_service.py  # User management service
│   └── utils/
│       └── localization.py  # Multi-language support
├── meetings.json            # Meeting schedules config
├── requirements.txt         # Python dependencies
└── debug.py                 # Debug/testing utilities
```

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/Kaijikun-337/meeting-bot.git
cd meeting-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Configure your environment variables

# Run the bot
python -m app.main
```

## 🔧 Configuration

Create a `.env` file in the root directory:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=default_chat_id
ADMIN_CHAT_ID=your_admin_chat_id

# Timezone
TIMEZONE=Asia/Almaty

# Database (PostgreSQL for production)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Google Sheets (optional)
GOOGLE_SHEETS_ID=your_sheets_id
```

### Meetings Configuration

Create a `meetings.json` file with your lesson schedules:

```json
{
  "meetings": [
    {
      "id": "math-101",
      "title": "Mathematics 101",
      "description": "Basic algebra and geometry",
      "subject": "Math",
      "group_name": "Group-A",
      "teacher_name": "Mr. Smith",
      "schedule": {
        "days": ["monday", "wednesday", "friday"],
        "hour": 10,
        "minute": 0
      },
      "duration_minutes": 60
    }
  ]
}
```

## 📦 Dependencies

```
python-telegram-bot==20.7   # Telegram Bot API
apscheduler==3.10.4         # Task scheduling
python-dotenv==1.0.0        # Environment variables
pytz==2024.1                # Timezone handling
aiosqlite==0.19.0           # Async SQLite
google-auth==2.27.0         # Google authentication
google-api-python-client    # Google Sheets API
gspread==6.0.0              # Google Sheets wrapper
psycopg2-binary             # PostgreSQL adapter
flask                       # Keep-alive server
gunicorn                    # WSGI server
oauth2client                # OAuth2 for Google
```

## 💬 Bot Commands

### User Commands
| Command | Description |
|---------|-------------|
| `/start` | Start the bot and register |
| `/menu` | Show main menu |
| `/schedule` | View upcoming lessons |
| `/homework` | Access homework section |
| `/language` | Change language preference |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/admin` | Open admin panel |
| `/add_user` | Add new user |
| `/attendance` | Mark/view attendance |
| `/stats` | View statistics |
| `/broadcast` | Send message to all users |

## 🎥 How Meeting Links Work

1. **Scheduled Time** - Bot automatically creates a Jitsi Meet room
2. **Notifications** - Teachers and students receive the link via Telegram
3. **Join Meeting** - Anyone with the link can join (no account required)
4. **After Lesson** - Teacher receives reminder to upload recording

### Jitsi Meet Integration

The bot uses Jitsi Meet for free, instant video conferencing:
- ✅ No account required
- ✅ Free to use
- ✅ End-to-end encrypted
- ✅ Screen sharing support
- ✅ Up to 100 participants

## 🌍 Localization

Supports multiple languages through `utils/localization.py`. Messages are sent in the user's preferred language.

## 🚢 Deployment

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Use `gunicorn app.main:main` as start command

The bot includes a keep-alive server that prevents Render from sleeping.

### Local Development

```bash
# Run with live reload
python -m app.main
```

## 🔐 Security

- Admin access restricted by chat ID
- Environment variables for sensitive data
- PostgreSQL for production data
- Error handling and logging

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source. Check the repository for license details.

## 👨‍💻 Author

**Kaijikun-337**

- GitHub: [@Kaijikun-337](https://github.com/Kaijikun-337)
- Repository: [meeting-bot](https://github.com/Kaijikun-337/meeting-bot)

---

Made with 💜
