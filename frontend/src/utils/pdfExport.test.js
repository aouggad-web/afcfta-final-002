import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const sources = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
  const p = path.join(dir, e.name);
  if (e.isDirectory()) return sources(p);
  return /\.(js|jsx)$/.test(e.name) && !/\.test\./.test(e.name) ? [p] : [];
});

// html2canvas 1.4 ne comprend pas les couleurs CSS modernes du thème
// (color(), color-mix()) : il levait une erreur et aucun PDF « capture »
// ne sortait (Statistiques, Production, Logistique, 08/11/2026).
describe('export PDF par capture d’écran', () => {
  it('n’emploie plus html2canvas 1.x, mais html2canvas-pro', () => {
    const fautifs = sources(SRC).filter((f) => /from ['"]html2canvas['"]/.test(fs.readFileSync(f, 'utf-8')));
    expect(fautifs).toEqual([]);
    expect(fs.readFileSync(path.join(SRC, 'utils/pdfExport.js'), 'utf-8')).toContain("from 'html2canvas-pro'");
  });
});
