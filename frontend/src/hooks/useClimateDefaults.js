import { useState, useCallback } from "react";
import { getClimatePercentiles } from "../api/climate";

/** Obtiene percentiles climáticos históricos y los convierte al formato de escenarios estacionales. */
export function useClimateDefaults() {
  const [loading, setLoading] = useState(false);
  const [slowLoad, setSlowLoad] = useState(false);
  const [error, setError] = useState(null);

  const fetchDefaults = useCallback(
    async (coordinates, source = "openmeteo") => {
      if (!coordinates?.length) return null;

      setLoading(true);
      setSlowLoad(false);
      setError(null);

      const timer = setTimeout(() => setSlowLoad(true), 300);

      try {
        const mid = coordinates[Math.floor(coordinates.length / 2)];
        const data = await getClimatePercentiles(mid.lat, mid.lon, source);

        return Object.fromEntries(
          Object.entries(data.percentiles).map(([season, p]) => [
            season,
            {
              temp: p.temp_p90_c,
              viento: p.wind_p10_ms,
              radiacion: p.radiation_p90_wm2,
              angulo: 90,
            },
          ]),
        );
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

  return { fetchDefaults, loading, slowLoad, error };
}
