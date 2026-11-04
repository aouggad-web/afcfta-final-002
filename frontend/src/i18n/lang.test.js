import { describe, it, expect } from 'vitest';

import { pick, intlLocale, isRtl } from './lang';

describe('langues de l’interface', () => {
  it('pick choisit le libellé de la langue, le français par défaut', () => {
    expect(pick('fr', 'Pays', 'Country', 'البلد')).toBe('Pays');
    expect(pick('en', 'Pays', 'Country', 'البلد')).toBe('Country');
    expect(pick('ar', 'Pays', 'Country', 'البلد')).toBe('البلد');
    expect(pick(undefined, 'Pays', 'Country', 'البلد')).toBe('Pays');
    expect(pick('de', 'Pays', 'Country', 'البلد')).toBe('Pays');
  });

  it('seul l’arabe s’écrit de droite à gauche', () => {
    expect(isRtl('ar')).toBe(true);
    expect(isRtl('fr')).toBe(false);
    expect(isRtl('en')).toBe(false);
  });

  it('l’arabe formate les nombres en chiffres latins', () => {
    expect(intlLocale('fr')).toBe('fr-FR');
    expect(intlLocale('en')).toBe('en-US');
    expect((1234.5).toLocaleString(intlLocale('ar'))).toMatch(/^[0-9.,\s]+$/);
  });
});
