/**
 * Comparaison multi-pays : quand les calculs sans abonnement sont épuisés
 * (429 de tier « anonymous », audit E1), l'invitation à souscrire s'affiche
 * une seule fois, dans la langue de l'interface, et non à chaque pays.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import MultiCountryComparison from './MultiCountryComparison';

vi.mock('axios');

const LIMITE = { response: { status: 429, data: { detail: {
  error: 'quota_exceeded', tier: 'anonymous', module: 'calculator', quota: 10, quota_period: 'day',
  message: 'Limite de 10 calculs par jour sans abonnement atteinte. Souscrivez un abonnement pour continuer.',
} } } };

describe('MultiCountryComparison', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    axios.get.mockResolvedValue({ data: { pays: {} } });
  });

  it('invite une seule fois à souscrire quand les calculs sans abonnement sont épuisés', async () => {
    axios.post.mockRejectedValue(LIMITE);
    render(<MultiCountryComparison language="en" />);

    await userEvent.click(screen.getByTestId('compare-button'));

    const echecs = await screen.findByTestId('compare-echecs');
    expect(echecs).toHaveTextContent('limit reached');
    expect(screen.getAllByTestId('subscription-notice')).toHaveLength(1);
    expect(screen.getByTestId('subscription-notice'))
      .toHaveTextContent('Limit of 10 calculations per day without a subscription reached. Subscribe to continue.');
    expect(screen.getByRole('link', { name: 'See the plans' })).toHaveAttribute('href', '/pricing.html');
  });

  it("garde le message du serveur pour un pays qui échoue pour une autre raison", async () => {
    axios.post.mockRejectedValue({ response: { status: 503, data: { detail: 'Socle indisponible' } } });
    render(<MultiCountryComparison language="fr" />);

    await userEvent.click(screen.getByTestId('compare-button'));

    expect(await screen.findByTestId('compare-echecs')).toHaveTextContent('Socle indisponible');
    expect(screen.queryByTestId('subscription-notice')).not.toBeInTheDocument();
  });
});
