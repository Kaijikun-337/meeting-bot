import asyncio
from telegram import Bot
from app.config import Config


class MeetingBot:
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.chat_id = Config.TELEGRAM_CHAT_ID
    
    async def send_meeting_link(self, meeting: dict) -> bool:
        """Send meeting link to Telegram."""
        message = f"""🎥 <b>Meeting Time!</b>

📌 <b>Title:</b> {meeting['title']}
⏰ <b>Time:</b> {meeting['start_time']}

🔗 <b>Join here:</b>
{meeting['meet_link']}

👆 Click the link to join!"""
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            print(f"✅ Meeting link sent to Telegram")
            return True
        except Exception as e:
            print(f"❌ Failed to send: {e}")
            return False
    
    async def send_reminder(self, meeting: dict, minutes: int = 10) -> bool:
        """Send reminder before meeting."""
        message = f"""⏰ <b>Reminder!</b>

Meeting <b>{meeting['title']}</b> starts in {minutes} minutes!

🔗 {meeting['meet_link']}"""
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            print(f"❌ Reminder failed: {e}")
            return False
    
    def send_meeting_link_sync(self, meeting: dict) -> bool:
        """Synchronous wrapper."""
        return asyncio.run(self.send_meeting_link(meeting))


# Global instance
meeting_bot = MeetingBot()