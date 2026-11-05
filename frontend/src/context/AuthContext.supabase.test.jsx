/**
 * Liens reçus par e-mail (audit M6) : avec le flux PKCE, ils portent un
 * token_hash vérifié par verifyOtp, pour marcher sur n'importe quel appareil.
 * - Le jeton ne doit jamais rester dans la barre d'adresse.
 * - La vérification passe par un client jetable : le client principal ne
 *   reçoit la session qu'après le contrôle de l'adresse.
 * - Ce navigateur utilise le lien sans demander seulement s'il l'attendait,
 *   pour la même adresse et depuis moins de 24 h ; sinon, il faut cliquer sur
 *   « Continuer » (connexion forcée par un lien transmis, scanners).
 */
import React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import axios from 'axios';

import { AuthProvider, useAuth } from './AuthContext';

// Client principal (persistant) et client jetable de vérification.
const auth = vi.hoisted(() => ({
  getSession: vi.fn(),
  onAuthStateChange: vi.fn(),
  setSession: vi.fn(),
  signOut: vi.fn(),
}));
const verif = vi.hoisted(() => ({ verifyOtp: vi.fn(), signOut: vi.fn() }));
const toast = vi.hoisted(() => vi.fn());

vi.mock('../lib/supabase', () => ({
  supabase: { auth },
  creerClientVerification: () => ({ auth: verif }),
  TERMS_VERSION: 'test',
}));
vi.mock('../hooks/use-toast', () => ({ toast }));
vi.mock('axios');

const CLE = 'zlecaf_lien_email_attendu';
const SESSION = { access_token: 'jeton-alice', refresh_token: 'rafraichissement-alice' };
let contexte;
let ecouteur;

function Etat() {
  contexte = useAuth();
  const { recovery, user, lienEnAttente } = contexte;
  const qui = user === undefined ? 'chargement' : user ? user.email : 'anonyme';
  return <div data-testid="etat">{`${recovery}|${qui}|${lienEnAttente ? lienEnAttente.type : '-'}`}</div>;
}

function rendre() {
  render(
    <AuthProvider>
      <Etat />
    </AuthProvider>
  );
}

const etat = () => screen.getByTestId('etat').textContent;
const marquer = (email, t = Date.now()) => localStorage.setItem(CLE, JSON.stringify({ email, t }));
const messages = () => toast.mock.calls.map(([m]) => m.description).join(' | ');

beforeEach(() => {
  verif.verifyOtp.mockResolvedValue({ data: { user: { email: 'alice@example.com' }, session: SESSION }, error: null });
  verif.signOut.mockResolvedValue({ error: null });
  // Le client principal ne connaît une session qu'après setSession.
  let session = null;
  auth.setSession.mockImplementation(async (s) => {
    session = s;
    return { data: { session: s }, error: null };
  });
  auth.getSession.mockImplementation(async () => ({ data: { session } }));
  auth.signOut.mockResolvedValue({ error: null });
  auth.onAuthStateChange.mockImplementation((rappel) => {
    ecouteur = rappel;
    return { data: { subscription: { unsubscribe: vi.fn() } } };
  });
  axios.get.mockRejectedValue(new Error('401'));
  axios.post.mockResolvedValue({ data: { email: 'alice@example.com' } });
});

afterEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  window.history.replaceState(null, '', '/');
});

it('lien attendu : vérifié, session confiée au client principal, saisie du nouveau mot de passe', async () => {
  marquer('alice@example.com');
  window.history.replaceState(null, '', '/?onglet=calcul&token_hash=abc123&type=recovery#haut');
  rendre();

  await waitFor(() => expect(etat()).toBe('true|alice@example.com|-'));
  expect(verif.verifyOtp).toHaveBeenCalledWith({ token_hash: 'abc123', type: 'recovery' });
  expect(auth.setSession).toHaveBeenCalledWith(SESSION);
  // Le site ouvre sa session d'abord ; le client principal ne la reçoit qu'ensuite.
  expect(axios.post.mock.invocationCallOrder[0]).toBeLessThan(auth.setSession.mock.invocationCallOrder[0]);
  expect(window.location.search).toBe('?onglet=calcul');
  expect(window.location.hash).toBe('#haut');
  await waitFor(() => expect(messages()).toMatch(/Connecté en tant que alice@example\.com/));
  expect(localStorage.getItem(CLE)).toBeNull();
});

it("lien non attendu : rien n'est vérifié avant « Continuer », puis connexion annoncée", async () => {
  window.history.replaceState(null, '', '/?token_hash=lien-transmis&type=email');
  rendre();

  await waitFor(() => expect(etat()).toBe('false|anonyme|email'));
  expect(verif.verifyOtp).not.toHaveBeenCalled();
  expect(window.location.search).toBe('');

  await act(async () => {
    await contexte.confirmerLienEmail();
  });
  expect(verif.verifyOtp).toHaveBeenCalledWith({ token_hash: 'lien-transmis', type: 'email' });
  expect(axios.post).toHaveBeenCalledWith(
    expect.stringContaining('/auth/session'),
    {},
    expect.objectContaining({ headers: { Authorization: 'Bearer jeton-alice' } })
  );
  expect(messages()).toMatch(/Connecté en tant que alice@example\.com/);
  expect(etat()).toBe('false|alice@example.com|-');
});

it("lien d'un autre compte : jamais confié au client principal, même si la déconnexion échoue", async () => {
  marquer('victime@example.com');
  verif.verifyOtp.mockImplementation(async () => {
    // Comme auth-js : l'événement part pendant la vérification… mais du
    // client jetable, que l'application n'écoute pas.
    return { data: { user: { email: 'attaquant@example.com' }, session: { access_token: 'jeton-attaquant', refresh_token: 'r' } }, error: null };
  });
  verif.signOut.mockResolvedValue({ error: { message: 'réseau' } });
  window.history.replaceState(null, '', '/?token_hash=autre&type=recovery');
  rendre();

  await waitFor(() => expect(verif.signOut).toHaveBeenCalledWith({ scope: 'local' }));
  await waitFor(() => expect(etat()).toBe('false|anonyme|-'));
  expect(auth.setSession).not.toHaveBeenCalled();
  expect(axios.post).not.toHaveBeenCalled();
  expect(localStorage.getItem(CLE)).toBeNull();
  expect(toast.mock.calls[0][0].variant).toBe('destructive');
  expect(messages()).toMatch(/autre compte.*aucune session n'a été ouverte/);
  // Le lien est consommé : le message ne propose pas de le rouvrir.
  expect(messages()).not.toMatch(/Ouvrez-le/);
});

it('PASSWORD_RECOVERY du client principal ne précède plus le contrôle : aucun formulaire après un refus', async () => {
  marquer('victime@example.com');
  verif.verifyOtp.mockResolvedValue({ data: { user: { email: 'attaquant@example.com' }, session: SESSION }, error: null });
  window.history.replaceState(null, '', '/?token_hash=autre&type=recovery');
  rendre();

  await waitFor(() => expect(verif.signOut).toHaveBeenCalled());
  expect(typeof ecouteur).toBe('function');
  await waitFor(() => expect(etat()).toBe('false|anonyme|-'));
});

it('marqueur de plus de 24 h : traité comme absent, le lien demande confirmation', async () => {
  marquer('alice@example.com', Date.now() - 25 * 3600 * 1000);
  window.history.replaceState(null, '', '/?token_hash=vieux-marqueur&type=email');
  rendre();

  await waitFor(() => expect(etat()).toBe('false|anonyme|email'));
  expect(verif.verifyOtp).not.toHaveBeenCalled();
  expect(localStorage.getItem(CLE)).toBeNull();
});

it('lien expiré : signalé, sans session ni saisie du mot de passe', async () => {
  marquer('alice@example.com');
  verif.verifyOtp.mockResolvedValue({ data: {}, error: { code: 'otp_expired', message: 'expired' } });
  window.history.replaceState(null, '', '/?token_hash=vieux&type=email');
  rendre();

  await waitFor(() => expect(messages()).toMatch(/expiré/));
  await waitFor(() => expect(etat()).toBe('false|anonyme|-'));
  expect(auth.setSession).not.toHaveBeenCalled();
});

it("« Continuer » puis échec de l'ouverture de session du site : session révoquée, client principal intact", async () => {
  axios.post.mockRejectedValue({ response: { data: { detail: "Service d'authentification injoignable, réessayez." } } });
  window.history.replaceState(null, '', '/?token_hash=lien&type=recovery');
  rendre();
  await waitFor(() => expect(etat()).toBe('false|anonyme|recovery'));

  await act(async () => {
    await expect(contexte.confirmerLienEmail()).resolves.toBeNull();
  });
  expect(verif.signOut).toHaveBeenCalledWith({ scope: 'local' });
  expect(auth.setSession).not.toHaveBeenCalled();
  expect(etat()).toBe('false|anonyme|-');
  expect(messages()).toMatch(/injoignable/);
  expect(messages()).not.toMatch(/Connecté en tant que/);
});

it("lien attendu puis échec de l'ouverture de session du site : rien ne reste dans le client principal", async () => {
  marquer('alice@example.com');
  axios.post.mockRejectedValue({ response: { data: { detail: 'Session invalide ou expirée' } } });
  window.history.replaceState(null, '', '/?token_hash=abc&type=email');
  rendre();

  await waitFor(() => expect(verif.signOut).toHaveBeenCalledWith({ scope: 'local' }));
  await waitFor(() => expect(etat()).toBe('false|anonyme|-'));
  expect(auth.setSession).not.toHaveBeenCalled();
  expect(messages()).toMatch(/Session invalide/);
});

it('une coupure brève pendant setSession est rattrapée par une nouvelle tentative', async () => {
  marquer('alice@example.com');
  let session = null;
  auth.setSession
    .mockResolvedValueOnce({ data: {}, error: { message: '{}' } })
    .mockImplementation(async (s) => {
      session = s;
      return { data: { session: s }, error: null };
    });
  auth.getSession.mockImplementation(async () => ({ data: { session } }));
  window.history.replaceState(null, '', '/?token_hash=abc&type=recovery');
  rendre();

  await waitFor(() => expect(etat()).toBe('true|alice@example.com|-'), { timeout: 3000 });
  expect(auth.setSession).toHaveBeenCalledTimes(2);
  expect(messages()).not.toMatch(/impossible/);
});

it("changement d'adresse sans session à ouvrir : confirmation enregistrée, rien d'autre", async () => {
  verif.verifyOtp.mockResolvedValue({ data: { user: null, session: null }, error: null });
  marquer('alice@example.com');
  window.history.replaceState(null, '', '/?token_hash=chg&type=email_change');
  rendre();

  await waitFor(() => expect(messages()).toMatch(/Confirmation enregistrée/));
  expect(axios.post).not.toHaveBeenCalled();
  expect(auth.setSession).not.toHaveBeenCalled();
});

it('erreur sans message (« {} ») : libellé lisible', async () => {
  marquer('alice@example.com');
  verif.verifyOtp.mockResolvedValue({ data: {}, error: { message: '{}' } });
  window.history.replaceState(null, '', '/?token_hash=x&type=email');
  rendre();

  await waitFor(() => expect(messages()).toMatch(/service d'authentification impossible/));
});

it('Site URL terminée par « / » : le lien //?token_hash= ne fait pas planter la page', async () => {
  window.history.replaceState(null, '', `${window.location.origin}//?token_hash=x1&type=email`);
  rendre();

  await waitFor(() => expect(etat()).toBe('false|anonyme|email'));
  expect(window.location.search).toBe('');
});

it("ignore une adresse sans lien d'e-mail", async () => {
  window.history.replaceState(null, '', '/?type=recovery');
  rendre();

  await waitFor(() => expect(auth.getSession).toHaveBeenCalled());
  expect(verif.verifyOtp).not.toHaveBeenCalled();
  expect(window.location.search).toBe('?type=recovery');
});

it('échec définitif de setSession : un seul message, cookie du lien retiré, pas de faux « Connecté »', async () => {
  marquer('alice@example.com');
  auth.setSession.mockResolvedValue({ data: {}, error: { name: 'AuthRetryableFetchError', message: 'Failed to fetch' } });
  window.history.replaceState(null, '', '/?token_hash=abc&type=recovery');
  rendre();

  await waitFor(() => expect(verif.signOut).toHaveBeenCalledWith({ scope: 'local' }), { timeout: 4000 });
  await waitFor(() => expect(etat()).toBe('false|anonyme|-'));
  expect(auth.setSession).toHaveBeenCalledTimes(3);
  expect(axios.post).toHaveBeenCalledWith(expect.stringContaining('/auth/logout'), {}, expect.anything());
  // TOAST_LIMIT = 1 : un second message effacerait le premier.
  expect(toast).toHaveBeenCalledTimes(1);
  expect(toast.mock.calls[0][0].variant).toBe('destructive');
  expect(messages()).toMatch(/la session n'a pas pu s'ouvrir/);
  expect(messages()).not.toMatch(/Connecté en tant que/);
});

it('connecté en A, « Continuer » sur un lien de B puis échec de setSession : retour au compte A', async () => {
  const sessionA = { access_token: 'jeton-a', refresh_token: 'r-a', user: { email: 'a@example.com' } };
  auth.getSession.mockResolvedValue({ data: { session: sessionA } });
  auth.setSession.mockResolvedValue({ data: {}, error: { message: 'session_not_found' } });
  axios.post.mockImplementation(async (url, corps, options) => {
    if (url.endsWith('/auth/logout')) return { data: {} };
    const jeton = options.headers.Authorization;
    return { data: { email: jeton === 'Bearer jeton-a' ? 'a@example.com' : 'alice@example.com' } };
  });
  window.history.replaceState(null, '', '/?token_hash=lien-b&type=email');
  rendre();
  await waitFor(() => expect(etat()).toBe('false|a@example.com|email'));

  await act(async () => {
    await expect(contexte.confirmerLienEmail()).resolves.toBeNull();
  });
  expect(etat()).toBe('false|a@example.com|-');
  expect(verif.signOut).toHaveBeenCalledWith({ scope: 'local' });
  const urls = axios.post.mock.calls.map(([url, , o]) => `${url.split('/api')[1]} ${o.headers?.Authorization || ''}`.trim());
  expect(urls).toEqual(['/auth/session Bearer jeton-a', '/auth/session Bearer jeton-alice', '/auth/logout', '/auth/session Bearer jeton-a']);
  expect(messages()).not.toMatch(/Connecté en tant que/);
}, 8000);

it("échec du site après « Continuer » : le message dit que le lien a servi", async () => {
  axios.post.mockRejectedValue({ response: { data: { detail: 'Session invalide ou expirée' } } });
  window.history.replaceState(null, '', '/?token_hash=lien&type=email');
  rendre();
  await waitFor(() => expect(etat()).toBe('false|anonyme|email'));

  await act(async () => {
    await contexte.confirmerLienEmail();
  });
  expect(messages()).toBe(
    "Ce lien a servi, mais la session n'a pas pu s'ouvrir (Session invalide ou expirée). Connectez-vous avec votre mot de passe, ou demandez un nouveau lien."
  );
  expect(toast).toHaveBeenCalledTimes(1);
});

it('coupure réseau pendant la vérification : message traduit, pas « Failed to fetch »', async () => {
  marquer('alice@example.com');
  verif.verifyOtp.mockResolvedValue({ data: {}, error: { name: 'AuthRetryableFetchError', message: 'Failed to fetch', status: 0 } });
  window.history.replaceState(null, '', '/?token_hash=x&type=email');
  rendre();

  await waitFor(() => expect(messages()).toMatch(/service d'authentification impossible/));
  expect(messages()).not.toMatch(/Failed to fetch/);
});

it('connexion dans un autre onglet : cet onglet affiche le nouveau compte', async () => {
  axios.get.mockResolvedValue({ data: { email: 'a@example.com' } });
  axios.post.mockResolvedValue({ data: { email: 'b@example.com' } });
  rendre();
  await waitFor(() => expect(etat()).toBe('false|a@example.com|-'));

  // Même compte (relecture de la session au retour sur l'onglet) : rien.
  await act(async () => {
    ecouteur('SIGNED_IN', { access_token: 'jeton-a', user: { email: 'A@example.com' } });
  });
  expect(axios.post).not.toHaveBeenCalled();

  // Autre compte, diffusé par l'onglet où la personne s'est connectée.
  await act(async () => {
    ecouteur('SIGNED_IN', { access_token: 'jeton-b', user: { email: 'b@example.com' } });
  });
  await waitFor(() => expect(etat()).toBe('false|b@example.com|-'));
  expect(axios.post).toHaveBeenCalledWith(
    expect.stringContaining('/auth/session'),
    {},
    expect.objectContaining({ headers: { Authorization: 'Bearer jeton-b' } })
  );
});

it('onglet déconnecté : un SIGNED_IN (session restée dans le stockage) ne le reconnecte pas', async () => {
  rendre();
  await waitFor(() => expect(etat()).toBe('false|anonyme|-'));
  await act(async () => {
    ecouteur('SIGNED_IN', { access_token: 'jeton-a', user: { email: 'a@example.com' } });
  });
  expect(axios.post).not.toHaveBeenCalled();
  expect(etat()).toBe('false|anonyme|-');
});

it('SIGNED_IN émis au démarrage, avant que la page ait fixé le compte : ignoré', async () => {
  let finir;
  axios.get.mockReturnValue(new Promise((ok) => { finir = ok; }));
  rendre();
  await act(async () => {
    ecouteur('SIGNED_IN', { access_token: 'jeton-b', user: { email: 'b@example.com' } });
  });
  expect(axios.post).not.toHaveBeenCalled();
  await act(async () => finir({ data: { email: 'a@example.com' } }));
  expect(etat()).toBe('false|a@example.com|-');
});
