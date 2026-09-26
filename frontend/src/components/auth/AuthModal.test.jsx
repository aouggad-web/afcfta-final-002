import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AuthModal from './AuthModal';
import { useAuth } from '../../context/AuthContext';

vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
  formatApiErrorDetail: (detail, fallback) => detail || fallback,
}));

vi.mock('../../hooks/use-toast', () => ({
  toast: vi.fn(),
}));

describe('AuthModal', () => {
  const login = vi.fn();
  const register = vi.fn();

  beforeEach(() => {
    login.mockReset();
    register.mockReset();
    useAuth.mockReturnValue({ login, register });
  });

  it('refuses registration when password confirmation differs', async () => {
    const user = userEvent.setup();
    render(
      <AuthModal
        open
        onClose={vi.fn()}
        onAuthenticated={vi.fn()}
        language="fr"
      />
    );

    await user.click(screen.getByRole('tab', { name: 'Inscription' }));
    await user.type(screen.getByTestId('register-name-input'), 'Alice Test');
    await user.type(screen.getByTestId('register-email-input'), 'alice@example.com');
    await user.type(screen.getByTestId('register-password-input'), 'SecurePass123');
    await user.type(screen.getByTestId('register-confirm-password-input'), 'DifferentPass123');
    await user.click(screen.getByTestId('register-submit-btn'));

    expect(screen.getByRole('alert')).toHaveTextContent('Les mots de passe ne correspondent pas.');
    expect(register).not.toHaveBeenCalled();
  });

  it('normalizes identity fields and completes registration', async () => {
    register.mockResolvedValue({ id: 'user-1' });
    const onAuthenticated = vi.fn();
    const user = userEvent.setup();
    render(
      <AuthModal
        open
        onClose={vi.fn()}
        onAuthenticated={onAuthenticated}
        language="fr"
      />
    );

    await user.click(screen.getByRole('tab', { name: 'Inscription' }));
    await user.type(screen.getByTestId('register-name-input'), '  Alice   Test  ');
    await user.type(screen.getByTestId('register-email-input'), 'ALICE@EXAMPLE.COM');
    await user.type(screen.getByTestId('register-password-input'), 'SecurePass123');
    await user.type(screen.getByTestId('register-confirm-password-input'), 'SecurePass123');
    await user.click(screen.getByTestId('register-accept-terms'));
    await user.click(screen.getByTestId('register-submit-btn'));

    expect(register).toHaveBeenCalledWith('Alice Test', 'alice@example.com', 'SecurePass123');
    expect(onAuthenticated).toHaveBeenCalledTimes(1);
  });

  it('shows the API error inside the dialog when login fails', async () => {
    login.mockRejectedValue({ response: { data: { detail: 'Email ou mot de passe incorrect' } } });
    const user = userEvent.setup();
    render(
      <AuthModal
        open
        onClose={vi.fn()}
        onAuthenticated={vi.fn()}
        language="fr"
      />
    );

    await user.type(screen.getByTestId('login-email-input'), 'nobody@example.com');
    await user.type(screen.getByTestId('login-password-input'), 'WrongPassword');
    await user.click(screen.getByTestId('login-submit-btn'));

    expect(await screen.findByRole('alert')).toHaveTextContent('Email ou mot de passe incorrect');
  });

  const fillRegistration = async (user) => {
    await user.click(screen.getByRole('tab', { name: 'Inscription' }));
    await user.type(screen.getByTestId('register-name-input'), 'Alice Test');
    await user.type(screen.getByTestId('register-email-input'), 'alice@example.com');
    await user.type(screen.getByTestId('register-password-input'), 'SecurePass123');
    await user.type(screen.getByTestId('register-confirm-password-input'), 'SecurePass123');
  };

  it('requires accepting the terms before registering', async () => {
    const user = userEvent.setup();
    render(<AuthModal open onClose={vi.fn()} onAuthenticated={vi.fn()} language="fr" />);
    await fillRegistration(user);
    await user.click(screen.getByTestId('register-submit-btn'));

    expect(screen.getByRole('alert')).toHaveTextContent('Veuillez accepter les conditions');
    expect(register).not.toHaveBeenCalled();
  });

  it('asks to confirm the email when Supabase requires it', async () => {
    register.mockResolvedValue({ needsConfirmation: true });
    const onAuthenticated = vi.fn();
    const user = userEvent.setup();
    render(<AuthModal open onClose={vi.fn()} onAuthenticated={onAuthenticated} language="fr" />);
    await fillRegistration(user);
    await user.click(screen.getByTestId('register-accept-terms'));
    await user.click(screen.getByTestId('register-submit-btn'));

    expect(await screen.findByTestId('auth-info')).toHaveTextContent('Cliquez sur le lien');
    expect(onAuthenticated).not.toHaveBeenCalled();
  });

  it('sends a password reset link', async () => {
    const requestPasswordReset = vi.fn().mockResolvedValue();
    useAuth.mockReturnValue({ login, register, supabaseEnabled: true, requestPasswordReset });
    const user = userEvent.setup();
    render(<AuthModal open onClose={vi.fn()} language="fr" />);

    await user.type(screen.getByTestId('login-email-input'), 'alice@example.com');
    await user.click(screen.getByTestId('forgot-password-link'));
    await user.click(screen.getByRole('button', { name: 'Recevoir un lien de réinitialisation' }));

    expect(requestPasswordReset).toHaveBeenCalledWith('alice@example.com');
    expect(await screen.findByTestId('auth-info')).toHaveTextContent('email de réinitialisation');
  });

  it('deletes the account only after explicit confirmation', async () => {
    const deleteAccount = vi.fn().mockResolvedValue();
    useAuth.mockReturnValue({
      user: { name: 'Alice', email: 'alice@example.com' },
      login,
      register,
      deleteAccount,
    });
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<AuthModal open onClose={onClose} language="fr" />);

    await user.click(screen.getByTestId('delete-account-btn'));
    expect(deleteAccount).not.toHaveBeenCalled();
    await user.click(screen.getByTestId('confirm-delete-btn'));

    expect(deleteAccount).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalled();
  });

  it('shows the Stripe subscription and opens the billing portal', async () => {
    const openBillingPortal = vi.fn().mockResolvedValue();
    useAuth.mockReturnValue({
      user: { name: 'Alice', email: 'alice@example.com' },
      getSubscription: vi.fn().mockResolvedValue({
        effective_tier: 'pro',
        cycle: 'monthly',
        status: 'active',
        payment_provider: 'stripe',
        current_period_end: '2026-10-25T00:00:00Z',
        cancel_at_period_end: false,
        can_manage_billing: true,
      }),
      openBillingPortal,
    });
    const user = userEvent.setup();
    render(<AuthModal open onClose={vi.fn()} language="fr" />);

    const block = await screen.findByTestId('subscription-block');
    expect(block).toHaveTextContent('Formule Pro · mensuel');
    expect(block).toHaveTextContent('Prochain renouvellement le 25/10/2026');
    await user.click(screen.getByTestId('manage-billing-btn'));
    expect(openBillingPortal).toHaveBeenCalledTimes(1);
  });

  it('offers renewal instead of the Stripe portal for Chargily payments', async () => {
    useAuth.mockReturnValue({
      user: { name: 'Karim', email: 'karim@example.com' },
      getSubscription: vi.fn().mockResolvedValue({
        effective_tier: 'starter',
        cycle: 'monthly',
        status: 'active',
        payment_provider: 'chargily',
        current_period_end: '2026-10-25T00:00:00Z',
        can_manage_billing: false,
      }),
    });
    render(<AuthModal open onClose={vi.fn()} language="fr" />);

    const block = await screen.findByTestId('subscription-block');
    expect(block).toHaveTextContent('sans renouvellement automatique');
    expect(screen.queryByTestId('manage-billing-btn')).toBeNull();
    expect(screen.getByRole('button', { name: 'Renouveler' })).toBeInTheDocument();
  });
});

