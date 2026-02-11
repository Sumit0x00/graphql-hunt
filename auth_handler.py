import requests
from colorama import Fore, Style

class AuthHandler:
    """Handles authentication for GraphQL requests"""
    
    def __init__(self, auth_type=None, token=None, cookies=None):
        """
        Initialize authentication handler
        
        Args:
            auth_type: 'bearer' or 'cookie'
            token: JWT token string (for bearer auth)
            cookies: Cookie string or dict (for session auth)
        """
        self.auth_type = auth_type
        self.token = token
        self.cookies = cookies
        self.headers = {}
        self.cookie_dict = {}
        
        if auth_type:
            self._setup_auth()
    
    def _setup_auth(self):
        """Setup authentication headers/cookies based on type"""
        if self.auth_type == "bearer" and self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
            print(f"{Fore.CYAN}[*] Using Bearer Token authentication")
        
        elif self.auth_type == "cookie" and self.cookies:
            # Handle cookie string format: "session=abc123; token=xyz789"
            if isinstance(self.cookies, str):
                self.cookie_dict = self._parse_cookie_string(self.cookies)
            elif isinstance(self.cookies, dict):
                self.cookie_dict = self.cookies
            print(f"{Fore.CYAN}[*] Using Session Cookie authentication")
    
    def _parse_cookie_string(self, cookie_string):
        """Parse cookie string into dictionary"""
        cookie_dict = {}
        for cookie in cookie_string.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookie_dict[key.strip()] = value.strip()
        return cookie_dict
    
    def get_headers(self, base_headers=None):
        """
        Get headers with authentication
        
        Args:
            base_headers: Base headers dict to merge with auth headers
        
        Returns:
            Complete headers dict
        """
        if base_headers is None:
            base_headers = {}
        
        # Merge base headers with auth headers
        merged_headers = {**base_headers, **self.headers}
        return merged_headers
    
    def get_cookies(self):
        """Get cookies dictionary"""
        return self.cookie_dict
    
    def validate_auth(self, url, base_headers=None):
        """
        Validate authentication credentials
        
        Args:
            url: GraphQL endpoint URL
            base_headers: Base headers for the request
        
        Returns:
            tuple: (is_valid, message)
        """
        if not self.auth_type:
            return True, "No authentication provided (testing unauthenticated endpoint)"
        
        print(f"{Fore.YELLOW}[*] Validating authentication credentials...{Style.RESET_ALL}")
        
        probe_query = {"query": "{ __typename }"}
        headers = self.get_headers(base_headers)
        cookies = self.get_cookies()
        
        try:
            response = requests.post(
                url, 
                json=probe_query, 
                headers=headers, 
                cookies=cookies,
                timeout=10
            )
            
            # Check status codes
            if response.status_code == 401:
                return False, f"{Fore.RED}[✗] Invalid or expired credentials (401 Unauthorized){Style.RESET_ALL}"
            
            elif response.status_code == 403:
                return False, f"{Fore.YELLOW}[!] Valid credentials but insufficient permissions (403 Forbidden){Style.RESET_ALL}"
            
            elif response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data or "errors" in data:
                        return True, f"{Fore.GREEN}[✓] Authentication successful{Style.RESET_ALL}"
                except ValueError:
                    pass
            
            return False, f"{Fore.RED}[✗] Unexpected response (Status: {response.status_code}){Style.RESET_ALL}"
        
        except requests.exceptions.RequestException as e:
            return False, f"{Fore.RED}[✗] Connection error: {e}{Style.RESET_ALL}"
    
    def is_authenticated(self):
        """Check if authentication is configured"""
        return self.auth_type is not None


def create_auth_handler(auth_type=None, token=None, cookies=None):
    """
    Factory function to create AuthHandler
    
    Args:
        auth_type: 'bearer' or 'cookie' or None
        token: JWT token string
        cookies: Cookie string or dict
    
    Returns:
        AuthHandler instance
    """
    return AuthHandler(auth_type=auth_type, token=token, cookies=cookies)