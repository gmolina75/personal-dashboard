"""OAuth management for Google Workspace using Personal Mode.

Personal Mode advantages:
- No 7-day token expiration
- No CASA/security assessment required
- No app verification needed
- Only your account can authorize it (client_user_mismatch error for others)

Usage:
1. Go to http://localhost:8000/auth/google to start OAuth
2. Complete Google's consent flow
3. Google redirects to http://localhost:8000/auth/google/callback
4. Server stores encrypted refresh_token
"""

import os
import secrets
import hashlib
from urllib.parse import urlencode
from typing import Optional, Dict, Any
from datetime import datetime

# Google OAuth endpoints
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# Personal Mode uses a special URL for onboarding
PERSONAL_MODE_URL = "https://console.cloud.google.com/auth/overview/personal"


class OAuthManager:
    """Manages Google OAuth using Personal Mode flow."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "http://localhost:8000/auth/google/callback"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._state_tokens: Dict[str, float] = {}  # Store temporarily for CSRF protection

    def get_authorization_url(self, scopes: list, access_type: str = "offline") -> str:
        """Generate Google OAuth authorization URL with Personal Mode parameters."""
        state = secrets.token_urlsafe(32)
        self._state_tokens[state] = datetime.now().timestamp()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": access_type,
            "prompt": "consent",  # Force consent screen for refresh token
            "state": state,
            "include_granted_scopes": "true",
        }

        return f"{AUTH_ENDPOINT}?{urlencode(params)}"

    def parse_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens.

        Note: Does not include HTTP call here - that's done by the route handler.
        Returns the request body for exchanging code -> tokens.
        """
        if state not in self._state_tokens:
            raise ValueError("Invalid state parameter")

        # State expires after 10 minutes
        if datetime.now().timestamp() - self._state_tokens[state] > 600:
            del self._state_tokens[state]
            raise ValueError("State token expired")

        del self._state_tokens[state]

        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

    def build_token_request(self, code: str, state: str) -> Dict[str, Any]:
        """Build complete request body for token exchange."""
        parsed = self.parse_callback(code, state)
        parsed["grant_type"] = "authorization_code"
        return parsed


def get_oauth_manager() -> OAuthManager:
    """Get OAuth manager with credentials from environment."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env")

    return OAuthManager(client_id, client_secret)