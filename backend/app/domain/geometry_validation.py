from app.domain.entities import ValidationResult
from app.core.utils.geo import haversine_m

COBERTURA = {
    "Open-Meteo":            {"lat": (-90,  90), "lon": (-180, 180)},
    "NASA POWER":            {"lat": (-90,  90), "lon": (-180, 180)},
    "Copernicus DEM GLO-30": {"lat": (-90,  84), "lon": (-180, 180)},
}

LIMITES = {
    "min_puntos":          2,
    "min_longitud_m":      100,
    "max_longitud_km":     500,
    "max_bbox_grados":     10,
    "max_vano_km":         50,
    "max_check_intersect": 200,
}


def validate_route(coordenadas: list[dict]) -> ValidationResult:
    errores    = []
    avisos     = []
    info       = {"n_puntos": len(coordenadas)}

    if len(coordenadas) < LIMITES["min_puntos"]:
        return ValidationResult(
            valid   = False,
            errors  = [f"El trazado tiene {len(coordenadas)} punto(s). Mínimo: {LIMITES['min_puntos']}."],
            info    = info,
        )

    fuera_rango = [
        i for i, c in enumerate(coordenadas)
        if not (-90 <= c["lat"] <= 90) or not (-180 <= c["lon"] <= 180)
    ]
    if fuera_rango:
        errores.append(
            f"{len(fuera_rango)} punto(s) fuera del rango WGS84 "
            f"(índices: {fuera_rango[:5]}{'…' if len(fuera_rango) > 5 else ''})."
        )
        return ValidationResult(valid=False, errors=errores, info=info)

    lats = [c["lat"] for c in coordenadas]
    lons = [c["lon"] for c in coordenadas]
    bbox = {
        "lat_min": min(lats), "lat_max": max(lats),
        "lon_min": min(lons), "lon_max": max(lons),
    }
    info["bbox"] = bbox
    span_lat = bbox["lat_max"] - bbox["lat_min"]
    span_lon = bbox["lon_max"] - bbox["lon_min"]

    if span_lat > LIMITES["max_bbox_grados"] or span_lon > LIMITES["max_bbox_grados"]:
        avisos.append(
            f"Bounding box muy amplio: {span_lat:.1f}° lat × {span_lon:.1f}° lon. "
            f"Comprueba que no hay coordenadas erróneas."
        )

    longitud_m  = sum(
        haversine_m(coordenadas[i], coordenadas[i + 1])
        for i in range(len(coordenadas) - 1)
    )
    longitud_km = longitud_m / 1000.0
    info["longitud_km"] = round(longitud_km, 2)

    if longitud_m < LIMITES["min_longitud_m"]:
        errores.append(
            f"Trazado demasiado corto: {longitud_m:.0f} m. Mínimo: {LIMITES['min_longitud_m']} m."
        )
    elif longitud_km > LIMITES["max_longitud_km"]:
        avisos.append(
            f"Trazado muy largo: {longitud_km:.0f} km. El cálculo puede tardar varios minutos."
        )

    vanos_largos = []
    for i in range(len(coordenadas) - 1):
        d_km = haversine_m(coordenadas[i], coordenadas[i + 1]) / 1000.0
        if d_km > LIMITES["max_vano_km"]:
            vanos_largos.append({"desde": i, "hasta": i + 1, "km": round(d_km, 1)})
    if vanos_largos:
        avisos.append(
            f"{len(vanos_largos)} vano(s) con separación > {LIMITES['max_vano_km']} km entre apoyos consecutivos."
        )
    info["vanos_largos"] = vanos_largos

    for fuente, cob in COBERTURA.items():
        fuera = [
            c for c in coordenadas
            if not (cob["lat"][0] <= c["lat"] <= cob["lat"][1])
            or not (cob["lon"][0] <= c["lon"] <= cob["lon"][1])
        ]
        if fuera:
            avisos.append(f"{len(fuera)} punto(s) fuera de la cobertura de {fuente}.")

    if len(coordenadas) - 1 <= LIMITES["max_check_intersect"]:
        intersections  = _detect_self_intersections(coordenadas)
        if intersections :
            avisos.append(f"El trazado se autointersecta en {len(intersections )} punto(s).")
            info["autointersecciones "] = intersections 

    return ValidationResult(
        valid    = len(errores) == 0,
        errors   = errores,
        warnings = avisos,
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


# Devuelve los pares de segmentos que se cruzan. Limitado a trazados cortos.
def _detect_self_intersections(coordenadas: list[dict]) -> list[dict]:
    intersections  = []
    n = len(coordenadas)
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if i == 0 and j == n - 2:
                continue
            if _segments_intersect(
                coordenadas[i],     coordenadas[i + 1],
                coordenadas[j],     coordenadas[j + 1],
            ):
                intersections .append({"segmento_a": i, "segmento_b": j})
    return intersections 