import { describe, expect, it } from 'vitest';
import {
  effectiveTaxRateFromSteps,
  isCustomsDutyTax,
  isDisplayableZlecafResult,
  neutralizeZlecafBreakdown,
  neutralizeZlecafSummary,
  resolveZlecafAvailability,
} from './zlecafAvailability';

it.each(['DD', 'D.D', 'CET'])('reconnait %s comme droit de douane', (tax) => {
  expect(isCustomsDutyTax({ tax })).toBe(true);
});

it('ne confond pas la TVA avec le droit de douane', () => {
  expect(isCustomsDutyTax({ tax: 'TVA' })).toBe(false);
});

describe('resolveZlecafAvailability', () => {
  it('conserve un taux documente effectivement resolu, y compris 0 %', () => {
    expect(resolveZlecafAvailability({
      zlecaf_status: 'DOCUMENTED',
      trade_regime: 'ZLECAF',
      rates: { effective_zlecaf_rate_pct: 0 },
    })).toEqual({
      available: true,
      status: 'DOCUMENTED',
      effectiveRatePct: 0,
      offerRatePct: null,
      offerRateExpression: null,
    });
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
      offerRatePct: null,
      offerRateExpression: null,
    });
  });

  it.each(['OFFER_ONLY', 'PARTNER_NOTICE_REQUIRED'])(
    'distingue une offre non verifiee (%s) d une absence pure de source, sans jamais la calculer',
    (status) => {
      expect(resolveZlecafAvailability({
        zlecaf_status: status,
        trade_regime: 'NPF',
        rates: {},
      })).toEqual({
        available: false,
        status,
        effectiveRatePct: null,
        offerRatePct: null,
        offerRateExpression: null,
      });
    },
  );

  it.each(['OFFER_ONLY', 'PARTNER_NOTICE_REQUIRED'])(
    'porte le taux publie (%s) a titre informatif, sans jamais le rendre calculable',
    (status) => {
      expect(resolveZlecafAvailability({
        zlecaf_status: status,
        trade_regime: 'NPF',
        rates: {},
        zlecaf_offer_rate_pct: 2.0,
        zlecaf_offer_rate_expression: '2%',
      })).toEqual({
        available: false,
        status,
        effectiveRatePct: null,
        offerRatePct: 2.0,
        offerRateExpression: '2%',
      });
    },
  );

  it('n expose jamais un taux d offre publie quand un taux verifie est disponible', () => {
    expect(resolveZlecafAvailability({
      zlecaf_status: 'DOCUMENTED',
      trade_regime: 'ZLECAF',
      rates: { effective_zlecaf_rate_pct: 4 },
      zlecaf_offer_rate_pct: 2.0,
      zlecaf_offer_rate_expression: '2%',
    })).toEqual({
      available: true,
      status: 'DOCUMENTED',
      effectiveRatePct: 4,
      offerRatePct: null,
      offerRateExpression: null,
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
