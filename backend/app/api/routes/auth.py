from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_users_repo
from app.api.schemas.models import UserCreateDTO, LoginDTO, TokenDTO
from app.domain.repository_interfaces import IUsersRepository
from app.services import auth_service

router = APIRouter()
from app.core.limiter import limiter


@router.post("/users", response_model=TokenDTO, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    data: UserCreateDTO,
    db: AsyncSession = Depends(get_db),
    repo: IUsersRepository = Depends(get_users_repo),
):
    return await auth_service.register(db, data, repo)


@router.post("/sessions", response_model=TokenDTO)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginDTO,
    db: AsyncSession = Depends(get_db),
    repo: IUsersRepository = Depends(get_users_repo),
):
    return await auth_service.login(db, data, repo)
