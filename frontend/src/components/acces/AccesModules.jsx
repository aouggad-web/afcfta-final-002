import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { pick } from '../../i18n/lang';

/**
 * Accès aux modules (décision de l'exploitant du 09/11/2026) :
 * - sans compte, seul le tableau de bord d'accueil est consultable ;
 * - un compte inscrit (e-mail validé) sans abonnement a, chaque mois, 2 calculs
 *   et 5 recherches par module, puis l'invitation à s'abonner ;
 * - Opportunités et Outils restent réservés aux abonnés.
 * Le serveur fait foi (entitlement_guard) ; l'écran explique ses refus.
 */

export const PRICING_URL = '/pricing.html';
export const EVENEMENT_ACCES = 'zlecaf:acces-refuse';
export const ONGLETS_PUBLICS = ['dashboard', 'contact'];

const T = {
  titreConnexion: ['Créez votre compte gratuit', 'Create your free account', 'أنشئ حسابك المجاني'],
  texteConnexion: [
    "Sans compte, seul le tableau de bord est consultable. Avec un compte (adresse e-mail validée), vous disposez chaque mois de 2 calculs et de 5 recherches dans chaque module. Abonnez-vous pour un accès sans limite.",
    'Without an account, only the dashboard is available. With an account (verified email), you get 2 calculations and 5 searches in each module every month. Subscribe for unlimited access.',
    'بدون حساب، لا يمكن الاطلاع إلا على لوحة القيادة. مع حساب (بريد إلكتروني مؤكَّد) تحصل كل شهر على حسابين و5 عمليات بحث في كل وحدة. اشترك للوصول دون حدود.',
  ],
  seConnecter: ['Créer un compte / Se connecter', 'Sign up / Sign in', 'إنشاء حساب / تسجيل الدخول'],
  voirFormules: ['Voir les formules', 'See plans', 'عرض الاشتراكات'],
  fermer: ['Fermer', 'Close', 'إغلاق'],
  titreQuota: ['Vos recherches gratuites du mois sont utilisées', 'Your free searches for this month are used up', 'استُنفدت عمليات بحثك المجانية لهذا الشهر'],
  texteQuota: [
    'Vous avez utilisé vos {quota} recherches gratuites du mois dans ce module. Abonnez-vous pour continuer sans limite.',
    'You have used your {quota} free searches this month in this module. Subscribe to continue without limits.',
    'استخدمت عمليات البحث المجانية الـ{quota} لهذا الشهر في هذه الوحدة. اشترك للمتابعة دون حدود.',
  ],
  titreCalculs: ['Vos calculs gratuits du mois sont utilisés', 'Your free calculations for this month are used up', 'استُنفدت حساباتك المجانية لهذا الشهر'],
  texteCalculs: [
    'Vous avez utilisé vos {quota} calculs gratuits du mois. Abonnez-vous pour continuer.',
    'You have used your {quota} free calculations this month. Subscribe to continue.',
    'استخدمت حساباتك المجانية الـ{quota} لهذا الشهر. اشترك للمتابعة.',
  ],
  titreAbonnes: ['Réservé aux abonnés', 'Subscribers only', 'مخصص للمشتركين'],
  texteAbonnes: [
    'Ce module est inclus dans les formules payantes. Abonnez-vous pour y accéder.',
    'This module is included in paid plans. Subscribe to access it.',
    'هذه الوحدة مشمولة في الاشتراكات المدفوعة. اشترك للوصول إليها.',
  ],
};
const tr = (lang, [fr, en, ar]) => pick(lang, fr, en, ar);

/** Refus d'accès d'une réponse du serveur, ou null (les 403 du jeton CSRF,
 *  sans `detail.error`, ne sont pas des refus d'accès). */
export function refusAcces(error) {
  const statut = error?.response?.status;
  const detail = error?.response?.data?.detail;
  if (!detail || typeof detail !== 'object') return null;
  if (statut === 401 && detail.error === 'login_required') return { genre: 'connexion', ...detail };
  if (statut === 429 && detail.error === 'quota_exceeded') return { genre: 'quota', ...detail };
  if (statut === 403 && detail.error === 'upgrade_required') return { genre: 'abonnes', ...detail };
  return null;
}

let intercepteurPose = false;
/** Prévient l'écran à chaque refus d'accès, quel que soit le module qui l'a
 *  reçu (les modules de consultation n'ont pas de message à eux). */
export function installerInterceptionAcces() {
  if (intercepteurPose) return;
  intercepteurPose = true;
  axios.interceptors.response.use(undefined, (error) => {
    const refus = refusAcces(error);
    // Le calculateur et ses comparaisons affichent déjà leur propre message.
    if (refus && refus.module !== 'calculator') {
      window.dispatchEvent(new CustomEvent(EVENEMENT_ACCES, { detail: refus }));
    }
    return Promise.reject(error);
  });
}

const boutonPrincipal = {
  background: 'var(--terra)',
  color: 'var(--bg)',
  border: 'none',
  borderRadius: 10,
  padding: '10px 18px',
  fontWeight: 700,
  cursor: 'pointer',
};
const boutonSecondaire = {
  background: 'transparent',
  color: 'var(--text)',
  border: '1px solid var(--lift-border)',
  borderRadius: 10,
  padding: '10px 18px',
  fontWeight: 600,
  cursor: 'pointer',
  textDecoration: 'none',
  display: 'inline-block',
};

/** À la place d'un module, pour un visiteur sans compte. */
export function ConnexionRequise({ language, onOpenAuth }) {
  return (
    <div className="afcfta-section afcfta-fadeIn" data-testid="connexion-requise">
      <div className="stats-hero" style={{ textAlign: 'center', padding: '40px 24px' }}>
        <div style={{ fontSize: 36 }} aria-hidden="true">🔒</div>
        <h2 className="stats-hero-title" style={{ marginTop: 8 }}>{tr(language, T.titreConnexion)}</h2>
        <p className="stats-hero-subtitle" style={{ maxWidth: 640, margin: '12px auto 0' }}>{tr(language, T.texteConnexion)}</p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', marginTop: 22 }}>
          <button type="button" style={boutonPrincipal} onClick={onOpenAuth}>{tr(language, T.seConnecter)}</button>
          <a href={PRICING_URL} style={boutonSecondaire}>{tr(language, T.voirFormules)}</a>
        </div>
      </div>
    </div>
  );
}

function textes(refus, language) {
  const avecQuota = (modele) => tr(language, modele).replace('{quota}', String(refus.quota ?? ''));
  if (refus.genre === 'connexion') return [tr(language, T.titreConnexion), tr(language, T.texteConnexion)];
  if (refus.genre === 'quota') {
    return refus.module === 'calculator'
      ? [tr(language, T.titreCalculs), avecQuota(T.texteCalculs)]
      : [tr(language, T.titreQuota), avecQuota(T.texteQuota)];
  }
  return [tr(language, T.titreAbonnes), tr(language, T.texteAbonnes)];
}

/** Fenêtre d'invitation : connexion, ou abonnement quand le quota du mois est
 *  atteint ou que le module est réservé aux abonnés. */
export function InvitationAbonnement({ language, onOpenAuth }) {
  const [refus, setRefus] = useState(null);
  useEffect(() => {
    const surRefus = (e) => setRefus(e.detail);
    window.addEventListener(EVENEMENT_ACCES, surRefus);
    return () => window.removeEventListener(EVENEMENT_ACCES, surRefus);
  }, []);
  useEffect(() => {
    if (!refus) return undefined;
    const echap = (e) => e.key === 'Escape' && setRefus(null);
    window.addEventListener('keydown', echap);
    return () => window.removeEventListener('keydown', echap);
  }, [refus]);
  if (!refus) return null;
  const [titre, texte] = textes(refus, language);
  return (
    <div
      data-testid="invitation-abonnement"
      style={{ position: 'fixed', inset: 0, zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.55)', padding: 16 }}
      onClick={(e) => e.target === e.currentTarget && setRefus(null)}
    >
      <div role="dialog" aria-modal="true" aria-labelledby="invitation-abonnement-titre" style={{ position: 'relative', maxWidth: 480, width: '100%', background: 'var(--afcfta-card)', color: 'var(--text)', borderRadius: 16, padding: '30px 24px 22px', border: '1px solid var(--lift-border)' }}>
        <h2 id="invitation-abonnement-titre" style={{ fontSize: 20, fontWeight: 800, marginBottom: 10 }}>{titre}</h2>
        <p style={{ color: 'var(--text-soft)', fontSize: 14, lineHeight: 1.5 }}>{texte}</p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 20 }}>
          {refus.genre === 'connexion' ? (
            <button type="button" style={boutonPrincipal} onClick={() => { setRefus(null); onOpenAuth(); }}>
              {tr(language, T.seConnecter)}
            </button>
          ) : (
            <a href={PRICING_URL} style={{ ...boutonPrincipal, textDecoration: 'none' }}>{tr(language, T.voirFormules)}</a>
          )}
          <button type="button" style={boutonSecondaire} onClick={() => setRefus(null)}>{tr(language, T.fermer)}</button>
        </div>
      </div>
    </div>
  );
}
