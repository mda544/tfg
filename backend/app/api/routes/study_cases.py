from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import get_db
from app.infrastructure.orm_models import UserORM
from app.api.deps import get_current_user
from app.api.schemas.models import (
    StudyCaseCreateDTO,
    StudyCaseResponseDTO,
    RateResultResponseDTO,
)
from app.services import study_cases_service, rates_service

router = APIRouter()


@router.get("/", response_model=list[StudyCaseResponseDTO])
async def list_study_cases(
    db: AsyncSession = Depends(get_db), user: UserORM = Depends(get_current_user)
):
    return await study_cases_service.get_all(db, user.id)


@router.post(
    "/", response_model=StudyCaseResponseDTO, status_code=status.HTTP_201_CREATED
)
async def create_study_case(
    data: StudyCaseCreateDTO,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await study_cases_service.create(db, data, user.id)


@router.get("/{case_id}", response_model=StudyCaseResponseDTO)
async def get_study_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await study_cases_service.get_by_id(db, case_id, user.id)


@router.put("/{case_id}", response_model=StudyCaseResponseDTO)
async def update_study_case(
    case_id: str,
    data: StudyCaseCreateDTO,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await study_cases_service.update(db, case_id, data, user.id)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    await study_cases_service.delete(db, case_id, user.id)


@router.get("/{case_id}/rates", response_model=list[RateResultResponseDTO])
async def list_case_rates(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await rates_service.get_by_study_case(db, case_id)


@router.get("/{case_id}/rates/{rate_id}", response_model=RateResultResponseDTO)
async def get_case_rate(
    case_id: str,
    rate_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserORM = Depends(get_current_user),
):
    return await rates_service.get_by_id(db, rate_id)
