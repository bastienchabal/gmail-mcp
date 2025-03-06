"""
Gmail Client Module

This module provides tools for interacting with the Gmail API.
"""

import logging
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP, Context
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.utils.config import get_config
from gmail_mcp.auth.oauth import get_credentials

# Get logger
logger = get_logger(__name__)


def setup_gmail_tools(mcp: FastMCP) -> None:
    """
    Set up Gmail tools on the FastMCP application.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    @mcp.tool()
    def get_email_count() -> Dict[str, Any]:
        """
        Get the count of emails in the user's inbox.
        
        Returns:
            Dict[str, Any]: The email count information.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the login tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the profile information
            profile = service.users().getProfile(userId="me").execute()
            
            # Get the inbox messages
            result = service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
            
            return {
                "email": profile.get("emailAddress", "Unknown"),
                "total_messages": profile.get("messagesTotal", 0),
                "inbox_messages": len(result.get("messages", [])),
                "next_page_token": result.get("nextPageToken"),
            }
        except HttpError as error:
            logger.error(f"Failed to get email count: {error}")
            return {"error": f"Failed to get email count: {error}"}
    
    @mcp.tool()
    def list_emails(max_results: int = 10, label: str = "INBOX") -> Dict[str, Any]:
        """
        List emails from the user's mailbox.
        
        Args:
            max_results (int, optional): Maximum number of emails to return. Defaults to 10.
            label (str, optional): The label to filter by. Defaults to "INBOX".
            
        Returns:
            Dict[str, Any]: The list of emails.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the login tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the messages
            result = service.users().messages().list(
                userId="me", 
                labelIds=[label], 
                maxResults=max_results
            ).execute()
            
            messages = result.get("messages", [])
            emails = []
            
            for message in messages:
                msg = service.users().messages().get(userId="me", id=message["id"]).execute()
                
                # Extract headers
                headers = {}
                for header in msg["payload"]["headers"]:
                    headers[header["name"].lower()] = header["value"]
                
                # Add to emails list
                emails.append({
                    "id": msg["id"],
                    "thread_id": msg["threadId"],
                    "subject": headers.get("subject", "No Subject"),
                    "from": headers.get("from", "Unknown"),
                    "to": headers.get("to", "Unknown"),
                    "date": headers.get("date", "Unknown"),
                    "snippet": msg["snippet"],
                })
            
            return {
                "emails": emails,
                "next_page_token": result.get("nextPageToken"),
            }
        except HttpError as error:
            logger.error(f"Failed to list emails: {error}")
            return {"error": f"Failed to list emails: {error}"}
    
    @mcp.tool()
    def get_email(email_id: str) -> Dict[str, Any]:
        """
        Get a specific email by ID.
        
        Args:
            email_id (str): The ID of the email to retrieve.
            
        Returns:
            Dict[str, Any]: The email details.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the login tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the message
            msg = service.users().messages().get(userId="me", id=email_id, format="full").execute()
            
            # Extract headers
            headers = {}
            for header in msg["payload"]["headers"]:
                headers[header["name"].lower()] = header["value"]
            
            # Extract body
            body = ""
            if "parts" in msg["payload"]:
                for part in msg["payload"]["parts"]:
                    if part["mimeType"] == "text/plain":
                        body = part["body"]["data"]
                        break
            elif "body" in msg["payload"] and "data" in msg["payload"]["body"]:
                body = msg["payload"]["body"]["data"]
            
            # Decode body if needed (base64url encoded)
            import base64
            if body:
                body = base64.urlsafe_b64decode(body.encode("ASCII")).decode("utf-8")
            
            return {
                "id": msg["id"],
                "thread_id": msg["threadId"],
                "subject": headers.get("subject", "No Subject"),
                "from": headers.get("from", "Unknown"),
                "to": headers.get("to", "Unknown"),
                "cc": headers.get("cc", ""),
                "date": headers.get("date", "Unknown"),
                "body": body,
                "snippet": msg["snippet"],
                "labels": msg["labelIds"],
            }
        except HttpError as error:
            logger.error(f"Failed to get email: {error}")
            return {"error": f"Failed to get email: {error}"}
    
    @mcp.tool()
    def search_emails(query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search for emails using Gmail's search syntax.
        
        Args:
            query (str): The search query using Gmail's search syntax.
            max_results (int, optional): Maximum number of emails to return. Defaults to 10.
            
        Returns:
            Dict[str, Any]: The search results.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the login tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Search for messages
            result = service.users().messages().list(
                userId="me", 
                q=query, 
                maxResults=max_results
            ).execute()
            
            messages = result.get("messages", [])
            emails = []
            
            for message in messages:
                msg = service.users().messages().get(userId="me", id=message["id"]).execute()
                
                # Extract headers
                headers = {}
                for header in msg["payload"]["headers"]:
                    headers[header["name"].lower()] = header["value"]
                
                # Add to emails list
                emails.append({
                    "id": msg["id"],
                    "thread_id": msg["threadId"],
                    "subject": headers.get("subject", "No Subject"),
                    "from": headers.get("from", "Unknown"),
                    "to": headers.get("to", "Unknown"),
                    "date": headers.get("date", "Unknown"),
                    "snippet": msg["snippet"],
                })
            
            return {
                "query": query,
                "emails": emails,
                "next_page_token": result.get("nextPageToken"),
            }
        except HttpError as error:
            logger.error(f"Failed to search emails: {error}")
            return {"error": f"Failed to search emails: {error}"} 