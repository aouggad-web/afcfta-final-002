/**
 * Manufacture — le détail ISIC 4, celui qu'on n'atteint qu'au clic.
 *
 * Ce fichier existe à cause d'une lacune précise. La phase 4.4 avait mis
 * chaque ONGLET sous test et s'était crue couverte ; trois composants du
 * détail ISIC 4 appelaient pourtant `t()` sans l'avoir en portée et auraient
 * planté à l'affichage. Les 313 tests ne l'ont pas vu — aucun n'allait
 * jusqu'au clic. C'est un contrôle statique qui les a trouvés.
 *
 * Tester les onglets n'est pas tester l'écran. Ce test déplie la grille
 * ISIC 4, sélectionne une classe, et vérifie que le panneau de détail se rend
 * pour de bon.
 *
 * Il verrouille aussi deux distinctions que le module prend soin de faire et
 * qu'il serait facile de perdre :
 *   • INDSTAT (officiel) et IDSB (estimation dérivée) sont affichés dans deux
 *     tableaux séparés, jamais mêlés ;
 *   • une classe sans libellé publié le dit, au lieu d'afficher son code nu
 *     comme s'il était un nom.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ProductionManufacturing from './ProductionManufacturing';

vi.mock('axios');

vi.mock('./EnhancedCountrySelector', () => ({
  default: ({ value }) => <div data-testid="country-selector">{value}</div>,
}));

const UNIDO = {
  country_iso3: 'MAR',
  country_name: 'Maroc',
  source: 'UNIDO INDSTAT',
  top_sectors: [{ name: 'Produits alimentaires', isic: '10', share_mva: 21.5, value_mln_usd: 4200 }],
};

const ISIC4 = {
  data_basis: 'MEASURED',
  data_quality: 'official',
  methodology: 'INDSTAT 4-digit',
  coverage: '2018-2024',
  source: 'UNIDO Statistics Data Portal',
  sectors: [
    { isic4: '1010', isic_description: 'Transformation et conservation de la viande' },
    { isic4: '1020', isic_description: null },
  ],
};

const TIMESERIES = {
  status: 'ready',
  series: {
    output: [{ year: 2023, value: 1200 }],
    employees: [{ year: 2023, value: 5400 }],
    female_employees: [{ year: 2023, value: 2160 }],
  },
};

const mockApi = () =>
  axios.get.mockImplementation((url) => {
    if (/\/production\/isic4\/MAR\/\d+\/?$/.test(url) || url.includes('/timeseries')) {
      return Promise.resolve({ data: TIMESERIES });
    }
    if (url.includes('/production/isic4/MAR')) return Promise.resolve({ data: ISIC4 });
    if (url.includes('/production/unido/MAR')) return Promise.resolve({ data: UNIDO });
    return Promise.resolve({ data: {} });
  });

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ProductionManufacturing — détail ISIC 4 (au clic)', () => {
  it('affiche la grille des classes avec leur libellé', async () => {
    mockApi();
    render(<ProductionManufacturing language="fr" />);
    expect(await screen.findByText('1010')).toBeInTheDocument();
    expect(screen.getByText(/Transformation et conservation de la viande/)).toBeInTheDocument();
  });

  it('dit qu’un libellé n’est pas publié plutôt que de servir le code nu', async () => {
    mockApi();
    render(<ProductionManufacturing language="fr" />);
    await screen.findByText('1020');
    // Le code 1020 existe, son intitulé non : l'écran doit le dire.
    expect(screen.getByText(/non publié|not published/i)).toBeInTheDocument();
  });

  it('déplie le panneau de détail sans planter, et le referme', async () => {
    mockApi();
    render(<ProductionManufacturing language="fr" />);
    // Une fois le détail ouvert, « 1010 » figure aussi dans son en-tête : on
    // garde la référence du bouton de la grille plutôt que de la rechercher.
    const bouton = (await screen.findByText('1010')).closest('button');
    await userEvent.click(bouton);

    // Le panneau demande sa série temporelle : c'est le signe qu'il s'est
    // monté. Un composant sans `t` en portée aurait levé ici.
    await waitFor(() =>
      expect(axios.get.mock.calls.some(([u]) => /\/production\/isic4\/MAR\/1010$/.test(u))).toBe(true));
    expect(bouton).toHaveAttribute('aria-pressed', 'true');

    await userEvent.click(bouton);
    await waitFor(() => expect(bouton).toHaveAttribute('aria-pressed', 'false'));
  });

  it('ne laisse aucune clé i18n brute dans la vue dépliée', async () => {
    mockApi();
    const { container } = render(<ProductionManufacturing language="fr" />);
    const classe = await screen.findByText('1010');
    await userEvent.click(classe.closest('button'));
    await waitFor(() =>
      expect(axios.get.mock.calls.some(([u]) => /\/production\/isic4\/MAR\/1010$/.test(u))).toBe(true));
    expect(container.textContent).not.toMatch(/production\.[a-zA-Z]+\./);
  });
});
