/**
 * Normalisation de `taxes_detail` (liste `[{ tax, rate, observation }, ...]`
 * servie par `mapCalculToLegacyResult`) pour la carte « Détail des Taxes ».
 *
 * Le taux préférentiel par taxe est repris de `taxes_breakdown`
 * (`rate_zlecaf_pct`) quand la ventilation le fournit : c'est la seule source
 * qui distingue une taxe réellement réduite (DD, DAPS exonéré) d'une taxe
 * inchangée. Absent, il reste `null` — l'appelant décide alors quoi afficher.
 */

const isNumber = (value) => typeof value === 'number' && Number.isFinite(value);

const toRate = (value) => {
  const rate = typeof value === 'string' ? Number.parseFloat(value) : value;
  return isNumber(rate) ? rate : null;
};

/** Clé de rapprochement entre `taxes_detail` et `taxes_breakdown`. */
const matchKey = (code) => String(code || '').trim().toUpperCase().replace(/[.\s_-]/g, '');

/**
 * Index des taux préférentiels par taxe, sur DEUX clés : le code (`DD`) et
 * l'intitulé (`Droit de douane`).
 *
 * Le code prime : un intitulé n'écrase jamais une entrée déjà indexée.
 */
function zlecafRatesByCode(taxesBreakdown) {
  const rates = new Map();
  if (!Array.isArray(taxesBreakdown)) return rates;
  const add = (value, rate) => {
    const key = matchKey(value);
    if (key && !rates.has(key)) rates.set(key, rate);
  };
  taxesBreakdown.forEach((row) => {
    if (isNumber(row?.rate_zlecaf_pct)) add(row.code, row.rate_zlecaf_pct);
  });
  taxesBreakdown.forEach((row) => {
    if (isNumber(row?.rate_zlecaf_pct)) add(row.name, row.rate_zlecaf_pct);
  });
  return rates;
}

export function normalizeTaxesDetail(taxesDetail, taxesBreakdown) {
  const zlecafRates = zlecafRatesByCode(taxesBreakdown);

  const withZlecafRate = (row) => {
    const key = [row.code, row.tax]
      .map(matchKey)
      .find((candidate) => candidate && zlecafRates.has(candidate));
    return {
      ...row,
      rate_zlecaf_pct: key ? zlecafRates.get(key) : null,
    };
  };

  if (Array.isArray(taxesDetail)) {
    return taxesDetail
      .filter((item) => item && (item.tax || item.code))
      .map((item) => withZlecafRate({
        code: item.code || item.tax,
        tax: item.tax || item.code,
        rate: toRate(item.rate),
        observation: item.observation || item.label || null,
        ...(item.note ? { note: item.note } : {}),
      }));
  }

  return [];
}
