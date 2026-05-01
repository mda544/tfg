"""
dem_elevation.py
----------------
Obtención de altitudes para puntos del trazado.

Estrategia en cascada (primera que responda gana):
  1. Open-Meteo Elevation API  — SRTM/Copernicus, batch de hasta 100 puntos, sin registro
  2. Open-Topo-Data SRTM       — fallback, 1 punto por request
  3. Z del Excel               — si el punto ya trae altitud, no se consulta nada

La API de Open-Meteo es la preferida porque:
  - Sin registro ni API key
  - Batch hasta 100 puntos en una sola request
  - Fuente: SRTM 90m + Copernicus DEM 30m fusionados
  - Cobertura global
"""

import httpx
import asyncio
import math
import json
import hashlib
from pathlib import Path
from typing import Optional

# ── Caché en disco para no repetir consultas ─────────────────────────────────
CACHE_DIR = Path("dem_cache")
CACHE_DIR.mkdir(exist_ok=True)

def _clave_cache(lat: float, lon: float) -> str:
    # Redondear a 0.001° (~100m) — resolución suficiente para el DEM
    lat_r = round(lat, 3)
    lon_r = round(lon, 3)
    return hashlib.md5(f"{lat_r}_{lon_r}".encode()).hexdigest()[:10]

def _leer_cache(lat: float, lon: float) -> Optional[float]:
    ruta = CACHE_DIR / f"{_clave_cache(lat, lon)}.json"
    if ruta.exists():
        return json.loads(ruta.read_text())["altitud_m"]
    return None

def _escribir_cache(lat: float, lon: float, altitud_m: float):
    ruta = CACHE_DIR / f"{_clave_cache(lat, lon)}.json"
    ruta.write_text(json.dumps({"lat": lat, "lon": lon, "altitud_m": altitud_m}))


# ── Open-Meteo Elevation API (batch) ─────────────────────────────────────────

async def _consultar_openmeteo_batch(
    puntos: list[tuple[float, float]]
) -> list[Optional[float]]:
    """
    Consulta altitudes en batch via Open-Meteo Elevation API.
    Acepta hasta 100 puntos por request.
    https://open-meteo.com/en/docs/elevation-api
    """
    if not puntos:
        return []

    # Dividir en chunks de 100
    resultados = []
    for i in range(0, len(puntos), 100):
        chunk = puntos[i:i + 100]
        lats = ",".join(f"{p[0]:.6f}" for p in chunk)
        lons = ",".join(f"{p[1]:.6f}" for p in chunk)

        url = "https://api.open-meteo.com/v1/elevation"
        params = {"latitude": lats, "longitude": lons}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                datos = r.json()
                elevaciones = datos.get("elevation", [])
                resultados.extend(
                    float(e) if e is not None else None
                    for e in elevaciones
                )
        except Exception as e:
            print(f"[DEM] Open-Meteo batch falló para chunk {i}: {e}")
            resultados.extend([None] * len(chunk))

    return resultados


# ── Open-Topo-Data (fallback, punto a punto) ──────────────────────────────────

async def _consultar_opentopodata(lat: float, lon: float) -> Optional[float]:
    """Fallback: Open-Topo-Data SRTM30m."""
    url = f"https://api.opentopodata.org/v1/srtm30m?locations={lat:.6f},{lon:.6f}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            datos = r.json()
            results = datos.get("results", [])
            if results:
                return float(results[0].get("elevation") or 0)
    except Exception as e:
        print(f"[DEM] Open-Topo-Data falló para ({lat:.4f}, {lon:.4f}): {e}")
    return None


# ── Función principal pública ─────────────────────────────────────────────────

async def obtener_altitudes_trazado(
    coordenadas: list[dict],
) -> list[float]:
    """
    Dada una lista de coordenadas {lat, lng/lon, [altitud]},
    devuelve una lista de altitudes en metros para cada punto.

    Prioridad:
      1. altitud ya presente en el punto (viene del Excel con columna Z)
      2. caché en disco de consultas anteriores
      3. Open-Meteo Elevation API (batch)
      4. Open-Topo-Data (fallback punto a punto)
      5. 0.0 si todo falla
    """
    n = len(coordenadas)
    altitudes = [0.0] * n
    pendientes_idx = []   # índices que necesitan consulta externa
    pendientes_pts = []   # (lat, lon) de esos índices

    for i, c in enumerate(coordenadas):
        # 1. Altitud en el propio objeto (Excel con columna Z)
        alt_existente = c.get("altitud") or c.get("z") or c.get("elevation")
        if alt_existente and float(alt_existente) > 0:
            altitudes[i] = float(alt_existente)
            continue

        lat = c["lat"]
        lon = c.get("lon") or c.get("lng", 0)

        # 2. Caché en disco
        cached = _leer_cache(lat, lon)
        if cached is not None:
            altitudes[i] = cached
            continue

        pendientes_idx.append(i)
        pendientes_pts.append((lat, lon))

    if not pendientes_pts:
        return altitudes

    # 3. Consulta batch a Open-Meteo
    print(f"[DEM] Consultando altitudes para {len(pendientes_pts)} puntos via Open-Meteo...")
    resultados_batch = await _consultar_openmeteo_batch(pendientes_pts)

    # 4. Para los que fallaron, intentar fallback
    aun_pendientes = []
    for j, (idx, alt) in enumerate(zip(pendientes_idx, resultados_batch)):
        if alt is not None:
            altitudes[idx] = alt
            lat, lon = pendientes_pts[j]
            _escribir_cache(lat, lon, alt)
        else:
            aun_pendientes.append((idx, pendientes_pts[j]))

    if aun_pendientes:
        print(f"[DEM] {len(aun_pendientes)} puntos sin altitud, intentando fallback...")
        tasks = [_consultar_opentopodata(lat, lon) for _, (lat, lon) in aun_pendientes]
        fallbacks = await asyncio.gather(*tasks)
        for (idx, (lat, lon)), alt in zip(aun_pendientes, fallbacks):
            if alt is not None:
                altitudes[idx] = alt
                _escribir_cache(lat, lon, alt)
            else:
                altitudes[idx] = 0.0  # último recurso

    return altitudes


async def enriquecer_coordenadas_con_dem(
    coordenadas: list[dict],
) -> list[dict]:
    """
    Devuelve una copia de las coordenadas con el campo 'altitud' relleno.
    No modifica los objetos originales.
    """
    altitudes = await obtener_altitudes_trazado(coordenadas)
    enriquecidas = []
    for c, alt in zip(coordenadas, altitudes):
        nuevo = dict(c)
        if not (nuevo.get("altitud") and float(nuevo["altitud"]) > 0):
            nuevo["altitud"] = alt
        enriquecidas.append(nuevo)
    return enriquecidas