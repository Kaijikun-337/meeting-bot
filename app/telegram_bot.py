import asyncio
from telegram import Bot
from app.config import Config


class MeetingBot:
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.default_chat_id = Config.DEFAULT_CHAT_ID
    
    async def send_meeting_link(self, meeting: dict, chat_id: str = None) -> bool:
        """Send meeting link to Telegram."""
        target_chat_id = chat_id or self.default_chat_id
        
        message = f"""🎥 <b>Meeting Time!</b>

📌 <b>Title:</b> {meeting['title']}
⏰ <b>Time:</b> {meeting['start_time']}

🔗 <b>Join here:</b>
{meeting['meet_link']}

👆 Click the link to join!"""
        
        try:
            await self.bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode='HTML'
            )
            print(f"✅ Sent to chat {target_chat_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to send to {target_chat_id}: {e}")
            return False
    
    async def send_reminder(self, meeting: dict, chat_id: str = None, minutes: int = 10) -> bool:
        """Send reminder before meeting."""
        target_chat_id = chat_id or self.default_chat_id
        
        message = f"""⏰ <b>Reminder!</b>

Meeting <b>{meeting['title']}</b> starts in {minutes} minutes!

🔗 {meeting['meet_link']}"""
        
        try:
            await self.bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            print(f"❌ Reminder failed: {e}")
            return False
    
    def send_meeting_link_sync(self, meeting: dict, chat_id: str = None) -> bool:
        """Synchronous wrapper."""
        return asyncio.run(self.send_meeting_link(meeting, chat_id))


# Global instance
meeting_bot = MeetingBot()