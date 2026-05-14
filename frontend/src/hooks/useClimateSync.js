import { useState, useCallback } from "react";
import { getClimatePercentiles } from "../api/climate";

/**
 * Obtiene percentiles climáticos para el punto medio de un trazado
 * y los convierte al formato de escenarios del panel.
 */
export function useClimateSync() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sync = useCallback(async (coordenadas, source = "openmeteo") => {
    if (!coordenadas?.length) return null;
    setLoading(true);
    setError(null);

    try {
      const mid = coordenadas[Math.floor(coordenadas.length / 2)];
      // coordenadas ya usan {lat, lon} — clave correcta para el backend
      const data = await getClimatePercentiles(mid.lat, mid.lon, source);

      // data.percentiles: { verano: { temp_p90_c, wind_p10_ms, radiation_p90_wm2, ... }, ... }
      const nuevosEscenarios = {};
      Object.entries(data.percentiles).forEach(([estacion, p]) => {
        nuevosEscenarios[estacion] = {
          temp: p.temp_p90_c,
          viento: p.wind_p10_ms,
          radiacion: p.radiation_p90_wm2,
          angulo: 90,
        };
      });

      return nuevosEscenarios;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { sync, loading, error };
}
