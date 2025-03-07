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
        
        This tool retrieves the total number of messages in the user's Gmail account
        and the number of messages in the inbox.
        
        Prerequisites:
        - The user must be authenticated. Check auth://status resource first.
        - If not authenticated, guide the user through the authentication process.
        
        Returns:
            Dict[str, Any]: The email count information including:
                - email: The user's email address
                - total_messages: Total number of messages in the account
                - inbox_messages: Number of messages in the inbox
                - next_page_token: Token for pagination (if applicable)
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. If authenticated, call get_email_count()
        3. If not authenticated, guide user to authenticate first
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
        
        This tool retrieves a list of emails from the specified label in the user's
        Gmail account, with basic information about each email.
        
        Prerequisites:
        - The user must be authenticated. Check auth://status resource first.
        - If not authenticated, guide the user through the authentication process.
        
        Args:
            max_results (int, optional): Maximum number of emails to return. Defaults to 10.
            label (str, optional): The label to filter by. Defaults to "INBOX".
                Common labels: "INBOX", "SENT", "DRAFT", "TRASH", "SPAM", "STARRED"
            
        Returns:
            Dict[str, Any]: The list of emails including:
                - emails: List of email objects with basic information
                - next_page_token: Token for pagination (if applicable)
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. If authenticated, call list_emails(max_results=5, label="INBOX")
        3. If not authenticated, guide user to authenticate first
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
        
        This tool retrieves the full details of a specific email, including
        the body content, headers, and other metadata.
        
        Prerequisites:
        - The user must be authenticated. Check auth://status resource first.
        - You need an email ID, which can be obtained from list_emails() or search_emails()
        
        Args:
            email_id (str): The ID of the email to retrieve. This ID comes from the
                            list_emails() or search_emails() results.
            
        Returns:
            Dict[str, Any]: The email details including:
                - id: Email ID
                - thread_id: Thread ID
                - subject: Email subject
                - from: Sender information
                - to: Recipient information
                - cc: CC recipients
                - date: Email date
                - body: Email body content
                - snippet: Short snippet of the email
                - labels: Email labels
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. Get a list of emails: list_emails()
        3. Extract an email ID from the results
        4. Get the full email: get_email(email_id="...")
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
        
        This tool searches for emails matching the specified query using
        Gmail's powerful search syntax.
        
        Prerequisites:
        - The user must be authenticated. Check auth://status resource first.
        - If not authenticated, guide the user through the authentication process.
        
        Args:
            query (str): The search query using Gmail's search syntax.
                Examples:
                - "from:example@gmail.com" - Emails from a specific sender
                - "to:example@gmail.com" - Emails to a specific recipient
                - "subject:meeting" - Emails with "meeting" in the subject
                - "has:attachment" - Emails with attachments
                - "is:unread" - Unread emails
                - "after:2023/01/01" - Emails after January 1, 2023
            max_results (int, optional): Maximum number of emails to return. Defaults to 10.
            
        Returns:
            Dict[str, Any]: The search results including:
                - query: The search query used
                - emails: List of email objects matching the query
                - next_page_token: Token for pagination (if applicable)
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. If authenticated, search for emails: search_emails(query="from:example@gmail.com")
        3. If not authenticated, guide user to authenticate first
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
    
    @mcp.resource("gmail://status")
    def gmail_status() -> Dict[str, Any]:
        """
        Get the current status of the Gmail account.
        
        This resource provides information about the user's Gmail account,
        including authentication status, email address, and account statistics.
        
        Returns:
            Dict[str, Any]: The Gmail account status.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {
                "authenticated": False,
                "message": "Not authenticated. Use the authenticate tool to start the authentication process.",
                "next_steps": [
                    "Check auth://status for authentication details",
                    "Call authenticate() to start the authentication process"
                ]
            }
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the profile information
            profile = service.users().getProfile(userId="me").execute()
            
            # Get labels to calculate counts
            labels = service.users().labels().list(userId="me").execute()
            
            # Extract label information
            label_info = {}
            for label in labels.get("labels", []):
                try:
                    label_details = service.users().labels().get(userId="me", id=label["id"]).execute()
                    label_info[label["name"]] = {
                        "total": label_details.get("messagesTotal", 0),
                        "unread": label_details.get("messagesUnread", 0)
                    }
                except Exception as e:
                    logger.error(f"Failed to get label details for {label['name']}: {e}")
            
            # Get the authentication status
            import httpx
            response = httpx.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {credentials.token}"},
            )
            user_info = response.json()
            
            return {
                "authenticated": True,
                "email": profile.get("emailAddress", user_info.get("email", "Unknown")),
                "name": user_info.get("name", "Unknown"),
                "picture": user_info.get("picture"),
                "account_stats": {
                    "total_messages": profile.get("messagesTotal", 0),
                    "total_threads": profile.get("threadsTotal", 0),
                    "storage_used": profile.get("storageUsed", 0),
                    "storage_used_percent": round(int(profile.get("storageUsed", 0)) / (15 * 1024 * 1024 * 1024) * 100, 2)  # Assuming 15GB limit
                },
                "labels": label_info,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "message": "Gmail account is accessible.",
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to get Gmail status: {e}")
            return {
                "authenticated": True,
                "error": f"Failed to get Gmail status: {e}",
                "message": "Authentication is valid, but failed to get Gmail account information.",
                "next_steps": [
                    "Try again later",
                    "Check if the Gmail API is enabled in the Google Cloud Console",
                    "Check if the user has granted the necessary permissions"
                ],
                "status": "error"
            }
    
    @mcp.tool()
    def get_email_overview() -> Dict[str, Any]:
        """
        Get a simple overview of the user's emails.
        
        This tool provides a quick summary of the user's Gmail account,
        including counts and recent emails, all in one call.
        
        Returns:
            Dict[str, Any]: The email overview.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the profile information
            profile = service.users().getProfile(userId="me").execute()
            
            # Get the inbox messages
            inbox_result = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=5).execute()
            
            # Get unread messages
            unread_result = service.users().messages().list(userId="me", labelIds=["UNREAD"], maxResults=5).execute()
            
            # Get labels
            labels_result = service.users().labels().list(userId="me").execute()
            
            # Process recent emails
            recent_emails = []
            if "messages" in inbox_result:
                for message in inbox_result["messages"][:5]:  # Limit to 5 emails
                    msg = service.users().messages().get(userId="me", id=message["id"]).execute()
                    
                    # Extract headers
                    headers = {}
                    for header in msg["payload"]["headers"]:
                        headers[header["name"].lower()] = header["value"]
                    
                    # Add to emails list
                    recent_emails.append({
                        "id": msg["id"],
                        "subject": headers.get("subject", "No Subject"),
                        "from": headers.get("from", "Unknown"),
                        "date": headers.get("date", "Unknown"),
                        "snippet": msg["snippet"],
                    })
            
            # Count emails by label
            label_counts = {}
            for label in labels_result.get("labels", []):
                if label["type"] == "system":
                    label_detail = service.users().labels().get(userId="me", id=label["id"]).execute()
                    label_counts[label["name"]] = {
                        "total": label_detail.get("messagesTotal", 0),
                        "unread": label_detail.get("messagesUnread", 0)
                    }
            
            return {
                "account": {
                    "email": profile.get("emailAddress", "Unknown"),
                    "total_messages": profile.get("messagesTotal", 0),
                    "total_threads": profile.get("threadsTotal", 0),
                },
                "counts": {
                    "inbox": label_counts.get("INBOX", {}).get("total", 0),
                    "unread": label_counts.get("UNREAD", {}).get("total", 0),
                    "sent": label_counts.get("SENT", {}).get("total", 0),
                    "draft": label_counts.get("DRAFT", {}).get("total", 0),
                    "spam": label_counts.get("SPAM", {}).get("total", 0),
                    "trash": label_counts.get("TRASH", {}).get("total", 0),
                },
                "recent_emails": recent_emails,
                "unread_count": len(unread_result.get("messages", [])),
            }
        except Exception as e:
            logger.error(f"Failed to get email overview: {e}")
            return {"error": f"Failed to get email overview: {e}"} 