from app.domain.entities import ValidationResult
from app.core.utils.geo import haversine_m

COVERAGE = {
    "Open-Meteo": {"lat": (-90, 90), "lon": (-180, 180)},
    "NASA POWER": {"lat": (-90, 90), "lon": (-180, 180)},
    "Copernicus DEM GLO-30": {"lat": (-90, 84), "lon": (-180, 180)},
}

LIMITS = {
    "min_points": 2,
    "min_length_m": 100,
    "max_length_km": 500,
    "max_bbox_deg": 10,
    "max_span_km": 50,
    "max_check_intersect": 200,
}


def validate_route(coordinates: list[dict]) -> ValidationResult:
    errors = []
    warnings = []
    info = {"n_points": len(coordinates)}

    if len(coordinates) < LIMITS["min_points"]:
        return ValidationResult(
            valid=False,
            errors=[
                f"El trazado tiene {len(coordinates)} punto(s). Mínimo: {LIMITS['min_points']}."
            ],
            info=info,
        )

    out_of_range = [
        i
        for i, c in enumerate(coordinates)
        if not (-90 <= c["lat"] <= 90) or not (-180 <= c["lon"] <= 180)
    ]
    if out_of_range:
        errors.append(
            f"{len(out_of_range)} punto(s) fuera del rango WGS84 "
            f"(índices: {out_of_range[:5]}{'…' if len(out_of_range) > 5 else ''})."
        )
        return ValidationResult(valid=False, errors=errors, info=info)

    lats = [c["lat"] for c in coordinates]
    lons = [c["lon"] for c in coordinates]
    bbox = {
        "lat_min": min(lats),
        "lat_max": max(lats),
        "lon_min": min(lons),
        "lon_max": max(lons),
    }
    info["bbox"] = bbox
    span_lat = bbox["lat_max"] - bbox["lat_min"]
    span_lon = bbox["lon_max"] - bbox["lon_min"]

    if span_lat > LIMITS["max_bbox_deg"] or span_lon > LIMITS["max_bbox_deg"]:
        warnings.append(
            f"Bounding box muy amplio: {span_lat:.1f}° lat × {span_lon:.1f}° lon. "
            f"Comprueba que no hay coordenadas erróneas."
        )

    total_length_m = sum(
        haversine_m(coordinates[i], coordinates[i + 1])
        for i in range(len(coordinates) - 1)
    )
    length_km = total_length_m / 1000.0
    info["length_km"] = round(length_km, 2)

    if total_length_m < LIMITS["min_length_m"]:
        errors.append(
            f"Trazado demasiado corto: {total_length_m:.0f} m. Mínimo: {LIMITS['min_length_m']} m."
        )
    elif length_km > LIMITS["max_length_km"]:
        warnings.append(
            f"Trazado muy largo: {length_km:.0f} km. El cálculo puede tardar varios minutos."
        )

    long_spans = []
    for i in range(len(coordinates) - 1):
        d_km = haversine_m(coordinates[i], coordinates[i + 1]) / 1000.0
        if d_km > LIMITS["max_span_km"]:
            long_spans.append({"from": i, "to": i + 1, "km": round(d_km, 1)})
    if long_spans:
        warnings.append(
            f"{len(long_spans)} vano(s) con separación > {LIMITS['max_span_km']} km entre apoyos consecutivos."
        )
    info["long_spans"] = long_spans

    for source, cov in COVERAGE.items():
        out_of_cov = [
            c
            for c in coordinates
            if not (cov["lat"][0] <= c["lat"] <= cov["lat"][1])
            or not (cov["lon"][0] <= c["lon"] <= cov["lon"][1])
        ]
        if out_of_cov:
            warnings.append(
                f"{len(out_of_cov)} punto(s) fuera de la cobertura de {source}."
            )

    if len(coordinates) - 1 <= LIMITS["max_check_intersect"]:
        intersections = _detect_self_intersections(coordinates)
        if intersections:
            warnings.append(
                f"El trazado se autointersecta en {len(intersections)} punto(s)."
            )
            info["self_intersects"] = intersections

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info=info,
    )


def _segments_intersect(p1, p2, p3, p4) -> bool:
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    A = (p1["lon"], p1["lat"])
    B = (p2["lon"], p2["lat"])
    C = (p3["lon"], p3["lat"])
    D = (p4["lon"], p4["lat"])
    return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))


# Devuelve los pares de segmentos que se cruzan. Limitado a trazados cortos.
def _detect_self_intersections(coordinates: list[dict]) -> list[dict]:
    intersections = []
    n = len(coordinates)
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if i == 0 and j == n - 2:
                continue
            if _segments_intersect(
                coordinates[i],
                coordinates[i + 1],
                coordinates[j],
                coordinates[j + 1],
            ):
                intersections.append({"segment_a": i, "segment_b": j})
    return intersections
