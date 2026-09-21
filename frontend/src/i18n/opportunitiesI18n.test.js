/**
 * Le module Opportunités ne retombe pas dans le bilinguisme en dur.
 *
 * Ses libellés vivaient dans 200 ternaires `lang === 'fr' ? 'X' : 'Y'`. Tant
 * qu'ils y étaient, ajouter l'arabe ou le portugais — langues de travail de la
 * ZLECAf — revenait à ajouter une branche à chacun : impossible en pratique,
 * et à moitié fait dès la première oubliée.
 *
 * Deux garde-fous, qui échouent pour des raisons différentes :
 *
 *   1. AUCUN TERNAIRE DE LIBELLÉ ne réapparaît. Le test distingue le libellé
 *      du CODE de langue : `fr ? 'fr-FR' : 'en-US'` choisit une locale de
 *      formatage, `fr ? 'fr' : 'en'` indexe un dictionnaire. Ceux-là sont
 *      légitimes tant que les langues sont deux ; ils devront devenir
 *      dérivés d'i18n le jour où elles seront quatre.
 *   2. TOUTE CLÉ APPELÉE EXISTE dans le fichier de langue. `localeParity`
 *      compare les locales entre elles ; il ne voit pas une clé que le code
 *      appelle et qu'aucune locale ne porte. i18n rendrait alors la clé brute
 *      à l'écran — « opportunities.aiAnalysis.title » — sans rien casser.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, it, expect } from 'vitest';

import fr from './locales/fr.json';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const MODULE_DIR = path.resolve(HERE, '../components/opportunities');

const SOURCES = fs
  .readdirSync(MODULE_DIR)
  .filter((f) => f.endsWith('.jsx') && !f.endsWith('.test.jsx'))
  .map((f) => ({ file: f, code: fs.readFileSync(path.join(MODULE_DIR, f), 'utf-8') }));

const LITERAL = "(?:'(?:[^'\\\\]|\\\\.)*'|\"(?:[^\"\\\\]|\\\\.)*\"|`(?:[^`\\\\]|\\\\.)*`)";
const CONDITION = "(?:fr|lang|language|currentLang|currentLanguage)\\s*(?:===|!==)\\s*['\"](?:fr|en)['\"]|\\bfr\\b";
const TERNARY = new RegExp(`(?:${CONDITION})\\s*\\?\\s*(${LITERAL})\\s*:\\s*(${LITERAL})`, 'g');

/** Codes de langue et locales de formatage — pas des libellés. */
const LANGUAGE_CODES = new Set(['fr', 'en', 'fra', 'eng', 'fr-fr', 'en-us', 'fr_fr', 'en_us']);

const unquote = (literal) => literal.slice(1, -1);

/** Appel `t("cle")` ou `t('cle')`.
 *
 * Les deux styles de guillemets coexistent dans le module : `SectoralAnalysis`
 * écrit en doubles, les autres en simples. Ne reconnaître qu'un seul style ne
 * ferait pas échouer ce fichier — il cesserait simplement d'y regarder, ce qui
 * est le pire des deux : un garde-fou muet passe pour un garde-fou. */
const KEY_CALL = /\bt\(\s*['"]((?:opportunities|production|common)\.[^'"]+)['"]/g;

/** Valeur d'une clé pointée, ou undefined. */
const lookup = (bundle, dotted) =>
  dotted.split('.').reduce((node, part) => (node == null ? undefined : node[part]), bundle);

describe('module Opportunités — les libellés sont passés à i18n', () => {
  it('aucun libellé n’est choisi par un ternaire de langue', () => {
    const offenders = [];
    SOURCES.forEach(({ file, code }) => {
      for (const match of code.matchAll(TERNARY)) {
        const [a, b] = [unquote(match[1]), unquote(match[2])];
        const isLanguageCode =
          LANGUAGE_CODES.has(a.toLowerCase()) && LANGUAGE_CODES.has(b.toLowerCase());
        if (!isLanguageCode) {
          const line = code.slice(0, match.index).split('\n').length;
          offenders.push(`${file}:${line} — ${match[0].slice(0, 70)}`);
        }
      }
    });
    expect(offenders).toEqual([]);
  });

  it('chaque clé appelée par le code existe dans la locale de référence', () => {
    // Une clé peut manquer de deux façons. La seconde est la plus sournoise :
    // elle EXISTE mais désigne une BRANCHE, parce qu'un espace de noms a
    // recouvert un libellé de même nom. i18next rend alors la clé brute à
    // l'écran, sans rien casser. Exiger une feuille attrape les deux.
    const missing = [];
    const isLeaf = (v) =>
      typeof v === 'string' || (Array.isArray(v) && v.every((x) => typeof x === 'string'));
    SOURCES.forEach(({ file, code }) => {
      for (const match of code.matchAll(KEY_CALL)) {
        if (!isLeaf(lookup(fr, match[1]))) {
          const line = code.slice(0, match.index).split('\n').length;
          missing.push(`${file}:${line} — ${match[1]}`);
        }
      }
    });
    expect(missing).toEqual([]);
  });

  it('le module porte bien un vrai volume de libellés traduits', () => {
    // Un garde-fou qui ne garde rien passerait tout aussi vert : si la
    // migration était annulée, ce compte s'effondrerait.
    const calls = SOURCES.reduce((n, { code }) => n + [...code.matchAll(KEY_CALL)].length, 0);
    expect(calls).toBeGreaterThan(150);
  });
});
