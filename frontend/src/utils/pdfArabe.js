/**
 * PDF en arabe : police arabe, texte écrit de droite à gauche.
 *
 * Les polices standard de jsPDF n'ont pas l'arabe. On intègre Noto Sans
 * Arabic (pdfPoliceArabe.js, chargée à la demande : 260 Ko qu'aucun PDF en
 * français ou en anglais ne télécharge), et jsPDF lie les lettres (formes de
 * présentation) et ordonne la ligne (algorithme bidirectionnel).
 *
 * La mise en page reste celle du français et de l'anglais (décision de
 * l'exploitant du 07/11/2026) : logo, titre, cartes et colonnes aux mêmes
 * places. Seule la ligne de texte arabe s'écrit de droite à gauche.
 *
 * Deux réglages tiennent l'ordre des mots et des nombres :
 * - un texte qui contient de l'arabe est un paragraphe de droite à gauche
 *   (sans cela, jsPDF retourne la phrase dès qu'elle contient un mot latin) ;
 * - l'espace entre deux groupes de chiffres devient insécable : c'est un
 *   séparateur pour l'algorithme bidirectionnel, et « 10 000 » reste
 *   « 10 000 » au lieu de devenir « 000 10 ».
 */

let polices = null;

export const estArabe = (langue) => String(langue || '').startsWith('ar');

/** Charge la police (une fois). À attendre avant de construire un PDF arabe. */
export async function chargerPoliceArabe() {
  if (!polices) polices = await import('./pdfPoliceArabe');
  return polices;
}

const ARABE = /[؀-ۿﭐ-﷿ﹰ-﻿]/;
// isSymmetricSwapping : les parenthèses gardent leur sens dans un texte arabe.
const DROITE_A_GAUCHE = { isInputVisual: false, isOutputVisual: true, isInputRtl: true, isOutputRtl: false, isSymmetricSwapping: true };

const chiffresLies = (t) => (typeof t === 'string'
  ? t.replace(/(\d)[   ](?=\d)/g, '$1 ')
  : Array.isArray(t) ? t.map(chiffresLies) : t);

const contientArabe = (t) => ARABE.test(Array.isArray(t) ? t.join(' ') : String(t ?? ''));

/**
 * Prépare `doc` pour l'arabe. La police doit être chargée
 * (`await chargerPoliceArabe()`). Rend `doc`.
 */
export function preparerArabe(doc) {
  if (!polices) throw new Error('Police arabe non chargée : appeler chargerPoliceArabe() avant.');
  doc.addFileToVFS('NotoSansArabic-Regular.ttf', polices.NOTO_ARABE_REGULIER);
  doc.addFont('NotoSansArabic-Regular.ttf', 'NotoArabe', 'normal');
  doc.addFileToVFS('NotoSansArabic-Bold.ttf', polices.NOTO_ARABE_GRAS);
  doc.addFont('NotoSansArabic-Bold.ttf', 'NotoArabe', 'bold');

  doc.__arabe = true;

  const setFont = doc.setFont.bind(doc);
  doc.setFont = (nom, style, ...reste) => setFont(
    nom === 'helvetica' ? 'NotoArabe' : nom,
    String(style || '').includes('bold') ? 'bold' : 'normal',
    ...reste
  );

  const text = doc.text.bind(doc);
  doc.text = (t, x, y, options, ...reste) => {
    const contenu = chiffresLies(t);
    const o = { ...(options || {}) };
    if (contientArabe(contenu)) Object.assign(o, DROITE_A_GAUCHE);
    return text(contenu, x, y, o, ...reste);
  };
  ['splitTextToSize', 'getTextWidth'].forEach((m) => {
    const f = doc[m].bind(doc);
    doc[m] = (t, ...reste) => f(chiffresLies(t), ...reste);
  });

  doc.setFont('helvetica', 'normal');
  return doc;
}
