import { useState, useCallback } from "react";
import { calculateRates } from "../api/rates";
import {
  densificarTrazado,
  normalizarALatLon,
} from "../utils/geometryValidator";

/**
 * Orquesta el cálculo de rates: normaliza el payload al contrato
 * del backend (RateCalculationRequestDTO) y gestiona el estado.
 */
export function useRateCalculation() {
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const calculate = useCallback(
    async ({
      coordenadas,
      conductor,
      escenarios,
      useDem,
      studyCaseId = null,
    }) => {
      setLoading(true);
      setError(null);
      setResultado(null);

      try {
        // Normalizar a {lat, lon} por si llegara algo con {lat, lng}
        const coordsNorm = normalizarALatLon(coordenadas);
        const coordsDensas = densificarTrazado(coordsNorm, 500);
        const tieneZExcel = coordsDensas.some((c) => (c.altitud ?? 0) > 0);
        const esFicheroReal = coordsDensas.length > 10;

        const payload = {
          coordinates: coordsDensas.map(({ lat, lon }) => ({ lat, lon })),
          conductor: {
            diameter_mm: conductor.diameter_mm,
            r_ac_75_ohm_km: conductor.r_ac_75_ohm_km,
            r_ac_25_ohm_km: conductor.r_ac_25_ohm_km,
            emissivity: conductor.emissivity ?? 0.5,
            absorptivity: conductor.absorptivity ?? 0.5,
            max_temp_c: conductor.max_temp_c,
          },
          scenarios: Object.entries(escenarios).map(([season, s]) => ({
            season,
            temp_amb_c: s.temp,
            wind_speed_ms: s.viento,
            wind_angle_deg: s.angulo,
            solar_radiation_wm2: s.radiacion,
          })),
          segment_step_m: 500,
          use_real_spans: tieneZExcel || esFicheroReal,
          use_dem: useDem && !tieneZExcel,
        };

        const data = await calculateRates(payload, studyCaseId);
        setResultado(data);
        return data;
      } catch (err) {
        setError(err.message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setResultado(null);
    setError(null);
  }, []);

  return { calculate, resultado, loading, error, reset };
}
