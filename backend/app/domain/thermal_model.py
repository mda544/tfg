from cable import cable as cable_module
from case import case as case_module
from ieee738 import ieee738 as ieee738_module

from app.domain.entities import Conductor
from app.domain.value_objects import PointMeteoConditions, SegmentRating
from app.domain.types import ConvMode, Season

SEASON_REPRESENTATIVE_DAY: dict[Season, int] = {
    "verano": 172,  # June 21   — solsticio de verano (dia mas largo)
    "otono": 264,  # Sept 21   — equinocio de otoño
    "invierno": 355,  # Dec 21    — solsticio de invierno (dia mas corto)
    "primavera": 80,  # March 21  — equinocio de primavera
}

# Hora con la radiacion mas alta
REPRESENTATIVE_SUN_HOUR = 14


class IEEE738Calculator:

    def _build_cable(self, conductor: Conductor) -> cable_module.Cable:
        cable = cable_module.Cable()
        cable.Cstring = "custom"
        cable.D = conductor.diameter_mm
        cable.d = conductor.diameter_mm * 0.15
        cable.TLO = 25.0
        cable.THI = 75.0
        cable.TCDRMAX = conductor.max_temp_c
        cable.RLO = conductor.r_ac_25_ohm_km / 1000.0
        cable.RHI = conductor.r_ac_75_ohm_km / 1000.0
        cable.EMISS = conductor.emissivity
        cable.ABSORP = conductor.absorptivity
        return cable

    def _build_case(
        self,
        meteo: PointMeteoConditions,
        latitude_deg: float,
        line_azimuth_deg: float,
        max_temp_c: float,
        season: Season,
    ) -> case_module.Case:
        case = case_module.Case()
        case.demo(2)
        case.TAMB = meteo.temp_amb_c
        case.VWIND = max(meteo.wind_speed_ms, 0.01)
        case.WINDANG_DEG = meteo.wind_angle_deg
        case.CDR_ELEV = float(meteo.elevation_m or 0.0)
        case.SOLAR = 1
        case.SolarRadiation = float(meteo.solar_radiation_wm2 or 0.0)
        case.CDR_LAT_DEG = latitude_deg
        case.NDAY = SEASON_REPRESENTATIVE_DAY[season]
        case.SUN_TIME = REPRESENTATIVE_SUN_HOUR
        case.A3 = 0
        case.Ns = 1.0
        case.ALBEDO = 0.2
        case.Z1_DEG = float(line_azimuth_deg or 90.0) % 180.0
        case.beta = 0.0
        case.TCDR = max_temp_c
        return case

    def calcular(
        self,
        conductor: Conductor,
        meteo: PointMeteoConditions,
        season: Season,
        latitud_deg: float = 43.0,
        azimut_linea_deg: float = 90.0,
    ) -> SegmentRating:
        cable = self._build_cable(conductor)
        case = self._build_case(
            meteo, latitud_deg, azimut_linea_deg, conductor.max_temp_c, season
        )

        calc = ieee738_module.IEEE738()
        calc.Debug = 0
        calc.set_cable(cable)
        calc.set_case(case)
        calc.ieee_738_2013()

        ampacity = float(case.TR or 0.0)
        qc = float(case.QC or 0.0)
        qr = float(case.QR or 0.0)
        qs = float(case.QS or 0.0)

        max_temp = conductor.max_temp_c
        r_low = conductor.r_ac_25_ohm_km / 1000.0
        r_high = conductor.r_ac_75_ohm_km / 1000.0
        r_at_max = r_low + (r_high - r_low) * (max_temp - 25.0) / 50.0

        if meteo.wind_speed_ms >= 2.0:
            conv_mode: ConvMode = "forced_high"
        elif meteo.wind_speed_ms >= 0.5:
            conv_mode = "forced_low"
        else:
            conv_mode = "natural"

        return SegmentRating(
            ampacity=round(ampacity, 1),
            temp_conductor_c=max_temp,
            qc_wm=round(qc, 2),
            qr_wm=round(qr, 2),
            qs_wm=round(qs, 2),
            r_tc_ohm_m=round(r_at_max, 6),
            conv_mode=conv_mode,
        )
