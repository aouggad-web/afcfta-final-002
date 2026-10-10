import React from 'react';
import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import i18n from '../../i18n';
import EtatCalculBadge from './EtatCalculBadge';
import TaxBreakdownDual from './TaxBreakdownDual';

afterEach(() => i18n.changeLanguage('fr'));

describe('EtatCalculBadge', () => {
  it('nomme un total partiel et les droits qui manquent', () => {
    render(
      <EtatCalculBadge
        etat="PARTIEL"
        manques={[
          { code: 'DSV', motif: 'ASSIETTE_INDISPONIBLE' },
          { code: 'TVA', motif: 'ASSIETTE_INCOMPLETE' },
        ]}
      />,
    );
    expect(screen.getByText('Total partiel')).toBeInTheDocument();
    expect(screen.getByText('2 droits non calculés : DSV, TVA')).toBeInTheDocument();
  });

  it('se traduit en anglais', async () => {
    await i18n.changeLanguage('en');
    render(<EtatCalculBadge etat="INDISPONIBLE" manques={[{ code: 'DD', motif: 'TAUX_INDISPONIBLE' }]} />);
    expect(screen.getByText('Calculation unavailable')).toBeInTheDocument();
    expect(screen.getByText('1 duty not calculated: DD')).toBeInTheDocument();
  });

  it("n'invente aucun état quand le moteur n'en rend pas", () => {
    const { container } = render(<EtatCalculBadge etat={undefined} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('accompagne le coût total du tableau comparatif', () => {
    render(
      <TaxBreakdownDual
        breakdown={[{
          code: 'DD', name: 'Droit de douane', category: 'droit_douane', base_expr: 'CIF',
          rate_npf_pct: 36, rate_zlecaf_pct: null, amount_npf: 3600, amount_zlecaf: null,
          affected_by_zlecaf: false,
        }]}
        summary={{
          npf: { droit_douane: 3600, autres_taxes: null, tva: null, cout_total: null },
          zlecaf: null,
          economie_totale: null,
        }}
        currency={null}
        zlecafAvailable={false}
        language="fr"
        etats={{ npf: { etat: 'PARTIEL', manques: [{ code: 'TVA', motif: 'ASSIETTE_INCOMPLETE' }] } }}
      />,
    );
    expect(screen.getByText('Total partiel')).toBeInTheDocument();
    expect(screen.getByText('1 droit non calculé : TVA')).toBeInTheDocument();
  });
});
