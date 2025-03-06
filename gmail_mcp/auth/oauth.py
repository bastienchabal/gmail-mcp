"""
OAuth Module

This module provides OAuth2 authentication functionality for the Gmail API.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple

import httpx
from mcp.server.fastmcp import FastMCP, Context
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from google.auth.exceptions import RefreshError

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.utils.config import get_config
from gmail_mcp.auth.token_manager import TokenManager

# Get logger
logger = get_logger(__name__)

# Get token manager
token_manager = TokenManager()


def setup_oauth_routes(mcp: FastMCP) -> None:
    """
    Set up OAuth routes on the FastMCP application.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    # FastMCP doesn't directly support custom HTTP routes like FastAPI
    # Instead, we'll implement OAuth functionality as tools and resources
    
    @mcp.tool()
    def login() -> str:
        """
        Initiate the OAuth2 flow by providing a link to the Google authorization page.
        
        Returns:
            str: The authorization URL to redirect to.
        """
        config = get_config()
        
        # Create the OAuth2 flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": config["google_client_id"],
                    "client_secret": config["google_client_secret"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [config["google_redirect_uri"]],
                }
            },
            scopes=config["gmail_api_scopes"],
        )
        
        # Set the redirect URI
        flow.redirect_uri = config["google_redirect_uri"]
        
        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        
        # Store the state for later verification
        token_manager.store_state(state)
        
        return f"Please visit this URL to authorize the application: {authorization_url}"
    
    @mcp.tool()
    def process_auth_code(code: str, state: str) -> str:
        """
        Process the OAuth2 authorization code and state.
        
        Args:
            code (str): The authorization code from Google.
            state (str): The state parameter from Google.
            
        Returns:
            str: A success or error message.
        """
        config = get_config()
        
        # Verify the state
        if not token_manager.verify_state(state):
            logger.error("Invalid state parameter")
            return "Error: Invalid state parameter. Authorization failed."
        
        # Create the OAuth2 flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": config["google_client_id"],
                    "client_secret": config["google_client_secret"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [config["google_redirect_uri"]],
                }
            },
            scopes=config["gmail_api_scopes"],
            state=state,
        )
        
        # Set the redirect URI
        flow.redirect_uri = config["google_redirect_uri"]
        
        try:
            # Exchange the authorization code for credentials
            flow.fetch_token(code=code)
            
            # Get the credentials
            credentials = flow.credentials
            
            # Store the credentials
            token_manager.store_token(credentials)
            
            return "Authorization successful! You can now use the Gmail MCP server."
        except Exception as e:
            logger.error(f"Failed to process authorization code: {e}")
            return f"Error: Failed to process authorization code: {e}"
    
    @mcp.tool()
    def logout() -> str:
        """
        Log out by revoking the access token and clearing the stored credentials.
        
        Returns:
            str: A success or error message.
        """
        # Get the credentials
        credentials = token_manager.get_token()
        
        if credentials:
            try:
                # Revoke the access token
                httpx.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": credentials.token},
                    headers={"content-type": "application/x-www-form-urlencoded"},
                )
                
                # Clear the stored credentials
                token_manager.clear_token()
                
                return "Logged out successfully."
            except Exception as e:
                logger.error(f"Failed to revoke token: {e}")
                return f"Error: Failed to revoke token: {e}"
        else:
            return "No active session to log out from."
    
    @mcp.resource("auth://status")
    def auth_status() -> Dict[str, Any]:
        """
        Get the current authentication status.
        
        Returns:
            Dict[str, Any]: The authentication status.
        """
        credentials = token_manager.get_token()
        
        if credentials:
            return {
                "authenticated": True,
                "email": credentials.client_id,  # This is not the email, just a placeholder
                "scopes": credentials.scopes,
                "expires": credentials.expiry.isoformat() if credentials.expiry else None,
            }
        else:
            return {
                "authenticated": False,
            }


def get_credentials() -> Optional[Credentials]:
    """
    Get the OAuth2 credentials.
    
    Returns:
        Optional[Credentials]: The OAuth2 credentials, or None if not authenticated.
    """
    # Get the credentials
    credentials = token_manager.get_token()
    
    if not credentials:
        logger.warning("No credentials found")
        return None
    
    # Refresh the credentials if expired
    if credentials.expired:
        try:
            credentials.refresh(GoogleRequest())
            token_manager.store_token(credentials)
        except RefreshError as e:
            logger.error(f"Failed to refresh credentials: {e}")
            token_manager.clear_token()
            return None
    
    return credentials 