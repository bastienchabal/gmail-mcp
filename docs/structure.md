# Gmail MCP Project Structure

This document outlines the structure of the Gmail MCP project, showing the organization of files and directories with brief descriptions of their purpose.

```
gmail-mcp/
├── gmail_mcp/                     # Main package directory
│   ├── auth/                      # Authentication-related modules
│   │   ├── callback_server.py     # Server for handling OAuth callbacks
│   │   ├── oauth.py               # OAuth2 authentication implementation
│   │   └── token_manager.py       # Manages authentication tokens
│   │
│   ├── calendar/                  # Calendar-related modules
│   │   └── processor.py           # Functions for processing calendar events
│   │
│   ├── gmail/                     # Gmail-related modules
│   │   └── processor.py           # Functions for processing emails
│   │
│   ├── mcp/                       # MCP implementation modules
│   │   ├── resources.py           # MCP resources implementation
│   │   ├── prompts.py             # MCP prompts implementation
│   │   ├── tools.py               # MCP tools implementation
│   │   └── schemas.py             # Data schemas for MCP components
│   │
│   ├── utils/                     # Utility modules
│   │   ├── config.py              # Configuration management
│   │   └── logger.py              # Logging utilities
│   │
│   └── main.py                    # Main application entry point
│
├── docs/                          # Documentation
│   ├── functions.md               # Documentation of functions
│   ├── notes.md                   # Development notes
│   ├── overview.md                # Overview of MCP components
│   ├── structure.md               # This file - project structure
│   └── todo.md                    # Task tracking
│
├── project/                       # Project management files
│   ├── functions.md               # Function specifications
│   ├── notes.md                   # Project notes and decisions
│   ├── project.md                 # Project overview and goals
│   ├── structure.md               # Project structure planning
│   └── todo.md                    # Task list and progress
│
├── config.yaml                    # Application configuration
├── pyproject.toml                 # Project dependencies and metadata
├── pyrightconfig.json             # Pyright (type checking) configuration
├── README.md                      # Project readme
├── setup.cfg                      # Package setup configuration
└── uv.lock                        # UV package manager lock file
```

## Key Components

### Authentication (auth/)

The authentication module handles OAuth2 authentication with Google's APIs:

- **callback_server.py**: Implements a local web server to receive OAuth callbacks
- **oauth.py**: Manages the OAuth2 flow with Google
- **token_manager.py**: Handles token storage, retrieval, and refresh

### Gmail Processing (gmail/)

- **processor.py**: Contains functions for parsing, analyzing, and processing emails, including thread analysis, entity extraction, and communication pattern analysis

### Calendar Processing (calendar/)

- **processor.py**: Provides utilities for calendar operations, including natural language date parsing, event creation, and meeting time suggestions

### MCP Implementation (mcp/)

The core MCP implementation that exposes Gmail functionality to Claude:

- **resources.py**: Defines MCP resources that provide context to Claude
- **prompts.py**: Defines MCP prompts for user guidance
- **tools.py**: Implements MCP tools that Claude can call
- **schemas.py**: Defines data structures used throughout the MCP

### Utilities (utils/)

- **config.py**: Manages application configuration
- **logger.py**: Provides logging functionality

### Main Application

- **main.py**: The entry point for the MCP server, sets up FastAPI and MCP components

## Configuration Files

- **config.yaml**: Contains application settings like API keys and server configuration
- **pyproject.toml**: Defines project dependencies and build configuration
- **setup.cfg**: Package setup configuration

## Documentation

- **docs/**: Contains user and developer documentation
- **project/**: Contains project planning and management documents 