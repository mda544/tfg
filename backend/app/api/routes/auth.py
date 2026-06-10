from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_db
from app.api.schemas.models import UserCreateDTO, LoginDTO, TokenDTO
from app.services import auth_service

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/users", response_model=TokenDTO, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    data: UserCreateDTO,
    db: AsyncSession = Depends(get_db),
):
    
    return await auth_service.register(db, data)


@router.post("/sessions", response_model=TokenDTO)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginDTO,
    db: AsyncSession = Depends(get_db),
):
    
    return await auth_service.login(db, data)