from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.api.schemas.models import (
    CalculationCreateDTO,
    CalculationResponseDTO,
)
from app.services import calculations_service

router = APIRouter()


@router.get("/", response_model=list[CalculationResponseDTO])
async def list_calculations(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await calculations_service.get_by_study_case(db, case_id, user_id)


@router.post(
    "/", response_model=CalculationResponseDTO, status_code=status.HTTP_201_CREATED
)
async def create_calculation(
    case_id: str,
    req: CalculationCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    req.study_case_id = case_id
    return await calculations_service.create(db, req, user_id)


@router.get("/{calc_id}", response_model=CalculationResponseDTO)
async def get_calculation(
    case_id: str,
    calc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await calculations_service.get_by_id(db, calc_id, case_id, user_id)


@router.delete("/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calculation(
    case_id: str,
    calc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    await calculations_service.delete(db, calc_id, case_id, user_id)
