import math
import traceback
import asyncio
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from thermal_model import IEEE738Calculator, ConductorParams, MeteoParams
from seasonal_scenarios import ESCENARIOS_DEFAULT, SeasonalRates, ScenarioMeteo, Season
from segmentation import segmentar_trazado, segmentar_por_apoyos

from geometry_validation import validar_trazado
from dem_elevation import enriquecer_coordenadas_con_dem
from historical_cache import obtener_percentiles  

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
calculator = IEEE738Calculator()

# Modelos Pydantic
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
    usar_dem: bool = True  

# Endpoint principal
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
        coordenadas_ricas = req.coordenadas
        fuente_altitud = "sin_altitud"

        tiene_z_excel = any((c.get("altitud") or 0) > 0 for c in req.coordenadas)

        if tiene_z_excel:
            fuente_altitud = "excel_z"
        elif req.usar_dem:
            try:
                coordenadas_ricas = await enriquecer_coordenadas_con_dem(req.coordenadas)
                fuente_altitud = "open_meteo_dem"
            except Exception as e:
                print(f"[DEM] Enriquecimiento falló: {e}")
                fuente_altitud = "sin_altitud_error"

        # 3. CONFIGURACIÓN DEL CONDUCTOR
        conductor = ConductorParams(**req.conductor.model_dump())

        # 4. ESCENARIOS METEOROLÓGICOS
        escenarios = {
            s.estacion: ScenarioMeteo(**s.model_dump(), nombre=s.estacion)
            for s in req.escenarios
        } if req.escenarios else ESCENARIOS_DEFAULT

        # 5. SEGMENTACIÓN DEL TRAZADO
        if req.usar_apoyos_reales and len(coordenadas_ricas) >= 2:
            tramos = segmentar_por_apoyos(coordenadas_ricas)
            modo_segmentacion = f"vanos_reales ({len(tramos)} vanos)"
        elif req.paso_segmentacion_m > 0:
            tramos = segmentar_trazado(coordenadas_ricas, req.paso_segmentacion_m)
            modo_segmentacion = f"cada_{req.paso_segmentacion_m:.0f}m"
        else:
            raise HTTPException(status_code=400, detail="Segmentación inválida.")

        if not tramos:
            raise HTTPException(status_code=400, detail="No se pudieron generar tramos.")

        # 6. CÁLCULO TÉRMICO IEEE 738 POR TRAMO
        resultados = []
        for tramo in tramos:            
            
            lat_tramo = tramo.punto_medio["lat"]               
            altitud_segura = float(tramo.altitud_m) if tramo.altitud_m is not None else 0.0

            seasonal = SeasonalRates(
                id_tramo=tramo.id,
                longitud_km=tramo.longitud_km,
                altitud_media_m=altitud_segura,
            )

            for estacion, escenario in escenarios.items():
                meteo = MeteoParams(
                    temp_amb_c=escenario.temp_amb_c,
                    vel_viento_ms=escenario.vel_viento_ms,
                    angulo_viento_deg=escenario.angulo_viento_deg,
                    radiacion_solar_wm2=escenario.radiacion_solar_wm2,
                    altitud_m=altitud_segura,
                )
                
                # INYECTAR PARÁMETROS GEOGRÁFICOS DINÁMICOS
                resultado = calculator.calcular(
                    conductor=conductor, 
                    meteo=meteo,
                    latitud_deg=lat_tramo,
                    azimut_linea_deg=tramo.azimut_deg                 
                )
                
                seasonal.rates[estacion] = resultado.ampacidad_a
                seasonal.detalles[estacion] = {
                    "ampacidad_a": resultado.ampacidad_a,
                    "qc_wm": resultado.qc_wm,
                    "qr_wm": resultado.qr_wm,
                    "qs_wm": resultado.qs_wm,
                    "r_tc_ohm_m": resultado.r_tc_ohm_m,
                    "modo_conveccion": resultado.modo_conveccion,
                    "altitud_m": altitud_segura,
                    "escenario": {
                        "temp_amb_c": escenario.temp_amb_c,
                        "vel_viento_ms": escenario.vel_viento_ms,
                        "radiacion_wm2": escenario.radiacion_solar_wm2,
                    },
                }

            resultados.append({
                "id_tramo": seasonal.id_tramo,
                "longitud_km": seasonal.longitud_km,
                "altitud_m": altitud_segura,
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
        print("--- ERROR INTERNO ---")
        traceback.print_exc() 
        print("---------------------")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint de climatología

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


# Endpoint de altitud puntual (para debug/preview)

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