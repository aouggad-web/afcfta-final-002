import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegulatoryQAPanel from './RegulatoryQAPanel';
import { regulatoryApi } from '../../services/api-v2';

vi.mock('../../services/api-v2', () => ({
  regulatoryApi: {
    getQACoverageReport: vi.fn(),
    getQAContradictions: vi.fn(),
    getQAStaleCountries: vi.fn(),
  },
}));

const CLEAN_COVERAGE = {
  total_tracked_countries: 54,
  published_country_count: 6,
  countries: [
    {
      country_iso3: 'CIV',
      as_of: '2026-08-08',
      measure_count: 4,
      mandated_actor_count: 1,
      terminated_actor_count: 1,
    },
    {
      country_iso3: 'COD',
      as_of: '2026-08-08',
      measure_count: 3,
      mandated_actor_count: 1,
      terminated_actor_count: 0,
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  regulatoryApi.getQACoverageReport.mockResolvedValue({ success: true, report: CLEAN_COVERAGE });
  regulatoryApi.getQAContradictions.mockResolvedValue({
    success: true,
    total: 0,
    contradictions: [],
  });
  regulatoryApi.getQAStaleCountries.mockResolvedValue({
    success: true,
    total: 0,
    stale_countries: [],
  });
});

describe('RegulatoryQAPanel', () => {
  it("n'appelle aucun des trois endpoints QA avant expansion du panneau", () => {
    render(<RegulatoryQAPanel language="fr" />);
    expect(regulatoryApi.getQACoverageReport).not.toHaveBeenCalled();
    expect(regulatoryApi.getQAContradictions).not.toHaveBeenCalled();
    expect(regulatoryApi.getQAStaleCountries).not.toHaveBeenCalled();
  });

  it('charge le rapport à l\'ouverture et affiche le résumé de couverture', async () => {
    render(<RegulatoryQAPanel language="fr" />);
    await userEvent.click(screen.getByText('Qualité des données réglementaires'));

    await waitFor(() => expect(regulatoryApi.getQACoverageReport).toHaveBeenCalled());
    expect(await screen.findByText('6 / 54 pays publiés')).toBeInTheDocument();
    expect(screen.getByText('CIV')).toBeInTheDocument();
    expect(screen.getByText('COD')).toBeInTheDocument();
  });

  it('affiche un message positif quand aucune contradiction et aucun pays périmé', async () => {
    render(<RegulatoryQAPanel language="fr" />);
    await userEvent.click(screen.getByText('Qualité des données réglementaires'));

    expect(
      await screen.findByText('Aucune contradiction et aucun dataset périmé détecté.')
    ).toBeInTheDocument();
  });

  it('affiche les contradictions détectées sans les masquer', async () => {
    regulatoryApi.getQAContradictions.mockResolvedValue({
      success: true,
      total: 1,
      contradictions: [
        {
          country_iso3: 'CIV',
          record_id: 'CIV-FAKE',
          measure_verification_status: 'DOCUMENTED',
          source_id: 'CIV-FAKE-SOURCE',
          source_verification_status: 'PENDING_COLLECTION',
        },
      ],
    });

    render(<RegulatoryQAPanel language="fr" />);
    await userEvent.click(screen.getByText('Qualité des données réglementaires'));

    expect(await screen.findByText('1 contradiction détectée')).toBeInTheDocument();
    expect(screen.getByText(/CIV-FAKE/)).toBeInTheDocument();
    expect(
      screen.queryByText('Aucune contradiction et aucun dataset périmé détecté.')
    ).not.toBeInTheDocument();
  });

  it('affiche les pays périmés détectés', async () => {
    regulatoryApi.getQAStaleCountries.mockResolvedValue({
      success: true,
      total: 1,
      stale_countries: [{ country_iso3: 'CIV', as_of: '2020-01-01', reason: 'older_than_threshold' }],
    });

    render(<RegulatoryQAPanel language="fr" />);
    await userEvent.click(screen.getByText('Qualité des données réglementaires'));

    expect(await screen.findByText('1 pays avec dataset périmé')).toBeInTheDocument();
  });

  it("ne plante pas si le rapport de couverture est renvoyé sans champ countries", async () => {
    regulatoryApi.getQACoverageReport.mockResolvedValue({
      success: true,
      report: { total_tracked_countries: 54, published_country_count: 0 },
    });

    render(<RegulatoryQAPanel language="fr" />);
    await userEvent.click(screen.getByText('Qualité des données réglementaires'));

    expect(
      await screen.findByText('Aucune contradiction et aucun dataset périmé détecté.')
    ).toBeInTheDocument();
  });

  it('affiche correctement le pluriel pour plusieurs pays périmés', async () => {
    regulatoryApi.getQAStaleCountries.mockResolvedValue({
      success: true,
      total: 2,
      stale_countries: [
        { country_iso3: 'CIV', as_of: '2020-01-01', reason: 'older_than_threshold' },
        { country_iso3: 'COD', as_of: '2020-01-01', reason: 'older_than_threshold' },
      ],
    });

    render(<RegulatoryQAPanel language="fr" />);
    await userEvent.click(screen.getByText('Qualité des données réglementaires'));

    expect(await screen.findByText('2 pays avec datasets périmés')).toBeInTheDocument();
  });
});
