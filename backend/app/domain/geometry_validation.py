from app.domain.entities import ValidationResult
from app.core.utils.geo import haversine_m

COVERAGE = {
    "Open-Meteo":            {"lat": (-90,  90), "lon": (-180, 180)},
    "NASA POWER":            {"lat": (-90,  90), "lon": (-180, 180)},
    "Copernicus DEM GLO-30": {"lat": (-90,  84), "lon": (-180, 180)},
}

LIMITS = {
    "min_points":       2,
    "min_length_m":     100,
    "max_length_km":    500,
    "max_bbox_deg":     10,
    "max_span_km":      50,
    "max_intersect_check": 200,
}


def validate_route(coordinates: list[dict]) -> ValidationResult:
    errors   = []
    warnings = []
    info     = {"n_points": len(coordinates)}

    if len(coordinates) < LIMITS["min_points"]:
        return ValidationResult(
            valid  = False,
            errors = [f"Route has {len(coordinates)} point(s). Minimum: {LIMITS['min_points']}."],
            info   = info,
        )

    out_of_range = [
        i for i, c in enumerate(coordinates)
        if not (-90 <= c["lat"] <= 90) or not (-180 <= c["lon"] <= 180)
    ]
    if out_of_range:
        errors.append(
            f"{len(out_of_range)} point(s) outside WGS84 range "
            f"(indices: {out_of_range[:5]}{'…' if len(out_of_range) > 5 else ''})."
        )
        return ValidationResult(valid=False, errors=errors, info=info)

    lats = [c["lat"] for c in coordinates]
    lons = [c["lon"] for c in coordinates]
    bbox = {
        "min_lat": min(lats), "max_lat": max(lats),
        "min_lon": min(lons), "max_lon": max(lons),
    }
    info["bbox"] = bbox
    span_lat = bbox["max_lat"] - bbox["min_lat"]
    span_lon = bbox["max_lon"] - bbox["min_lon"]

    if span_lat > LIMITS["max_bbox_deg"] or span_lon > LIMITS["max_bbox_deg"]:
        warnings.append(
            f"Wide bounding box: {span_lat:.1f}° lat × {span_lon:.1f}° lon. "
            f"Check for erroneous coordinates."
        )

    length_m  = sum(
        haversine_m(coordinates[i], coordinates[i + 1])
        for i in range(len(coordinates) - 1)
    )
    length_km = length_m / 1000.0
    info["length_km"] = round(length_km, 2)

    if length_m < LIMITS["min_length_m"]:
        errors.append(
            f"Route too short: {length_m:.0f} m. Minimum: {LIMITS['min_length_m']} m."
        )
    elif length_km > LIMITS["max_length_km"]:
        warnings.append(
            f"Long route: {length_km:.0f} km. Calculation may take several minutes."
        )

    long_spans = []
    for i in range(len(coordinates) - 1):
        d_km = haversine_m(coordinates[i], coordinates[i + 1]) / 1000.0
        if d_km > LIMITS["max_span_km"]:
            long_spans.append({"from": i, "to": i + 1, "km": round(d_km, 1)})
    if long_spans:
        warnings.append(
            f"{len(long_spans)} span(s) > {LIMITS['max_span_km']} km between consecutive points."
        )
    info["long_spans"] = long_spans

    for source, cov in COVERAGE.items():
        out = [
            c for c in coordinates
            if not (cov["lat"][0] <= c["lat"] <= cov["lat"][1])
            or not (cov["lon"][0] <= c["lon"] <= cov["lon"][1])
        ]
        if out:
            warnings.append(f"{len(out)} point(s) outside {source} coverage.")

    if len(coordinates) - 1 <= LIMITS["max_intersect_check"]:
        intersections = _detect_self_intersections(coordinates)
        if intersections:
            warnings.append(f"Route self-intersects at {len(intersections)} point(s).")
            info["self_intersects"] = intersections

    return ValidationResult(
        valid    = len(errors) == 0,
        errors   = errors,
        warnings = warnings,
        info     = info,
    )


def _segments_intersect(p1, p2, p3, p4) -> bool:
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    A = (p1["lon"], p1["lat"])
    B = (p2["lon"], p2["lat"])
    C = (p3["lon"], p3["lat"])
    D = (p4["lon"], p4["lat"])
    return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))


def _detect_self_intersections(coordinates: list[dict]) -> list[dict]:
    intersections = []
    n = len(coordinates)
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if i == 0 and j == n - 2:
                continue
            if _segments_intersect(
                coordinates[i],     coordinates[i + 1],
                coordinates[j],     coordinates[j + 1],
            ):
                intersections.append({"seg_a": i, "seg_b": j})
    return intersections