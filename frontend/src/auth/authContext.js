import { createContext } from "react";

export const AuthContext = createContext(null);

export function loadSession() {
  try {
    const token = localStorage.getItem("access_token");
    const user  = JSON.parse(localStorage.getItem("user") ?? "null");
    return token && user ? { token, user } : null;
  } catch {
    return null;
  }
}