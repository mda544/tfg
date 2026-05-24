from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.orm_models import ElevationCacheORM


class ElevationRepository:

    def _round_coords(self, val: float) -> float:
        """Redondear a 3 decimales — precisión de ~100 m."""
        return round(val, 3)

    async def get_elevation(
        self, db: AsyncSession, lat: float, lon: float
    ) -> float | None:
        result = await db.execute(
            select(ElevationCacheORM.elevation_m)
            .where(ElevationCacheORM.lat == self._round_coords(lat))
            .where(ElevationCacheORM.lon == self._round_coords(lon))
        )
        return result.scalar_one_or_none()

    async def create_elevation(
        self, db: AsyncSession, lat: float, lon: float, elevation_m: float
    ) -> None:
        """Persiste la elevación en caché.
        Usa ON CONFLICT DO NOTHING — no sobreescribe si ya existe."""
        stmt = (
            insert(ElevationCacheORM)
            .values(
                lat=self._round_coords(lat),
                lon=self._round_coords(lon),
                elevation_m=elevation_m,
            )
            .on_conflict_do_nothing(constraint="uq_elevation_cache")
        )
        await db.execute(stmt)


elevation_repo = ElevationRepository()
