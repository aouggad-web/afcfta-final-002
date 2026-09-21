/**
 * Onglet Chaînes de valeur — rendu, et le repli qui ne se dit pas.
 *
 * Ce composant vient de perdre 35 libellés en dur au profit d'i18n, dans deux
 * portées distinctes (`HS6SearchResult` et le composant principal) qui
 * nommaient toutes deux leur dictionnaire `txt`. Le premier test s'assure
 * qu'aucune clé brute n'a survécu à cette séparation.
 *
 * Le second RETIENT un défaut plutôt qu'il ne le bénit : quand l'API des
 * chaînes de valeur échoue, l'écran affiche `DEFAULT_VALUE_CHAINS`, un jeu
 * écrit en dur — noms d'étapes, pays, et valeurs chiffrées — sans rien dire
 * de l'échec. Voir la section « données servies sans source » du plan.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ValueChains from './ValueChains';

vi.mock('axios');

const CHAINS = {
  value_chains: [
    {
      id: 'coffee',
      name: 'Café',
      hs_code: '0901',
      stages: [{ name: 'Production', countries: ['ETH'], value: 2.8 }],
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ValueChains', () => {
  it('rend l’écran et ne laisse aucune clé i18n brute', async () => {
    axios.get.mockImplementation((url) =>
      url.includes('/ai/value-chains')
        ? Promise.resolve({ data: CHAINS })
        : Promise.resolve({ data: {} }),
    );
    const { container } = render(<ValueChains language="fr" />);
    await screen.findByTestId('value-chains');
    expect(container.textContent).not.toMatch(/opportunities\.[a-zA-Z]+\./);
  });

  it('DÉFAUT CONNU : sur échec de l’API, sert un jeu écrit en dur sans le dire', async () => {
    // Le jour où l'écran dira « données de démonstration » ou affichera
    // l'échec, CE TEST DOIT ÉCHOUER — c'est le signal de le réécrire.
    axios.get.mockRejectedValue(new Error('réseau'));
    render(<ValueChains language="fr" />);
    await screen.findByTestId('value-chains');
    // Le repli nomme ses chaînes ; plusieurs libellés contiennent « Café ».
    await waitFor(() => expect(screen.getAllByText(/Café/).length).toBeGreaterThan(0));
    expect(screen.queryByText(/indisponible|démonstration|erreur/i)).not.toBeInTheDocument();
  });
});
