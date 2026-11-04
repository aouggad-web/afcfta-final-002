import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import axios from 'axios';
import { supabase, TERMS_VERSION, creerClientVerification } from '../lib/supabase';
import { toast } from '../hooks/use-toast';
import i18n from '../i18n';

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
  otp_expired: 'Ce lien a expiré ou a déjà servi. Demandez-en un nouveau.',
};

// Mêmes messages pour l'interface en arabe ; le français reste servi en
// français comme en anglais, comme avant.
const SUPABASE_ERRORS_AR = {
  invalid_credentials: 'البريد الإلكتروني أو كلمة المرور غير صحيحة',
  email_not_confirmed: 'أكّد عنوان بريدك الإلكتروني: انقر على الرابط الذي وصلك عبر البريد.',
  user_already_exists: 'يوجد حساب مسجّل بهذا البريد الإلكتروني',
  weak_password: 'كلمة المرور ضعيفة جدًا: 8 أحرف على الأقل، امزج بين الحروف والأرقام.',
  over_email_send_rate_limit: 'طلبات كثيرة جدًا. أعد المحاولة بعد بضع دقائق.',
  over_request_rate_limit: 'طلبات كثيرة جدًا. أعد المحاولة بعد بضع دقائق.',
  same_password: 'يجب أن تختلف كلمة المرور الجديدة عن القديمة.',
  otp_expired: 'انتهت صلاحية هذا الرابط أو سبق استخدامه. اطلب رابطًا جديدًا.',
};

function supabaseError(error) {
  const arabe = i18n.language === 'ar' && SUPABASE_ERRORS_AR[error.code];
  return { response: { data: { detail: arabe || SUPABASE_ERRORS[error.code] || error.message } } };
}

// Liens envoyés par e-mail (confirmation d'adresse, mot de passe oublié,
// changement d'adresse) : /?token_hash=…&type=…, vérifiés par verifyOtp.
// Contrairement au code PKCE, ce jeton ne dépend pas du navigateur qui a fait
// la demande : le lien marche ouvert sur un autre appareil. Revers : un lien
// que quelqu'un obtient pour SON compte, puis transmet, connecterait la
// personne qui l'ouvre à ce compte (connexion forcée). D'où trois garde-fous :
// - le lien est vérifié par un client jetable, qui ne garde rien : la session
//   obtenue n'est confiée au client principal qu'après le contrôle ;
// - le navigateur qui fait la demande note l'adresse attendue (24 h) ; un lien
//   d'un autre compte y est refusé ;
// - un lien que ce navigateur n'attend pas (autre appareil, lien transmis,
//   scanner de messagerie) n'est vérifié qu'après un clic sur « Continuer ».
// Une fois la session ouverte, l'adresse du compte connecté est affichée.
const TYPES_LIEN_EMAIL = new Set(['email', 'signup', 'recovery', 'email_change']);
const CLE_LIEN_ATTENDU = 'zlecaf_lien_email_attendu';
// Durée de validité la plus longue des liens Supabase (confirmation : 24 h).
const DUREE_LIEN_ATTENDU_MS = 24 * 3600 * 1000;

function noterLienAttendu(email) {
  try {
    localStorage.setItem(CLE_LIEN_ATTENDU, JSON.stringify({ email, t: Date.now() }));
  } catch {
    // Stockage indisponible (navigation privée stricte) : le lien demandera
    // simplement une confirmation.
  }
}

function lireLienAttendu() {
  try {
    const marqueur = JSON.parse(localStorage.getItem(CLE_LIEN_ATTENDU) || 'null');
    if (marqueur && typeof marqueur.email === 'string' && Date.now() - marqueur.t < DUREE_LIEN_ATTENDU_MS) {
      return marqueur.email;
    }
    localStorage.removeItem(CLE_LIEN_ATTENDU);
  } catch {
    // Marqueur illisible ou stockage indisponible : traité comme absent.
  }
  return null;
}

function oublierLienAttendu() {
  try {
    localStorage.removeItem(CLE_LIEN_ATTENDU);
  } catch {
    // rien à faire
  }
}

const MESSAGES_LIEN = {
  connecte: { fr: 'Connecté en tant que {email}.', ar: 'تم تسجيل الدخول بالحساب {email}.' },
  autreCompte: {
    fr: "Ce lien concerne un autre compte que celui demandé dans ce navigateur : il a été refusé. Ouvrez-le sur l'appareil qui l'a demandé, ou demandez-en un nouveau.",
    ar: 'يخص هذا الرابط حسابًا غير الحساب المطلوب في هذا المتصفح، فتم رفضه. افتحه على الجهاز الذي طلبه، أو اطلب رابطًا جديدًا.',
  },
  confirmationEnregistree: {
    fr: "Confirmation enregistrée. Ouvrez aussi le lien envoyé à l'autre adresse.",
    ar: 'تم تسجيل التأكيد. افتح أيضًا الرابط المرسل إلى العنوان الآخر.',
  },
  serviceIndisponible: {
    fr: "Connexion au service d'authentification impossible, réessayez.",
    ar: 'تعذّر الاتصال بخدمة المصادقة، أعد المحاولة.',
  },
};

const attendre = (ms) => new Promise((fin) => setTimeout(fin, ms));

function messageLien(cle, email = '') {
  const m = MESSAGES_LIEN[cle];
  return (i18n.language === 'ar' ? m.ar : m.fr).replace('{email}', email);
}

export function lireLienEmail() {
  const url = new URL(window.location.href);
  const tokenHash = url.searchParams.get('token_hash');
  const type = url.searchParams.get('type');
  if (!tokenHash || !TYPES_LIEN_EMAIL.has(type)) return null;
  // Le jeton ne doit rester ni dans la barre d'adresse ni dans l'historique.
  // URL complète : un chemin relatif « //… » (Site URL terminée par « / »)
  // serait lu comme une autre origine et ferait échouer replaceState.
  url.searchParams.delete('token_hash');
  url.searchParams.delete('type');
  window.history.replaceState(window.history.state, '', url.href);
  return { tokenHash, type };
}

export function AuthProvider({ children }) {
  // undefined = checking session, null = logged out, object = logged in user
  const [user, setUser] = useState(undefined);
  // Vrai quand l'utilisateur arrive depuis le lien « mot de passe oublié ».
  const [recovery, setRecovery] = useState(false);
  // Lien d'e-mail que ce navigateur n'attendait pas : vérifié seulement si la
  // personne clique sur « Continuer » (voir lireLienEmail).
  const [lienEnAttente, setLienEnAttente] = useState(null);

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

  // Vérifie un lien d'e-mail. `attendu` : adresse notée par ce navigateur au
  // moment de la demande (null quand la personne a confirmé à la main).
  // La vérification passe par un client jetable : rien n'est enregistré ni
  // annoncé (autres onglets, écouteurs, serveur) avant le contrôle. Renvoie
  // le lien accepté ({ email, session, verification, type }), sinon null.
  const verifierLien = useCallback(async (lien, attendu) => {
    const verification = creerClientVerification();
    const { data, error } = await verification.auth.verifyOtp({
      token_hash: lien.tokenHash,
      type: lien.type,
    });
    if (error) {
      const detail = error.message && error.message !== '{}' ? supabaseError(error).response.data.detail : messageLien('serviceIndisponible');
      toast({ variant: 'destructive', description: detail });
      return null;
    }
    if (!data?.session) {
      // Rien à ouvrir (changement d'adresse : première des deux
      // confirmations) : aucun risque de connexion forcée.
      oublierLienAttendu();
      toast({ description: messageLien('confirmationEnregistree') });
      return null;
    }
    const email = String(data.user?.email || '').toLowerCase();
    if (attendu && email !== attendu) {
      // Lien d'un autre compte que celui demandé ici : la session obtenue est
      // révoquée côté Supabase, et le client principal n'en a jamais rien su.
      await verification.auth.signOut({ scope: 'local' }).catch(() => {});
      oublierLienAttendu();
      toast({ variant: 'destructive', description: messageLien('autreCompte') });
      return null;
    }
    oublierLienAttendu();
    return { email, session: data.session, verification, type: lien.type };
  }, []);

  // Ouvre la session du site pour un lien accepté, puis seulement la confie au
  // client principal (renouvellement, changement de mot de passe). Si le site
  // refuse, la session est révoquée et le client principal reste intact :
  // rien ne peut s'ouvrir plus tard sans prévenir.
  const ouvrirSessionLien = useCallback(
    async (accepte) => {
      let compte;
      try {
        compte = await syncSupabaseSession(accepte.session);
      } catch (err) {
        await accepte.verification.auth.signOut({ scope: 'local' }).catch(() => {});
        throw err;
      }
      let erreur = null;
      // Une coupure brève ne doit pas perdre un lien déjà consommé.
      for (const delai of [0, 500, 1500]) {
        if (delai) await attendre(delai);
        ({ error: erreur } = await supabase.auth.setSession({
          access_token: accepte.session.access_token,
          refresh_token: accepte.session.refresh_token,
        }));
        if (!erreur) break;
      }
      if (erreur) {
        toast({ variant: 'destructive', description: messageLien('serviceIndisponible') });
      } else if (accepte.type === 'recovery') {
        setRecovery(true);
      }
      toast({ description: messageLien('connecte', accepte.email) });
      return compte;
    },
    [syncSupabaseSession]
  );

  useEffect(() => {
    if (!supabase) {
      refreshUser();
      return undefined;
    }
    let active = true;
    const lien = lireLienEmail();
    const attendu = lien ? lireLienAttendu() : null;
    let verification = Promise.resolve(null);
    if (lien && attendu) {
      verification = verifierLien(lien, attendu).catch(() => null);
    } else if (lien) {
      setLienEnAttente(lien);
    }
    verification.then(async (accepte) => {
      if (accepte) {
        try {
          await ouvrirSessionLien(accepte);
        } catch (err) {
          toast({ variant: 'destructive', description: formatApiErrorDetail(err?.response?.data?.detail) });
          setUser(null);
        }
        return;
      }
      const { data } = await supabase.auth.getSession();
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
  }, [refreshUser, syncSupabaseSession, verifierLien, ouvrirSessionLien]);

  // Clic sur « Continuer » pour un lien non attendu. Ne rejette jamais : une
  // erreur est affichée, et « Connecté en tant que » n'apparaît qu'une fois la
  // session du site réellement ouverte.
  const confirmerLienEmail = async () => {
    const lien = lienEnAttente;
    setLienEnAttente(null);
    if (!lien) return null;
    try {
      const accepte = await verifierLien(lien, null);
      if (!accepte) return null;
      return await ouvrirSessionLien(accepte);
    } catch (err) {
      toast({
        variant: 'destructive',
        description: formatApiErrorDetail(err?.response?.data?.detail),
      });
      return null;
    }
  };

  const ignorerLienEmail = () => setLienEnAttente(null);

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
      if (!data.session) {
        noterLienAttendu(email.trim().toLowerCase());
        return { needsConfirmation: true };
      }
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
      oublierLienAttendu();
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
      oublierLienAttendu();
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
    noterLienAttendu(email.trim().toLowerCase());
  };

  const updatePassword = async (password) => {
    const { data, error } = await supabase.auth.updateUser({ password });
    if (error) throw supabaseError(error);
    setRecovery(false);
    const { data: current } = await supabase.auth.getSession();
    return syncSupabaseSession(current.session || data.session);
  };

  // Abonnement : état affiché dans Mon compte, et espace client Stripe
  // (carte bancaire, factures, changement de formule, résiliation).
  const getSubscription = useCallback(async () => {
    const { data } = await axios.get(`${API}/billing/subscription`, { withCredentials: true });
    return data;
  }, []);

  const openBillingPortal = async () => {
    const { data } = await axios.post(`${API}/billing/portal`, {}, { withCredentials: true });
    window.location.href = data.url;
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
        lienEnAttente,
        confirmerLienEmail,
        ignorerLienEmail,
        requestPasswordReset,
        updatePassword,
        exportAccount,
        deleteAccount,
        getSubscription,
        openBillingPortal,
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
