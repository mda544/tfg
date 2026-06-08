import re
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.core.config import settings
from app.infrastructure.repositories.users_repository import users_repo
from app.api.schemas.models import UserCreateDTO, LoginDTO, TokenDTO
from app.infrastructure.mappers.auth_mapper import user_to_token_dto

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def _create_token(user_id: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_min)
    payload = {"sub": user_id, "username": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _validate_credentials(username: str, password: str) -> None:
    """Valida las reglas de negocio de usuario y contraseña.
    Se ejecuta en el servicio — no en el DTO — para mantener los DTOs
    como estructuras de datos puras sin lógica."""

    if len(username) < 3:
        raise HTTPException(
            422, detail="El nombre de usuario debe tener al menos 3 caracteres."
        )
    if len(username) > 64:
        raise HTTPException(
            422, detail="El nombre de usuario no puede superar los 64 caracteres."
        )
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise HTTPException(
            422,
            detail="El nombre de usuario solo puede contener letras, números, guiones y guiones bajos.",
        )

    if len(password) < 8:
        raise HTTPException(
            422, detail="La contraseña debe tener al menos 8 caracteres."
        )
    if not any(c.isupper() for c in password):
        raise HTTPException(
            422, detail="La contraseña debe contener al menos una letra mayúscula."
        )
    if not any(c.islower() for c in password):
        raise HTTPException(
            422, detail="La contraseña debe contener al menos una letra minúscula."
        )
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            422, detail="La contraseña debe contener al menos un número."
        )


async def register(db: AsyncSession, data: UserCreateDTO) -> TokenDTO:
    _validate_credentials(data.username, data.password)
    if await users_repo.exists_by_username(db, data.username):
        raise HTTPException(409, detail="Username already registered.")
    user = await users_repo.create(db, data.username, _hash_password(data.password))
    return user_to_token_dto(user, _create_token(user.id, user.username))


async def login(db: AsyncSession, data: LoginDTO) -> TokenDTO:
    user = await users_repo.get_by_username(db, data.username)
    if user is None or not _verify_password(data.password, user.password):
        raise HTTPException(401, detail="Invalid username or password.")
    return user_to_token_dto(user, _create_token(user.id, user.username))
