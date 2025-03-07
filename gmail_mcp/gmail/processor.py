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
    ThreadInfo as Thread, 
    SenderInfo as Sender
)

# Get logger
logger = get_logger(__name__)


def parse_email_message(message: Dict[str, Any]) -> Tuple[EmailMetadata, EmailContent]:
    """
    Parse an email message from the Gmail API.
    
    Args:
        message (Dict[str, Any]): The Gmail API message object.
        
    Returns:
        Tuple[EmailMetadata, EmailContent]: The parsed email metadata and content.
    """
    # Extract headers
    headers = {}
    for header in message["payload"]["headers"]:
        headers[header["name"].lower()] = header["value"]
    
    # Extract basic metadata
    subject = headers.get("subject", "No Subject")
    
    # Parse from field
    from_field = headers.get("from", "")
    from_name, from_email = parseaddr(from_field)
    
    # Decode from_name if needed
    if from_name:
        try:
            decoded_parts = []
            for part, encoding in decode_header(from_name):
                if isinstance(part, bytes):
                    decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
                else:
                    decoded_parts.append(part)
            from_name = "".join(decoded_parts)
        except Exception as e:
            logger.warning(f"Failed to decode from_name: {e}")
    
    # Parse to field
    to_field = headers.get("to", "")
    to_list = []
    if to_field:
        for addr in to_field.split(","):
            _, email_addr = parseaddr(addr.strip())
            if email_addr:
                to_list.append(email_addr)
    
    # Parse cc field
    cc_field = headers.get("cc", "")
    cc_list = []
    if cc_field:
        for addr in cc_field.split(","):
            _, email_addr = parseaddr(addr.strip())
            if email_addr:
                cc_list.append(email_addr)
    
    # Parse date
    date_str = headers.get("date", "")
    date = datetime.now()  # Default to now if parsing fails
    if date_str:
        try:
            date = parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Failed to parse date: {e}")
    
    # Check for attachments
    has_attachments = False
    if "parts" in message["payload"]:
        for part in message["payload"]["parts"]:
            if part.get("filename"):
                has_attachments = True
                break
    
    # Create metadata object
    metadata = EmailMetadata(
        id=message["id"],
        thread_id=message["threadId"],
        subject=subject,
        from_email=from_email,
        from_name=from_name if from_name else "",
        to=to_list,
        cc=cc_list if cc_list else [],
        date=date,
        labels=message.get("labelIds", []),
        has_attachments=has_attachments
    )
    
    # Extract content
    content = extract_content(message["payload"])
    
    return metadata, content


def extract_content(payload: Dict[str, Any]) -> EmailContent:
    """
    Extract content from an email payload.
    
    Args:
        payload (Dict[str, Any]): The email payload.
        
    Returns:
        EmailContent: The extracted email content.
    """
    plain_text = ""
    html = None
    attachments = []
    
    def extract_body(part):
        """
        Extract body from a message part.
        
        Args:
            part (Dict[str, Any]): The message part.
            
        Returns:
            Tuple[str, str]: The plain text and HTML content.
        """
        nonlocal plain_text, html, attachments
        
        # Check if this part has a filename (attachment)
        if part.get("filename"):
            attachments.append({
                "filename": part["filename"],
                "mimeType": part["mimeType"],
                "size": len(part.get("body", {}).get("data", "")),
                "part_id": part.get("partId")
            })
            return
        
        # Check if this part has subparts
        if "parts" in part:
            for subpart in part["parts"]:
                extract_body(subpart)
            return
        
        # Extract body data
        body_data = part.get("body", {}).get("data", "")
        if not body_data:
            return
        
        # Decode body data
        try:
            decoded_data = base64.urlsafe_b64decode(body_data).decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to decode body data: {e}")
            return
        
        # Store based on mime type
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            plain_text = decoded_data
        elif mime_type == "text/html":
            html = decoded_data
            # If we have HTML but no plain text, extract text from HTML
            if not plain_text:
                plain_text = extract_text_from_html(decoded_data)
    
    # Start extraction
    extract_body(payload)
    
    # If we still don't have plain text but have a body, try to decode it
    if not plain_text and "body" in payload and "data" in payload["body"]:
        try:
            plain_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to decode body data: {e}")
    
    # Create content object
    content = EmailContent(
        plain_text=plain_text,
        html=html,
        attachments=attachments
    )
    
    return content


def extract_text_from_html(html_content: str) -> str:
    """
    Extract plain text from HTML content.
    
    Args:
        html_content (str): The HTML content.
        
    Returns:
        str: The extracted plain text.
    """
    # Simple regex-based extraction
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Replace HTML entities
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;', "'", text)
    
    return text.strip()


def analyze_thread(thread_id: str) -> Optional[Thread]:
    """
    Analyze a thread to extract information.
    
    Args:
        thread_id (str): The ID of the thread to analyze.
        
    Returns:
        Optional[Thread]: The thread information, or None if the thread could not be analyzed.
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
        
        # Extract basic information
        messages = thread.get("messages", [])
        
        if not messages:
            logger.warning(f"Thread {thread_id} has no messages")
            return None
        
        # Extract subject from the first message
        subject = "No Subject"
        for header in messages[0]["payload"]["headers"]:
            if header["name"].lower() == "subject":
                subject = header["value"]
                break
        
        # Extract participants
        participants = set()
        message_ids = []
        last_message_date = None
        
        for message in messages:
            message_ids.append(message["id"])
            
            # Extract headers
            headers = {}
            for header in message["payload"]["headers"]:
                headers[header["name"].lower()] = header["value"]
            
            # Extract participants from from, to, and cc fields
            for field in ["from", "to", "cc"]:
                if field in headers:
                    for addr in headers[field].split(","):
                        name, email_addr = parseaddr(addr.strip())
                        if email_addr:
                            participants.add(email_addr)
            
            # Extract date
            date_str = headers.get("date", "")
            if date_str:
                try:
                    date = parsedate_to_datetime(date_str)
                    if not last_message_date or date > last_message_date:
                        last_message_date = date
                except Exception as e:
                    logger.warning(f"Failed to parse date: {e}")
        
        # Create thread object
        thread_obj = Thread(
            id=thread_id,
            subject=subject,
            participants=[{"email": p} for p in participants],
            last_message_date=last_message_date or datetime.now(),
            message_count=len(messages)
        )
        
        return thread_obj
    
    except HttpError as error:
        logger.error(f"Failed to analyze thread: {error}")
        return None


def get_sender_history(sender_email: str) -> Optional[Sender]:
    """
    Get the history of a sender.
    
    Args:
        sender_email (str): The email address of the sender.
        
    Returns:
        Optional[Sender]: The sender information, or None if the sender could not be analyzed.
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
                name="",
                message_count=0
            )
        
        # Extract metadata from messages
        message_metadata = []
        sender_name = ""
        
        for message_info in messages:
            message = service.users().messages().get(userId="me", id=message_info["id"]).execute()
            metadata = extract_email_metadata(message)
            message_metadata.append(metadata)
            
            # Get sender name from the first message
            if not sender_name and metadata.from_name:
                sender_name = metadata.from_name
        
        # Sort by date
        message_metadata.sort(key=lambda x: x.date)
        
        # Get first and last message dates
        first_metadata = message_metadata[0]
        last_metadata = message_metadata[-1]
        
        # Extract common topics
        # This is a simple implementation that just counts words in subjects
        word_counts = {}
        for metadata in message_metadata:
            # Split subject into words
            words = re.findall(r'\b\w+\b', metadata.subject.lower())
            for word in words:
                # Skip common words
                if word in ["re", "fw", "fwd", "the", "and", "or", "to", "from", "for", "in", "on", "at", "with", "by"]:
                    continue
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top topics
        topics = []
        for word, count in sorted(word_counts.items(), key=lambda x: x[1], reverse=True):
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