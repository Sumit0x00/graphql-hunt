import requests
from colorama import Fore, Style

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

def find_graphql_endpoint(base_url):
    print(f"{Fore.CYAN}[*] Starting endpoint fuzzing on: {base_url}")
    
    base_url = base_url.rstrip('/')
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    for path in COMMON_PATHS:
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
            
    print(f"{Fore.RED}[-] No common GraphQL endpoints discovered.")
    return None