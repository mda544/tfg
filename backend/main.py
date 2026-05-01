from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from thermal_model import IEEE738Calculator, ConductorParams, MeteoParams
from seasonal_scenarios import ESCENARIOS_DEFAULT, SeasonalRates, ScenarioMeteo, Season
from segmentation import segmentar_trazado, segmentar_por_apoyos
from geometry_validation import validar_trazado
from dem_elevation import enriquecer_coordenadas_con_dem
from historical_cache import obtener_percentiles

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
calculator = IEEE738Calculator()


# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class ConductorInput(BaseModel):
    diametro_mm: float
    r_ac_75_ohm_km: float
    r_ac_25_ohm_km: float
    emisividad: float = 0.5
    absortividad: float = 0.5
    temp_max_c: float = 90.0

class ScenarioInput(BaseModel):
    estacion: Season
    temp_amb_c: float
    vel_viento_ms: float
    angulo_viento_deg: float = 90.0
    radiacion_solar_wm2: float

class CalculoRequest(BaseModel):
    coordenadas: List[dict]
    conductor: ConductorInput
    escenarios: Optional[List[ScenarioInput]] = None
    paso_segmentacion_m: float = 500.0
    usar_apoyos_reales: bool = False
    usar_dem: bool = True  # Nuevo: activar/desactivar consulta DEM


# ── Endpoint principal ────────────────────────────────────────────────────────

@app.post("/calcular/rates-estacionales")
async def calcular_rates_estacionales(req: CalculoRequest):
    try:
        # 1. VALIDACIÓN GEOMÉTRICA
        val = validar_trazado([
            {"lat": c["lat"], "lng": c.get("lng") or c.get("lon", 0)}
            for c in req.coordenadas
        ])
        if not val.valido:
            raise HTTPException(status_code=422, detail={
                "errores": val.errores,
                "advertencias": val.advertencias,
                "info": val.info,
            })

        # 2. ENRIQUECIMIENTO CON DEM
        # Si las coordenadas ya tienen altitud (Excel con Z) o el usuario activó DEM,
        # enriquecemos. Si todas las altitudes son 0 y usar_dem=True, consultamos la API.
        coordenadas_ricas = req.coordenadas
        fuente_altitud = "sin_altitud"

        tiene_z_excel = any(
            (c.get("altitud") or 0) > 0 for c in req.coordenadas
        )

        if tiene_z_excel:
            # Ya tenemos altitudes del Excel — no consultamos DEM externo
            coordenadas_ricas = req.coordenadas
            fuente_altitud = "excel_z"
        elif req.usar_dem:
            # Consultamos Open-Meteo Elevation API
            try:
                coordenadas_ricas = await enriquecer_coordenadas_con_dem(req.coordenadas)
                fuente_altitud = "open_meteo_dem"
            except Exception as e:
                print(f"[DEM] Enriquecimiento falló, continuando sin altitud: {e}")
                coordenadas_ricas = req.coordenadas
                fuente_altitud = "sin_altitud_error"

        # 3. CONFIGURACIÓN DEL CONDUCTOR
        conductor = ConductorParams(
            diametro_mm=req.conductor.diametro_mm,
            r_ac_75_ohm_km=req.conductor.r_ac_75_ohm_km,
            r_ac_25_ohm_km=req.conductor.r_ac_25_ohm_km,
            emisividad=req.conductor.emisividad,
            absortividad=req.conductor.absortividad,
            temp_max_c=req.conductor.temp_max_c,
        )

        # 4. ESCENARIOS METEOROLÓGICOS
        if req.escenarios:
            escenarios = {
                s.estacion: ScenarioMeteo(
                    nombre=s.estacion,
                    estacion=s.estacion,
                    temp_amb_c=s.temp_amb_c,
                    vel_viento_ms=s.vel_viento_ms,
                    angulo_viento_deg=s.angulo_viento_deg,
                    radiacion_solar_wm2=s.radiacion_solar_wm2,
                )
                for s in req.escenarios
            }
        else:
            escenarios = ESCENARIOS_DEFAULT

        # 5. SEGMENTACIÓN DEL TRAZADO
        if req.usar_apoyos_reales and len(coordenadas_ricas) >= 2:
            tramos = segmentar_por_apoyos(coordenadas_ricas)
            modo_segmentacion = f"vanos_reales ({len(tramos)} vanos)"
        elif req.paso_segmentacion_m > 0:
            tramos = segmentar_trazado(coordenadas_ricas, req.paso_segmentacion_m)
            modo_segmentacion = f"cada_{req.paso_segmentacion_m:.0f}m"
        else:
            from segmentation import proyectar_linea, Tramo
            linea = proyectar_linea(coordenadas_ricas)
            mid = coordenadas_ricas[len(coordenadas_ricas) // 2]
            lon_0 = req.coordenadas[0].get("lon") or req.coordenadas[0].get("lng")
            lon_f = req.coordenadas[-1].get("lon") or req.coordenadas[-1].get("lng")
            tramos = [Tramo(
                id="V001", indice=0,
                punto_inicio={"lat": req.coordenadas[0]["lat"], "lon": lon_0},
                punto_medio={"lat": mid["lat"], "lon": mid.get("lon") or mid.get("lng")},
                punto_fin={"lat": req.coordenadas[-1]["lat"], "lon": lon_f},
                longitud_km=round(linea.length / 1000.0, 3),
                altitud_m=0.0,
            )]
            modo_segmentacion = "tramo_unico"

        if not tramos:
            raise HTTPException(status_code=400, detail="No se pudieron generar tramos.")

        # 6. CÁLCULO TÉRMICO IEEE 738 POR TRAMO
        resultados = []
        for tramo in tramos:
            seasonal = SeasonalRates(
                id_tramo=tramo.id,
                longitud_km=tramo.longitud_km,
                altitud_media_m=tramo.altitud_m,
            )

            for estacion, escenario in escenarios.items():
                meteo = MeteoParams(
                    temp_amb_c=escenario.temp_amb_c,
                    vel_viento_ms=escenario.vel_viento_ms,
                    angulo_viento_deg=escenario.angulo_viento_deg,
                    radiacion_solar_wm2=escenario.radiacion_solar_wm2,
                    altitud_m=tramo.altitud_m,  # ← aquí entra el DEM
                )
                resultado = calculator.calcular(conductor, meteo)
                seasonal.rates[estacion] = resultado.ampacidad_a
                seasonal.detalles[estacion] = {
                    "ampacidad_a": resultado.ampacidad_a,
                    "qc_wm": resultado.qc_wm,
                    "qr_wm": resultado.qr_wm,
                    "qs_wm": resultado.qs_wm,
                    "r_tc_ohm_m": resultado.r_tc_ohm_m,
                    "modo_conveccion": resultado.modo_conveccion,
                    "altitud_m": tramo.altitud_m,
                    "escenario": {
                        "temp_amb_c": escenario.temp_amb_c,
                        "vel_viento_ms": escenario.vel_viento_ms,
                        "radiacion_wm2": escenario.radiacion_solar_wm2,
                    },
                }

            resultados.append({
                "id_tramo": seasonal.id_tramo,
                "longitud_km": seasonal.longitud_km,
                "altitud_m": tramo.altitud_m,
                "punto_medio": tramo.punto_medio,
                "punto_inicio": tramo.punto_inicio,
                "punto_fin": tramo.punto_fin,
                "rates": seasonal.rates,
                "detalles": seasonal.detalles,
                "rate_diseno_a": min(seasonal.rates.values()),
            })

        # 7. RESUMEN Y RESPUESTA
        return {
            "status": "ok",
            "n_tramos": len(resultados),
            "conductor": req.conductor.model_dump(),
            "tramos": resultados,
            "rate_linea_diseno_a": min(t["rate_diseno_a"] for t in resultados),
            "rates_por_estacion": {
                est: min(t["rates"].get(est, 9999) for t in resultados)
                for est in escenarios
            },
            "info_trazado": {
                **val.info,
                "fuente_altitud": fuente_altitud,
                "modo_segmentacion": modo_segmentacion,
                "altitud_min_m": min(t["altitud_m"] for t in resultados),
                "altitud_max_m": max(t["altitud_m"] for t in resultados),
                "altitud_media_m": round(
                    sum(t["altitud_m"] for t in resultados) / len(resultados), 1
                ),
            },
            "advertencias_validacion": val.advertencias,
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Endpoint de climatología ──────────────────────────────────────────────────

@app.get("/climatologia/percentiles")
async def get_percentiles(
    lat: float,
    lon: float,
    fuente: str = "openmeteo",
    anio_inicio: int = 1990,
    anio_fin: int = 2023,
):
    try:
        percentiles = await obtener_percentiles(lat, lon, fuente, anio_inicio, anio_fin)
        return {
            "status": "ok",
            "fuente": fuente,
            "punto": {"lat": lat, "lon": lon},
            "percentiles": {
                est: {
                    "temp_p10_c":        p.temp_p10_c,
                    "temp_p50_c":        p.temp_p50_c,
                    "temp_p90_c":        p.temp_p90_c,
                    "viento_p10_ms":     p.viento_p10_ms,
                    "viento_p50_ms":     p.viento_p50_ms,
                    "viento_p90_ms":     p.viento_p90_ms,
                    "radiacion_p50_wm2": p.radiacion_p50_wm2,
                    "radiacion_p90_wm2": p.radiacion_p90_wm2,
                    "n_horas":           p.n_horas,
                    "fuente":            p.fuente,
                    "anios_cubiertos":   p.anios_cubiertos,
                }
                for est, p in percentiles.items()
            },
        }
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}


# ── Endpoint de altitud puntual (para debug/preview) ─────────────────────────

@app.get("/dem/altitud")
async def get_altitud_punto(lat: float, lon: float):
    """Devuelve la altitud de un punto según Open-Meteo DEM."""
    try:
        resultado = await enriquecer_coordenadas_con_dem([{"lat": lat, "lng": lon}])
        return {
            "status": "ok",
            "lat": lat,
            "lon": lon,
            "altitud_m": resultado[0].get("altitud", 0),
        }
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}