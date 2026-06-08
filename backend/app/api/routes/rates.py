import logging
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.infrastructure.orm_models import UserORM
from app.api.deps import get_current_user
from app.api.schemas.models import RateCreateDTO, RateResultResponseDTO
from app.services import rates_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/", response_model=RateResultResponseDTO, status_code=status.HTTP_201_CREATED
)
async def create_rate(
    req: RateCreateDTO,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    try:
        return await rates_service.create(db, req, user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in create_rate: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor. Contacte con el administrador.",
        )


@router.get("/{rate_id}", response_model=RateResultResponseDTO)
async def get_rate(
    rate_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await rates_service.get_by_id(db, rate_id)


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate(
    rate_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    await rates_service.delete(db, rate_id)