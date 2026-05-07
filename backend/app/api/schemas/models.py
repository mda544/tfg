from typing import List, Optional, Dict
from pydantic import BaseModel
from app.domain.types import Season


# Tipos compartidos

# Representa un punto geográfico WGS84.
# Compartido por TramoResult (inicio, medio y fin de cada tramo)
# y por PercentilesResponse (punto de consulta climática).
class PuntoGeo(BaseModel):
    lat: float
    lon: float


# Calculos: entrada

# Parámetros eléctricos y térmicos del conductor a analizar.
# Usado en CalculoRequest como campo anidado.
# En el servicio se convierte a ConductorParams (domain/thermal_model.py)
# para ser consumido por IEEE738Calculator.
class ConductorInput(BaseModel):
    diametro_mm:     float
    r_ac_75_ohm_km:  float
    r_ac_25_ohm_km:  float
    emisividad:      float = 0.5
    absortividad:    float = 0.5
    temp_max_c:      float = 90.0


# Parámetros meteorológicos de un escenario estacional personalizado.
# Usado en CalculoRequest.escenarios (lista opcional).
# Si el cliente no envía escenarios, el servicio usa ESCENARIOS_DEFAULT
# definidos en domain/seasonal_scenarios.py.
class ScenarioInput(BaseModel):
    estacion:            Season
    temp_amb_c:          float
    vel_viento_ms:       float
    angulo_viento_deg:   float = 90.0
    radiacion_solar_wm2: float


# Cuerpo de la petición del endpoint POST /calcular/rates-estacionales.
# Contiene el trazado geográfico, el conductor y la configuración
# de segmentación y escenarios. Es el único punto de entrada del cálculo.
class CalculoRequest(BaseModel):
    coordenadas:         List[dict]
    conductor:           ConductorInput
    escenarios:          Optional[List[ScenarioInput]] = None
    paso_segmentacion_m: float = 500.0
    usar_apoyos_reales:  bool  = False
    usar_dem:            bool  = True


# Calculos: respuesta

# Condiciones meteorológicas del escenario aplicado en un tramo concreto.
# Anidado dentro de DetalleTramo para que el cliente pueda saber
# exactamente con qué inputs se calculó cada ampacidad.
class DetalleEscenario(BaseModel):
    temp_amb_c:    float
    vel_viento_ms: float
    radiacion_wm2: float


# Resultado completo del cálculo IEEE 738 para un tramo y un escenario.
# Incluye los flujos de calor (qc, qr, qs), la resistencia interpolada
# y el modo de convección determinado por la velocidad del viento.
# Anidado dentro de TramoResult.detalles, indexado por estación.
class DetalleTramo(BaseModel):
    ampacidad_a:     float
    qc_wm:           float
    qr_wm:           float
    qs_wm:           float
    r_tc_ohm_m:      float
    modo_conveccion: str
    altitud_m:       float
    escenario:       DetalleEscenario


# Resultado de un tramo individual del trazado.
# Contiene su geometría (inicio, medio, fin), longitud, altitud media
# y los rates calculados para cada estación, tanto resumidos (rates)
# como con detalle completo (detalles). El rate_diseno_a es el mínimo
# de los cuatro escenarios, que es el valor limitante para el diseño.
# Usado como elemento de la lista CalculoResponse.tramos.
class TramoResult(BaseModel):
    id_tramo:      str
    longitud_km:   float
    altitud_m:     float
    punto_medio:   PuntoGeo
    punto_inicio:  PuntoGeo
    punto_fin:     PuntoGeo
    rates:         Dict[Season, float]
    detalles:      Dict[Season, DetalleTramo]
    rate_diseno_a: float


# Metadatos del trazado procesado: longitud total, número de puntos,
# fuente de altitud usada (excel_z / open_meteo_dem / sin_altitud),
# modo de segmentación aplicado y rangos de altitud.
# bbox y tramos_largos son opcionales porque solo se incluyen
# cuando la validación los detecta (trazado anómalo o vanos largos).
# Anidado en CalculoResponse.info_trazado.
class InfoTrazado(BaseModel):
    longitud_km:       float
    n_puntos:          int
    fuente_altitud:    str
    modo_segmentacion: str
    altitud_min_m:     float
    altitud_max_m:     float
    altitud_media_m:   float
    bbox:              Optional[dict] = None
    tramos_largos:     Optional[List[dict]] = None
    autocruces:        Optional[List[dict]] = None


# Respuesta completa del endpoint POST /calcular/rates-estacionales.
# Devuelve el resultado por tramo, los rates mínimos por estación
# (rates_por_estacion) y el rate de diseño global de la línea
# (rate_linea_diseno_a), que es el mínimo de todos los tramos
# en todos los escenarios. Las advertencias_validacion contienen
# avisos no bloqueantes detectados durante la validación del trazado.
class CalculoResponse(BaseModel):
    n_tramos:                int
    conductor:               ConductorInput
    tramos:                  List[TramoResult]
    rate_linea_diseno_a:     float
    rates_por_estacion:      Dict[Season, float]
    info_trazado:            InfoTrazado
    advertencias_validacion: List[str]


# Climatología: respuesta

# Percentiles estadísticos de temperatura, viento y radiación solar
# para una estación concreta, calculados sobre el periodo histórico
# configurado (por defecto 1990-2023).
# Anidado en PercentilesResponse.percentiles, indexado por Season.
# Se construye a partir de PercentilesEstacionales (infrastructure/cache/
# climate_processor.py) y se serializa aquí para la respuesta HTTP.
class PercentilesEstacionResponse(BaseModel):
    temp_p10_c:        float
    temp_p50_c:        float
    temp_p90_c:        float
    viento_p10_ms:     float
    viento_p50_ms:     float
    viento_p90_ms:     float
    radiacion_p50_wm2: float
    radiacion_p90_wm2: float
    n_horas:           int
    fuente:            str
    anios_cubiertos:   str


# Respuesta del endpoint GET /climatologia/percentiles.
# Agrupa los percentiles de las cuatro estaciones para un punto
# geográfico concreto. El campo fuente indica si los datos provienen
# de Open-Meteo (ERA5) o NASA POWER (MERRA-2), según el parámetro
# de consulta recibido.
class PercentilesResponse(BaseModel):
    fuente:      str
    punto:       PuntoGeo
    percentiles: Dict[Season, PercentilesEstacionResponse]


# DEM: respuesta

# Respuesta del endpoint GET /dem/altitud.
# Devuelve la altitud en metros de un punto concreto consultado
# contra Open-Meteo Elevation API (con fallback a Open-Topo-Data).
# Se usa principalmente para debug y preview desde el frontend,
# ya que el enriquecimiento masivo del trazado lo gestiona
# internamente dem_cache.py sin pasar por este endpoint.
class AltitudResponse(BaseModel):
    lat:       float
    lon:       float
    altitud_m: float