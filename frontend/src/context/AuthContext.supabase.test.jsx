/**
 * Liens reçus par e-mail (audit M6) : avec le flux PKCE, ils portent un
 * token_hash vérifié par verifyOtp, pour marcher sur n'importe quel appareil.
 * - Le jeton ne doit jamais rester dans la barre d'adresse.
 * - Ce navigateur l'utilise sans demander seulement s'il l'attendait, pour la
 *   même adresse ; sinon, il faut cliquer sur « Continuer » (connexion forcée
 *   par un lien transmis, scanners de messagerie).
 */
import React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import axios from 'axios';

import { AuthProvider, useAuth } from './AuthContext';

const auth = vi.hoisted(() => ({
  verifyOtp: vi.fn(),
  getSession: vi.fn(),
  onAuthStateChange: vi.fn(),
  signOut: vi.fn(),
}));
const toast = vi.hoisted(() => vi.fn());

vi.mock('../lib/supabase', () => ({ supabase: { auth }, TERMS_VERSION: 'test' }));
vi.mock('../hooks/use-toast', () => ({ toast }));
vi.mock('axios');

const CLE = 'zlecaf_lien_email_attendu';
let contexte;

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

beforeEach(() => {
  auth.verifyOtp.mockResolvedValue({ data: { user: { email: 'alice@example.com' } }, error: null });
  auth.getSession.mockResolvedValue({ data: { session: null } });
  auth.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
  auth.signOut.mockResolvedValue({ error: null });
  axios.get.mockRejectedValue(new Error('401'));
});

afterEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  window.history.replaceState(null, '', '/');
});

it('lien attendu par ce navigateur : vérifié, jeton effacé, saisie du nouveau mot de passe', async () => {
  localStorage.setItem(CLE, 'alice@example.com');
  window.history.replaceState(null, '', '/?onglet=calcul&token_hash=abc123&type=recovery#haut');
  rendre();

  await waitFor(() => expect(etat()).toBe('true|anonyme|-'));
  expect(auth.verifyOtp).toHaveBeenCalledWith({ token_hash: 'abc123', type: 'recovery' });
  expect(window.location.search).toBe('?onglet=calcul');
  expect(window.location.hash).toBe('#haut');
  expect(toast.mock.calls[0][0].description).toMatch(/alice@example\.com/);
  expect(localStorage.getItem(CLE)).toBeNull();
});

it("lien non attendu : rien n'est vérifié avant « Continuer »", async () => {
  window.history.replaceState(null, '', '/?token_hash=lien-transmis&type=email');
  rendre();

  await waitFor(() => expect(etat()).toBe('false|anonyme|email'));
  expect(auth.verifyOtp).not.toHaveBeenCalled();
  expect(window.location.search).toBe('');

  await act(async () => {
    await contexte.confirmerLienEmail();
  });
  expect(auth.verifyOtp).toHaveBeenCalledWith({ token_hash: 'lien-transmis', type: 'email' });
  expect(toast.mock.calls[0][0].description).toMatch(/Connecté en tant que alice@example\.com/);
  expect(etat()).toMatch(/\|-$/);
});

it("lien d'un autre compte que celui attendu : session retirée, pas de saisie de mot de passe", async () => {
  localStorage.setItem(CLE, 'victime@example.com');
  auth.verifyOtp.mockResolvedValue({ data: { user: { email: 'attaquant@example.com' } }, error: null });
  window.history.replaceState(null, '', '/?token_hash=autre&type=recovery');
  rendre();

  await waitFor(() => expect(auth.signOut).toHaveBeenCalledWith({ scope: 'local' }));
  expect(toast.mock.calls[0][0].variant).toBe('destructive');
  expect(toast.mock.calls[0][0].description).toMatch(/autre compte/);
  await waitFor(() => expect(etat()).toBe('false|anonyme|-'));
});

it('lien expiré : signalé, sans saisie du mot de passe', async () => {
  localStorage.setItem(CLE, 'alice@example.com');
  auth.verifyOtp.mockResolvedValue({ data: {}, error: { code: 'otp_expired', message: 'expired' } });
  window.history.replaceState(null, '', '/?token_hash=vieux&type=email');
  rendre();

  await waitFor(() => expect(toast).toHaveBeenCalled());
  expect(toast.mock.calls[0][0].description).toMatch(/expiré/);
  await waitFor(() => expect(etat()).toBe('false|anonyme|-'));
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
  expect(auth.verifyOtp).not.toHaveBeenCalled();
  expect(window.location.search).toBe('?type=recovery');
});
