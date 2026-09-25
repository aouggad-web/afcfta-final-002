import { createClient } from '@supabase/supabase-js';

// Comptes gérés par Supabase Auth quand le projet est configuré. Sans ces deux
// variables, `supabase` vaut null et l'ancien système de comptes (routes
// /api/auth/register|login du backend) reste utilisé tel quel.
const url = import.meta.env.VITE_SUPABASE_URL;
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const supabase = url && publishableKey ? createClient(url, publishableKey) : null;

// Version des CGU / politique de confidentialité acceptée à l'inscription.
// À changer à chaque nouvelle version des textes (preuve du consentement).
export const TERMS_VERSION = '2026-09';
