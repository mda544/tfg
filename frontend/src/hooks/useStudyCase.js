import { useState, useCallback } from "react";
import { createLine } from "../api/lines";
import { createStudyCase } from "../api/studyCases";

/**
 * Persiste el trazado en el backend y crea el caso de estudio.
 * Responsabilidad única: POST /lines + POST /study-cases.
 */
export function useStudyCase() {
  const [studyCaseId, setStudyCaseId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  /**
   * @param {Array}  coordinates  lista de {lat, lon}
   * @param {Object} opts         { lineName, lineDesc, caseName, segmentStep, useRealSpans, useDem }
   */
  const save = useCallback(async (coordinates, opts = {}) => {
    setSaving(true);
    setError(null);

    try {
      // 1. POST /lines — el backend enriquece con DEM
      const line = await createLine({
        name: opts.lineName ?? "Línea sin nombre",
        description: opts.lineDesc ?? null,
        coordinates: coordinates.map(({ lat, lon }) => ({ lat, lon })),
      });

      // 2. POST /study-cases
      const sc = await createStudyCase({
        name: opts.caseName ?? `Estudio ${new Date().toLocaleDateString()}`,
        line_id: line.id,
        segment_step_m: opts.segmentStep ?? 500.0,
        use_real_spans: opts.useRealSpans ?? false,
        use_dem: opts.useDem ?? true,
      });

      setStudyCaseId(sc.id);
      return sc.id;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setSaving(false);
    }
  }, []);

  const reset = useCallback(() => {
    setStudyCaseId(null);
    setError(null);
  }, []);

  return { studyCaseId, saving, error, save, reset };
}
