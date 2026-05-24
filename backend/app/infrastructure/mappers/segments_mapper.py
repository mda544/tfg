from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKTElement

from app.domain.entities import Segment
from app.domain.value_objects import GeoPoint, SegmentRating
from app.domain.types import Season, SEASONS
from app.infrastructure.orm_models import SegmentORM
from app.api.schemas.models import GeoPointDTO, SegmentRatingDTO, SegmentResultDTO

_SEASON_TO_ATTR: dict[Season, str] = {
    "verano": "summer",
    "otono": "autumn",
    "invierno": "winter",
    "primavera": "spring",
}


def _wkt_point(p: GeoPoint) -> str:
    return f"POINT({p.lon} {p.lat})"


def _wkt_line(a: GeoPoint, b: GeoPoint) -> str:
    return f"LINESTRING({a.lon} {a.lat}, {b.lon} {b.lat})"


def _geopoint_from_wkb_point(geom) -> GeoPoint:
    p = to_shape(geom)
    return GeoPoint(lat=p.y, lon=p.x)


def _geopoint_from_wkb_line(geom, index: int) -> GeoPoint:
    coords = to_shape(geom).coords
    p = coords[index]
    return GeoPoint(lat=p[1], lon=p[0])


# ORM → Entidad


def orm_to_entity(obj: SegmentORM, max_temp_c: float = 90.0) -> Segment:
    """SegmentORM → Segment. Reconstruye rates y ratings desde columnas."""
    seg = Segment(
        id=obj.segment_id,
        index=obj.index,
        start_point=_geopoint_from_wkb_line(obj.geometry, 0),
        mid_point=_geopoint_from_wkb_point(obj.mid_point),
        end_point=_geopoint_from_wkb_line(obj.geometry, -1),
        length_km=obj.length_km,
        elevation_m=obj.elevation_m,
        azimuth_deg=obj.azimuth_deg,
    )
    for season, attr in _SEASON_TO_ATTR.items():
        seg.rates[season] = getattr(obj, f"rate_{attr}")
        seg.ratings[season] = SegmentRating(
            ampacity=getattr(obj, f"rate_{attr}"),
            temp_conductor_c=max_temp_c,
            qc_wm=getattr(obj, f"qc_{attr}"),
            qr_wm=getattr(obj, f"qr_{attr}"),
            qs_wm=getattr(obj, f"qs_{attr}"),
            r_tc_ohm_m=getattr(obj, f"r_tc_{attr}"),
            conv_mode=getattr(obj, f"conv_mode_{attr}"),
        )
    return seg


# Entidad → ORM


def entity_to_orm(entity: Segment, rate_result_id: str) -> SegmentORM:
    """Segment → SegmentORM con todas las columnas por estación."""
    orm = SegmentORM(
        rate_result_id=rate_result_id,
        segment_id=entity.id,
        index=entity.index,
        geometry=WKTElement(_wkt_line(entity.start_point, entity.end_point), srid=4326),
        mid_point=WKTElement(_wkt_point(entity.mid_point), srid=4326),
        length_km=entity.length_km,
        elevation_m=entity.elevation_m,
        azimuth_deg=entity.azimuth_deg,
        design_rate=entity.design_rate,
    )
    for season, attr in _SEASON_TO_ATTR.items():
        rating = entity.ratings.get(season)
        setattr(orm, f"rate_{attr}", entity.rates.get(season, 0.0))
        setattr(orm, f"qc_{attr}", rating.qc_wm if rating else 0.0)
        setattr(orm, f"qr_{attr}", rating.qr_wm if rating else 0.0)
        setattr(orm, f"qs_{attr}", rating.qs_wm if rating else 0.0)
        setattr(orm, f"r_tc_{attr}", rating.r_tc_ohm_m if rating else 0.0)
        setattr(orm, f"conv_mode_{attr}", rating.conv_mode if rating else "")
    return orm


# Entidad → DTO


def entity_to_dto(entity: Segment) -> SegmentResultDTO:
    """Segment → SegmentResultDTO para el frontend."""
    return SegmentResultDTO(
        segment_id=entity.id,
        index=entity.index,
        length_km=entity.length_km,
        elevation_m=entity.elevation_m,
        azimuth_deg=entity.azimuth_deg,
        mid_point=GeoPointDTO(lat=entity.mid_point.lat, lon=entity.mid_point.lon),
        start_point=GeoPointDTO(lat=entity.start_point.lat, lon=entity.start_point.lon),
        end_point=GeoPointDTO(lat=entity.end_point.lat, lon=entity.end_point.lon),
        rates=entity.rates,
        ratings={
            season: SegmentRatingDTO(
                ampacity=r.ampacity,
                qc_wm=r.qc_wm,
                qr_wm=r.qr_wm,
                qs_wm=r.qs_wm,
                r_tc_ohm_m=r.r_tc_ohm_m,
                conv_mode=r.conv_mode,
            )
            for season, r in entity.ratings.items()
        },
        design_rate=entity.design_rate,
    )
