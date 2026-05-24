import { useState, useCallback } from "react";
import {
  validateRoute,
  densifyRoute,
  normalizeToLatLon,
} from "../utils/geometryValidator";
import { useClimateDefaults } from "./useClimateDefaults";

/**
 * Gestiona el trazado en memoria — validación, densificación y sincronización climática.
 */
export function useRoute(climateSource) {
  const [routeData, setRouteData] = useState(null);
  const [validation, setValidation] = useState(null);

  const {
    fetchDefaults,
    loading: loadingClimate,
    slowLoad: climateSlowLoad,
  } = useClimateDefaults();

  const _process = useCallback((rawCoords) => {
    const normalized = normalizeToLatLon(rawCoords);
    const dense = densifyRoute(normalized, 500);
    setValidation(validateRoute(dense));
    return dense;
  }, []);

  const _syncClimate = useCallback(
    (coordinates, source) =>
      fetchDefaults(coordinates, source ?? climateSource),
    [fetchDefaults, climateSource],
  );

  /** Carga un feature (de archivo o del mapa), procesa coordenadas y sincroniza clima. */
  const loadRoute = useCallback(
    async (rawFeature) => {
      const feature = Array.isArray(rawFeature) ? rawFeature[0] : rawFeature;
      const dense = _process(feature.coordinates);
      const final = { ...feature, coordinates: dense };
      setRouteData(final);
      const scenarios = await _syncClimate(dense);
      return { feature: final, scenarios };
    },
    [_process, _syncClimate],
  );

  /** Resincroniza el clima con una fuente distinta sin recargar el trazado. */
  const resyncClimate = useCallback(
    (source) => {
      if (!routeData?.coordinates) return Promise.resolve(null);
      return _syncClimate(routeData.coordinates, source);
    },
    [routeData, _syncClimate],
  );

  const clear = useCallback(() => {
    setRouteData(null);
    setValidation(null);
  }, []);

  return {
    routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    loadRoute,
    resyncClimate,
    clear,
  };
}
