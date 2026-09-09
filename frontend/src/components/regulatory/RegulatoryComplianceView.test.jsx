import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import RegulatoryComplianceView, {
  hasActiveMandatedProvider,
  hasUnpricedActiveProviderFees,
} from './RegulatoryComplianceView';

// Fabriques de données minimales reflétant la forme du backend
// (regulatory_compliance_service), injectée par le calculateur via
// result.regulatory_compliance.
function measure(overrides = {}) {
  return {
    record_id: 'REC-1',
    measure_name: 'Contrôle de conformité',
    measure_category: 'conformity',
    scope: 'Plateforme obligatoire.',
    products: 'Toutes marchandises',
    transport: 'Tous modes',
    transport_modes: ['MULTIMODAL'],
    documents: ['UCR'],
    authority: 'Autorité douanière',
    platform: 'https://portail.example.gov/',
    fees: null,
    fees_status: 'NOT_AVAILABLE',
    legal_reference: 'Décret X',
    verification_status: 'PARTIAL',
    mandated_actor_status: 'NOT_AVAILABLE',
    mandated_actors: [],
    ...overrides,
  };
}

function actor(overrides = {}) {
  return {
    actor_name: 'Prestataire SA',
    actor_type: 'TECHNICAL_OPERATOR',
    mandate_status: 'CONFIRMED_UNDATED_END',
    mandating_authority: 'Ministère du Commerce',
    mandate_duration: 'Depuis 2020',
    delivered_document: 'UCR',
    authorized_fees: null,
    authorized_fees_status: 'NOT_AVAILABLE',
    mandate_evidence: [{ date: '2026-08-08', title: 'Source officielle', url: 'https://gra.example.gov/' }],
    ...overrides,
  };
}

function compliance(measures) {
  return { country_iso3: 'XXX', as_of: '2026-08-08', disclaimer: 'Info.', measures };
}

// Les quatre états de frais / prestataire demandés par la recette.
const KNOWN = compliance([
  measure({
    mandated_actor_status: 'DOCUMENTED',
    fees: '0,4% CIF',
    fees_status: 'DOCUMENTED',
    mandated_actors: [actor({ authorized_fees: '0,4% de la valeur CIF', authorized_fees_status: 'DOCUMENTED' })],
  }),
]);
const UNKNOWN = compliance([
  measure({ mandated_actor_status: 'DOCUMENTED', mandated_actors: [actor()] }),
]);
const EXPIRED = compliance([
  measure({
    mandated_actor_status: 'NOT_AVAILABLE',
    mandated_actors: [actor({ mandate_status: 'TERMINATED', authorized_fees: '1% CIF', authorized_fees_status: 'DOCUMENTED' })],
  }),
]);
const NOT_APPLICABLE = compliance([
  measure({ mandated_actor_status: 'NOT_APPLICABLE', mandated_actors: [] }),
]);

describe('RegulatoryComplianceView — affichage', () => {
  it('frais CONNUS : affiche le montant chiffré prouvé + sourcé', () => {
    render(<RegulatoryComplianceView compliance={KNOWN} language="fr" showFilters={false} />);
    expect(screen.getByText(/0,4% de la valeur CIF/)).toBeInTheDocument();
  });

  it('frais INCONNUS : signalés « non fabriqué », jamais un montant ni un zéro', () => {
    render(<RegulatoryComplianceView compliance={UNKNOWN} language="fr" showFilters={false} />);
    expect(screen.getAllByText(/Non disponible \(non fabriqué\)/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText(/\$|USD|GHS|0,00/)).toBeNull();
  });

  it('mandat EXPIRÉ : rendu en historique, jamais comme prestataire actif', () => {
    render(<RegulatoryComplianceView compliance={EXPIRED} language="fr" showFilters={false} />);
    expect(screen.getByText(/Mandats non actifs/i)).toBeInTheDocument();
    // Le libellé « Prestataires mandatés » (section active) ne doit pas apparaître.
    expect(screen.queryByText('Prestataires mandatés')).toBeNull();
  });

  it('NON APPLICABLE : affiche que l’administration opère directement', () => {
    render(<RegulatoryComplianceView compliance={NOT_APPLICABLE} language="fr" showFilters={false} />);
    expect(screen.getByText(/administration opère cette formalité directement/i)).toBeInTheDocument();
  });

  it('affiche un lien/moyen de contact quand disponible (preuve datée)', () => {
    render(<RegulatoryComplianceView compliance={UNKNOWN} language="fr" showFilters={false} />);
    const link = screen.getByRole('link', { name: /Source officielle/i });
    expect(link).toHaveAttribute('href', 'https://gra.example.gov/');
  });

  it('aucune donnée conforme → message NOT_AVAILABLE explicite', () => {
    render(<RegulatoryComplianceView compliance={null} language="fr" />);
    expect(screen.getByText(/NOT_AVAILABLE/i)).toBeInTheDocument();
  });
});

describe('hasActiveMandatedProvider — limite le volet aux pays concernés', () => {
  it('vrai avec un mandat confirmé actif (CONNU/INCONNU)', () => {
    expect(hasActiveMandatedProvider(KNOWN)).toBe(true);
    expect(hasActiveMandatedProvider(UNKNOWN)).toBe(true);
  });
  it('faux si le seul acteur est expiré (mandat non appliqué)', () => {
    expect(hasActiveMandatedProvider(EXPIRED)).toBe(false);
  });
  it('faux si la formalité est opérée directement (NOT_APPLICABLE)', () => {
    expect(hasActiveMandatedProvider(NOT_APPLICABLE)).toBe(false);
  });
  it('faux sur données absentes (fail-closed)', () => {
    expect(hasActiveMandatedProvider(null)).toBe(false);
    expect(hasActiveMandatedProvider({ measures: [] })).toBe(false);
  });
});

describe('hasUnpricedActiveProviderFees — signale l’incomplétude', () => {
  it('vrai : prestataire actif dont les frais sont NOT_AVAILABLE', () => {
    expect(hasUnpricedActiveProviderFees(UNKNOWN)).toBe(true);
  });
  it('faux : prestataire actif dont les frais sont chiffrés', () => {
    expect(hasUnpricedActiveProviderFees(KNOWN)).toBe(false);
  });
  it('faux : frais chiffrés mais mandat expiré (non actif)', () => {
    expect(hasUnpricedActiveProviderFees(EXPIRED)).toBe(false);
  });
});
