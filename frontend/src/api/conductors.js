import { apiClient, extractErrorMessage } from "./client";

export async function getConductors() {
  try {
    const { data } = await apiClient.get("/conductors/");
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function createConductor(payload) {
  try {
    const { data } = await apiClient.post("/conductors/", payload);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function updateConductor(id, payload) {
  try {
    const { data } = await apiClient.put(`/conductors/${id}`, payload);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function deleteConductor(id) {
  try {
    await apiClient.delete(`/conductors/${id}`);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
