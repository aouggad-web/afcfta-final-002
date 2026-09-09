import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import TaxBreakdownDual from './TaxBreakdownDual';

const breakdown = [{
  code: 'DD',
  name: 'Droit de douane',
  category: 'droit_douane',
  base_expr: 'CIF',
  rate_npf_pct: 20,
  rate_zlecaf_pct: 0,
  amount_npf: 200,
  amount_zlecaf: 0,
  affected_by_zlecaf: true,
}];

const summary = {
  npf: { droit_douane: 200, autres_taxes: 0, tva: 0, cout_total: 1200 },
  zlecaf: { droit_douane: 0, autres_taxes: 0, tva: 0, cout_total: 1000 },
  economie_totale: 200,
};

describe('TaxBreakdownDual availability', () => {
  it('neutralise la colonne et les economies quand le taux est indisponible', () => {
    render(
      <TaxBreakdownDual
        breakdown={breakdown}
        summary={summary}
        currency={null}
        zlecafAvailable={false}
        language="fr"
      />,
    );

    expect(screen.getByText(/Taux ZLECAf non disponible/i)).toBeInTheDocument();
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('affiche le taux documente quand il est disponible', () => {
    render(
      <TaxBreakdownDual
        breakdown={breakdown}
        summary={summary}
        currency={null}
        zlecafAvailable
        language="fr"
      />,
    );

    expect(screen.getByText('(0%)')).toBeInTheDocument();
    expect(screen.getAllByText('$200').length).toBeGreaterThan(0);
  });
});
