import datetime
from typing import Literal

from cable import cable as cable_module
from case import case as case_module
from ieee738 import ieee738 as ieee738_module

from app.domain.entities import Conductor
from app.domain.value_objects import PointMeteoConditions, SegmentRating


def _day_of_year() -> int:
    return datetime.date.today().timetuple().tm_yday


class IEEE738Calculator:

    def _build_cable(self, conductor: Conductor) -> cable_module.Cable:
        cab = cable_module.Cable()
        cab.Cstring = "custom"
        cab.D = conductor.diameter_mm
        cab.d = conductor.diameter_mm * 0.15
        cab.TLO = 25.0
        cab.THI = 75.0
        cab.TCDRMAX = conductor.max_temp_c
        cab.RLO = conductor.r_ac_25_ohm_km / 1000.0
        cab.RHI = conductor.r_ac_75_ohm_km / 1000.0
        cab.EMISS = conductor.emissivity
        cab.ABSORP = conductor.absorptivity
        return cab

    def _build_case(
        self,
        meteo: PointMeteoConditions,
        latitude_deg: float,
        line_azimuth_deg: float,
        max_temp_c: float,
    ) -> case_module.Case:
        cas = case_module.Case()
        cas.demo(2)
        cas.TAMB = meteo.temp_amb_c
        cas.VWIND = max(meteo.wind_speed_ms, 0.01)
        cas.WINDANG_DEG = meteo.wind_angle_deg
        cas.CDR_ELEV = float(meteo.elevation_m or 0.0)
        cas.SOLAR = 1
        cas.SolarRadiation = float(meteo.solar_radiation_wm2 or 0.0)
        cas.CDR_LAT_DEG = latitude_deg
        cas.NDAY = _day_of_year()
        cas.SUN_TIME = 14
        cas.A3 = 0
        cas.Ns = 1.0
        cas.ALBEDO = 0.2
        cas.Z1_DEG = float(line_azimuth_deg or 90.0) % 180.0
        cas.beta = 0.0
        cas.TCDR = max_temp_c
        return cas

    def calcular(
        self,
        conductor: Conductor,
        meteo: PointMeteoConditions,
        latitud_deg: float = 43.0,
        azimut_linea_deg: float = 90.0,
    ) -> SegmentRating:
        cab = self._build_cable(conductor)
        cas = self._build_case(
            meteo, latitud_deg, azimut_linea_deg, conductor.max_temp_c
        )

        calc = ieee738_module.IEEE738()
        calc.Debug = 0
        calc.set_cable(cab)
        calc.set_case(cas)
        calc.ieee_738_2013()

        ampacity = float(cas.TR or 0.0)
        qc = float(cas.QC or 0.0)
        qr = float(cas.QR or 0.0)
        qs = float(cas.QS or 0.0)

        tc = conductor.max_temp_c
        r_lo = conductor.r_ac_25_ohm_km / 1000.0
        r_hi = conductor.r_ac_75_ohm_km / 1000.0
        r_tc = r_lo + (r_hi - r_lo) * (tc - 25.0) / 50.0

        if meteo.wind_speed_ms >= 2.0:
            mode: Literal["forced_low", "forced_high", "natural"] = "forced_high"
        elif meteo.wind_speed_ms >= 0.5:
            mode = "forced_low"
        else:
            mode = "natural"

        return SegmentRating(
            ampacity=round(ampacity, 1),  # ← ampacity, no ampacity_a
            temp_conductor_c=tc,
            qc_wm=round(qc, 2),
            qr_wm=round(qr, 2),
            qs_wm=round(qs, 2),
            r_tc_ohm_m=round(r_tc, 6),
            conv_mode=mode,
        )
