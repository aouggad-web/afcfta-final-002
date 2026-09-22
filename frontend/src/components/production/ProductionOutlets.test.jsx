/**
 * Tests du chaînage Production → Débouchés.
 *
 * Le module Production savait dire ce qu'un pays produit, le module
 * Opportunités où vendre un produit, et rien ne reliait les deux. Ce que ces
 * tests verrouillent, c'est le pont lui-même :
 *
 *   • la production réelle du pays s'affiche avec ses codes SH ;
 *   • un clic dépose l'intention « market » — perspective EXPORTATEUR — et
 *     non l'intention historique « s3 », qui répond à la question inverse ;
 *   • le rang continental n'est jamais montré sans son dénominateur, et les
 *     réserves du serveur sont rendues telles quelles. C'est le garde-fou qui
 *     empêche de relire « 1ᵉʳ producteur » là où trois pays sont couverts.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ProductionOutlets, { handoffToMarkets } from './ProductionOutlets';

vi.mock('axios');

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    // Restitue la clé et ses variables : on teste le câblage, pas la
    // traduction — et une clé absente se voit immédiatement.
    t: (key, vars) => (vars ? `${key}:${JSON.stringify(vars)}` : key),
  }),
}));

vi.mock('./EnhancedCountrySelector', () => ({
  default: ({ value }) => <div data-testid="country-selector">{value}</div>,
}));

const PROFILE = {
  available: true,
  country_iso3: 'KEN',
  total_tracked: 82,
  products: [
    {
      hs_code: '0902',
      commodity: 'Tea',
      dataset: 'agri',
      measure: 'Production',
      unit: 'tonnes',
      institution: 'FAO',
      year: 2024,
      value: 2687200,
      rank: 1,
      total_countries: 17,
      share_pct: 69.4,
      coverage_caveat: null,
      commodity_caveat: null,
    },
    {
      hs_code: '070970',
      commodity: 'Spinach',
      dataset: 'agri',
      measure: 'Production',
      unit: 'tonnes',
      institution: 'FAO',
      year: 2024,
      value: 242720,
      rank: 1,
      total_countries: 2,
      share_pct: 86.2,
      coverage_caveat: 'Couverture FAO limitée à 2 pays africains — pas un leadership réel.',
      commodity_caveat: null,
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
});

describe('ProductionOutlets', () => {
  it("liste la production du pays avec ses codes SH", async () => {
    axios.get.mockResolvedValue({ data: PROFILE });
    render(<ProductionOutlets language="fr" />);

    await waitFor(() => expect(screen.getByTestId('outlets-table')).toBeInTheDocument());
    expect(screen.getByText('Tea')).toBeInTheDocument();
    expect(screen.getByText('0902')).toBeInTheDocument();
    expect(screen.getByText('070970')).toBeInTheDocument();
  });

  it("montre toujours le rang AVEC son dénominateur", async () => {
    axios.get.mockResolvedValue({ data: PROFILE });
    render(<ProductionOutlets language="fr" />);

    await waitFor(() => expect(screen.getByTestId('outlets-table')).toBeInTheDocument());
    // « 1ᵉʳ » seul ne se juge pas ; « 1ᵉʳ sur 17 » se juge.
    expect(screen.getByText(/rankOf:.*"rank":1.*"total":17/)).toBeInTheDocument();
    expect(screen.getByText(/rankOf:.*"rank":1.*"total":2/)).toBeInTheDocument();
  });

  it("rend la réserve du serveur au lieu de la taire", async () => {
    axios.get.mockResolvedValue({ data: PROFILE });
    render(<ProductionOutlets language="fr" />);

    await waitFor(() => expect(screen.getByTestId('outlets-table')).toBeInTheDocument());
    const caveats = screen.getAllByTestId('outlets-caveat');
    expect(caveats).toHaveLength(1);
    expect(caveats[0]).toHaveTextContent('pas un leadership réel');
  });

  it("dépose l'intention EXPORTATEUR au clic, et navigue", async () => {
    axios.get.mockResolvedValue({ data: PROFILE });
    const onGoto = vi.fn();
    window.addEventListener('zlecaf:goto-tab', onGoto);
    render(<ProductionOutlets language="fr" />);

    await waitFor(() => expect(screen.getByTestId('outlets-table')).toBeInTheDocument());
    await userEvent.click(screen.getByTestId('outlets-go-0902'));

    const handoff = JSON.parse(sessionStorage.getItem('zlecaf_opportunites_handoff'));
    expect(handoff.hsCode).toBe('0902');
    expect(handoff.country).toBe('KEN');
    // Le point décisif : « market » (où vendre) et non « s3 » (quel besoin),
    // qui enverrait le lecteur vers l'écran répondant à la question inverse.
    expect(handoff.mode).toBe('market');
    expect(onGoto).toHaveBeenCalled();
    window.removeEventListener('zlecaf:goto-tab', onGoto);
  });

  it("annonce l'absence plutôt que d'afficher un tableau vide", async () => {
    axios.get.mockResolvedValue({ data: { available: true, products: [] } });
    render(<ProductionOutlets language="fr" />);

    await waitFor(() =>
      expect(screen.getByText('production.outlets.empty')).toBeInTheDocument(),
    );
    expect(screen.queryByTestId('outlets-table')).not.toBeInTheDocument();
  });

  it("annonce l'échec réseau au lieu de rester muet", async () => {
    axios.get.mockRejectedValue(new Error('réseau'));
    render(<ProductionOutlets language="fr" />);

    await waitFor(() =>
      expect(screen.getByText('production.outlets.error')).toBeInTheDocument(),
    );
  });
});

describe('handoffToMarkets', () => {
  it('refuse un code SH vide plutôt que de naviguer pour rien', () => {
    const onGoto = vi.fn();
    window.addEventListener('zlecaf:goto-tab', onGoto);
    expect(handoffToMarkets({ iso3: 'KEN', hsCode: '' })).toBe(false);
    expect(onGoto).not.toHaveBeenCalled();
    expect(sessionStorage.getItem('zlecaf_opportunites_handoff')).toBeNull();
    window.removeEventListener('zlecaf:goto-tab', onGoto);
  });

  it('porte un jeton k, pour que deux clics sur le même produit relancent', () => {
    handoffToMarkets({ iso3: 'KEN', hsCode: '0902' });
    const first = JSON.parse(sessionStorage.getItem('zlecaf_opportunites_handoff'));
    expect(typeof first.k).toBe('number');
  });
});
