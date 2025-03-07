"""
OAuth Module

This module provides OAuth2 authentication for the Gmail API.
"""

import os
import logging
import threading
import webbrowser
import socket
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request as GoogleRequest
import httpx

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.utils.config import get_config
from gmail_mcp.auth.token_manager import TokenManager

# Get logger
logger = get_logger(__name__)

# Get configuration
config = get_config()

# Get token manager
token_manager = TokenManager()

# Define scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def login() -> str:
    """
    Initiate the OAuth2 flow by providing a link to the Google authorization page.
    
    Returns:
        str: The authorization URL to redirect to.
    """
    # Get client configuration
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    if not client_id or not client_secret:
        logger.error("Missing Google OAuth credentials")
        return "Error: Missing Google OAuth credentials. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
    
    # Create the flow
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    
    # Generate the authorization URL
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    
    logger.info(f"Authorization URL: {auth_url}")
    return auth_url


def process_auth_code(code: str, state: str) -> str:
    """
    Process the authorization code from the OAuth2 callback.
    
    Args:
        code (str): The authorization code.
        state (str): The state parameter.
        
    Returns:
        str: A message indicating the result of the operation.
    """
    # Get client configuration
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    if not client_id or not client_secret:
        logger.error("Missing Google OAuth credentials")
        return "Error: Missing Google OAuth credentials. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
    
    # Create the flow
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    
    try:
        # Exchange the authorization code for credentials
        flow.fetch_token(code=code)
        
        # Get the credentials
        credentials = flow.credentials
        
        # Save the credentials
        token_manager.store_token(credentials)
        
        logger.info("Successfully processed authorization code and saved credentials")
        return "Successfully authenticated with Google. You can now close this window and return to the application."
    except Exception as e:
        logger.error(f"Failed to process authorization code: {e}")
        return f"Error: Failed to process authorization code: {e}"


def start_oauth_process(timeout: int = 300) -> bool:
    """
    Start the OAuth process and wait for it to complete.
    
    Args:
        timeout (int, optional): Timeout in seconds. Defaults to 300 (5 minutes).
        
    Returns:
        bool: True if authentication was successful, False otherwise.
    """
    # Get the authorization URL
    auth_url = login()
    
    if auth_url.startswith("Error:"):
        logger.error(f"Failed to get authorization URL: {auth_url}")
        return False
    
    # Open the authorization URL in the default browser
    logger.info("Opening authorization URL in browser")
    webbrowser.open(auth_url)
    
    # Wait for the user to complete the authentication
    logger.info(f"Waiting for authentication to complete (timeout: {timeout} seconds)")
    
    # Check if tokens exist every 5 seconds
    start_time = time.time()
    while time.time() - start_time < timeout:
        if token_manager.tokens_exist():
            logger.info("Authentication completed successfully")
            return True
        
        time.sleep(5)
    
    logger.error(f"Authentication timed out after {timeout} seconds")
    return False


def get_credentials() -> Optional[Credentials]:
    """
    Get the OAuth2 credentials.
    
    Returns:
        Optional[Credentials]: The credentials, or None if not authenticated.
    """
    # Check if tokens exist
    if not token_manager.tokens_exist():
        logger.warning("No tokens found")
        return None
    
    # Load the tokens
    credentials = token_manager.get_token()
    
    if not credentials:
        return None
    
    # Check if the token is expired and refresh it if needed
    if credentials.expired:
        logger.info("Token is expired, refreshing")
        try:
            credentials.refresh(GoogleRequest())
            
            # Save the refreshed token
            token_manager.store_token(credentials)
            
            logger.info("Token refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return None
    
    return credentials 