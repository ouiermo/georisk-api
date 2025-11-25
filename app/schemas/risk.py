from pydantic import BaseModel
from typing import Optional

class RiskAnalysisRequest(BaseModel):
    lat: float
    lon: float
    nombre: Optional[str] = "Ubicación Solicitada"

class RiskAnalysisResponse(BaseModel):
    meta: dict
    propiedad: dict
    resumen_ejecutivo: dict
    detalle_indicadores: list
    legal: dict
