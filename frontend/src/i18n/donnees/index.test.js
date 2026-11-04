import { describe, it, expect } from 'vitest';
import { trDonnee } from './index';

describe('trDonnee', () => {
  it('laisse le texte intact hors arabe et quand il est inconnu', () => {
    expect(trDonnee('Texte inconnu', 'ar')).toBe('Texte inconnu');
    expect(trDonnee('Potatoes', 'fr')).toBe('Potatoes');
    expect(trDonnee(null, 'ar')).toBe(null);
  });
});
