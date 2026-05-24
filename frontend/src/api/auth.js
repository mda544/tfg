import { apiClient, extractErrorMessage } from "./client";

export async function login(username, password) {
  try {
    const { data } = await apiClient.post("/auth/sessions", {
      username,
      password,
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function register(username, password) {
  try {
    const { data } = await apiClient.post("/auth/users", {
      username,
      password,
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
