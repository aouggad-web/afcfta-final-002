import { describe, expect, it } from 'vitest';
import {
  isCustomsDutyTax,
  isDisplayableZlecafResult,
  preferentialRegimeLabel,
  zlecafTotalTaxRatePct,
} from './zlecafAvailability';

it.each(['DD', 'D.D', 'CET'])('reconnait %s comme droit de douane', (tax) => {
  expect(isCustomsDutyTax({ tax })).toBe(true);
});

it('ne confond pas la TVA avec le droit de douane', () => {
  expect(isCustomsDutyTax({ tax: 'TVA' })).toBe(false);
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

describe('zlecafTotalTaxRatePct', () => {
  const documented = {
    zlecaf_status: 'DOCUMENTED',
    trade_regime: 'ZLECAF',
    zlecaf_tariff_rate: 0.06,
  };

  it('renvoie le taux total quand il a été calculé', () => {
    expect(zlecafTotalTaxRatePct({ ...documented, total_taxes_zlecaf: 31.72 })).toBe(31.72);
  });

  it('renvoie null quand le chemin de repli ne fournit pas de total', () => {
    // Sans ce garde-fou, `result.total_taxes_zlecaf.toFixed(1)` faisait
    // échouer le rendu de tout le panneau de résultats.
    expect(zlecafTotalTaxRatePct(documented)).toBeNull();
    expect(zlecafTotalTaxRatePct({ ...documented, total_taxes_zlecaf: null })).toBeNull();
  });

  it('renvoie null quand aucune préférence n\'est affichable', () => {
    expect(zlecafTotalTaxRatePct({ zlecaf_status: 'NOT_AVAILABLE', total_taxes_zlecaf: 31.72 }))
      .toBeNull();
  });
});

describe('régime de zone de libre-échange retenu à la place de la ZLECAf (GZALE)', () => {
  const gzale = {
    zlecaf_status: 'NOT_AVAILABLE',
    trade_regime: 'FTA_CONDITIONAL',
    trade_regime_code: 'GZALE',
    preferential_regime_applied: true,
    zlecaf_tariff_rate: 0,
    total_taxes_zlecaf: 22.3,
  };

  it('chiffre la colonne préférentielle et ses totaux', () => {
    expect(isDisplayableZlecafResult(gzale)).toBe(true);
    expect(zlecafTotalTaxRatePct(gzale)).toBe(22.3);
  });

  it('la nomme GZALE, jamais ZLECAf', () => {
    expect(preferentialRegimeLabel(gzale)).toBe('GZALE');
    expect(preferentialRegimeLabel({ trade_regime: 'ZLECAF' })).toBeNull();
  });

  it("ne l'affiche pas quand aucun régime n'a été appliqué", () => {
    expect(isDisplayableZlecafResult({ ...gzale, preferential_regime_applied: false })).toBe(false);
  });
});
