"""
Context Builders Module

This module provides context builders for the Gmail MCP server.
These builders create rich context objects for Claude to use when processing requests.
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


def setup_context_builders(mcp: FastMCP) -> None:
    """
    Set up context builders on the FastMCP application.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    @mcp.context_builder()
    def build_email_context(context: Context) -> List[Dict[str, Any]]:
        """
        Build context for email-related requests.
        
        This context builder extracts information about the current email being viewed
        and adds it to the context for Claude to use.
        
        Args:
            context (Context): The current context.
            
        Returns:
            List[Dict[str, Any]]: The context items to add.
        """
        # Check if we have an email ID in the context
        email_id = context.get("email_id")
        if not email_id:
            return []
        
        credentials = get_credentials()
        if not credentials:
            logger.error("Not authenticated")
            return []
        
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
            
            return [email_context.dict()]
        
        except Exception as e:
            logger.error(f"Failed to build email context: {e}")
            return []
    
    @mcp.context_builder()
    def build_thread_context(context: Context) -> List[Dict[str, Any]]:
        """
        Build context for thread-related requests.
        
        This context builder extracts information about the current thread being viewed
        and adds it to the context for Claude to use.
        
        Args:
            context (Context): The current context.
            
        Returns:
            List[Dict[str, Any]]: The context items to add.
        """
        # Check if we have a thread ID in the context
        thread_id = context.get("thread_id")
        if not thread_id:
            # Try to get thread ID from email ID
            email_id = context.get("email_id")
            if not email_id:
                return []
            
            credentials = get_credentials()
            if not credentials:
                logger.error("Not authenticated")
                return []
            
            try:
                from googleapiclient.discovery import build
                
                # Build the Gmail API service
                service = build("gmail", "v1", credentials=credentials)
                
                # Get the message to extract thread ID
                message = service.users().messages().get(userId="me", id=email_id, fields="threadId").execute()
                thread_id = message.get("threadId")
                
                if not thread_id:
                    return []
            
            except Exception as e:
                logger.error(f"Failed to get thread ID from email: {e}")
                return []
        
        # Analyze the thread
        thread = analyze_thread(thread_id)
        if not thread:
            return []
        
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
        
        return [thread_context.dict()]
    
    @mcp.context_builder()
    def build_sender_context(context: Context) -> List[Dict[str, Any]]:
        """
        Build context for sender-related requests.
        
        This context builder extracts information about the sender of the current email
        and adds it to the context for Claude to use.
        
        Args:
            context (Context): The current context.
            
        Returns:
            List[Dict[str, Any]]: The context items to add.
        """
        # Check if we have an email ID in the context
        email_id = context.get("email_id")
        if not email_id:
            return []
        
        credentials = get_credentials()
        if not credentials:
            logger.error("Not authenticated")
            return []
        
        try:
            from googleapiclient.discovery import build
            
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the message
            message = service.users().messages().get(userId="me", id=email_id, fields="payload").execute()
            
            # Extract sender email
            sender_email = None
            for header in message["payload"]["headers"]:
                if header["name"].lower() == "from":
                    # Extract email from "Name <email>" format
                    from_value = header["value"]
                    import re
                    email_match = re.search(r'<([^>]+)>', from_value)
                    if email_match:
                        sender_email = email_match.group(1)
                    else:
                        sender_email = from_value
                    break
            
            if not sender_email:
                return []
            
            # Get sender history
            sender = get_sender_history(sender_email)
            if not sender:
                return []
            
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
            
            return [sender_context.dict()]
        
        except Exception as e:
            logger.error(f"Failed to build sender context: {e}")
            return [] 