/**
 * Ordre alphabétique des listes de pays, dans la langue affichée.
 *
 * `libelle(pays)` rend le nom tel qu'il est affiché dans la liste. Le tri
 * suit les règles de la langue (Intl.Collator) : « Égypte » se range avec
 * les E, « Côte d'Ivoire » avec les C, et l'arabe dans l'ordre arabe.
 */
const collateurs = {};

function collateur(langue) {
  const code = ['fr', 'en', 'ar'].includes(langue) ? langue : 'fr';
  if (!collateurs[code]) {
    collateurs[code] = new Intl.Collator(code, { sensitivity: 'base', ignorePunctuation: true });
  }
  return collateurs[code];
}

export function trierPays(liste, libelle, langue = 'fr') {
  const c = collateur(langue);
  return [...(liste || [])].sort((a, b) =>
    c.compare(String(libelle(a) ?? ''), String(libelle(b) ?? ''))
  );
}
