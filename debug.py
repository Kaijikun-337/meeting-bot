"""
test_send.py — Send a real test link via Telegram.
Run: python test_send.py <chat_id>
Example: python test_send.py 123456789
"""

import sys
import os
import re
import asyncio
import random
import string
from datetime import datetime

# Load .env
from dotenv import load_dotenv
load_dotenv()

from telegram import Bot
from telegram.constants import ParseMode


# ═══════════════════════════════════════════════════════════
# NEW jitsi_meet logic (same as debug.py)
# ═══════════════════════════════════════════════════════════

def generate_room_id(length: int = 10) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def _slugify(text: str) -> str:
    slug = "".join(c for c in text if c.isascii() and (c.isalnum() or c == ' '))
    slug = slug.strip().replace(' ', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug.lower())
    return slug if slug else "meeting"


def create_jitsi_meeting(title: str = "Meeting", room_name: str = None, subject: str = None) -> dict:
    if subject:
        clean_slug = _slugify(subject)
    else:
        clean_slug = _slugify(title)

    if not room_name:
        timestamp = datetime.now().strftime("%M%H%d%m%Y")
        random_id = generate_room_id(6)
        room_name = f"{clean_slug}-{timestamp}-{random_id}"

    room_name = re.sub(r'[^a-z0-9-]', '', room_name.lower())

    meet_link = f"https://meet.jit.si/{room_name}"

    return {
        'room_name': room_name,
        'meet_link': meet_link,
        'title': title,
        'start_time': datetime.now().strftime("%H:%M"),
        'platform': 'jitsi'
    }


# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    sys.exit(1)

# Chat ID from argument or fallback to ADMIN_CHAT_ID
if len(sys.argv) > 1:
    TARGET_CHAT_ID = sys.argv[1]
else:
    TARGET_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not TARGET_CHAT_ID:
    print("❌ Provide chat_id:  python test_send.py <chat_id>")
    print("   Or set ADMIN_CHAT_ID in .env")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════
# SEND
# ═══════════════════════════════════════════════════════════

async def send_test_link():
    # Generate link (same way scheduler does it)
    meeting_config = {
        "title": "Математика",
        "subject": "math",
        "group_name": "Group M/N",
        "teacher_name": "Amir",
        "description": "Групповые занятия по математике",
        "schedule": {"hour": 19, "minute": 0}
    }

    meeting_data = create_jitsi_meeting(
        title=meeting_config['title'],
        subject=meeting_config.get('subject')
    )

    link = meeting_data['meet_link']
    room = meeting_data['room_name']

    # ── Pre-send checks ──
    print("\n🔍 Pre-send checks:")
    print(f"   Room name : {room}")
    print(f"   Link      : {link}")
    print(f"   ASCII-only: {'✅' if all(ord(c) < 128 for c in link) else '❌'}")
    print(f"   Jitsi URL : {'✅' if link.startswith('https://meet.jit.si/') else '❌'}")
    print(f"   Target    : {TARGET_CHAT_ID}")

    if not all(ord(c) < 128 for c in link):
        print("\n❌ ABORT: Link contains non-ASCII characters!")
        return

    # ── Build message (same format as scheduler) ──
    html_link = f'<a href="{link}">{link}</a>'

    full_text = (
        f"🧪 <b>TEST LINK — Please Ignore</b>\n\n"
        f"📚 <b>Lesson:</b> {meeting_config['title']}\n"
        f"👥 <b>Group:</b> {meeting_config['group_name']}\n"
        f"👨‍🏫 <b>Teacher:</b> {meeting_config['teacher_name']}\n"
        f"🕐 <b>Time:</b> {meeting_config['schedule']['hour']:02d}:"
        f"{meeting_config['schedule']['minute']:02d}\n\n"
        f"🔗 <b>Join:</b> {html_link}\n\n"
        f"────────────────\n"
        f"room_name: <code>{room}</code>"
    )

    # ── Confirm ──
    print(f"\n📤 Message preview:")
    print(f"{'─' * 45}")
    print(full_text.replace('<a href="', '').replace('">', '\n').replace('</a>', ''))
    print(f"{'─' * 45}")

    confirm = input("\n⚡ Send? (y/n): ").strip().lower()
    if confirm != 'y':
        print("🚫 Cancelled.")
        return

    # ── Send ──
    print("\n📨 Sending...")
    bot = Bot(token=TOKEN)

    try:
        await bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=full_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        print(f"✅ Sent successfully to {TARGET_CHAT_ID}")
        print(f"\n🎯 Next step: Open the link on your phone/browser")
        print(f"   and confirm you can join the Jitsi room!")

    except Exception as e:
        print(f"❌ Send failed: {e}")

    # ── Optional: send a second one to test uniqueness ──
    confirm2 = input("\n🔄 Send a SECOND link to verify uniqueness? (y/n): ").strip().lower()
    if confirm2 == 'y':
        data2 = create_jitsi_meeting(
            title=meeting_config['title'],
            subject=meeting_config.get('subject')
        )
        link2 = data2['meet_link']
        html_link2 = f'<a href="{link2}">{link2}</a>'

        text2 = (
            f"🧪 <b>TEST LINK #2 — Uniqueness Check</b>\n\n"
            f"🔗 <b>Join:</b> {html_link2}\n\n"
            f"Room 1: <code>{room}</code>\n"
            f"Room 2: <code>{data2['room_name']}</code>\n\n"
            f"{'✅ Different rooms' if room != data2['room_name'] else '❌ SAME ROOM!'}"
        )

        try:
            await bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=text2,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            print(f"✅ Second link sent!")
        except Exception as e:
            print(f"❌ Second send failed: {e}")


if __name__ == "__main__":
    asyncio.run(send_test_link())