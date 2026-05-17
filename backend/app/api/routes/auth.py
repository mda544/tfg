from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.api.schemas.models import RegisterRequestDTO, LoginRequestDTO, TokenResponseDTO
from app.services import auth_service

router = APIRouter()


@router.post("/users", response_model=TokenResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequestDTO, db: AsyncSession = Depends(get_db)):
    """Registra un usuario nuevo y devuelve el JWT directamente."""
    return await auth_service.register(db, data)


@router.post("/auth/token", response_model=TokenResponseDTO)
async def login(data: LoginRequestDTO, db: AsyncSession = Depends(get_db)):
    """Valida credenciales y devuelve el JWT."""
    return await auth_service.login(db, data)