# Gmail MCP Server for Claude

This project provides a Model Context Protocol (MCP) server that allows Claude Desktop to access your Gmail account. It enables Claude to read your emails, search for specific messages, and perform other Gmail-related tasks.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Claude Desktop installed
- A Google account with Gmail

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/gmail-mcp.git
   cd gmail-mcp
   ```

2. Set up a virtual environment using uv:
   ```bash
   pip install uv
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

## Usage

### Step 1: Authenticate with Google

Before using the MCP server, you need to authenticate with Google:

```bash
python debug/simple_auth.py
```

This will:
1. Open the MCP inspector in your browser
2. Guide you through the Google authentication process
3. Generate a token file that allows the MCP server to access your Gmail account

Follow the on-screen instructions to complete the authentication.

### Step 2: Run the MCP Server

Once you have authenticated, you can run the MCP server:

```bash
python run_gmail_mcp.py
```

This will:
1. Start the Gmail MCP server
2. Keep it running in the background
3. Provide instructions for using it with Claude Desktop

Keep this terminal window open while using Claude Desktop.

### Step 3: Use Claude Desktop

With the MCP server running:
1. Open Claude Desktop
2. Type a prompt like: "Please retrieve my last email"
3. Claude should automatically connect to the MCP server and access your Gmail account

If Claude doesn't connect automatically, you can try:
- Restarting Claude Desktop
- Using specific prompts like "Check my Gmail" or "Connect to Gmail"
- Asking Claude to "Use the Gmail MCP server"

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
