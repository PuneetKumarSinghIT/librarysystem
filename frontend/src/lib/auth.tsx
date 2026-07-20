"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api, getToken, setToken, Staff } from "./api";
import { STAFF_KEY } from "./config";

interface AuthState {
  staff: Staff | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [staff, setStaff] = useState<Staff | null>(null);
  const [ready, setReady] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Restore session hint from a stored token (staff details re-fetched on login).
    const token = getToken();
    if (token) {
      const cached = window.localStorage.getItem(STAFF_KEY);
      if (cached) setStaff(JSON.parse(cached));
    }
    setReady(true);
  }, []);

  async function login(email: string, password: string) {
    const res = await api.login(email, password);
    setToken(res.access_token);
    window.localStorage.setItem(STAFF_KEY, JSON.stringify(res.staff));
    setStaff(res.staff);
    router.push("/books");
  }

  function logout() {
    setToken(null);
    window.localStorage.removeItem(STAFF_KEY);
    setStaff(null);
    router.push("/login");
  }

  return (
    <AuthContext.Provider value={{ staff, ready, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
