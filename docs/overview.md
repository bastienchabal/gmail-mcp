# Gmail MCP Overview

This document provides an overview of all components in the Gmail MCP server, including tools, resources, and prompts.

## Tools

Tools are functions that Claude can call to perform actions.

| Tool | Description | Parameters | Use Case |
|------|-------------|------------|----------|
| `login_tool` | Initiates the login process | None | Start authentication flow |
| `authenticate` | Starts the OAuth2 authentication process | None | Begin authentication with Google |
| `process_auth_code_tool` | Processes the authorization code | `code`: str, `state`: str | Complete OAuth2 flow after user grants permission |
| `logout` | Logs out the current user | None | End the current session |
| `check_auth_status` | Checks if user is authenticated | None | Verify authentication before performing actions |
| `get_email_count` | Gets count of emails | None | Quick overview of inbox status |
| `list_emails` | Lists emails from a label | `max_results`: int, `label`: str | Browse recent emails |
| `get_email` | Gets a specific email | `email_id`: str | View details of a single email |
| `search_emails` | Searches emails by query | `query`: str, `max_results`: int | Find specific emails |
| `get_email_overview` | Gets overview of inbox | None | Summarize inbox status |
| `prepare_email_reply` | Prepares context for reply | `email_id`: str | Gather context before replying |
| `send_email_reply` | Creates a draft reply | `email_id`: str, `reply_text`: str, `include_original`: bool | Draft a reply to an email |
| `confirm_send_email` | Sends a draft email | `draft_id`: str | Send a previously created draft |
| `create_calendar_event` | Creates a calendar event | `summary`: str, `start_time`: str, `end_time`: str, `description`: str, `location`: str, `attendees`: List[str], `color_id`: str (color name or ID 1-11) | Schedule a new event |
| `detect_events_from_email` | Detects events in email | `email_id`: str | Extract event details from email |
| `list_calendar_events` | Lists calendar events | `max_results`: int, `time_min`: str, etc. | View upcoming events |
| `suggest_meeting_times` | Suggests available times | `start_date`: str, `end_date`: str, etc. | Find free slots for meetings |

## Resources

Resources provide context data that Claude can access.

| Resource | Description | Parameters | Use Case |
|----------|-------------|------------|----------|
| `auth://status` | Authentication status | None | Check if user is authenticated |
| `gmail://status` | Gmail account status | None | Get overview of Gmail account |
| `email://{email_id}` | Email context | `email_id`: str | Get detailed context for an email |
| `thread://{thread_id}` | Thread context | `thread_id`: str | Get context for an entire thread |
| `sender://{sender_email}` | Sender context | `sender_email`: str | Get context about a specific sender |
| `server://info` | Server information | None | Get basic server details |
| `server://config` | Server configuration | None | Get server configuration |
| `server://status` | Comprehensive status | None | Get overall system status |
| `debug://help` | Debugging guidance | None | Get help with troubleshooting |
| `health://` | Health check | None | Check if server is healthy |

## Prompts

Prompts are templated messages for users.

| Prompt | Description | Use Case |
|--------|-------------|----------|
| `gmail://quickstart` | Quick start guide | Help users get started with Gmail MCP |
| `gmail://search_guide` | Gmail search syntax guide | Help users craft search queries |
| `gmail://authentication_guide` | Authentication guide | Help with authentication process |
| `gmail://debug_guide` | Debugging guide | Help troubleshoot issues |
| `gmail://reply_guide` | Email reply guide | Guide for context-aware replies |

## Email Processor Functions

The email processor module provides utility functions for processing emails.

| Function | Description | Parameters | Return Value |
|----------|-------------|------------|--------------|
| `parse_email_message` | Parses a Gmail API message | `message`: Dict | Tuple of EmailMetadata and EmailContent |
| `extract_content` | Extracts content from email payload | `payload`: Dict | EmailContent object |
| `extract_text_from_html` | Extracts plain text from HTML | `html_content`: str | Plain text string |
| `analyze_thread` | Analyzes an email thread | `thread_id`: str | Thread object or None |
| `get_sender_history` | Gets history of a sender | `sender_email`: str | Sender object or None |
| `extract_email_metadata` | Extracts metadata from message | `message`: Dict | EmailMetadata object |
| `extract_entities` | Extracts entities from text | `text`: str | Dict of entity types and values |
| `analyze_communication_patterns` | Analyzes communication patterns | `sender_email`: str, `recipient_email`: str | Dict of communication analysis |
| `find_related_emails` | Finds emails related to a given email | `email_id`: str, `max_results`: int | List of related emails |

## Calendar Processor Functions

The calendar processor module provides utility functions for handling calendar events.

| Function | Description | Parameters | Return Value |
|----------|-------------|------------|--------------|
| `get_user_timezone` | Gets user's timezone | None | Timezone string |
| `create_calendar_event_object` | Creates calendar event object | Various parameters | Dict for Calendar API |
| `get_color_id_from_name` | Converts color name to color ID | `color_name`: str | Color ID string or None |
| `get_free_busy_info` | Gets free/busy information | `start_time`, `end_time` | Dict of free/busy info |
| `suggest_meeting_times` | Suggests available meeting times | Various parameters | List of suggested times |

## Calendar Color Mapping

Google Calendar uses color IDs 1-11 for event colors. The MCP provides a mapping between color names and IDs:

| Color Name | Color ID | Alternative Names |
|------------|----------|-------------------|
| blue | 1 | light blue |
| green | 2 | light green |
| purple | 3 | lavender |
| red | 4 | salmon |
| yellow | 5 | pale yellow |
| orange | 6 | peach |
| turquoise | 7 | cyan |
| gray | 8 | light gray |
| bold blue | 9 | dark blue |
| bold green | 10 | dark green |
| bold red | 11 | dark red |

When creating calendar events, you can specify either:
- A color name (e.g., "red", "blue", "purple") which will be converted to its corresponding ID
- A color ID directly (e.g., "1", "2", "3")

If no color is specified or if the color name doesn't match any known color, the default color blue (1) will be used.

## Usage Flow

Typical usage flow:

1. Check authentication with `check_auth_status()`
2. If not authenticated, use `authenticate()` 
3. Get email overview with `get_email_overview()`
4. List or search emails
5. View specific emails with `get_email()`
6. Reply to emails using the context-aware reply system
7. Create or manage calendar events as needed

## Important Notes

- Always check authentication before performing actions
- For email replies, always get user confirmation before sending
- Use resources to get rich context for more intelligent interactions
- Refer to the appropriate guides when users need help
- When creating calendar events, you can use color names (e.g., "red", "blue") instead of color IDs - the conversion happens automatically in the tool, with blue (1) as the default if no color is specified or recognized
- The calendar tools now include better date/time parsing that works across multiple languages
- Calendar events include the current date/time in the response for better context awareness
- The calendar functionality has been streamlined for better performance and maintainability
- When creating calendar events, the current user is always added automatically as an attendee 