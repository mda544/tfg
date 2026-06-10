from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.api.schemas.models import RateCreateDTO, RateResultResponseDTO
from app.services import rates_service

router = APIRouter()


@router.post(
    "/", response_model=RateResultResponseDTO, status_code=status.HTTP_201_CREATED
)
async def create_rate(
    req: RateCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await rates_service.create(db, req, user_id)


@router.get("/{rate_id}", response_model=RateResultResponseDTO)
async def get_rate(
    rate_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await rates_service.get_by_id(db, rate_id, user_id)


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate(
    rate_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    await rates_service.delete(db, rate_id, user_id)
