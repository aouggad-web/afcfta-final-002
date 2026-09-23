import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('axios', () => ({ default: { get: vi.fn() } }));
import axios from 'axios';
import NationalIndustryView, { montant } from './NationalIndustryView';

// Formes fidèles aux réponses de backend/services/industrie_nationale_service.py
const estimation = (bas, central, haut, conf) => ({
  nature: 'estimation',
  is_estimation: true,
  confiance: conf,
  croissance_volume_pct: { bas, central, haut },
  indicateurs: ['ONS, comptes trimestriels : T1 2025 +5,9 %'],
  sources: ['ons_comptes'],
});
const industrie = {
  available: true,
  titre: "Industrie manufacturière de l'Algérie par branche, 2016-2025",
  methode_2025: 'Croissance en volume 2025 par branche…',
  limites: ['2016-2019 : seul le total est publié.'],
  sources: { ons_comptes: { titre: 'ONS, Les comptes économiques de 2021 à 2024, n° 1067 (août 2025)', url: 'https://www.ons.dz' } },
  total: {
    2024: { nature: 'officiel', va_musd: 25463.0, production_brute_musd: 54244.1 },
    2025: { nature: 'estimation', croissance_volume_pct: { bas: 0.1, central: 2.7, haut: 5.9 } },
  },
  branches: [
    {
      code: '19', libelle: 'Raffinage et cokéfaction', citi_rev4: ['19'],
      annees: {
        2024: { nature: 'officiel', va_musd: 13647.4, part_privee_va_pct: 2.3, croissance_volume_pct: 3.0 },
        2025: estimation(-2.5, -1.0, 2.0, 'B'),
      },
    },
    {
      code: '13-14', libelle: 'Textile, habillement et fourrures', citi_rev4: ['13', '14'],
      annees: {
        2024: { nature: 'officiel', va_musd: 1260.9, part_privee_va_pct: 90.4, croissance_volume_pct: 10.3 },
        2025: estimation(4.0, 7.3, 10.0, 'B'),
      },
    },
  ],
};
const exportations = {
  available: true, region: 'monde', source: 'CEPII BACI via l\'API OEC', limites: ['La Libye après 2019 manque.'],
  produits: [
    { hs6: '310210', libelle: 'Urée, même en solution aqueuse', exportations_2024_usd: 1024456424, part_afrique_2024_pct: 0.7, demande_monde_2024_usd: 20542650098, part_monde_2024_pct: 5.0 },
  ],
};
const caroube = {
  available: true, hs6: '121292', libelle: 'Caroubes fraîches, réfrigérées, congelées ou séchées, même pulvérisées',
  libelle_source: 'SEN — Tarif extérieur commun CEDEAO (Sénégal)',
  exportations: [{ annee: 2023, valeur_usd: 8370953, tonnes: 2453.9 }, { annee: 2024, valeur_usd: 2213800, tonnes: 2243 }],
  destinations_2024: [{ iso3: 'MAR', pays: 'Maroc', valeur_usd: 822357, tonnes: 349.7 }],
  marches_absents: {
    critere: { importations_2024_min_usd: 1000000, part_pays_max_pct: 1.0, note: 'Un filtre sur des flux réels, pas un score.' },
    monde: [{ iso3: 'ESP', pays: 'Spain', importations_2024_usd: 3846644, importations_2019_usd: 2612415, evolution_2019_2024_pct: 47.2, part_pays_pct: 0 }],
    afrique: [{ iso3: 'EGY', pays: 'Égypte', importations_2024_usd: 1137212, importations_2019_usd: 2007901, evolution_2019_2024_pct: -43.4, part_pays_pct: 0 }],
  },
  source: 'CEPII BACI via l\'API OEC', limites: [],
};

beforeEach(() => {
  axios.get.mockReset();
  axios.get.mockImplementation((url) => {
    if (url.includes('/exportations/121292')) return Promise.resolve({ data: caroube });
    if (url.includes('/exportations')) return Promise.resolve({ data: exportations });
    return Promise.resolve({ data: industrie });
  });
});

describe('montant — format des montants', () => {
  it('écrit « 13,6 Md $ » en français et « $13.6B » en anglais', () => {
    expect(montant(13647.4e6, true)).toBe('13,6\u00A0Md\u00A0$');
    expect(montant(13647.4e6, false)).toBe('$13.6B');
    expect(montant(822357, true)).toBe('822,4\u00A0k\u00A0$');
    expect(montant(null, true)).toBe('—');
  });
});

describe('NationalIndustryView', () => {
  it('distingue les chiffres officiels 2024 des estimations 2025', async () => {
    render(<NationalIndustryView fr={true} />);
    const bloc = await screen.findByTestId('dza-industrie');
    const raff = within(bloc).getByTestId('branche-19');
    // toHaveTextContent ramène l'espace insécable à une espace simple
    expect(raff).toHaveTextContent('13,6 Md $');
    expect(within(raff).getByTestId('nature-estimation')).toHaveTextContent('Estimation · confiance B');
    expect(within(bloc).getAllByTestId('nature-officiel').length).toBeGreaterThan(0);
    // la fourchette 2025 est toujours affichée à côté de la valeur centrale
    expect(raff).toHaveTextContent('-2,5 %');
    expect(raff).toHaveTextContent('+2 %');
  });

  it('ouvre la fiche caroube et montre les marchés où l’Algérie est absente', async () => {
    render(<NationalIndustryView fr={true} />);
    await screen.findByTestId('dza-exportations');
    await userEvent.click(screen.getByTestId('raccourci-caroube'));
    const fiche = await screen.findByTestId('fiche-produit');
    expect(fiche).toHaveTextContent('Caroubes');
    // nom du pays traduit par le navigateur à partir du code ISO (Spain → Espagne)
    expect(within(fiche).getByTestId('absents-monde')).toHaveTextContent('Espagne');
    expect(within(fiche).getByTestId('absents-afrique')).toHaveTextContent('Égypte');
    expect(fiche).toHaveTextContent('pas un score');
  });

  it('écarte les hydrocarbures par défaut, et les réintègre sur demande', async () => {
    render(<NationalIndustryView fr={true} />);
    await screen.findByTestId('dza-exportations');
    expect(axios.get.mock.calls.some(([u]) => u.includes('hors_hydrocarbures=true'))).toBe(true);
    await userEvent.click(screen.getByTestId('hors-hydrocarbures'));
    await waitFor(() =>
      expect(axios.get.mock.calls.some(([u]) => u.includes('hors_hydrocarbures=false'))).toBe(true)
    );
  });

  it('demande le tri africain quand on choisit « Afrique »', async () => {
    render(<NationalIndustryView fr={true} />);
    await screen.findByTestId('dza-exportations');
    await userEvent.click(screen.getByTestId('region-afrique'));
    await waitFor(() =>
      expect(axios.get.mock.calls.some(([u]) => u.includes('region=afrique'))).toBe(true)
    );
  });
});
