import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import TariffDocumentationPanel from './TariffDocumentationPanel';

describe('TariffDocumentationPanel', () => {
  it('withholds a payable total when the base tariff is blocked', () => {
    render(<TariffDocumentationPanel result={{ generic_legal_calculation: {
      status: 'BLOCKED_BASE_TARIFF',
      base_tariff: { status: 'MISSING' },
      components_missing: ['No dated base tariff'],
      informational_only: true,
      legally_binding: false,
    } }} />);
    expect(screen.getByText('Calcul indisponible — donnée indispensable manquante')).toBeInTheDocument();
    expect(screen.getByText(/aucun total n’est affiché/)).toBeInTheDocument();
    expect(screen.getByText('Simulation informative — non opposable à l’administration douanière.')).toBeInTheDocument();
    expect(screen.queryByText(/Montant/)).not.toBeInTheDocument();
  });

  it('labels an unverified amount as simulation and shows provenance', () => {
    render(<TariffDocumentationPanel result={{ generic_legal_calculation: {
      status: 'UNVERIFIED_SOURCE',
      simulated_total: 12,
      currency_code: 'USD',
      base_tariff: { status: 'UNVERIFIED', source_id: 'TARIFF-1', effective_from: null },
      monetary_components: [{ code: 'CUSTOMS_DUTY', status: 'UNVERIFIED' }],
      informational_only: true,
      legally_binding: false,
      quality_dimensions: { source: 'UNVERIFIED', temporal_validity: 'PARTIAL' },
    } }} />);
    expect(screen.getByText('Revue requise — simulation à confirmer')).toBeInTheDocument();
    expect(screen.getByText(/simulé — à confirmer/)).toBeInTheDocument();
    expect(screen.getByText(/TARIFF-1/)).toBeInTheDocument();
    expect(screen.getByText('Comprendre ce calcul')).toBeInTheDocument();
  });

  it('renders the closed quality vocabulary with human-readable labels', () => {
    render(<TariffDocumentationPanel result={{ generic_legal_calculation: {
      overall_status: 'INFORMATIVE_PARTIAL',
      quality_dimensions: {
        source: 'DOCUMENTED',
        temporal_validity: 'PARTIAL',
        classification: 'DOCUMENTED',
        taxes_and_levies: 'UNVERIFIED',
        preference_and_origin: 'NOT_APPLICABLE',
        formalities: 'NOT_AVAILABLE',
      },
    } }} />);
    expect(screen.getAllByText('Documenté').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Partiel').length).toBeGreaterThan(0);
    expect(screen.getByText('Non vérifié')).toBeInTheDocument();
    expect(screen.getByText('Non applicable')).toBeInTheDocument();
    expect(screen.getAllByText('Non disponible').length).toBeGreaterThan(0);
  });

  it('migrates legacy status labels without exposing the old label', () => {
    render(<TariffDocumentationPanel result={{ generic_legal_calculation: {
      status: 'VERIFIED_COMPLETE',
      verified_total: 10,
      currency_code: 'USD',
    } }} />);
    expect(screen.getByText('Information documentaire complète')).toBeInTheDocument();
    expect(screen.queryByText('VERIFIED_COMPLETE')).not.toBeInTheDocument();
  });
});
