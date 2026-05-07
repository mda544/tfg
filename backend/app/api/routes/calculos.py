import traceback
from fastapi import APIRouter, HTTPException
from app.api.schemas.models import CalculoRequest, CalculoResponse
from app.services import calculos_service

router = APIRouter()


@router.post("/rates-estacionales", response_model=CalculoResponse, status_code=201)
async def calcular_rates_estacionales(req: CalculoRequest):
    try:
        return await calculos_service.calcular_rates_estacionales(req)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
