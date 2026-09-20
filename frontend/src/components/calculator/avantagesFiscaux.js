/**
 * Les « avantages fiscaux » du chemin historique, rendus honnêtement.
 *
 * LE DÉFAUT CORRIGÉ. Le chemin `/authentic-tariffs/calculate` renvoie, dans
 * `fiscal_advantages`, TOUTES les colonnes préférentielles que le tarif de
 * DESTINATION publie — quel que soit le partenaire. Pour la Tunisie, cela
 * comprend le Koweït, la Palestine, l'Union européenne, la Turquie, le
 * Royaume-Uni, le Maroc, la Jordanie et l'AELE. L'interface les affichait
 * toutes, sous le titre « Avantages ZLECAf — Exonérations applicables », avec
 * un coche vert et SANS montrer le taux.
 *
 * Trois choses étaient fausses à la fois :
 *
 * 1. LE PARTENAIRE. Une colonne au nom du Koweït n'est pas un avantage pour
 *    une importation ghanéenne. Elle ne regarde que l'origine qu'elle nomme.
 * 2. LE RÉGIME. Aucune de ces colonnes n'est la ZLECAf ; les ranger sous ce
 *    titre est une affirmation que la source ne porte pas.
 * 3. LE SENS. Le taux était masqué. Sur TUN/27101981100, le droit NPF est de
 *    0 % et les colonnes nommées valent 50 % : un coche vert y annonçait un
 *    « avantage » qui, s'il s'appliquait, coûterait plus cher que le droit
 *    commun.
 *
 * CE QUE CE MODULE FAIT. Il trie, il ne corrige rien :
 *
 * - les colonnes qui nomment l'origine choisie sont RETENUES, avec leur taux ;
 * - les colonnes qui en nomment une autre sont ÉCARTÉES et COMPTÉES — l'appel
 *   les déclare d'une ligne sobre, sans les nommer ;
 * - les avantages qui ne nomment aucun partenaire (exonération ZLECAf
 *   algérienne, colonne COMESA éthiopienne…) sont rendus tels quels ;
 * - le rapport au droit NPF est CALCULÉ quand le droit est connu, et laissé
 *   indéterminé quand il ne l'est pas. Jamais supposé.
 */

import { AFRICAN_COUNTRIES } from '../../utils/countryCodes';

/** Majuscules, sans accents ni ponctuation : « Égypte » et « EGYPTE » se rejoignent. */
export function normaliserNom(valeur) {
  return String(valeur ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '');
}

/**
 * Graphies du tarif qui ne coïncident pas avec le nom courant du pays.
 *
 * Ces entrées ne portent AUCUNE valeur fiscale : elles rapprochent deux
 * écritures d'un même nom. Chacune a été relevée dans une source, et rien
 * n'est ajouté « au cas où » : un partenaire non reconnu n'est pas affiché,
 * il est compté dans le résidu — une omission déclarée vaut mieux qu'un
 * rapprochement deviné.
 */
export const GRAPHIES_PARTENAIRES = {
  // Relevées dans backend/data/tariffs/TUN_tariffs.json (douane.gov.tn).
  RUANDA: 'RWA',
};

/** Le nom du partenaire porté par un avantage, ou `null` s'il n'en nomme aucun. */
export function partenaireDeLAvantage(avantage) {
  if (!avantage || typeof avantage !== 'object') return null;
  if (avantage.country_name) return String(avantage.country_name).trim();
  const texte = avantage.condition_fr || avantage.condition_en || avantage.description || '';
  const trouve = /pays partenaire\s*:\s*(.+)$/i.exec(String(texte));
  return trouve ? trouve[1].trim() : null;
}

/** Le taux d'un avantage, en pourcentage, ou `null` si la source n'en donne pas. */
export function tauxDeLAvantage(avantage) {
  const brut = avantage?.rate_pct ?? avantage?.rate;
  if (typeof brut === 'number' && Number.isFinite(brut)) return brut;
  if (typeof brut === 'string') {
    const n = parseFloat(brut.replace('%', '').replace(',', '.').trim());
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

/**
 * Les écritures sous lesquelles un pays peut être nommé : codes, noms, graphies.
 *
 * La table des pays est lue directement (`utils/countryCodes`) et non prise
 * dans la liste affichée : celle-ci ne porte qu'UN nom, dans la langue de
 * l'interface, et le tarif tunisien écrit ses partenaires en français. En
 * anglais, la correspondance aurait échoué et toutes les colonnes seraient
 * tombées dans le résidu.
 */
function clesDuPays(codeOrigine) {
  const cles = new Set();
  const ajouter = (v) => {
    const n = normaliserNom(v);
    if (n) cles.add(n);
  };
  const code = normaliserNom(codeOrigine);
  if (!code) return cles;
  ajouter(code);

  const iso3 = Object.keys(AFRICAN_COUNTRIES).find(
    (k) => k === code || normaliserNom(AFRICAN_COUNTRIES[k].iso2) === code,
  );
  if (iso3) {
    const fiche = AFRICAN_COUNTRIES[iso3];
    ajouter(iso3);
    ajouter(fiche.iso2);
    ajouter(fiche.name_fr);
    ajouter(fiche.name_en);
  }

  for (const [graphie, cible] of Object.entries(GRAPHIES_PARTENAIRES)) {
    if (cles.has(normaliserNom(cible))) cles.add(graphie);
  }
  return cles;
}

/**
 * Trie les avantages d'une liquidation pour l'origine choisie.
 *
 * @param {object[]} avantages   `fiscal_advantages` tel que la route le sert.
 * @param {string}   origine     code du pays d'origine (ISO2 ou ISO3).
 * @param {number|null} droitNpfPct droit NPF de la ligne, en %, ou `null`.
 * @returns {{pourLOrigine: object[], generaux: object[], autresPartenaires: number}}
 */
export function trierAvantages(avantages, origine, droitNpfPct) {
  const pourLOrigine = [];
  const generaux = [];
  let autresPartenaires = 0;
  const cles = clesDuPays(origine);
  const npf = typeof droitNpfPct === 'number' && Number.isFinite(droitNpfPct) ? droitNpfPct : null;

  for (const avantage of avantages || []) {
    if (!avantage) continue;
    const partenaire = partenaireDeLAvantage(avantage);
    const libelle =
      avantage.condition_fr || avantage.condition_en || avantage.description || partenaire || '';
    const taux = tauxDeLAvantage(avantage);
    // `reduitLeDroit` reste `null` tant que l'un des deux termes manque : une
    // comparaison contre un droit inconnu dirait n'importe quoi.
    const reduitLeDroit = npf === null || taux === null ? null : taux < npf;
    const entree = { avantage, partenaire, libelle, taux, reduitLeDroit };

    if (partenaire === null) {
      generaux.push(entree);
    } else if (cles.has(normaliserNom(partenaire))) {
      pourLOrigine.push(entree);
    } else {
      autresPartenaires += 1;
    }
  }

  return { pourLOrigine, generaux, autresPartenaires };
}
