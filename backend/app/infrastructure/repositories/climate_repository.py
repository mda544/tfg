from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.infrastructure.orm_models import ClimateCacheORM
from app.domain.entities import SeasonalPercentiles
from app.domain.types import Season


class ClimateRepository:

    def _round_coords(self, lat: float, lon: float) -> tuple[float, float]:
        """Redondear a 0.1° — resolución de ~9-11 km (ERA5 / Open-Meteo)."""
        return round(lat, 1), round(lon, 1)

    async def get_climate(
        self, db: AsyncSession, lat: float, lon: float, source: str
    ) -> dict[Season, SeasonalPercentiles] | None:
        lat_r, lon_r = self._round_coords(lat, lon)
        result = await db.execute(
            select(ClimateCacheORM)
            .where(ClimateCacheORM.lat    == lat_r)
            .where(ClimateCacheORM.lon    == lon_r)
            .where(ClimateCacheORM.source == source)
        )
        rows = result.scalars().all()
        if len(rows) < 4:
            return None

        return {
            row.season: SeasonalPercentiles(
                season            = row.season,
                lat               = row.lat,
                lon               = row.lon,
                temp_p90_c        = row.temp_p90_c,
                temp_p50_c        = row.temp_p50_c,
                temp_p10_c        = row.temp_p10_c,
                wind_p10_ms       = row.wind_p10_ms,
                wind_p50_ms       = row.wind_p50_ms,
                wind_p90_ms       = row.wind_p90_ms,
                radiation_p50_wm2 = row.radiation_p50_wm2,
                radiation_p90_wm2 = row.radiation_p90_wm2,
                n_hours           = row.n_hours,
                source            = row.source,
                years_covered     = row.years_covered,
            )
            for row in rows
        }

    async def save_climate(
        self, db: AsyncSession, percentiles: dict[Season, SeasonalPercentiles]
    ) -> None:
        for season, p in percentiles.items():
            lat_r, lon_r = self._round_coords(p.lat, p.lon)
            stmt = insert(ClimateCacheORM).values(
                lat               = lat_r,
                lon               = lon_r,
                source            = p.source,
                season            = season,
                temp_p90_c        = p.temp_p90_c,
                temp_p50_c        = p.temp_p50_c,
                temp_p10_c        = p.temp_p10_c,
                wind_p10_ms       = p.wind_p10_ms,
                wind_p50_ms       = p.wind_p50_ms,
                wind_p90_ms       = p.wind_p90_ms,
                radiation_p50_wm2 = p.radiation_p50_wm2,
                radiation_p90_wm2 = p.radiation_p90_wm2,
                n_hours           = p.n_hours,
                years_covered     = p.years_covered,
            ).on_conflict_do_nothing(constraint="uq_climate_cache")
            await db.execute(stmt)


climate_repo = ClimateRepository()
