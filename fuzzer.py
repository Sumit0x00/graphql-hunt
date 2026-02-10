import requests
from colorama import Fore, Style
import os

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

def find_graphql_endpoint(base_url, payload_file="payloads.txt"):
    print(f"{Fore.CYAN}[*] Starting endpoint fuzzing on: {base_url}")
    
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

    for path in endpoints:
        target_url = f"{base_url}{path}"
        try:
            probe = {"query": "{ __typename }"}
            response = requests.post(target_url, json=probe, headers=headers, timeout=5)
            
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if "data" in res_json or "errors" in res_json:
                        print(f"{Fore.GREEN}[+] Found valid endpoint: {target_url}")
                        return target_url
                except ValueError:
                    continue
                    
        except requests.exceptions.RequestException:
            continue
            
    print(f"{Fore.RED}[-] No GraphQL endpoints discovered.")
    return None

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