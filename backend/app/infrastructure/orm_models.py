import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Float,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum as SAEnum,
    UniqueConstraint,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.infrastructure.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    conductors: Mapped[list["ConductorORM"]] = relationship(back_populates="owner")
    lines: Mapped[list["LineORM"]] = relationship(back_populates="owner")
    study_cases: Mapped[list["StudyCaseORM"]] = relationship(back_populates="owner")


class ConductorORM(Base):
    __tablename__ = "conductors"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    diameter_mm: Mapped[float] = mapped_column(Float, nullable=False)
    r_ac_75_ohm_km: Mapped[float] = mapped_column(Float, nullable=False)
    r_ac_25_ohm_km: Mapped[float] = mapped_column(Float, nullable=False)
    emissivity: Mapped[float] = mapped_column(Float, default=0.5)
    absorptivity: Mapped[float] = mapped_column(Float, default=0.5)
    max_temp_c: Mapped[float] = mapped_column(Float, default=90.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    owner: Mapped["UserORM | None"] = relationship(back_populates="conductors")


class LineORM(Base):
    __tablename__ = "lines"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    geometry: Mapped[object] = mapped_column(
        Geometry(geometry_type="GEOMETRYZ", srid=4326), nullable=False
    )
    length_km: Mapped[float] = mapped_column(Float, nullable=True)
    n_points: Mapped[int] = mapped_column(Integer, nullable=True)
    bbox_lat_min: Mapped[float] = mapped_column(Float, nullable=True)
    bbox_lat_max: Mapped[float] = mapped_column(Float, nullable=True)
    bbox_lon_min: Mapped[float] = mapped_column(Float, nullable=True)
    bbox_lon_max: Mapped[float] = mapped_column(Float, nullable=True)
    min_elevation_m: Mapped[float] = mapped_column(Float, nullable=True)
    max_elevation_m: Mapped[float] = mapped_column(Float, nullable=True)
    avg_elevation_m: Mapped[float] = mapped_column(Float, nullable=True)
    elevation_source: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    owner: Mapped["UserORM"] = relationship(back_populates="lines")
    study_cases: Mapped[list["StudyCaseORM"]] = relationship(back_populates="line")


class StudyCaseORM(Base):
    """Define el sistema a analizar: línea + conductor + parámetros de segmentación."""

    __tablename__ = "study_cases"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    line_id: Mapped[str] = mapped_column(ForeignKey("lines.id"), nullable=False)
    conductor_id: Mapped[str] = mapped_column(
        ForeignKey("conductors.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    segment_step_m: Mapped[float] = mapped_column(Float, default=500.0)
    use_real_spans: Mapped[bool] = mapped_column(Boolean, default=False)
    use_dem: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    owner: Mapped["UserORM"] = relationship(back_populates="study_cases")
    line: Mapped["LineORM"] = relationship(back_populates="study_cases")
    conductor: Mapped["ConductorORM"] = relationship()
    calculations: Mapped[list["CalculationORM"]] = relationship(
        back_populates="study_case",
        cascade="all, delete",
        passive_deletes=True,
    )


class CalculationORM(Base):
    """Una ejecución del cálculo sobre un StudyCase.
    Tiene exactamente 4 SeasonResultORM, uno por estación."""

    __tablename__ = "calculations"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    study_case_id: Mapped[str] = mapped_column(
        ForeignKey("study_cases.id", ondelete="CASCADE"), nullable=False
    )
    climate_source: Mapped[str] = mapped_column(String(50), nullable=False)
    n_segments: Mapped[int] = mapped_column(Integer, nullable=False)
    design_rate: Mapped[float] = mapped_column(Float, nullable=False)
    warnings: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    study_case: Mapped["StudyCaseORM"] = relationship(back_populates="calculations")
    season_results: Mapped[list["SeasonResultORM"]] = relationship(
        back_populates="calculation",
        cascade="all, delete",
        passive_deletes=True,
    )


class SeasonResultORM(Base):
    """Resultado del cálculo para una estación concreta.
    Agrupa el weather_input del usuario y los segmentos calculados.
    Un Calculation tiene exactamente 4 SeasonResult."""

    __tablename__ = "season_results"
    __table_args__ = (
        UniqueConstraint("calculation_id", "season", name="uq_season_result"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    calculation_id: Mapped[str] = mapped_column(
        ForeignKey("calculations.id", ondelete="CASCADE"), nullable=False
    )
    season: Mapped[str] = mapped_column(
        SAEnum("verano", "otono", "invierno", "primavera", name="season_enum"),
        nullable=False,
    )
    temp_amb_c: Mapped[float] = mapped_column(Float, nullable=False)
    wind_speed_ms: Mapped[float] = mapped_column(Float, nullable=False)
    wind_angle_deg: Mapped[float] = mapped_column(Float, default=90.0)
    wind_dir_predominant_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_radiation_wm2: Mapped[float] = mapped_column(Float, nullable=False)
    design_rate: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_source: Mapped[str] = mapped_column(String(50), nullable=False)

    calculation: Mapped["CalculationORM"] = relationship(
        back_populates="season_results"
    )
    segments: Mapped[list["SegmentORM"]] = relationship(
        back_populates="season_result",
        cascade="all, delete",
        passive_deletes=True,
    )


class SegmentORM(Base):
    """Tramo del trazado con resultado IEEE 738 para una estación concreta."""

    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    season_result_id: Mapped[str] = mapped_column(
        ForeignKey("season_results.id", ondelete="CASCADE"), nullable=False
    )
    segment_id: Mapped[str] = mapped_column(String(10), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry: Mapped[object] = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326), nullable=False
    )
    mid_point: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )
    length_km: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_m: Mapped[float] = mapped_column(Float, default=0.0)
    azimuth_deg: Mapped[float] = mapped_column(Float, default=90.0)
    ampacity: Mapped[float] = mapped_column(Float, nullable=False)
    design_rate: Mapped[float] = mapped_column(Float, nullable=False)
    qc_wm: Mapped[float] = mapped_column(Float, nullable=False)
    qr_wm: Mapped[float] = mapped_column(Float, nullable=False)
    qs_wm: Mapped[float] = mapped_column(Float, nullable=False)
    r_tc_ohm_m: Mapped[float] = mapped_column(Float, nullable=False)
    conv_mode: Mapped[str] = mapped_column(String(20), nullable=False)

    season_result: Mapped["SeasonResultORM"] = relationship(back_populates="segments")


class ClimateCacheORM(Base):
    __tablename__ = "climate_cache"
    __table_args__ = (
        UniqueConstraint("lat", "lon", "source", "season", name="uq_climate_cache"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    season: Mapped[str] = mapped_column(String(20), nullable=False)
    temp_p90_c: Mapped[float] = mapped_column(Float, nullable=False)
    temp_p50_c: Mapped[float] = mapped_column(Float, nullable=False)
    temp_p10_c: Mapped[float] = mapped_column(Float, nullable=False)
    wind_p10_ms: Mapped[float] = mapped_column(Float, nullable=False)
    wind_p50_ms: Mapped[float] = mapped_column(Float, nullable=False)
    wind_p90_ms: Mapped[float] = mapped_column(Float, nullable=False)
    wind_dir_predominant_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    radiation_p50_wm2: Mapped[float] = mapped_column(Float, nullable=False)
    radiation_p90_wm2: Mapped[float] = mapped_column(Float, nullable=False)
    n_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    years_covered: Mapped[str] = mapped_column(String(50), nullable=False)


class ElevationCacheORM(Base):
    __tablename__ = "elevation_cache"
    __table_args__ = (UniqueConstraint("lat", "lon", name="uq_elevation_cache"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=_uuid
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_m: Mapped[float] = mapped_column(Float, nullable=False)
