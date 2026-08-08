import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import RegulatoryComplianceView from './RegulatoryComplianceView';

// Jeu de données minimal reflétant la forme renvoyée par le backend
// (regulatory_compliance_service) et injectée par le calculateur via
// result.regulatory_compliance.
const COMPLIANCE = {
  country_iso3: 'GHA',
  as_of: '2026-08-08',
  disclaimer: 'Simulation informative — non opposable.',
  measures: [
    {
      record_id: 'GHA-GRA-ICUMS',
      measure_name: 'ICUMS',
      measure_category: 'single_window',
      scope: 'Plateforme électronique intégrée de dédouanement.',
      products: 'Toutes marchandises',
      transport: 'Tous modes',
      transport_modes: ['MULTIMODAL'],
      documents: ['UCR'],
      authority: 'Ghana Revenue Authority (GRA)',
      platform: 'https://gra.gov.gh/customs/icums/',
      fees: null,
      fees_status: 'NOT_AVAILABLE',
      legal_reference: 'Contrat 2018',
      verification_status: 'PARTIAL',
      mandated_actor_status: 'DOCUMENTED',
      mandated_actors: [
        {
          actor_name: 'Ghana Link Network Services Ltd (GLNS)',
          actor_type: 'TECHNICAL_OPERATOR',
          mandate_status: 'CONFIRMED_UNDATED_END',
          mandating_authority: "Ministère du Commerce et de l'Industrie",
          mandate_duration: 'Depuis le 1er juin 2020',
          delivered_document: 'UCR',
          authorized_fees: null,
          authorized_fees_status: 'NOT_AVAILABLE',
          mandate_evidence: [],
        },
      ],
    },
  ],
};

describe('RegulatoryComplianceView', () => {
  it("affiche les frais non chiffrés comme « non fabriqué » (fail-closed) et jamais un montant inventé", () => {
    render(<RegulatoryComplianceView compliance={COMPLIANCE} language="fr" showFilters={false} />);
    // Les frais réglementaires ET les frais autorisés du prestataire sont
    // NOT_AVAILABLE → rendus comme non disponibles, sans valeur numérique.
    expect(screen.getAllByText(/Non disponible \(non fabriqué\)/i).length).toBeGreaterThanOrEqual(2);
    // Aucun symbole monétaire ni montant fabriqué ne doit apparaître.
    expect(screen.queryByText(/\$|USD|GHS/)).toBeNull();
  });

  it('affiche le montant chiffré quand il est prouvé et sourcé', () => {
    const withFees = {
      ...COMPLIANCE,
      measures: [
        {
          ...COMPLIANCE.measures[0],
          fees: '0,4% CIF',
          fees_status: 'DOCUMENTED',
          mandated_actors: [
            {
              ...COMPLIANCE.measures[0].mandated_actors[0],
              authorized_fees: '0,4% de la valeur CIF',
              authorized_fees_status: 'DOCUMENTED',
            },
          ],
        },
      ],
    };
    render(<RegulatoryComplianceView compliance={withFees} language="fr" showFilters={false} />);
    expect(screen.getByText(/0,4% de la valeur CIF/)).toBeInTheDocument();
  });

  it('rend un message NOT_AVAILABLE explicite quand aucune donnée conforme n\'existe', () => {
    render(<RegulatoryComplianceView compliance={null} language="fr" />);
    expect(screen.getByText(/NOT_AVAILABLE/i)).toBeInTheDocument();
  });
});
