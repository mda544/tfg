from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database import AsyncSessionLocal
from app.domain.repository_interfaces import (
    ILinesRepository,
    IConductorsRepository,
    IStudyCasesRepository,
    ICalculationsRepository,
    IElevationRepository,
    IClimateRepository,
    IUsersRepository,
)
from app.infrastructure.repositories.users_repository import users_repo
from app.infrastructure.repositories.lines_repository import lines_repo
from app.infrastructure.repositories.conductors_repository import conductors_repo
from app.infrastructure.repositories.study_cases_repository import study_cases_repo
from app.infrastructure.repositories.calculations_repository import calculations_repo
from app.infrastructure.repositories.elevation_repository import elevation_repo
from app.infrastructure.repositories.climate_repository import climate_repo

_bearer = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise JWTError
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_users_repo() -> IUsersRepository:
    return users_repo


def get_lines_repo() -> ILinesRepository:
    return lines_repo


def get_conductors_repo() -> IConductorsRepository:
    return conductors_repo


def get_study_cases_repo() -> IStudyCasesRepository:
    return study_cases_repo


def get_calculations_repo() -> ICalculationsRepository:
    return calculations_repo


def get_elevation_repo() -> IElevationRepository:
    return elevation_repo


def get_climate_repo() -> IClimateRepository:
    return climate_repo
