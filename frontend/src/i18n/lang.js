/**
 * Langues de l'interface : français (référence), anglais et arabe — trois
 * des langues de travail de la ZLECAf. L'arabe s'écrit de droite à gauche.
 */

/** Vrai si la langue s'écrit de droite à gauche. */
export const isRtl = (lang) => String(lang || '').startsWith('ar');

/**
 * Libellé dans la langue de l'interface :
 * pick(language, 'Pays', 'Country', 'البلد').
 * Une langue inconnue retombe sur le français, langue de référence.
 */
export function pick(lang, fr, en, ar) {
  const l = String(lang || 'fr');
  if (l.startsWith('ar')) return ar;
  if (l.startsWith('en')) return en;
  return fr;
}

/**
 * Locale Intl (dates, nombres) de la langue de l'interface. L'arabe garde
 * les chiffres latins, d'usage au Maghreb et dans les codes du SH ; sans
 * « nu-latn », les navigateurs écriraient les chiffres arabes orientaux.
 */
export const intlLocale = (lang) => pick(lang, 'fr-FR', 'en-US', 'ar-u-nu-latn');
