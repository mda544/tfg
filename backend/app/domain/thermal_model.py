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

    def _build_cable(self, conductor: ConductorParams) -> cable_module.Cable:
        """Traduce ConductorParams al objeto Cable de pypacity."""
        cab = cable_module.Cable()
        cab.Cstring  = "custom"
        cab.D        = conductor.diametro_mm
        cab.d        = conductor.diametro_mm * 0.15   # hilo externo ~15 % del diámetro total
        cab.TLO      = 25.0
        cab.THI      = 75.0
        cab.TCDRMAX  = conductor.temp_max_c
        cab.RLO      = conductor.r_ac_25_ohm_km / 1000.0
        cab.RHI      = conductor.r_ac_75_ohm_km / 1000.0
        cab.EMISS    = conductor.emisividad
        cab.ABSORP   = conductor.absortividad
        return cab

    def _build_case(
        self,
        meteo: MeteoParams,
        latitud_deg: float,
        azimut_linea_deg: float,
        temp_max_c: float,
    ) -> case_module.Case:
        """Traduce MeteoParams + parámetros geográficos al objeto Case de pypacity."""
        cas = case_module.Case()
        cas.demo(2)  # 2 = cálculo estacionario (ampacidad)

        cas.TAMB           = meteo.temp_amb_c
        cas.VWIND          = max(meteo.vel_viento_ms, 0.01)
        cas.WINDANG_DEG    = meteo.angulo_viento_deg
        cas.CDR_ELEV       = float(meteo.altitud_m or 0.0)

        cas.SOLAR          = 1
        cas.SolarRadiation = float(meteo.radiacion_solar_wm2 or 0.0)

        cas.CDR_LAT_DEG    = latitud_deg
        cas.NDAY           = _dia_del_anio()
        cas.SUN_TIME       = 14       # hora solar pico conservadora
        cas.A3             = 0        # atmósfera limpia
        cas.Ns             = 1.0      # ratio de claridad estándar
        cas.ALBEDO         = 0.2      # suelo/urbano

        cas.Z1_DEG         = float(azimut_linea_deg or 90.0) % 180.0
        cas.beta           = 0.0

        cas.TCDR           = temp_max_c
        return cas

    def calcular(
        self,
        conductor: ConductorParams,
        meteo: MeteoParams,
        latitud_deg: float = 43.0,
        azimut_linea_deg: float = 90.0,
    ) -> RateResult:
        cab  = self._build_cable(conductor)
        cas  = self._build_case(meteo, latitud_deg, azimut_linea_deg, conductor.temp_max_c)

        calc = ieee738_module.IEEE738()
        calc.Debug = 0
        calc.set_cable(cab)
        calc.set_case(cas)
        calc.ieee_738_2013()

        ampacidad = float(cas.TR or 0.0)
        qc        = float(cas.QC or 0.0)
        qr        = float(cas.QR or 0.0)
        qs        = float(cas.QS or 0.0)

        tc   = conductor.temp_max_c
        r_lo = conductor.r_ac_25_ohm_km / 1000.0
        r_hi = conductor.r_ac_75_ohm_km / 1000.0
        r_tc = r_lo + (r_hi - r_lo) * (tc - 25.0) / 50.0

        if meteo.vel_viento_ms >= 2.0:
            modo: Literal["forzada_baja", "forzada_alta", "natural"] = "forzada_alta"
        elif meteo.vel_viento_ms >= 0.5:
            modo = "forzada_baja"
        else:
            modo = "natural"

        return RateResult(
            ampacidad_a      = round(ampacidad, 1),
            temp_conductor_c = tc,
            qc_wm            = round(qc, 2),
            qr_wm            = round(qr, 2),
            qs_wm            = round(qs, 2),
            r_tc_ohm_m       = round(r_tc, 6),
            modo_conveccion  = modo,
        )