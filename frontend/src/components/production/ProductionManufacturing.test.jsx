/**
 * Onglet Manufacture — rendu UNIDO, absence dite, et la course entre pays.
 *
 * Le troisième test est le plus important, et il ne porte pas sur l'affichage
 * mais sur une COURSE : si l'on change de pays pendant qu'une réponse est en
 * vol, la réponse tardive du pays quitté ne doit pas s'afficher sous le nom du
 * pays courant. L'erreur ne ressemble à rien à l'écran — les encadrés sont
 * remplis, les parts de MVA plausibles — et un lecteur attribuerait à un pays
 * la structure industrielle d'un autre. C'est exactement le genre de défaut
 * qu'aucune relecture ne rattrape et qu'un test tient.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import ProductionManufacturing from './ProductionManufacturing';

vi.mock('axios');

vi.mock('./EnhancedCountrySelector', () => ({
  default: ({ value, onChange }) => (
    <button type="button" data-testid="country-selector" onClick={() => onChange('TUN')}>
      {value}
    </button>
  ),
}));

const unido = (iso3, name, sector) => ({
  country_iso3: iso3,
  country_name: name,
  top_sectors: [{ name: sector, share_mva: 21.5, value_mln_usd: 4200 }],
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ProductionManufacturing', () => {
  it('affiche les données UNIDO du pays interrogé', async () => {
    axios.get.mockImplementation((url) =>
      url.includes('/production/unido/MAR')
        ? Promise.resolve({ data: unido('MAR', 'Maroc', 'Textile') })
        : Promise.resolve({ data: {} }),
    );
    render(<ProductionManufacturing language="fr" />);
    // Les secteurs ne vivent que dans les graphes recharts, qui ne se
    // disposent pas sous jsdom : c'est le pays porté par la réponse qui
    // atteste, dans le DOM, de quelle donnée est affichée.
    expect(await screen.findByText('Maroc')).toBeInTheDocument();
    expect(screen.queryByText(/Aucune donnée UNIDO/i)).not.toBeInTheDocument();
  });

  it('dit l’absence de donnée UNIDO au lieu de laisser l’écran muet', async () => {
    axios.get.mockImplementation((url) =>
      url.includes('/production/unido/MAR')
        ? Promise.reject(new Error('réseau'))
        : Promise.resolve({ data: {} }),
    );
    render(<ProductionManufacturing language="fr" />);
    expect(await screen.findByText(/Aucune donnée UNIDO disponible/i)).toBeInTheDocument();
  });

  it('jette la réponse d’un pays qu’on a quitté', async () => {
    let releaseMorocco;
    const moroccoLate = new Promise((resolve) => {
      releaseMorocco = () => resolve({ data: unido('MAR', 'MarocEnRetard', 'Textile') });
    });
    axios.get.mockImplementation((url) => {
      if (url.includes('/production/unido/MAR')) return moroccoLate;
      if (url.includes('/production/unido/TUN')) {
        return Promise.resolve({ data: unido('TUN', 'TunisieCourante', 'Cuir') });
      }
      return Promise.resolve({ data: {} });
    });

    render(<ProductionManufacturing language="fr" />);
    // On quitte le Maroc avant que sa réponse n'arrive, puis on la libère.
    (await screen.findByTestId('country-selector')).click();
    await waitFor(() => expect(screen.getByText('TunisieCourante')).toBeInTheDocument());
    releaseMorocco();

    await waitFor(() => expect(screen.getByText('TunisieCourante')).toBeInTheDocument());
    expect(screen.queryByText('MarocEnRetard')).not.toBeInTheDocument();
  });
});
