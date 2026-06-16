import { useState, useCallback } from "react";
import { createCalculation } from "../api/calculations";

/**
 * Convierte los escenarios internos al array WeatherInputDTO
 * que espera POST /study-cases/{id}/calculations.
 * Escenarios internos: { verano: { temp, viento, angulo, radiacion, wind_dir_predominant_deg }, ... }
 */
function buildWeatherInputs(scenarios) {
  return Object.entries(scenarios).map(([season, s]) => ({
    season,
    temp_amb_c: s.temp,
    wind_speed_ms: s.viento,
    wind_angle_deg: s.angulo ?? 90,
    solar_radiation_wm2: s.radiacion,
    wind_dir_predominant_deg: s.wind_dir_predominant_deg ?? null,
  }));
}

export function useCalculateRates() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * @param {Object} params
   * @param {string} params.studyCaseId     id del caso de estudio (ya tiene el conductor)
   * @param {Object} params.scenarios       { verano: {temp, viento, angulo, radiacion, wind_dir_predominant_deg}, ... }
   * @param {string} [params.climateSource] "openmeteo" | "nasa" | "manual"
   *
   */
  const calculate = useCallback(
    async ({ studyCaseId, scenarios, climateSource = "manual" }) => {
      if (!studyCaseId) {
        setError("Falta el caso de estudio.");
        return null;
      }

      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const payload = {
          study_case_id: studyCaseId,
          weather_inputs: buildWeatherInputs(scenarios),
          climate_source: climateSource,
        };

        const data = await createCalculation(studyCaseId, payload);
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

  return { calculate, result, setResult, loading, error, reset };
}
