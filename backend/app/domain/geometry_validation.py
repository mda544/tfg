from app.domain.entities import ValidationResult
from app.core.utils.geo import haversine_m

COBERTURAS = {
    "Open-Meteo":            {"lat": (-90,  90), "lon": (-180, 180)},
    "NASA POWER":            {"lat": (-90,  90), "lon": (-180, 180)},
    "Copernicus DEM GLO-30": {"lat": (-90,  84), "lon": (-180, 180)},
}

LIMITES = {
    "min_puntos":          2,
    "min_longitud_m":      100,
    "max_longitud_km":     500,
    "max_bbox_grados":     10,
    "max_separacion_km":   50,
    "max_autocruce_check": 200,
}


def validar_trazado(coordenadas: list[dict]) -> ValidationResult:
    errores      = []
    advertencias = []
    info         = {"n_puntos": len(coordenadas)}

    if len(coordenadas) < LIMITES["min_puntos"]:
        return ValidationResult(
            valido=False,
            errores=[f"Trazado con {len(coordenadas)} punto(s). Mínimo: {LIMITES['min_puntos']}."],
            info=info,
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
        return ValidationResult(valido=False, errores=errores, info=info)

    lats = [c["lat"] for c in coordenadas]
    lons = [c["lon"] for c in coordenadas]
    bbox = {
        "min_lat": min(lats), "max_lat": max(lats),
        "min_lon": min(lons), "max_lon": max(lons),
    }
    info["bbox"] = bbox
    span_lat = bbox["max_lat"] - bbox["min_lat"]
    span_lon = bbox["max_lon"] - bbox["min_lon"]

    if span_lat > LIMITES["max_bbox_grados"] or span_lon > LIMITES["max_bbox_grados"]:
        advertencias.append(
            f"Bounding box amplio: {span_lat:.1f}° lat × {span_lon:.1f}° lon. "
            f"Verifica que no haya coordenadas erróneas."
        )

    longitud_m  = sum(
        haversine_m(coordenadas[i], coordenadas[i + 1])
        for i in range(len(coordenadas) - 1)
    )
    longitud_km = longitud_m / 1000.0
    info["longitud_km"] = round(longitud_km, 2)

    if longitud_m < LIMITES["min_longitud_m"]:
        errores.append(
            f"Longitud demasiado corta: {longitud_m:.0f} m. "
            f"Mínimo: {LIMITES['min_longitud_m']} m."
        )
    elif longitud_km > LIMITES["max_longitud_km"]:
        advertencias.append(
            f"Longitud elevada: {longitud_km:.0f} km. "
            f"El cálculo puede tardar varios minutos."
        )

    tramos_largos = []
    for i in range(len(coordenadas) - 1):
        d_km = haversine_m(coordenadas[i], coordenadas[i + 1]) / 1000.0
        if d_km > LIMITES["max_separacion_km"]:
            tramos_largos.append({"desde": i, "hasta": i + 1, "km": round(d_km, 1)})
    if tramos_largos:
        advertencias.append(
            f"{len(tramos_largos)} tramo(s) con separación > "
            f"{LIMITES['max_separacion_km']} km entre apoyos consecutivos."
        )
    info["tramos_largos"] = tramos_largos

    for fuente, cob in COBERTURAS.items():
        fuera = [
            c for c in coordenadas
            if not (cob["lat"][0] <= c["lat"] <= cob["lat"][1])
            or not (cob["lon"][0] <= c["lon"] <= cob["lon"][1])
        ]
        if fuera:
            advertencias.append(
                f"{len(fuera)} punto(s) fuera de la cobertura de {fuente}."
            )

    if len(coordenadas) - 1 <= LIMITES["max_autocruce_check"]:
        cruces = _detectar_autocruce(coordenadas)
        if cruces:
            advertencias.append(f"El trazado se autocrusa en {len(cruces)} punto(s).")
            info["autocruces"] = cruces

    return ValidationResult(
        valido       = len(errores) == 0,
        errores      = errores,
        advertencias = advertencias,
        info         = info,
    )


def _segmentos_se_cruzan(p1, p2, p3, p4) -> bool:
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    A = (p1["lon"], p1["lat"])
    B = (p2["lon"], p2["lat"])
    C = (p3["lon"], p3["lat"])
    D = (p4["lon"], p4["lat"])
    return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))


def _detectar_autocruce(coordenadas: list[dict]) -> list[dict]:
    cruces = []
    n      = len(coordenadas)
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if i == 0 and j == n - 2:
                continue
            if _segmentos_se_cruzan(
                coordenadas[i],     coordenadas[i + 1],
                coordenadas[j],     coordenadas[j + 1],
            ):
                cruces.append({"seg_a": i, "seg_b": j})
    return cruces