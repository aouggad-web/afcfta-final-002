/**
 * Données du backend traduites en arabe.
 *
 * Les libellés que renvoient les sources (FAOSTAT, USGS, ISIC, Banque
 * mondiale, annuaires logistiques…) n'existent qu'en français ou en
 * anglais. Chaque domaine tient ici un dictionnaire « texte source → arabe »,
 * et trDonnee() traduit un libellé quand l'interface est en arabe. Un texte
 * absent du dictionnaire s'affiche tel quel : rien ne casse, il reste
 * seulement dans sa langue d'origine.
 */
import agriculture from './agriculture.json';
import mines from './mines.json';
import industrie from './industrie.json';
import statistiques from './statistiques.json';
import logistique from './logistique.json';
import { isRtl } from '../lang';

const normaliser = (t) => String(t).trim().replace(/\s+/g, ' ').toLowerCase();

const DICTIONNAIRE = new Map();
[agriculture, mines, industrie, statistiques, logistique].forEach((d) => {
  Object.entries(d).forEach(([source, ar]) => DICTIONNAIRE.set(normaliser(source), ar));
});

/** Libellé de donnée dans la langue de l'interface (arabe seulement ; sinon inchangé). */
export function trDonnee(texte, lang) {
  if (texte == null || !isRtl(lang)) return texte;
  return DICTIONNAIRE.get(normaliser(texte)) ?? texte;
}
