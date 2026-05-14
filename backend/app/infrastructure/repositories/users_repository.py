from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from app.infrastructure.orm_models import UserORM


class UsersRepository:

    async def get_by_id(self, db: AsyncSession, user_id: str) -> UserORM:
        result = await db.execute(
            select(UserORM).where(UserORM.id == user_id)
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"User {user_id} not found.")
        return obj

    async def get_by_username(self, db: AsyncSession, username: str) -> UserORM | None:
        result = await db.execute(
            select(UserORM).where(UserORM.username == username)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, username: str, hashed_password: str) -> UserORM:
        obj = UserORM(username=username, password=hashed_password)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def exists_by_username(self, db: AsyncSession, username: str) -> bool:
        result = await db.execute(
            select(UserORM.id).where(UserORM.username == username)
        )
        return result.scalar_one_or_none() is not None


users_repo = UsersRepository()