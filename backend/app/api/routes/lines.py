from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_lines_repo
from app.api.schemas.models import LineCreateDTO, LineResponseDTO
from app.domain.repository_interfaces import ILinesRepository
from app.services import lines_service

router = APIRouter()


@router.get("/", response_model=list[LineResponseDTO])
async def list_lines(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: ILinesRepository = Depends(get_lines_repo),
):
    return await lines_service.get_all(db, user_id, repo)


@router.post("/", response_model=LineResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_line(
    data: LineCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: ILinesRepository = Depends(get_lines_repo),
):
    return await lines_service.create(db, data, user_id, repo)


@router.get("/{line_id}", response_model=LineResponseDTO)
async def get_line(
    line_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: ILinesRepository = Depends(get_lines_repo),
):
    return await lines_service.get_by_id(db, line_id, user_id, repo)


@router.put("/{line_id}", response_model=LineResponseDTO)
async def update_line(
    line_id: str,
    data: LineCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: ILinesRepository = Depends(get_lines_repo),
):
    return await lines_service.update(db, line_id, data, user_id, repo)


@router.delete("/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_line(
    line_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: ILinesRepository = Depends(get_lines_repo),
):
    await lines_service.delete(db, line_id, user_id, repo)
