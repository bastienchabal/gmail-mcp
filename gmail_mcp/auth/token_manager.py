"""
Token Manager Module

This module provides functionality for securely storing and managing OAuth tokens.
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.utils.config import get_config

# Get logger
logger = get_logger(__name__)


class TokenManager:
    """
    Class for securely storing and managing OAuth tokens.
    """
    
    def __init__(self) -> None:
        """Initialize the TokenManager."""
        self.config = get_config()
        self.token_path = Path(self.config["token_storage_path"])
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key) if self.encryption_key else None
        self._state = None
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """
        Get the encryption key from the environment.
        
        Returns:
            Optional[bytes]: The encryption key, or None if not set.
        """
        key = self.config["token_encryption_key"]
        
        if not key:
            logger.warning("No encryption key found, tokens will not be encrypted")
            return None
        
        # Ensure the key is 32 bytes (256 bits) for Fernet
        if len(key) < 32:
            key = key.ljust(32, "0")
        elif len(key) > 32:
            key = key[:32]
        
        # Convert to bytes and encode for Fernet
        return base64.urlsafe_b64encode(key.encode())
    
    def store_token(self, credentials: Credentials) -> None:
        """
        Store the OAuth token securely.
        
        Args:
            credentials (Credentials): The OAuth credentials to store.
        """
        # Create the token directory if it doesn't exist
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert the credentials to a dictionary
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        
        # Convert the dictionary to JSON
        token_json = json.dumps(token_data)
        
        # Encrypt the JSON if encryption is enabled
        if self.fernet:
            token_json = self.fernet.encrypt(token_json.encode()).decode()
        
        # Write the token to the file
        with open(self.token_path, "w") as f:
            f.write(token_json)
        
        logger.info(f"Stored token at {self.token_path}")
    
    def get_token(self) -> Optional[Credentials]:
        """
        Get the stored OAuth token.
        
        Returns:
            Optional[Credentials]: The OAuth credentials, or None if not found.
        """
        # Check if the token file exists
        if not self.token_path.exists():
            logger.warning(f"Token file not found at {self.token_path}")
            return None
        
        try:
            # Read the token from the file
            with open(self.token_path, "r") as f:
                token_json = f.read()
            
            # Decrypt the JSON if encryption is enabled
            if self.fernet:
                token_json = self.fernet.decrypt(token_json.encode()).decode()
            
            # Parse the JSON
            token_data = json.loads(token_json)
            
            # Convert the expiry string to a datetime
            if token_data.get("expiry"):
                token_data["expiry"] = datetime.fromisoformat(token_data["expiry"])
            
            # Create the credentials
            credentials = Credentials(
                token=token_data["token"],
                refresh_token=token_data["refresh_token"],
                token_uri=token_data["token_uri"],
                client_id=token_data["client_id"],
                client_secret=token_data["client_secret"],
                scopes=token_data["scopes"],
            )
            
            # Set the expiry
            if token_data.get("expiry"):
                credentials.expiry = token_data["expiry"]
            
            return credentials
        
        except Exception as e:
            logger.error(f"Failed to get token: {e}")
            return None
    
    def clear_token(self) -> None:
        """Clear the stored OAuth token."""
        # Check if the token file exists
        if not self.token_path.exists():
            logger.warning(f"Token file not found at {self.token_path}")
            return
        
        # Delete the token file
        self.token_path.unlink()
        logger.info(f"Cleared token at {self.token_path}")
    
    def store_state(self, state: str) -> None:
        """
        Store the OAuth state parameter.
        
        Args:
            state (str): The state parameter.
        """
        self._state = state
        logger.info("Stored OAuth state parameter")
    
    def verify_state(self, state: str) -> bool:
        """
        Verify the OAuth state parameter.
        
        Args:
            state (str): The state parameter to verify.
            
        Returns:
            bool: True if the state parameter is valid, False otherwise.
        """
        if not self._state or not state or self._state != state:
            logger.warning("Invalid OAuth state parameter")
            return False
        
        logger.info("Verified OAuth state parameter")
        return True 