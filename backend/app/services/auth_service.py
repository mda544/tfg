from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.users_repository import users_repo
from app.infrastructure.orm_models import UserORM
from app.api.schemas.models import RegisterRequestDTO, LoginRequestDTO, TokenResponseDTO

# bcrypt para hashear contraseñas
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def _create_token(user_id: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_min)
    payload = {
        "sub":      user_id,
        "username": username,
        "exp":      expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def register(db: AsyncSession, data: RegisterRequestDTO) -> TokenResponseDTO:
    if await users_repo.exists_by_username(db, data.username):
        raise HTTPException(status_code=409, detail="Nombre de usuario ya en uso.")

    user  = await users_repo.create(db, data.username, _hash_password(data.password))
    token = _create_token(user.id, user.username)

    return TokenResponseDTO(
        access_token = token,
        user_id      = user.id,
        username     = user.username,
    )


async def login(db: AsyncSession, data: LoginRequestDTO) -> TokenResponseDTO:
    user = await users_repo.get_by_username(db, data.username)

    if user is None or not _verify_password(data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos.",
        )

    token = _create_token(user.id, user.username)
    return TokenResponseDTO(
        access_token = token,
        user_id      = user.id,
        username     = user.username,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserORM:
    """
    Dependencia FastAPI que extrae y valida el usuario del JWT.
    Se inyecta en todos los endpoints protegidos:
        current_user: UserORM = Depends(get_current_user)
    """
    try:
        payload  = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    try:
        return await users_repo.get_by_id(db, user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="User not found.")