from fastapi import APIRouter, HTTPException
from app.api.schemas.models import AltitudResponse
from app.infrastructure.cache.dem_cache import enriquecer_coordenadas_con_dem

router = APIRouter()


@router.get("/altitud", response_model=AltitudResponse)
async def get_altitud_punto(lat: float, lon: float):
    """Devuelve la altitud de un punto según Open-Meteo DEM."""
    try:
        resultado = await enriquecer_coordenadas_con_dem([{"lat": lat, "lon": lon}])
        return AltitudResponse(
            lat       = lat,
            lon       = lon,
            altitud_m = resultado[0].get("altitud", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
