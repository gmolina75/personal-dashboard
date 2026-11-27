"""Tasks connector for fetching tasks via Google Tasks API.
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.connectors.base import BaseConnector
from app.core.security import decrypt_token

SCOPES = ["https://www.googleapis.com/auth/tasks.readonly"]

class TasksConnector(BaseConnector):
    name = "tasks"
    
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
        return build("tasks", "v1", credentials=creds)
    
    async def fetch(self) -> List[Dict[str, Any]]:
        # Mock implementation for development
        now = datetime.now()
        return [
            {
                "id": "task-1",
                "source": "tasks",
                "type": "task",
                "title": "✅ Revisar contrato proveedor",
                "snippet": "Firmar antes del viernes - URGENTE",
                "url": "https://tasks.google.com/task/task-1",
                "ts_start": int(now.timestamp()),
                "ts_end": int((now + timedelta(days=2)).timestamp()),
                "meta_json": {"status": "pending", "list": "Trabajo"},
                "priority": 3,
                "updated_at": int(now.timestamp())
            },
            {
                "id": "task-2",
                "source": "tasks",
                "type": "task",
                "title": "📝 Preparar presentación Q1",
                "snippet": "Slides para reunión del lunes",
                "url": "https://tasks.google.com/task/task-2",
                "ts_start": int(now.timestamp()),
                "ts_end": int((now + timedelta(days=3)).timestamp()),
                "meta_json": {"status": "in_progress", "list": "Personal"},
                "priority": 1,
                "updated_at": int(now.timestamp())
            }
        ]

async def get_tasks_connector(credentials: Dict[str, Any]) -> TasksConnector:
    return TasksConnector(credentials)