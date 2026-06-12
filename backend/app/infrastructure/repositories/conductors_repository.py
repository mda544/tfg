from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.exc import NoResultFound

from app.infrastructure.db_exceptions import handle_db_exceptions
from app.infrastructure.orm_models import ConductorORM
from app.infrastructure.mappers.conductors_mapper import entity_to_orm, orm_to_entity
from app.domain.entities import Conductor


class ConductorsRepository:

    async def get_all(self, db: AsyncSession, owner_id: str) -> list[Conductor]:
        result = await db.execute(
            select(ConductorORM)
            .where(
                or_(
                    ConductorORM.owner_id == owner_id,
                    ConductorORM.owner_id.is_(None),
                )
            )
            .order_by(ConductorORM.owner_id.is_(None).desc(), ConductorORM.name)
        )
        return [orm_to_entity(o) for o in result.scalars().all()]

    async def get_by_id(
        self, db: AsyncSession, conductor_id: str, owner_id: str
    ) -> Conductor:
        result = await db.execute(
            select(ConductorORM).where(
                and_(
                    ConductorORM.id == conductor_id,
                    or_(
                        ConductorORM.owner_id == owner_id,
                        ConductorORM.owner_id.is_(None),
                    ),
                )
            )
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Conductor {conductor_id} not found.")
        return orm_to_entity(obj)

    async def exists(self, db: AsyncSession, conductor_id: str, owner_id: str) -> bool:
        result = await db.execute(
            select(ConductorORM.id)
            .where(ConductorORM.id == conductor_id)
            .where(ConductorORM.owner_id == owner_id)
        )
        return result.scalar_one_or_none() is not None

    @handle_db_exceptions
    async def create(
        self, db: AsyncSession, owner_id: str, entity: Conductor
    ) -> Conductor:
        obj = entity_to_orm(entity, owner_id)
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return orm_to_entity(obj)

    @handle_db_exceptions
    async def update(
        self, db: AsyncSession, conductor_id: str, owner_id: str, entity: Conductor
    ) -> Conductor:
        await db.execute(
            update(ConductorORM)
            .where(ConductorORM.id == conductor_id)
            .where(ConductorORM.owner_id == owner_id)
            .values(
                name=entity.name,
                description=entity.description,
                diameter_mm=entity.diameter_mm,
                r_ac_75_ohm_km=entity.r_ac_75_ohm_km,
                r_ac_25_ohm_km=entity.r_ac_25_ohm_km,
                emissivity=entity.emissivity,
                absorptivity=entity.absorptivity,
                max_temp_c=entity.max_temp_c,
            )
        )
        return await self.get_by_id(db, conductor_id, owner_id)

    @handle_db_exceptions
    async def delete(self, db: AsyncSession, conductor_id: str, owner_id: str) -> bool:
        result = await db.execute(
            delete(ConductorORM)
            .where(ConductorORM.id == conductor_id)
            .where(ConductorORM.owner_id == owner_id)
        )
        return result.rowcount > 0


conductors_repo = ConductorsRepository()
