"""Drive connector for fetching files via Google Drive API.
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.connectors.base import BaseConnector
from app.core.security import decrypt_token

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

class DriveConnector(BaseConnector):
    name = "drive"
    
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
        return build("drive", "v3", credentials=creds)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        # Mock implementation for development
        now = datetime.now()
        return [
            {
                "id": "drive-1",
                "source": "drive",
                "type": "document",
                "title": "📊 Q1 Dashboard Data.xlsx",
                "snippet": "Actualizado ayer por el equipo de datos",
                "url": "https://drive.google.com/file/d/drive-1/view",
                "ts_start": int((now - timedelta(days=1)).timestamp()),
                "ts_end": int((now - timedelta(days=1)).timestamp()),
                "meta_json": {"mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "owner": "data@empresa.com"},
                "priority": 1,
                "updated_at": int(now.timestamp())
            },
            {
                "id": "drive-2",
                "source": "drive",
                "type": "document",
                "title": "📄 Contrato Proveedor 2025.pdf",
                "snippet": "Versión final para firma - URGENTE",
                "url": "https://drive.google.com/file/d/drive-2/view",
                "ts_start": int((now - timedelta(hours=3)).timestamp()),
                "ts_end": int((now - timedelta(hours=3)).timestamp()),
                "meta_json": {"mimeType": "application/pdf", "owner": "legal@empresa.com"},
                "priority": 3,
                "updated_at": int(now.timestamp())
            }
        ]

async def get_drive_connector(credentials: Dict[str, Any]) -> DriveConnector:
    return DriveConnector(credentials)