from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.infrastructure.orm_models import UserORM
from app.api.deps import get_current_user
from app.api.schemas.models import LineCreateDTO, LineResponseDTO
from app.services import lines_service

router = APIRouter()


@router.get("/", response_model=list[LineResponseDTO])
async def list_lines(
    db: AsyncSession = Depends(get_db), user: UserORM = Depends(get_current_user)
):
    return await lines_service.get_all(db, user.id)


@router.post("/", response_model=LineResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_line(
    data: LineCreateDTO,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await lines_service.create(db, data, user.id)


@router.get("/{line_id}", response_model=LineResponseDTO)
async def get_line(
    line_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await lines_service.get_by_id(db, line_id, user.id)


@router.put("/{line_id}", response_model=LineResponseDTO)
async def update_line(
    line_id: str,
    data: LineCreateDTO,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await lines_service.update(db, line_id, data, user.id)


@router.delete("/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_line(
    line_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    await lines_service.delete(db, line_id, user.id)
