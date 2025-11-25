import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Georisk API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    
    # Earth Engine
    GEE_PROJECT_ID: str = "ee-olivaresg" # From notebook
    GEE_SERVICE_ACCOUNT_KEY_FILE: str = os.path.join(BASE_DIR, "ee-olivaresg-b7842843c247.json")

    class Config:
        env_file = ".env"

settings = Settings()
