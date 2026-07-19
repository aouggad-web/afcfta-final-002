import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Réponse minimale mais fidèle à la forme réelle de
// report_engine.get_opportunity_report_ultra_fine (voir backend
// tests/test_report_engine.py::test_opportunity_report_ultra_fine_includes_substitution_feasibility) :
// `substitution_feasibility` est un champ de premier niveau du rapport,
// jusqu'ici jamais rendu par ce composant malgré la donnée déjà calculée.
const reportWithFeasibility = {
  report_type: 'bilateral_product_opportunity',
  report_tier: 'ultra_fine',
  inputs: { destination_iso3: 'NGA' },
  national_need: { available: false, note: 'n/a' },
  substitution_feasibility: {
    hs_code: '8517',
    coefficient: 0.2,
    product_class: 'téléphonie et équipements télécoms',
    barriers: { brand_effect: 'fort', technology_gap: 'fort', after_sales_network: 'moyen', certification: 'moyen' },
    rationale: 'Marché dominé par des marques mondiales...',
    is_estimation: true,
  },
};

vi.mock('axios', () => ({ default: { get: vi.fn() } }));
import axios from 'axios';
import OpportunityReportTab, { BilateralView } from './OpportunityReportTab';

const countries = [
  { iso3: 'CIV', name: "Côte d'Ivoire" },
  { iso3: 'NGA', name: 'Nigeria' },
];

beforeEach(() => axios.get.mockReset());

describe('BilateralView — substitution feasibility card', () => {
  it('renders the substitutability coefficient once the report loads', async () => {
    axios.get.mockResolvedValue({ data: reportWithFeasibility });
    render(<BilateralView countries={countries} fr={true} prefill={null} />);

    await userEvent.click(screen.getByTestId('report-run'));

    await waitFor(() => expect(screen.getByTestId('report-substitution-feasibility')).toBeInTheDocument());
    const card = screen.getByTestId('report-substitution-feasibility');
    expect(card).toHaveTextContent('20%');
    expect(card).toHaveTextContent('téléphonie et équipements télécoms');
  });

  it('renders barrier chips with their labels and intensity', async () => {
    axios.get.mockResolvedValue({ data: reportWithFeasibility });
    render(<BilateralView countries={countries} fr={true} prefill={null} />);
    await userEvent.click(screen.getByTestId('report-run'));

    const card = await screen.findByTestId('report-substitution-feasibility');
    expect(card).toHaveTextContent('Effet marque');
    expect(card).toHaveTextContent('Écart technologique');
    expect(card).toHaveTextContent('Fort');
  });

  it('translates barrier labels in English mode', async () => {
    axios.get.mockResolvedValue({ data: reportWithFeasibility });
    render(<BilateralView countries={countries} fr={false} prefill={null} />);
    await userEvent.click(screen.getByTestId('report-run'));

    const card = await screen.findByTestId('report-substitution-feasibility');
    expect(card).toHaveTextContent('Brand effect');
    expect(card).toHaveTextContent('High');
  });

  it('does not render the card when the report has no substitution_feasibility field', async () => {
    axios.get.mockResolvedValue({
      data: { ...reportWithFeasibility, substitution_feasibility: undefined },
    });
    render(<BilateralView countries={countries} fr={true} prefill={null} />);
    await userEvent.click(screen.getByTestId('report-run'));

    await waitFor(() => expect(screen.getByTestId('report-national-need')).toBeInTheDocument());
    expect(screen.queryByTestId('report-substitution-feasibility')).not.toBeInTheDocument();
  });
});

// Le module Opportunités conserve les scénarios historiques S1–S4 + recherche
// de marchés + rapport bilatéral, et intègre le sous-module Substitution SH6
// comme mode S5 (voir SubstitutionAnalysis.jsx).
describe('OpportunityReportTab — S5 · Substitution mode', () => {
  it('shows all mode buttons including S5 and mounts SubstitutionAnalysis when S5 is selected', async () => {
    // SubstitutionAnalysis charge sa propre liste de pays au montage.
    axios.get.mockResolvedValue({ data: { countries: [] } });
    render(<OpportunityReportTab countries={countries} language="fr" />);

    for (const id of ['market', 'bilateral', 's1', 's2', 's3', 's4', 's5']) {
      expect(screen.getByTestId(`mode-${id}`)).toBeInTheDocument();
    }

    await userEvent.click(screen.getByTestId('mode-s5'));
    await waitFor(() =>
      expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('/substitution/countries'))
    );
  });
});
