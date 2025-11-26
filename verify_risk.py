import sys
import os
import json
# Add project root to path
sys.path.append(os.getcwd())

from app.services.risk_analysis import generar_certificado
from app.utils.gee_utils import init_gee

def test_risk():
    try:
        init_gee()
        print("GEE Initialized")
        
        # Santiago
        lat = -33.4489
        lon = -70.6693
        
        print(f"Analyzing {lat}, {lon}...")
        cert = generar_certificado(lat, lon, "Test Santiago")
        
        print(json.dumps(cert, indent=2, default=str))
        
        # Check for new fields
        found_suelo = False
        found_fuego = False
        
        for ind in cert['detalle_indicadores']:
            if ind['id'] == 'suelo':
                if 'detalles' in ind:
                    print("Found suelo detalles:", ind['detalles'])
                    found_suelo = True
            if ind['id'] == 'fuego':
                if 'detalles' in ind:
                    print("Found fuego detalles:", ind['detalles'])
                    found_fuego = True
                    
        if found_suelo and found_fuego:
            print("SUCCESS: New fields found.")
        else:
            print("FAILURE: New fields not found.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_risk()
