import { createClient } from '@supabase/supabase-js';

// Comptes gérés par Supabase Auth quand le projet est configuré. Sans ces deux
// variables, `supabase` vaut null et l'ancien système de comptes (routes
// /api/auth/register|login du backend) reste utilisé tel quel.
const url = import.meta.env.VITE_SUPABASE_URL;
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

// Flux PKCE (audit M6). Par défaut, le client utilise le flux « implicit » :
// le lien de connexion ramène la session dans l'URL (#access_token=…), qui
// peut fuir par l'historique ou l'en-tête Referer, et qu'un tiers peut forger
// pour connecter un visiteur à son propre compte. En PKCE, ce retour se fait
// par un code échangé contre la session avec une preuve gardée par ce
// navigateur seulement. Les liens envoyés par e-mail portent, eux, un
// token_hash vérifié par AuthContext : ils marchent aussi ouverts sur un autre
// appareil (voir docs/ACTIVER_SUPABASE.md, modèles d'e-mail). Ce jeton n'étant
// lié à aucun navigateur, AuthContext ne l'utilise sans demander que si ce
// navigateur l'attendait, pour la même adresse (voir lireLienEmail).
export const SUPABASE_AUTH_OPTIONS = {
  flowType: 'pkce',
  autoRefreshToken: true,
  persistSession: true,
  detectSessionInUrl: true,
};

export const supabase =
  url && publishableKey
    ? createClient(url, publishableKey, { auth: SUPABASE_AUTH_OPTIONS })
    : null;

// Client jetable pour vérifier un lien d'e-mail : il ne garde rien (ni
// stockage, ni rafraîchissement, ni diffusion aux autres onglets). La session
// qu'il obtient n'est confiée au client principal qu'après le contrôle de
// l'adresse, si bien qu'un lien refusé ne laisse aucune trace (voir
// AuthContext, lireLienEmail).
export function creerClientVerification() {
  return createClient(url, publishableKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
      storageKey: 'zlecaf-verification-lien',
    },
  });
}

// Version des CGU / politique de confidentialité acceptée à l'inscription.
// À changer à chaque nouvelle version des textes (preuve du consentement).
export const TERMS_VERSION = '2026-11';
