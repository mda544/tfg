import { useState, useCallback } from "react";
import { createConductor, deleteConductor } from "../api/conductors";
import { buildConductorCreateDTO } from "../api/types";
import { DEFAULT_CONDUCTORS } from "../features/conductor/conductorData";

export function useConductors() {
  const [custom,  setCustom]  = useState([]);
  const [saving,  setSaving]  = useState(false);
  const [error,   setError]   = useState(null);

  const conductors = [...DEFAULT_CONDUCTORS, ...custom];

  const create = useCallback(async (payload) => {
    setSaving(true);
    setError(null);
    try {
      const created = await createConductor(buildConductorCreateDTO(payload));
      setCustom((prev) => [...prev, created]);
      return created;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setSaving(false);
    }
  }, []);

  const remove = useCallback(async (id) => {
    try {
      await deleteConductor(id);
      setCustom((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }, []);

  return { conductors, custom, saving, error, create, remove };
}