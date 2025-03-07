"""
MCP Prompts Module

This module defines all prompts available in the Gmail MCP server.
Prompts are templated messages and workflows for users.
"""

import logging
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP

from gmail_mcp.utils.logger import get_logger

# Get logger
logger = get_logger(__name__)


def setup_prompts(mcp: FastMCP) -> None:
    """
    Set up all prompts for the Gmail MCP server.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    @mcp.prompt("gmail://quickstart")
    def quickstart_prompt() -> Dict[str, Any]:
        """
        Quick Start Guide for Gmail MCP
        
        This prompt provides a simple guide to get started with the Gmail MCP.
        It includes basic instructions for authentication and common operations.
        """
        return {
            "title": "Gmail MCP Quick Start Guide",
            "description": "Get started with Gmail integration in Claude Desktop",
            "content": """
# Gmail MCP Quick Start Guide

Welcome to the Gmail MCP for Claude Desktop! This integration allows Claude to access and work with your Gmail account.

## Getting Started

1. **Authentication**: First, you need to authenticate with your Google account.
   - Check your authentication status with `check_auth_status()`
   - If not authenticated, use `authenticate()` to start the process

2. **Basic Email Operations**:
   - Get an overview of your inbox with `get_email_overview()`
   - List recent emails with `list_emails(max_results=10, label="INBOX")`
   - Search for specific emails with `search_emails(query="from:example@gmail.com")`
   - View a specific email with `get_email(email_id="...")`

3. **Troubleshooting**:
   - If you encounter any issues, check the debug help resource: `debug://help`
   - You can also check the server status with `server://status`

## Example Workflow

Here's a simple workflow to get started:

1. Check authentication status:
   ```
   check_auth_status()
   ```

2. If not authenticated, start the authentication process:
   ```
   authenticate()
   ```

3. Get an overview of your inbox:
   ```
   get_email_overview()
   ```

4. Search for emails from a specific sender:
   ```
   search_emails(query="from:example@gmail.com")
   ```

5. View a specific email (replace with an actual email ID):
   ```
   get_email(email_id="18abc123def456")
   ```

## Need Help?

If you need more information, check the following resources:
- `server://info` - General server information
- `debug://help` - Troubleshooting guide
- `gmail://status` - Current Gmail account status
            """
        }
    
    @mcp.prompt("gmail://search_guide")
    def search_guide_prompt() -> Dict[str, Any]:
        """
        Gmail Search Syntax Guide
        
        This prompt provides a guide to Gmail's search syntax for use with the search_emails tool.
        """
        return {
            "title": "Gmail Search Syntax Guide",
            "description": "Learn how to use Gmail's powerful search syntax",
            "content": """
# Gmail Search Syntax Guide

When using the `search_emails()` tool, you can leverage Gmail's powerful search syntax to find exactly what you're looking for.

## Basic Search Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `from:` | Emails from a specific sender | `from:example@gmail.com` |
| `to:` | Emails to a specific recipient | `to:example@gmail.com` |
| `subject:` | Emails with specific text in the subject | `subject:meeting` |
| `has:attachment` | Emails with attachments | `has:attachment` |
| `filename:` | Emails with specific attachment types | `filename:pdf` |
| `in:` | Emails in a specific location | `in:inbox`, `in:trash` |
| `is:` | Emails with a specific status | `is:unread`, `is:starred` |
| `after:` | Emails after a date | `after:2023/01/01` |
| `before:` | Emails before a date | `before:2023/12/31` |
| `older:` | Emails older than a time period | `older:1d` (1 day) |
| `newer:` | Emails newer than a time period | `newer:1w` (1 week) |

## Combining Operators

You can combine multiple operators to create more specific searches:

- `from:example@gmail.com has:attachment` - Emails from example@gmail.com with attachments
- `subject:report is:unread` - Unread emails with "report" in the subject
- `after:2023/01/01 before:2023/01/31 from:example@gmail.com` - Emails from example@gmail.com in January 2023

## Advanced Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `OR` | Match either term | `from:alice OR from:bob` |
| `-` | Exclude matches | `-from:example@gmail.com` |
| `( )` | Group operators | `(from:alice OR from:bob) has:attachment` |
| `"..."` | Exact phrase | `"quarterly report"` |
| `{ }` | Find messages with only one of the terms | `{project meeting}` |

## Date Formats

- YYYY/MM/DD: `after:2023/01/01`
- Relative: `newer:2d` (2 days), `older:1w` (1 week), `newer:3m` (3 months), `older:1y` (1 year)

## Examples

1. Find unread emails with attachments:
   ```
   is:unread has:attachment
   ```

2. Find emails from a specific domain in the last week:
   ```
   from:@example.com newer:1w
   ```

3. Find emails with "report" in the subject that are starred:
   ```
   subject:report is:starred
   ```

4. Find emails from Alice or Bob with PDF attachments:
   ```
   (from:alice OR from:bob) filename:pdf
   ```

5. Find emails with "urgent" in the subject that are unread:
   ```
   subject:urgent is:unread
   ```
            """
        }
    
    @mcp.prompt("gmail://authentication_guide")
    def authentication_guide_prompt() -> Dict[str, Any]:
        """
        Gmail Authentication Guide
        
        This prompt provides a guide to the authentication process for the Gmail MCP.
        """
        return {
            "title": "Gmail Authentication Guide",
            "description": "Learn how to authenticate with your Google account",
            "content": """
# Gmail Authentication Guide

To use the Gmail MCP with Claude Desktop, you need to authenticate with your Google account. This guide explains the authentication process and how to troubleshoot common issues.

## Authentication Process

1. **Check Authentication Status**
   First, check if you're already authenticated:
   ```
   check_auth_status()
   ```

2. **Start Authentication**
   If not authenticated, start the process:
   ```
   authenticate()
   ```

3. **Complete Authentication**
   - A browser window will open with Google's login page
   - Sign in with your Google account and grant the requested permissions
   - After successful authentication, you'll receive an authorization code
   - Copy the authorization code and provide it to Claude:
     ```
     process_auth_code_tool(code="your_authorization_code_here")
     ```

4. **Verify Authentication**
   Check that authentication was successful:
   ```
   check_auth_status()
   ```

## Authentication Troubleshooting

### Common Issues

1. **Browser Doesn't Open**
   - The authentication URL will be displayed in Claude's response
   - Copy and paste the URL into your browser manually

2. **Authorization Code Invalid**
   - Make sure you copied the entire code without extra spaces
   - The code expires quickly, so use it immediately after receiving it
   - If it's expired, start the process again with `authenticate()`

3. **Permission Denied**
   - Ensure you grant all requested permissions
   - If you denied permissions, start again with `authenticate()`

4. **Already Authenticated**
   - If you want to switch accounts, first log out:
     ```
     logout()
     ```
   - Then start the authentication process again

5. **Token Expired**
   - Tokens automatically refresh, but if you encounter issues:
     ```
     authenticate()
     ```

## Security Information

- The Gmail MCP uses OAuth 2.0 for secure authentication
- Your credentials are stored securely on your local machine
- You can revoke access at any time through your Google Account settings or by using the `logout()` tool
- The MCP only requests the minimum permissions needed to function

## Need Help?

If you encounter any authentication issues:
- Check the `auth://status` resource for detailed information
- Check the `debug://help` resource for troubleshooting guidance
- Try the `logout()` tool followed by `authenticate()` to restart the process
            """
        }
    
    @mcp.prompt("gmail://debug_guide")
    def debug_guide_prompt() -> Dict[str, Any]:
        """
        Gmail MCP Debugging Guide
        
        This prompt provides a guide to debugging common issues with the Gmail MCP.
        """
        return {
            "title": "Gmail MCP Debugging Guide",
            "description": "Troubleshoot common issues with the Gmail MCP",
            "content": """
# Gmail MCP Debugging Guide

This guide helps you troubleshoot common issues with the Gmail MCP integration in Claude Desktop.

## Quick Diagnostic Steps

1. **Check Server Status**
   ```
   server://status
   ```

2. **Check Authentication Status**
   ```
   check_auth_status()
   ```

3. **Check Gmail Status**
   ```
   gmail://status
   ```

4. **Check Health**
   ```
   health://check
   ```

## Common Issues and Solutions

### Authentication Issues

**Symptoms:**
- "Not authenticated" errors
- Unable to access Gmail data
- Authentication loops

**Solutions:**
1. Check authentication status:
   ```
   check_auth_status()
   ```

2. If not authenticated, start the process:
   ```
   authenticate()
   ```

3. If authentication fails repeatedly:
   - Log out and try again:
     ```
     logout()
     authenticate()
     ```
   - Check that you're granting all requested permissions
   - Try using a different browser

### API Rate Limiting

**Symptoms:**
- "Rate limit exceeded" errors
- Operations fail after many requests

**Solutions:**
1. Wait a few minutes before trying again
2. Reduce the frequency of requests
3. Use batch operations when possible

### Connection Issues

**Symptoms:**
- Timeout errors
- "Failed to connect" messages

**Solutions:**
1. Check your internet connection
2. Verify the server is running:
   ```
   server://status
   ```
3. Restart the MCP server if necessary

### Permission Issues

**Symptoms:**
- "Insufficient permissions" errors
- Unable to access certain Gmail features

**Solutions:**
1. Log out and re-authenticate to grant all permissions:
   ```
   logout()
   authenticate()
   ```
2. Make sure you're using the correct Google account

### Data Not Updating

**Symptoms:**
- Stale or outdated email information
- New emails not appearing

**Solutions:**
1. Refresh the data by making a new request
2. Check for pagination tokens if listing many emails
3. Verify the correct query parameters are being used

## Advanced Debugging

### Check Debug Logs

Access detailed debug information:
```
debug://help
```

### Server Information

Get information about the server configuration:
```
server://info
server://config
```

### Health Check

Perform a comprehensive health check:
```
health://check
```

## Still Having Issues?

If you continue to experience problems:

1. Try restarting the MCP server
2. Check for any error messages in the server logs
3. Verify that your Google account has not revoked access
4. Ensure you're using the latest version of the Gmail MCP
            """
        } 