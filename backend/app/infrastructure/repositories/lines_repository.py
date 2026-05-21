from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import NoResultFound
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping

from app.infrastructure.orm_models import LineORM
from app.api.schemas.models import LineCreateDTO
from app.core.utils.geo import haversine_m


def _coords_to_wkt(coordinates: list[dict]) -> str:
    pts = " ".join(f"{c.get('lon') or c.get('lng', 0)} {c['lat']}" for c in coordinates)
    return f"LINESTRING({pts})"


def _calc_length_km(coordinates: list[dict]) -> float:
    total = sum(
        haversine_m(coordinates[i], coordinates[i + 1])
        for i in range(len(coordinates) - 1)
    )
    return round(total / 1000.0, 3)


def geometry_to_geojson(obj: LineORM) -> dict:
    return mapping(to_shape(obj.geometry))


class LinesRepository:

    async def get_all(self, db: AsyncSession, owner_id: str) -> list[LineORM]:
        result = await db.execute(
            select(LineORM).where(LineORM.owner_id == owner_id).order_by(LineORM.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, db: AsyncSession, line_id: str, owner_id: str) -> LineORM:
        result = await db.execute(
            select(LineORM)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Line {line_id} not found.")
        return obj

    async def exists(self, db: AsyncSession, line_id: str, owner_id: str) -> bool:
        result = await db.execute(
            select(LineORM.id)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self, db: AsyncSession, owner_id: str, data: LineCreateDTO
    ) -> LineORM:
        obj = LineORM(
            owner_id=owner_id,
            name=data.name,
            description=data.description,
            geometry=_coords_to_wkt(data.coordinates),
            length_km=_calc_length_km(data.coordinates),
        )
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return obj

    async def update(
        self, db: AsyncSession, line_id: str, owner_id: str, data: LineCreateDTO
    ) -> LineORM:
        await db.execute(
            update(LineORM)
            .where(LineORM.id == line_id)
            .where(LineORM.owner_id == owner_id)
            .values(
                name=data.name,
                description=data.description,
                geometry=_coords_to_wkt(data.coordinates),
                length_km=_calc_length_km(data.coordinates),
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
