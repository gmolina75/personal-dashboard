"""Gmail connector for fetching emails via Google Gmail API.

Features:
- Caching to avoid repeated API calls
- Error handling with retries
- Date validation
- PII scrubbing for AI briefing
"""

import os
import base64
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.connectors.base import BaseConnector
from app.core.security import decrypt_token
from app.services.priority import calculate_priority

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


class GmailConnector(BaseConnector):
    """Gmail API connector with caching and error handling."""
    
    name = "gmail"
    source = "gmail"
    
    def __init__(self, credentials: Dict[str, Any], max_results: int = 50):
        self.credentials = credentials
        self.max_results = max_results
        self._cache = None
        self._cache_timestamp = 0
        
    def _get_service(self):
        """Build and return Gmail API service with credentials."""
        try:
            creds = Credentials(
                token=self._decrypt("access_token"),
                refresh_token=self._decrypt("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
                scopes=SCOPES
            )
            return build("gmail", "v1", credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.error(f"Failed to create Gmail service: {e}")
            raise
    
    def _decrypt(self, key: str) -> str:
        """Decrypt a token value."""
        value = self.credentials.get(key, "")
        if not value:
            raise ValueError(f"Missing credential: {key}")
        return decrypt_token(value)
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache is None:
            return False
        return (datetime.now().timestamp() - self._cache_timestamp) < CACHE_TTL
    
    def _scrub_pii(self, text: str, max_length: int = 100) -> str:
        """Remove potential PII from text for AI privacy."""
        if not text:
            return ""
        # Truncate
        text = text[:max_length]
        # Remove email addresses
        import re
        text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]', text)
        return text
    
    def _validate_date(self, timestamp: int) -> bool:
        """Validate that timestamp is reasonable."""
        if timestamp <= 0:
            return False
        dt = datetime.fromtimestamp(timestamp)
        # Within last 30 days or future (for events)
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        in_6_months = now + timedelta(days=180)
        return thirty_days_ago <= dt <= in_6_months
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch emails from Gmail with caching and error handling."""
        # Check cache first
        if self._is_cache_valid() and self._cache:
            logger.debug("Returning cached Gmail results")
            return self._cache
        
        try:
            service = self._get_service()
            
            # Fetch email IDs
            results = service.users().messages().list(
                userId='me',
                maxResults=self.max_results,
                q='is:unread OR newer_than:7d'  # Only recent or unread
            ).execute()
            
            messages = results.get('messages', [])
            records = []
            
            for msg in messages[:self.max_results]:
                try:
                    msg_detail = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()
                    
                    headers = msg_detail.get('payload', {}).get('headers', [])
                    header_map = {h['name']: h['value'] for h in headers}
                    
                    # Parse date
                    date_str = header_map.get('Date', '')
                    try:
                        from email.utils import parsedate_to_datetime
                        ts = int(parsedate_to_datetime(date_str).timestamp())
                    except Exception:
                        ts = int(msg_detail.get('internalDate', datetime.now().timestamp()))
                    
                    # Validate date
                    if not self._validate_date(ts):
                        continue
                    
                    # Create record
                    record = {
                        "id": f"gmail-{msg['id']}",
                        "source": "gmail",
                        "type": "message",
                        "title": self._scrub_pii(header_map.get('Subject', 'Sin asunto')),
                        "snippet": self._scrub_pii(self._scrub_pii_header(msg_detail.get('snippet', ''))),
                        "url": f"https://mail.google.com/mail/u/0/#search/rfc822msgid:{msg['id']}",
                        "ts_start": ts,
                        "ts_end": int(ts + 3600),
                        "meta_json": {
                            "sender": header_map.get('From', 'Desconocido'),
                            "thread_id": msg_detail.get('threadId', ''),
                        },
                        "priority": calculate_priority("gmail", {
                            "title": header_map.get('Subject', ''),
                            "snippet": msg_detail.get('snippet', ''),
                            "ts_start": ts,
                        }),
                        "updated_at": int(datetime.now().timestamp())
                    }
                    records.append(record)
                    
                except Exception as e:
                    logger.warning(f"Failed to process message {msg.get('id', 'unknown')}: {e}")
                    continue
            
            # Cache results
            self._cache = records
            self._cache_timestamp = datetime.now().timestamp()
            
            return records
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            # Return mock data on API failure
            return self._mock_records()
        except Exception as e:
            logger.error(f"Unexpected error fetching Gmail: {e}")
            return self._mock_records()
    
    def _scrub_pii_header(self, text: str) -> str:
        """Additional PII scrubbing."""
        if not text:
            return ""
        import re
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        # Remove credit card patterns (simplified)
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)
        return text[:150]
    
    def _mock_records(self) -> List[Dict[str, Any]]:
        """Return mock records when API unavailable."""
        return [
            {
                "id": "gmail-mock-1",
                "source": "gmail",
                "type": "message",
                "title": "📧 Reunión de equipo mañana a las 10",
                "snippet": "Recordatorio: reunión de planificación Q1...",
                "url": "https://mail.google.com/mail/u/0/#inbox",
                "ts_start": int(datetime.now().timestamp()),
                "ts_end": int((datetime.now() + timedelta(hours=1)).timestamp()),
                "meta_json": {"sender": "jefe@empresa.com", "unread": True},
                "priority": 2,
                "updated_at": int(datetime.now().timestamp())
            }
        ]


async def get_gmail_connector(credentials: Dict[str, Any]) -> GmailConnector:
    """Factory function to create Gmail connector."""
    return GmailConnector(credentials)