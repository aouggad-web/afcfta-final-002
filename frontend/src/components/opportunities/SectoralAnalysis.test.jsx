/**
 * Analyse sectorielle : un refus d'abonnement du module Opportunités (audit
 * E1) s'annonce comme tel, avec un lien vers les formules, et non comme un
 * service indisponible.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import SectoralAnalysis from './SectoralAnalysis';

vi.mock('axios');

describe('SectoralAnalysis', () => {
  beforeEach(() => vi.resetAllMocks());

  it('annonce que le module est réservé aux abonnements payants', async () => {
    axios.get.mockRejectedValue({ response: { status: 403, data: { detail: {
      error: 'upgrade_required', tier: 'free', module: 'reports',
    } } } });
    render(<SectoralAnalysis hsCode="1801" origin="CIV" destination="NGA" language="fr" />);

    expect(await screen.findByTestId('subscription-notice'))
      .toHaveTextContent('Le module Opportunités est réservé aux abonnements payants.');
    expect(screen.getByRole('link', { name: 'Voir les formules' })).toHaveAttribute('href', '/pricing.html');
  });

  it('garde l’avis de service indisponible pour une vraie panne', async () => {
    axios.get.mockRejectedValue({ response: { status: 500, data: {} } });
    render(<SectoralAnalysis hsCode="1801" origin="CIV" destination="NGA" language="fr" />);

    expect(await screen.findByText(/indisponible/i)).toBeInTheDocument();
    expect(screen.queryByTestId('subscription-notice')).not.toBeInTheDocument();
  });
});
