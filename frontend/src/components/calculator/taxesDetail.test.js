import { describe, expect, it } from 'vitest';

import { normalizeTaxesDetail } from './taxesDetail';

// Forme réellement servie par /authentic-tariffs/calculate/DZA/0101211100
// (services/authentic_tariff_service.py normalise en OBJET indexé par code).
const AUTHENTIC_DZA_DETAIL = {
  DD: { rate: 15.0, label: 'Droit de Douane', source: 'crawled', source_tax_code: 'DD' },
  TCS: { rate: 3.0, label: 'Taxe de Contribution de Solidarité', source: 'crawled', source_tax_code: 'TCS' },
  TVA: { rate: 19.0, label: 'TVA', source: 'crawled', source_tax_code: 'TVA' },
  PRCT: { rate: 2.0, label: 'Précompte sur Impôt', source: 'crawled', source_tax_code: 'PRCT' },
};

const AUTHENTIC_DZA_BREAKDOWN = [
  { code: 'DD', rate_npf_pct: 15.0, rate_zlecaf_pct: 6.0 },
  { code: 'TCS', rate_npf_pct: 3.0, rate_zlecaf_pct: 3.0 },
  { code: 'TVA', rate_npf_pct: 19.0, rate_zlecaf_pct: 19.0 },
  { code: 'PRCT', rate_npf_pct: 2.0, rate_zlecaf_pct: 2.0 },
];

describe('normalizeTaxesDetail', () => {
  it('rend la fiscalité du chemin authentique (objet) exploitable par la liste UI', () => {
    const rows = normalizeTaxesDetail(AUTHENTIC_DZA_DETAIL, AUTHENTIC_DZA_BREAKDOWN);

    expect(rows).toHaveLength(4);
    expect(rows.map((r) => r.tax)).toEqual(['DD', 'TCS', 'TVA', 'PRCT']);
    expect(rows.map((r) => r.rate)).toEqual([15.0, 3.0, 19.0, 2.0]);
    expect(rows[0].observation).toBe('Droit de Douane');
  });

  it('reprend le taux ZLECAf par taxe depuis la ventilation', () => {
    const rows = normalizeTaxesDetail(AUTHENTIC_DZA_DETAIL, AUTHENTIC_DZA_BREAKDOWN);
    const byCode = Object.fromEntries(rows.map((r) => [r.code, r.rate_zlecaf_pct]));

    // Seul le droit de douane est démantelé (circulaire DGD 482/2024).
    expect(byCode.DD).toBe(6.0);
    expect(byCode.TVA).toBe(19.0);
  });

  it('accepte la forme liste servie par le chemin de repli', () => {
    const rows = normalizeTaxesDetail(
      [{ tax: 'D.D', rate: 20, observation: 'Source: officielle' }],
      [{ code: 'DD', rate_zlecaf_pct: 0 }],
    );

    expect(rows).toEqual([{
      code: 'D.D',
      tax: 'D.D',
      rate: 20,
      observation: 'Source: officielle',
      rate_zlecaf_pct: 0,
    }]);
  });

  it('laisse le taux ZLECAf à null quand la ventilation ne le documente pas', () => {
    const rows = normalizeTaxesDetail(AUTHENTIC_DZA_DETAIL, null);
    expect(rows.every((r) => r.rate_zlecaf_pct === null)).toBe(true);
  });

  it('ne fabrique rien a partir d une fiscalite absente ou mal formee', () => {
    expect(normalizeTaxesDetail(undefined, [])).toEqual([]);
    expect(normalizeTaxesDetail(null, [])).toEqual([]);
    expect(normalizeTaxesDetail('DD 15%', [])).toEqual([]);
    expect(normalizeTaxesDetail({ DD: null }, [])).toEqual([]);
  });
});
