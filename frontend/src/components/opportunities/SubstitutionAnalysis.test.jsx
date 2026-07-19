import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { OpportunityCard } from './SubstitutionAnalysis';

// Reproduit exactement la forme renvoyée par
// real_substitution_service.find_import_substitution_opportunities (voie OEC
// réelle ET repli statique attachent toutes deux ces champs — voir
// backend/services/real_substitution_service.py lignes ~767 et ~850).
const importOpportunity = (overrides = {}) => ({
  imported_product: {
    hs_code: '8517',
    name: 'Téléphones et équipements de télécommunication',
    import_value: 1_500_000_000,
    current_source: 'Chine',
  },
  african_suppliers: [
    { country_iso3: 'EGY', country_name: 'Égypte', export_value: 200_000_000, share_potential: 13.3 },
  ],
  substitution_potential: 300_000_000,
  substitution_feasibility: {
    hs_code: '8517',
    coefficient: 0.2,
    product_class: 'téléphonie et équipements télécoms',
    barriers: { brand_effect: 'fort', technology_gap: 'fort', after_sales_network: 'moyen', certification: 'moyen' },
    rationale: 'Marché dominé par des marques mondiales...',
    is_estimation: true,
  },
  addressable_value: 300_000_000,
  binding_constraint: 'substituabilité',
  difficulty: 'Difficile',
  ...overrides,
});

describe('OpportunityCard — difficulty badge (regression: FR backend value vs EN key comparison)', () => {
  it.each([
    ['Facile', 'Facile'],
    ['Modéré', 'Modéré'],
    ['Difficile', 'Difficile'],
    ['Très difficile', 'Très difficile'],
  ])('renders the actual backend difficulty "%s" as-is in French (not a mismatched fallback)', (backendValue, expected) => {
    render(
      <OpportunityCard
        opportunity={importOpportunity({ difficulty: backendValue })}
        type="import"
        language="fr"
      />
    );
    // Le bug corrigé : avant, toute valeur ('Facile' comme 'Très difficile')
    // s'affichait "Difficile" faute de correspondance avec les clés 'easy'/
    // 'moderate'/'difficult'. On vérifie maintenant l'exactitude par valeur.
    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  it('translates the difficulty label in English mode', () => {
    render(
      <OpportunityCard
        opportunity={importOpportunity({ difficulty: 'Facile' })}
        type="import"
        language="en"
      />
    );
    expect(screen.getByText('Easy')).toBeInTheDocument();
    expect(screen.queryByText('Facile')).not.toBeInTheDocument();
  });
});

describe('OpportunityCard — substitution feasibility block', () => {
  it('shows the substitutability coefficient as a percentage', () => {
    render(<OpportunityCard opportunity={importOpportunity()} type="import" language="fr" />);
    expect(screen.getByTestId('substitution-feasibility')).toHaveTextContent('20%');
  });

  it('shows the binding-constraint explanation matching binding_constraint', () => {
    render(
      <OpportunityCard
        opportunity={importOpportunity({ binding_constraint: 'substituabilité' })}
        type="import"
        language="fr"
      />
    );
    expect(screen.getByTestId('substitution-feasibility')).toHaveTextContent(/substituabilité/i);
  });

  it('shows the capacity-bound explanation when binding_constraint is capacité africaine', () => {
    render(
      <OpportunityCard
        opportunity={importOpportunity({ binding_constraint: 'capacité africaine' })}
        type="import"
        language="fr"
      />
    );
    expect(screen.getByTestId('substitution-feasibility')).toHaveTextContent(/capacité africaine/i);
  });

  it('renders one barrier chip per barrier entry with its intensity', () => {
    render(<OpportunityCard opportunity={importOpportunity()} type="import" language="fr" />);
    const block = screen.getByTestId('substitution-feasibility');
    expect(block).toHaveTextContent('Effet marque');
    expect(block).toHaveTextContent('Écart technologique');
    expect(block).toHaveTextContent('Réseau après-vente');
    expect(block).toHaveTextContent('Certification');
  });

  it('renders nothing when substitution_feasibility is absent (no crash on legacy/partial data)', () => {
    render(
      <OpportunityCard
        opportunity={importOpportunity({ substitution_feasibility: undefined, barriers: undefined })}
        type="import"
        language="fr"
      />
    );
    expect(screen.queryByTestId('substitution-feasibility')).not.toBeInTheDocument();
  });

  it('is shown on export opportunities too (same bounding applies to capturing African markets)', () => {
    render(
      <OpportunityCard
        opportunity={{
          export_product: { hs_code: '87', name: 'Véhicules' },
          potential_markets: [{ country_name: 'Nigeria', market_size: 50_000_000, capture_potential: 0.45 }],
          total_market_potential: 22_500_000,
          substitution_feasibility: {
            hs_code: '87',
            coefficient: 0.45,
            product_class: 'véhicules et matériel de transport terrestre',
            barriers: { brand_effect: 'fort', technology_gap: 'moyen', after_sales_network: 'fort', certification: 'moyen' },
            rationale: 'Effet marque réel...',
            is_estimation: true,
          },
          binding_constraint: 'capacité exportateur',
          competitiveness: 'competitive',
        }}
        type="export"
        language="fr"
      />
    );
    const block = screen.getByTestId('substitution-feasibility');
    expect(block).toHaveTextContent('45%');
    expect(block).toHaveTextContent(/capacité d'export du pays/i);
  });

  it('shows exporter average price and per-market price positioning on export cards', () => {
    render(
      <OpportunityCard
        opportunity={{
          export_product: { hs_code: '870321', name: 'Voitures de tourisme à moteur à piston' },
          exporter_avg_price_usd_per_tonne: 10_000,
          market_match_level: 'hs6',
          potential_markets: [
            {
              country_name: 'Nigeria',
              market_size: 2_000_000_000,
              addressable_market_size: 1_000_000_000,
              capture_potential: 0.5,
              price_positioning: {
                exporter_avg_price_usd_per_tonne: 10_000,
                market_avg_price_usd_per_tonne: 16_000,
                price_ratio: 0.63,
                price_delta_pct: -37.5,
                positioning: 'compétitif',
              },
            },
          ],
          total_market_potential: 1_000_000_000,
          substitution_feasibility: {
            hs_code: '8703', coefficient: 0.5, product_class: 'véhicules de tourisme',
            barriers: null, rationale: '...', is_estimation: true,
          },
          binding_constraint: 'substituabilité',
        }}
        type="export"
        language="fr"
      />
    );
    expect(screen.getByTestId('exporter-avg-price')).toHaveTextContent('$10,000/t');
    const pp = screen.getByTestId('price-positioning');
    expect(pp).toHaveTextContent('$16,000/t');
    expect(pp).toHaveTextContent('-37.5%');
    expect(pp).toHaveTextContent('Compétitif');
    // Exact HS6 product match: no HS4-level caveat.
    expect(screen.queryByTestId('market-match-caveat')).not.toBeInTheDocument();
  });

  it('shows the HS4-level caveat when markets are hs4 fallback, hides prices when absent', () => {
    render(
      <OpportunityCard
        opportunity={{
          export_product: { hs_code: '870321', name: 'Voitures de tourisme à moteur à piston' },
          exporter_avg_price_usd_per_tonne: null,
          market_match_level: 'hs4',
          potential_markets: [
            { country_name: 'Égypte', market_size: 8_000_000_000, capture_potential: 0.5, price_positioning: null },
          ],
          total_market_potential: 4_000_000_000,
        }}
        type="export"
        language="fr"
      />
    );
    expect(screen.getByTestId('market-match-caveat')).toHaveTextContent(/niveau SH4/i);
    expect(screen.queryByTestId('exporter-avg-price')).not.toBeInTheDocument();
    expect(screen.queryByTestId('price-positioning')).not.toBeInTheDocument();
  });

  it('renders nothing on an export opportunity lacking the feasibility field (legacy data)', () => {
    render(
      <OpportunityCard
        opportunity={{
          export_product: { hs_code: '1801', name: 'Cacao en fèves' },
          potential_markets: [{ country_name: 'Nigeria', market_size: 50_000_000, capture_potential: 0.4 }],
          total_market_potential: 20_000_000,
          competitiveness: 'competitive',
        }}
        type="export"
        language="fr"
      />
    );
    expect(screen.queryByTestId('substitution-feasibility')).not.toBeInTheDocument();
  });
});

// Regression coverage for the Statistiques -> Opportunités handoff (see
// OpportunitiesTab.jsx / CountryHS6History.jsx): selecting a country + HS6
// code elsewhere in the app deposits `initialCountry` in sessionStorage and
// should land directly on a pre-filled, already-analyzed import view — no
// manual re-selection or extra click on "Analyser" required.
describe('SubstitutionAnalysis — initialCountry handoff', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('pre-selects the import tab and auto-triggers analysis for the handoff country', async () => {
    vi.doMock('axios', () => {
      const get = vi.fn((url) => {
        if (url.includes('/substitution/countries')) {
          return Promise.resolve({
            data: { countries: [{ iso3: 'DZA', name: 'Algérie', has_trade_data: true }] },
          });
        }
        if (url.includes('/substitution/opportunities/import/DZA')) {
          return Promise.resolve({
            data: {
              opportunities: [],
              summary: { total_opportunities: 0, total_substitutable_value: 0, top_sectors: [] },
              is_estimation: false,
              data_source: 'OEC',
            },
          });
        }
        if (url.includes('/substitution/opportunities/export/DZA')) {
          return Promise.resolve({
            data: {
              opportunities: [],
              summary: { total_opportunities: 0, total_market_potential: 0 },
              is_estimation: false,
              data_source: 'OEC',
            },
          });
        }
        return Promise.reject(new Error(`Unexpected URL: ${url}`));
      });
      return { default: { get } };
    });

    const axios = (await import('axios')).default;
    const { default: SubstitutionAnalysis } = await import('./SubstitutionAnalysis');

    render(
      <SubstitutionAnalysis language="fr" initialCountry={{ iso3: 'DZA', k: 1 }} />
    );

    // The handoff never touches activeTab='export': import stays selected.
    await waitFor(() => {
      expect(screen.getByTestId('import-tab')).toHaveAttribute('data-state', 'active');
    });
    expect(screen.getByTestId('export-tab')).toHaveAttribute('data-state', 'inactive');

    // analyzeCountry() must fire on its own — no click on "Analyser" needed.
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/substitution/opportunities/import/DZA')
      );
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/substitution/opportunities/export/DZA')
      );
    });
  });
});
