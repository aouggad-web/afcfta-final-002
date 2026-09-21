/**
 * Les couleurs qui VEULENT DIRE quelque chose suivent le thème.
 *
 * Le thème sombre est celui par défaut (`localStorage.getItem('zlecaf_theme')
 * || 'dark'`). Or les couleurs qui étaient écrites en dur dans ce module
 * avaient manifestement été choisies sur fond clair : `#92400e` donne 7,09:1
 * sur blanc et 2,30:1 sur la carte sombre. Trente occurrences de texte
 * passaient ainsi sous le seuil AA pour le visiteur ordinaire — et aucun
 * réglage ne pouvait les sauver, puisqu'une valeur fixe ne peut pas satisfaire
 * deux fonds à la fois. C'est à cela que servent les jetons : ils changent
 * avec le thème.
 *
 * CE QUE CE TEST NE CONDAMNE PAS
 * -------------------------------
 * Toute couleur en dur n'est pas fautive. Sont légitimes, et donc tolérées :
 *   • les PALETTES CATÉGORIELLES (`COLORS`, `DEFAULT_VALUE_CHAINS[].color`…)
 *     dont le rôle est de distinguer des séries entre elles. Les rendre
 *     sémantiques ferait dire « erreur » à « cacao » et fondrait deux chaînes
 *     dans la même teinte ;
 *   • le CHROME RECHARTS (axes, grilles, info-bulles), que la bibliothèque ne
 *     sait pas lire depuis une variable CSS ;
 *   • les REPLIS de jeton, `var(--afcfta-muted, #667)`, déjà corrects ;
 *   • le BLANC sur aplat coloré, juste dans les deux thèmes.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, it, expect } from 'vitest';

const HERE = path.dirname(fileURLToPath(import.meta.url));

/** Teintes sémantiques retirées du dur ; elles ne doivent pas revenir. */
const SEMANTIC = [
  '#e05070', '#dc2626', '#1a7f37', '#059669', '#92400e', '#9a6700',
  '#b45309', '#ca8a04', '#d97706', '#d4891a', '#0969da', '#4f8ef7', '#2563eb',
];

/** Contextes où une couleur en dur reste légitime (voir l'en-tête). */
const TOLERATED = /var\(--|fill=|stroke=|stopColor=|barColor=|tick=|link=|vc\.color/;

const PALETTE_DECL =
  /const (DEFAULT_VALUE_CHAINS|COLORS|SOURCE_COLORS|MIDDLE_COLORS|SINK_COLORS|CHART_COLORS)\s*=/;

/** Numéros de ligne appartenant à une déclaration de palette. */
function paletteLines(lines) {
  const inside = new Set();
  let open = false;
  let depth = 0;
  lines.forEach((line, i) => {
    if (PALETTE_DECL.test(line)) {
      open = true;
      depth = 0;
    }
    if (!open) return;
    inside.add(i);
    for (const ch of line) {
      if (ch === '{' || ch === '[') depth += 1;
      if (ch === '}' || ch === ']') depth -= 1;
    }
    if (depth <= 0 && /[;\]]\s*$/.test(line)) open = false;
  });
  return inside;
}

describe('couleurs sémantiques du module Opportunités', () => {
  it('aucune teinte sémantique n’est réécrite en dur', () => {
    const offenders = [];
    fs.readdirSync(HERE)
      .filter((f) => f.endsWith('.jsx') && !f.endsWith('.test.jsx'))
      .forEach((file) => {
        const lines = fs.readFileSync(path.join(HERE, file), 'utf-8').split('\n');
        const skip = paletteLines(lines);
        lines.forEach((line, i) => {
          if (skip.has(i) || TOLERATED.test(line)) return;
          const hit = SEMANTIC.find((c) => line.toLowerCase().includes(c));
          if (hit) offenders.push(`${file}:${i + 1} — ${hit}`);
        });
      });
    expect(offenders).toEqual([]);
  });

  it('les jetons sémantiques sont réellement employés', () => {
    // Un garde-fou qui ne garde rien passerait tout aussi vert : si la
    // migration était annulée, ce compte s'effondrerait.
    const used = fs
      .readdirSync(HERE)
      .filter((f) => f.endsWith('.jsx') && !f.endsWith('.test.jsx'))
      .reduce((n, f) => {
        const src = fs.readFileSync(path.join(HERE, f), 'utf-8');
        return n + ['--danger', '--success', '--info'].reduce(
          (m, tk) => m + src.split(`var(${tk})`).length - 1, 0);
      }, 0);
    expect(used).toBeGreaterThan(20);
  });
});
