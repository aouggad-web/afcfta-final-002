/**
 * Tests de la fiche Profils Pays.
 *
 *   • la recherche de pays, en plus du menu déroulant : sans accents ni
 *     casse, par code ISO, au clavier, et un message quand rien ne correspond ;
 *   • le rang africain s'affiche avec son dénominateur et son année, et chaque
 *     tuile porte l'année réelle de sa valeur, jamais une année figée ;
 *   • dette extérieure et réserves de change remplacent le solde budgétaire et
 *     le compte courant.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import CountryProfilesTab from './CountryProfilesTab';

vi.mock('axios');

const COUNTRIES = [
  { code: 'DZA', iso2: 'DZ', name: 'Algérie', region: 'Afrique du Nord' },
  { code: 'CIV', iso2: 'CI', name: "Côte d'Ivoire", region: "Afrique de l'Ouest" },
  { code: 'ETH', iso2: 'ET', name: 'Éthiopie', region: "Afrique de l'Est" },
];

const PROFILE = {
  country_code: 'DZA',
  country_name: 'Algérie',
  region: 'Afrique du Nord',
  population: 47435312,
  population_millions: 47.44,
  gdp_usd: 287031225987,
  gdp_per_capita: 6051,
  inflation_rate: 1.4,
  unemployment_rate: 11.6,
  hdi: 0.763,
  hdi_rank: 96,
  total_debt_pct_gdp: 52.1,
  projections: {
    indicator_years: { gdp: 2025, gdp_per_capita: 2025, population: 2025, inflation: 2025, unemployment: 2025 },
    gdp_growth_latest: 3.8,
    gdp_growth_latest_year: 2025,
    gdp_growth_latest_source: 'Banque mondiale (WDI)',
    debt_year: 2025,
    hdi_year: 2023,
    hdi_source: 'PNUD RDH 2025',
    external_debt: { year: 2024, pct_gni: 2.67, usd: 6898271361 },
    reserves: { year: 2025, usd: 76825229205, import_months: 11.63, import_months_year: 2025 },
  },
  african_rankings: {
    gdp: { rank: 4, total: 52, year: 2025 },
    hdi: { rank: 3, total: 54, year: 2023 },
    external_debt: { rank: 1, total: 47, year: 2024 },
  },
  infrastructure_ranking: {},
  ongoing_projects: [],
};

beforeEach(() => {
  axios.get.mockReset();
  axios.get.mockImplementation((url) =>
    Promise.resolve({ data: url.includes('/country-profile/') ? PROFILE : COUNTRIES })
  );
});

const profileCalls = () =>
  axios.get.mock.calls.map(([url]) => url).filter((url) => url.includes('/country-profile/'));

describe('Profils Pays — recherche de pays', () => {
  it('trouve un pays sans accents et charge son profil au clic', async () => {
    render(<CountryProfilesTab language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());

    await userEvent.type(screen.getByRole('combobox', { name: 'Rechercher un pays' }), 'cote');
    await userEvent.click(await screen.findByRole('option', { name: /Côte d'Ivoire/ }));

    await waitFor(() => expect(profileCalls()[0]).toContain('/country-profile/CIV'));
  });

  it('accepte un code ISO et la touche Entrée', async () => {
    render(<CountryProfilesTab language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());

    await userEvent.type(screen.getByRole('combobox', { name: 'Rechercher un pays' }), 'dza{Enter}');

    await waitFor(() => expect(profileCalls()[0]).toContain('/country-profile/DZA'));
  });

  it('dit quand aucun pays ne correspond', async () => {
    render(<CountryProfilesTab language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());

    await userEvent.type(screen.getByRole('combobox', { name: 'Rechercher un pays' }), 'zzz');

    expect(await screen.findByRole('status')).toHaveTextContent('Aucun pays trouvé');
    expect(profileCalls()).toHaveLength(0);
  });
});

describe('Profils Pays — classement africain et années réelles', () => {
  it('affiche le rang africain avec son dénominateur et les vraies années', async () => {
    render(<CountryProfilesTab language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    await userEvent.type(screen.getByRole('combobox', { name: 'Rechercher un pays' }), 'alg{Enter}');

    expect(await screen.findByLabelText('Rang Afrique 2025 : 4/52')).toHaveTextContent('#4/52');
    expect(screen.getByLabelText('Rang Afrique 2023 : 3/54')).toHaveTextContent('#3/54');
    expect(screen.getByText('Croissance 2025')).toBeInTheDocument();
    expect(screen.getByText('IDH 2023')).toBeInTheDocument();
    expect(screen.queryByText(/Inflation 2024|Chômage 2024|IDH 2024/)).not.toBeInTheDocument();
  });

  it('montre la dette extérieure et les réserves de change, plus le solde ni le compte courant', async () => {
    render(<CountryProfilesTab language="fr" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalled());
    await userEvent.type(screen.getByRole('combobox', { name: 'Rechercher un pays' }), 'alg{Enter}');

    expect(await screen.findByText('Dette extérieure 2024')).toBeInTheDocument();
    expect(screen.getByLabelText('Rang Afrique 2024 : 1/47')).toHaveTextContent('#1/47');
    expect(screen.getByText('Réserves de change 2025')).toBeInTheDocument();
    expect(screen.getByText(/11,6 mois d'importations/)).toBeInTheDocument();
    expect(screen.queryByText(/Solde budgétaire|Compte courant/)).not.toBeInTheDocument();
  });
});
