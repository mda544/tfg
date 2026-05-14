import { apiClient, extractErrorMessage } from "./client";

export async function getStudyCases() {
  try {
    const { data } = await apiClient.get("/study-cases/");
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function createStudyCase(payload) {
  try {
    const { data } = await apiClient.post("/study-cases/", payload);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function getStudyCase(id) {
  try {
    const { data } = await apiClient.get(`/study-cases/${id}`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function updateStudyCase(id, payload) {
  try {
    const { data } = await apiClient.put(`/study-cases/${id}`, payload);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function deleteStudyCase(id) {
  try {
    await apiClient.delete(`/study-cases/${id}`);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
