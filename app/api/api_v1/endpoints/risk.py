from fastapi import APIRouter, HTTPException
from app.schemas.risk import RiskAnalysisRequest, RiskAnalysisResponse
from app.services.risk_analysis import generar_certificado
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_risk(request: RiskAnalysisRequest):
    try:
        logger.info(f"Analyzing risk for {request.lat}, {request.lon}")
        certificado = generar_certificado(request.lat, request.lon, request.nombre)
        return certificado
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
