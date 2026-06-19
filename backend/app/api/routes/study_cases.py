from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_current_user,
    get_study_cases_repo,
    get_lines_repo,
    get_conductors_repo,
    get_calculations_repo,
)
from app.api.schemas.models import StudyCaseCreateDTO, StudyCaseResponseDTO
from app.domain.repository_interfaces import (
    IStudyCasesRepository,
    ILinesRepository,
    IConductorsRepository,
    ICalculationsRepository,
)
from app.services import study_cases_service

router = APIRouter()


@router.get("/", response_model=list[StudyCaseResponseDTO])
async def list_study_cases(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: IStudyCasesRepository = Depends(get_study_cases_repo),
):
    return await study_cases_service.get_all(db, user_id, repo)


@router.post(
    "/", response_model=StudyCaseResponseDTO, status_code=status.HTTP_201_CREATED
)
async def create_study_case(
    data: StudyCaseCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    study_cases_repo: IStudyCasesRepository = Depends(get_study_cases_repo),
    lines_repo: ILinesRepository = Depends(get_lines_repo),
    conductors_repo: IConductorsRepository = Depends(get_conductors_repo),
):
    return await study_cases_service.create(
        db, data, user_id, study_cases_repo, lines_repo, conductors_repo
    )


@router.get("/{case_id}", response_model=StudyCaseResponseDTO)
async def get_study_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: IStudyCasesRepository = Depends(get_study_cases_repo),
):
    return await study_cases_service.get_by_id(db, case_id, user_id, repo)


@router.put("/{case_id}", response_model=StudyCaseResponseDTO)
async def update_study_case(
    case_id: str,
    data: StudyCaseCreateDTO,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    study_cases_repo: IStudyCasesRepository = Depends(get_study_cases_repo),
    lines_repo: ILinesRepository = Depends(get_lines_repo),
    conductors_repo: IConductorsRepository = Depends(get_conductors_repo),
):
    return await study_cases_service.update(
        db, case_id, data, user_id, study_cases_repo, lines_repo, conductors_repo
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
    repo: IStudyCasesRepository = Depends(get_study_cases_repo),
):
    await study_cases_service.delete(db, case_id, user_id, repo)
