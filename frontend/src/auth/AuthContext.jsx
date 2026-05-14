import { useState, useEffect, useCallback } from "react";
import { login as apiLogin, register as apiRegister } from "../api/auth";
import { AuthContext, loadSession } from "./authContext";

export function AuthProvider({ children }) {
  const [session, setSession] = useState(loadSession);
  const isAuthenticated = Boolean(session);

  // Escucha el evento que dispara el interceptor 401
  useEffect(() => {
    const handleLogout = () => setSession(null);
    window.addEventListener("auth:logout", handleLogout);
    return () => window.removeEventListener("auth:logout", handleLogout);
  }, []);

  const persistSession = useCallback((data) => {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem(
      "user",
      JSON.stringify({ id: data.user_id, username: data.username }),
    );
    setSession({
      token: data.access_token,
      user: { id: data.user_id, username: data.username },
    });
  }, []);

  const login = useCallback(
    async (username, password) => {
      const data = await apiLogin(username, password);
      persistSession(data);
      return data;
    },
    [persistSession],
  );

  const register = useCallback(
    async (username, password) => {
      const data = await apiRegister(username, password);
      persistSession(data);
      return data;
    },
    [persistSession],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setSession(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ session, isAuthenticated, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}
