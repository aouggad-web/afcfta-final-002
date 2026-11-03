/**
 * Module Outils, tarifs NPF : aucun téléchargement, quelle que soit la
 * formule (décision du responsable produit, 03/11/2026). L'écran n'affiche
 * que le nombre de positions tarifaires nationales de chaque pays.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import axios from 'axios';

import TariffDownloads from './TariffDownloads';

vi.mock('axios');

const LISTE = {
  count: 1,
  countries: [{ code: 'COG', name: 'Congo', positions: 5876, collecte: '2026', devise: 'XAF' }],
  regions: { cemac: { name: 'CEMAC + RDC + STP', countries: ['COG'] } },
};

describe('TariffDownloads', () => {
  it('affiche le nombre de positions nationales, sans aucun téléchargement', async () => {
    axios.get.mockResolvedValue({ data: LISTE });
    const { container } = render(<TariffDownloads language="fr" />);

    expect(await screen.findByTestId('positions-nationales')).toHaveTextContent(
      'positions tarifaires nationales'
    );
    expect(screen.getByTestId('positions-nationales').textContent).toMatch(/5\s876/);
    expect(container.querySelectorAll('button, a[download]')).toHaveLength(0);
    expect(container.textContent).not.toMatch(/CSV|JSON|Télécharger/);
  });
});
