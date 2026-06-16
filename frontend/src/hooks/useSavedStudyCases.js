import { useState, useCallback } from "react";
import { getStudyCases } from "../api/studyCases";

/**
 * Hook que carga los casos de estudio del usuario filtrados por line_id.
 */
export function useSavedStudyCases() {
  const [studyCases, setStudyCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async (lineId = null) => {
    setLoading(true);
    setError(null);
    setStudyCases([]);
    try {
      const all = await getStudyCases();
      const filtered = lineId ? all.filter((sc) => sc.line_id === lineId) : all;
      setStudyCases(filtered);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setStudyCases([]);
    setError(null);
  }, []);

  return { studyCases, loading, error, refresh, reset };
}
