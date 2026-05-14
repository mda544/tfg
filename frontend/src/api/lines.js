import { apiClient, extractErrorMessage } from "./client";

export async function getLines() {
  try {
    const { data } = await apiClient.get("/lines/");
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function createLine(payload) {
  // payload: { name, description?, coordinates: [{lat, lon}] }
  try {
    const { data } = await apiClient.post("/lines/", payload);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function getLine(id) {
  try {
    const { data } = await apiClient.get(`/lines/${id}`);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function updateLine(id, payload) {
  try {
    const { data } = await apiClient.put(`/lines/${id}`, payload);
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function deleteLine(id) {
  try {
    await apiClient.delete(`/lines/${id}`);
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
