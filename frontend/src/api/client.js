import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url ?? "";
      const PUBLIC = ["/auth/sessions", "/auth/users"];
      if (!PUBLIC.some((u) => url.includes(u))) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.dispatchEvent(new Event("auth:logout"));
      }
    }
    return Promise.reject(error);
  },
);

export function extractErrorMessage(error) {
  if (error.response) {
    const { status, data } = error.response;
    if (status === 422 && data.detail) {
      if (typeof data.detail === "string") return data.detail;
      if (Array.isArray(data.detail))
        return data.detail
          .map((e) => `${e.loc?.join(".")}: ${e.msg}`)
          .join(" | ");
    }
    return data?.detail || `Error del servidor (${status})`;
  }
  if (error.request) return "No se pudo contactar con el servidor.";
  return "Error inesperado.";
}
