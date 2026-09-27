import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, setAccessToken, setUnauthorizedHandler } from "./api";
import type { User } from "@/types/api";

const ACCESS_KEY = "consilium.access";
const REFRESH_KEY = "consilium.refresh";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    setUser(null);
    setAccessToken(null);
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }, []);

  // Restore session on mount.
  useEffect(() => {
    const token = localStorage.getItem(ACCESS_KEY);
    setUnauthorizedHandler(() => logout());
    if (!token) {
      setLoading(false);
      return;
    }
    setAccessToken(token);
    api
      .me()
      .then((u) => setUser(u))
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [logout]);

  const login = useCallback(
    async (email: string, password: string) => {
      const resp = await api.login(email, password);
      setAccessToken(resp.access_token);
      localStorage.setItem(ACCESS_KEY, resp.access_token);
      localStorage.setItem(REFRESH_KEY, resp.refresh_token);
      const u = await api.me();
      setUser(u);
    },
    []
  );

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
