# Generated by https://smithery.ai. See: https://smithery.ai/docs/config#dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app

# Create virtual environment
RUN python -m venv .venv

# Upgrade pip
RUN ./.venv/bin/pip install --upgrade pip

# Install dependencies without running project scripts
RUN ./.venv/bin/pip install --ignore-installed --no-cache-dir -e .

# Expose any ports if needed (e.g., 8000 if the MCP server uses it)
EXPOSE 8000

# Start the MCP server
# The command will be overridden by the startCommand provided in the Smithery config
ENTRYPOINT ["./.venv/bin/mcp", "run", "gmail_mcp/main.py:mcp"]
