import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegulatoryComplianceTab from './RegulatoryComplianceTab';
import { regulatoryApi } from '../../services/api-v2';

vi.mock('../../services/api-v2', () => ({
  regulatoryApi: {
    getSupportedCountries: vi.fn(),
    getCountryCompliance: vi.fn(),
    getMasterRegistryCountries: vi.fn(),
    getMasterRegistry: vi.fn(),
    getMasterRegistryCountry: vi.fn(),
  },
}));

const CIV_COMPLIANCE = {
  country_iso3: 'CIV',
  as_of: '2026-07-29',
  measure_type: 'import_regulatory_compliance',
  measures: [
    {
      record_id: 'CIV-GUCE-SINGLE-WINDOW',
      measure_name: 'Guichet Unique du Commerce Extérieur (GUCE-CI)',
      measure_category: 'single_window',
      scope: 'Plateforme électronique nationale obligatoire.',
      scope_type: 'GENERAL',
      products: 'Toutes marchandises',
      transport: 'Tous modes',
      transport_modes: ['MULTIMODAL'],
      documents: ['déclaration en douane dématérialisée'],
      authority: 'Guichet Unique du Commerce Extérieur de Côte d\'Ivoire (GUCE-CI)',
      platform: 'https://www.guce.gouv.ci/',
      fees: null,
      fees_status: 'NOT_AVAILABLE',
      legal_reference: 'Décret n°2023-168 du 22 mars 2023',
      verification_status: 'PARTIAL',
      hs_codes_explicit: [],
      mandated_actors: [
        {
          actor_name: 'Webb Fontaine',
          actor_type: 'TECHNICAL_OPERATOR',
          mandating_authority: 'État de Côte d\'Ivoire',
          mandate_status: 'TERMINATED',
          mandate_duration: '2013-07 à 2023-03-22',
          delivered_document: 'NOT_AVAILABLE',
          mandate_evidence: [
            {
              date: '2023-03-22',
              title: "Communiqué du Conseil des Ministres",
              publisher: 'Présidence',
              url: 'https://www.presidence.ci/',
            },
          ],
        },
      ],
    },
    {
      record_id: 'CIV-OIC-BSC',
      measure_name: 'Bordereau de Suivi des Cargaisons (BSC)',
      measure_category: 'cargo_tracking_note',
      scope: 'Document obligatoire de suivi des cargaisons.',
      scope_type: 'GENERAL',
      products: 'Marchandises importées par voie maritime',
      transport: 'Fret maritime exclusivement',
      transport_modes: ['MARITIME'],
      documents: ['connaissement (bill of lading)'],
      authority: 'Office Ivoirien des Chargeurs (OIC)',
      platform: 'https://www.oic.ci/',
      fees: null,
      fees_status: 'NOT_AVAILABLE',
      legal_reference: 'Décret n°95-820 du 29 septembre 1995',
      verification_status: 'PARTIAL',
      hs_codes_explicit: [],
      mandated_actors: [],
    },
  ],
  notes: 'Test notes',
  disclaimer: 'Simulation informative.',
};

beforeEach(() => {
  vi.clearAllMocks();
  regulatoryApi.getSupportedCountries.mockResolvedValue({
    success: true,
    total: 1,
    countries: ['CIV'],
  });
  regulatoryApi.getMasterRegistryCountries.mockResolvedValue({
    success: true,
    total: 54,
    countries: [],
    published_total: 1,
    published_countries: ['CIV'],
  });
  regulatoryApi.getCountryCompliance.mockResolvedValue({
    success: true,
    country_iso3: 'CIV',
    regulatory_compliance: CIV_COMPLIANCE,
  });
});

describe('RegulatoryComplianceTab', () => {
  it('charge la liste des pays disponibles au montage', async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    expect(screen.getByText(/Formalités particulières et prestataires mandatés/)).toBeInTheDocument();
  });

  it('affiche le nombre de pays non encore publiés', async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() =>
      expect(screen.getByText(/53 pays supplémentaires/)).toBeInTheDocument()
    );
  });

  it('charge et affiche les mesures du pays sélectionné', async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());

    await userEvent.click(screen.getByRole('combobox', { name: '' }) || screen.getAllByRole('combobox')[0]);
    const option = await screen.findByText(/Côte d'Ivoire/);
    await userEvent.click(option);

    await waitFor(() => expect(regulatoryApi.getCountryCompliance).toHaveBeenCalledWith('CIV'));
    expect(await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)')).toBeInTheDocument();
    expect(screen.getByText('Bordereau de Suivi des Cargaisons (BSC)')).toBeInTheDocument();
  });

  it("n'affiche jamais un mandat TERMINATED dans la section active", async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getAllByRole('combobox')[0]);
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));

    await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)');
    expect(screen.getByText(/Mandats terminés/)).toBeInTheDocument();
    expect(screen.queryByText('Prestataires mandatés')).not.toBeInTheDocument();
    expect(screen.getByText('Webb Fontaine')).toBeInTheDocument();
  });

  it('filtre les mesures par mode de transport', async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getAllByRole('combobox')[0]);
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));
    await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)');

    const transportSelect = screen.getByRole('combobox', { name: /transport/i });
    await userEvent.click(transportSelect);
    await userEvent.click(await screen.findByRole('option', { name: 'Maritime' }));

    expect(screen.getByText('Bordereau de Suivi des Cargaisons (BSC)')).toBeInTheDocument();
    expect(screen.queryByText('Guichet Unique du Commerce Extérieur (GUCE-CI)')).not.toBeInTheDocument();
  });

  it('filtre par texte de recherche (nom de prestataire)', async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getAllByRole('combobox')[0]);
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));
    await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)');

    const search = screen.getByPlaceholderText(/Mesure, prestataire, document/);
    await userEvent.type(search, 'Webb Fontaine');

    expect(screen.getByText('Guichet Unique du Commerce Extérieur (GUCE-CI)')).toBeInTheDocument();
    expect(screen.queryByText('Bordereau de Suivi des Cargaisons (BSC)')).not.toBeInTheDocument();
  });
});
