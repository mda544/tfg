import { useState, useEffect, useCallback } from "react";
import {
  getConductors,
  createConductor,
  deleteConductor,
} from "../api/conductors";

/** Conductores de fallback por si la API no está disponible o el usuario no está autenticado */
const CONDUCTORES_FALLBACK = [
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
  const [conductors, setConductors] = useState(CONDUCTORES_FALLBACK);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fromApi, setFromApi] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getConductors();
      if (data.length > 0) {
        setConductors(data);
        setFromApi(true);
      }
    } catch {
      setFromApi(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const create = useCallback(async (payload) => {
    const nuevo = await createConductor(payload);
    setConductors((prev) => [...prev, nuevo]);
    return nuevo;
  }, []);

  const remove = useCallback(async (id) => {
    await deleteConductor(id);
    setConductors((prev) => prev.filter((c) => c.id !== id));
  }, []);

  return { conductors, loading, error, fromApi, reload: load, create, remove };
}
