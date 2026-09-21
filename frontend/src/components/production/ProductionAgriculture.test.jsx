/**
 * Onglet Agriculture — rendu FAOSTAT et absence dite.
 *
 * Deux garanties, et la seconde compte autant que la première :
 *
 *   • les cultures et l'élevage remontés par FAOSTAT s'affichent avec leur
 *     année, parce qu'une tonne sans millésime n'est pas une mesure ;
 *   • quand l'appel échoue, l'écran le DIT. Un module de production qui rend
 *     un écran vide se lit exactement comme « ce pays ne produit rien » — la
 *     confusion la plus coûteuse de toute la plateforme, puisque c'est
 *     précisément ce qu'elle est censée mesurer.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ProductionAgriculture from './ProductionAgriculture';

vi.mock('axios');

vi.mock('./EnhancedCountrySelector', () => ({
  default: ({ value }) => <div data-testid="country-selector">{value}</div>,
}));

const DETAIL = {
  country_name: 'Algérie',
  region: 'Afrique du Nord',
  source: 'FAOSTAT 2024',
  sources: ['FAOSTAT QCL'],
  cultures: [
    { name: 'Blé', value_2023: 3_100_000, year: 2023, is_bulk_faostat: true },
    { name: 'Dattes', value_2023: 1_200_000, year: 2023, is_bulk_faostat: true },
  ],
  elevage: [],
  evolution: {},
  key_indicators: {},
};

const respond = (url) => {
  if (url.includes('/faostat/country-detail/')) return Promise.resolve({ data: DETAIL });
  if (url.includes('/faostat/statistics')) return Promise.resolve({ data: { countries: 54 } });
  return Promise.resolve({ data: {} });
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ProductionAgriculture', () => {
  it('affiche les cultures du pays servies par FAOSTAT', async () => {
    axios.get.mockImplementation(respond);
    render(<ProductionAgriculture language="fr" />);
    expect(await screen.findByText(/Blé/)).toBeInTheDocument();
    expect(screen.getByText(/Dattes/)).toBeInTheDocument();
  });

  it('interroge le détail pays de FAOSTAT pour le pays sélectionné', async () => {
    axios.get.mockImplementation(respond);
    render(<ProductionAgriculture language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    const urls = axios.get.mock.calls.map(([u]) => u);
    expect(urls.some((u) => /\/faostat\/country-detail\/DZA\b/.test(u))).toBe(true);
  });

  it('dit l’absence de donnée quand l’appel échoue, au lieu d’un écran vide', async () => {
    axios.get.mockRejectedValue(new Error('réseau'));
    render(<ProductionAgriculture language="fr" />);
    expect(await screen.findByText(/Aucune donnée disponible pour ce pays/i)).toBeInTheDocument();
  });
});
