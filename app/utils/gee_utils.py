import ee
import os
from app.core.config import settings

def init_gee():
    """Initializes Earth Engine."""
    try:
        key_file = settings.GEE_SERVICE_ACCOUNT_KEY_FILE
        if not os.path.exists(key_file):
            # Check Render secret path fallback
            render_secret = "/etc/secrets/service_account.json"
            if os.path.exists(render_secret):
                print(f"Using Render secret file at {render_secret}")
                key_file = render_secret

        if os.path.exists(key_file):
             import json
             try:
                 with open(key_file) as f:
                     key_content = json.load(f)
                 email = key_content.get('client_email')
                 if email:
                     credentials = ee.ServiceAccountCredentials(email, key_file)
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
