import json 
import requests
import argparse

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
    
def dump_introspection(url , filename="schema_dump.json"):
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
            with open(filename, "w") as f:
                json.dump(response.json(), f, indent=4)
            print(f"Schema dumped successfully to {filename}")
            return True
    except Exception as e:
        print(f"[-] Dump failed: {e}")
    return False

parser = argparse.ArgumentParser(description="GraphQL Introspection Detector")
parser.add_argument("-u", "--url", help="The target GraphQL URL", required=True)

args = parser.parse_args()

target_url = args.url
print(f"Targeting: {target_url}")

if is_introspection_enabled(target_url):
    print("[!] Introspection is ENABLED! Starting dump...")
    dump_introspection(target_url)
else:
    print("[-] Introspection is disabled or the endpoint is protected.")