import math
from dataclasses import dataclass
from typing import Literal

@dataclass
class ConductorParams:
    diametro_mm: float        # Diámetro exterior (mm)
    r_ac_75_ohm_km: float     # Resistencia AC a 75°C (Ω/km)
    r_ac_25_ohm_km: float     # Resistencia AC a 25°C (Ω/km)
    emisividad: float         # ε, adimensional [0-1]
    absortividad: float       # α solar, adimensional [0-1]
    temp_max_c: float         # Temperatura máxima de operación (°C)

@dataclass
class MeteoParams:
    temp_amb_c: float         # Temperatura ambiente (°C)
    vel_viento_ms: float      # Velocidad viento a altura del cable (m/s)
    angulo_viento_deg: float  # Ángulo viento respecto al eje del conductor (°)
    radiacion_solar_wm2: float  # Irradiancia total (W/m²)
    altitud_m: float = 0.0    # Altitud sobre el nivel del mar (m)

@dataclass
class RateResult:
    ampacidad_a: float
    temp_conductor_c: float
    qc_wm: float   # Convección (W/m)
    qr_wm: float   # Radiación (W/m)
    qs_wm: float   # Ganancia solar (W/m)
    r_tc_ohm_m: float  # Resistencia a Tc (Ω/m)
    modo_conveccion: Literal["forzada_baja", "forzada_alta", "natural"]

class IEEE738Calculator:
    """
    Implementación del balance térmico en régimen estacionario según IEEE Std 738-2012.
    Ecuación central: I²R(Tc) + Qs = Qc + Qr  →  I = sqrt((Qc + Qr - Qs) / R(Tc))
    """

    def _resistencia_a_temp(self, params: ConductorParams, tc: float) -> float:
        """
        Interpolación lineal de R entre los dos puntos de referencia del datasheet.
        R(Tc) = R25 + (R75 - R25) * (Tc - 25) / (75 - 25)
        """
        r25 = params.r_ac_25_ohm_km / 1000.0  # → Ω/m
        r75 = params.r_ac_75_ohm_km / 1000.0
        return r25 + (r75 - r25) * (tc - 25.0) / 50.0

    def _densidad_aire(self, ta: float, altitud_m: float) -> float:
        """Densidad del aire corregida por temperatura y altitud (kg/m³)."""
        rho_sl = 1.293  # kg/m³ a 0°C nivel del mar
        # Corrección por temperatura (gas ideal)
        rho_t = rho_sl * 273.15 / (273.15 + ta)
        # Corrección por altitud (barométrica simplificada)
        rho = rho_t * math.exp(-altitud_m / 8500.0)
        return rho

    def _viscosidad_aire(self, tf: float) -> float:
        """Viscosidad dinámica del aire a temperatura de película Tf (Pa·s)."""
        # Fórmula de Sutherland simplificada para el rango operativo
        return (1.458e-6 * (tf + 273.15)**1.5) / (tf + 273.15 + 110.4)

    def _conductividad_termica_aire(self, tf: float) -> float:
        """Conductividad térmica del aire (W/m·K)."""
        return 2.42e-2 + 7.2e-5 * tf

    def _calor_conveccion(
        self,
        d: float,
        tc: float,
        ta: float,
        vel_ms: float,
        angulo_deg: float,
        altitud_m: float,
    ) -> tuple[float, str]:
        """
        Calcula la pérdida de calor por convección (W/m) según IEEE 738-2012, Sec. 4.4.
        Evalúa Qc1 (forzada baja Re), Qc2 (forzada alta Re) y Qcn (natural)
        y devuelve el máximo junto con el modo activo.
        """
        tf = (tc + ta) / 2.0  # Temperatura de película
        delta_t = tc - ta

        rho_f = self._densidad_aire(tf, altitud_m)
        mu_f  = self._viscosidad_aire(tf)
        kf    = self._conductividad_termica_aire(tf)

        # Factor de ángulo de incidencia del viento (IEEE 738 Ec. 4a)
        phi_rad = math.radians(angulo_deg)
        k_angle = (
            1.194
            - math.cos(phi_rad)
            + 0.194 * math.cos(2 * phi_rad)
            + 0.368 * math.sin(2 * phi_rad)
        )

        vel_ef = max(vel_ms, 0.01)
        Re = rho_f * vel_ef * d / mu_f  # Número de Reynolds

        # Qc1: forzada, Re bajo (IEEE 738 Ec. 3a)
        qc1 = k_angle * (1.01 + 1.35 * Re**0.52) * kf * delta_t

        # Qc2: forzada, Re alto (IEEE 738 Ec. 3b)
        qc2 = k_angle * 0.754 * Re**0.6 * kf * delta_t

        # Qcn: convección natural (IEEE 738 Ec. 5)
        rho_a = self._densidad_aire(ta, altitud_m)
        qcn = max(0.0, 3.645 * rho_a**0.5 * d**0.75 * delta_t**1.25)

        # Se toma el mayor de los tres
        if qc1 >= qc2 and qc1 >= qcn:
            return qc1, "forzada_baja"
        elif qc2 >= qcn:
            return qc2, "forzada_alta"
        else:
            return qcn, "natural"

    def _calor_radiacion(
        self, d: float, emisividad: float, tc: float, ta: float
    ) -> float:
        """Pérdida de calor por radiación (W/m), IEEE 738-2012 Ec. 6."""
        sigma = 5.6704e-8  # W/m²·K⁴
        Tc_k = tc + 273.15
        Ta_k = ta + 273.15
        return emisividad * math.pi * d * sigma * (Tc_k**4 - Ta_k**4)

    def _ganancia_solar(
        self,
        d: float,
        absortividad: float,
        radiacion_wm2: float,
        angulo_incidencia_deg: float = 90.0,
    ) -> float:
        """
        Ganancia de calor solar (W/m), IEEE 738-2012 Ec. 7.
        Se asume incidencia perpendicular si no se conoce el ángulo solar exacto.
        """
        theta_rad = math.radians(angulo_incidencia_deg)
        return absortividad * radiacion_wm2 * math.sin(theta_rad) * d

    def calcular(
        self,
        conductor: ConductorParams,
        meteo: MeteoParams,
        angulo_solar_deg: float = 90.0,
    ) -> RateResult:
        """
        Calcula la ampacidad en régimen estacionario resolviendo el balance térmico.
        Fija Tc = temp_max y despeja I.
        """
        tc = conductor.temp_max_c
        d  = conductor.diametro_mm / 1000.0  # → metros

        r_tc = self._resistencia_a_temp(conductor, tc)

        qc, modo = self._calor_conveccion(
            d, tc, meteo.temp_amb_c,
            meteo.vel_viento_ms, meteo.angulo_viento_deg,
            meteo.altitud_m
        )
        qr = self._calor_radiacion(d, conductor.emisividad, tc, meteo.temp_amb_c)
        qs = self._ganancia_solar(d, conductor.absortividad, meteo.radiacion_solar_wm2, angulo_solar_deg)

        calor_a_disipar = qc + qr - qs
        if calor_a_disipar <= 0 or meteo.temp_amb_c >= tc:
            ampacidad = 0.0
        else:
            ampacidad = math.sqrt(calor_a_disipar / r_tc)

        return RateResult(
            ampacidad_a=round(ampacidad, 1),
            temp_conductor_c=tc,
            qc_wm=round(qc, 2),
            qr_wm=round(qr, 2),
            qs_wm=round(qs, 2),
            r_tc_ohm_m=round(r_tc, 6),
            modo_conveccion=modo,
        )