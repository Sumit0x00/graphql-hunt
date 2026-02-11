import json 
import requests
import argparse
from colorama import Fore, Style, init
import fuzzer as f 
import sys
from auth_handler import create_auth_handler

# Initialize colorama
init(autoreset=True)

def is_introspection_enabled(url, auth_handler):
    probe_query = {"query": "{ __schema { queryType { name } } }"}
    
    try:
        headers = auth_handler.get_headers()
        cookies = auth_handler.get_cookies()
        
        response = requests.post(
            url,
            timeout=10,
            json=probe_query,
            headers=headers,
            cookies=cookies
        )
        
        if response.status_code == 401:
            print(f"{Fore.RED}[✗] 401 Unauthorized - Invalid credentials{Style.RESET_ALL}")
            return False
        elif response.status_code == 403:
            print(f"{Fore.YELLOW}[!] 403 Forbidden - Insufficient permissions{Style.RESET_ALL}")
            return False
        elif response.status_code == 200:
            data = response.json()
            if data.get("data",{}).get("__schema"):
                return True
            
        return False
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}{Style.RESET_ALL}")
        return False
    
def dump_introspection(url, auth_handler, filename="schema_dump.json"):
    full_query = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          ...FullType
        }
      }
    }
    fragment FullType on __Type {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args { ...InputValue }
        type { ...TypeRef }
      }
      inputFields { ...InputValue }
      enumValues { name description }
      possibleTypes { ...TypeRef }
    }
    fragment InputValue on __InputValue {
      name
      description
      type { ...TypeRef }
      defaultValue
    }
    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
        }
      }
    }
    """
    payload = {"query": full_query}
    
    try:
        headers = auth_handler.get_headers()
        cookies = auth_handler.get_cookies()
        
        response = requests.post(
            url,
            json=payload,
            timeout=20,
            headers=headers,
            cookies=cookies
        )
        
        if response.status_code == 401:
            print(f"{Fore.RED}[✗] 401 Unauthorized - Invalid credentials{Style.RESET_ALL}")
            return False, None
        elif response.status_code == 403:
            print(f"{Fore.YELLOW}[!] 403 Forbidden - Insufficient permissions{Style.RESET_ALL}")
            return False, None
        elif response.status_code == 200:
            with open(filename, "w") as file:
                json.dump(response.json(), file, indent=4)
            print(f"{Fore.GREEN}Schema dumped successfully to {filename}{Style.RESET_ALL}")
            intdata = response.json()
            return True, intdata
    except Exception as e:
        print(f"{Fore.RED}[-] Dump failed: {e}{Style.RESET_ALL}")
    
    return False, None


def get_mutations(introspection_data):
    try:
        schema = introspection_data.get('data', {}).get('__schema', {})
        mutation_type_info = schema.get('mutationType')

        if not mutation_type_info:
            print(f"{Fore.YELLOW}[*] No mutations found in the schema.{Style.RESET_ALL}")
            return []

        mutation_name = mutation_type_info.get('name')
        types = schema.get('types', [])

        for gql_type in types:
            if gql_type.get('name') == mutation_name:
                fields = gql_type.get('fields', [])
                
                mutation_list = [f['name'] for f in fields]
                
                if mutation_list:
                    print(f"{Fore.MAGENTA}{Style.BRIGHT}\n[!] DISCOVERED {len(mutation_list)} MUTATIONS:")
                    for m in mutation_list:
                        if any(word in m.lower() for word in ['delete', 'update', 'remove', 'admin', 'password']):
                            print(f"  {Fore.RED}-> {m} (SENSITIVE)")
                        else:
                            print(f"  {Fore.WHITE}-> {m}")
                    return mutation_list
        
        return []

    except Exception as e:
        print(f"{Fore.RED}[-] Error parsing mutations: {e}{Style.RESET_ALL}")
        return []


# Argument parser
parser = argparse.ArgumentParser(description="GraphQL Introspection Detector with Authentication Support")
parser.add_argument("-u", "--url", help="The target GraphQL URL", required=True)
parser.add_argument("-o", "--output", help="Output filename for schema dump", default="schema_dump.json")

# Authentication arguments
auth_group = parser.add_argument_group('Authentication Options')
auth_group.add_argument("-t", "--token", help="Bearer token (JWT) for authentication", default=None)
auth_group.add_argument("-c", "--cookies", help="Session cookies (format: 'key1=value1; key2=value2')", default=None)

args = parser.parse_args()

target_url = args.url
output_file = args.output

print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
print(f"{Fore.CYAN}GraphQL Reconnaissance Tool{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
print(f"{Fore.WHITE}Targeting: {target_url}{Style.RESET_ALL}\n")

# Setup authentication
auth_type = None
if args.token:
    auth_type = "bearer"
elif args.cookies:
    auth_type = "cookie"

auth_handler = create_auth_handler(
    auth_type=auth_type,
    token=args.token,
    cookies=args.cookies
)

# Endpoint discovery
if not target_url.endswith(tuple(f.COMMON_PATHS)):
    found_url = f.find_graphql_endpoint(target_url)
    if not found_url:
        print(f"{Fore.RED}[-] Could not find a GraphQL endpoint. Try providing the path manually.{Style.RESET_ALL}")
        sys.exit(1)
    target_url = found_url

# Validate authentication if provided
if auth_handler.is_authenticated():
    is_valid, message = auth_handler.validate_auth(target_url)
    print(message)
    if not is_valid:
        sys.exit(1)
else:
    print(f"{Fore.YELLOW}[*] No authentication provided - testing unauthenticated endpoint{Style.RESET_ALL}\n")

# Check introspection
if is_introspection_enabled(target_url, auth_handler):
    print(f"{Fore.GREEN}[!] Introspection is ENABLED! {Fore.RED}[Information Disclosure]{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}Starting Schema Dump....{Style.RESET_ALL}")
    
    success, introspection_data = dump_introspection(target_url, auth_handler, output_file)
    
    if success and introspection_data:
        print(f"\n{Fore.CYAN}Analyzing Mutations...{Style.RESET_ALL}")
        get_mutations(introspection_data)
    else:
        print(f"{Fore.RED}[-] Failed to retrieve introspection data.{Style.RESET_ALL}")
else:
    print(f"{Fore.YELLOW}[-] Introspection is disabled or the endpoint is protected.{Style.RESET_ALL}")

print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
print(f"{Fore.GREEN}Scan Complete!{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")