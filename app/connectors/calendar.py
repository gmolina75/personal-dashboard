"""Calendar connector for fetching events via Google Calendar API.
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.connectors.base import BaseConnector
from app.core.security import decrypt_token

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

class CalendarConnector(BaseConnector):
    name = "calendar"
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        
    def _get_service(self):
        creds = Credentials(
            token=decrypt_token(self.credentials.get("access_token", "")),
            refresh_token=decrypt_token(self.credentials.get("refresh_token", "")),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            scopes=SCOPES
        )
        return build("calendar", "v3", credentials=creds)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        # Mock implementation for development
        now = datetime.now()
        return [
            {
                "id": "cal-1",
                "source": "calendar",
                "type": "event",
                "title": "📅 Reunión Q1 Planning",
                "snippet": "Planificación trimestral con el equipo",
                "url": "https://calendar.google.com/calendar/event?eid=cal-1",
                "ts_start": int((now + timedelta(hours=2)).timestamp()),
                "ts_end": int((now + timedelta(hours=3)).timestamp()),
                "meta_json": {"location": "Sala A / Meet", "attendees": 5},
                "priority": 2,
                "updated_at": int(now.timestamp())
            },
            {
                "id": "cal-2",
                "source": "calendar",
                "type": "event",
                "title": "🦷 Cita dentista - URGENTE",
                "snippet": "Control semestral - No olvides traer radiografías",
                "url": "https://calendar.google.com/calendar/event?eid=cal-2",
                "ts_start": int((now + timedelta(days=1)).timestamp()),
                "ts_end": int((now + timedelta(days=1, hours=1)).timestamp()),
                "meta_json": {"location": "Clínica Dental", "attendees": 0},
                "priority": 1,
                "updated_at": int(now.timestamp())
            }
        ]

async def get_calendar_connector(credentials: Dict[str, Any]) -> CalendarConnector:
    return CalendarConnector(credentials)