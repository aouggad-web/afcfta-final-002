const isNumber = (value) => typeof value === 'number' && Number.isFinite(value);

export function isCustomsDutyTax(tax) {
  const code = String(tax?.tax || tax?.code || '').trim().toUpperCase();
  return code === 'DD' || code === 'D.D' || code === 'CET';
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
