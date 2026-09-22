/**
 * Onglet Mines — la différence entre « pas de production » et « pas de donnée ».
 *
 * L'écran servait le même message aux deux cas, et c'était faux dans les deux
 * sens : les Seychelles n'extraient rien, tandis que d'autres pays figurent au
 * relevé de l'USGS sans que la plateforme ait encore ingéré leurs chiffres.
 * Confondre les deux revient à faire dire à la plateforme qu'un pays minier ne
 * produit pas.
 *
 * Le serveur qualifie désormais l'absence (`coverage.status`, `coverage.note`),
 * et ces tests vérifient que la qualification ARRIVE À L'ÉCRAN — pas seulement
 * qu'elle existe dans la réponse. La distinction entre les deux est la leçon
 * la plus chère de ce chantier.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ProductionMining from './ProductionMining';

vi.mock('axios');

vi.mock('./EnhancedCountrySelector', () => ({
  default: ({ value }) => <div data-testid="country-selector">{value}</div>,
}));

const WITH_PRODUCTION = {
  country_iso3: 'ZAF',
  total_records: 12,
  years_covered: [2023],
  data_by_commodity: {
    Or: [{ year: 2023, value: 99.2, unit: 'tonnes', institution: 'USGS' }],
  },
};

const NO_EXTRACTION = {
  country_iso3: 'SYC',
  total_records: 0,
  data_by_commodity: {},
  coverage: {
    status: 'NOT_LISTED_BY_SOURCES',
    note: "Aucune des sources consultées ne recense de production minière pour ce pays.",
    sources_consulted: ['USGS Mineral Commodity Summaries 2025'],
  },
};

const NOT_INGESTED = {
  country_iso3: 'TCD',
  total_records: 0,
  data_by_commodity: {},
  coverage: {
    status: 'LISTED_BY_USGS_NOT_INGESTED',
    note: "L'USGS recense ce pays, mais ses chiffres ne sont pas encore ingérés.",
    sources_consulted: ['USGS Mineral Commodity Summaries 2025'],
    usgs_source_url: 'https://pubs.usgs.gov/periodicals/mcs2025/',
    usgs_edition: 'MCS 2025',
  },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ProductionMining', () => {
  it('affiche les commodités quand le pays a une production ingérée', async () => {
    axios.get.mockResolvedValue({ data: WITH_PRODUCTION });
    render(<ProductionMining language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    expect(screen.queryByTestId('mining-coverage')).not.toBeInTheDocument();
  });

  it('distingue « rien à extraire » de « rien d’ingéré »', async () => {
    axios.get.mockResolvedValue({ data: NOT_INGESTED });
    const { unmount } = render(<ProductionMining language="fr" />);
    const ingested = await screen.findByTestId('mining-coverage');
    expect(ingested).toHaveTextContent(/pas encore ingérés/i);
    // La source est nommée et liée : le lecteur peut aller vérifier.
    expect(ingested).toHaveTextContent(/USGS/);
    unmount();

    vi.clearAllMocks();
    axios.get.mockResolvedValue({ data: NO_EXTRACTION });
    render(<ProductionMining language="fr" />);
    const absent = await screen.findByTestId('mining-coverage');
    expect(absent).toHaveTextContent(/ne recense de production minière/i);
  });

  it('ne rend pas de graphe vide quand data_by_commodity est un objet vide', async () => {
    // `{}` est vrai en JavaScript : la condition d'affichage portait dessus et
    // ouvrait des graphes sans série. C'est le décompte qui fait foi.
    axios.get.mockResolvedValue({ data: NO_EXTRACTION });
    render(<ProductionMining language="fr" />);
    await screen.findByTestId('mining-coverage');
    expect(screen.queryByText(/📈/)).not.toBeInTheDocument();
  });
});
