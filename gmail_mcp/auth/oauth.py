"""
OAuth Module

This module provides OAuth2 authentication functionality for the Gmail API.
"""

import os
import json
import logging
import sys
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
from gmail_mcp.auth.callback_server import start_oauth_flow

# Get logger
logger = get_logger(__name__)

# Get token manager
token_manager = TokenManager()

# Define login function outside of setup_oauth_routes for direct import
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
    
    return authorization_url


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


def start_oauth_process(timeout: int = 300) -> bool:
    """
    Start the OAuth process by opening the browser and starting the callback server.
    
    This function handles the complete OAuth flow, including:
    1. Generating the authorization URL
    2. Starting the callback server
    3. Opening the browser
    4. Processing the authorization code
    5. Storing the credentials
    
    Args:
        timeout (int, optional): The maximum time to wait for the callback in seconds. Defaults to 300 (5 minutes).
        
    Returns:
        bool: True if authentication was successful, False otherwise.
    """
    try:
        # Get the authorization URL
        auth_url = login()
        
        # Get the host from the redirect URI
        config = get_config()
        redirect_uri = config["google_redirect_uri"]
        host = "localhost"  # Default
        
        # Extract host from redirect URI if possible
        if redirect_uri.startswith("http://") or redirect_uri.startswith("https://"):
            parts = redirect_uri.split("://")[1].split("/")[0].split(":")
            host = parts[0]
        
        # Start the OAuth flow - don't specify a port, let it be extracted from the redirect URI
        start_oauth_flow(auth_url, process_auth_code, host, timeout=timeout)
        
        # Check if the tokens were created
        if token_manager.tokens_exist():
            logger.info("Authentication successful, tokens created")
            return True
        else:
            logger.error("Authentication failed, no tokens created")
            print("\nAuthentication failed. Please try again.")
            return False
            
    except KeyboardInterrupt:
        logger.info("Authentication process interrupted by user")
        print("\nAuthentication process interrupted. Exiting...")
        return False
        
    except Exception as e:
        logger.error(f"Error during authentication process: {e}")
        print(f"\nError during authentication: {e}")
        print("Please try again or check the logs for more information.")
        return False


def setup_oauth_routes(mcp: FastMCP) -> None:
    """
    Set up OAuth routes on the FastMCP application.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    # FastMCP doesn't directly support custom HTTP routes like FastAPI
    # Instead, we'll implement OAuth functionality as tools and resources
    
    @mcp.tool()
    def login_tool() -> str:
        """
        Initiate the OAuth2 flow by providing a link to the Google authorization page.
        
        Returns:
            str: The authorization URL to redirect to.
        """
        return login()
    
    @mcp.tool()
    def authenticate() -> str:
        """
        Start the complete OAuth authentication process.
        
        This tool opens a browser window and starts a local server to handle the callback.
        
        Returns:
            str: A message indicating that the authentication process has started.
        """
        # Start the OAuth process in a separate thread
        import threading
        thread = threading.Thread(target=start_oauth_process)
        thread.daemon = True
        thread.start()
        
        return "Authentication process started. Please check your browser to complete the process."
    
    @mcp.tool()
    def process_auth_code_tool(code: str, state: str) -> str:
        """
        Process the OAuth2 authorization code and state.
        
        Args:
            code (str): The authorization code from Google.
            state (str): The state parameter from Google.
            
        Returns:
            str: A success or error message.
        """
        return process_auth_code(code, state)
    
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
    
    @mcp.tool()
    def check_auth_status() -> Dict[str, Any]:
        """
        Check the current authentication status.
        
        This tool provides a direct way to check if the user is authenticated
        without having to access the auth://status resource.
        
        Returns:
            Dict[str, Any]: The authentication status.
        """
        # Get the credentials
        credentials = token_manager.get_token()
        
        if not credentials:
            return {
                "authenticated": False,
                "message": "Not authenticated. Use the authenticate tool to start the authentication process.",
                "next_steps": [
                    "Call authenticate() to start the authentication process"
                ]
            }
        
        # Check if the credentials are expired
        if credentials.expired:
            try:
                # Try to refresh the token
                credentials.refresh(GoogleRequest())
                token_manager.store_token(credentials)
                
                return {
                    "authenticated": True,
                    "message": "Authentication is valid. Token was refreshed.",
                    "status": "refreshed"
                }
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                return {
                    "authenticated": False,
                    "message": f"Authentication expired and could not be refreshed: {e}",
                    "next_steps": [
                        "Call authenticate() to start a new authentication process"
                    ],
                    "status": "expired"
                }
        
        return {
            "authenticated": True,
            "message": "Authentication is valid.",
            "status": "valid"
        }
    
    @mcp.resource("auth://status")
    def auth_status() -> Dict[str, Any]:
        """
        Get the current authentication status.
        
        Returns:
            Dict[str, Any]: The authentication status.
        """
        # Get the credentials
        credentials = token_manager.get_token()
        
        if not credentials:
            return {
                "authenticated": False,
                "message": "Not authenticated. Use the authenticate tool to start the authentication process.",
                "next_steps": [
                    "Call authenticate() to start the authentication process",
                    "The user will need to complete the authentication in their browser"
                ]
            }
        
        # Check if the credentials are expired
        if credentials.expired:
            try:
                # Try to refresh the token
                credentials.refresh(GoogleRequest())
                token_manager.store_token(credentials)
                
                # Get the user info
                import httpx
                response = httpx.get(
                    "https://www.googleapis.com/oauth2/v1/userinfo",
                    headers={"Authorization": f"Bearer {credentials.token}"},
                )
                user_info = response.json()
                
                return {
                    "authenticated": True,
                    "email": user_info.get("email", "Unknown"),
                    "name": user_info.get("name", "Unknown"),
                    "picture": user_info.get("picture"),
                    "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                    "scopes": credentials.scopes,
                    "message": "Authentication is valid. Token was refreshed.",
                    "status": "refreshed"
                }
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                return {
                    "authenticated": False,
                    "message": f"Authentication expired and could not be refreshed: {e}",
                    "next_steps": [
                        "Call authenticate() to start a new authentication process",
                        "The user will need to complete the authentication in their browser"
                    ],
                    "status": "expired"
                }
        
        # Get the user info
        try:
            import httpx
            response = httpx.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {credentials.token}"},
            )
            user_info = response.json()
            
            return {
                "authenticated": True,
                "email": user_info.get("email", "Unknown"),
                "name": user_info.get("name", "Unknown"),
                "picture": user_info.get("picture"),
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "scopes": credentials.scopes,
                "message": "Authentication is valid.",
                "status": "valid"
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {
                "authenticated": True,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "scopes": credentials.scopes,
                "message": f"Authentication is valid, but failed to get user info: {e}",
                "status": "valid_with_errors"
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