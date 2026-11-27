"""Gmail connector for fetching emails via Google Gmail API.
"""

import os
import base64
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.connectors.base import BaseConnector
from app.core.security import decrypt_token

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

class GmailConnector(BaseConnector):
    name = "gmail"
    
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
        return build("gmail", "v1", credentials=creds)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        # Mock implementation for development
        # Replace with real Gmail API calls when credentials are available
        return [
            {
                "id": "gmail-1",
                "source": "gmail",
                "type": "message",
                "title": "📧 Reunión de equipo mañana a las 10",
                "snippet": "Recordatorio: reunión de planificación Q1...",
                "url": "https://mail.google.com/mail/u/0/#inbox/gmail-1",
                "ts_start": int(datetime.now().timestamp()),
                "ts_end": int((datetime.now() + timedelta(hours=1)).timestamp()),
                "meta_json": {"sender": "jefe@empresa.com", "unread": True},
                "priority": 2,
                "updated_at": int(datetime.now().timestamp())
            },
            {
                "id": "gmail-2",
                "source": "gmail",
                "type": "message",
                "title": "Factura proveedores - Vence hoy",
                "snippet": "URGENTE: Pago pendiente factura #12345...",
                "url": "https://mail.google.com/mail/u/0/#inbox/gmail-2",
                "ts_start": int(datetime.now().timestamp()),
                "ts_end": int((datetime.now() + timedelta(hours=2)).timestamp()),
                "meta_json": {"sender": "contabilidad@proveedor.com", "unread": False},
                "priority": 3,
                "updated_at": int(datetime.now().timestamp())
            }
        ]

async def get_gmail_connector(credentials: Dict[str, Any]) -> GmailConnector:
    return GmailConnector(credentials)