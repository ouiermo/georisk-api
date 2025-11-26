import requests
import json

# URL de tu API desplegada
API_URL = "https://georisk-api.onrender.com/api/v1/analyze"

# Datos de prueba (Santiago, Chile)
payload = {
    "lat": -33.4489,
    "lon": -70.6693,
    "nombre": "Santiago Centro"
}

print(f"Enviando petición a: {API_URL}...")

try:
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Análisis Exitoso:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Error {response.status_code}:")
        print(response.text)

except Exception as e:
    print(f"\n❌ Error de conexión: {e}")
