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
    // Les graphes recharts ne se disposent pas sous jsdom : c'est le pays
    // porté par la réponse, et la légende HTML du camembert, qui attestent
    // dans le DOM de quelle donnée est affichée.
    expect(await screen.findByText('Maroc')).toBeInTheDocument();
    expect(screen.getByTestId('manufacture-legende-camembert')).toHaveTextContent('Textile21,5 %');
    expect(screen.queryByText(/Aucune donnée UNIDO/i)).not.toBeInTheDocument();
    // Une entrée UNIDO seule ne déclare pas de nature : aucun badge, aucune estimation.
    expect(screen.queryAllByTestId(/^nature-/)).toHaveLength(0);
    expect(screen.queryByTestId('manufacture-estimation')).not.toBeInTheDocument();
    expect(screen.queryByTestId('manufacture-mva-2024')).not.toBeInTheDocument();
    expect(screen.getByText(/proviennent de la base UNIDO INDSTAT4/)).toBeInTheDocument();
  });

  it('dit la nature de chaque chiffre et l’estimation de l’année en cours', async () => {
    // Entrée recalculée sur un office national (forme de l'entrée algérienne).
    const ons = {
      country_iso3: 'DZA',
      country_name: 'Algérie',
      mva_2023_mln_usd: 22610.7,
      mva_2024_mln_usd: 25463.0,
      mva_gdp_percent: 9.12,
      mva_per_capita_usd: 490,
      growth_rate_2023: 2.2,
      growth_rate_2024: 4.2,
      data_year: 2024,
      source_institution: 'ONS Algérie',
      source_dataset: 'Les comptes économiques de 2021 à 2024 (n° 1067)',
      top_sectors: [{ isic: '19', name: 'Raffinage et cokéfaction', share_mva: 53.6, value_mln_usd: 13647.4 }],
      natures: {
        mva_2023_mln_usd: 'officiel',
        mva_2024_mln_usd: 'officiel',
        top_sectors: 'officiel',
        growth_rate_2023: 'calcul_officiel',
        growth_rate_2024: 'calcul_officiel',
        mva_gdp_percent: 'calcul_officiel',
        mva_per_capita_usd: 'calcul_officiel',
      },
      estimation_2025: {
        annee: 2025,
        va_mln_usd: { bas: 25480.9, central: 26144.8, haut: 26952.7 },
        croissance_volume_pct: { bas: 0.1, central: 2.7, haut: 5.9 },
        confiance_part_va_pct: { B: 65.5, C: 34.5 },
        methode: 'Comptes trimestriels 2025 de l’ONS, indicateurs physiques.',
        note: 'Somme des projections par branche.',
        base_prix: 'prix et taux de change de 2024',
      },
    };
    axios.get.mockImplementation((url) =>
      url.includes('/production/unido/MAR') ? Promise.resolve({ data: ons }) : Promise.resolve({ data: {} }),
    );
    render(<ProductionManufacturing language="fr" />);
    expect(await screen.findByText('Algérie')).toBeInTheDocument();
    expect(screen.getAllByTestId('nature-officiel').length).toBeGreaterThan(0);
    expect(screen.getAllByTestId('nature-calcul_officiel')).toHaveLength(3);

    const estimation = screen.getByTestId('manufacture-estimation');
    expect(estimation).toHaveTextContent('Industrie manufacturière 2025');
    expect(estimation).toHaveTextContent('Estimation');
    expect(estimation).toHaveTextContent('Fourchette');
    expect(estimation).toHaveTextContent('+2,7 % [0,1 ; 5,9]');
    expect(screen.getByTestId('manufacture-confiance')).toHaveTextContent('B : 65,5 % · C : 34,5 %');
    expect(screen.getByTestId('manufacture-structure-source')).toHaveTextContent('ONS Algérie');
    // Le dernier total officiel est à l'écran, pas seulement celui de 2023.
    expect(screen.getByTestId('manufacture-mva-2024')).toHaveTextContent('2024 : 25,5 Md $');
    expect(screen.getByTestId('manufacture-croissance-2024')).toHaveTextContent('2024 : +4,2 %');
    // Les tuiles suivent le même format : « 9,12 % », « +2,2 % ».
    expect(screen.getByText('9,12 %')).toBeInTheDocument();
    expect(screen.getByText('+2,2 %')).toBeInTheDocument();
    // La note de bas d'écran ne dit plus « données UNIDO INDSTAT4 ».
    expect(screen.queryByText(/proviennent de la base UNIDO INDSTAT4/)).not.toBeInTheDocument();
    expect(screen.getByText(/comptes nationaux publiés par l'office statistique/)).toBeInTheDocument();
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
