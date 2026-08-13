import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // undefined = checking session, null = logged out, object = logged in user
  const [user, setUser] = useState(undefined);

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(data);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const register = async (name, email, password) => {
    const { data } = await axios.post(
      `${API}/auth/register`,
      { name: name.trim().replace(/\s+/g, ' '), email: email.trim().toLowerCase(), password },
      { withCredentials: true }
    );
    setUser(data);
    return data;
  };

  const login = async (email, password) => {
    const { data } = await axios.post(
      `${API}/auth/login`,
      { email: email.trim().toLowerCase(), password },
      { withCredentials: true }
    );
    setUser(data);
    return data;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } finally {
      // L'interface ne doit jamais conserver une identité affichée si la
      // déconnexion réseau échoue ; le cookie expirera côté serveur/navigateur.
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function formatApiErrorDetail(
  detail,
  fallback = 'Une erreur est survenue. Veuillez réessayer.'
) {
  if (detail == null) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => (e && typeof e.msg === 'string' ? e.msg : JSON.stringify(e)))
      .filter(Boolean)
      .join(' ');
  }
  if (detail && typeof detail.msg === 'string') return detail.msg;
  return String(detail);
}
