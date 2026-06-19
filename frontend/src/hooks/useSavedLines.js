import { useState, useEffect, useCallback } from "react";
import { getLines, getLine } from "../api/lines";

/**
 * Hook que gestiona las líneas guardadas del usuario.
 */
export function useSavedLines() {
  const [lines, setLines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLines();
      setLines(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  /**
   * Obtiene la geometría de una línea guardada y la convierte al formato
   * interno que usa useRouteManager — igual que si viniera del excelParser.
   */
  const loadLineGeoJSON = useCallback(async (lineId) => {
    try {
      const line = await getLine(lineId);
      const { coordinates } = line.geometry_geojson;

      // geometry_geojson es GeoJSON 2D [lon, lat] — convertir a {lat, lon}
      const coords = coordinates.map(([lon, lat]) => ({ lat, lon }));

      return {
        tipo: "Line",
        coordinates: coords,
        propiedades: {
          fuente: "saved",
          nombre: line.name,
          n_apoyos: line.n_points,
          length_km: line.length_km,
          elevation_source: line.elevation_source,
          min_elevation_m: line.min_elevation_m,
          max_elevation_m: line.max_elevation_m,
          avg_elevation_m: line.avg_elevation_m,
          support_metadata: line.support_metadata ?? [],
        },
        _savedLine: line,
      };
    } catch (err) {
      throw new Error(err.message);
    }
  }, []);

  return { lines, loading, error, refresh, loadLineGeoJSON };
}
