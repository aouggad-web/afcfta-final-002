/**
 * Montants et nombres compacts, selon la langue de l'interface.
 *
 * Français : virgule décimale, espace insécable, unités k / M / Md,
 * symbole après le nombre — « 64,6 Md $ », « 850 k $ », « 12 345 $ ».
 * Le billion (10^12) reste compté en milliards — « 2 700 Md $ » — comme
 * dans la presse : l'abréviation « Bn » se confondrait avec l'anglais bn.
 * Anglais : la forme que l'application affichait déjà — « $64.6B ».
 *
 * La précision reste celle que demande l'appelant, unité par unité : on
 * change la forme d'un chiffre, jamais son arrondi.
 */

// Espace insécable ordinaire (U+00A0). Intl sépare les milliers français par
// une espace fine insécable (U+202F), absente des polices standard de jsPDF :
// on la ramène à U+00A0 pour que les exports PDF l'impriment aussi.
const NBSP = ' ';
const FINE = / /g;

// Du plus grand au plus petit ; la clé est celle que l'appelant utilise
// pour fixer ses décimales.
const UNITES = [
  { cle: 'T', div: 1e12, fr: 'Md', en: 'T' },
  { cle: 'B', div: 1e9, fr: 'Md', en: 'B' },
  { cle: 'M', div: 1e6, fr: 'M', en: 'M' },
  { cle: 'K', div: 1e3, fr: 'k', en: 'K' },
];

export const estAnglais = (langue) => String(langue || 'fr').toLowerCase().startsWith('en');

/** Chiffres seuls, décimales fixes : chiffres(4.25, 'fr', 1) → « 4,3 ». */
export function chiffres(n, langue = 'fr', decimales = 0) {
  if (estAnglais(langue)) return Number(n).toFixed(decimales);
  return Number(n)
    .toLocaleString('fr-FR', {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
    })
    .replace(FINE, NBSP);
}

// Choisit l'unité parmi celles que l'appelant a prévues (clés de
// `decimales`), comme le faisait son formateur ; en deçà, valeur brute.
function decoupe(valeur, decimales, langue) {
  const abs = Math.abs(valeur);
  const u = UNITES.find((x) => x.cle in decimales && abs >= x.div);
  if (!u) return { n: valeur, d: decimales.u ?? 0, fr: '', en: '' };
  if (u.cle === 'T' && !estAnglais(langue)) {
    // Billions comptés en milliards : 3 décimales de moins, même valeur.
    return { n: valeur / 1e9, d: Math.max(0, decimales.T - 3), fr: 'Md', en: 'T' };
  }
  return { n: valeur / u.div, d: decimales[u.cle], fr: u.fr, en: u.en };
}

/**
 * Nombre compact : nombreCompact(4.2e6, 'fr', { M: 1, K: 0 }) → « 4,2 M » ;
 * en anglais → « 4.2M ».
 */
export function nombreCompact(valeur, langue = 'fr', decimales = {}) {
  const { n, d, fr, en } = decoupe(Number(valeur), decimales, langue);
  if (estAnglais(langue)) return `${Number(n).toFixed(d)}${en}`;
  return fr ? `${chiffres(n, 'fr', d)}${NBSP}${fr}` : chiffres(n, 'fr', d);
}

/**
 * Montant compact en dollars : montantCompact(64.56e9, 'fr', { B: 2 })
 * → « 64,56 Md $ » ; en anglais → « $64.56B ». Avec { max: true }, les
 * décimales sont un plafond, sans zéros finaux : 7,4 Md $ plutôt que 7,40.
 */
export function montantCompact(valeur, langue = 'fr', decimales = {}, { max = false } = {}) {
  const { n, d, fr, en } = decoupe(Number(valeur), decimales, langue);
  if (estAnglais(langue)) return `$${max ? nombre(n, 'en', d) : Number(n).toFixed(d)}${en}`;
  return `${max ? nombre(n, 'fr', d) : chiffres(n, 'fr', d)}${NBSP}${fr ? `${fr}${NBSP}` : ''}$`;
}

/**
 * Nombre groupé par milliers : nombre(12345.6, 'fr', 1) → « 12 345,6 » ;
 * en anglais → « 12,345.6 ».
 */
export function nombre(valeur, langue = 'fr', maxDecimales = 0) {
  const opts = { maximumFractionDigits: maxDecimales };
  if (estAnglais(langue)) return Number(valeur).toLocaleString('en-US', opts);
  return Number(valeur).toLocaleString('fr-FR', opts).replace(FINE, NBSP);
}

/**
 * Montant entier en dollars : montant(12345, 'fr') → « 12 345 $ » ;
 * en anglais → « $12,345 ».
 */
export function montant(valeur, langue = 'fr', maxDecimales = 0) {
  const n = nombre(valeur, langue, maxDecimales);
  return estAnglais(langue) ? `$${n}` : `${n}${NBSP}$`;
}

const unite = (cle) => UNITES.find((x) => x.cle === cle) || { fr: '', en: '' };

/**
 * Montant dans une unité imposée, pour une valeur déjà exprimée en
 * milliards (B), millions (M) ou milliers (K) — pas en billions, que le
 * français compte en milliards (voir montantCompact) : montantUnite(290.8, 'B', 'fr', 1)
 * → « 290,8 Md $ » ; en anglais → « $290.8B ». Sans `decimales`, la
 * valeur garde les chiffres qu'elle a : montantUnite(213.8, 'B', 'fr')
 * → « 213,8 Md $ », en anglais « $213.8B » comme avant. Avec `cle` à
 * null, montant sans unité : montantUnite(287.5, null, 'fr') → « 287,5 $ ».
 * Avec { max: true }, décimales plafonnées et milliers groupés, comme
 * toLocaleString : montantUnite(1234.5, 'M', 'en', 3, { max: true })
 * → « $1,234.5M ».
 */
export function montantUnite(n, cle, langue = 'fr', decimales, { max = false } = {}) {
  const u = unite(cle);
  if (estAnglais(langue)) {
    if (max) return `$${nombre(n, 'en', decimales)}${u.en}`;
    return `$${decimales == null ? n : Number(n).toFixed(decimales)}${u.en}`;
  }
  const d = decimales ?? (String(n).split('.')[1] || '').length;
  return `${max ? nombre(n, 'fr', d) : chiffres(n, 'fr', d)}${NBSP}${u.fr ? `${u.fr}${NBSP}` : ''}$`;
}

/**
 * Nombre dans une unité imposée : nombreUnite(47.4, 'M', 'fr', 1)
 * → « 47,4 M » ; en anglais → « 47.4M ».
 */
export function nombreUnite(n, cle, langue = 'fr', decimales = 0) {
  const u = unite(cle);
  if (estAnglais(langue)) return `${Number(n).toFixed(decimales)}${u.en}`;
  return u.fr ? `${chiffres(n, 'fr', decimales)}${NBSP}${u.fr}` : chiffres(n, 'fr', decimales);
}
