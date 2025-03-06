"""
Configuration Utility Module

This module provides functions for loading and accessing application configuration.
"""

import os
import logging
from typing import Dict, Any, Optional

from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()


def get_config() -> Dict[str, Any]:
    """
    Get the application configuration from environment variables.

    Returns:
        Dict[str, Any]: A dictionary containing the application configuration.
    """
    return {
        "host": os.getenv("MCP_SERVER_HOST", "localhost"),
        "port": int(os.getenv("MCP_SERVER_PORT", "8000")),
        "debug": os.getenv("MCP_SERVER_DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "google_client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "google_client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "google_redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback"),
        "gmail_api_scopes": os.getenv(
            "GMAIL_API_SCOPES",
            "https://www.googleapis.com/auth/gmail.readonly,"
            "https://www.googleapis.com/auth/gmail.send,"
            "https://www.googleapis.com/auth/gmail.labels,"
            "https://www.googleapis.com/auth/gmail.modify"
        ).split(","),
        "token_storage_path": os.getenv("TOKEN_STORAGE_PATH", "./tokens.json"),
        "token_encryption_key": os.getenv("TOKEN_ENCRYPTION_KEY", ""),
        "mcp_version": os.getenv("MCP_VERSION", "2024-11-05"),
        "mcp_server_name": os.getenv("MCP_SERVER_NAME", "Gmail MCP"),
        "mcp_server_description": os.getenv(
            "MCP_SERVER_DESCRIPTION",
            "A Model Context Protocol server for Gmail integration with Claude Desktop"
        ),
        "calendar_api_enabled": os.getenv("CALENDAR_API_ENABLED", "false").lower() == "true",
        "calendar_api_scopes": os.getenv(
            "CALENDAR_API_SCOPES",
            "https://www.googleapis.com/auth/calendar.readonly,"
            "https://www.googleapis.com/auth/calendar.events"
        ).split(",") if os.getenv("CALENDAR_API_ENABLED", "false").lower() == "true" else [],
    }


def get_config_value(key: str, default: Optional[Any] = None) -> Any:
    """
    Get a specific configuration value.

    Args:
        key (str): The configuration key to retrieve.
        default (Optional[Any], optional): The default value if the key is not found. Defaults to None.

    Returns:
        Any: The configuration value.
    """
    config = get_config()
    return config.get(key, default) 