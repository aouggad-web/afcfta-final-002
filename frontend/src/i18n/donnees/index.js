/**
 * Données du backend traduites dans la langue de l'interface.
 *
 * Les libellés que renvoient les sources (FAOSTAT, USGS, ISIC, Banque
 * mondiale, annuaires logistiques…) n'existent qu'en français ou en
 * anglais. Chaque domaine tient ici un dictionnaire « texte source → arabe »,
 * et trDonnee() traduit un libellé quand l'interface est en arabe. Les mines,
 * publiées en anglais par l'USGS, ont aussi un dictionnaire « source →
 * français » (mines.fr.json). Un texte absent du dictionnaire s'affiche tel
 * quel : rien ne casse, il reste seulement dans sa langue d'origine.
 */
import agriculture from './agriculture.json';
import mines from './mines.json';
import minesFr from './mines.fr.json';
import industrie from './industrie.json';
import statistiques from './statistiques.json';
import logistique from './logistique.json';
import { isRtl } from '../lang';

const normaliser = (t) => String(t).trim().replace(/\s+/g, ' ').toLowerCase();

const DICTIONNAIRE = new Map();
[agriculture, mines, industrie, statistiques, logistique].forEach((d) => {
  Object.entries(d).forEach(([source, ar]) => DICTIONNAIRE.set(normaliser(source), ar));
});

const DICTIONNAIRE_FR = new Map(
  Object.entries(minesFr).map(([source, fr]) => [normaliser(source), fr]),
);

/** Libellé de donnée dans la langue de l'interface (arabe, ou français pour les mines ; sinon inchangé). */
export function trDonnee(texte, lang) {
  if (texte == null) return texte;
  if (isRtl(lang)) return DICTIONNAIRE.get(normaliser(texte)) ?? texte;
  if (String(lang || '').startsWith('fr')) return DICTIONNAIRE_FR.get(normaliser(texte)) ?? texte;
  return texte;
}
