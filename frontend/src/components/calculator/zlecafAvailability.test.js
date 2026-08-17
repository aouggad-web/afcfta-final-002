import { describe, expect, it } from 'vitest';
import {
  effectiveTaxRateFromSteps,
  isDisplayableZlecafResult,
  neutralizeZlecafBreakdown,
  neutralizeZlecafSummary,
  resolveZlecafAvailability,
} from './zlecafAvailability';

describe('resolveZlecafAvailability', () => {
  it('conserve un taux documente effectivement resolu, y compris 0 %', () => {
    expect(resolveZlecafAvailability({
      zlecaf_status: 'DOCUMENTED',
      trade_regime: 'ZLECAF',
      rates: { effective_zlecaf_rate_pct: 0 },
    })).toEqual({ available: true, status: 'DOCUMENTED', effectiveRatePct: 0 });
  });

  it.each([
    [{ zlecaf_status: 'NOT_AVAILABLE', trade_regime: 'ZLECAF', rates: {} }],
    [{ zlecaf_status: 'DOCUMENTED', trade_regime: 'ZLECAF', rates: { effective_zlecaf_rate_pct: null } }],
    [{ zlecaf_status: 'DOCUMENTED', trade_regime: 'CUSTOMS_UNION', rates: { effective_zlecaf_rate_pct: 0 } }],
  ])('ne transforme jamais une absence de taux en 0 %%', (payload) => {
    expect(resolveZlecafAvailability(payload)).toEqual({
      available: false,
      status: 'NOT_AVAILABLE',
      effectiveRatePct: null,
    });
  });
});

it('n affiche la colonne ZLECAf que pour un taux documente', () => {
  expect(isDisplayableZlecafResult({
    zlecaf_status: 'DOCUMENTED',
    trade_regime: 'ZLECAF',
    zlecaf_tariff_rate: 0,
  })).toBe(true);
  expect(isDisplayableZlecafResult({
    zlecaf_status: 'NOT_AVAILABLE',
    trade_regime: 'ZLECAF',
    zlecaf_tariff_rate: null,
  })).toBe(false);
});

it('neutralise les colonnes et economies ZLECAf indisponibles', () => {
  const breakdown = neutralizeZlecafBreakdown([
    { code: 'DD', rate_npf_pct: 20, rate_zlecaf_pct: 0, amount_zlecaf: 0 },
  ], false);
  expect(breakdown[0]).toMatchObject({
    rate_zlecaf_pct: null,
    amount_zlecaf: null,
    affected_by_zlecaf: false,
  });
  expect(neutralizeZlecafSummary({
    npf: { cout_total: 120 },
    zlecaf: { cout_total: 100 },
    economie_totale: 20,
  }, false)).toEqual({
    npf: { cout_total: 120 },
    zlecaf: null,
    economie_droits: null,
    economie_totale: null,
  });
});

it('calcule le taux effectif uniquement a partir d etapes numeriques', () => {
  expect(effectiveTaxRateFromSteps([{ amount: 100 }, { amount: 90 }], 1000)).toBe(19);
  expect(effectiveTaxRateFromSteps([], 0)).toBeNull();
});
