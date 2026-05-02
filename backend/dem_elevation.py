"""
Obtención de altitudes para puntos del trazado.

Estrategia en cascada (primera que responda gana):
  1. Open-Meteo Elevation API  — SRTM/Copernicus, batch de hasta 100 puntos
  2. Open-Topo-Data SRTM       — fallback, 1 punto por req (Rate limitado)
  3. Z del Excel               — si el punto ya trae altitud, no se consulta nada
"""

import httpx
import asyncio
import math
import json
import hashlib
from pathlib import Path
from typing import Optional

# Ancla la ruta al archivo actual (la carpeta /backend)
BASE_DIR = Path(__file__).resolve().parent 
CACHE_DIR = BASE_DIR / "dem_cache"
CACHE_DIR.mkdir(exist_ok=True)

# Semáforo para respetar el rate limit de Open-Topo-Data (1 req/s)
_OPENTOPODATA_SEMAPHORE = asyncio.Semaphore(1)

# Caché

def _clave_cache(lat: float, lon: float) -> str:
    lat_r = round(lat, 3)
    lon_r = round(lon, 3)
    return hashlib.md5(f"{lat_r}_{lon_r}".encode()).hexdigest()[:10]

def _leer_cache(lat: float, lon: float) -> Optional[float]:
    ruta = CACHE_DIR / f"{_clave_cache(lat, lon)}.json"
    if not ruta.exists():
        return None
    try:
        return json.loads(ruta.read_text())["altitud_m"]
    except Exception:
        # Archivo corrupto — lo ignoramos, lo borramos y forzamos nueva consulta
        ruta.unlink(missing_ok=True)
        return None

def _escribir_cache(lat: float, lon: float, altitud_m: float):
    ruta = CACHE_DIR / f"{_clave_cache(lat, lon)}.json"
    try:
        ruta.write_text(json.dumps({"lat": lat, "lon": lon, "altitud_m": altitud_m}))
    except Exception as e:
        print(f"[DEM] No se pudo escribir caché para ({lat}, {lon}): {e}")


# Open-Meteo Elevation API (batch)

async def _consultar_openmeteo_batch(
    puntos: list[tuple[float, float]]
) -> list[Optional[float]]:
    """Consulta altitudes en batch (100 pts/req). Reutiliza la conexión HTTP."""
    if not puntos:
        return []

    resultados: list[Optional[float]] = []
    
    # Un solo cliente para todos los chunks — reutiliza la conexión TCP
    async with httpx.AsyncClient(timeout=15.0) as client:
        for i in range(0, len(puntos), 100):
            chunk = puntos[i:i + 100]
            params = {
                "latitude": ",".join(f"{p[0]:.6f}" for p in chunk),
                "longitude": ",".join(f"{p[1]:.6f}" for p in chunk)
            }

            try:
                r = await client.get("https://api.open-meteo.com/v1/elevation", params=params)
                r.raise_for_status()
                elevaciones = r.json().get("elevation", [])
                resultados.extend(
                    float(e) if e is not None else None
                    for e in elevaciones
                )
            except Exception as e:
                print(f"[DEM] Open-Meteo batch falló para chunk {i}: {e}")
                resultados.extend([None] * len(chunk))

    return resultados


# Open-Topo-Data (fallback, punto a punto)

async def _consultar_opentopodata(lat: float, lon: float) -> Optional[float]:
    """Fallback: Open-Topo-Data SRTM30m. Limita a 1 petición simultánea."""
    async with _OPENTOPODATA_SEMAPHORE:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://api.opentopodata.org/v1/srtm30m",
                    params={"locations": f"{lat:.6f},{lon:.6f}"}
                )
                r.raise_for_status()
                results = r.json().get("results", [])
                if results:
                    return float(results[0].get("elevation") or 0)
        except Exception as e:
            print(f"[DEM] Open-Topo-Data falló para ({lat:.4f}, {lon:.4f}): {e}")
            
        # Pausa obligatoria entre peticiones para que no nos baneen la IP
        await asyncio.sleep(1.1)
        return None


# Función principal pública

async def obtener_altitudes_trazado(
    coordenadas: list[dict],
) -> list[float]:
    
    n = len(coordenadas)
    altitudes = [0.0] * n
    pendientes_idx = []   
    pendientes_pts = []   

    for i, c in enumerate(coordenadas):
        # 1. Altitud en el propio objeto
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

    # 4. Para los que fallaron, intentar fallback secuencial
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
                altitudes[idx] = 0.0  # Último recurso

    return altitudes


async def enriquecer_coordenadas_con_dem(
    coordenadas: list[dict],
) -> list[dict]:
    altitudes = await obtener_altitudes_trazado(coordenadas)
    enriquecidas = []
    for c, alt in zip(coordenadas, altitudes):
        nuevo = dict(c)
        if not (nuevo.get("altitud") and float(nuevo["altitud"]) > 0):
            nuevo["altitud"] = alt
        enriquecidas.append(nuevo)
    return enriquecidas