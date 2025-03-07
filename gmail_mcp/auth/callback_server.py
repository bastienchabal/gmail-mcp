"""
OAuth Callback Server Module

This module provides a simple HTTP server to handle the OAuth callback.
"""

import http.server
import socketserver
import threading
import webbrowser
import urllib.parse
import logging
import socket
import time
import re
from typing import Dict, Any, Optional, Callable, Tuple, ClassVar, Type, cast, Protocol, Union, TypeVar, Generic

from gmail_mcp.utils.logger import get_logger
from gmail_mcp.utils.config import get_config

# Get logger
logger = get_logger(__name__)

# Define a type for the callback function
CallbackFn = Callable[[str, str], str]

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """
    HTTP request handler for OAuth callback.
    """
    
    # Class variable to store the callback function
    callback_fn: ClassVar[Optional[CallbackFn]] = None
    # Flag to indicate if the callback has been processed
    callback_processed: ClassVar[bool] = False
    
    def do_GET(self) -> None:
        """Handle GET requests."""
        try:
            # Parse the URL and query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Check if this is the OAuth callback
            if parsed_url.path == "/auth/callback":
                # Extract the authorization code and state
                code = query_params.get("code", [""])[0]
                state = query_params.get("state", [""])[0]
                
                # Process the authorization code if a callback function is set
                if OAuthCallbackHandler.callback_fn is not None and code and state:
                    # Use a safer approach to call the function
                    fn = OAuthCallbackHandler.callback_fn
                    result = fn(code, state)
                    success = not result.startswith("Error")
                    # Set the flag to indicate that the callback has been processed
                    OAuthCallbackHandler.callback_processed = True
                else:
                    result = "Error: No callback function set or missing parameters"
                    success = False
                
                # Send a response to the user
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                # Create a simple HTML response
                html_response = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Gmail MCP - Authentication</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                        h1 {{ color: {'#4CAF50' if success else '#F44336'}; }}
                        .message {{ margin: 20px 0; padding: 10px; background-color: {'#E8F5E9' if success else '#FFEBEE'}; border-radius: 5px; }}
                        .button {{ display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>{'Authentication Successful' if success else 'Authentication Failed'}</h1>
                        <div class="message">{result}</div>
                        <p>{'You can now close this window and return to the Gmail MCP server.' if success else 'Please try again or check the server logs for more information.'}</p>
                        <p>This window will automatically close in 5 seconds.</p>
                        <script>
                            setTimeout(function() {{
                                window.close();
                            }}, 5000);
                        </script>
                    </div>
                </body>
                </html>
                """
                
                self.wfile.write(html_response.encode())
                
                # Log the result
                if success:
                    logger.info("OAuth callback processed successfully")
                else:
                    logger.error(f"OAuth callback processing failed: {result}")
                
                # Signal the server to shut down after a short delay to allow the response to be sent
                threading.Timer(1.0, self.server.shutdown).start()
            else:
                # Handle other paths
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Not found")
        
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode())
    
    def log_message(self, format: str, *args: Any) -> None:
        """Override log_message to use our logger."""
        logger.debug(f"{self.client_address[0]} - {format % args}")


class ReuseAddressTCPServer(socketserver.TCPServer):
    """TCP Server that reuses the address."""
    allow_reuse_address = True


class OAuthCallbackServer:
    """
    Simple HTTP server for handling OAuth callbacks.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000) -> None:
        """
        Initialize the OAuth callback server.
        
        Args:
            host (str, optional): The host to bind to. Defaults to "localhost".
            port (int, optional): The port to bind to. Defaults to 8000.
        """
        self.host = host
        self.port = self._find_available_port(port)
        self.server = None
        self.server_thread = None
    
    def _find_available_port(self, preferred_port: int) -> int:
        """
        Find an available port, starting with the preferred port.
        
        Args:
            preferred_port (int): The preferred port to use.
            
        Returns:
            int: An available port.
        """
        port = preferred_port
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                # Try to create a socket with the current port
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    # If we get here, the port is available
                    return port
            except OSError:
                # Port is in use, try the next one
                logger.warning(f"Port {port} is already in use, trying {port + 1}")
                port += 1
        
        # If we get here, we couldn't find an available port
        logger.warning(f"Could not find an available port after {max_attempts} attempts, using {port}")
        return port
    
    def start(self, callback_fn: CallbackFn) -> None:
        """
        Start the OAuth callback server.
        
        Args:
            callback_fn (CallbackFn): The function to call when a callback is received.
                The function should take the authorization code and state as arguments and return a result message.
        """
        # Reset the callback processed flag
        OAuthCallbackHandler.callback_processed = False
        
        # Set the callback function
        OAuthCallbackHandler.callback_fn = callback_fn
        
        try:
            # Create and start the server in a separate thread
            self.server = ReuseAddressTCPServer((self.host, self.port), OAuthCallbackHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logger.info(f"OAuth callback server started at http://{self.host}:{self.port}/auth/callback")
        except OSError as e:
            logger.error(f"Failed to start OAuth callback server: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the OAuth callback server."""
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                logger.info("OAuth callback server stopped")
            except Exception as e:
                logger.error(f"Error stopping OAuth callback server: {e}")


def extract_port_from_redirect_uri(redirect_uri: str) -> int:
    """
    Extract the port from a redirect URI.
    
    Args:
        redirect_uri (str): The redirect URI.
        
    Returns:
        int: The port number, or 8000 if not found.
    """
    # Parse the URI
    parsed = urllib.parse.urlparse(redirect_uri)
    
    # Check if there's a port in the netloc
    if ":" in parsed.netloc:
        try:
            return int(parsed.netloc.split(":")[1])
        except (ValueError, IndexError):
            pass
    
    # Default to 8000 if no port is found
    return 8000


def start_oauth_flow(auth_url: str, callback_fn: CallbackFn, host: str = "localhost", port: Optional[int] = None, timeout: int = 300) -> None:
    """
    Start the OAuth flow by opening the browser and starting the callback server.
    
    Args:
        auth_url (str): The authorization URL to open in the browser.
        callback_fn (CallbackFn): The function to call when a callback is received.
        host (str, optional): The host to bind to. Defaults to "localhost".
        port (int, optional): The port to bind to. If None, extract from redirect_uri.
        timeout (int, optional): The maximum time to wait for the callback in seconds. Defaults to 300 (5 minutes).
    """
    # Get the configuration
    config = get_config()
    redirect_uri = config.get("google_redirect_uri", "http://localhost:8000/auth/callback")
    
    # Extract the port from the redirect URI if not provided
    if port is None:
        port = extract_port_from_redirect_uri(redirect_uri)
    
    # Start the callback server
    try:
        server = OAuthCallbackServer(host, port)
        actual_port = server.port
        
        # If the actual port is different from the configured port, we need to warn the user
        if actual_port != port:
            logger.warning(f"Port {port} from redirect URI is already in use. Using port {actual_port} instead.")
            logger.warning(f"This may cause a redirect_uri_mismatch error. Please update your Google Cloud Console configuration.")
            logger.warning(f"Add http://{host}:{actual_port}/auth/callback as an authorized redirect URI.")
            
            print("\n" + "=" * 80)
            print("WARNING: PORT MISMATCH")
            print("=" * 80)
            print(f"The port {port} from your redirect URI is already in use.")
            print(f"Using port {actual_port} instead, but this may cause authentication to fail.")
            print(f"To fix this, add http://{host}:{actual_port}/auth/callback as an authorized redirect URI")
            print("in your Google Cloud Console project.")
            print("=" * 80 + "\n")
        
        server.start(callback_fn)
        
        # Open the browser
        webbrowser.open(auth_url)
        
        # Print instructions
        print(f"\nA browser window should have opened to complete the authentication process.")
        print(f"If not, please manually open this URL: {auth_url}")
        print(f"\nWaiting for authentication to complete (timeout: {timeout} seconds)...")
        
        # Wait for the callback to be processed or timeout
        start_time = time.time()
        while not OAuthCallbackHandler.callback_processed and time.time() - start_time < timeout:
            time.sleep(1)
            
            # Check if the server thread is still alive
            if server.server_thread and not server.server_thread.is_alive():
                break
        
        # Check if we timed out
        if not OAuthCallbackHandler.callback_processed and time.time() - start_time >= timeout:
            logger.error(f"OAuth authentication timed out after {timeout} seconds")
            print(f"\nAuthentication timed out after {timeout} seconds.")
            print("Please try again or check your network connection.")
        
        # Make sure the server is stopped
        server.stop()
        
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {e}")
        print(f"\nError starting OAuth flow: {e}")
        print("Please try again later or contact support.") 