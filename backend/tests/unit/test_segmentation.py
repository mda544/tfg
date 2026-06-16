"""
Pruebas unitarias de segmentation.py — U2

Verifican:
- segment_route: número correcto de tramos usando longitud geodésica (no EPSG:3857)
- segment_route: interpolación lineal de elevación
- segment_route: coordenadas reales de Cantabria (43°N) para detectar distorsión Mercator
- segment_by_spans: segmentación por vanos reales con elevación
- _interpolate_elevation_linear: casos límite

Bug documentado (v2): la versión original usaba line_proj.length (EPSG:3857) para
calcular n_segments, generando ~24% más tramos de los esperados a 43°N por la
distorsión de la proyección Mercator. El fix usa haversine para n_segments y
EPSG:3857 solo para interpolar posiciones a lo largo de la polilínea.
"""

import math
import pytest
from app.domain.segmentation import (
    segment_route,
    segment_by_spans,
    _geodesic_length_m,
    _interpolate_elevation_linear,
)
from app.domain.value_objects import GeoPoint


# ── Coordenadas de referencia ────────────────────────────────────────────────
# Línea Este-Oeste en Asturias (43°N) de ~10 km aproximados
# Oviedo área: 43.36°N, -5.85°E / -5.75°E
COORD_OVIEDO_W = {"lat": 43.36, "lon": -5.85}
COORD_OVIEDO_E = {"lat": 43.36, "lon": -5.74}

# Línea Norte-Sur en Asturias de ~10 km aproximados
COORD_N = {"lat": 43.42, "lon": -5.85}
COORD_S = {"lat": 43.32, "lon": -5.85}

# Apoyos reales de Corredoria-Grado (primeros 5 del Excel)
APOYOS_REALES = [
    {"lat": 43.38814, "lon": -5.99372, "elevation_m": 107.7},
    {"lat": 43.38861, "lon": -5.99151, "elevation_m": 115.9},
    {"lat": 43.38953, "lon": -5.98719, "elevation_m": 100.1},
    {"lat": 43.39052, "lon": -5.98256, "elevation_m": 89.5},
    {"lat": 43.39036, "lon": -5.98039, "elevation_m": 95.2},
]


# ── U2.0 — _geodesic_length_m ────────────────────────────────────────────────

class TestGeodesicLength:

    def test_longitud_oviedo_ew_aprox_10km(self):
        """Línea E-O a 43°N debe medir ~8 km geodésicos."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        length = _geodesic_length_m(coords)
        # A 43°N, 0.11° de longitud ≈ 8 km (cos(43°) × 111km × 0.11 ≈ 8.9 km)
        assert 8_000 < length < 10_000, f"Esperado ~8-10 km, obtenido {length:.0f} m"

    def test_longitud_ns_aprox_11km(self):
        """Línea N-S debe medir ~11 km (111 km/grado × 0.1 grado)."""
        coords = [COORD_N, COORD_S]
        length = _geodesic_length_m(coords)
        assert 10_000 < length < 12_000, f"Esperado ~11 km, obtenido {length:.0f} m"

    def test_distorsion_mercator_significativa(self):
        """La longitud EPSG:3857 debe ser mayor que la geodésica a 43°N.
        Esto confirma por qué no se puede usar line_proj.length para n_segments."""
        from shapely.geometry import LineString
        from shapely.ops import transform
        from pyproj import Transformer

        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        geodesic = _geodesic_length_m(coords)

        points = [(c["lon"], c["lat"]) for c in coords]
        t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        line_3857 = transform(t.transform, LineString(points))
        mercator = line_3857.length

        ratio = mercator / geodesic
        # A 43°N la distorsión es 1/cos(43°) ≈ 1.367 — al menos 1.3
        assert ratio > 1.3, f"Distorsión esperada > 1.3, obtenida {ratio:.3f}"
        assert ratio < 1.5, f"Distorsión demasiado alta: {ratio:.3f}"


# ── U2.1 — segment_route ────────────────────────────────────────────────────

class TestSegmentRoute:

    def test_numero_tramos_linea_ew_step500(self):
        """Línea E-O de ~8-10 km con step=500m → ~16-20 tramos.
        Bug original (EPSG:3857): habría generado ~22-27 tramos."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        longitud_real = _geodesic_length_m(coords)
        esperado = int(longitud_real / 500)
        assert len(segs) == esperado, (
            f"Esperado {esperado} tramos, obtenido {len(segs)}. "
            f"Bug Mercator si > {int(longitud_real * 1.367 / 500)}"
        )

    def test_numero_tramos_no_distorsionado_por_mercator(self):
        """El número de tramos debe corresponder a la longitud real, no a EPSG:3857.
        Comprueba específicamente el bug corregido."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        longitud_geodesica = _geodesic_length_m(coords)

        # Número correcto basado en longitud real
        n_correcto = int(longitud_geodesica / 500)
        # Número incorrecto que habría dado el bug (EPSG:3857)
        from shapely.geometry import LineString
        from shapely.ops import transform
        from pyproj import Transformer
        points = [(c["lon"], c["lat"]) for c in coords]
        t = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        n_bug = int(transform(t.transform, LineString(points)).length / 500)

        assert len(segs) == n_correcto
        assert len(segs) != n_bug, (
            "El bug de Mercator no habría afectado a esta línea — "
            "elige coordenadas con mayor distorsión"
        )

    def test_suma_longitudes_aproxima_total(self):
        """La suma de length_km de todos los tramos debe aproximarse
        a la longitud total del trazado."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        longitud_total = _geodesic_length_m(coords) / 1000
        suma = sum(s.length_km for s in segs)
        assert abs(suma - longitud_total) < 0.1, (
            f"Suma tramos {suma:.3f} km, longitud total {longitud_total:.3f} km"
        )

    def test_todos_tramos_mismo_length(self):
        """Todos los tramos deben tener la misma longitud (step_real uniforme)."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        lengths = [s.length_km for s in segs]
        assert max(lengths) - min(lengths) < 0.01, (
            f"Longitudes no uniformes: min={min(lengths):.3f}, max={max(lengths):.3f}"
        )

    def test_ids_secuenciales(self):
        """Los ids deben ser T001, T002, T003..."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        for i, s in enumerate(segs):
            assert s.id == f"T{i + 1:03d}", f"Id incorrecto: {s.id}"
            assert s.index == i

    def test_indices_secuenciales(self):
        """Los índices deben ser 0, 1, 2..."""
        coords = [COORD_N, COORD_S]
        segs = segment_route(coords, step_m=500.0)
        for i, s in enumerate(segs):
            assert s.index == i

    def test_primer_punto_igual_inicio(self):
        """El start_point del primer segmento debe coincidir con el inicio del trazado."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        assert abs(segs[0].start_point.lat - COORD_OVIEDO_W["lat"]) < 0.001
        assert abs(segs[0].start_point.lon - COORD_OVIEDO_W["lon"]) < 0.001

    def test_ultimo_punto_igual_fin(self):
        """El end_point del último segmento debe coincidir con el fin del trazado."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        assert abs(segs[-1].end_point.lat - COORD_OVIEDO_E["lat"]) < 0.001
        assert abs(segs[-1].end_point.lon - COORD_OVIEDO_E["lon"]) < 0.001

    def test_sin_elevacion_todos_cero(self):
        """Sin elevation_m en las coordenadas todos los tramos tienen elevation_m=0.0."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        assert all(s.elevation_m == 0.0 for s in segs)

    def test_con_elevacion_interpola(self):
        """Con elevation_m en los extremos el punto medio debe interpolarse."""
        coords = [
            {"lat": 43.36, "lon": -5.85, "elevation_m": 100.0},
            {"lat": 43.36, "lon": -5.74, "elevation_m": 200.0},
        ]
        segs = segment_route(coords, step_m=500.0)
        # El primer segmento (cerca del inicio, elev=100) debe tener elevación < media
        # El último segmento (cerca del fin, elev=200) debe tener elevación > media
        assert segs[0].elevation_m < 150.0
        assert segs[-1].elevation_m > 150.0

    def test_azimuth_linea_ew_aprox_90(self):
        """Una línea E-O debe tener azimut aproximadamente 90° (Este)."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        for s in segs:
            assert 80 < s.azimuth_deg < 100, (
                f"Azimut E-O esperado ~90°, obtenido {s.azimuth_deg}°"
            )

    def test_azimuth_linea_ns_aprox_180(self):
        """Una línea N-S debe tener azimut aproximadamente 180° (Sur)."""
        coords = [COORD_N, COORD_S]
        segs = segment_route(coords, step_m=500.0)
        for s in segs:
            assert 170 < s.azimuth_deg < 190, (
                f"Azimut N-S esperado ~180°, obtenido {s.azimuth_deg}°"
            )

    def test_step_grande_genera_un_segmento(self):
        """Con step mayor que la longitud total debe generarse 1 segmento."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=50_000.0)  # 50 km
        assert len(segs) == 1

    def test_dos_puntos_minimo(self):
        """Con solo 2 coordenadas debe funcionar correctamente."""
        coords = [COORD_OVIEDO_W, COORD_OVIEDO_E]
        segs = segment_route(coords, step_m=500.0)
        assert len(segs) >= 1
        assert all(s.length_km > 0 for s in segs)


# ── U2.2 — segment_by_spans ─────────────────────────────────────────────────

class TestSegmentBySpans:

    def test_n_segmentos_es_n_minus_1(self):
        """Con N apoyos deben generarse N-1 vanos."""
        segs = segment_by_spans(APOYOS_REALES)
        assert len(segs) == len(APOYOS_REALES) - 1

    def test_ids_secuenciales_vanos(self):
        """Los ids deben ser V001, V002, V003..."""
        segs = segment_by_spans(APOYOS_REALES)
        for i, s in enumerate(segs):
            assert s.id == f"V{i + 1:03d}"
            assert s.index == i

    def test_elevacion_media_extremos(self):
        """La elevation_m de cada vano debe ser la media de sus dos apoyos."""
        segs = segment_by_spans(APOYOS_REALES)
        for i, s in enumerate(segs):
            p1 = APOYOS_REALES[i]
            p2 = APOYOS_REALES[i + 1]
            expected = round((p1["elevation_m"] + p2["elevation_m"]) / 2, 1)
            assert s.elevation_m == expected, (
                f"Vano {i}: elevación esperada {expected}, obtenida {s.elevation_m}"
            )

    def test_primer_vano_elevacion_correcta(self):
        """V001: media de apoyo 1 (107.7) y apoyo 2 (115.9) = 111.8."""
        segs = segment_by_spans(APOYOS_REALES)
        assert segs[0].elevation_m == pytest.approx(111.8, abs=0.1)

    def test_sin_elevacion_todos_cero(self):
        """Sin elevation_m en los apoyos todos los vanos tienen elevation_m=0.0."""
        apoyos_sin_z = [
            {"lat": a["lat"], "lon": a["lon"]}
            for a in APOYOS_REALES
        ]
        segs = segment_by_spans(apoyos_sin_z)
        assert all(s.elevation_m == 0.0 for s in segs)

    def test_length_km_positivo(self):
        """Todos los vanos deben tener longitud positiva."""
        segs = segment_by_spans(APOYOS_REALES)
        assert all(s.length_km > 0 for s in segs)

    def test_mid_point_entre_extremos(self):
        """El mid_point debe estar entre start y end geográficamente."""
        segs = segment_by_spans(APOYOS_REALES)
        for s in segs:
            lat_min = min(s.start_point.lat, s.end_point.lat)
            lat_max = max(s.start_point.lat, s.end_point.lat)
            lon_min = min(s.start_point.lon, s.end_point.lon)
            lon_max = max(s.start_point.lon, s.end_point.lon)
            assert lat_min <= s.mid_point.lat <= lat_max or abs(lat_max - lat_min) < 1e-6
            assert lon_min <= s.mid_point.lon <= lon_max or abs(lon_max - lon_min) < 1e-6

    def test_start_end_coinciden_con_apoyos(self):
        """El start_point de cada vano debe coincidir con el apoyo correspondiente."""
        segs = segment_by_spans(APOYOS_REALES)
        for i, s in enumerate(segs):
            assert abs(s.start_point.lat - APOYOS_REALES[i]["lat"]) < 1e-5
            assert abs(s.start_point.lon - APOYOS_REALES[i]["lon"]) < 1e-5
            assert abs(s.end_point.lat - APOYOS_REALES[i + 1]["lat"]) < 1e-5
            assert abs(s.end_point.lon - APOYOS_REALES[i + 1]["lon"]) < 1e-5


# ── U2.3 — _interpolate_elevation_linear ────────────────────────────────────

class TestInterpolateElevation:

    def test_sin_puntos_con_elevacion_devuelve_cero(self):
        """Sin coordenadas con elevation_m debe devolver 0.0."""
        from app.domain.segmentation import _interpolate_elevation_linear
        coords = [{"lat": 43.36, "lon": -5.85}, {"lat": 43.36, "lon": -5.74}]
        mid = GeoPoint(lat=43.36, lon=-5.795)
        assert _interpolate_elevation_linear(coords, mid) == 0.0

    def test_un_punto_devuelve_su_elevacion(self):
        """Con un solo punto con elevation_m devuelve esa elevación."""
        from app.domain.segmentation import _interpolate_elevation_linear
        coords = [
            {"lat": 43.36, "lon": -5.85, "elevation_m": 250.0},
            {"lat": 43.36, "lon": -5.74},
        ]
        mid = GeoPoint(lat=43.36, lon=-5.795)
        assert _interpolate_elevation_linear(coords, mid) == 250.0

    def test_punto_medio_interpola_entre_extremos(self):
        """Punto medio entre [100m, 200m] debe dar ~150m."""
        from app.domain.segmentation import _interpolate_elevation_linear
        coords = [
            {"lat": 43.36, "lon": -5.85, "elevation_m": 100.0},
            {"lat": 43.36, "lon": -5.74, "elevation_m": 200.0},
        ]
        mid = GeoPoint(lat=43.36, lon=-5.795)  # punto medio exacto
        result = _interpolate_elevation_linear(coords, mid)
        assert 130.0 < result < 170.0, f"Esperado ~150m, obtenido {result}m"

    def test_punto_cerca_del_inicio_tiende_a_elevacion_inicial(self):
        """Punto cerca del inicio debe dar elevación próxima a la del inicio."""
        from app.domain.segmentation import _interpolate_elevation_linear
        coords = [
            {"lat": 43.36, "lon": -5.85, "elevation_m": 100.0},
            {"lat": 43.36, "lon": -5.74, "elevation_m": 500.0},
        ]
        mid = GeoPoint(lat=43.36, lon=-5.848)  # muy cerca del inicio
        result = _interpolate_elevation_linear(coords, mid)
        assert result < 200.0, f"Esperado próximo a 100m, obtenido {result}m"

    def test_ignora_puntos_con_elevation_cero(self):
        """Los puntos con elevation_m=0 se tratan como sin elevación."""
        from app.domain.segmentation import _interpolate_elevation_linear
        coords = [
            {"lat": 43.36, "lon": -5.85, "elevation_m": 0.0},  # ignorado
            {"lat": 43.36, "lon": -5.74, "elevation_m": 300.0},
        ]
        mid = GeoPoint(lat=43.36, lon=-5.795)
        result = _interpolate_elevation_linear(coords, mid)
        assert result == 300.0  # solo hay un punto válido → devuelve ese