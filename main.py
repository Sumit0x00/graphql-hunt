import json 
import requests
import argparse
from colorama import Fore, Style, init
import fuzzer as f 
import sys

def is_introspection_enabled(url):
    probe_query = {"query": "{ __schema { queryType { name } } }"}
    
    try:
        response = requests.post(url,timeout=10,json=probe_query)
        if response.status_code == 200:
            data = response.json()
            if data.get("data",{}).get("__schema"):
                return True
            
        return False
    except Exception:
        return False
    
def dump_introspection(url, filename="schema_dump.json"):
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
        response = requests.post(url,json=payload,timeout=20)
        if response.status_code == 200:
            with open(filename, "w") as file:
                json.dump(response.json(), file, indent=4)
            print(f"Schema dumped successfully to {filename}")
            intdata = response.json()
            return True, intdata
    except Exception as e:
        print(f"[-] Dump failed: {e}")
    return False, None  

def get_mutations(introspection_data):
    try:
        schema = introspection_data.get('data', {}).get('__schema', {})
        mutation_type_info = schema.get('mutationType')

        if not mutation_type_info:
            print(f"{Fore.YELLOW}[*] No mutations found in the schema.")
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
        print(f"{Fore.RED}[-] Error parsing mutations: {e}")
        return []

parser = argparse.ArgumentParser(description="GraphQL Introspection Detector")
parser.add_argument("-u", "--url", help="The target GraphQL URL", required=True)

args = parser.parse_args()

target_url = args.url
print(f"Targeting: {target_url}")

if not target_url.endswith(tuple(f.COMMON_PATHS)):
    found_url = f.find_graphql_endpoint(target_url)
    if not found_url:
        print(f"{Fore.RED}[-] Could not find a GraphQL endpoint. Try providing the path manually.")
        sys.exit()
    target_url = found_url  

if is_introspection_enabled(target_url):
    print(f"[!] Introspection is ENABLED! {Fore.RED}[Information Disclosure]{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}Starting Dump....{Style.RESET_ALL}")
    success, introspection_data = dump_introspection(target_url)  
    if success and introspection_data:
        print("Mutation Identified---")
        get_mutations(introspection_data)  
    else:
        print(f"{Fore.RED}[-] Failed to retrieve introspection data.")
else:
    print("[-] Introspection is disabled or the endpoint is protected.")