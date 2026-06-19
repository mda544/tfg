from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_current_user,
    get_study_cases_repo,
    get_lines_repo,
    get_calculations_repo,
)
from app.api.schemas.models import CalculationCreateDTO, CalculationResponseDTO
from app.domain.repository_interfaces import (
    IStudyCasesRepository,
    ILinesRepository,
    ICalculationsRepository,
)
from app.services import calculations_service

router = APIRouter()


@router.get("/", response_model=list[CalculationResponseDTO])
async def list_calculations(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: ICalculationsRepository = Depends(get_calculations_repo),
):
    return await calculations_service.get_by_study_case(db, case_id, user_id, repo)


@router.post(
    "/", response_model=CalculationResponseDTO, status_code=status.HTTP_201_CREATED
)
async def create_calculation(
    case_id: str,
    req: CalculationCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    study_cases_repo: IStudyCasesRepository = Depends(get_study_cases_repo),
    lines_repo: ILinesRepository = Depends(get_lines_repo),
    calculations_repo: ICalculationsRepository = Depends(get_calculations_repo),
):
    req.study_case_id = case_id
    return await calculations_service.create(
        db, req, user_id, study_cases_repo, lines_repo, calculations_repo
    )


@router.get("/{calc_id}", response_model=CalculationResponseDTO)
async def get_calculation(
    case_id: str,
    calc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: ICalculationsRepository = Depends(get_calculations_repo),
):
    return await calculations_service.get_by_id(db, calc_id, case_id, user_id, repo)


@router.delete("/{calc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calculation(
    case_id: str,
    calc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: ICalculationsRepository = Depends(get_calculations_repo),
):
    await calculations_service.delete(db, calc_id, case_id, user_id, repo)
