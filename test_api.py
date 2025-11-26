import requests
import json

url = "https://georisk-api.onrender.com/api/v1/analyze"
payload = {
    "lat": -33.4489,
    "lon": -70.6693,
    "nombre": "Test Santiago"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
