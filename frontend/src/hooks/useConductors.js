import { useState, useCallback } from "react";
import { createConductor, deleteConductor } from "../api/conductors";

export const CONDUCTORES_FALLBACK = [
  {
    id: "local-1",
    name: "LA-110 (Hawk)",
    diameter_mm: 21.78,
    r_ac_75_ohm_km: 0.119,
    r_ac_25_ohm_km: 0.101,
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 85,
  },
  {
    id: "local-2",
    name: "LA-280 (Condor)",
    diameter_mm: 27.72,
    r_ac_75_ohm_km: 0.072,
    r_ac_25_ohm_km: 0.061,
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 90,
  },
  {
    id: "local-3",
    name: "LA-380 (Gull)",
    diameter_mm: 25.4,
    r_ac_75_ohm_km: 0.089,
    r_ac_25_ohm_km: 0.076,
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 90,
  },
  {
    id: "local-4",
    name: "LA-455 (Cardinal)",
    diameter_mm: 30.42,
    r_ac_75_ohm_km: 0.059,
    r_ac_25_ohm_km: 0.05,
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 90,
  },
];

export function useConductors() {
  const [custom, setCustom] = useState([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Todos los conductores: estándar + personalizados del usuario
  const conductors = [...CONDUCTORES_FALLBACK, ...custom];

  const create = useCallback(async (payload) => {
    setSaving(true);
    setError(null);
    try {
      const nuevo = await createConductor(payload);
      setCustom((prev) => [...prev, nuevo]);
      return nuevo;
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
