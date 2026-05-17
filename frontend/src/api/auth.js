import { apiClient, extractErrorMessage } from "./client";

export async function login(username, password) {
  try {
    const { data } = await apiClient.post("/auth/token", {
      username,
      password,
    });
    return data; // { access_token, token_type, user_id, username }
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}

export async function register(username, password) {
  try {
    const { data } = await apiClient.post("/users", {
      username,
      password,
    });
    return data;
  } catch (err) {
    throw new Error(extractErrorMessage(err));
  }
}
