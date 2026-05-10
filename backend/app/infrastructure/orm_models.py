import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, Boolean, Integer, DateTime, ForeignKey, Text, Enum as SAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.infrastructure.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())

def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserORM(Base):
    """
    Usuario de la aplicación.
    Todas las tablas de datos tienen owner_id → users.id
    para aislar los datos entre usuarios.
    """
    __tablename__ = "users"

    id:         Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    email:      Mapped[str]      = mapped_column(String(255), unique=True, nullable=False)
    password:   Mapped[str]      = mapped_column(String(255), nullable=False)  # bcrypt hash
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    conductors:  Mapped[list["ConductorORM"]]  = relationship(back_populates="owner")
    lines:       Mapped[list["LineORM"]]       = relationship(back_populates="owner")
    study_cases: Mapped[list["StudyCaseORM"]]  = relationship(back_populates="owner")


class ConductorORM(Base):
    __tablename__ = "conductors"

    id:             Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    owner_id:       Mapped[str]      = mapped_column(ForeignKey("users.id"), nullable=False)
    name:           Mapped[str]      = mapped_column(String(100), nullable=False)
    description:    Mapped[str]      = mapped_column(Text, nullable=True)
    diameter_mm:    Mapped[float]    = mapped_column(Float, nullable=False)
    r_ac_75_ohm_km: Mapped[float]    = mapped_column(Float, nullable=False)
    r_ac_25_ohm_km: Mapped[float]    = mapped_column(Float, nullable=False)
    emissivity:     Mapped[float]    = mapped_column(Float, default=0.5)
    absorptivity:   Mapped[float]    = mapped_column(Float, default=0.5)
    max_temp_c:     Mapped[float]    = mapped_column(Float, default=90.0)
    created_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    owner:       Mapped["UserORM"]          = relationship(back_populates="conductors")
    study_cases: Mapped[list["StudyCaseORM"]] = relationship(back_populates="conductor")


class LineORM(Base):
    __tablename__ = "lines"

    id:          Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    owner_id:    Mapped[str]      = mapped_column(ForeignKey("users.id"), nullable=False)
    name:        Mapped[str]      = mapped_column(String(200), nullable=False)
    description: Mapped[str]      = mapped_column(Text, nullable=True)
    geometry:    Mapped[object]   = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326), nullable=False
    )
    length_km:   Mapped[float]    = mapped_column(Float, nullable=True)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    owner:       Mapped["UserORM"]            = relationship(back_populates="lines")
    study_cases: Mapped[list["StudyCaseORM"]] = relationship(back_populates="line")


class StudyCaseORM(Base):
    __tablename__ = "study_cases"

    id:             Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    owner_id:       Mapped[str]      = mapped_column(ForeignKey("users.id"), nullable=False)
    name:           Mapped[str]      = mapped_column(String(200), nullable=False)
    description:    Mapped[str]      = mapped_column(Text, nullable=True)
    line_id:        Mapped[str]      = mapped_column(ForeignKey("lines.id"), nullable=False)
    conductor_id:   Mapped[str]      = mapped_column(ForeignKey("conductors.id"), nullable=False)
    segment_step_m: Mapped[float]    = mapped_column(Float, default=500.0)
    use_real_spans: Mapped[bool]     = mapped_column(Boolean, default=False)
    use_dem:        Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    owner:     Mapped["UserORM"]      = relationship(back_populates="study_cases")
    line:      Mapped["LineORM"]      = relationship(back_populates="study_cases")
    conductor: Mapped["ConductorORM"] = relationship(back_populates="study_cases")
    scenarios: Mapped[list["MeteoScenarioORM"]] = relationship(
        back_populates="study_case", cascade="all, delete-orphan"
    )
    results: Mapped[list["RateResultORM"]] = relationship(
        back_populates="study_case", cascade="all, delete-orphan"
    )


class MeteoScenarioORM(Base):
    __tablename__ = "meteo_scenarios"

    id:                  Mapped[str]   = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    study_case_id:       Mapped[str]   = mapped_column(ForeignKey("study_cases.id"), nullable=False)
    season:              Mapped[str]   = mapped_column(
        SAEnum("verano", "otono", "invierno", "primavera", name="season_enum"), nullable=False
    )
    temp_amb_c:          Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed_ms:       Mapped[float] = mapped_column(Float, nullable=False)
    wind_angle_deg:      Mapped[float] = mapped_column(Float, default=90.0)
    solar_radiation_wm2: Mapped[float] = mapped_column(Float, nullable=False)

    study_case: Mapped["StudyCaseORM"] = relationship(back_populates="scenarios")


class RateResultORM(Base):
    __tablename__ = "rate_results"

    id:                 Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True)
    study_case_id:      Mapped[str]      = mapped_column(ForeignKey("study_cases.id"), nullable=True)
    n_segments:         Mapped[int]      = mapped_column(Integer, nullable=False)
    design_rate_a:      Mapped[float]    = mapped_column(Float, nullable=False)
    rates_by_season:    Mapped[dict]     = mapped_column(JSONB, nullable=False)
    route_info:         Mapped[dict]     = mapped_column(JSONB, nullable=False)
    warnings:           Mapped[list]     = mapped_column(JSONB, nullable=True)
    conductor_snapshot: Mapped[dict]     = mapped_column(JSONB, nullable=False)
    created_at:         Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    study_case: Mapped["StudyCaseORM"]     = relationship(back_populates="results")
    segments:   Mapped[list["SegmentORM"]] = relationship(
        back_populates="rate_result", cascade="all, delete-orphan"
    )


class SegmentORM(Base):
    __tablename__ = "segments"

    id:             Mapped[str]    = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    rate_result_id: Mapped[str]    = mapped_column(ForeignKey("rate_results.id"), nullable=False)
    segment_id:     Mapped[str]    = mapped_column(String(10), nullable=False)
    index:          Mapped[int]    = mapped_column(Integer, nullable=False)
    mid_point:      Mapped[object] = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    geometry:       Mapped[object] = mapped_column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    length_km:      Mapped[float]  = mapped_column(Float, nullable=False)
    elevation_m:    Mapped[float]  = mapped_column(Float, default=0.0)
    azimuth_deg:    Mapped[float]  = mapped_column(Float, default=90.0)
    rate_summer_a:  Mapped[float]  = mapped_column(Float, nullable=False)
    rate_autumn_a:  Mapped[float]  = mapped_column(Float, nullable=False)
    rate_winter_a:  Mapped[float]  = mapped_column(Float, nullable=False)
    rate_spring_a:  Mapped[float]  = mapped_column(Float, nullable=False)
    design_rate_a:  Mapped[float]  = mapped_column(Float, nullable=False)
    details:        Mapped[dict]   = mapped_column(JSONB, nullable=False)

    rate_result: Mapped["RateResultORM"] = relationship(back_populates="segments")

class ClimateCacheORM(Base):
    __tablename__ = "climate_cache"
    __table_args__ = (UniqueConstraint('lat', 'lon', 'source', 'season', name='uq_climate_cache'),)

    id:                Mapped[str]   = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    lat:               Mapped[float] = mapped_column(Float, nullable=False)
    lon:               Mapped[float] = mapped_column(Float, nullable=False)
    source:            Mapped[str]   = mapped_column(String(50), nullable=False)
    season:            Mapped[str]   = mapped_column(String(20), nullable=False)
    temp_p90_c:        Mapped[float] = mapped_column(Float, nullable=False)
    temp_p50_c:        Mapped[float] = mapped_column(Float, nullable=False)
    temp_p10_c:        Mapped[float] = mapped_column(Float, nullable=False)
    wind_p10_ms:       Mapped[float] = mapped_column(Float, nullable=False)
    wind_p50_ms:       Mapped[float] = mapped_column(Float, nullable=False)
    wind_p90_ms:       Mapped[float] = mapped_column(Float, nullable=False)
    radiation_p50_wm2: Mapped[float] = mapped_column(Float, nullable=False)
    radiation_p90_wm2: Mapped[float] = mapped_column(Float, nullable=False)
    n_hours:           Mapped[int]   = mapped_column(Integer, nullable=False)
    years_covered:     Mapped[str]   = mapped_column(String(50), nullable=False)


class ElevationCacheORM(Base):
    __tablename__ = "elevation_cache"
    __table_args__ = (UniqueConstraint('lat', 'lon', name='uq_elevation_cache'),)

    id:          Mapped[str]   = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    lat:         Mapped[float] = mapped_column(Float, nullable=False)
    lon:         Mapped[float] = mapped_column(Float, nullable=False)
    elevation_m: Mapped[float] = mapped_column(Float, nullable=False)