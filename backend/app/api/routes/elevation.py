from fastapi import APIRouter, HTTPException
from app.api.schemas.models import ElevationResponseDTO
from app.services import elevation_service

router = APIRouter()


@router.get("/", response_model=ElevationResponseDTO)
async def get_elevation(lat: float, lon: float):
    try:
        return await elevation_service.get_elevation(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))