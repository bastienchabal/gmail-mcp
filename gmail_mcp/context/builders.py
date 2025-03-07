"""
Resource Builders Module

This module provides resource builders for the Gmail MCP server.
These builders create rich resources that Claude can use as context when processing requests.
Resources are exposed through the MCP protocol and can be accessed by the client application.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP, Context

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.auth.oauth import get_credentials
from gmail_mcp.gmail.processor import (
    parse_email_message,
    analyze_thread,
    get_sender_history,
    extract_email_metadata
)
from gmail_mcp.mcp.schemas import (
    EmailContextItem,
    ThreadContextItem,
    SenderContextItem
)

# Get logger
logger = get_logger(__name__)


def setup_resource_builders(mcp: FastMCP) -> None:
    """
    Set up resource builders on the FastMCP application.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    @mcp.resource("email://{email_id}")
    def build_email_context(email_id: str) -> Dict[str, Any]:
        """
        Build context for email-related requests.
        
        This resource extracts information about the specified email
        and provides it as context for Claude to use.
        
        Args:
            email_id (str): The ID of the email to get context for.
            
        Returns:
            Dict[str, Any]: The email context.
        """
        credentials = get_credentials()
        if not credentials:
            logger.error("Not authenticated")
            return {"error": "Not authenticated"}
        
        try:
            from googleapiclient.discovery import build
            
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the message
            message = service.users().messages().get(userId="me", id=email_id, format="full").execute()
            
            # Parse the message
            metadata, content = parse_email_message(message)
            
            # Create context item
            email_context = EmailContextItem(
                type="email",
                content={
                    "id": metadata.id,
                    "thread_id": metadata.thread_id,
                    "subject": metadata.subject,
                    "from": {
                        "email": metadata.from_email,
                        "name": metadata.from_name
                    },
                    "to": metadata.to,
                    "cc": metadata.cc,
                    "date": metadata.date.isoformat(),
                    "body": content.plain_text,
                    "has_attachments": metadata.has_attachments,
                    "labels": metadata.labels
                }
            )
            
            return email_context.dict()
        
        except Exception as e:
            logger.error(f"Failed to build email context: {e}")
            return {"error": f"Failed to build email context: {e}"}
    
    @mcp.resource("thread://{thread_id}")
    def build_thread_context(thread_id: str) -> Dict[str, Any]:
        """
        Build context for thread-related requests.
        
        This resource extracts information about the specified thread
        and provides it as context for Claude to use.
        
        Args:
            thread_id (str): The ID of the thread to get context for.
            
        Returns:
            Dict[str, Any]: The thread context.
        """
        # Analyze the thread
        thread = analyze_thread(thread_id)
        if not thread:
            return {"error": "Thread not found or could not be analyzed"}
        
        # Create context item
        thread_context = ThreadContextItem(
            type="thread",
            content={
                "id": thread.id,
                "subject": thread.subject,
                "message_count": thread.message_count,
                "participants": thread.participants,
                "last_message_date": thread.last_message_date.isoformat()
            }
        )
        
        return thread_context.dict()
    
    @mcp.resource("sender://{sender_email}")
    def build_sender_context(sender_email: str) -> Dict[str, Any]:
        """
        Build context for sender-related requests.
        
        This resource extracts information about the specified sender
        and provides it as context for Claude to use.
        
        Args:
            sender_email (str): The email address of the sender to get context for.
            
        Returns:
            Dict[str, Any]: The sender context.
        """
        # Get sender history
        sender = get_sender_history(sender_email)
        if not sender:
            return {"error": "Sender not found or could not be analyzed"}
        
        # Create context item
        sender_context = SenderContextItem(
            type="sender",
            content={
                "email": sender.email,
                "name": sender.name,
                "message_count": sender.message_count,
                "first_message_date": sender.first_message_date.isoformat() if sender.first_message_date else None,
                "last_message_date": sender.last_message_date.isoformat() if sender.last_message_date else None,
                "common_topics": sender.common_topics
            }
        )
        
        return sender_context.dict() 