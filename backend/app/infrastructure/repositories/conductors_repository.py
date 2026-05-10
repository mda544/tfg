from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import NoResultFound

from app.infrastructure.orm_models import ConductorORM
from app.api.schemas.models import ConductorCreateDTO


class ConductorsRepository:

    async def get_all(self, db: AsyncSession, owner_id: str) -> list[ConductorORM]:
        result = await db.execute(
            select(ConductorORM)
            .where(ConductorORM.owner_id == owner_id)
            .order_by(ConductorORM.name)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self, db: AsyncSession, conductor_id: str, owner_id: str
    ) -> ConductorORM:
        result = await db.execute(
            select(ConductorORM)
            .where(ConductorORM.id == conductor_id)
            .where(ConductorORM.owner_id == owner_id)
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Conductor {conductor_id} not found.")
        return obj

    async def exists(
        self, db: AsyncSession, conductor_id: str, owner_id: str
    ) -> bool:
        result = await db.execute(
            select(ConductorORM.id)
            .where(ConductorORM.id == conductor_id)
            .where(ConductorORM.owner_id == owner_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self, db: AsyncSession, owner_id: str, data: ConductorCreateDTO
    ) -> ConductorORM:
        obj = ConductorORM(owner_id=owner_id, **data.model_dump())
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def update(
        self, db: AsyncSession, conductor_id: str, owner_id: str, data: ConductorCreateDTO
    ) -> ConductorORM:
        await db.execute(
            update(ConductorORM)
            .where(ConductorORM.id == conductor_id)
            .where(ConductorORM.owner_id == owner_id)
            .values(**data.model_dump())
        )
        return await self.get_by_id(db, conductor_id, owner_id)

    async def delete(
        self, db: AsyncSession, conductor_id: str, owner_id: str
    ) -> bool:
        result = await db.execute(
            delete(ConductorORM)
            .where(ConductorORM.id == conductor_id)
            .where(ConductorORM.owner_id == owner_id)
        )
        return result.rowcount > 0


conductors_repo = ConductorsRepository()