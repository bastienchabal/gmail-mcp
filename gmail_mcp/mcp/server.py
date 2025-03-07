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
from gmail_mcp.auth.oauth import get_credentials

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
        Get information about the server.
        
        Returns:
            Dict[str, Any]: The server information.
        """
        config = get_config()
        
        return {
            "name": config.get("server_name", "Gmail MCP"),
            "version": config.get("server_version", "1.3.0"),
            "description": config.get("server_description", "A Model Context Protocol server for Gmail integration with Claude Desktop"),
            "host": config.get("host", "localhost"),
            "port": config.get("port", 8000),
        }
    
    @mcp.resource("server://config")
    def server_config() -> Dict[str, Any]:
        """
        Get the server configuration.
        
        Returns:
            Dict[str, Any]: The server configuration.
        """
        config = get_config()
        
        # Remove sensitive information
        safe_config = {k: v for k, v in config.items() if not any(sensitive in k for sensitive in ["secret", "password", "token", "key"])}
        
        return safe_config
    
    @mcp.resource("debug://help")
    def debug_help() -> Dict[str, Any]:
        """
        Get debugging help for the Gmail MCP server.
        
        This resource provides guidance on how to debug issues with the MCP server,
        particularly focusing on Claude Desktop integration problems.
        
        Returns:
            Dict[str, Any]: Debugging help information.
        """
        return {
            "title": "Gmail MCP Debugging Guide",
            "description": "This guide helps diagnose issues with the Gmail MCP server.",
            "common_issues": [
                {
                    "issue": "Claude Desktop is stuck in a polling loop",
                    "possible_causes": [
                        "Claude is not accessing resources",
                        "Claude is not calling tools",
                        "Claude is waiting for a response that never comes",
                        "The MCP server is not responding correctly"
                    ],
                    "solutions": [
                        "Simplify prompts and focus on direct tool calls",
                        "Use simple code examples without await/async",
                        "Check logs for errors or unexpected behavior",
                        "Restart the MCP server and Claude Desktop"
                    ]
                },
                {
                    "issue": "Authentication fails",
                    "possible_causes": [
                        "Invalid client ID or client secret",
                        "Redirect URI mismatch",
                        "Insufficient permissions",
                        "Token expired or invalid"
                    ],
                    "solutions": [
                        "Check Google Cloud Console configuration",
                        "Verify redirect URI matches exactly",
                        "Ensure all required scopes are included",
                        "Delete tokens.json and re-authenticate"
                    ]
                },
                {
                    "issue": "Gmail API calls fail",
                    "possible_causes": [
                        "Not authenticated",
                        "Insufficient permissions",
                        "API quota exceeded",
                        "Invalid request parameters"
                    ],
                    "solutions": [
                        "Check authentication status",
                        "Verify Gmail API is enabled in Google Cloud Console",
                        "Check for quota errors in logs",
                        "Verify request parameters are valid"
                    ]
                }
            ],
            "debugging_steps": [
                "1. Check logs for errors or unexpected behavior",
                "2. Verify authentication status using auth://status resource",
                "3. Try simple tool calls like get_email_count()",
                "4. Check if Claude Desktop is accessing resources",
                "5. Restart the MCP server and Claude Desktop",
                "6. Try using the MCP Inspector to verify functionality"
            ],
            "example_workflow": {
                "description": "A simple workflow to test basic functionality",
                "steps": [
                    "1. Access auth://status resource",
                    "2. If not authenticated, call authenticate()",
                    "3. Call get_email_count()",
                    "4. Call list_emails(max_results=3)"
                ],
                "code": """
# Check authentication
auth_status = mcp.resources.get("auth://status")
print(f"Authentication status: {auth_status}")

# Authenticate if needed
if not auth_status.get("authenticated", False):
    result = mcp.tools.authenticate()
    print(f"Authentication result: {result}")
    
    # Check authentication status again
    auth_status = mcp.resources.get("auth://status")
    print(f"Updated authentication status: {auth_status}")

# Get email count
email_count = mcp.tools.get_email_count()
print(f"Email count: {email_count}")

# List recent emails
emails = mcp.tools.list_emails(max_results=3)
print(f"Recent emails: {emails}")
"""
            }
        }
    
    @mcp.resource("server://status")
    def server_status() -> Dict[str, Any]:
        """
        Get the comprehensive server status, including authentication and Gmail status.
        
        This resource provides a one-stop overview of the server status, including
        authentication status, Gmail account information, and available functionality.
        
        Returns:
            Dict[str, Any]: The server status.
        """
        # Get credentials
        credentials = get_credentials()
        authenticated = credentials is not None
        
        # Basic status
        status = {
            "server": {
                "name": "Gmail MCP",
                "version": "1.3.0",
                "status": "running",
            },
            "authentication": {
                "authenticated": authenticated,
                "status": "authenticated" if authenticated else "not_authenticated",
            },
            "available_resources": [
                "auth://status",
                "gmail://status",
                "server://info",
                "server://config",
                "server://status",
                "debug://help",
                "health://",
            ],
            "available_tools": [
                "authenticate()",
                "login_tool()",
                "process_auth_code_tool(code, state)",
                "logout()",
                "check_auth_status()",
                "get_email_count()",
                "list_emails(max_results=10, label='INBOX')",
                "get_email(email_id)",
                "search_emails(query, max_results=10)",
                "get_email_overview()",
            ],
            "available_prompts": [
                "gmail_welcome",
                "authenticate_gmail",
                "access_gmail_data",
            ],
            "next_steps": [],
        }
        
        # Add next steps based on authentication status
        if not authenticated:
            status["next_steps"] = [
                "Check authentication status: mcp.tools.check_auth_status()",
                "Start authentication: mcp.tools.authenticate()",
                "After authentication, verify status: mcp.tools.check_auth_status()",
            ]
        else:
            status["next_steps"] = [
                "Get email overview: mcp.tools.get_email_overview()",
                "Get email count: mcp.tools.get_email_count()",
                "List recent emails: mcp.tools.list_emails(max_results=5)",
                "Search for emails: mcp.tools.search_emails(query='is:unread')",
            ]
            
            # Add Gmail account information if authenticated
            try:
                from googleapiclient.discovery import build
                
                # Build the Gmail API service
                service = build("gmail", "v1", credentials=credentials)
                
                # Get the profile information
                profile = service.users().getProfile(userId="me").execute()
                
                status["gmail"] = {
                    "email": profile.get("emailAddress", "Unknown"),
                    "total_messages": profile.get("messagesTotal", 0),
                    "total_threads": profile.get("threadsTotal", 0),
                    "storage_used": profile.get("storageUsed", 0),
                }
            except Exception as e:
                status["gmail"] = {
                    "status": "error",
                    "error": str(e),
                }
        
        return status 