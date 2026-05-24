from app.api.schemas.models import ElevationResponseDTO


def build_elevation_dto(
    lat: float, lon: float, elevation_m: float
) -> ElevationResponseDTO:
    return ElevationResponseDTO(lat=lat, lon=lon, elevation_m=elevation_m)
