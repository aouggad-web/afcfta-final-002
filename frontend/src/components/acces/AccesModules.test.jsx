import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import {
  ConnexionRequise,
  EVENEMENT_ACCES,
  InvitationAbonnement,
  ONGLETS_PUBLICS,
  refusAcces,
} from './AccesModules';

const reponse = (status, detail) => ({ response: { status, data: { detail } } });

describe('refusAcces', () => {
  it('reconnaît connexion requise, quota du mois et module réservé aux abonnés', () => {
    expect(refusAcces(reponse(401, { error: 'login_required', module: 'stats' })).genre).toBe('connexion');
    expect(refusAcces(reponse(429, { error: 'quota_exceeded', module: 'logistics', quota: 5 })).genre).toBe('quota');
    expect(refusAcces(reponse(403, { error: 'upgrade_required', module: 'reports' })).genre).toBe('abonnes');
    // Plafond du jour des routes du calculateur (formule Découverte, 17/11/2026).
    expect(refusAcces(reponse(429, { error: 'daily_limit' })).genre).toBe('plafond');
  });

  it("ignore les autres erreurs (jeton CSRF, panne, détail en texte)", () => {
    expect(refusAcces(reponse(403, 'CSRF token missing'))).toBeNull();
    expect(refusAcces(reponse(500, { error: 'boom' }))).toBeNull();
    expect(refusAcces({ message: 'Network Error' })).toBeNull();
  });
});

describe('accès sans compte', () => {
  it('seuls le tableau de bord et le contact sont publics', () => {
    expect(ONGLETS_PUBLICS).toEqual(['dashboard', 'contact']);
  });

  it('propose de créer un compte et de voir les formules', () => {
    const ouvrir = vi.fn();
    render(<ConnexionRequise language="fr" onOpenAuth={ouvrir} />);
    expect(screen.getByText(/2 calculs et de 5 recherches dans chaque module/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Créer un compte / Se connecter' }));
    expect(ouvrir).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('link', { name: 'Voir les formules' }).getAttribute('href')).toBe('/pricing.html');
  });
});

describe('InvitationAbonnement', () => {
  afterEach(() => vi.restoreAllMocks());
  const refuser = (detail) => act(() => {
    window.dispatchEvent(new CustomEvent(EVENEMENT_ACCES, { detail }));
  });

  it("invite à s'abonner quand les 5 recherches du mois sont utilisées", () => {
    render(<InvitationAbonnement language="fr" onOpenAuth={vi.fn()} />);
    expect(screen.queryByRole('dialog')).toBeNull();
    refuser({ genre: 'quota', tier: 'free', module: 'stats', quota: 5, quota_period: 'month' });
    expect(screen.getByRole('dialog').textContent).toContain('vos 5 recherches gratuites du mois');
    expect(screen.getByRole('link', { name: 'Voir les formules' }).getAttribute('href')).toBe('/pricing.html');
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it("n'annonce pas de recherches gratuites à un abonné au quota du jour atteint", () => {
    render(<InvitationAbonnement language="fr" onOpenAuth={vi.fn()} />);
    refuser({ genre: 'quota', tier: 'starter', module: 'reports', quota: 10, quota_period: 'day' });
    const texte = screen.getByRole('dialog').textContent;
    expect(texte).toContain('Quota de votre formule atteint');
    expect(texte).toContain('les 10 utilisations du jour');
    expect(texte).not.toContain('gratuites');
  });

  it("annonce le plafond du jour sans parler de recherches du mois", () => {
    render(<InvitationAbonnement language="fr" onOpenAuth={vi.fn()} />);
    refuser({ genre: 'plafond' });
    const texte = screen.getByRole('dialog').textContent;
    expect(texte).toContain("Limite d'usage du jour atteinte");
    expect(texte).toContain('se renouvelle demain');
    expect(texte).not.toContain('recherches gratuites');
  });

  it('ouvre la connexion pour un visiteur sans compte', () => {
    const ouvrir = vi.fn();
    render(<InvitationAbonnement language="en" onOpenAuth={ouvrir} />);
    refuser({ genre: 'connexion', module: 'production' });
    fireEvent.click(screen.getByRole('button', { name: 'Sign up / Sign in' }));
    expect(ouvrir).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('dit, en arabe, que le module est réservé aux abonnés', () => {
    render(<InvitationAbonnement language="ar" onOpenAuth={vi.fn()} />);
    refuser({ genre: 'abonnes', module: 'reports' });
    expect(screen.getByRole('dialog').textContent).toContain('مخصص للمشتركين');
  });
});
