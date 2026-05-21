import { useState, useCallback, useRef } from "react";
import {
  validateRoute,
  densifyRoute,
  normalizeToLatLon,
} from "../utils/geometryValidator";
import { useClimateDefaults } from "./useClimateDefaults";

export function useRoute(climateSource) {
  const mapRef = useRef(null);
  const [routeData, setRouteData] = useState(null);
  const [validation, setValidation] = useState(null);
  const {
    fetchDefaults,
    loading: loadingClimate,
    slowLoad: climateSlowLoad,
  } = useClimateDefaults();

  const _process = useCallback(async (rawCoords) => {
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

  const loadRoute = useCallback(
    async (rawFeature) => {
      const feature = Array.isArray(rawFeature) ? rawFeature[0] : rawFeature;
      const dense = await _process(feature.coordinates);
      const final = { ...feature, coordinates: dense };
      setRouteData(final);
      mapRef.current?.drawRoute(final);
      const scenarios = await _syncClimate(dense);
      return { feature: final, scenarios };
    },
    [_process, _syncClimate],
  );

  const clear = useCallback(() => {
    mapRef.current?.clearAll();
    setRouteData(null);
    setValidation(null);
  }, []);

  const resyncClimate = useCallback(
    (source) => {
      if (!routeData?.coordinates) return Promise.resolve(null);
      return _syncClimate(routeData.coordinates, source);
    },
    [routeData, _syncClimate],
  );

  return {
    mapRef,
    routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    loadRoute,
    clear,
    resyncClimate,
  };
}
