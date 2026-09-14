import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { api } from "../api/client";
import { User } from "../api/types";

interface AuthState {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("milan_token"));
  const [user, setUser] = useState<User | null>(null);

  const refreshUser = useCallback(async (): Promise<User | null> => {
    try {
      const me = await api<User>("/auth/me");
      setUser(me);
      return me;
    } catch {
      setUser(null);
      localStorage.removeItem("milan_token");
      setToken(null);
      return null;
    }
  }, []);

  useEffect(() => {
    if (token) void refreshUser();
  }, [token, refreshUser]);

  useEffect(() => {
    const handler = () => {
      localStorage.removeItem("milan_token");
      setToken(null);
      setUser(null);
    };
    window.addEventListener("milan-unauthorized", handler);
    return () => window.removeEventListener("milan-unauthorized", handler);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);
    const res = await fetch("/api/auth/login", { method: "POST", body: form });
    if (!res.ok) {
      let detail = "No se pudo iniciar sesión";
      try {
        const data = await res.json();
        if (typeof data.detail === "string") detail = data.detail;
      } catch {
        /* ignore */
      }
      throw new Error(detail);
    }
    const data = await res.json();
    localStorage.setItem("milan_token", data.access_token);
    setToken(data.access_token);
    const me = await refreshUser();
    if (!me) throw new Error("No se pudo cargar el usuario");
    return me;
  }, [refreshUser]);

  const logout = useCallback(() => {
    localStorage.removeItem("milan_token");
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, token, login, logout, isAdmin: user?.role === "admin" }),
    [user, token, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}