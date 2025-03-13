#!/usr/bin/env python3
"""
Re-authenticate with Calendar API Scopes

This script helps users re-authenticate with the Gmail MCP server
to include the Calendar API scopes.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.utils.config import get_config
from gmail_mcp.auth.token_manager import TokenManager
from gmail_mcp.auth.oauth import start_oauth_process

# Get logger
logger = get_logger(__name__)

# Get configuration
config = get_config()

def main():
    """
    Main entry point for the re-authentication script.
    """
    # Check if Calendar API is enabled
    if not config.get("calendar_api_enabled", False):
        print("Calendar API is not enabled in your configuration.")
        print("Please set CALENDAR_API_ENABLED=true in your environment variables.")
        return False
    
    # Get token manager
    token_manager = TokenManager()
    
    # Check if tokens exist
    if token_manager.tokens_exist():
        print("Existing authentication tokens found.")
        print("Deleting tokens to force re-authentication with Calendar API scopes...")
        token_manager.clear_token()
    
    # Start authentication process
    print("Starting authentication process with Calendar API scopes...")
    print("This will open a browser window for you to authenticate with Google.")
    
    # Print the scopes being requested
    print("\nRequesting the following scopes:")
    for scope in config.get("gmail_api_scopes", []):
        print(f"- {scope}")
    if config.get("calendar_api_enabled", False):
        for scope in config.get("calendar_api_scopes", []):
            print(f"- {scope}")
    print("- https://www.googleapis.com/auth/userinfo.email")
    print("- https://www.googleapis.com/auth/userinfo.profile")
    
    # Start the OAuth process
    success = start_oauth_process(timeout=300)
    
    if success:
        print("\nAuthentication successful!")
        print("You now have access to both Gmail and Calendar APIs.")
        return True
    else:
        print("\nAuthentication failed.")
        print("Please try again or check your configuration.")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 