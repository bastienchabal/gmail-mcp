#!/usr/bin/env python3
"""
Gmail MCP Server - Main Entry Point

This module serves as the entry point for the Gmail MCP server application.
It initializes the FastMCP application and sets up the MCP tools and resources.
"""

import os
import logging
from typing import Dict, Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from gmail_mcp.utils.config import get_config
from gmail_mcp.utils.logger import setup_logger
from gmail_mcp.auth.oauth import setup_oauth_routes
from gmail_mcp.gmail.client import setup_gmail_tools
from gmail_mcp.gmail.processor import parse_email_message, analyze_thread, get_sender_history, extract_email_metadata
from gmail_mcp.context.builders import setup_resource_builders
from gmail_mcp.mcp.server import setup_mcp_handlers

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
    version="0.1.0",
)

# Setup OAuth routes
setup_oauth_routes(mcp)

# Setup Gmail tools
setup_gmail_tools(mcp)

# Setup resource builders (formerly context builders)
setup_resource_builders(mcp)

# Setup additional MCP handlers
setup_mcp_handlers(mcp)

# Health check resource
@mcp.resource("health://")
def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}

def main() -> None:
    """Run the application."""
    logger.info("Starting Gmail MCP server")
    logger.info(f"Server configuration: host={config['host']}, port={config['port']}")
    
    # Run the server
    # The run method doesn't accept host, port, reload, or log_level parameters
    # Instead, we should use the mcp CLI tool to run the server
    mcp.run()

if __name__ == "__main__":
    main() 