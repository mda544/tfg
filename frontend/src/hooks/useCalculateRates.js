import { useState, useCallback } from "react";
import { calculateRates } from "../api/rates";
import { buildConductorDTO, buildMeteoScenarioDTO } from "../api/types";
import { densifyRoute, normalizeToLatLon } from "../utils/geometryValidator";

export function useCalculateRates() {
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  const calculate = useCallback(async ({ coordinates, conductor, scenarios, useDem }) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const normalized   = normalizeToLatLon(coordinates);
      const dense        = densifyRoute(normalized, 500);
      const hasExcelZ    = dense.some((c) => (c.altitude ?? 0) > 0);
      const isRealFile   = dense.length > 10;

      const payload = {
        coordinates:    dense.map(({ lat, lon }) => ({ lat, lon })),
        conductor:      buildConductorDTO(conductor),
        scenarios:      Object.entries(scenarios).map(([season, s]) =>
                          buildMeteoScenarioDTO(season, s)
                        ),
        segment_step_m: 500,
        use_real_spans: hasExcelZ || isRealFile,
        use_dem:        useDem && !hasExcelZ,
      };

      const data = await calculateRates(payload);
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { calculate, result, loading, error, reset };
}