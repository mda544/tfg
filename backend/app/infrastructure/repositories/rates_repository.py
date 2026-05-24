from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from app.infrastructure.orm_models import RateResultORM
from app.infrastructure.mappers.rates_mapper import (
    orm_to_entity,
    weather_input_vo_to_orm,
)
from app.infrastructure.mappers.segments_mapper import (
    entity_to_orm as segment_entity_to_orm,
)
from app.domain.entities import RateResult


class RatesRepository:

    async def create(self, db: AsyncSession, entity: RateResult) -> RateResult:
        orm_result = RateResultORM(
            id=entity.id,
            study_case_id=entity.study_case_id,
            conductor_id=entity.conductor_id,
            climate_source=entity.climate_source,
            elevation_source=entity.elevation_source,
            n_segments=entity.n_segments,
            rate_summer=entity.rates_by_season.get("verano", 0.0),
            rate_autumn=entity.rates_by_season.get("otono", 0.0),
            rate_winter=entity.rates_by_season.get("invierno", 0.0),
            rate_spring=entity.rates_by_season.get("primavera", 0.0),
            design_rate=entity.design_rate,
            warnings=entity.warnings or [],
        )
        db.add(orm_result)
        await db.flush()

        for wi in entity.weather_inputs:
            db.add(weather_input_vo_to_orm(wi, entity.id))

        for segment in entity.segments:
            db.add(segment_entity_to_orm(segment, entity.id))

        await db.flush()
        return await self.get_by_id(db, entity.id)

    async def get_by_id(self, db: AsyncSession, result_id: str) -> RateResult:
        result = await db.execute(
            select(RateResultORM)
            .options(
                selectinload(RateResultORM.conductor),
                selectinload(RateResultORM.weather_inputs),
                selectinload(RateResultORM.segments),
            )
            .where(RateResultORM.id == result_id)
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Rate result {result_id} not found.")
        return orm_to_entity(obj)

    async def get_by_study_case(
        self, db: AsyncSession, case_id: str
    ) -> list[RateResult]:
        result = await db.execute(
            select(RateResultORM)
            .options(
                selectinload(RateResultORM.conductor),
                selectinload(RateResultORM.weather_inputs),
                selectinload(RateResultORM.segments),
            )
            .where(RateResultORM.study_case_id == case_id)
            .order_by(RateResultORM.created_at.desc())
        )
        return [orm_to_entity(o) for o in result.scalars().all()]

    async def delete(self, db: AsyncSession, result_id: str) -> bool:
        result = await db.execute(
            delete(RateResultORM).where(RateResultORM.id == result_id)
        )
        return result.rowcount > 0


rates_repo = RatesRepository()
