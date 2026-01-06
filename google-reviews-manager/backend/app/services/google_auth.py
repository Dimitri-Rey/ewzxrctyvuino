"""Google OAuth 2.0 authentication service."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import settings
import json


class GoogleAuthService:
    """Service for handling Google OAuth authentication."""
    
    def __init__(self):
        """Initialize the Google Auth service."""
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")
        
        self.client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        }
    
    def get_authorization_url(self) -> str:
        """
        Generate the Google OAuth authorization URL.
        
        Returns:
            str: The authorization URL to redirect the user to
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url
    
    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: The authorization code from Google callback
            
        Returns:
            dict: Dictionary containing tokens and user info
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Get user info
        from googleapiclient.discovery import build
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry,
            "email": user_info.get("email"),
            "scopes": credentials.scopes
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using the refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            dict: Dictionary containing new access token and expiry
        """
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        
        # Refresh the token
        credentials.refresh(Request())
        
        return {
            "access_token": credentials.token,
            "token_expiry": credentials.expiry
        }
    
    def is_token_expired(self, token_expiry: Optional[datetime]) -> bool:
        """
        Check if a token is expired or will expire soon (within 5 minutes).
        
        Args:
            token_expiry: The token expiry datetime
            
        Returns:
            bool: True if token is expired or will expire soon
        """
        if not token_expiry:
            return True
        
        # Consider token expired if it expires within 5 minutes
        return datetime.utcnow() >= (token_expiry - timedelta(minutes=5))


# Singleton instance (lazy initialization)
_google_auth_service = None

def get_google_auth_service() -> GoogleAuthService:
    """Get or create the Google Auth service instance."""
    global _google_auth_service
    if _google_auth_service is None:
        _google_auth_service = GoogleAuthService()
    return _google_auth_service
