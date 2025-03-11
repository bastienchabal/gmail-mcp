# Gmail MCP Server

A Model Context Protocol (MCP) server for Gmail integration with Claude Desktop, enabling intelligent, context-aware interactions with your email.

## Features

- **Deep Email Analysis**: Provides comprehensive context from entire conversation threads
- **Context-Aware Responses**: Generates responses considering full communication history
- **Intelligent Action Suggestions**: Analyzes email content for calendar events, tasks, and follow-ups
- **Advanced Search**: Searches across entire email history with semantic understanding
- **Personalization**: Adapts to your communication style with specific contacts

## Prerequisites

- Python 3.10+
- A Google Cloud Platform account with Gmail API enabled
- OAuth 2.0 credentials for the Gmail API
- Claude Desktop with MCP support

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/bastienchabal/gmail-mcp.git
   cd gmail-mcp
   ```

2. Set up a virtual environment using uv:
   ```bash
   pip install uv
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

## Configuration

### Step 1: Authenticate with Google

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
2. Enable Google APIs :
   - [Enable the Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
   - [Enable the Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)
3. Configure the [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent):
   - Select "External" user type
   - Add your email as a test user
   - Add the scope: `https://www.googleapis.com/auth/gmail/modify`
4. Create [OAuth 2.0 credentials](https://console.cloud.google.com/apis/credentials):
   - Choose "Desktop app" as the application type
   - Download the JSON credentials file
   - Copy the Client ID and Client Secret
7. Replace every values between < > in `claude_desktop_config.json` file in `/Users/<username>/Library/Application Support/Claude`
```json
{
  "mcpServers": {
    "gmail-mcp": {
      "command": "/<absolute-path>/gmail-mcp/.venv/bin/mcp",
      "args": [
        "run",
        "/<absolute-path>/gmail-mcp/gmail_mcp/main.py:mcp"
      ],
      "cwd": "/<absolute-path>/gmail-mcp",
      "env": {
        "PYTHONPATH": "/<absolute-path>/gmail-mcp",
        "MCP_SERVER_NAME": "Gmail MCP",
        "MCP_SERVER_DESCRIPTION": "A Model Context Protocol server for Gmail integration with Claude Desktop",
        "HOST": "localhost",
        "PORT": "8000",
        "DEBUG": "true",
        "LOG_LEVEL": "INFO",
        "GOOGLE_CLIENT_ID": "<your-client-id>",
        "GOOGLE_CLIENT_SECRET": "<your-client-secret>",
        "GOOGLE_REDIRECT_URI": "http://localhost:8000/auth/callback",
        "GOOGLE_AUTH_SCOPES": "https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.send",
        "GMAIL_API_SCOPES": "https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.labels,https://www.googleapis.com/auth/gmail.modify",
        "TOKEN_STORAGE_PATH": "/<absolute-path>/gmail-mcp/tokens.json",
        "TOKEN_ENCRYPTION_KEY": "45b9a6655b42fb9e41a8671e8edd2c2345c0eb42cb334d30a2f403b61cb7d0e8",
        "MCP_VERSION": "2025-03-07",
        "CALENDAR_API_ENABLED": "false",
        "CALENDAR_API_SCOPES": "https://www.googleapis.com/auth/calendar.readonly,https://www.googleapis.com/auth/calendar.events"
      }
    }
  }
}
```

### Step 2: Use Claude Desktop

With the MCP server running:
1. Open Claude Desktop
2. Type a prompt like: "Please retrieve my last email"
3. Claude should automatically connect to the MCP server and ask you to authenticate to your Gmail account (creating the file tokens.json)

If Claude Desktop doesn't connect automatically (i.e. you do not see the tool icon underneath the prompt input), you can try:
- Restarting Claude Desktop
- Asking Claude to "Use the Gmail MCP server"
- Login to Gmail manually using : 
```bash
python -c "from gmail_mcp.auth.oauth import start_oauth_process; print(start_oauth_process(timeout=60))"
```

## Troubleshooting

If you encounter issues:

1. **Authentication Problems**:
   - Run `python debug/simple_auth.py` again to re-authenticate
   - Check that the token file exists at the project root

2. **Connection Issues**:
   - Make sure the MCP server is running (`python run_gmail_mcp.py`)
   - Restart Claude Desktop
   - Check for any error messages in the terminal running the MCP server

3. **JSON Errors**:
   - Restart the MCP server and Claude Desktop
   - Run `python debug/diagnose_claude_mcp.py` to diagnose issues

## Advanced Usage

The MCP server provides several tools that Claude can use:

- `get_email_count`: Get the count of emails in your inbox
- `list_emails`: List emails from your mailbox
- `get_email`: Get a specific email by ID
- `search_emails`: Search for emails using Gmail's search syntax

You can ask Claude to use these tools by phrasing your requests naturally, such as:
- "How many unread emails do I have?"
- "Show me my recent emails"
- "Find emails from John about the project"
- "Get the details of my last email"

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project uses the Model Context Protocol (MCP) developed by Anthropic
- Gmail API access is provided by Google's API services
