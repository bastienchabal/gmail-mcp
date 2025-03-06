"""
Logger Utility Module

This module provides functions for setting up and configuring the application logger.
"""

import os
import logging
import sys
from typing import Optional

from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name (Optional[str], optional): The name of the logger. Defaults to None.

    Returns:
        logging.Logger: The configured logger.
    """
    # Get the logger
    logger = logging.getLogger(name or "gmail_mcp")
    
    # Set the log level from environment variable or default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)
    
    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The logger.
    """
    return logging.getLogger(name) 