# Gmail MCP Project Structure

## Overview

The Gmail MCP project is organized into several modules, each with a specific responsibility:

```
gmail-mcp/
├── gmail_mcp/                  # Main package
│   ├── __init__.py             # Package initialization
│   ├── __main__.py             # Entry point for running as a module
│   ├── main.py                 # FastMCP application setup
│   ├── auth/                   # Authentication module
│   │   ├── __init__.py
│   │   └── oauth.py            # OAuth2 authentication
│   ├── gmail/                  # Gmail API module
│   │   └── processor.py        # Context building functions
│   ├── mcp/                    # MCP module
│   │   ├── resources.py        # Centralized MCP resources
│   │   ├── tools.py            # Centralized MCP tools
│   │   ├── prompts.py          # Centralized MCP prompts
│   │   └── schemas.py          # Pydantic schemas for resources
│   └── utils/                  # Utility module
│       ├── config.py           # Configuration management
│       └── logger.py           # Logging setup
├── debug/                      # Debugging tools
│   └── restart_server.sh       # Script to restart the server
├── docs/                       # Documentation
│   ├── functions.md            # MCP Functions details
│   ├── structure.md            # Project structure documentation
│   └── todo.md                 # Todo list
├── .env                        # Environment variables
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore file
├── LICENSE                     # License file
└── README.md                   # Project README
```

## Module Descriptions

### Main Package (`gmail_mcp/`)

- **`__init__.py`**: Package initialization.
- **`__main__.py`**: Entry point for running the application as a module.
- **`main.py`**: Sets up the FastAPI application and MCP server.

### Authentication Module (`gmail_mcp/auth/`)

- **`oauth.py`**: Implements OAuth2 authentication for the Gmail API.

### Gmail Module (`gmail_mcp/gmail/`)

- This module is now a placeholder for potential future Gmail-specific functionality.

### MCP Module (`gmail_mcp/mcp/`)

- **`resources.py`**: Centralizes all MCP resources.
- **`tools.py`**: Centralizes all MCP tools.
- **`prompts.py`**: Centralizes all MCP prompts.
- **`schemas.py`**: Defines Pydantic schemas used by resources.

### Utils Module (`gmail_mcp/utils/`)

- **`config.py`**: Manages configuration from environment variables.
- **`logger.py`**: Sets up logging for the application.

### Debug Tools (`debug/`)

- **`restart_server.sh`**: Script to restart the server.

### Documentation (`docs/`)

- **`notes.md`**: Development notes and decisions.
- **`structure.md`**: Documentation of the project structure.
- **`todo.md`**: Todo list for the project.

## Key Components

### MCP Resources

All MCP resources are now centralized in `gmail_mcp/mcp/resources.py`. These include:

- `auth://status`: Authentication status
- `gmail://status`: Gmail account status
- `email://{email_id}`: Email context
- `thread://{thread_id}`: Thread context
- `sender://{sender_email}`: Sender context
- `server://info`: Server information
- `server://config`: Server configuration
- `server://status`: Server status
- `debug://help`: Debugging help
- `health://check`: Health check

### MCP Tools

All MCP tools are now centralized in `gmail_mcp/mcp/tools.py`. These include:

- Authentication tools: `login_tool()`, `authenticate()`, `process_auth_code_tool()`, `logout()`, `check_auth_status()`
- Email tools: `get_email_count()`, `list_emails()`, `get_email()`, `search_emails()`, `get_email_overview()`

### MCP Prompts

All MCP prompts are now centralized in `gmail_mcp/mcp/prompts.py`. These include:

- `gmail://quickstart`: Quick start guide
- `gmail://search_guide`: Gmail search syntax guide
- `gmail://authentication_guide`: Authentication guide
- `gmail://debug_guide`: Debugging guide
