#!/usr/bin/env python3
"""
Gmail MCP Server - Main Entry Point

This module serves as the entry point for the Gmail MCP server application.
It initializes the FastMCP application and sets up the MCP tools and resources.
"""

import os
import logging
import sys
import traceback
from typing import Dict, Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from gmail_mcp.utils.config import get_config
from gmail_mcp.utils.logger import setup_logger
from gmail_mcp.auth.oauth import setup_oauth_routes, start_oauth_process
from gmail_mcp.auth.token_manager import TokenManager
from gmail_mcp.gmail.client import setup_gmail_tools
from gmail_mcp.gmail.processor import parse_email_message, analyze_thread, get_sender_history, extract_email_metadata
from gmail_mcp.context.builders import setup_resource_builders
from gmail_mcp.mcp.server import setup_mcp_handlers
from gmail_mcp.mcp.prompts import setup_prompts

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger()

# Get configuration
config = get_config()

# Create FastMCP application
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "Gmail MCP"),
    description=os.getenv(
        "MCP_SERVER_DESCRIPTION",
        "A Model Context Protocol server for Gmail integration with Claude Desktop",
    ),
    version="1.3.0",
    default_prompt="gmail_welcome",
)

# Setup OAuth routes
setup_oauth_routes(mcp)

# Setup Gmail tools
setup_gmail_tools(mcp)

# Setup resource builders
setup_resource_builders(mcp)

# Setup additional MCP handlers
setup_mcp_handlers(mcp)

# Setup prompts
setup_prompts(mcp)

# Health check resource
@mcp.resource("health://")
def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}

def check_authentication(max_attempts: int = 3, timeout: int = 300) -> bool:
    """
    Check if the user is authenticated and prompt them to authenticate if not.
    
    Args:
        max_attempts (int, optional): Maximum number of authentication attempts. Defaults to 3.
        timeout (int, optional): Timeout for each authentication attempt in seconds. Defaults to 300 (5 minutes).
        
    Returns:
        bool: True if authentication is successful, False otherwise.
    """
    token_manager = TokenManager()
    
    # If tokens already exist, we're good to go
    if token_manager.tokens_exist():
        logger.info("Authentication tokens found, user is authenticated")
        try:
            # Verify that the tokens are valid by checking if we can get credentials
            from gmail_mcp.auth.oauth import get_credentials
            credentials = get_credentials()
            if credentials:
                logger.info("Credentials are valid")
                return True
            else:
                logger.warning("Tokens exist but credentials are invalid, need to re-authenticate")
                # Delete the invalid tokens
                token_manager.clear_token()
        except Exception as e:
            logger.error(f"Error checking credentials: {e}")
            logger.error(traceback.format_exc())
            # Delete the invalid tokens
            token_manager.clear_token()
    
    # Try to authenticate
    for attempt in range(1, max_attempts + 1):
        logger.warning("No authentication tokens found. User needs to authenticate.")
        print("\n" + "=" * 80)
        print("AUTHENTICATION REQUIRED")
        print("=" * 80)
        print(f"Starting the authentication process (attempt {attempt}/{max_attempts})...")
        print("A browser window will open to complete the authentication.")
        print("=" * 80 + "\n")
        
        # Start the OAuth process with the specified timeout
        success = start_oauth_process(timeout=timeout)
        
        if success:
            logger.info("Authentication successful")
            return True
        
        # If we've reached the maximum number of attempts, give up
        if attempt >= max_attempts:
            logger.error(f"Authentication failed after {max_attempts} attempts")
            print("\n" + "=" * 80)
            print("AUTHENTICATION FAILED")
            print("=" * 80)
            print(f"Failed to authenticate after {max_attempts} attempts.")
            print("Please check your Google Cloud Console configuration and try again later.")
            print("=" * 80 + "\n")
            return False
        
        # Otherwise, try again
        print("\n" + "=" * 80)
        print("AUTHENTICATION FAILED - RETRYING")
        print("=" * 80)
        print(f"Authentication attempt {attempt}/{max_attempts} failed.")
        print(f"Retrying in 3 seconds...")
        print("=" * 80 + "\n")
        
        # Wait a bit before trying again
        import time
        time.sleep(3)
    
    # We should never get here, but just in case
    return False

def main() -> None:
    """Run the application."""
    logger.info("Starting Gmail MCP server")
    logger.info(f"Server configuration: host={config['host']}, port={config['port']}")
    
    try:
        # Check if the user is authenticated
        if not check_authentication():
            logger.error("Authentication failed, exiting")
            print("Exiting due to authentication failure.")
            sys.exit(1)
        
        # Run the server
        # The run method doesn't accept host, port, reload, or log_level parameters
        # Instead, we should use the mcp CLI tool to run the server
        mcp.run()
    except Exception as e:
        logger.error(f"Error running the application: {e}")
        logger.error(traceback.format_exc())
        print(f"Error running the application: {e}")
        print("Please check the logs for more information.")
        sys.exit(1)

if __name__ == "__main__":
    main() 