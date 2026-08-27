/**
 * Normalisation de `taxes_detail` — le calculateur reçoit CE champ sous deux
 * formes selon le chemin de calcul emprunté par le frontend :
 *
 *  - chemin « authentique » (`/authentic-tariffs/calculate/...`) : un OBJET
 *    indexé par code de taxe canonique, produit par la normalisation de
 *    `services/authentic_tariff_service.py` —
 *    `{ DD: { rate, label, source, source_tax_code }, TVA: {...}, ... }` ;
 *  - chemin de repli (`/calculate-tariff`, `routes/calculator.py`) : une LISTE
 *    `[{ tax, rate, observation }, ...]` (contrat `TariffCalculationResponse`).
 *
 * L'affichage « Détail des Taxes » n'acceptait que la liste : sur le chemin
 * authentique, `taxes_detail.length` valait `undefined`, la carte entière
 * disparaissait et, avec elle, la colonne des taux ZLECAf par taxe. On
 * ramène donc les deux formes au même tableau, sans jamais fabriquer de taux.
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

function zlecafRatesByCode(taxesBreakdown) {
  const rates = new Map();
  if (!Array.isArray(taxesBreakdown)) return rates;
  taxesBreakdown.forEach((row) => {
    const key = matchKey(row?.code);
    if (key && isNumber(row?.rate_zlecaf_pct)) rates.set(key, row.rate_zlecaf_pct);
  });
  return rates;
}

export function normalizeTaxesDetail(taxesDetail, taxesBreakdown) {
  const zlecafRates = zlecafRatesByCode(taxesBreakdown);

  const withZlecafRate = (row) => {
    const key = matchKey(row.code) || matchKey(row.tax);
    return {
      ...row,
      rate_zlecaf_pct: zlecafRates.has(key) ? zlecafRates.get(key) : null,
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
      }));
  }

  if (taxesDetail && typeof taxesDetail === 'object') {
    return Object.entries(taxesDetail)
      .filter(([, info]) => info && typeof info === 'object')
      .map(([code, info]) => withZlecafRate({
        code,
        tax: info.source_tax_code || code,
        rate: toRate(info.rate),
        observation: info.label || info.name || null,
      }));
  }

  return [];
}
