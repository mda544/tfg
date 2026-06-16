import { useState, useCallback } from "react";
import { getClimatePercentiles } from "../api/climate";

export function useClimateDefaults() {
  const [loading, setLoading] = useState(false);
  const [slowLoad, setSlowLoad] = useState(false);
  const [error, setError] = useState(null);

  const [apiDefaults, setApiDefaults] = useState(null);

  const fetchDefaults = useCallback(
    async (coordinates, source = "openmeteo") => {
      if (!coordinates?.length) return null;

      setLoading(true);
      setSlowLoad(false);
      setError(null);

      const timer = setTimeout(() => setSlowLoad(true), 1500); // 1.5s — la caché local es rápida

      try {
        const mid = coordinates[Math.floor(coordinates.length / 2)];
        const data = await getClimatePercentiles(mid.lat, mid.lon, source);

        const scenarios = Object.fromEntries(
          Object.entries(data.percentiles).map(([season, p]) => [
            season,
            {
              temp: p.temp_p90_c,
              viento: p.wind_p10_ms,
              radiacion: p.radiation_p90_wm2,
              angulo: 90,
              wind_dir_predominant_deg: p.wind_dir_predominant_deg ?? null,
            },
          ]),
        );

        setApiDefaults(scenarios);

        return scenarios;
      } catch (err) {
        setError(err.message);
        return null;
      } finally {
        clearTimeout(timer);
        setLoading(false);
        setSlowLoad(false);
      }
    },
    [],
  );

  const resetDefaults = useCallback(() => {
    setApiDefaults(null);
  }, []);

  return {
    fetchDefaults,
    loading,
    slowLoad,
    error,
    apiDefaults,
    resetDefaults,
  };
}
