/**
 * Catálogo estándar de conductores.
 * El frontend los usa como fallback hasta que GET /conductors responda.
 */
export const DEFAULT_CONDUCTORS = [
  {
    id: "00000000-0000-0000-0000-000000000001",
    name: "LA-110 (Hawk)",
    description:
      "Conductor de aluminio-acero 110 mm² — uso frecuente en distribución.",
    diameter_mm: 21.78,
    r_ac_75_ohm_km: 0.119,
    r_ac_25_ohm_km: 0.101,
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 85,
  },
  {
    id: "00000000-0000-0000-0000-000000000002",
    name: "LA-280 (Condor)",
    description:
      "Conductor de aluminio-acero 280 mm² — transporte en alta tensión.",
    diameter_mm: 27.72,
    r_ac_75_ohm_km: 0.072,
    r_ac_25_ohm_km: 0.061,
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 90,
  },
  {
    id: "00000000-0000-0000-0000-000000000003",
    name: "LA-380 (Gull)",
    description: "Conductor de aluminio-acero 380 mm² — alta capacidad.",
    diameter_mm: 25.4,
    r_ac_75_ohm_km: 0.089,
    r_ac_25_ohm_km: 0.076,
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 90,
  },
  {
    id: "00000000-0000-0000-0000-000000000004",
    name: "LA-455 (Cardinal)",
    description: "Conductor de aluminio-acero 455 mm² — muy alta capacidad.",
    diameter_mm: 30.42,
    r_ac_75_ohm_km: 0.059,
    r_ac_25_ohm_km: 0.05,
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 90,
  },
];
