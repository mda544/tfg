import { apiClient, extractErrorMessage } from "./client";

/**
 * Calcula rates estacionales IEEE 738.
 * @param {import('../api/types').RateCalculationRequest} payload
 * @param {string} [studyCaseId]
 */
export async function calculateRates(payload, studyCaseId = null) {
  try {
    const params = studyCaseId ? { study_case_id: studyCaseId } : {};
    const { data } = await apiClient.post("/rates/", payload, { params });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function getRatesByStudyCase(caseId) {
  try {
    const { data } = await apiClient.get("/rates/", {
      params: { case_id: caseId },
    });
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
