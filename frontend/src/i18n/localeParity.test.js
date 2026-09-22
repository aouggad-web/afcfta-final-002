/**
 * Parité des fichiers de langue.
 *
 * Une clé traduite dans une langue et pas dans l'autre ne se voit pas : i18n
 * retombe silencieusement sur la clé brute, et l'écran affiche
 * « production.outlets.title » à un utilisateur. Ce test rend cette
 * divergence bruyante.
 *
 * Il devient indispensable à mesure que le module Opportunités migre ses
 * libellés vers i18n, et davantage encore le jour où l'arabe et le portugais
 * — langues de travail de la ZLECAf — seront ajoutés : il suffira alors de
 * les déclarer dans LOCALES pour que toute clé manquante soit signalée.
 */
import { describe, it, expect } from 'vitest';

import en from './locales/en.json';
import fr from './locales/fr.json';

const LOCALES = { fr, en };
const REFERENCE = 'fr';

/** Chemins de toutes les feuilles d'un objet, en notation pointée. */
function leafPaths(node, prefix = '') {
  if (node === null || typeof node !== 'object' || Array.isArray(node)) {
    return [prefix];
  }
  return Object.entries(node).flatMap(([key, value]) =>
    leafPaths(value, prefix ? `${prefix}.${key}` : key),
  );
}

const reference = new Set(leafPaths(LOCALES[REFERENCE]));

describe('parité des locales', () => {
  it('la locale de référence porte des clés', () => {
    expect(reference.size).toBeGreaterThan(50);
  });

  Object.keys(LOCALES)
    .filter((code) => code !== REFERENCE)
    .forEach((code) => {
      it(`« ${code} » ne laisse aucune clé de « ${REFERENCE} » sans traduction`, () => {
        const missing = [...reference].filter((k) => !new Set(leafPaths(LOCALES[code])).has(k));
        expect(missing).toEqual([]);
      });

      it(`« ${code} » n'introduit pas de clé absente de « ${REFERENCE} »`, () => {
        // Une clé orpheline est du texte mort : personne ne l'affiche, et elle
        // survit aux relectures parce qu'elle ressemble à du travail fait.
        const extra = leafPaths(LOCALES[code]).filter((k) => !reference.has(k));
        expect(extra).toEqual([]);
      });
    });

  it('aucune valeur traduite n’est vide', () => {
    Object.entries(LOCALES).forEach(([code, bundle]) => {
      const blanks = [];
      const walk = (node, prefix = '') => {
        // Une liste de chaînes est une valeur traduite légitime : les étapes de
        // chargement de l'analyse IA sont lues par index, pas une à une.
        if (Array.isArray(node)) {
          const ok = node.length > 0 && node.every((v) => typeof v === 'string' && v.trim() !== '');
          if (!ok) blanks.push(prefix);
          return;
        }
        if (node === null || typeof node !== 'object') {
          if (typeof node !== 'string' || node.trim() === '') blanks.push(prefix);
          return;
        }
        Object.entries(node).forEach(([k, v]) => walk(v, prefix ? `${prefix}.${k}` : k));
      };
      walk(bundle);
      expect({ code, blanks }).toEqual({ code, blanks: [] });
    });
  });

  it('les onglets du module Opportunités sont traduits, plus codés en dur', () => {
    // Ils vivaient dans deux listes parallèles au sein du composant ; toute
    // langue supplémentaire en aurait demandé une troisième.
    ['ai', 'strategic', 'substitution', 'simulator', 'bilateral', 'summary',
      'valueChains', 'byProduct', 'comparison'].forEach((id) => {
      expect(fr.opportunities.tabs[id]).toBeTruthy();
      expect(en.opportunities.tabs[id]).toBeTruthy();
    });
  });
});
