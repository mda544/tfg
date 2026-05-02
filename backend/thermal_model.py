import math
import datetime
from dataclasses import dataclass
from typing import Literal

# pypacity imports
from cable import cable as cable_module
from case  import case  as case_module
from ieee738 import ieee738 as ieee738_module

@dataclass
class ConductorParams:
    diametro_mm:      float
    r_ac_75_ohm_km:   float   
    r_ac_25_ohm_km:   float   
    emisividad:       float
    absortividad:     float
    temp_max_c:       float

@dataclass
class MeteoParams:
    temp_amb_c:           float
    vel_viento_ms:        float
    angulo_viento_deg:    float
    radiacion_solar_wm2:  float
    altitud_m:            float = 0.0

@dataclass
class RateResult:
    ampacidad_a:       float
    temp_conductor_c:  float
    qc_wm:             float
    qr_wm:             float
    qs_wm:             float
    r_tc_ohm_m:        float
    modo_conveccion:   Literal["forzada_baja", "forzada_alta", "natural"]

def _dia_del_anio() -> int:
    return datetime.date.today().timetuple().tm_yday

class IEEE738Calculator:
    def calcular(
        self,
        conductor: ConductorParams,
        meteo: MeteoParams,
        latitud_deg: float = 43.0,
        azimut_linea_deg: float = 90.0, 
    ) -> RateResult:
        
        # 1. Configurar conductor
        cab = cable_module.Cable()
        cab.Cstring  = "custom"
        cab.D        = conductor.diametro_mm             
        cab.d        = conductor.diametro_mm * 0.15      
        cab.TLO      = 25.0                              
        cab.THI      = 75.0                              
        cab.TCDRMAX  = conductor.temp_max_c
        cab.RLO      = conductor.r_ac_25_ohm_km / 1000.0  
        cab.RHI      = conductor.r_ac_75_ohm_km / 1000.0
        cab.EMISS    = conductor.emisividad
        cab.ABSORP   = conductor.absortividad
        cab.HNH      = 2          
        cab.HEATOUT  = 700.0      # Valores dummy (solo afectan a transitorios)
        cab.HEATCORE = 200.0      # Valores dummy (solo afectan a transitorios)
        cab.HEATCAP  = cab.HEATOUT + cab.HEATCORE

        # 2. Configurar caso meteorológico 
        cas = case_module.Case()
        cas.NSELECT      = 2             # Modo estacionario
        cas.IORTPRELOAD  = 1
        cas.SORM         = 0
        cas.TT           = 0
        cas.DELTIME      = 10
        cas.TCDRPRELOAD  = conductor.temp_max_c   
        cas.XIPRELOAD    = 0.0
        cas.XISTEP       = 0.0

        # Meteorología base
        cas.TAMB         = meteo.temp_amb_c
        cas.VWIND        = max(meteo.vel_viento_ms, 0.01)   
        cas.DWIND_DEG    = 90.0
        cas.WINDANG_DEG  = meteo.angulo_viento_deg
        
        # Blindaje de la altitud
        cas.CDR_ELEV     = float(meteo.altitud_m) if meteo.altitud_m is not None else 0.0

        # Radiación solar
        cas.SOLAR           = 1
        cas.SolarRadiation  = float(meteo.radiacion_solar_wm2) if meteo.radiacion_solar_wm2 is not None else 0.0   

        # Campos de posición solar obligatorios
        cas.CDR_LAT_DEG  = latitud_deg
        cas.NDAY         = _dia_del_anio()
        cas.SUN_TIME     = 14               
        cas.A3           = 0                
        cas.Ns           = 1.0
        cas.ALBEDO       = 0.2

        # Azimut (Limitado a 180º para modelar el cilindro)
        azimut_seguro    = float(azimut_linea_deg) if azimut_linea_deg is not None else 90.0
        cas.Z1_DEG       = azimut_seguro % 180.0
        cas.beta         = 0.0   

        cas.ATCDR        = []
        cas.TIME         = []
        cas.TR           = None
        cas.TCDR         = conductor.temp_max_c

        # 3. Ejecutar 
        calc = ieee738_module.IEEE738()
        calc.Debug = 0          
        calc.set_cable(cab)
        calc.set_case(cas)
        calc.ieee_738_2013()

        # 4. Extraer resultados
        ampacidad = float(cas.TR) if cas.TR is not None else 0.0
        qc = float(cas.QC) if cas.QC is not None else 0.0
        qr = float(cas.QR) if cas.QR is not None else 0.0
        qs = float(cas.QS) if cas.QS is not None else 0.0

        tc     = conductor.temp_max_c
        r_lo   = conductor.r_ac_25_ohm_km / 1000.0
        r_hi   = conductor.r_ac_75_ohm_km / 1000.0
        r_tc   = r_lo + (r_hi - r_lo) * (tc - 25.0) / 50.0

        # Inferencia lógica de la convección
        modo = "forzada_baja" if meteo.vel_viento_ms >= 0.5 else "natural"

        return RateResult(
            ampacidad_a      = round(ampacidad, 1),
            temp_conductor_c = tc,
            qc_wm            = round(qc, 2),
            qr_wm            = round(qr, 2),
            qs_wm            = round(qs, 2),
            r_tc_ohm_m       = round(r_tc, 6),
            modo_conveccion  = modo,   
        )