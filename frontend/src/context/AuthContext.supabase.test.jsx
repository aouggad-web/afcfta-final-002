/**
 * Liens reçus par e-mail (audit M6) : avec le flux PKCE, ils portent un
 * token_hash vérifié par verifyOtp, pour marcher sur n'importe quel appareil.
 * Le jeton ne doit jamais rester dans la barre d'adresse.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import axios from 'axios';

import { AuthProvider, useAuth } from './AuthContext';

const auth = vi.hoisted(() => ({
  verifyOtp: vi.fn(),
  getSession: vi.fn(),
  onAuthStateChange: vi.fn(),
}));
const toast = vi.hoisted(() => vi.fn());

vi.mock('../lib/supabase', () => ({ supabase: { auth }, TERMS_VERSION: 'test' }));
vi.mock('../hooks/use-toast', () => ({ toast }));
vi.mock('axios');

function Etat() {
  const { recovery, user } = useAuth();
  const qui = user === undefined ? 'chargement' : user ? user.email : 'anonyme';
  return <div data-testid="etat">{`${recovery}|${qui}`}</div>;
}

function rendre() {
  render(
    <AuthProvider>
      <Etat />
    </AuthProvider>
  );
}

beforeEach(() => {
  auth.verifyOtp.mockResolvedValue({ data: {}, error: null });
  auth.getSession.mockResolvedValue({ data: { session: null } });
  auth.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } });
  axios.get.mockRejectedValue(new Error('401'));
});

afterEach(() => {
  vi.clearAllMocks();
  window.history.replaceState(null, '', '/');
});

it('vérifie le lien de mot de passe oublié, efface le jeton et ouvre la saisie du nouveau mot de passe', async () => {
  window.history.replaceState(null, '', '/?onglet=calcul&token_hash=abc123&type=recovery#haut');
  rendre();

  await waitFor(() => expect(screen.getByTestId('etat').textContent).toBe('true|anonyme'));
  expect(auth.verifyOtp).toHaveBeenCalledWith({ token_hash: 'abc123', type: 'recovery' });
  expect(window.location.search).toBe('?onglet=calcul');
  expect(window.location.hash).toBe('#haut');
});

it('signale un lien expiré sans ouvrir la saisie du mot de passe', async () => {
  auth.verifyOtp.mockResolvedValue({ data: {}, error: { code: 'otp_expired', message: 'expired' } });
  window.history.replaceState(null, '', '/?token_hash=vieux&type=email');
  rendre();

  await waitFor(() => expect(toast).toHaveBeenCalled());
  expect(toast.mock.calls[0][0].description).toMatch(/expiré/);
  expect(window.location.search).toBe('');
  await waitFor(() => expect(screen.getByTestId('etat').textContent).toBe('false|anonyme'));
});

it("ignore une adresse sans lien d'e-mail", async () => {
  window.history.replaceState(null, '', '/?type=recovery');
  rendre();

  await waitFor(() => expect(auth.getSession).toHaveBeenCalled());
  expect(auth.verifyOtp).not.toHaveBeenCalled();
  expect(window.location.search).toBe('?type=recovery');
});
