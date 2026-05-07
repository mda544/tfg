from dataclasses import dataclass, field
from typing import Literal

from app.core.utils.geo import haversine_m


Nivel = Literal["ok", "advertencia", "error"]

# Cobertura de fuentes meteorológicas y DEM usadas en el backend
COBERTURAS = {
    "Open-Meteo":            {"lat": (-90,  90), "lon": (-180, 180)},
    "NASA POWER":            {"lat": (-90,  90), "lon": (-180, 180)},
    "Copernicus DEM GLO-30": {"lat": (-90,  84), "lon": (-180, 180)},
}

LIMITES = {
    "min_puntos":           2,
    "min_longitud_m":       100,
    "max_longitud_km":      500,
    "max_bbox_grados":      10,
    "max_separacion_km":    50,
    "max_autocruce_check":  200,  # solo revisar si hay menos de 200 segmentos
}


@dataclass
class ResultadoValidacion:
    valido: bool
    errores:      list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    info:         dict      = field(default_factory=dict)


def validar_trazado(coordenadas: list[dict]) -> ResultadoValidacion:
    """
    Validación completa del trazado en el backend.
    Recibe lista de {lat, lng} ya en WGS84 (la reproyección UTM se hace antes).
    """
    errores      = []
    advertencias = []
    info         = {}

    # 1. Mínimo de puntos
    if len(coordenadas) < LIMITES["min_puntos"]:
        return ResultadoValidacion(
            valido=False,
            errores=[f"Trazado con {len(coordenadas)} punto(s). Mínimo: {LIMITES['min_puntos']}."]
        )

    # 2. Rango WGS84 estricto
    fuera_rango = [
        i for i, c in enumerate(coordenadas)
        if not (-90 <= c["lat"] <= 90) or not (-180 <= c["lng"] <= 180)
    ]
    if fuera_rango:
        errores.append(
            f"{len(fuera_rango)} punto(s) fuera del rango WGS84 "
            f"(índices: {fuera_rango[:5]}{'…' if len(fuera_rango) > 5 else ''})."
        )
        return ResultadoValidacion(valido=False, errores=errores)

    # 3. Bounding box
    lats = [c["lat"] for c in coordenadas]
    lons = [c["lng"] for c in coordenadas]
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

    # 4. Longitud total
    longitud_m = sum(
        haversine_m(coordenadas[i], coordenadas[i + 1])
        for i in range(len(coordenadas) - 1)
    )
    longitud_km = longitud_m / 1000.0
    info["longitud_km"] = round(longitud_km, 2)

    if longitud_m < LIMITES["min_longitud_m"]:
        errores.append(
            f"Longitud del trazado demasiado corta: {longitud_m:.0f} m. "
            f"Mínimo: {LIMITES['min_longitud_m']} m."
        )
    elif longitud_km > LIMITES["max_longitud_km"]:
        advertencias.append(
            f"Longitud elevada: {longitud_km:.0f} km. "
            f"El cálculo puede tardar varios minutos."
        )

    # 5. Separación entre apoyos
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

    # 6. Cobertura de fuentes de datos
    for fuente, cob in COBERTURAS.items():
        fuera = [
            c for c in coordenadas
            if not (cob["lat"][0] <= c["lat"] <= cob["lat"][1])
            or not (cob["lon"][0] <= c["lng"] <= cob["lon"][1])
        ]
        if fuera:
            advertencias.append(
                f"{len(fuera)} punto(s) fuera de la cobertura de {fuente}. "
                f"Los datos pueden no estar disponibles para esas coordenadas."
            )

    # 7. Autocruce (solo trazados cortos)
    n_seg = len(coordenadas) - 1
    if n_seg <= LIMITES["max_autocruce_check"]:
        cruces = _detectar_autocruce(coordenadas)
        if cruces:
            advertencias.append(
                f"El trazado se autocrusa en {len(cruces)} punto(s). "
                f"Revisa el dibujo."
            )
            info["autocruces"] = cruces

    info["n_puntos"] = len(coordenadas)

    return ResultadoValidacion(
        valido=len(errores) == 0,
        errores=errores,
        advertencias=advertencias,
        info=info,
    )


def _segmentos_se_cruzan(p1, p2, p3, p4) -> bool:
    """Detecta si el segmento p1-p2 se cruza con p3-p4 (2D, ignorando extremos compartidos)."""
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    A = (p1["lng"], p1["lat"])
    B = (p2["lng"], p2["lat"])
    C = (p3["lng"], p3["lat"])
    D = (p4["lng"], p4["lat"])
    return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))


def _detectar_autocruce(coordenadas: list[dict]) -> list[dict]:
    cruces = []
    n = len(coordenadas)
    for i in range(n - 1):
        for j in range(i + 2, n - 1):
            if i == 0 and j == n - 2:
                continue  # extremos de una línea cerrada, ignorar
            if _segmentos_se_cruzan(
                coordenadas[i],     coordenadas[i + 1],
                coordenadas[j],     coordenadas[j + 1],
            ):
                cruces.append({"seg_a": i, "seg_b": j})
    return cruces