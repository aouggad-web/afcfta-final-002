/**
 * Onglet Macro — rendu, séparation pourcentages / USD, état sans donnée.
 *
 * Ce que ces tests verrouillent tient en une phrase : **une part de PIB et un
 * montant en dollars ne se mélangent pas**. L'API les sert dans deux champs
 * distincts (`data_by_sector` en % du PIB, `data_by_sector_usd` en USD
 * courants) précisément pour qu'aucun graphe ne les empile. Un jour où le
 * front relirait les deux depuis la même clé, la courbe serait muette sur son
 * unité et le lecteur y verrait une progression là où il y a un changement
 * d'échelle.
 *
 * Le troisième cas — l'appel qui échoue — vérifie que l'écran le DIT. Un
 * module de données qui tombe en silence sur un tableau vide se lit comme
 * « ce pays ne produit rien ».
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ProductionMacro from './ProductionMacro';

vi.mock('axios');

vi.mock('./EnhancedCountrySelector', () => ({
  default: ({ value }) => <div data-testid="country-selector">{value}</div>,
}));

const PAYLOAD = {
  country_iso3: 'DZA',
  total_records: 42,
  years_covered: [2022, 2023],
  data_by_sector: {
    Agriculture: [
      { year: 2022, value: 12.4, unit: '% of GDP', institution: 'World Bank' },
      { year: 2023, value: 12.9, unit: '% of GDP', institution: 'World Bank' },
    ],
  },
  data_by_sector_usd: {
    Agriculture: [
      { year: 2022, value: 24_500_000_000, unit: 'USD', institution: 'World Bank' },
      { year: 2023, value: 26_100_000_000, unit: 'USD', institution: 'World Bank' },
    ],
  },
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ProductionMacro', () => {
  it('affiche les montants absolus dans un bloc séparé des pourcentages', async () => {
    axios.get.mockResolvedValue({ data: PAYLOAD });
    render(<ProductionMacro language="fr" />);

    const usd = await screen.findByTestId('macro-usd');
    expect(usd).toBeInTheDocument();
    // Le bloc USD porte son propre avertissement d'unité : sans lui, un
    // lecteur rapporterait ces montants aux pourcentages du graphe voisin.
    expect(usd).toHaveTextContent(/dollars courants/i);
    expect(usd).toHaveTextContent(/Agriculture/);
  });

  it('interroge l’endpoint macro du pays sélectionné', async () => {
    axios.get.mockResolvedValue({ data: PAYLOAD });
    render(<ProductionMacro language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    expect(axios.get.mock.calls[0][0]).toMatch(/\/production\/macro\/DZA$/);
  });

  it('dit qu’il n’a pas de donnée quand l’appel échoue, au lieu de se taire', async () => {
    axios.get.mockRejectedValue(new Error('réseau'));
    render(<ProductionMacro language="fr" />);
    expect(await screen.findByText(/Aucune donnée disponible/i)).toBeInTheDocument();
    expect(screen.queryByTestId('macro-usd')).not.toBeInTheDocument();
  });

  it('ne montre pas le bloc USD quand la source ne publie que des parts de PIB', async () => {
    const percentOnly = { ...PAYLOAD, data_by_sector_usd: {} };
    axios.get.mockResolvedValue({ data: percentOnly });
    render(<ProductionMacro language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    expect(screen.queryByTestId('macro-usd')).not.toBeInTheDocument();
  });
});
