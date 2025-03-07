"""
Email Processing Module

This module provides tools for processing emails, including parsing, thread analysis,
sender history collection, and metadata extraction.
"""

import base64
import re
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.auth.oauth import get_credentials
from gmail_mcp.mcp.schemas import (
    EmailMetadata, 
    EmailContent, 
    Thread, 
    Sender
)

# Get logger
logger = get_logger(__name__)


def parse_email_message(message: Dict[str, Any]) -> Tuple[EmailMetadata, EmailContent]:
    """
    Parse a Gmail API message into structured email metadata and content.
    
    Args:
        message (Dict[str, Any]): The Gmail API message object.
        
    Returns:
        Tuple[EmailMetadata, EmailContent]: A tuple containing the email metadata and content.
    """
    # Extract headers
    headers = {}
    for header in message["payload"]["headers"]:
        headers[header["name"].lower()] = header["value"]
    
    # Parse from field
    from_email, from_name = parseaddr(headers.get("from", ""))
    
    # Parse to field
    to_list = []
    if "to" in headers:
        for addr in headers["to"].split(","):
            email_addr, _ = parseaddr(addr.strip())
            if email_addr:
                to_list.append(email_addr)
    
    # Parse cc field
    cc_list = []
    if "cc" in headers:
        for addr in headers["cc"].split(","):
            email_addr, _ = parseaddr(addr.strip())
            if email_addr:
                cc_list.append(email_addr)
    
    # Parse date
    date = None
    if "date" in headers:
        try:
            date = parsedate_to_datetime(headers["date"])
        except Exception as e:
            logger.warning(f"Failed to parse date: {e}")
            date = datetime.now()
    else:
        date = datetime.now()
    
    # Check for attachments
    has_attachments = False
    if "parts" in message["payload"]:
        for part in message["payload"]["parts"]:
            if part.get("filename") and part["filename"].strip():
                has_attachments = True
                break
    
    # Create metadata
    metadata = EmailMetadata(
        id=message["id"],
        thread_id=message["threadId"],
        subject=headers.get("subject", "No Subject"),
        from_email=from_email,
        from_name=from_name if from_name else None,
        to=to_list,
        cc=cc_list if cc_list else None,
        bcc=None,  # Gmail API doesn't provide BCC information
        date=date,
        labels=message.get("labelIds", []),
        has_attachments=has_attachments
    )
    
    # Extract content
    plain_text = ""
    html = None
    
    def extract_body(part):
        """Extract body from message part."""
        if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
            return base64.urlsafe_b64decode(part["body"]["data"].encode("ASCII")).decode("utf-8")
        elif part.get("mimeType") == "text/html" and "data" in part.get("body", {}):
            return base64.urlsafe_b64decode(part["body"]["data"].encode("ASCII")).decode("utf-8")
        return None
    
    if "parts" in message["payload"]:
        for part in message["payload"]["parts"]:
            if part.get("mimeType") == "text/plain":
                plain_text = extract_body(part) or ""
            elif part.get("mimeType") == "text/html":
                html = extract_body(part)
            
            # Handle nested multipart messages
            if part.get("mimeType", "").startswith("multipart/") and "parts" in part:
                for subpart in part["parts"]:
                    if subpart.get("mimeType") == "text/plain" and not plain_text:
                        plain_text = extract_body(subpart) or ""
                    elif subpart.get("mimeType") == "text/html" and not html:
                        html = extract_body(subpart)
    elif "body" in message["payload"] and "data" in message["payload"]["body"]:
        body_data = message["payload"]["body"]["data"]
        decoded_data = base64.urlsafe_b64decode(body_data.encode("ASCII")).decode("utf-8")
        
        if message["payload"].get("mimeType") == "text/plain":
            plain_text = decoded_data
        elif message["payload"].get("mimeType") == "text/html":
            html = decoded_data
            # Extract plain text from HTML if no plain text part
            plain_text = extract_text_from_html(decoded_data)
    
    # Create content
    content = EmailContent(
        plain_text=plain_text,
        html=html
    )
    
    return metadata, content


def extract_text_from_html(html_content: str) -> str:
    """
    Extract plain text from HTML content by removing HTML tags.
    
    Args:
        html_content (str): The HTML content.
        
    Returns:
        str: The extracted plain text.
    """
    # Simple regex to remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Replace HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', "'")
    
    return text.strip()


def analyze_thread(thread_id: str) -> Optional[Thread]:
    """
    Analyze an email thread to extract thread information.
    
    Args:
        thread_id (str): The ID of the thread to analyze.
        
    Returns:
        Optional[Thread]: The thread information, or None if an error occurred.
    """
    credentials = get_credentials()
    
    if not credentials:
        logger.error("Not authenticated")
        return None
    
    try:
        # Build the Gmail API service
        service = build("gmail", "v1", credentials=credentials)
        
        # Get the thread
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        
        # Extract messages
        messages = thread.get("messages", [])
        message_ids = [msg["id"] for msg in messages]
        
        # Extract participants
        participants = set()
        for message in messages:
            metadata, _ = parse_email_message(message)
            participants.add(metadata.from_email)
            participants.update(metadata.to or [])
            if metadata.cc:
                participants.update(metadata.cc)
        
        # Get subject from the first message
        subject = ""
        if messages:
            for header in messages[0]["payload"]["headers"]:
                if header["name"].lower() == "subject":
                    subject = header["value"]
                    break
        
        # Get last message date
        last_message_date = datetime.now()
        if messages:
            last_message = messages[-1]
            for header in last_message["payload"]["headers"]:
                if header["name"].lower() == "date":
                    try:
                        last_message_date = parsedate_to_datetime(header["value"])
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {e}")
                    break
        
        # Create thread object
        thread_obj = Thread(
            id=thread_id,
            subject=subject,
            messages=message_ids,
            participants=list(participants),
            last_message_date=last_message_date,
            message_count=len(messages)
        )
        
        return thread_obj
    
    except HttpError as error:
        logger.error(f"Failed to analyze thread: {error}")
        return None


def get_sender_history(sender_email: str) -> Optional[Sender]:
    """
    Get the history of emails from a specific sender.
    
    Args:
        sender_email (str): The email address of the sender.
        
    Returns:
        Optional[Sender]: The sender information, or None if an error occurred.
    """
    credentials = get_credentials()
    
    if not credentials:
        logger.error("Not authenticated")
        return None
    
    try:
        # Build the Gmail API service
        service = build("gmail", "v1", credentials=credentials)
        
        # Search for messages from the sender
        query = f"from:{sender_email}"
        result = service.users().messages().list(userId="me", q=query, maxResults=100).execute()
        
        messages = result.get("messages", [])
        
        if not messages:
            # No messages found
            return Sender(
                email=sender_email,
                message_count=0
            )
        
        # Get the first and last message dates
        first_message = service.users().messages().get(userId="me", id=messages[-1]["id"]).execute()
        last_message = service.users().messages().get(userId="me", id=messages[0]["id"]).execute()
        
        first_metadata, _ = parse_email_message(first_message)
        last_metadata, _ = parse_email_message(last_message)
        
        # Extract sender name from the last message
        sender_name = last_metadata.from_name
        
        # Analyze common topics
        topics = []
        subject_words = {}
        
        # Process up to 20 messages to find common topics
        for i, message_info in enumerate(messages[:20]):
            message = service.users().messages().get(userId="me", id=message_info["id"]).execute()
            metadata, _ = parse_email_message(message)
            
            # Extract words from subject
            if metadata.subject:
                words = re.findall(r'\b\w+\b', metadata.subject.lower())
                for word in words:
                    if len(word) > 3:  # Ignore short words
                        subject_words[word] = subject_words.get(word, 0) + 1
        
        # Find common topics (words that appear in multiple subjects)
        for word, count in sorted(subject_words.items(), key=lambda x: x[1], reverse=True):
            if count >= 2 and len(topics) < 5:  # At least 2 occurrences, max 5 topics
                topics.append(word)
        
        # Create sender object
        sender = Sender(
            email=sender_email,
            name=sender_name,
            message_count=len(messages),
            first_message_date=first_metadata.date,
            last_message_date=last_metadata.date,
            common_topics=topics
        )
        
        return sender
    
    except HttpError as error:
        logger.error(f"Failed to get sender history: {error}")
        return None


def extract_email_metadata(message: Dict[str, Any]) -> EmailMetadata:
    """
    Extract metadata from an email message.
    
    Args:
        message (Dict[str, Any]): The Gmail API message object.
        
    Returns:
        EmailMetadata: The extracted email metadata.
    """
    metadata, _ = parse_email_message(message)
    return metadata 