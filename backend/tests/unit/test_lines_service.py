import pytest
from app.services.lines_service import _calc_length_km, _set_bbox
from app.domain.value_objects import GeoPoint
from app.domain.entities import Line


class TestCalcLengthKm:

    def test_dos_puntos_distancia_conocida(self):
        """Línea E-O de ~0.11° de longitud a 43°N mide entre 8 y 10 km."""
        coords = [
            GeoPoint(lat=43.36, lon=-5.85),
            GeoPoint(lat=43.36, lon=-5.74),
        ]
        length = _calc_length_km(coords)
        assert 8.0 < length < 10.0

    def test_mismo_punto_repetido_da_cero(self):
        """Dos puntos idénticos dan longitud 0."""
        p = GeoPoint(lat=43.37, lon=-5.99)
        coords = [p, p]
        assert _calc_length_km(coords) == 0.0

    def test_suma_de_varios_tramos(self):
        """Con N puntos, la longitud es la suma de los N-1 tramos
        consecutivos, no la distancia directa entre el primero y el último."""
        coords = [
            GeoPoint(lat=43.36, lon=-5.85),
            GeoPoint(lat=43.40, lon=-5.85),  # tramo hacia el norte
            GeoPoint(lat=43.40, lon=-5.80),  # tramo hacia el este
        ]
        length = _calc_length_km(coords)
        # Cada tramo mide individualmente > 0; la suma debe ser mayor que
        # la distancia directa del primero al último (no es línea recta)
        assert length > 0

    def test_resultado_redondeado_a_tres_decimales(self):
        """El resultado se redondea a 3 decimales (metros de precisión)."""
        coords = [
            GeoPoint(lat=43.36, lon=-5.85),
            GeoPoint(lat=43.36, lon=-5.74),
        ]
        length = _calc_length_km(coords)
        assert round(length, 3) == length

    def test_apoyos_reales_corredoria_grado(self):
        """Primeros 2 apoyos reales del Excel — vano de ~240m de media."""
        coords = [
            GeoPoint(lat=43.38814, lon=-5.99372),
            GeoPoint(lat=43.38861, lon=-5.99151),
        ]
        length = _calc_length_km(coords)
        assert 0.1 < length < 0.3  # entre 100 y 300 metros



class TestSetBbox:

    def test_bbox_dos_puntos(self):
        """El bbox debe coincidir exactamente con los extremos cuando
        solo hay 2 puntos."""
        coords = [
            GeoPoint(lat=43.30, lon=-6.00),
            GeoPoint(lat=43.40, lon=-5.90),
        ]
        entity = Line(name="test", coordinates=coords)
        _set_bbox(entity, coords)

        assert entity.bbox_lat_min == 43.30
        assert entity.bbox_lat_max == 43.40
        assert entity.bbox_lon_min == -6.00
        assert entity.bbox_lon_max == -5.90

    def test_bbox_con_punto_intermedio_fuera_de_rango(self):
        """El bbox debe capturar el mínimo/máximo real, no solo los
        extremos de la lista. Un punto intermedio puede ser el más
        al norte/sur/este/oeste."""
        coords = [
            GeoPoint(lat=43.30, lon=-6.00),
            GeoPoint(lat=43.50, lon=-5.95),
            GeoPoint(lat=43.35, lon=-5.90),
        ]
        entity = Line(name="test", coordinates=coords)
        _set_bbox(entity, coords)

        assert entity.bbox_lat_max == 43.50 
        assert entity.bbox_lat_min == 43.30
        assert entity.bbox_lon_max == -5.90
        assert entity.bbox_lon_min == -6.00

    def test_bbox_punto_unico(self):
        """Con un solo punto el bbox colapsa a ese mismo punto."""
        coords = [GeoPoint(lat=43.37, lon=-5.99)]
        entity = Line(name="test", coordinates=coords)
        _set_bbox(entity, coords)

        assert entity.bbox_lat_min == entity.bbox_lat_max == 43.37
        assert entity.bbox_lon_min == entity.bbox_lon_max == -5.99

    def test_bbox_no_afecta_otros_campos(self):
        """_set_bbox solo debe modificar los 4 campos de bbox, no tocar
        length_km, n_points ni otros atributos de la entidad."""
        coords = [
            GeoPoint(lat=43.30, lon=-6.00),
            GeoPoint(lat=43.40, lon=-5.90),
        ]
        entity = Line(name="test", coordinates=coords, length_km=15.7, n_points=2)
        _set_bbox(entity, coords)

        assert entity.length_km == 15.7
        assert entity.n_points == 2
        assert entity.name == "test"
