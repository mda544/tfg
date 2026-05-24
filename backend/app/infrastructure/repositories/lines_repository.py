from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import NoResultFound

from app.infrastructure.orm_models import LineORM
from app.infrastructure.mappers.lines_mapper import entity_to_wkt, orm_to_entity
from app.domain.entities import Line


async def _calc_length_km(db: AsyncSession, wkt: str) -> float:
    result = await db.execute(select(func.ST_Length(func.ST_GeogFromText(wkt))))
    return round(result.scalar() / 1000.0, 3)


def _bbox_from_coordinates(coordinates) -> dict:
    lats = [c.lat for c in coordinates]
    lons = [c.lon for c in coordinates]
    return {
        "lat_min": min(lats),
        "lat_max": max(lats),
        "lon_min": min(lons),
        "lon_max": max(lons),
    }


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

    async def create(self, db: AsyncSession, owner_id: str, entity: Line) -> Line:
        wkt = entity_to_wkt(entity)
        bbox = _bbox_from_coordinates(entity.coordinates)
        obj = LineORM(
            owner_id=owner_id,
            name=entity.name,
            description=entity.description,
            geometry=wkt,
            length_km=await _calc_length_km(db, wkt),
            n_points=len(entity.coordinates),
            bbox_lat_min=bbox["lat_min"],
            bbox_lat_max=bbox["lat_max"],
            bbox_lon_min=bbox["lon_min"],
            bbox_lon_max=bbox["lon_max"],
        )
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return orm_to_entity(obj)

    async def update(
        self, db: AsyncSession, line_id: str, owner_id: str, entity: Line
    ) -> Line:
        wkt = entity_to_wkt(entity)
        bbox = _bbox_from_coordinates(entity.coordinates)
        await db.execute(
            update(LineORM)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
            .values(
                name=entity.name,
                description=entity.description,
                geometry=wkt,
                length_km=await _calc_length_km(db, wkt),
                n_points=len(entity.coordinates),
                bbox_lat_min=bbox["lat_min"],
                bbox_lat_max=bbox["lat_max"],
                bbox_lon_min=bbox["lon_min"],
                bbox_lon_max=bbox["lon_max"],
            )
        )
        return await self.get_by_id(db, line_id, owner_id)

    async def enrich_with_elevation(
        self,
        db: AsyncSession,
        line_id: str,
        owner_id: str,
        min_elev: float,
        max_elev: float,
        avg_elev: float,
    ) -> Line:
        """Actualiza las elevaciones de la línea tras el enriquecimiento DEM."""
        await db.execute(
            update(LineORM)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
            .values(
                min_elevation_m=min_elev,
                max_elevation_m=max_elev,
                avg_elevation_m=avg_elev,
            )
        )
        return await self.get_by_id(db, line_id, owner_id)

    async def delete(self, db: AsyncSession, line_id: str, owner_id: str) -> bool:
        result = await db.execute(
            delete(LineORM)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
        )
        return result.rowcount > 0


lines_repo = LinesRepository()
