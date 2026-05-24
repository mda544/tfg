import { apiClient, extractErrorMessage } from "./client";

/**
 * POST /rates
 * @param {{ study_case_id, conductor_id, weather_inputs, climate_source }} payload
 */
export async function calculateRates(payload) {
  try {
    const { data } = await apiClient.post("/rates/", payload);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

/** GET /study-cases/{id}/rates — historial de un caso de estudio */
export async function getRatesByStudyCase(caseId) {
  try {
    const { data } = await apiClient.get(`/study-cases/${caseId}/rates`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function getRate(id) {
  try {
    const { data } = await apiClient.get(`/rates/${id}`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function deleteRate(id) {
  try {
    await apiClient.delete(`/rates/${id}`);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
