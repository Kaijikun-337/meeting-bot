import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.config import Config

# Full access to calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_google_credentials():
    """Get or refresh Google credentials."""
    creds = None
    
    # Load existing token
    if os.path.exists(Config.TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(Config.TOKEN_FILE, SCOPES)
    
    # Refresh or create new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                Config.CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save token for next time
        with open(Config.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def create_meeting(
    title: str = "Daily Meeting",
    duration_minutes: int = 60,
    description: str = ""
) -> dict:
    """
    Create a Google Calendar event with Google Meet link.
    Returns dict with meeting details.
    """
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    # Meeting times
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(minutes=duration_minutes)
    
    # Event with Google Meet
    event = {
        'summary': title,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': Config.TIMEZONE,
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': Config.TIMEZONE,
        },
        'conferenceData': {
            'createRequest': {
                'requestId': f"meeting-{start_time.timestamp()}",
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        },
        # Open meeting - anyone with link can join
        'guestsCanModify': False,
        'guestsCanInviteOthers': True,
        'guestsCanSeeOtherGuests': True,
    }
    
    # Create event
    event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()
    
    # Extract meeting info
    meet_link = event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', '')
    
    return {
        'event_id': event['id'],
        'title': title,
        'meet_link': meet_link,
        'start_time': start_time.strftime("%H:%M"),
        'calendar_link': event.get('htmlLink', '')
    }


# Test function
if __name__ == "__main__":
    print("Creating test meeting...")
    meeting = create_meeting(
        title="Test Meeting",
        duration_minutes=30,
        description="Testing the meeting bot"
    )
    print(f"✅ Meeting created!")
    print(f"📎 Link: {meeting['meet_link']}")