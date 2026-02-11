import requests
from colorama import Fore, Style
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def load_payloads(filename="payloads.txt"):
    """Load GraphQL endpoints from a file"""
    if not os.path.exists(filename):
        print(f"{Fore.RED}[-] Payload file '{filename}' not found!")
        return []
    
    try:
        with open(filename, 'r') as f:
            payloads = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        print(f"{Fore.CYAN}[*] Loaded {len(payloads)} endpoints from {filename}")
        return payloads
    except Exception as e:
        print(f"{Fore.RED}[-] Error reading payload file: {e}")
        return []


def test_single_endpoint(base_url, path, headers):
    """Test a single GraphQL endpoint"""
    target_url = f"{base_url}{path}"
    try:
        probe = {"query": "{ __typename }"}
        response = requests.post(target_url, json=probe, headers=headers, timeout=5)
        
        if response.status_code == 200:
            try:
                res_json = response.json()
                if "data" in res_json or "errors" in res_json:
                    return target_url
            except ValueError:
                pass
    except requests.exceptions.RequestException:
        pass
    
    return None


def find_graphql_endpoint(base_url, payload_file="payloads.txt", threads=10):
    """
    Find GraphQL endpoint using multi-threaded fuzzing
    
    Args:
        base_url: Target base URL
        payload_file: Path to payloads file
        threads: Number of concurrent threads (default: 10)
    
    Returns:
        Found endpoint URL or None
    """
    print(f"{Fore.CYAN}[*] Starting endpoint fuzzing on: {base_url}")
    print(f"{Fore.CYAN}[*] Using {threads} concurrent threads")
    
    base_url = base_url.rstrip('/')
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    endpoints = load_payloads(payload_file)
    
    if not endpoints:
        print(f"{Fore.RED}[-] No endpoints to test.")
        return None

    found_url = None
    lock = threading.Lock()
    
    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Submit all tasks
        future_to_path = {
            executor.submit(test_single_endpoint, base_url, path, headers): path 
            for path in endpoints
        }
        
        # Process completed tasks
        for future in as_completed(future_to_path):
            result = future.result()
            if result:
                with lock:
                    if not found_url:  # Only print first found
                        found_url = result
                        print(f"{Fore.GREEN}[+] Found valid endpoint: {found_url}")
                        # Cancel remaining tasks
                        for f in future_to_path:
                            f.cancel()
                        break
    
    if not found_url:
        print(f"{Fore.RED}[-] No GraphQL endpoints discovered.")
    
    return found_url


COMMON_PATHS = [
    "/graphql", 
    "/graphiql", 
    "/v1/graphql", 
    "/v2/graphql",
    "/api/graphql", 
    "/graphql/console", 
    "/playground", 
    "/query",
    "/api/v1/graphql"
]