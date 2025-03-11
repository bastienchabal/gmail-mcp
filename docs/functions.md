# Gmail MCP Functions Documentation

This document provides a comprehensive guide to all the tools, resources, and prompts available in the Gmail MCP server, along with instructions on how to use them with Claude Desktop.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Tools](#tools)
  - [Authentication Tools](#authentication-tools)
  - [Email Tools](#email-tools)
- [Resources](#resources)
  - [Authentication Resources](#authentication-resources)
  - [Gmail Resources](#gmail-resources)
  - [Email Resources](#email-resources)
  - [Server Resources](#server-resources)
- [Prompts](#prompts)
- [Common Workflows](#common-workflows)

## Overview

The Gmail MCP (Model Context Protocol) server provides Claude Desktop with access to your Gmail account. It enables Claude to read, search, and analyze your emails, providing context-aware assistance.

## Authentication

Before using any Gmail functionality, you must authenticate with your Google account. The authentication process uses OAuth2 to securely access your Gmail data without storing your password.

### Authentication Flow

1. Check your authentication status
2. If not authenticated, start the authentication process
3. Complete the authentication in your browser
4. Verify that authentication was successful

## Tools

Tools are functions that Claude can call to perform actions. Here's how to use the available tools:

### Authentication Tools

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `authenticate()` | Start the OAuth authentication process | `authenticate()` |
| `login_tool()` | Get the OAuth authorization URL | `login_tool()` |
| `process_auth_code_tool(code, state)` | Process the OAuth authorization code | `process_auth_code_tool(code="4/1AX...", state="...")` |
| `logout()` | Log out and revoke the access token | `logout()` |
| `check_auth_status()` | Check the current authentication status | `check_auth_status()` |

### Email Tools

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `get_email_count()` | Get the count of emails in your inbox | `get_email_count()` |
| `list_emails(max_results, label)` | List emails from a specific label | `list_emails(max_results=10, label="INBOX")` |
| `get_email(email_id)` | Get a specific email by ID | `get_email(email_id="18abc123def456")` |
| `search_emails(query, max_results)` | Search for emails using Gmail's search syntax | `search_emails(query="from:example@gmail.com", max_results=10)` |
| `get_email_overview()` | Get a simple overview of your emails | `get_email_overview()` |
| `prepare_email_reply(email_id)` | Prepare a context-rich reply to an email | `prepare_email_reply(email_id="18abc123def456")` |
| `send_email_reply(email_id, reply_text, include_original)` | Create a draft reply to an email | `send_email_reply(email_id="18abc123def456", reply_text="Your reply here", include_original=True)` |
| `confirm_send_email(draft_id)` | Send a draft email after user confirmation | `confirm_send_email(draft_id="r-123456789")` |

## Resources

Resources are data that Claude can access to get context. Here's how to access the available resources:

### Authentication Resources

| Resource | Description | Example Usage |
|----------|-------------|---------------|
| `auth://status` | Get the current authentication status | `auth://status` |

### Gmail Resources

| Resource | Description | Example Usage |
|----------|-------------|---------------|
| `gmail://status` | Get the current status of the Gmail account | `gmail://status` |

### Email Resources

| Resource | Description | Example Usage |
|----------|-------------|---------------|
| `email://{email_id}` | Get context for a specific email | `email://18abc123def456` |
| `thread://{thread_id}` | Get context for a specific thread | `thread://18abc123def456` |
| `sender://{sender_email}` | Get context for a specific sender | `sender://example@gmail.com` |

### Server Resources

| Resource | Description | Example Usage |
|----------|-------------|---------------|
| `server://info` | Get information about the server | `server://info` |
| `server://config` | Get the server configuration | `server://config` |
| `server://status` | Get the current server status | `server://status` |
| `debug://help` | Get debugging help | `debug://help` |
| `health://` | Check the server health | `health://` |

## Prompts

Prompts are templated messages and workflows for users. Here's how to access the available prompts:

| Prompt | Description | Example Usage |
|--------|-------------|---------------|
| `gmail://quickstart` | Quick start guide for Gmail MCP | `gmail://quickstart` |
| `gmail://search_guide` | Guide to Gmail's search syntax | `gmail://search_guide` |
| `gmail://authentication_guide` | Guide to the authentication process | `gmail://authentication_guide` |
| `gmail://debug_guide` | Guide to debugging common issues | `gmail://debug_guide` |
| `gmail://reply_guide` | Guide to crafting context-aware email replies | `gmail://reply_guide` |

## Common Workflows

### Getting Started

1. Check authentication status:
   ```
   check_auth_status()
   ```

2. If not authenticated, start the authentication process:
   ```
   authenticate()
   ```

3. Get an overview of your inbox:
   ```
   get_email_overview()
   ```

### Searching and Reading Emails

1. Search for emails from a specific sender:
   ```
   search_emails(query="from:example@gmail.com")
   ```

2. List recent emails in your inbox:
   ```
   list_emails(max_results=10, label="INBOX")
   ```

3. View a specific email (replace with an actual email ID):
   ```
   get_email(email_id="18abc123def456")
   ```

### Replying to Emails

1. Find the email you want to reply to:
   ```
   list_emails(max_results=10, label="INBOX")
   ```

2. Prepare a context-rich reply:
   ```
   reply_context = prepare_email_reply(email_id="18abc123def456")
   ```

3. Create a draft reply:
   ```
   draft_result = send_email_reply(
       email_id="18abc123def456",
       reply_text="Your personalized reply here...",
       include_original=True
   )
   ```

4. Ask for user confirmation:
   ```
   "I've created a draft reply. Would you like me to send it?"
   ```

5. Send only after explicit confirmation:
   ```
   confirm_send_email(draft_id=draft_result["draft_id"])
   ```

### Troubleshooting

1. Check authentication status:
   ```
   check_auth_status()
   ```

2. Check server status:
   ```
   server://status
   ```

3. Get debugging help:
   ```
   debug://help
   ```

4. If needed, log out and re-authenticate:
   ```
   logout()
   authenticate()
   ```

## Important Guidelines

### Email Links

When discussing or referencing emails, always include the direct link to the email in Gmail's web interface. These links are automatically included in the context:

- Email context includes `email_link`
- Thread context includes `thread_link`
- Each message in a thread includes its own `email_link`

Example:
```
You can view this email here: https://mail.google.com/mail/u/0/#inbox/12345abcde
```

### Email Confirmation

Never send an email without explicit user confirmation. Always follow this workflow:

1. Create a draft reply using `send_email_reply()`
2. Show the draft to the user and explicitly ask for confirmation
3. Only after receiving explicit confirmation, use `confirm_send_email()`

Example confirmation request:
```
I've created a draft reply. Here's what I've written:

[Draft content]

Would you like me to send this email? If yes, I'll send it. If you'd like to make changes, please let me know.
```
