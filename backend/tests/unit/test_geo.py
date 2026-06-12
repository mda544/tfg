import pytest
import numpy as np
from app.domain.geo import (
    haversine_m,
    calcular_azimut,
    circular_mean,
    wind_angle_for_segment,
)

# U7.1 — haversine_m


def test_haversine_mismo_punto():
    """Distancia de un punto a sí mismo es 0."""
    a = {"lat": 43.37, "lon": -5.99}
    assert haversine_m(a, a) == 0.0


def test_haversine_distancia_conocida():
    """Distancia en línea recta (vuelo de pájaro) entre Oviedo y Gijón ~25.5 km."""
    oviedo = {"lat": 43.3614, "lon": -5.8493}
    gijon = {"lat": 43.5453, "lon": -5.6616}
    d = haversine_m(oviedo, gijon)
    assert 24_000 < d < 27_000


def test_haversine_simetrico():
    """La distancia de A a B es igual que de B a A."""
    a = {"lat": 43.37, "lon": -5.99}
    b = {"lat": 43.41, "lon": -5.95}
    assert haversine_m(a, b) == haversine_m(b, a)


def test_haversine_acepta_objeto_con_atributos():
    """Acepta objetos con atributos .lat y .lon además de dicts."""

    class Punto:
        def __init__(self, lat, lon):
            self.lat = lat
            self.lon = lon

    a = Punto(43.37, -5.99)
    b = Punto(43.41, -5.95)
    assert haversine_m(a, b) > 0


# U7.2 — calcular_azimut


def test_azimut_hacia_norte():
    """Moverse hacia el Norte da azimut ≈ 0°."""
    az = calcular_azimut(43.0, -5.0, 44.0, -5.0)
    assert abs(az - 0.0) < 1.0 or abs(az - 360.0) < 1.0


def test_azimut_hacia_este():
    """Moverse hacia el Este da azimut ≈ 90°."""
    az = calcular_azimut(43.0, -5.0, 43.0, -4.0)
    assert abs(az - 90.0) < 2.0


def test_azimut_hacia_sur():
    """Moverse hacia el Sur da azimut ≈ 180°."""
    az = calcular_azimut(44.0, -5.0, 43.0, -5.0)
    assert abs(az - 180.0) < 1.0


def test_azimut_hacia_oeste():
    """Moverse hacia el Oeste da azimut ≈ 270°."""
    az = calcular_azimut(43.0, -4.0, 43.0, -5.0)
    assert abs(az - 270.0) < 2.0


def test_azimut_rango_valido():
    """El azimut siempre está en [0°, 360°)."""
    az = calcular_azimut(43.37, -5.99, 43.41, -5.95)
    assert 0.0 <= az < 360.0


# U7.3 — circular_mean


def test_circular_mean_caso_trivial():
    """Media de un único ángulo es ese mismo ángulo."""
    result = circular_mean(np.array([45.0]))
    assert abs(result - 45.0) < 0.1


def test_circular_mean_angulos_opuestos_del_norte():
    """350° y 10° tienen media circular 0°, no 180°.
    Este es el caso que hace necesaria la media circular."""
    result = circular_mean(np.array([350.0, 10.0]))
    assert result < 20.0 or result > 340.0


def test_circular_mean_este_oeste():
    """90° y 270° son opuestos — la media circular es indeterminada
    pero el resultado debe estar en [0°, 360°)."""
    result = circular_mean(np.array([90.0, 270.0]))
    assert 0.0 <= result < 360.0


def test_circular_mean_angulos_iguales():
    """Media de ángulos iguales es ese ángulo."""
    result = circular_mean(np.array([120.0, 120.0, 120.0]))
    assert abs(result - 120.0) < 0.1


def test_circular_mean_array_vacio():
    """Array vacío devuelve 0.0 sin error."""
    result = circular_mean(np.array([]))
    assert result == 0.0


def test_circular_mean_vientos_nordeste():
    """Media de vientos del NE (30°-60°) debe estar en el rango NE."""
    result = circular_mean(np.array([30.0, 40.0, 50.0, 60.0]))
    assert 30.0 <= result <= 60.0


# U7.4 — wind_angle_for_segment


def test_wind_angle_sin_era5_usa_usuario():
    """Sin wind_dir_predominant_deg usa el ángulo del usuario."""
    phi = wind_angle_for_segment(
        wind_dir_predominant_deg=None,
        segment_azimuth_deg=73.6,
        user_wind_angle_deg=90.0,
    )
    assert phi == 90.0


def test_wind_angle_sin_era5_respeta_angulo_personalizado():
    """Sin ERA5 respeta cualquier ángulo del usuario."""
    phi = wind_angle_for_segment(
        wind_dir_predominant_deg=None,
        segment_azimuth_deg=45.0,
        user_wind_angle_deg=30.0,
    )
    assert phi == 30.0


def test_wind_angle_perpendicular():
    """Viento del Este (90°) sobre conductor N-S (0°) -> φ=90°."""
    phi = wind_angle_for_segment(
        wind_dir_predominant_deg=90.0,
        segment_azimuth_deg=0.0,
        user_wind_angle_deg=90.0,
    )
    assert phi == 90.0


def test_wind_angle_paralelo():
    """Viento del Norte (0°) sobre conductor N-S (0°) -> φ=0°."""
    phi = wind_angle_for_segment(
        wind_dir_predominant_deg=0.0,
        segment_azimuth_deg=0.0,
        user_wind_angle_deg=90.0,
    )
    assert phi == 0.0


def test_wind_angle_caso_real_cantabria():
    """Caso real: wind_dir=52.8° (NE), azimuth=73.6° -> φ=20.8°."""
    phi = wind_angle_for_segment(
        wind_dir_predominant_deg=52.8,
        segment_azimuth_deg=73.6,
        user_wind_angle_deg=90.0,
    )
    assert abs(phi - 20.8) < 0.1


def test_wind_angle_normalizado_maximo_90():
    """φ nunca supera 90°."""
    phi = wind_angle_for_segment(
        wind_dir_predominant_deg=0.0,
        segment_azimuth_deg=135.0,
        user_wind_angle_deg=90.0,
    )
    assert 0.0 <= phi <= 90.0


def test_wind_angle_simetrico():
    """φ es simétrico — el orden de los ángulos no importa."""
    phi1 = wind_angle_for_segment(30.0, 60.0, 90.0)
    phi2 = wind_angle_for_segment(60.0, 30.0, 90.0)
    assert phi1 == phi2


def test_wind_angle_distinto_por_azimut():
    """Mismo wind_dir, distintos azimuts → distintos φ.
    Verifica que el cálculo varía por segmento."""
    phi1 = wind_angle_for_segment(52.8, 45.0, 90.0)
    phi2 = wind_angle_for_segment(52.8, 135.0, 90.0)
    assert phi1 != phi2


def test_wind_angle_igual_azimut_da_cero():
    """Cuando wind_dir coincide con azimut -> φ=0° (paralelo)."""
    phi = wind_angle_for_segment(
        wind_dir_predominant_deg=90.0,
        segment_azimuth_deg=90.0,
        user_wind_angle_deg=90.0,
    )
    assert phi == 0.0
