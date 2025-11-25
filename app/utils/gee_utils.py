import ee
import os
from app.core.config import settings

def init_gee():
    """Initializes Earth Engine."""
    try:
        if os.path.exists(settings.GEE_SERVICE_ACCOUNT_KEY_FILE):
             import json
             try:
                 with open(settings.GEE_SERVICE_ACCOUNT_KEY_FILE) as f:
                     key_content = json.load(f)
                 email = key_content.get('client_email')
                 if email:
                     credentials = ee.ServiceAccountCredentials(email, settings.GEE_SERVICE_ACCOUNT_KEY_FILE)
                     ee.Initialize(credentials)
                     print("Earth Engine initialized successfully with Service Account.")
                     return
             except Exception as e:
                 print(f"Error loading service account: {e}")
        
        # Fallback/Default initialization
        try:
            ee.Initialize(project=settings.GEE_PROJECT_ID)
        except Exception:
            ee.Authenticate()
            ee.Initialize(project=settings.GEE_PROJECT_ID)
            
        print("Earth Engine initialized successfully.")
    except Exception as e:
        print(f"Error initializing Earth Engine: {e}")
        raise e
