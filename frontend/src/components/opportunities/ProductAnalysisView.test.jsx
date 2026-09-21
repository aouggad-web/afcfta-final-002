/**
 * Onglet Par produit — recherche par code SH, rendu, et dégradation annoncée.
 *
 * Le deuxième test vérifie une bonne pratique déjà en place, et qu'il s'agit
 * de ne pas perdre : quand l'analyse IA n'est pas disponible, l'écran sert
 * une `note` qui le DIT, au lieu de rendre un produit vide. C'est la
 * différence entre « nous n'avons pas pu analyser » et « il n'y a rien à
 * analyser » — deux phrases que tout le reste du module confond encore.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ProductAnalysisView from './ProductAnalysisView';

vi.mock('axios');

const AI = {
  product: { name: 'Café non torréfié', hs2_code: '09', hs2_name: 'Café, thé', hs4_code: '0901' },
  production_capacities: [{ country: 'Éthiopie', iso3: 'ETH', capacity: 480000, unit: 'tonnes', share: 31 }],
  top_african_importers: [{ country: 'Égypte', iso3: 'EGY', import_value_musd: 42 }],
  top_african_exporters: [{ country: 'Éthiopie', iso3: 'ETH', export_value_musd: 910 }],
  substitution_opportunities: [],
  sources: ['OEC', 'FAOSTAT'],
  note: null,
};

async function chercher(code = '090111') {
  await userEvent.clear(screen.getByTestId('product-hs-input'));
  await userEvent.type(screen.getByTestId('product-hs-input'), code);
  await userEvent.click(screen.getByTestId('product-search-btn'));
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ProductAnalysisView', () => {
  it('interroge l’analyse produit sur le code SH saisi', async () => {
    axios.get.mockImplementation((url) =>
      url.includes('/ai/product/') ? Promise.resolve({ data: AI }) : Promise.resolve({ data: null }),
    );
    render(<ProductAnalysisView language="fr" />);
    await chercher('090111');
    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    const urls = axios.get.mock.calls.map(([u]) => u);
    expect(urls.some((u) => u.includes('/ai/product/090111'))).toBe(true);
    // Le nom du produit paraît à plusieurs endroits de la fiche.
    await waitFor(() => expect(screen.getAllByText(/Café non torréfié/).length).toBeGreaterThan(0));
  });

  it('annonce la dégradation au lieu de rendre un produit vide', async () => {
    // L'analyse IA échoue, la fiche SH répond : l'écran doit le dire.
    axios.get.mockImplementation((url) => {
      if (url.includes('/ai/product/')) return Promise.reject(new Error('IA indisponible'));
      return Promise.resolve({ data: { description_fr: 'Café Arabica', chapter_name_fr: 'Café, thé' } });
    });
    render(<ProductAnalysisView language="fr" />);
    await chercher('090111');
    expect(await screen.findByText(/temporairement indisponible/i)).toBeInTheDocument();
  });

  it('affiche l’échec au lieu de « aucune donnée », qui dit autre chose', async () => {
    // L'échec était consigné au `console.error` et nulle part ailleurs :
    // l'écran retombait sur son état vide, et le lecteur en concluait que le
    // produit n'existe pas. Un jet SYNCHRONE atteint le `catch` externe, le
    // seul qui alimente l'état d'erreur — les deux appels portent chacun le
    // leur.
    axios.get.mockImplementation(() => {
      throw new Error('axios indisponible');
    });
    render(<ProductAnalysisView language="fr" />);
    await chercher('090111');
    const bloc = await screen.findByTestId('product-analysis-error');
    expect(bloc).toHaveTextContent(/n'a pas pu être chargée|could not be loaded/i);
    // L'état vide ne doit pas s'afficher en même temps : il affirmerait le
    // contraire de ce que dit le bloc d'erreur.
    expect(screen.queryByText(/^Aucune donnée/i)).not.toBeInTheDocument();
  });

  it('ne laisse aucune clé i18n brute à l’écran', async () => {
    axios.get.mockImplementation((url) =>
      url.includes('/ai/product/') ? Promise.resolve({ data: AI }) : Promise.resolve({ data: null }),
    );
    const { container } = render(<ProductAnalysisView language="fr" />);
    await chercher('090111');
    await waitFor(() => expect(screen.getAllByText(/Café non torréfié/).length).toBeGreaterThan(0));
    expect(container.textContent).not.toMatch(/opportunities\.[a-zA-Z]+\./);
  });
});
