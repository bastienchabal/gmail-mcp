#!/usr/bin/env python3
"""
Authentication Test Script

This script tests the OAuth authentication process and provides detailed feedback.
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger(__name__)

def main():
    """
    Main entry point for the authentication test script.
    """
    print("\n" + "=" * 80)
    print("Gmail MCP Authentication Test")
    print("=" * 80)
    
    # Get configuration
    config = get_config()
    
    # Check required configuration
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    print("\nChecking configuration...")
    
    if not client_id:
        print("❌ GOOGLE_CLIENT_ID is not set")
        print("   Please set this environment variable with your Google OAuth client ID")
        return False
    else:
        print(f"✅ GOOGLE_CLIENT_ID: {client_id[:5]}...{client_id[-5:]}")
    
    if not client_secret:
        print("❌ GOOGLE_CLIENT_SECRET is not set")
        print("   Please set this environment variable with your Google OAuth client secret")
        return False
    else:
        print(f"✅ GOOGLE_CLIENT_SECRET: {client_secret[:3]}...{client_secret[-3:]}")
    
    print(f"✅ GOOGLE_REDIRECT_URI: {redirect_uri}")
    
    # Check if Calendar API is enabled
    calendar_enabled = config.get("calendar_api_enabled", False)
    print(f"✅ Calendar API: {'Enabled' if calendar_enabled else 'Disabled'}")
    
    # Print scopes
    print("\nRequested OAuth scopes:")
    for scope in config.get("gmail_api_scopes", []):
        print(f"✅ {scope}")
    
    if calendar_enabled:
        for scope in config.get("calendar_api_scopes", []):
            print(f"✅ {scope}")
    
    # Check if tokens already exist
    token_manager = TokenManager()
    if token_manager.tokens_exist():
        print("\n⚠️ Authentication tokens already exist")
        print("   Existing tokens will be deleted to perform a fresh authentication")
        token_manager.clear_token()
    
    # Start authentication process
    print("\nStarting authentication process...")
    print("This will open a browser window for you to authenticate with Google.")
    print("Please follow the instructions in the browser.")
    
    success = start_oauth_process(timeout=300)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ Authentication successful!")
        print("=" * 80)
        print(f"Tokens saved to: {os.path.abspath(config.get('token_storage_path', './tokens.json'))}")
        print("\nYou can now use the Gmail MCP server with Claude Desktop.")
        return True
    else:
        print("\n" + "=" * 80)
        print("❌ Authentication failed")
        print("=" * 80)
        print("Please check the error messages above and try again.")
        print("If the problem persists, check your Google Cloud Console configuration.")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 