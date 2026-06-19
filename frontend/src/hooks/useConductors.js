import { useState, useCallback, useEffect } from "react";
import {
  createConductor,
  deleteConductor,
  getConductors,
} from "../api/conductors";
import { buildConductorCreateDTO } from "../api/types";
import { DEFAULT_CONDUCTORS } from "../features/conductor/conductorData";

const GLOBAL_IDS = new Set([
  "00000000-0000-0000-0000-000000000001",
  "00000000-0000-0000-0000-000000000002",
  "00000000-0000-0000-0000-000000000003",
  "00000000-0000-0000-0000-000000000004",
]);

export function useConductors() {
  const [globals, setGlobals] = useState(DEFAULT_CONDUCTORS);
  const [custom, setCustom] = useState([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getConductors()
      .then((data) => {
        setGlobals(data.filter((c) => GLOBAL_IDS.has(c.id)));
        setCustom(data.filter((c) => !GLOBAL_IDS.has(c.id)));
      })
      .catch(() => {});
  }, []);

  const conductors = [...globals, ...custom];

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
