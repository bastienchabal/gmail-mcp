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

## Installation

1. Clone the repository:
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

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Configure your OAuth credentials in the `.env` file.

## Configuration

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Web application type)
5. Add `http://localhost:8000/auth/callback` as an authorized redirect URI
6. Copy the Client ID and Client Secret to your `.env` file

## Usage

1. Start the MCP server:
   ```bash
   python -m gmail_mcp.main
   ```

2. The server will start on `http://localhost:8000`

3. On first run, you'll be prompted to authorize the application with your Google account

4. In Claude Desktop, connect to the MCP server using the URL `http://localhost:8000`

## Development

### Project Structure

See [docs/structure.md](docs/structure.md) for the detailed project structure.

### Implementation Plan

The implementation plan and progress are tracked in [docs/todo.md](docs/todo.md).

### Running Tests

```bash
pytest
```

## License

MIT

## Acknowledgements

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/)
- [Anthropic MCP Documentation](https://www.anthropic.com/news/model-context-protocol)
