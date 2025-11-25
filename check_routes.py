import requests
import json

try:
    response = requests.get("http://127.0.0.1:8000/api/v1/openapi.json")
    if response.status_code == 200:
        schema = response.json()
        print("Paths found:")
        for path in schema.get('paths', {}):
            print(path)
    else:
        print(f"Failed to get openapi.json: {response.status_code}")
        # Try root openapi just in case
        response = requests.get("http://127.0.0.1:8000/openapi.json")
        if response.status_code == 200:
            schema = response.json()
            print("Paths found (root):")
            for path in schema.get('paths', {}):
                print(path)
except Exception as e:
    print(f"Error: {e}")
