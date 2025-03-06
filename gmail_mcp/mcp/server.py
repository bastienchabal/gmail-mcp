"""
MCP Server Module

This module provides helper functions for the MCP server implementation.
With FastMCP, we no longer need to manually set up routes as they are handled automatically.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4

from mcp.server.fastmcp import FastMCP, Context

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.utils.config import get_config

# Get logger
logger = get_logger(__name__)

# This file is kept for compatibility, but most of its functionality
# has been moved to the main.py file and other modules.
# FastMCP handles the MCP protocol implementation automatically.

def setup_mcp_handlers(mcp: FastMCP) -> None:
    """
    Set up additional MCP message handlers if needed.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    # FastMCP automatically handles the core MCP protocol
    # We can add custom message handlers here if needed
    
    @mcp.resource("server://info")
    def server_info() -> Dict[str, Any]:
        """
        Get information about the MCP server.
        
        Returns:
            Dict[str, Any]: Server information.
        """
        config = get_config()
        return {
            "name": config["mcp_server_name"],
            "description": config["mcp_server_description"],
            "version": "0.1.0",
            "mcp_version": config["mcp_version"],
        }
    
    @mcp.resource("server://config")
    def server_config() -> Dict[str, Any]:
        """
        Get the server configuration.
        
        Returns:
            Dict[str, Any]: Server configuration.
        """
        config = get_config()
        # Filter out sensitive information
        safe_config = {
            k: v for k, v in config.items() 
            if not any(sensitive in k for sensitive in ["secret", "key", "token", "password"])
        }
        return safe_config 