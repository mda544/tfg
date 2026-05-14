from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import NoResultFound
from geoalchemy2.elements import WKTElement

from app.infrastructure.orm_models import RateResultORM, SegmentORM


def _point_to_wkt(point: dict) -> str:
    return f"POINT({point['lon']} {point['lat']})"


def _line_to_wkt(start: dict, end: dict) -> str:
    return (
        f"LINESTRING({start['lon']} {start['lat']}, "
        f"{end['lon']} {end['lat']})"
    )


class RatesRepository:

    async def save(self, db: AsyncSession, result: dict) -> RateResultORM:
        orm_result = RateResultORM(
            id                 = result["id"],
            study_case_id      = result.get("study_case_id"),
            n_segments         = result["n_segments"],
            design_rate_a      = result["design_rate_a"],
            rates_by_season    = result["rates_by_season"],
            route_info         = result["route_info"],
            warnings           = result.get("warnings", []),
            conductor_snapshot = result["conductor"],
            segments_data      = result["segments"],  
        )
        db.add(orm_result)

        for seg in result["segments"]:
            rates   = seg["rates"]
            orm_seg = SegmentORM(
                rate_result_id = result["id"],
                segment_id     = seg["segment_id"],
                index          = seg.get("index", 0),
                mid_point      = WKTElement(_point_to_wkt(seg["mid_point"]),  srid=4326),
                geometry       = WKTElement(_line_to_wkt(seg["start_point"], seg["end_point"]), srid=4326),
                length_km      = seg["length_km"],
                elevation_m    = seg["elevation_m"],
                azimuth_deg    = seg.get("azimuth_deg", 90.0),
                rate_summer_a  = rates.get("verano",    0.0),
                rate_autumn_a  = rates.get("otono",     0.0),
                rate_winter_a  = rates.get("invierno",  0.0),
                rate_spring_a  = rates.get("primavera", 0.0),
                design_rate_a  = seg["design_rate_a"],
                details        = seg["details"],
            )
            db.add(orm_seg)

        await db.flush()
        await db.refresh(orm_result)
        return orm_result

    async def get_by_id(self, db: AsyncSession, result_id: str) -> RateResultORM:
        result = await db.execute(
            select(RateResultORM).where(RateResultORM.id == result_id)
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Rate result {result_id} not found.")
        return obj

    async def get_by_study_case(
        self, db: AsyncSession, case_id: str
    ) -> list[RateResultORM]:
        result = await db.execute(
            select(RateResultORM)
            .where(RateResultORM.study_case_id == case_id)
            .order_by(RateResultORM.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, db: AsyncSession, result_id: str) -> bool:
        result = await db.execute(
            delete(RateResultORM).where(RateResultORM.id == result_id)
        )
        return result.rowcount > 0


rates_repo = RatesRepository()