import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegulatoryComplianceTab from './RegulatoryComplianceTab';
import { regulatoryApi } from '../../services/api-v2';

const SLOW_TEST_TIMEOUT = 90000;

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
      mandated_actor_status: 'NOT_AVAILABLE',
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
      mandated_actor_status: 'NOT_APPLICABLE',
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

    await userEvent.click(screen.getByRole('combobox', { name: /choisir un pays/i }));
    const option = await screen.findByText(/Côte d'Ivoire/);
    await userEvent.click(option);

    await waitFor(() => expect(regulatoryApi.getCountryCompliance).toHaveBeenCalledWith('CIV'));
    expect(await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)')).toBeInTheDocument();
    expect(screen.getByText('Bordereau de Suivi des Cargaisons (BSC)')).toBeInTheDocument();
  }, SLOW_TEST_TIMEOUT);

  it("n'affiche jamais un mandat TERMINATED dans la section active", async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getByRole('combobox', { name: /choisir un pays/i }));
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));

    await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)');
    expect(screen.getByText(/Mandats non actifs/)).toBeInTheDocument();
    expect(screen.queryByText('Prestataires mandatés')).not.toBeInTheDocument();
    expect(screen.getByText('Webb Fontaine')).toBeInTheDocument();
  }, SLOW_TEST_TIMEOUT);

  it('distingue NOT_AVAILABLE (prestataire non documenté) de NOT_APPLICABLE (aucun prestataire, confirmé)', async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getByRole('combobox', { name: /choisir un pays/i }));
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));

    await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)');
    // GUCE (mandated_actor_status NOT_AVAILABLE) : le mandat Webb Fontaine est
    // terminé, mais l'absence de tout prestataire n'est pas confirmée pour autant.
    expect(
      screen.getByText(/prestataire actuellement actif confirmé par une source/)
    ).toBeInTheDocument();
    // BSC (mandated_actor_status NOT_APPLICABLE) : source confirmant une
    // exploitation directe par l'autorité, jamais présumée par défaut.
    expect(
      screen.getByText(/administration opère cette formalité directement/)
    ).toBeInTheDocument();
  }, SLOW_TEST_TIMEOUT);

  it("un acteur UNVERIFIED ne s'affiche jamais comme prestataire actif (régression revue codex PR #373)", async () => {
    regulatoryApi.getCountryCompliance.mockResolvedValue({
      success: true,
      country_iso3: 'GHA',
      regulatory_compliance: {
        ...CIV_COMPLIANCE,
        measures: [
          {
            ...CIV_COMPLIANCE.measures[0],
            record_id: 'GHA-GSA-EASYPASS',
            measure_name: 'EasyPASS',
            mandated_actor_status: 'NOT_APPLICABLE',
            mandated_actors: [
              {
                actor_name: 'Bureau Veritas',
                actor_type: 'TECHNICAL_OPERATOR',
                mandating_authority: 'Ghana Standards Authority (GSA)',
                mandate_status: 'TERMINATED',
                mandate_duration: 'Juillet 2019 au 30 juin 2026.',
                delivered_document: 'Certificat de Conformité',
                mandate_evidence: [
                  { date: '2026-07-01', title: 'GSA clarify', publisher: 'GSA', url: 'https://gsa.gov.gh/' },
                ],
              },
              {
                actor_name: 'Intertek',
                actor_type: 'TECHNICAL_OPERATOR',
                mandating_authority: 'Ghana Standards Authority (GSA)',
                mandate_status: 'UNVERIFIED',
                mandate_duration: 'Depuis juin 2019 ; statut après juillet 2026 non confirmé.',
                delivered_document: 'Certificat de Conformité, statut non confirmé.',
                mandate_evidence: [
                  { date: '2026-08-08', title: 'Intertek Ghana', publisher: 'Intertek', url: 'https://www.intertek.com/' },
                ],
              },
            ],
          },
        ],
      },
    });

    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getByRole('combobox', { name: /choisir un pays/i }));
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));
    await screen.findByText('EasyPASS');

    // Un acteur UNVERIFIED (Intertek) ne doit jamais apparaître sous la
    // section "Prestataires mandatés" (réservée aux mandats confirmés actifs).
    expect(screen.queryByText('Prestataires mandatés')).not.toBeInTheDocument();
    // Le texte explicatif NOT_APPLICABLE doit être affiché malgré la présence
    // d'un acteur UNVERIFIED dans mandated_actors.
    expect(
      screen.getByText(/administration opère cette formalité directement/)
    ).toBeInTheDocument();
    // Intertek et Bureau Veritas restent visibles, mais dans la section historique.
    expect(screen.getByText(/Mandats non actifs/)).toBeInTheDocument();
    expect(screen.getByText('Intertek')).toBeInTheDocument();
    expect(screen.getByText('Bureau Veritas')).toBeInTheDocument();
  }, SLOW_TEST_TIMEOUT);

  it('filtre les mesures par mode de transport', async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getByRole('combobox', { name: /choisir un pays/i }));
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));
    await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)');

    const transportSelect = screen.getByRole('combobox', { name: /transport/i });
    await userEvent.click(transportSelect);
    await userEvent.click(await screen.findByRole('option', { name: 'Maritime' }));

    expect(screen.getByText('Bordereau de Suivi des Cargaisons (BSC)')).toBeInTheDocument();
    expect(screen.queryByText('Guichet Unique du Commerce Extérieur (GUCE-CI)')).not.toBeInTheDocument();
  }, SLOW_TEST_TIMEOUT);

  it('filtre par texte de recherche (nom de prestataire)', async () => {
    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getByRole('combobox', { name: /choisir un pays/i }));
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));
    await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)');

    const search = screen.getByPlaceholderText(/Mesure, prestataire, document/);
    await userEvent.type(search, 'Webb Fontaine');

    expect(screen.getByText('Guichet Unique du Commerce Extérieur (GUCE-CI)')).toBeInTheDocument();
    expect(screen.queryByText('Bordereau de Suivi des Cargaisons (BSC)')).not.toBeInTheDocument();
  }, SLOW_TEST_TIMEOUT);

  it('ne rend jamais un lien cliquable pour un schéma non http(s) (javascript:/data:)', async () => {
    regulatoryApi.getCountryCompliance.mockResolvedValue({
      success: true,
      country_iso3: 'CIV',
      regulatory_compliance: {
        ...CIV_COMPLIANCE,
        measures: [
          {
            ...CIV_COMPLIANCE.measures[0],
            platform: 'javascript:alert(1)',
            mandated_actors: [
              {
                ...CIV_COMPLIANCE.measures[0].mandated_actors[0],
                mandate_evidence: [
                  {
                    date: '2023-03-22',
                    title: 'Preuve malveillante',
                    publisher: 'Test',
                    url: 'javascript:alert(1)',
                  },
                ],
              },
            ],
          },
        ],
      },
    });

    render(<RegulatoryComplianceTab language="fr" />);
    await waitFor(() => expect(regulatoryApi.getSupportedCountries).toHaveBeenCalled());
    await userEvent.click(screen.getByRole('combobox', { name: /choisir un pays/i }));
    await userEvent.click(await screen.findByText(/Côte d'Ivoire/));
    await screen.findByText('Guichet Unique du Commerce Extérieur (GUCE-CI)');

    // Le texte doit rester visible mais jamais dans un <a href="javascript:...">
    expect(screen.getByText('javascript:alert(1)')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /javascript:alert/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Preuve malveillante/ })).not.toBeInTheDocument();
  }, SLOW_TEST_TIMEOUT);
});
