import { apiClient, extractErrorMessage } from "./client";

/**
 * Obtiene percentiles climáticos históricos para un punto geográfico.
 * @param {number} lat
 * @param {number} lon
 * @param {string} source  "openmeteo" | "nasa"
 */
export async function getClimatePercentiles(
  lat,
  lon,
  source = "openmeteo",
  yearStart = 1990,
  yearEnd = 2023,
) {
  try {
    const { data } = await apiClient.get("/climate/percentiles", {
      params: { lat, lon, source, year_start: yearStart, year_end: yearEnd },
    });
    return data; // ClimatePercentilesResponseDTO
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
