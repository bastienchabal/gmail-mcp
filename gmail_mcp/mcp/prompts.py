"""
Prompts Module

This module defines MCP prompts that guide Claude through the authentication and email access workflow.
Prompts help Claude understand how to use the tools in the correct sequence and provide context-aware responses.
"""

from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP


def setup_prompts(mcp: FastMCP) -> None:
    """
    Set up prompts on the FastMCP application.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    
    @mcp.prompt(
        name="gmail_welcome",
        description="Welcome to Gmail MCP",
    )
    def gmail_welcome_prompt() -> Dict[str, Any]:
        """
        Welcome prompt for Gmail MCP.
        
        This is the default prompt that is shown when Claude connects to the Gmail MCP.
        It provides an overview of the available functionality and guides Claude through
        the first steps.
        
        Returns:
            Dict[str, Any]: The prompt content.
        """
        return {
            "content": """
# Gmail MCP

This MCP server allows you to access your Gmail emails. Here's how to use it:

## Quick Start

The simplest way to get started:

```
# Check if authenticated
status = mcp.tools.check_auth_status()

# If not authenticated, authenticate
if not status["authenticated"]:
    mcp.tools.authenticate()
    
# Get an overview of emails
overview = mcp.tools.get_email_overview()
```

## Authentication

Check authentication status:

```
status = mcp.tools.check_auth_status()
```

If not authenticated, authenticate:

```
result = mcp.tools.authenticate()
```

## Reading Emails

Once authenticated, you can:

1. Get email overview (recommended):
```
overview = mcp.tools.get_email_overview()
```

2. Get email count:
```
email_count = mcp.tools.get_email_count()
```

3. List recent emails:
```
emails = mcp.tools.list_emails(max_results=5)
```

4. Get a specific email:
```
email = mcp.tools.get_email(email_id="...")
```

5. Search emails:
```
results = mcp.tools.search_emails(query="is:unread")
```

## Debugging

If you encounter issues:

```
debug_help = mcp.resources.get("debug://help")
```
            """,
            "suggested_queries": [
                "Check if I'm authenticated with Gmail",
                "Show me my recent emails",
                "Search for emails from a specific person",
                "Help me authenticate with Gmail"
            ]
        }
    
    @mcp.prompt(
        name="authenticate_gmail",
        description="Authenticate with Gmail to access email data",
    )
    def authenticate_gmail_prompt() -> Dict[str, Any]:
        """
        Prompt for authenticating with Gmail.
        
        This prompt guides Claude through the authentication process,
        explaining how to use the authentication tools in the correct sequence.
        
        Returns:
            Dict[str, Any]: The prompt content.
        """
        return {
            "content": """
# Gmail Authentication

To access Gmail, you need to authenticate first:

1. Check authentication status:
```
auth_status = mcp.resources.get("auth://status")
```

2. If not authenticated, authenticate:
```
result = mcp.tools.authenticate()
```

3. The user will see a browser window to complete authentication.

4. After authentication, check status again:
```
auth_status = mcp.resources.get("auth://status")
```

5. Once authenticated, you can access Gmail data.
            """,
            "suggested_queries": [
                "Help me authenticate with Gmail",
                "I need to log in to my Gmail account",
                "How do I connect to Gmail?"
            ]
        }
    
    @mcp.prompt(
        name="access_gmail_data",
        description="Access and analyze Gmail data",
    )
    def access_gmail_data_prompt() -> Dict[str, Any]:
        """
        Prompt for accessing Gmail data.
        
        This prompt guides Claude through the process of accessing and analyzing Gmail data,
        explaining how to use the Gmail tools in the correct sequence.
        
        Returns:
            Dict[str, Any]: The prompt content.
        """
        return {
            "content": """
# Accessing Gmail Data

Once authenticated, you can access Gmail data:

1. Get email count:
```
email_count = mcp.tools.get_email_count()
```

2. List recent emails:
```
emails = mcp.tools.list_emails(max_results=5)
```

3. Get a specific email:
```
email = mcp.tools.get_email(email_id="...")
```

4. Search emails:
```
results = mcp.tools.search_emails(query="is:unread")
```

## Gmail Search Syntax

When searching, you can use Gmail's search syntax:
- `from:sender` - Emails from a specific sender
- `to:recipient` - Emails to a specific recipient
- `subject:text` - Emails with specific text in the subject
- `has:attachment` - Emails with attachments
- `is:unread` - Unread emails
            """,
            "suggested_queries": [
                "Show me my recent emails",
                "Search for emails from a specific person",
                "Find emails with attachments",
                "How many unread emails do I have?"
            ]
        } 