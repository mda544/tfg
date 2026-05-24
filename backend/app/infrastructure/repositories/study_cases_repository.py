from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import NoResultFound

from app.infrastructure.orm_models import StudyCaseORM
from app.infrastructure.mappers.study_cases_mapper import orm_to_entity
from app.domain.entities import StudyCase


class StudyCasesRepository:

    async def get_all(self, db: AsyncSession, owner_id: str) -> list[StudyCase]:
        result = await db.execute(
            select(StudyCaseORM)
            .where(StudyCaseORM.owner_id == owner_id)
            .order_by(StudyCaseORM.created_at.desc())
        )
        return [orm_to_entity(o) for o in result.scalars().all()]

    async def get_by_id(
        self, db: AsyncSession, case_id: str, owner_id: str
    ) -> StudyCase:
        result = await db.execute(
            select(StudyCaseORM)
            .where(StudyCaseORM.id == case_id)
            .where(StudyCaseORM.owner_id == owner_id)
        )
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NoResultFound(f"Study case {case_id} not found.")
        return orm_to_entity(obj)

    async def exists(self, db: AsyncSession, case_id: str, owner_id: str) -> bool:
        result = await db.execute(
            select(StudyCaseORM.id)
            .where(StudyCaseORM.id == case_id)
            .where(StudyCaseORM.owner_id == owner_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self, db: AsyncSession, owner_id: str, entity: StudyCase
    ) -> StudyCase:
        obj = StudyCaseORM(
            owner_id=owner_id,
            name=entity.name,
            description=entity.description,
            line_id=entity.line_id,
            segment_step_m=entity.segment_step_m,
            use_real_spans=entity.use_real_spans,
            use_dem=entity.use_dem,
        )
        db.add(obj)
        await db.flush()
        await db.refresh(obj)
        return orm_to_entity(obj)

    async def update(
        self, db: AsyncSession, case_id: str, owner_id: str, entity: StudyCase
    ) -> StudyCase:
        await db.execute(
            update(StudyCaseORM)
            .where(StudyCaseORM.id == case_id)
            .where(StudyCaseORM.owner_id == owner_id)
            .values(
                name=entity.name,
                description=entity.description,
                line_id=entity.line_id,
                segment_step_m=entity.segment_step_m,
                use_real_spans=entity.use_real_spans,
                use_dem=entity.use_dem,
            )
        )
        return await self.get_by_id(db, case_id, owner_id)

    async def delete(self, db: AsyncSession, case_id: str, owner_id: str) -> bool:
        result = await db.execute(
            delete(StudyCaseORM)
            .where(StudyCaseORM.id == case_id)
            .where(StudyCaseORM.owner_id == owner_id)
        )
        return result.rowcount > 0


study_cases_repo = StudyCasesRepository()
