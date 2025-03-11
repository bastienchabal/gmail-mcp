"""
MCP Tools Module

This module defines all the tools available in the Gmail MCP server.
Tools are functions that Claude can call to perform actions.
"""

import os
import json
import logging
import base64
from typing import Dict, Any, List, Optional, Union
import httpx

from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request as GoogleRequest

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.utils.config import get_config
from gmail_mcp.auth.token_manager import TokenManager
from gmail_mcp.auth.oauth import get_credentials, login, process_auth_code, start_oauth_process
from gmail_mcp.gmail.processor import (
    parse_email_message,
    analyze_thread,
    get_sender_history,
    extract_entities,
    analyze_communication_patterns,
    find_related_emails
)

# Get logger
logger = get_logger(__name__)

# Get token manager
token_manager = TokenManager()


def setup_tools(mcp: FastMCP) -> None:
    """
    Set up all MCP tools on the FastMCP application.
    
    Args:
        mcp (FastMCP): The FastMCP application.
    """
    # Authentication tools
    @mcp.tool()
    def login_tool() -> str:
        """
        Initiate the OAuth2 flow by providing a link to the Google authorization page.
        
        Returns:
            str: The authorization URL to redirect to.
        """
        return login()
    
    @mcp.tool()
    def authenticate() -> str:
        """
        Start the complete OAuth authentication process.
        
        This tool opens a browser window and starts a local server to handle the callback.
        
        Returns:
            str: A message indicating that the authentication process has started.
        """
        # Start the OAuth process in a separate thread
        import threading
        thread = threading.Thread(target=start_oauth_process)
        thread.daemon = True
        thread.start()
        
        return "Authentication process started. Please check your browser to complete the process."
    
    @mcp.tool()
    def process_auth_code_tool(code: str, state: str) -> str:
        """
        Process the OAuth2 authorization code and state.
        
        Args:
            code (str): The authorization code from Google.
            state (str): The state parameter from Google.
            
        Returns:
            str: A success or error message.
        """
        return process_auth_code(code, state)
    
    @mcp.tool()
    def logout() -> str:
        """
        Log out by revoking the access token and clearing the stored credentials.
        
        Returns:
            str: A success or error message.
        """
        # Get the credentials
        credentials = token_manager.get_token()
        
        if credentials:
            try:
                # Revoke the access token
                httpx.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": credentials.token},
                    headers={"content-type": "application/x-www-form-urlencoded"},
                )
                
                # Clear the stored credentials
                token_manager.clear_token()
                
                return "Logged out successfully."
            except Exception as e:
                logger.error(f"Failed to revoke token: {e}")
                return f"Error: Failed to revoke token: {e}"
        else:
            return "No active session to log out from."
    
    @mcp.tool()
    def check_auth_status() -> Dict[str, Any]:
        """
        Check the current authentication status.
        
        This tool provides a direct way to check if the user is authenticated
        without having to access the auth://status resource.
        
        Returns:
            Dict[str, Any]: The authentication status.
        """
        # Get the credentials
        credentials = token_manager.get_token()
        
        if not credentials:
            return {
                "authenticated": False,
                "message": "Not authenticated. Use the authenticate tool to start the authentication process.",
                "next_steps": [
                    "Call authenticate() to start the authentication process"
                ]
            }
        
        # Check if the credentials are expired
        if credentials.expired:
            try:
                # Try to refresh the token
                credentials.refresh(GoogleRequest())
                token_manager.store_token(credentials)
                
                return {
                    "authenticated": True,
                    "message": "Authentication is valid. Token was refreshed.",
                    "status": "refreshed"
                }
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                return {
                    "authenticated": False,
                    "message": f"Authentication expired and could not be refreshed: {e}",
                    "next_steps": [
                        "Call authenticate() to start a new authentication process"
                    ],
                    "status": "expired"
                }
        
        return {
            "authenticated": True,
            "message": "Authentication is valid.",
            "status": "valid"
        }
    
    # Gmail tools
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
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
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
                - emails: List of email objects with basic information and links
                - next_page_token: Token for pagination (if applicable)
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. If authenticated, call list_emails(max_results=5, label="INBOX")
        3. If not authenticated, guide user to authenticate first
        4. Always include the email_link when discussing specific emails with the user
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
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
                
                # Generate a link to the email in Gmail web interface
                email_id = msg["id"]
                thread_id = msg["threadId"]
                email_link = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}/{email_id}"
                
                # Add to emails list
                emails.append({
                    "id": email_id,
                    "thread_id": thread_id,
                    "subject": headers.get("subject", "No Subject"),
                    "from": headers.get("from", "Unknown"),
                    "to": headers.get("to", "Unknown"),
                    "date": headers.get("date", "Unknown"),
                    "snippet": msg["snippet"],
                    "email_link": email_link
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
                - email_link: Direct link to the email in Gmail web interface
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. Get a list of emails: list_emails()
        3. Extract an email ID from the results
        4. Get the full email: get_email(email_id="...")
        5. Always include the email_link when discussing the email with the user
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
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
            if body:
                body = base64.urlsafe_b64decode(body.encode("ASCII")).decode("utf-8")
            
            # Generate a link to the email in Gmail web interface
            thread_id = msg["threadId"]
            email_link = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}/{email_id}"
            
            return {
                "id": msg["id"],
                "thread_id": thread_id,
                "subject": headers.get("subject", "No Subject"),
                "from": headers.get("from", "Unknown"),
                "to": headers.get("to", "Unknown"),
                "cc": headers.get("cc", ""),
                "date": headers.get("date", "Unknown"),
                "body": body,
                "snippet": msg["snippet"],
                "labels": msg["labelIds"],
                "email_link": email_link
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
                - emails: List of email objects matching the query with links
                - next_page_token: Token for pagination (if applicable)
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. If authenticated, search for emails: search_emails(query="from:example@gmail.com")
        3. If not authenticated, guide user to authenticate first
        4. Always include the email_link when discussing specific emails with the user
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
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
                
                # Generate a link to the email in Gmail web interface
                email_id = msg["id"]
                thread_id = msg["threadId"]
                email_link = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}/{email_id}"
                
                # Add to emails list
                emails.append({
                    "id": email_id,
                    "thread_id": thread_id,
                    "subject": headers.get("subject", "No Subject"),
                    "from": headers.get("from", "Unknown"),
                    "to": headers.get("to", "Unknown"),
                    "date": headers.get("date", "Unknown"),
                    "snippet": msg["snippet"],
                    "email_link": email_link
                })
            
            return {
                "query": query,
                "emails": emails,
                "next_page_token": result.get("nextPageToken"),
            }
        except HttpError as error:
            logger.error(f"Failed to search emails: {error}")
            return {"error": f"Failed to search emails: {error}"}
    
    @mcp.tool()
    def get_email_overview() -> Dict[str, Any]:
        """
        Get a simple overview of the user's emails.
        
        This tool provides a quick summary of the user's Gmail account,
        including counts and recent emails, all in one call.
        
        Returns:
            Dict[str, Any]: The email overview including:
                - account: Account information
                - counts: Email counts by label
                - recent_emails: List of recent emails with links
                - unread_count: Number of unread emails
                
        Note: Always include the email_link when discussing specific emails with the user.
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
                    
                    # Generate a link to the email in Gmail web interface
                    email_id = msg["id"]
                    thread_id = msg["threadId"]
                    email_link = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}/{email_id}"
                    
                    # Add to emails list
                    recent_emails.append({
                        "id": email_id,
                        "thread_id": thread_id,
                        "subject": headers.get("subject", "No Subject"),
                        "from": headers.get("from", "Unknown"),
                        "date": headers.get("date", "Unknown"),
                        "snippet": msg["snippet"],
                        "email_link": email_link
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
    
    @mcp.tool()
    def prepare_email_reply(email_id: str) -> Dict[str, Any]:
        """
        Prepare a context-rich reply to an email.
        
        This tool gathers comprehensive context for replying to an email,
        including the original email, thread history, sender information,
        communication patterns, and related emails.
        
        Prerequisites:
        - The user must be authenticated. Check auth://status resource first.
        - You need an email ID, which can be obtained from list_emails() or search_emails()
        
        Args:
            email_id (str): The ID of the email to reply to.
            
        Returns:
            Dict[str, Any]: Comprehensive context for generating a reply, including:
                - original_email: The email being replied to
                - thread_context: Information about the thread
                - sender_context: Information about the sender
                - communication_patterns: Analysis of communication patterns
                - entities: Entities extracted from the email
                - related_emails: Related emails for context
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. Get a list of emails: list_emails()
        3. Extract an email ID from the results
        4. Prepare a reply: prepare_email_reply(email_id="...")
        5. Use the returned context to craft a personalized reply
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the original email
            message = service.users().messages().get(userId="me", id=email_id, format="full").execute()
            metadata, content = parse_email_message(message)
            
            # Get the user's email
            profile = service.users().getProfile(userId="me").execute()
            user_email = profile.get("emailAddress", "")
            
            # Extract entities from the email content
            entities = extract_entities(content.plain_text)
            
            # Get thread context
            thread_context = None
            if metadata.thread_id:
                thread = analyze_thread(metadata.thread_id)
                if thread:
                    thread_context = {
                        "id": thread.id,
                        "subject": thread.subject,
                        "message_count": thread.message_count,
                        "participants": thread.participants,
                        "last_message_date": thread.last_message_date.isoformat()
                    }
            
            # Get sender context
            sender_context = None
            if metadata.from_email:
                sender = get_sender_history(metadata.from_email)
                if sender:
                    sender_context = {
                        "email": sender.email,
                        "name": sender.name,
                        "message_count": sender.message_count,
                        "first_message_date": sender.first_message_date.isoformat() if sender.first_message_date else None,
                        "last_message_date": sender.last_message_date.isoformat() if sender.last_message_date else None,
                        "common_topics": sender.common_topics
                    }
            
            # Analyze communication patterns
            communication_patterns = None
            if metadata.from_email:
                patterns = analyze_communication_patterns(metadata.from_email, user_email)
                if patterns and "error" not in patterns:
                    communication_patterns = patterns
            
            # Find related emails
            related_emails = find_related_emails(email_id, max_results=5)
            
            # Create original email object
            original_email = {
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
            
            # Create reply context
            reply_context = {
                "original_email": original_email,
                "thread_context": thread_context,
                "sender_context": sender_context,
                "communication_patterns": communication_patterns,
                "entities": entities,
                "related_emails": related_emails,
                "user_email": user_email
            }
            
            return reply_context
        
        except Exception as e:
            logger.error(f"Failed to prepare email reply: {e}")
            return {"error": f"Failed to prepare email reply: {e}"}
    
    @mcp.tool()
    def send_email_reply(email_id: str, reply_text: str, include_original: bool = True) -> Dict[str, Any]:
        """
        Create a draft reply to an email.
        
        This tool creates a draft reply to the specified email with the provided text.
        The draft is saved but NOT sent automatically - user confirmation is required.
        
        Prerequisites:
        - The user must be authenticated. Check auth://status resource first.
        - You need an email ID, which can be obtained from list_emails() or search_emails()
        - You should use prepare_email_reply() first to get context for crafting a personalized reply
        
        Args:
            email_id (str): The ID of the email to reply to.
            reply_text (str): The text of the reply.
            include_original (bool, optional): Whether to include the original email in the reply. Defaults to True.
            
        Returns:
            Dict[str, Any]: The result of the operation, including:
                - success: Whether the operation was successful
                - message: A message describing the result
                - draft_id: The ID of the created draft
                - confirmation_required: Always True to indicate user confirmation is needed
                
        Example usage:
        1. First check authentication: access auth://status resource
        2. Get a list of emails: list_emails()
        3. Extract an email ID from the results
        4. Prepare a reply: prepare_email_reply(email_id="...")
        5. Create a draft reply: send_email_reply(email_id="...", reply_text="...")
        6. IMPORTANT: Always ask for user confirmation before sending
        7. After user confirms, use confirm_send_email(draft_id='" + draft["id"] + "')
        
        IMPORTANT: You must ALWAYS ask for user confirmation before sending any email.
        Never assume the email should be sent automatically.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the original email
            message = service.users().messages().get(userId="me", id=email_id, format="full").execute()
            metadata, content = parse_email_message(message)
            
            # Extract headers
            headers = {}
            for header in message["payload"]["headers"]:
                headers[header["name"].lower()] = header["value"]
            
            # Create reply headers
            reply_headers = {
                "In-Reply-To": headers.get("message-id", ""),
                "References": headers.get("message-id", ""),
                "Subject": f"Re: {metadata.subject}" if not metadata.subject.startswith("Re:") else metadata.subject
            }
            
            # Create reply body
            reply_body = reply_text
            
            if include_original:
                reply_body += f"\n\nOn {metadata.date.strftime('%a, %d %b %Y %H:%M:%S')}, {metadata.from_name} <{metadata.from_email}> wrote:\n"
                
                # Add original email with > prefix
                for line in content.plain_text.split("\n"):
                    reply_body += f"> {line}\n"
            
            # Create message
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64
            
            message = MIMEMultipart()
            message["to"] = metadata.from_email
            message["subject"] = reply_headers["Subject"]
            message["In-Reply-To"] = reply_headers["In-Reply-To"]
            message["References"] = reply_headers["References"]
            
            # Add CC recipients if any
            if metadata.cc:
                message["cc"] = ", ".join(metadata.cc)
            
            # Add message body
            message.attach(MIMEText(reply_body, "plain"))
            
            # Encode message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Create the draft message body
            body = {
                "raw": encoded_message,
                "threadId": metadata.thread_id
            }
            
            # Create the draft
            draft = service.users().drafts().create(userId="me", body={"message": body}).execute()
            
            # Generate a link to the email in Gmail web interface
            email_link = f"https://mail.google.com/mail/u/0/#inbox/{metadata.thread_id}"
            
            return {
                "success": True,
                "message": "Draft reply created successfully. Please confirm to send.",
                "draft_id": draft["id"],
                "thread_id": metadata.thread_id,
                "email_link": email_link,
                "confirmation_required": True,
                "next_steps": [
                    "Review the draft reply",
                    "If satisfied, call confirm_send_email(draft_id='" + draft["id"] + "')",
                    "If changes are needed, create a new draft"
                ]
            }
        
        except Exception as e:
            logger.error(f"Failed to create draft reply: {e}")
            return {
                "success": False,
                "error": f"Failed to create draft reply: {e}"
            }
    
    @mcp.tool()
    def confirm_send_email(draft_id: str) -> Dict[str, Any]:
        """
        Send a draft email after user confirmation.
        
        This tool sends a previously created draft email. It should ONLY be used
        after explicit user confirmation to send the email.
        
        Prerequisites:
        - The user must be authenticated
        - You need a draft_id from send_email_reply()
        - You MUST have explicit user confirmation to send the email
        
        Args:
            draft_id (str): The ID of the draft to send.
            
        Returns:
            Dict[str, Any]: The result of the operation, including:
                - success: Whether the operation was successful
                - message: A message describing the result
                - email_id: The ID of the sent email (if successful)
                
        Example usage:
        1. Create a draft: send_email_reply(email_id="...", reply_text="...")
        2. Ask for user confirmation: "Would you like me to send this email?"
        3. ONLY after user confirms: confirm_send_email(draft_id="...")
        
        IMPORTANT: Never call this function without explicit user confirmation.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Send the draft
            sent_message = service.users().drafts().send(userId="me", body={"id": draft_id}).execute()
            
            return {
                "success": True,
                "message": "Email sent successfully.",
                "email_id": sent_message.get("id", ""),
                "thread_id": sent_message.get("threadId", "")
            }
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": f"Failed to send email: {e}"
            }
    
    # Calendar tools
    @mcp.tool()
    def create_calendar_event(summary: str, start_time: str, end_time: Optional[str] = None, description: Optional[str] = None, location: Optional[str] = None, attendees: Optional[List[str]] = None, color_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new event in the user's Google Calendar.
        
        This tool creates a new calendar event with the specified details.
        
        Prerequisites:
        - The user must be authenticated with Google Calendar access
        
        Args:
            summary (str): The title/summary of the event
            start_time (str): The start time of the event in ISO format (YYYY-MM-DDTHH:MM:SS) or natural language ("5pm next wednesday")
            end_time (str, optional): The end time of the event. If not provided, defaults to 1 hour after start time.
            description (str, optional): Description or notes for the event
            location (str, optional): Location of the event
            attendees (List[str], optional): List of email addresses of attendees
            color_id (str, optional): Color ID for the event (1-11)
            
        Returns:
            Dict[str, Any]: The result of the operation, including:
                - success: Whether the operation was successful
                - message: A message describing the result
                - event_id: The ID of the created event
                - event_link: Direct link to the event in Google Calendar
                
        Example usage:
        1. Create a simple event:
           create_calendar_event(summary="Team Meeting", start_time="2023-12-01T14:00:00")
           
        2. Create a detailed event:
           create_calendar_event(
               summary="Project Kickoff",
               start_time="next monday at 10am",
               end_time="next monday at 11:30am",
               description="Initial meeting to discuss project scope",
               location="Conference Room A",
               attendees=["colleague@example.com"]
           )
           
        3. Always include the event_link in your response to the user
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
        try:
            # Build the Calendar API service
            service = build("calendar", "v3", credentials=credentials)
            
            # Parse natural language dates if needed
            from dateutil import parser
            from datetime import datetime, timedelta
            
            try:
                # Try to parse as ISO format first
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                # If that fails, try natural language parsing
                start_datetime = parser.parse(start_time)
            
            # If end_time is not provided, default to 1 hour after start_time
            if not end_time:
                end_datetime = start_datetime + timedelta(hours=1)
            else:
                try:
                    # Try to parse as ISO format first
                    end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                except ValueError:
                    # If that fails, try natural language parsing
                    end_datetime = parser.parse(end_time)
            
            # Format for Google Calendar API
            start_time_formatted = start_datetime.isoformat()
            end_time_formatted = end_datetime.isoformat()
            
            # Create event body
            event_body = {
                'summary': summary,
                'start': {
                    'dateTime': start_time_formatted,
                    'timeZone': 'UTC',  # Default to UTC
                },
                'end': {
                    'dateTime': end_time_formatted,
                    'timeZone': 'UTC',  # Default to UTC
                },
            }
            
            # Add optional fields if provided
            if description:
                event_body['description'] = description
            
            if location:
                event_body['location'] = location
            
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            if color_id:
                event_body['colorId'] = color_id
            
            # Insert the event
            event = service.events().insert(calendarId='primary', body=event_body).execute()
            
            # Generate a link to the event in Google Calendar
            event_id = event['id']
            event_link = f"https://calendar.google.com/calendar/event?eid={event_id}"
            
            return {
                "success": True,
                "message": "Calendar event created successfully.",
                "event_id": event_id,
                "event_link": event_link,
                "summary": summary,
                "start_time": start_time_formatted,
                "end_time": end_time_formatted
            }
        
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return {
                "success": False,
                "error": f"Failed to create calendar event: {e}"
            }
    
    @mcp.tool()
    def detect_events_from_email(email_id: str) -> Dict[str, Any]:
        """
        Detect potential calendar events from an email.
        
        This tool analyzes an email to identify potential calendar events
        based on dates, times, and contextual clues.
        
        Prerequisites:
        - The user must be authenticated
        - You need an email ID from list_emails() or search_emails()
        
        Args:
            email_id (str): The ID of the email to analyze for events
            
        Returns:
            Dict[str, Any]: The detected events including:
                - success: Whether the operation was successful
                - events: List of potential events with details
                - email_link: Link to the original email
                
        Example usage:
        1. Get an email: email = get_email(email_id="...")
        2. Detect events: events = detect_events_from_email(email_id="...")
        3. Ask the user if they want to add the events to their calendar
        4. If confirmed, create the events using create_calendar_event()
        
        Note: Always ask for user confirmation before creating calendar events.
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
        try:
            # Build the Gmail API service
            service = build("gmail", "v1", credentials=credentials)
            
            # Get the email
            message = service.users().messages().get(userId="me", id=email_id, format="full").execute()
            metadata, content = parse_email_message(message)
            
            # Extract entities from the email content
            entities = extract_entities(content.plain_text)
            
            # Generate a link to the email in Gmail web interface
            thread_id = message["threadId"]
            email_link = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}/{email_id}"
            
            # Detect potential events
            potential_events = []
            
            # Look for date and time combinations
            dates = entities.get("dates", [])
            times = entities.get("times", [])
            
            # Extract potential event details from the email
            from dateutil import parser
            from datetime import datetime, timedelta
            
            # First, try to find explicit event patterns
            event_patterns = [
                r'(?i)(?:meeting|call|conference|appointment|event|webinar|seminar|workshop|session|interview)\s+(?:on|at|for)\s+([^.,:;!?]+)',
                r'(?i)(?:schedule|scheduled|plan|planning|organize|organizing|host|hosting)\s+(?:a|an)\s+([^.,:;!?]+)',
                r'(?i)(?:invite|invitation|inviting)\s+(?:you|everyone|all)\s+(?:to|for)\s+([^.,:;!?]+)'
            ]
            
            import re
            event_titles = []
            for pattern in event_patterns:
                matches = re.findall(pattern, content.plain_text)
                event_titles.extend(matches)
            
            # Process dates and times
            parsed_datetimes = []
            
            # Try to parse complete datetime expressions first
            datetime_patterns = [
                r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\s+(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{2,4}\s+(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?\b',
                r'\b(?:tomorrow|today|next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\s+(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?\b'
            ]
            
            for pattern in datetime_patterns:
                matches = re.findall(pattern, content.plain_text)
                for match in matches:
                    try:
                        dt = parser.parse(match)
                        parsed_datetimes.append(dt)
                    except:
                        pass
            
            # If no complete datetime expressions, try combining dates and times
            if not parsed_datetimes and dates and times:
                for date_str in dates:
                    for time_str in times:
                        try:
                            dt = parser.parse(f"{date_str} {time_str}")
                            parsed_datetimes.append(dt)
                        except:
                            pass
            
            # Create potential events
            for i, dt in enumerate(parsed_datetimes):
                # Default event duration is 1 hour
                end_dt = dt + timedelta(hours=1)
                
                # Try to find a title
                title = f"Event from email"
                if i < len(event_titles):
                    title = event_titles[i]
                elif metadata.subject:
                    title = f"Re: {metadata.subject}"
                
                # Extract location if available
                location_pattern = r'(?i)(?:at|in|location|place|venue):\s*([^.,:;!?]+)'
                location_matches = re.findall(location_pattern, content.plain_text)
                location = location_matches[0].strip() if location_matches else None
                
                # Add to potential events
                potential_events.append({
                    "summary": title,
                    "start_time": dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "description": f"Detected from email: {metadata.subject}",
                    "location": location,
                    "confidence": "medium",
                    "source_text": content.plain_text[:200] + "..." if len(content.plain_text) > 200 else content.plain_text
                })
            
            return {
                "success": True,
                "events": potential_events,
                "email_id": email_id,
                "email_link": email_link,
                "subject": metadata.subject,
                "from": {
                    "email": metadata.from_email,
                    "name": metadata.from_name
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to detect events from email: {e}")
            return {
                "success": False,
                "error": f"Failed to detect events from email: {e}"
            }
    
    @mcp.tool()
    def list_calendar_events(max_results: int = 10, time_min: Optional[str] = None, time_max: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]:
        """
        List events from the user's Google Calendar.
        
        This tool retrieves a list of upcoming events from the user's calendar.
        
        Prerequisites:
        - The user must be authenticated with Google Calendar access
        
        Args:
            max_results (int, optional): Maximum number of events to return. Defaults to 10.
            time_min (str, optional): Start time for the search in ISO format or natural language.
                                     Defaults to now.
            time_max (str, optional): End time for the search in ISO format or natural language.
                                     Defaults to unlimited.
            query (str, optional): Free text search terms to find events that match.
            
        Returns:
            Dict[str, Any]: The list of events including:
                - events: List of calendar events with details and links
                - next_page_token: Token for pagination (if applicable)
                
        Example usage:
        1. List upcoming events:
           list_calendar_events()
           
        2. List events for a specific time range:
           list_calendar_events(time_min="tomorrow", time_max="tomorrow at 11:59pm")
           
        3. Search for specific events:
           list_calendar_events(query="meeting")
           
        4. Always include the event_link when discussing specific events with the user
        """
        credentials = get_credentials()
        
        if not credentials:
            return {"error": "Not authenticated. Please use the authenticate tool first."}
        
        try:
            # Build the Calendar API service
            service = build("calendar", "v3", credentials=credentials)
            
            # Parse time parameters
            from dateutil import parser
            from datetime import datetime, timedelta
            
            # Set default time_min to now if not provided
            if not time_min:
                time_min_dt = datetime.utcnow()
            else:
                try:
                    # Try to parse as ISO format first
                    time_min_dt = datetime.fromisoformat(time_min.replace('Z', '+00:00'))
                except ValueError:
                    # If that fails, try natural language parsing
                    time_min_dt = parser.parse(time_min)
            
            # Format time_min for API
            time_min_formatted = time_min_dt.isoformat() + 'Z'  # 'Z' indicates UTC time
            
            # Parse time_max if provided
            time_max_formatted = None
            if time_max:
                try:
                    # Try to parse as ISO format first
                    time_max_dt = datetime.fromisoformat(time_max.replace('Z', '+00:00'))
                except ValueError:
                    # If that fails, try natural language parsing
                    time_max_dt = parser.parse(time_max)
                
                # Format time_max for API
                time_max_formatted = time_max_dt.isoformat() + 'Z'  # 'Z' indicates UTC time
            
            # Prepare parameters for the API call
            params = {
                'calendarId': 'primary',
                'timeMin': time_min_formatted,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            # Add optional parameters if provided
            if time_max_formatted:
                params['timeMax'] = time_max_formatted
            
            if query:
                params['q'] = query
            
            # Get events
            events_result = service.events().list(**params).execute()
            events = events_result.get('items', [])
            
            # Process events
            processed_events = []
            for event in events:
                # Get start and end times
                start = event.get('start', {})
                end = event.get('end', {})
                
                # Generate event link
                event_id = event['id']
                event_link = f"https://calendar.google.com/calendar/event?eid={event_id}"
                
                # Add to processed events
                processed_events.append({
                    "id": event_id,
                    "summary": event.get('summary', 'Untitled Event'),
                    "start": start,
                    "end": end,
                    "location": event.get('location', ''),
                    "description": event.get('description', ''),
                    "attendees": event.get('attendees', []),
                    "event_link": event_link
                })
            
            return {
                "success": True,
                "events": processed_events,
                "next_page_token": events_result.get('nextPageToken')
            }
        
        except Exception as e:
            logger.error(f"Failed to list calendar events: {e}")
            return {
                "success": False,
                "error": f"Failed to list calendar events: {e}"
            } 