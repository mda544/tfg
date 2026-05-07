from fastapi import APIRouter, HTTPException
from app.api.schemas.models import PercentilesResponse, PercentilesEstacionResponse, PuntoGeo
from app.infrastructure.cache.historical_cache import obtener_percentiles

router = APIRouter()


@router.get("/percentiles", response_model=PercentilesResponse)
async def get_percentiles(
    lat: float,
    lon: float,
    fuente: str = "openmeteo",
    anio_inicio: int = 1990,
    anio_fin: int = 2023,
):
    try:
        percentiles = await obtener_percentiles(lat, lon, fuente, anio_inicio, anio_fin)
        return PercentilesResponse(
            fuente=fuente,
            punto=PuntoGeo(lat=lat, lon=lon),
            percentiles={
                est: PercentilesEstacionResponse(
                    temp_p10_c        = p.temp_p10_c,
                    temp_p50_c        = p.temp_p50_c,
                    temp_p90_c        = p.temp_p90_c,
                    viento_p10_ms     = p.viento_p10_ms,
                    viento_p50_ms     = p.viento_p50_ms,
                    viento_p90_ms     = p.viento_p90_ms,
                    radiacion_p50_wm2 = p.radiacion_p50_wm2,
                    radiacion_p90_wm2 = p.radiacion_p90_wm2,
                    n_horas           = p.n_horas,
                    fuente            = p.fuente,
                    anios_cubiertos   = p.anios_cubiertos,
                )
                for est, p in percentiles.items()
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
