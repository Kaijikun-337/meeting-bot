import random
import string
from datetime import datetime


def generate_room_id(length: int = 10) -> str:
    """Generate random room ID."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def create_jitsi_meeting(
    title: str = "Meeting",
    room_name: str = None
) -> dict:
    """
    Create a Jitsi Meet link.
    
    Jitsi is free and requires no host!
    Anyone with the link can join immediately.
    """
    
    # Clean title for URL
    clean_title = "".join(c for c in title if c.isalnum() or c == ' ')
    clean_title = clean_title.replace(' ', '-')
    
    # Generate unique room name
    if not room_name:
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        random_id = generate_room_id(6)
        room_name = f"{clean_title}-{timestamp}-{random_id}"
    
    # Create meeting link
    meet_link = f"https://meet.jit.si/{room_name}"
    
    return {
        'room_name': room_name,
        'meet_link': meet_link,
        'title': title,
        'start_time': datetime.now().strftime("%H:%M"),
        'platform': 'jitsi'
    }