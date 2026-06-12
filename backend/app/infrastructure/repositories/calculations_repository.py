from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from app.infrastructure.orm_models import CalculationORM, SeasonResultORM, StudyCaseORM
from app.infrastructure.mappers.calculations_mapper import orm_to_entity
from app.infrastructure.mappers.season_results_mapper import (
    entity_to_orm as season_result_entity_to_orm,
)
from app.infrastructure.mappers.segments_mapper import (
    entity_to_orm as segment_entity_to_orm,
)
from app.domain.entities import Calculation

_EAGER = [
    selectinload(CalculationORM.season_results).selectinload(SeasonResultORM.segments)
]


class CalculationsRepository:

    async def _get_orm(
        self, db: AsyncSession, calc_id: str, user_id: str | None = None
    ) -> CalculationORM:
        """Carga el ORM con todos sus hijos. Verifica propiedad mediante
        JOIN con study_cases si se proporciona user_id."""
        q = select(CalculationORM).options(*_EAGER).where(CalculationORM.id == calc_id)
        if user_id is not None:
            q = q.join(
                StudyCaseORM,
                CalculationORM.study_case_id == StudyCaseORM.id,
            ).where(StudyCaseORM.owner_id == user_id)

        result = await db.execute(q)
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Calculation {calc_id} not found.")
        return obj

    async def create(self, db: AsyncSession, entity: Calculation) -> Calculation:
        # 1. Insertar Calculation
        orm_calc = CalculationORM(
            id=entity.id,
            study_case_id=entity.study_case_id,
            climate_source=entity.climate_source,
            n_segments=entity.n_segments,
            design_rate=entity.design_rate,
            warnings=entity.warnings or [],
        )
        db.add(orm_calc)
        await db.flush()

        for sr in entity.season_results:
            orm_sr = season_result_entity_to_orm(sr, entity.id)
            orm_sr.id = sr.id
            db.add(orm_sr)
            await db.flush()

            for segment in sr.segments:
                db.add(segment_entity_to_orm(segment, orm_sr.id))

        await db.flush()

        return orm_to_entity(await self._get_orm(db, entity.id))

    async def get_by_id(
        self, db: AsyncSession, calc_id: str, user_id: str | None = None
    ) -> Calculation:
        return orm_to_entity(await self._get_orm(db, calc_id, user_id))

    async def get_by_study_case(
        self, db: AsyncSession, case_id: str, user_id: str
    ) -> list[Calculation]:
        result = await db.execute(
            select(CalculationORM)
            .options(*_EAGER)
            .join(StudyCaseORM, CalculationORM.study_case_id == StudyCaseORM.id)
            .where(CalculationORM.study_case_id == case_id)
            .where(StudyCaseORM.owner_id == user_id)
            .order_by(CalculationORM.created_at.desc())
        )
        return [orm_to_entity(o) for o in result.scalars().all()]

    async def delete(
        self, db: AsyncSession, calc_id: str, user_id: str | None = None
    ) -> bool:
        if user_id is not None:
            try:
                await self._get_orm(db, calc_id, user_id)
            except NoResultFound:
                return False

        await db.execute(delete(CalculationORM).where(CalculationORM.id == calc_id))
        return True


calculations_repo = CalculationsRepository()
