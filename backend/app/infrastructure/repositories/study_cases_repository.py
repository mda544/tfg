from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import NoResultFound

from app.infrastructure.orm_models import StudyCaseORM, MeteoScenarioORM
from app.api.schemas.models import StudyCaseCreateDTO


class StudyCasesRepository:

    async def get_all(self, db: AsyncSession, owner_id: str) -> list[StudyCaseORM]:
        result = await db.execute(
            select(StudyCaseORM)
            .options(selectinload(StudyCaseORM.scenarios))
            .where(StudyCaseORM.owner_id == owner_id)
            .order_by(StudyCaseORM.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(
        self, db: AsyncSession, case_id: str, owner_id: str
    ) -> StudyCaseORM:
        result = await db.execute(
            select(StudyCaseORM)
            .options(selectinload(StudyCaseORM.scenarios))
            .where(StudyCaseORM.id == case_id)
            .where(StudyCaseORM.owner_id == owner_id)
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Study case {case_id} not found.")
        return obj

    async def exists(
        self, db: AsyncSession, case_id: str, owner_id: str
    ) -> bool:
        result = await db.execute(
            select(StudyCaseORM.id)
            .where(StudyCaseORM.id == case_id)
            .where(StudyCaseORM.owner_id == owner_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self, db: AsyncSession, owner_id: str, data: StudyCaseCreateDTO
    ) -> StudyCaseORM:
        obj = StudyCaseORM(
            owner_id       = owner_id,
            name           = data.name,
            description    = data.description,
            line_id        = data.line_id,
            conductor_id   = data.conductor_id,
            segment_step_m = data.segment_step_m,
            use_real_spans = data.use_real_spans,
            use_dem        = data.use_dem,
            scenarios      = [
                MeteoScenarioORM(**s.model_dump())
                for s in (data.scenarios or [])
            ],
        )
        db.add(obj)
        await db.flush()
        return await self.get_by_id(db, obj.id, owner_id)

    async def update(
        self, db: AsyncSession, case_id: str, owner_id: str, data: StudyCaseCreateDTO
    ) -> StudyCaseORM:
        await db.execute(
            update(StudyCaseORM)
            .where(StudyCaseORM.id == case_id)
            .where(StudyCaseORM.owner_id == owner_id)
            .values(
                name           = data.name,
                description    = data.description,
                line_id        = data.line_id,
                conductor_id   = data.conductor_id,
                segment_step_m = data.segment_step_m,
                use_real_spans = data.use_real_spans,
                use_dem        = data.use_dem,
            )
        )
        if data.scenarios is not None:
            await db.execute(
                delete(MeteoScenarioORM)
                .where(MeteoScenarioORM.study_case_id == case_id)
            )
            for s in data.scenarios:
                db.add(MeteoScenarioORM(study_case_id=case_id, **s.model_dump()))
        return await self.get_by_id(db, case_id, owner_id)

    async def delete(
        self, db: AsyncSession, case_id: str, owner_id: str
    ) -> bool:
        result = await db.execute(
            delete(StudyCaseORM)
            .where(StudyCaseORM.id == case_id)
            .where(StudyCaseORM.owner_id == owner_id)
        )
        return result.rowcount > 0


study_cases_repo = StudyCasesRepository()