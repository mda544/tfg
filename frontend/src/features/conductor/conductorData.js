/**
 * Catálogo estándar de conductores.
 * Cargados en la bd.
 * Se usan como fallback mientras GET /conductors carga.
 */
export const DEFAULT_CONDUCTORS = [
  {
    id:             "00000000-0000-0000-0000-000000000001",
    name:           "LA-110 (Hawk)",
    diameter_mm:    21.78,
    r_ac_75_ohm_km: 0.119,
    r_ac_25_ohm_km: 0.101,
    emissivity:     0.5,
    absorptivity:   0.5,
    max_temp_c:     85,
  },
  {
    id:             "00000000-0000-0000-0000-000000000002",
    name:           "LA-280 (Condor)",
    diameter_mm:    27.72,
    r_ac_75_ohm_km: 0.072,
    r_ac_25_ohm_km: 0.061,
    emissivity:     0.5,
    absorptivity:   0.5,
    max_temp_c:     90,
  },
  {
    id:             "00000000-0000-0000-0000-000000000003",
    name:           "LA-380 (Gull)",
    diameter_mm:    25.4,
    r_ac_75_ohm_km: 0.089,
    r_ac_25_ohm_km: 0.076,
    emissivity:     0.5,
    absorptivity:   0.5,
    max_temp_c:     90,
  },
  {
    id:             "00000000-0000-0000-0000-000000000004",
    name:           "LA-455 (Cardinal)",
    diameter_mm:    30.42,
    r_ac_75_ohm_km: 0.059,
    r_ac_25_ohm_km: 0.05,
    emissivity:     0.5,
    absorptivity:   0.5,
    max_temp_c:     90,
  },
];