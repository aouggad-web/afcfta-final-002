import { describe, it, expect } from 'vitest';
import { trDonnee } from './index';

describe('trDonnee', () => {
  it('laisse le texte intact hors arabe et quand il est inconnu', () => {
    expect(trDonnee('Texte inconnu', 'ar')).toBe('Texte inconnu');
    expect(trDonnee('Potatoes', 'fr')).toBe('Potatoes');
    expect(trDonnee(null, 'ar')).toBe(null);
  });

  it('traduit les libellés miniers de l’USGS en français, pas en anglais', () => {
    expect(trDonnee('Crude oil', 'fr')).toBe('Pétrole brut');
    expect(trDonnee('Mine production, estimated', 'fr')).toBe('Production minière, estimée');
    expect(trDonnee('1000 b/d', 'fr')).toBe('milliers de barils/jour');
    expect(trDonnee('Crude oil', 'en')).toBe('Crude oil');
    expect(trDonnee('Crude oil', undefined)).toBe('Crude oil');
    expect(trDonnee('Crude oil', 'ar')).toBe('النفط الخام');
  });
});
