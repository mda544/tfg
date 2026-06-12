from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKTElement

from app.domain.entities import Segment
from app.domain.value_objects import GeoPoint, SegmentRating
from app.infrastructure.orm_models import SegmentORM
from app.api.schemas.models import GeoPointDTO, SegmentResultDTO


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


def orm_to_entity(obj: SegmentORM) -> Segment:
    return Segment(
        id=obj.segment_id,
        index=obj.index,
        start_point=_geopoint_from_wkb_line(obj.geometry, 0),
        mid_point=_geopoint_from_wkb_point(obj.mid_point),
        end_point=_geopoint_from_wkb_line(obj.geometry, -1),
        length_km=obj.length_km,
        elevation_m=obj.elevation_m,
        azimuth_deg=obj.azimuth_deg,
        ampacity=obj.ampacity,
        rating=SegmentRating(
            ampacity=obj.ampacity,
            temp_conductor_c=obj.r_tc_ohm_m and 90.0 or 90.0,
            qc_wm=obj.qc_wm,
            qr_wm=obj.qr_wm,
            qs_wm=obj.qs_wm,
            r_tc_ohm_m=obj.r_tc_ohm_m,
            conv_mode=obj.conv_mode,
        ),
    )


def entity_to_orm(entity: Segment, season_result_id: str) -> SegmentORM:
    rating = entity.rating
    return SegmentORM(
        season_result_id=season_result_id,
        segment_id=entity.id,
        index=entity.index,
        geometry=WKTElement(_wkt_line(entity.start_point, entity.end_point), srid=4326),
        mid_point=WKTElement(_wkt_point(entity.mid_point), srid=4326),
        length_km=entity.length_km,
        elevation_m=entity.elevation_m,
        azimuth_deg=entity.azimuth_deg,
        ampacity=entity.ampacity,
        design_rate=entity.design_rate,
        qc_wm=rating.qc_wm if rating else 0.0,
        qr_wm=rating.qr_wm if rating else 0.0,
        qs_wm=rating.qs_wm if rating else 0.0,
        r_tc_ohm_m=rating.r_tc_ohm_m if rating else 0.0,
        conv_mode=rating.conv_mode if rating else "natural",
    )


def entity_to_dto(entity: Segment) -> SegmentResultDTO:
    rating = entity.rating
    return SegmentResultDTO(
        segment_id=entity.id,
        index=entity.index,
        length_km=entity.length_km,
        elevation_m=entity.elevation_m,
        azimuth_deg=entity.azimuth_deg,
        mid_point=GeoPointDTO(lat=entity.mid_point.lat, lon=entity.mid_point.lon),
        start_point=GeoPointDTO(lat=entity.start_point.lat, lon=entity.start_point.lon),
        end_point=GeoPointDTO(lat=entity.end_point.lat, lon=entity.end_point.lon),
        ampacity=entity.ampacity,
        design_rate=entity.design_rate,
        qc_wm=rating.qc_wm if rating else 0.0,
        qr_wm=rating.qr_wm if rating else 0.0,
        qs_wm=rating.qs_wm if rating else 0.0,
        r_tc_ohm_m=rating.r_tc_ohm_m if rating else 0.0,
        conv_mode=rating.conv_mode if rating else "natural",
    )
