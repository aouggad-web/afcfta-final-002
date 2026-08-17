export const ZLECAF_NOT_AVAILABLE = 'NOT_AVAILABLE';

const isNumber = (value) => typeof value === 'number' && Number.isFinite(value);

/**
 * A ZLECAf rate is displayable only when the backend documented the rate,
 * resolved the ZLECAf regime for this origin/destination pair, and returned
 * the effective percentage after all legal gates. Missing data never means 0%.
 */
export function resolveZlecafAvailability(authenticResult) {
  const effectiveRatePct = authenticResult?.rates?.effective_zlecaf_rate_pct;
  const status = authenticResult?.zlecaf_status || ZLECAF_NOT_AVAILABLE;
  const available = (
    status === 'DOCUMENTED'
    && authenticResult?.trade_regime === 'ZLECAF'
    && isNumber(effectiveRatePct)
  );

  return {
    available,
    status: available ? status : ZLECAF_NOT_AVAILABLE,
    effectiveRatePct: available ? effectiveRatePct : null,
  };
}

export function isDisplayableZlecafResult(result) {
  return (
    result?.zlecaf_status === 'DOCUMENTED'
    && result?.trade_regime === 'ZLECAF'
    && isNumber(result?.zlecaf_tariff_rate)
  );
}

export function effectiveTaxRateFromSteps(steps, cifValue) {
  if (!Array.isArray(steps) || !isNumber(cifValue) || cifValue <= 0) return null;
  const total = steps.reduce((sum, step) => sum + (isNumber(step?.amount) ? step.amount : 0), 0);
  return Math.round((total / cifValue) * 10000) / 100;
}

export function neutralizeZlecafBreakdown(breakdown, available) {
  if (!Array.isArray(breakdown) || available) return breakdown || [];
  return breakdown.map((line) => ({
    ...line,
    rate_zlecaf_pct: null,
    amount_zlecaf: null,
    amount_zlecaf_local: null,
    base_value_zlecaf: null,
    affected_by_zlecaf: false,
  }));
}

export function neutralizeZlecafSummary(summary, available) {
  if (!summary || available) return summary || null;
  return {
    ...summary,
    zlecaf: null,
    economie_droits: null,
    economie_totale: null,
  };
}
