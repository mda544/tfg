from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.infrastructure.repositories.users_repository import users_repo
from app.infrastructure.orm_models import UserORM
from app.api.schemas.models import UserCreateDTO, LoginDTO, TokenDTO
from app.infrastructure.mappers.auth_mapper import user_to_token_dto

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def _create_token(user_id: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_min)
    payload = {"sub": user_id, "username": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def register(db: AsyncSession, data: UserCreateDTO) -> TokenDTO:
    if await users_repo.exists_by_username(db, data.username):
        raise HTTPException(status_code=409, detail="Username already registered.")
    user = await users_repo.create(db, data.username, _hash_password(data.password))
    return user_to_token_dto(user, _create_token(user.id, user.username))


async def login(db: AsyncSession, data: LoginDTO) -> TokenDTO:
    user = await users_repo.get_by_username(db, data.username)
    if user is None or not _verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return user_to_token_dto(user, _create_token(user.id, user.username))
