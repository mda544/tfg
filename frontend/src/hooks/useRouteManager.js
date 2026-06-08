import { useState, useRef, useCallback } from "react";
import {
  validateRoute,
  densifyRoute,
  normalizeToLatLon,
} from "../utils/geometryValidator";
import { useClimateDefaults } from "./useClimateDefaults";
import { createLine } from "../api/lines";
import { createStudyCase } from "../api/studyCases";

/**
 * Gestiona todo el ciclo de vida del trazado
 */
export function useRouteManager(climateSource) {
  const mapRef = useRef(null);

  // Estado del trazado
  const [routeData, setRouteData] = useState(null);
  const [validation, setValidation] = useState(null);

  // Estado de persistencia
  const [studyCaseId, setStudyCaseId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

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

  /** Carga un archivo o mapa (feature), procesa y sincroniza clima. */
  const loadRoute = useCallback(
    async (rawFeature) => {
      const feature = Array.isArray(rawFeature) ? rawFeature[0] : rawFeature;
      const dense = _process(feature.coordinates);
      const final = { ...feature, coordinates: dense };
      setRouteData(final);
      mapRef.current?.drawRoute(final);
      const scenarios = await _syncClimate(dense);
      return { feature: final, scenarios };
    },
    [_process, _syncClimate],
  );

  /** Resincroniza el clima con una fuente distinta. */
  const resyncClimate = useCallback(
    (source) => {
      if (!routeData?.coordinates) return Promise.resolve(null);
      return _syncClimate(routeData.coordinates, source);
    },
    [routeData, _syncClimate],
  );

  /** Persiste la línea y crea el caso de estudio en el backend. */
  const saveRoute = useCallback(
    async (opts = {}) => {
      if (!routeData) return null;
      setSaving(true);
      setSaveError(null);
      try {
        const mappedCoords = routeData.coordinates.map(
          ({ lat, lon, altitud }) => ({
            lat,
            lon,
            ...(altitud && altitud > 0 ? { altitud } : {}),
          }),
        );

        const line = await createLine({
          name: opts.lineName ?? "Línea sin nombre",
          description: opts.lineDesc ?? null,
          coordinates: mappedCoords,
        });

        const isExcel = routeData?.propiedades?.fuente === "excel";


        const sc = await createStudyCase({
          name: opts.caseName ?? `Estudio ${new Date().toLocaleDateString()}`,
          line_id: line.id,
          segment_step_m: opts.segmentStep ?? 500.0,
          use_real_spans: opts.useRealSpans ?? isExcel,
          use_dem: opts.useDem ?? true,
        });

        setStudyCaseId(sc.id);
        return sc.id;
      } catch (err) {
        setSaveError(err.message);
        return null;
      } finally {
        setSaving(false);
      }
    },
    [routeData],
  );

  /** Limpia todo */
  const clear = useCallback(() => {
    mapRef.current?.clearAll();
    setRouteData(null);
    setValidation(null);
    setStudyCaseId(null);
    setSaveError(null);
  }, []);

  return {
    // Ref del mapa
    mapRef,
    // Estado del trazado
    routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    // Estado de persistencia
    studyCaseId,
    saving,
    saveError,
    // Acciones
    loadRoute,
    resyncClimate,
    saveRoute,
    clear,
  };
}
