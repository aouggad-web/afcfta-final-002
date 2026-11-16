/**
 * Marque du site sur les PDF : le logo et le nom, tels qu'affichés dans la
 * barre du haut (AfcftaTopbar). Un PDF circule détaché de l'écran : il doit
 * dire d'où il vient.
 */
import { LOGO_PNG } from './pdfLogo';

export const NOM_SAAS = { fr: 'ZLECAf Intelligence', en: 'AfCFTA Intelligence' };

export function nomSaas(langue) {
  return String(langue || '').startsWith('en') ? NOM_SAAS.en : NOM_SAAS.fr;
}

/** Le logo, carré de `taille` mm, coin haut-gauche en (x, y). */
export function dessinerLogo(doc, x, y, taille) {
  try {
    doc.addImage(LOGO_PNG, 'PNG', x, y, taille, taille, 'logo-saas', 'FAST');
  } catch {
    // Un logo illisible ne doit jamais empêcher le rapport de sortir.
  }
}
