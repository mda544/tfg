from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.api.schemas.models import UserCreateDTO, LoginDTO, TokenDTO
from app.services import auth_service

router = APIRouter()


@router.post("/users", response_model=TokenDTO, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreateDTO, db: AsyncSession = Depends(get_db)):
    """Crea un nuevo usuario. Devuelve token de sesión."""
    return await auth_service.register(db, data)


@router.post("/sessions", response_model=TokenDTO)
async def login(data: LoginDTO, db: AsyncSession = Depends(get_db)):
    """Inicia sesión. Devuelve token que representa la sesión."""
    return await auth_service.login(db, data)
