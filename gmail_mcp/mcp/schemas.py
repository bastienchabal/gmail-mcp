"""
Gmail MCP Data Models

This module defines data models for the Gmail MCP server.
FastMCP handles the core MCP protocol schemas automatically.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class EmailMetadata(BaseModel):
    """Model for email metadata."""
    
    id: str
    thread_id: str
    subject: str
    from_email: str
    from_name: Optional[str] = None
    to: List[str]
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    date: datetime
    labels: List[str] = Field(default_factory=list)
    has_attachments: bool = False


class EmailContent(BaseModel):
    """Model for email content."""
    
    plain_text: str
    html: Optional[str] = None


class Thread(BaseModel):
    """Model for email thread."""
    
    id: str
    subject: str
    messages: List[str]
    participants: List[str]
    last_message_date: datetime
    message_count: int


class Sender(BaseModel):
    """Model for email sender."""
    
    email: str
    name: Optional[str] = None
    message_count: int = 0
    first_message_date: Optional[datetime] = None
    last_message_date: Optional[datetime] = None
    common_topics: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Model for search results."""
    
    query: str
    results: List[EmailMetadata] = Field(default_factory=list)
    total_results: int = 0
    next_page_token: Optional[str] = None


class ContextItem(BaseModel):
    """Base model for context items."""
    
    type: str
    content: Dict[str, Any]


class ActionDefinition(BaseModel):
    """Model for action definitions."""
    
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class MessageRequest(BaseModel):
    """Model for MCP message requests."""
    
    request_id: str
    content: str
    context: Optional[List[Dict[str, Any]]] = None


class MessageResponse(BaseModel):
    """Model for MCP message responses."""
    
    response_id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    context: List[ContextItem] = Field(default_factory=list)
    actions: List[ActionDefinition] = Field(default_factory=list)


class ActionRequest(BaseModel):
    """Model for MCP action requests."""
    
    request_id: str
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[List[Dict[str, Any]]] = None


class ActionResponse(BaseModel):
    """Model for MCP action responses."""
    
    response_id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    context: List[ContextItem] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """Model for MCP search requests."""
    
    request_id: str
    query: str
    filters: Optional[Dict[str, Any]] = None
    context: Optional[List[Dict[str, Any]]] = None


class SearchResponse(BaseModel):
    """Model for MCP search responses."""
    
    response_id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    context: List[ContextItem] = Field(default_factory=list)


class EmailContextItem(ContextItem):
    """Model for email context items."""
    
    type: str = "email"
    content: Dict[str, Any]


class ThreadContextItem(ContextItem):
    """Model for thread context items."""
    
    type: str = "thread"
    content: Dict[str, Any]


class SenderContextItem(ContextItem):
    """Model for sender context items."""
    
    type: str = "sender"
    content: Dict[str, Any]


class SearchResultContextItem(ContextItem):
    """Model for search result context items."""
    
    type: str = "search_result"
    content: Dict[str, Any] 