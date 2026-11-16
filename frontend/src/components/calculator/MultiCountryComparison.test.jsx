/**
 * Comparaison multi-pays : quand les calculs gratuits du mois sont épuisés
 * (429 d'un compte sans abonnement, 2 calculs par mois), l'invitation à souscrire s'affiche
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
  error: 'quota_exceeded', tier: 'free', module: 'calculator', quota: 2, quota_period: 'month',
  message: 'Quota de la formule free atteint.',
} } } };

describe('MultiCountryComparison', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    axios.get.mockResolvedValue({ data: { pays: {} } });
  });

  it('invite une seule fois à souscrire quand les calculs gratuits du mois sont épuisés', async () => {
    axios.post.mockRejectedValue(LIMITE);
    render(<MultiCountryComparison language="en" />);

    await userEvent.click(screen.getByTestId('compare-button'));

    const echecs = await screen.findByTestId('compare-echecs');
    expect(echecs).toHaveTextContent('limit reached');
    expect(screen.getAllByTestId('subscription-notice')).toHaveLength(1);
    expect(screen.getByTestId('subscription-notice'))
      .toHaveTextContent('Your 2 free calculations for this month are used up. Subscribe to continue.');
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
