from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.api.schemas.models import ConductorCreateDTO, ConductorResponseDTO
from app.services import conductors_service

router = APIRouter()


@router.get("/", response_model=list[ConductorResponseDTO])
async def list_conductors(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await conductors_service.get_all(db, user_id)


@router.post(
    "/", response_model=ConductorResponseDTO, status_code=status.HTTP_201_CREATED
)
async def create_conductor(
    data: ConductorCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await conductors_service.create(db, data, user_id)


@router.get("/{conductor_id}", response_model=ConductorResponseDTO)
async def get_conductor(
    conductor_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await conductors_service.get_by_id(db, conductor_id, user_id)


@router.put("/{conductor_id}", response_model=ConductorResponseDTO)
async def update_conductor(
    conductor_id: str,
    data: ConductorCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    return await conductors_service.update(db, conductor_id, data, user_id)


@router.delete("/{conductor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conductor(
    conductor_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    await conductors_service.delete(db, conductor_id, user_id)
