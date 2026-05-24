from app.domain.entities import SeasonalPercentiles
from app.domain.types import Season
from app.api.schemas.models import (
    GeoPointDTO,
    SeasonalPercentilesDTO,
    ClimatePercentilesResponseDTO,
)


def percentiles_to_dto(p: SeasonalPercentiles) -> SeasonalPercentilesDTO:
    return SeasonalPercentilesDTO(
        temp_p10_c=p.temp_p10_c,
        temp_p50_c=p.temp_p50_c,
        temp_p90_c=p.temp_p90_c,
        wind_p10_ms=p.wind_p10_ms,
        wind_p50_ms=p.wind_p50_ms,
        wind_p90_ms=p.wind_p90_ms,
        radiation_p50_wm2=p.radiation_p50_wm2,
        radiation_p90_wm2=p.radiation_p90_wm2,
        n_hours=p.n_hours,
        source=p.source,
        years_covered=p.years_covered,
    )


def build_climate_dto(
    lat: float, lon: float, source: str, percentiles: dict[Season, SeasonalPercentiles]
) -> ClimatePercentilesResponseDTO:
    return ClimatePercentilesResponseDTO(
        source=source,
        point=GeoPointDTO(lat=lat, lon=lon),
        percentiles={
            season: percentiles_to_dto(p) for season, p in percentiles.items()
        },
    )
