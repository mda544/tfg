import { apiClient, extractErrorMessage } from "./client";

export async function getElevation(lat, lon) {
  try {
    const { data } = await apiClient.get("/elevation/", {
      params: { lat, lon },
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
