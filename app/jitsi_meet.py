import random
import string
import re
from datetime import datetime


def generate_room_id(length: int = 10) -> str:
    """Generate random room ID."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def _slugify(text: str) -> str:
    """Convert text to an ASCII-safe URL slug."""
    # Keep only ASCII alphanumeric and spaces
    slug = "".join(c for c in text if c.isascii() and (c.isalnum() or c == ' '))
    slug = slug.strip().replace(' ', '-')
    # Remove any remaining non-safe chars
    slug = re.sub(r'[^a-z0-9-]', '', slug.lower())
    return slug if slug else "meeting"


def create_jitsi_meeting(
    title: str = "Meeting",
    room_name: str = None,
    subject: str = None
) -> dict:
    """
    Create a Jitsi Meet link.

    Jitsi is free and requires no host!
    Anyone with the link can join immediately.
    """
    # Prefer subject (typically ASCII like "math") for the URL slug
    if subject:
        clean_slug = _slugify(subject)
    else:
        clean_slug = _slugify(title)

    # Generate unique room name (ASCII-only!)
    if not room_name:
        timestamp = datetime.now().strftime("%M%H%d%m%Y")
        random_id = generate_room_id(6)
        room_name = f"{clean_slug}-{timestamp}-{random_id}"

    # Final safety net: strip any non-ASCII that slipped in
    room_name = re.sub(r'[^a-z0-9-]', '', room_name.lower())

    meet_link = f"https://meet.jit.si/{room_name}"

    return {
        'room_name': room_name,
        'meet_link': meet_link,
        'title': title,
        'start_time': datetime.now().strftime("%H:%M"),
        'platform': 'jitsi'
    }