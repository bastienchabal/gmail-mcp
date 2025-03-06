"""
MCP Schemas Module

This module defines the Pydantic models for MCP requests and responses.
"""

from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


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


# Email-specific context item models
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