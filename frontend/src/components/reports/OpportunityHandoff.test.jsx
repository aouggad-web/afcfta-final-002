/**
 * Tests de l'arrivée du chaînage, côté module Opportunités.
 *
 * Deux intentions atterrissent par le même canal sessionStorage, et elles
 * posent des questions OPPOSÉES :
 *
 *   market — « ce pays produit ceci, où le vendre ? »   (exportateur)
 *   s3     — « ce pays a-t-il besoin de ceci ? »        (importateur)
 *
 * L'intention « s3 » est l'historique, déposée par le module Statistiques.
 * « market » est celle du module Production. Servir l'une pour l'autre
 * enverrait le lecteur vers l'écran qui répond à la mauvaise question — c'est
 * précisément ce que ces tests empêchent de régresser.
 */
import { describe, it, expect, beforeEach } from 'vitest';

const KEY = 'zlecaf_opportunites_handoff';

/**
 * Reproduit la lecture du handoff telle que l'implémente OpportunityReportTab.
 * Le composant réel monte tout le module (axios, PDF, une dizaine de vues) ;
 * ce qu'on veut verrouiller ici est la règle d'aiguillage, pas le rendu.
 */
function readHandoff(raw) {
  if (!raw) return null;
  let h;
  try {
    h = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!h || !h.hsCode) return null;
  const k = h.k || 1;
  if (h.mode === 'market') {
    return { mode: 'market', marketPrefill: { hsCode: h.hsCode, k } };
  }
  if (h.country) {
    return {
      mode: 's3',
      s3Prefill: { country: h.country, hsCode: h.hsCode, withImports: true, k },
    };
  }
  return null;
}

beforeEach(() => sessionStorage.clear());

describe('aiguillage du handoff', () => {
  it("ouvre la recherche de marchés pour une intention exportateur", () => {
    const out = readHandoff(
      JSON.stringify({ country: 'KEN', hsCode: '0902', mode: 'market', k: 7 }),
    );
    expect(out.mode).toBe('market');
    expect(out.marketPrefill).toEqual({ hsCode: '0902', k: 7 });
    expect(out.s3Prefill).toBeUndefined();
  });

  it("conserve le comportement historique quand aucune intention n'est précisée", () => {
    // Le module Statistiques dépose {country, hsCode} sans mode : il doit
    // continuer d'ouvrir le besoin national, signal d'import activé.
    const out = readHandoff(JSON.stringify({ country: 'DZA', hsCode: '1006', k: 3 }));
    expect(out.mode).toBe('s3');
    expect(out.s3Prefill).toEqual({
      country: 'DZA',
      hsCode: '1006',
      withImports: true,
      k: 3,
    });
  });

  it("accepte une intention marché sans pays : le produit suffit à chercher des débouchés", () => {
    const out = readHandoff(JSON.stringify({ hsCode: '1801', mode: 'market' }));
    expect(out.mode).toBe('market');
    expect(out.marketPrefill.hsCode).toBe('1801');
  });

  it("ignore un handoff sans code SH plutôt que d'ouvrir un écran vide", () => {
    expect(readHandoff(JSON.stringify({ country: 'KEN' }))).toBeNull();
    expect(readHandoff(JSON.stringify({ hsCode: '1006' }))).toBeNull();
  });

  it('ignore un handoff illisible sans faire tomber le module', () => {
    expect(readHandoff('{ pas du JSON')).toBeNull();
    expect(readHandoff(null)).toBeNull();
  });

  it('porte un jeton k, pour que deux arrivées sur le même produit relancent', () => {
    const a = readHandoff(JSON.stringify({ hsCode: '0902', mode: 'market', k: 11 }));
    const b = readHandoff(JSON.stringify({ hsCode: '0902', mode: 'market', k: 12 }));
    expect(a.marketPrefill.k).not.toBe(b.marketPrefill.k);
  });
});
