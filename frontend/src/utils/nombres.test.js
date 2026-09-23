import { describe, it, expect } from 'vitest';
import { montantCompact, nombreCompact, montant, nombre, chiffres, montantUnite, nombreUnite } from './nombres';

// Les espaces produites sont insécables (U+00A0) ; on les lit comme des
// espaces ordinaires pour garder les attentes lisibles.
const s = (x) => x.replace(/\u00A0/g, ' ');

describe('montantCompact', () => {
  it('écrit les montants à la française : virgule, Md, symbole après', () => {
    expect(s(montantCompact(64.56e9, 'fr', { B: 2, M: 1, K: 0 }))).toBe('64,56 Md $');
    expect(s(montantCompact(6.4e6, 'fr', { B: 2, M: 1, K: 0 }))).toBe('6,4 M $');
    expect(s(montantCompact(850e3, 'fr', { B: 2, M: 1, K: 0 }))).toBe('850 k $');
    expect(s(montantCompact(512, 'fr', { B: 2, M: 1, K: 0 }))).toBe('512 $');
  });

  it("ne change rien à l'anglais", () => {
    expect(montantCompact(64.56e9, 'en', { B: 2, M: 1, K: 0 })).toBe('$64.56B');
    expect(montantCompact(850e3, 'en', { B: 2, M: 1, K: 0 })).toBe('$850K');
    expect(montantCompact(1.2e12, 'en', { T: 2, B: 2 })).toBe('$1.20T');
  });

  it('compte les billions en milliards en français', () => {
    expect(s(montantCompact(2.7e12, 'fr', { T: 1 }))).toBe('2 700 Md $');
    expect(montantCompact(2.7e12, 'en', { T: 1 })).toBe('$2.7T');
  });

  it("n'utilise que les unités prévues par l'appelant", () => {
    // Sans palier K, 850 000 reste en unités, comme l'ancien formateur.
    expect(s(montantCompact(850e3, 'fr', { B: 1, M: 1 }))).toBe('850 000 $');
  });

  it('accepte des décimales plafonnées, sans zéros finaux', () => {
    const d = { B: 2, M: 1, u: 3 };
    expect(s(montantCompact(7.4e9, 'fr', d, { max: true }))).toBe('7,4 Md $');
    expect(montantCompact(21.8391e9, 'en', d, { max: true })).toBe('$21.84B');
    expect(s(montantCompact(123456, 'fr', d, { max: true }))).toBe('123 456 $');
    expect(montantCompact(123456, 'en', d, { max: true })).toBe('$123,456');
  });

  it("garde la précision demandée, sans l'arrondir davantage", () => {
    expect(s(montantCompact(64.564e9, 'fr', { B: 2 }))).toBe('64,56 Md $');
    expect(s(montantCompact(-1.25e9, 'fr', { B: 2 }))).toBe('-1,25 Md $');
  });
});

describe('nombreCompact', () => {
  it('écrit les quantités compactes à la française', () => {
    expect(s(nombreCompact(47.4e6, 'fr', { M: 1, K: 0 }))).toBe('47,4 M');
    expect(nombreCompact(47.4e6, 'en', { M: 1, K: 0 })).toBe('47.4M');
  });
});

describe('montant', () => {
  it('écrit les montants entiers à la française, et laisse l’anglais tel quel', () => {
    expect(s(montant(12345, 'fr'))).toBe('12 345 $');
    expect(montant(12345, 'en')).toBe('$12,345');
  });

  it("n'émet pas d'espace fine (U+202F), que les polices des PDF n'ont pas", () => {
    expect(montant(1234567, 'fr')).not.toMatch(/\u202F/);
    expect(montantCompact(1234.5e9, 'fr', { B: 1 })).not.toMatch(/\u202F/);
  });
});

describe('nombre', () => {
  it('groupe les milliers selon la langue', () => {
    expect(s(nombre(12345.6, 'fr', 1))).toBe('12 345,6');
    expect(nombre(12345.6, 'en', 1)).toBe('12,345.6');
    expect(nombre(12345.6, 'en')).toBe('12,346');
  });
});

describe('chiffres', () => {
  it('fixe les décimales dans les deux langues', () => {
    expect(chiffres(4.25, 'fr', 1)).toBe('4,3');
    expect(chiffres(4.25, 'en', 1)).toBe('4.3');
  });
});

describe('unités imposées', () => {
  it('garde l’unité de la donnée, dans les deux langues', () => {
    expect(s(montantUnite(290.8, 'B', 'fr', 1))).toBe('290,8 Md $');
    expect(s(montantUnite(0.8, 'B', 'fr', 1))).toBe('0,8 Md $');
    expect(montantUnite(290.8, 'B', 'en', 1)).toBe('$290.8B');
    expect(montantUnite(-10800, 'M', 'en', 0)).toBe('$-10800M');
    expect(s(montantUnite(-10800, 'M', 'fr', 0))).toBe('-10 800 M $');
    expect(s(nombreUnite(47.4, 'M', 'fr', 1))).toBe('47,4 M');
    expect(s(montantUnite(213.8, 'B', 'fr'))).toBe('213,8 Md $');
    expect(s(montantUnite(7500, 'M', 'fr'))).toBe('7 500 M $');
    expect(montantUnite(213.8, 'B', 'en')).toBe('$213.8B');
    expect(montantUnite(2.5, 'M', 'en')).toBe('$2.5M');
    expect(s(montantUnite(287.5, null, 'fr'))).toBe('287,5 $');
    expect(montantUnite(287.5, null, 'en')).toBe('$287.5');
    expect(montantUnite(1234.5, 'M', 'en', 3, { max: true })).toBe('$1,234.5M');
    expect(s(montantUnite(1234.5, 'M', 'fr', 3, { max: true }))).toBe('1 234,5 M $');
    expect(nombreUnite(47.4, 'M', 'en', 1)).toBe('47.4M');
  });
});
