"""
MCP Schemas Module

This module defines the schemas used by the MCP resources.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EmailContextItem(BaseModel):
    """
    Schema for email context items.
    
    This schema defines the structure of email context items that are
    returned by the email resource.
    """
    type: str = "email"
    content: Dict[str, Any]


class ThreadContextItem(BaseModel):
    """
    Schema for thread context items.
    
    This schema defines the structure of thread context items that are
    returned by the thread resource.
    """
    type: str = "thread"
    content: Dict[str, Any]


class SenderContextItem(BaseModel):
    """
    Schema for sender context items.
    
    This schema defines the structure of sender context items that are
    returned by the sender resource.
    """
    type: str = "sender"
    content: Dict[str, Any]


class EmailMetadata(BaseModel):
    """
    Schema for email metadata.
    
    This schema defines the structure of email metadata that is
    extracted from Gmail API responses.
    """
    id: str
    thread_id: str
    subject: str
    from_email: str
    from_name: str
    to: List[str]
    cc: List[str] = []
    date: datetime
    has_attachments: bool
    labels: List[str]


class EmailContent(BaseModel):
    """
    Schema for email content.
    
    This schema defines the structure of email content that is
    extracted from Gmail API responses.
    """
    plain_text: str
    html: Optional[str] = None
    attachments: List[Dict[str, Any]] = []


class ThreadInfo(BaseModel):
    """
    Schema for thread information.
    
    This schema defines the structure of thread information that is
    extracted from Gmail API responses.
    """
    id: str
    subject: str
    message_count: int
    participants: List[Dict[str, str]]
    last_message_date: datetime


class SenderInfo(BaseModel):
    """
    Schema for sender information.
    
    This schema defines the structure of sender information that is
    extracted from Gmail API responses.
    """
    email: str
    name: str
    message_count: int
    first_message_date: Optional[datetime] = None
    last_message_date: Optional[datetime] = None
    common_topics: List[str] = [] 