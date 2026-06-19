import { useState, useCallback } from "react";
import { getCalculationsByStudyCase } from "../api/calculations";

/**
 * Carga los cálculos de un caso de estudio.
 */
export function useSavedCalculations() {
  const [calculations, setCalculations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refresh = useCallback(async (caseId) => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    setCalculations([]);
    try {
      const data = await getCalculationsByStudyCase(caseId);
      setCalculations(
        [...data].sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at),
        ),
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setCalculations([]);
    setError(null);
  }, []);

  return { calculations, loading, error, refresh, reset };
}
