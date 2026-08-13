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
});
