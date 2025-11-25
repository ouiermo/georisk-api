from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.api_v1.endpoints import risk
from app.utils.gee_utils import init_gee

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_gee()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(risk.router, prefix=settings.API_V1_STR, tags=["risk"])

@app.get("/")
def root():
    return {"message": "Welcome to Georisk API"}
