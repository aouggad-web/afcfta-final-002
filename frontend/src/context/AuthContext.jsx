import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import axios from 'axios';
import { supabase, TERMS_VERSION } from '../lib/supabase';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

// Messages Supabase Auth → libellés FR affichés par la modale (qui lit
// `err.response.data.detail`, comme pour les erreurs du backend).
const SUPABASE_ERRORS = {
  invalid_credentials: 'Email ou mot de passe incorrect',
  email_not_confirmed: 'Confirmez votre adresse email : cliquez sur le lien reçu par email.',
  user_already_exists: 'Un compte existe déjà avec cet email',
  weak_password: 'Mot de passe trop faible : 8 caractères minimum, mélangez lettres et chiffres.',
  over_email_send_rate_limit: 'Trop de demandes. Réessayez dans quelques minutes.',
  over_request_rate_limit: 'Trop de demandes. Réessayez dans quelques minutes.',
  same_password: 'Le nouveau mot de passe doit être différent de l\'ancien.',
};

function supabaseError(error) {
  return { response: { data: { detail: SUPABASE_ERRORS[error.code] || error.message } } };
}

export function AuthProvider({ children }) {
  // undefined = checking session, null = logged out, object = logged in user
  const [user, setUser] = useState(undefined);
  // Vrai quand l'utilisateur arrive depuis le lien « mot de passe oublié ».
  const [recovery, setRecovery] = useState(false);

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(data);
    } catch {
      setUser(null);
    }
  }, []);

  // Session Supabase → cookie de session du site (POST /auth/session), pour
  // que tout le reste (pricing.html, paiements, quotas) fonctionne inchangé.
  const syncSupabaseSession = useCallback(async (session) => {
    if (!session) {
      setUser(null);
      return null;
    }
    const { data } = await axios.post(
      `${API}/auth/session`,
      {},
      { withCredentials: true, headers: { Authorization: `Bearer ${session.access_token}` } }
    );
    setUser(data);
    return data;
  }, []);

  useEffect(() => {
    if (!supabase) {
      refreshUser();
      return undefined;
    }
    let active = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      if (data.session) {
        syncSupabaseSession(data.session).catch(() => setUser(null));
      } else {
        // Session de l'ancien système encore valide pendant la transition.
        refreshUser();
      }
    });
    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'PASSWORD_RECOVERY') setRecovery(true);
      if (event === 'TOKEN_REFRESHED') syncSupabaseSession(session).catch(() => {});
      if (event === 'SIGNED_OUT') setUser(null);
    });
    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, [refreshUser, syncSupabaseSession]);

  const register = async (name, email, password) => {
    if (supabase) {
      const { data, error } = await supabase.auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: {
          emailRedirectTo: window.location.origin,
          data: {
            name: name.trim().replace(/\s+/g, ' '),
            terms_version: TERMS_VERSION,
            terms_accepted_at: new Date().toISOString(),
          },
        },
      });
      if (error) throw supabaseError(error);
      // Confirmation d'email activée : pas de session tant que le lien
      // reçu par email n'a pas été cliqué.
      if (!data.session) return { needsConfirmation: true };
      return syncSupabaseSession(data.session);
    }
    const { data } = await axios.post(
      `${API}/auth/register`,
      { name: name.trim().replace(/\s+/g, ' '), email: email.trim().toLowerCase(), password },
      { withCredentials: true }
    );
    setUser(data);
    return data;
  };

  const login = async (email, password) => {
    if (supabase) {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      });
      if (error) throw supabaseError(error);
      return syncSupabaseSession(data.session);
    }
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
      if (supabase) await supabase.auth.signOut();
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } finally {
      // L'interface ne doit jamais conserver une identité affichée si la
      // déconnexion réseau échoue ; le cookie expirera côté serveur/navigateur.
      setUser(null);
    }
  };

  const requestPasswordReset = async (email) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim().toLowerCase(), {
      redirectTo: window.location.origin,
    });
    if (error) throw supabaseError(error);
  };

  const updatePassword = async (password) => {
    const { data, error } = await supabase.auth.updateUser({ password });
    if (error) throw supabaseError(error);
    setRecovery(false);
    const { data: current } = await supabase.auth.getSession();
    return syncSupabaseSession(current.session || data.session);
  };

  // Droits RGPD : copie de toutes ses données (fichier JSON) et suppression.
  const exportAccount = async () => {
    const { data } = await axios.get(`${API}/auth/account/export`, { withCredentials: true });
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'mes-donnees-zlecaf.json';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const deleteAccount = async () => {
    await axios.delete(`${API}/auth/account`, { withCredentials: true });
    if (supabase) await supabase.auth.signOut({ scope: 'local' }).catch(() => {});
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        register,
        login,
        logout,
        supabaseEnabled: Boolean(supabase),
        recovery,
        requestPasswordReset,
        updatePassword,
        exportAccount,
        deleteAccount,
      }}
    >
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
  if (typeof detail === 'string') return detail.trim() || fallback;
  if (Array.isArray(detail)) {
    const message = detail
      .map((e) => (e && typeof e.msg === 'string' ? e.msg : JSON.stringify(e)))
      .filter(Boolean)
      .join(' ')
      .trim();
    return message || fallback;
  }
  if (detail && typeof detail.msg === 'string') {
    return detail.msg.trim() || fallback;
  }
  return String(detail);
}
