"""
Token Manager Module

This module provides functionality for securely storing and managing OAuth tokens.
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List, Union, cast
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
        # Use tokens.json in the root directory by default
        token_path = self.config.get("token_storage_path", "tokens.json")
        # Expand the path if it contains a tilde
        if token_path.startswith("~"):
            token_path = os.path.expanduser(token_path)
        self.token_path = Path(token_path)
        
        # Also store the project directory path for tokens
        self.project_token_path = Path("tokens.json")
        
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key) if self.encryption_key else None
        self._state = None
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """
        Get the encryption key from the environment.
        
        Returns:
            Optional[bytes]: The encryption key, or None if not set.
        """
        key = self.config.get("token_encryption_key", "")
        
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
    
    def store_token(self, credentials: Any) -> None:
        """
        Store the OAuth token securely.
        
        Args:
            credentials (Any): The OAuth credentials to store. This can be any type of credentials
                               that has the required attributes.
        """
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
        
        # First try to write to the project directory
        try:
            # Write the token to the project directory
            with open(self.project_token_path, "w") as f:
                f.write(token_json)
            
            logger.info(f"Stored token in project directory at {self.project_token_path}")
            # Update the token path to the project directory
            self.token_path = self.project_token_path
            return
        except Exception as e:
            logger.warning(f"Failed to store token in project directory: {e}")
        
        # If that fails, try the configured token path
        try:
            # Create the token directory if it doesn't exist
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the token to the file
            with open(self.token_path, "w") as f:
                f.write(token_json)
            
            logger.info(f"Stored token at {self.token_path}")
        except Exception as e:
            logger.error(f"Failed to store token at configured path: {e}")
            # Try to store in a fallback location if the primary location fails
            fallback_path = Path(os.path.join(os.path.expanduser("~"), "gmail_mcp_tokens", "tokens.json"))
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(fallback_path, "w") as f:
                    f.write(token_json)
                
                logger.info(f"Stored token at fallback location: {fallback_path}")
                # Update the token path to the fallback location
                self.token_path = fallback_path
            except Exception as e2:
                logger.error(f"Failed to store token at fallback location: {e2}")
                raise
    
    def get_token(self) -> Optional[Credentials]:
        """
        Get the stored OAuth token.
        
        Returns:
            Optional[Credentials]: The OAuth credentials, or None if not found.
        """
        # Check all possible token locations in order of preference
        token_paths = [
            self.project_token_path,  # Project directory first
            self.token_path,          # Configured path second
            Path(os.path.join(os.path.expanduser("~"), "gmail_mcp_tokens", "tokens.json"))  # Fallback location last
        ]
        
        for path in token_paths:
            if path.exists():
                logger.info(f"Found token at {path}")
                try:
                    # Read the token from the file
                    with open(path, "r") as f:
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
                    
                    # Update the token path to the found location
                    self.token_path = path
                    
                    return credentials
                except Exception as e:
                    logger.error(f"Failed to get token from {path}: {e}")
        
        logger.warning("No valid token found in any location")
        return None
    
    def clear_token(self) -> None:
        """Clear the stored OAuth token from all possible locations."""
        # Check all possible token locations
        token_paths = [
            self.project_token_path,  # Project directory
            self.token_path,          # Configured path
            Path(os.path.join(os.path.expanduser("~"), "gmail_mcp_tokens", "tokens.json"))  # Fallback location
        ]
        
        for path in token_paths:
            if path.exists():
                try:
                    # Delete the token file
                    path.unlink()
                    logger.info(f"Cleared token at {path}")
                except Exception as e:
                    logger.error(f"Failed to clear token at {path}: {e}")
    
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
        
    def tokens_exist(self) -> bool:
        """
        Check if the token file exists in any of the possible locations.
        
        Returns:
            bool: True if the token file exists, False otherwise.
        """
        # Check all possible token locations
        token_paths = [
            self.project_token_path,  # Project directory first
            self.token_path,          # Configured path second
            Path(os.path.join(os.path.expanduser("~"), "gmail_mcp_tokens", "tokens.json"))  # Fallback location last
        ]
        
        for path in token_paths:
            if path.exists():
                logger.info(f"Found token at {path}")
                # Update the token path to the found location
                self.token_path = path
                return True
        
        return False 