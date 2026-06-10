import { useState, useCallback } from "react";
import { calculateRates } from "../api/rates";

/**
 * Convierte el mapa de escenarios internos al array WeatherInputDTO
 */
function buildWeatherInputs(scenarios) {
  return Object.entries(scenarios).map(([season, s]) => ({
    season,
    temp_amb_c: s.temp,
    wind_speed_ms: s.viento,
    wind_angle_deg: s.angulo,
    solar_radiation_wm2: s.radiacion,
    wind_dir_predominant_deg: s.wind_dir_predominant_deg ?? null,
  }));
}

export function useCalculateRates() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const calculate = useCallback(
    async ({
      studyCaseId,
      conductorId,
      scenarios,
      climateSource = "manual",
    }) => {
      if (!studyCaseId || !conductorId) {
        setError("Falta el caso de estudio o el conductor.");
        return null;
      }

      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const payload = {
          study_case_id: studyCaseId,
          conductor_id: conductorId,
          weather_inputs: buildWeatherInputs(scenarios),
          climate_source: climateSource,
        };

        const data = await calculateRates(payload);
        setResult(data);
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
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, calculate, reset };
}
