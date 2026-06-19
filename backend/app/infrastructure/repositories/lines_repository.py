from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import NoResultFound

from app.infrastructure.db_exceptions import handle_db_exceptions
from app.infrastructure.orm_models import LineORM
from app.infrastructure.mappers.lines_mapper import (
    entity_to_orm,
    entity_to_geometry,
    orm_to_entity,
)
from app.domain.entities import Line


class LinesRepository:

    async def get_all(self, db: AsyncSession, owner_id: str) -> list[Line]:
        result = await db.execute(
            select(LineORM).where(LineORM.owner_id == owner_id).order_by(LineORM.name)
        )
        return [orm_to_entity(o) for o in result.scalars().all()]

    async def get_by_id(self, db: AsyncSession, line_id: str, owner_id: str) -> Line:
        result = await db.execute(
            select(LineORM)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Line {line_id} not found.")
        return orm_to_entity(obj)

    async def exists(self, db: AsyncSession, line_id: str, owner_id: str) -> bool:
        result = await db.execute(
            select(LineORM.id)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
        )
        return result.scalar_one_or_none() is not None

    @handle_db_exceptions
    async def create(self, db: AsyncSession, owner_id: str, entity: Line) -> Line:
        obj = entity_to_orm(entity, owner_id)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return orm_to_entity(obj)

    @handle_db_exceptions
    async def update(
        self, db: AsyncSession, line_id: str, owner_id: str, entity: Line
    ) -> Line:
        await db.execute(
            update(LineORM)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
            .values(
                name=entity.name,
                description=entity.description,
                geometry=entity_to_geometry(entity),
                length_km=entity.length_km,
                n_points=entity.n_points,
                bbox_lat_min=entity.bbox_lat_min,
                bbox_lat_max=entity.bbox_lat_max,
                bbox_lon_min=entity.bbox_lon_min,
                bbox_lon_max=entity.bbox_lon_max,
            )
        )
        return await self.get_by_id(db, line_id, owner_id)

    @handle_db_exceptions
    async def delete(self, db: AsyncSession, line_id: str, owner_id: str) -> bool:
        result = await db.execute(
            delete(LineORM)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
        )
        return result.rowcount > 0


lines_repo = LinesRepository()
