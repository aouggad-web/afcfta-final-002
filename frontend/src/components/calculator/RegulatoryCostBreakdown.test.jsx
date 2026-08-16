import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import RegulatoryCostBreakdown from './RegulatoryCostBreakdown';

const CUSTOMS = {
  value: 100000,
  destination_country: 'CMR',
  normal_tariff_amount: 10000,
  normal_vat_amount: 2000,
  normal_statistical_fee: 100,
  normal_community_levy: 0,
  normal_ecowas_levy: 0,
  normal_other_taxes_total: 100,
  normal_total_cost: 12200,
};

function costBlock(lineItems, overrides = {}) {
  return {
    ...CUSTOMS,
    regulatory_cost: {
      line_items: lineItems,
      complete: overrides.complete ?? false,
      has_unpriced_fees: overrides.has_unpriced_fees ?? false,
      regulatory_cost_total: overrides.regulatory_cost_total ?? null,
      regulatory_cost_currency: overrides.regulatory_cost_currency ?? null,
    },
  };
}

const CALCULABLE_ITEM = {
  scope: 'provider',
  measure_name: 'Contrôle de conformité',
  actor_name: 'COTECNA',
  mandating_authority: 'Ministère du Commerce',
  side: 'import',
  stage: 'export',
  payer: 'EXPORTER',
  fee_status: 'CALCULABLE',
  calculated_amount: 500,
  currency: 'USD',
  contact: 'https://cotecna.example/',
};

const UNPRICED_ITEM = {
  scope: 'provider',
  measure_name: 'Inspection avant embarquement',
  actor_name: 'SGS',
  mandating_authority: 'Douanes',
  side: 'export',
  stage: 'export',
  payer: 'EXPORTER',
  fee_status: 'FEE_EXISTS_AMOUNT_NOT_AVAILABLE',
  calculated_amount: null,
  currency: null,
  contact: null,
};

describe('RegulatoryCostBreakdown', () => {
  it('ne rend rien sans ventilation de frais', () => {
    const { container } = render(<RegulatoryCostBreakdown result={CUSTOMS} language="fr" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('affiche un montant calculé et le total réglementaire quand complet', () => {
    const result = costBlock([CALCULABLE_ITEM], {
      complete: true,
      regulatory_cost_total: 500,
      regulatory_cost_currency: 'USD',
    });
    render(<RegulatoryCostBreakdown result={result} language="fr" />);
    expect(screen.getAllByText(/500 USD/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Coût réglementaire total/)).toBeInTheDocument();
    expect(screen.getByText(/Complet/)).toBeInTheDocument();
    expect(screen.getByText(/Droits de douane/)).toBeInTheDocument();
    // Volet EXPORT (le frais est payé par l'exportateur) + tag prestataire privé.
    expect(screen.getByText(/Formalités à l'export/)).toBeInTheDocument();
    expect(screen.getByText(/prestataire privé/)).toBeInTheDocument();
  });

  it('affiche un encadré explicatif import vs export', () => {
    const result = costBlock([CALCULABLE_ITEM], { complete: true });
    render(<RegulatoryCostBreakdown result={result} language="fr" />);
    expect(screen.getByText(/Import vs export : comment lire ces frais/)).toBeInTheDocument();
    expect(screen.getByText(/à l'IMPORT \(aval\)/i)).toBeInTheDocument();
  });

  it('sépare les volets export (amont) et import (aval)', () => {
    const importItem = {
      ...CALCULABLE_ITEM,
      measure_name: 'Redevance OCC',
      stage: 'import',
      payer: 'IMPORTER',
      collector_type: 'STATE_BODY',
      scope: 'formality',
    };
    const result = costBlock([CALCULABLE_ITEM, importItem], { complete: true });
    render(<RegulatoryCostBreakdown result={result} language="fr" />);
    expect(screen.getByText(/Formalités à l'export/)).toBeInTheDocument();
    expect(screen.getByText(/Formalités à l'import/)).toBeInTheDocument();
    expect(screen.getByText(/Redevance OCC/)).toBeInTheDocument();
    // Le perçu public (OCC) porte le tag « perçu public ».
    expect(screen.getByText(/perçu public/)).toBeInTheDocument();
  });

  it('signale « montant à confirmer » et le message quand un frais existe mais est inconnu', () => {
    const result = costBlock([UNPRICED_ITEM], { has_unpriced_fees: true, complete: false });
    render(<RegulatoryCostBreakdown result={result} language="fr" />);
    expect(screen.getAllByText(/montant à confirmer/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/prendre attache avec le prestataire/i)).toBeInTheDocument();
    expect(screen.getByText(/Partiel/)).toBeInTheDocument();
    // Jamais un zéro fabriqué pour le frais inconnu.
    expect(screen.queryByText(/0 USD|0,00/)).toBeNull();
  });

  it('affiche une formalité sans prestataire confirmé, jamais masquée', () => {
    const UNCONFIRMED_ITEM = {
      scope: 'formality',
      measure_name: 'Guichet Unique du Commerce Extérieur (GUCE-CI)',
      actor_name: null,
      mandating_authority: "Ministère du Commerce (CIV)",
      side: 'import',
      stage: 'import',
      fee_status: 'FEE_EXISTS_AMOUNT_NOT_AVAILABLE',
      provider_status: 'UNCONFIRMED',
      calculated_amount: null,
      currency: null,
      contact: null,
    };
    const result = costBlock([UNCONFIRMED_ITEM], { has_unpriced_fees: true, complete: false });
    render(<RegulatoryCostBreakdown result={result} language="fr" />);
    expect(screen.getByText(/Guichet Unique du Commerce Extérieur/)).toBeInTheDocument();
    expect(screen.getByText(/prestataire non confirmé/i)).toBeInTheDocument();
    expect(screen.getByText(/l'absence de prestataire n'est pas démontrée/i)).toBeInTheDocument();
    // Jamais un zéro fabriqué pour ce frais non trouvé.
    expect(screen.queryByText(/0 USD|0,00/)).toBeNull();
  });

  it('affiche une fourchette vérifiée ad valorem avec badge VÉRIFIÉ et conditions', () => {
    const VERIFIED_RANGE = {
      scope: 'provider',
      measure_name: 'VOC — Vérification de la Conformité',
      actor_name: 'Bureau Veritas, COTECNA, INTERTEK, SGS',
      mandating_authority: 'Ministère du Commerce (CIV)',
      side: 'import',
      fee_status: 'CALCULABLE',
      is_range: true,
      ad_valorem: true,
      rate_min: 0.003,
      rate_max: 0.0045,
      calculated_amount_min: 300,
      calculated_amount_max: 450,
      currency: null,
      tier: 'VERIFIED_PRIMARY',
      contact: 'https://www.douanes.ci/node/40794',
      conditions: 'Taux 0,30% à 0,45% de la valeur FOB ; seuil 1 000 000 FCFA.',
    };
    const result = costBlock([VERIFIED_RANGE], { complete: true });
    render(<RegulatoryCostBreakdown result={result} language="fr" />);
    expect(screen.getByText(/entre\s*300\s*et\s*450/i)).toBeInTheDocument();
    expect(screen.getByText(/VÉRIFIÉ \(source primaire\)/)).toBeInTheDocument();
    expect(screen.getByText(/0,3%–0,45% du FOB/)).toBeInTheDocument();
    expect(screen.getByText(/Taux 0,30% à 0,45% de la valeur FOB/)).toBeInTheDocument();
  });

  it('affiche un lien de contact cliquable quand disponible', () => {
    const result = costBlock([CALCULABLE_ITEM], {
      complete: true,
      regulatory_cost_total: 500,
      regulatory_cost_currency: 'USD',
    });
    render(<RegulatoryCostBreakdown result={result} language="fr" />);
    const link = screen.getByRole('link', { name: /cotecna\.example/i });
    expect(link).toHaveAttribute('href', 'https://cotecna.example/');
  });
});
