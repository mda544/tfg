"""
POST   /api/v1/rates              → calcular y persistir (201)
GET    /api/v1/rates?case_id=...  → listar resultados de un caso
GET    /api/v1/rates/{id}         → recuperar resultado
DELETE /api/v1/rates/{id}         → eliminar resultado
"""

import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.api.schemas.models import RateCalculationRequestDTO, RateCalculationResponseDTO
from app.services import rates_service

router = APIRouter()


@router.post("/", response_model=RateCalculationResponseDTO, status_code=status.HTTP_201_CREATED)
async def calculate_rates(
    req:           RateCalculationRequestDTO,
    study_case_id: Optional[str]    = None,
    db:            AsyncSession     = Depends(get_db),
):
    try:
        return await rates_service.calculate_seasonal_rates(
            req, db=db, study_case_id=study_case_id
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[RateCalculationResponseDTO])
async def list_rates(case_id: str, db: AsyncSession = Depends(get_db)):
    return await rates_service.get_by_study_case(db, case_id)


@router.get("/{rate_id}", response_model=RateCalculationResponseDTO)
async def get_rate(rate_id: str, db: AsyncSession = Depends(get_db)):
    return await rates_service.get_by_id(db, rate_id)


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate(rate_id: str, db: AsyncSession = Depends(get_db)):
    await rates_service.delete(db, rate_id)