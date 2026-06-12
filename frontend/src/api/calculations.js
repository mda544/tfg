import { apiClient, extractErrorMessage } from "./client";

/** POST /study-cases/{caseId}/calculations */
export async function createCalculation(caseId, payload) {
  try {
    const { data } = await apiClient.post(
      `/study-cases/${caseId}/calculations/`,
      payload,
    );
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

/** GET /study-cases/{caseId}/calculations */
export async function getCalculationsByStudyCase(caseId) {
  try {
    const { data } = await apiClient.get(
      `/study-cases/${caseId}/calculations/`,
    );
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

/** GET /study-cases/{caseId}/calculations/{calcId} */
export async function getCalculation(caseId, calcId) {
  try {
    const { data } = await apiClient.get(
      `/study-cases/${caseId}/calculations/${calcId}`,
    );
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

/** DELETE /study-cases/{caseId}/calculations/{calcId} */
export async function deleteCalculation(caseId, calcId) {
  try {
    await apiClient.delete(`/study-cases/${caseId}/calculations/${calcId}`);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
