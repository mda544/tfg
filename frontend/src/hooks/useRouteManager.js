import { useState, useRef, useCallback } from "react";
import {
  validateRoute,
  densifyRoute,
  normalizeToLatLon,
} from "../utils/geometryValidator";
import { useClimateDefaults } from "./useClimateDefaults";
import { createLine } from "../api/lines";
import { createStudyCase } from "../api/studyCases";

export function useRouteManager(climateSource) {
  const mapRef = useRef(null);

  const [routeData, setRouteData] = useState(null);
  const [validation, setValidation] = useState(null);
  const [studyCaseId, setStudyCaseId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const {
    fetchDefaults,
    loading: loadingClimate,
    slowLoad: climateSlowLoad,
    apiDefaults,
    resetDefaults,
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

  const loadRoute = useCallback(
    async (rawFeature) => {
      const feature = Array.isArray(rawFeature) ? rawFeature[0] : rawFeature;
      const dense = _process(feature.coordinates);
      const final = { ...feature, coordinates: dense };
      setRouteData(final);
      resetDefaults();
      mapRef.current?.drawRoute(final);
      const scenarios = await _syncClimate(dense);
      return { feature: final, scenarios };
    },
    [_process, _syncClimate, resetDefaults],
  );

  const resyncClimate = useCallback(
    (source) => {
      if (!routeData?.coordinates) return Promise.resolve(null);
      return _syncClimate(routeData.coordinates, source);
    },
    [routeData, _syncClimate],
  );

  const saveRoute = useCallback(
    async (opts = {}) => {
      if (!routeData) return null;
      if (!opts.conductorId) {
        setSaveError("Selecciona un conductor antes de guardar.");
        return null;
      }
      setSaving(true);
      setSaveError(null);
      try {
        const singulars = routeData.propiedades?.puntos_singulares ?? [];
        const hasRealSpans = singulars.length >= 2;

        const coordsPayload = routeData.coordinates.map(
          ({ lat, lon, elevation_m, altitud }) => ({
            lat,
            lon,
            ...(elevation_m != null
              ? { elevation_m }
              : altitud != null
                ? { elevation_m: altitud }
                : {}),
          }),
        );

        const line = await createLine({
          name: opts.lineName ?? "Línea sin nombre",
          description: opts.lineDesc ?? null,
          coordinates: coordsPayload,
        });

        const sc = await createStudyCase({
          name: opts.caseName ?? `Estudio ${new Date().toLocaleDateString()}`,
          line_id: line.id,
          conductor_id: opts.conductorId,
          segment_step_m: opts.segmentStep ?? 500.0,
          use_real_spans: opts.useRealSpans ?? hasRealSpans,
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

  const clear = useCallback(() => {
    mapRef.current?.clearAll();
    setRouteData(null);
    setValidation(null);
    setStudyCaseId(null);
    setSaveError(null);
    resetDefaults();
  }, [resetDefaults]);

  return {
    mapRef,
    routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    studyCaseId,
    saving,
    saveError,
    apiDefaults,
    loadRoute,
    resyncClimate,
    saveRoute,
    clear,
  };
}
