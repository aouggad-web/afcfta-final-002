export const ZLECAF_NOT_AVAILABLE = 'NOT_AVAILABLE';
export const ZLECAF_OFFER_ONLY = 'OFFER_ONLY';
export const ZLECAF_PARTNER_NOTICE_REQUIRED = 'PARTNER_NOTICE_REQUIRED';

const isNumber = (value) => typeof value === 'number' && Number.isFinite(value);

export function isCustomsDutyTax(tax) {
  const code = String(tax?.tax || tax?.code || '').trim().toUpperCase();
  return code === 'DD' || code === 'D.D' || code === 'CET';
}

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

  // OFFER_ONLY : offre tarifaire officielle archivée sans preuve
  // d'application ; PARTNER_NOTICE_REQUIRED : domestication en vigueur sans
  // liste de partenaires réciproques publiée. Aucun des deux n'est calculé,
  // mais tous deux sont distincts d'une absence pure de source
  // (NOT_AVAILABLE) pour l'affichage.
  const unavailableStatus =
    status === ZLECAF_OFFER_ONLY || status === ZLECAF_PARTNER_NOTICE_REQUIRED
      ? status
      : ZLECAF_NOT_AVAILABLE;

  // Taux publié au e-Tariff Book officiel de la ZLECAf, non vérifié comme
  // applicable : porté tel quel pour l'affichage informatif uniquement.
  // Jamais utilisé quand `available` est vrai (le taux vérifié prime).
  const offerRatePct = authenticResult?.zlecaf_offer_rate_pct;
  const offerRateExpression = authenticResult?.zlecaf_offer_rate_expression ?? null;

  return {
    available,
    status: available ? status : unavailableStatus,
    effectiveRatePct: available ? effectiveRatePct : null,
    offerRatePct: available ? null : (isNumber(offerRatePct) ? offerRatePct : null),
    offerRateExpression: available ? null : offerRateExpression,
  };
}

export function isDisplayableZlecafResult(result) {
  return (
    result?.zlecaf_status === 'DOCUMENTED'
    && result?.trade_regime === 'ZLECAF'
    && isNumber(result?.zlecaf_tariff_rate)
  );
}

/**
 * Taux de taxation total sous régime préférentiel, en pourcentage du CIF.
 *
 * `isDisplayableZlecafResult` ne garantit que la présence d'un TAUX de droit
 * de douane préférentiel, jamais celle du TOTAL : selon la réponse servie et
 * la ventilation disponible, `total_taxes_zlecaf` peut manquer même quand une
 * préférence est documentée. Le lire sans vérification
 * (`result.total_taxes_zlecaf.toFixed(1)`) faisait alors échouer le rendu de
 * tout le panneau de résultats. On renvoie `null` dans ce cas, et l'appelant
 * affiche « — » plutôt qu'un total fabriqué.
 */
export function zlecafTotalTaxRatePct(result) {
  return isDisplayableZlecafResult(result) && isNumber(result?.total_taxes_zlecaf)
    ? result.total_taxes_zlecaf
    : null;
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
