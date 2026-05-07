from fastapi import HTTPException

from app.domain.geometry_validation import validar_trazado
from app.domain.thermal_model import IEEE738Calculator, ConductorParams, MeteoParams
from app.domain.segmentation import segmentar_trazado, segmentar_por_apoyos
from app.domain.seasonal_scenarios import ESCENARIOS_DEFAULT, SeasonalRates, ScenarioMeteo
from app.domain.types import Season
from app.infrastructure.cache.dem_cache import enriquecer_coordenadas_con_dem
from app.api.schemas.models import CalculoRequest

_calculator = IEEE738Calculator()


def _normalizar_coordenadas(coordenadas: list[dict]) -> list[dict]:
    
    # Normaliza todas las coordenadas a la clave 'lon'.
    
    normalizadas = []
    for c in coordenadas:
        punto = {
            "lat": c["lat"],
            "lon": c.get("lon") or c.get("lng", 0),
        }
        if c.get("altitud"):
            punto["altitud"] = c["altitud"]
        normalizadas.append(punto)
    return normalizadas


async def calcular_rates_estacionales(req: CalculoRequest) -> dict:

    # 1. Normalización de coordenadas a clave canónica 'lon'
    coordenadas = _normalizar_coordenadas(req.coordenadas)

    # 2. Validación geométrica
    val = validar_trazado(coordenadas)
    if not val.valido:
        raise HTTPException(status_code=422, detail={
            "errores":      val.errores,
            "advertencias": val.advertencias,
            "info":         val.info,
        })

    # 3. Enriquecimiento DEM
    fuente_altitud  = "sin_altitud"
    tiene_z_excel   = any((c.get("altitud") or 0) > 0 for c in coordenadas)

    if tiene_z_excel:
        fuente_altitud = "excel_z"
    elif req.usar_dem:
        try:
            coordenadas    = await enriquecer_coordenadas_con_dem(coordenadas)
            fuente_altitud = "open_meteo_dem"
        except Exception as e:
            print(f"[DEM] Enriquecimiento falló: {e}")
            fuente_altitud = "sin_altitud_error"

    # 4. Conductor
    conductor = ConductorParams(**req.conductor.model_dump())

    # 5. Escenarios meteorológicos
    escenarios: dict[Season, ScenarioMeteo] = (
        {
            s.estacion: ScenarioMeteo(
                nombre               = s.estacion,
                estacion             = s.estacion,
                temp_amb_c           = s.temp_amb_c,
                vel_viento_ms        = s.vel_viento_ms,
                angulo_viento_deg    = s.angulo_viento_deg,
                radiacion_solar_wm2  = s.radiacion_solar_wm2,
            )
            for s in req.escenarios
        }
        if req.escenarios
        else ESCENARIOS_DEFAULT
    )

    # 6. Segmentación — usa las coordenadas normalizadas y enriquecidas
    if req.usar_apoyos_reales and len(coordenadas) >= 2:
        tramos            = segmentar_por_apoyos(coordenadas)
        modo_segmentacion = f"vanos_reales ({len(tramos)} vanos)"
    elif req.paso_segmentacion_m > 0:
        tramos            = segmentar_trazado(coordenadas, req.paso_segmentacion_m)
        modo_segmentacion = f"cada_{req.paso_segmentacion_m:.0f}m"
    else:
        raise HTTPException(status_code=400, detail="Segmentación inválida.")

    if not tramos:
        raise HTTPException(status_code=400, detail="No se pudieron generar tramos.")

    # 7. Cálculo térmico IEEE 738 por tramo
    resultados = []
    for tramo in tramos:
        lat_tramo      = tramo.punto_medio["lat"]
        altitud_segura = float(tramo.altitud_m or 0.0)

        seasonal = SeasonalRates(
            id_tramo        = tramo.id,
            longitud_km     = tramo.longitud_km,
            altitud_media_m = altitud_segura,
        )

        for estacion, escenario in escenarios.items():
            meteo = MeteoParams(
                temp_amb_c          = escenario.temp_amb_c,
                vel_viento_ms       = escenario.vel_viento_ms,
                angulo_viento_deg   = escenario.angulo_viento_deg,
                radiacion_solar_wm2 = escenario.radiacion_solar_wm2,
                altitud_m           = altitud_segura,
            )
            resultado = _calculator.calcular(
                conductor        = conductor,
                meteo            = meteo,
                latitud_deg      = lat_tramo,
                azimut_linea_deg = tramo.azimut_deg,
            )

            seasonal.rates[estacion]    = resultado.ampacidad_a
            seasonal.detalles[estacion] = {
                "ampacidad_a":     resultado.ampacidad_a,
                "qc_wm":           resultado.qc_wm,
                "qr_wm":           resultado.qr_wm,
                "qs_wm":           resultado.qs_wm,
                "r_tc_ohm_m":      resultado.r_tc_ohm_m,
                "modo_conveccion": resultado.modo_conveccion,
                "altitud_m":       altitud_segura,
                "escenario": {
                    "temp_amb_c":    escenario.temp_amb_c,
                    "vel_viento_ms": escenario.vel_viento_ms,
                    "radiacion_wm2": escenario.radiacion_solar_wm2,
                },
            }

        resultados.append({
            "id_tramo":      seasonal.id_tramo,
            "longitud_km":   seasonal.longitud_km,
            "altitud_m":     altitud_segura,
            "punto_medio":   tramo.punto_medio,
            "punto_inicio":  tramo.punto_inicio,
            "punto_fin":     tramo.punto_fin,
            "rates":         seasonal.rates,
            "detalles":      seasonal.detalles,
            "rate_diseno_a": min(seasonal.rates.values()),
        })

    # 8. Respuesta
    return {
        "n_tramos":  len(resultados),
        "conductor": req.conductor.model_dump(),
        "tramos":    resultados,
        "rate_linea_diseno_a": min(t["rate_diseno_a"] for t in resultados),
        "rates_por_estacion": {
            est: min(t["rates"].get(est, 9999) for t in resultados)
            for est in escenarios
        },
        "info_trazado": {
            **val.info,
            "fuente_altitud":    fuente_altitud,
            "modo_segmentacion": modo_segmentacion,
            "altitud_min_m":     min(t["altitud_m"] for t in resultados),
            "altitud_max_m":     max(t["altitud_m"] for t in resultados),
            "altitud_media_m":   round(
                sum(t["altitud_m"] for t in resultados) / len(resultados), 1
            ),
        },
        "advertencias_validacion": val.advertencias,
    }
