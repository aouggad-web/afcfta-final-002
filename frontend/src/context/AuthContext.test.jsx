import { describe, expect, it } from 'vitest';

import { formatApiErrorDetail } from './AuthContext';

describe('formatApiErrorDetail', () => {
  it('uses the supplied fallback for a blank API detail', () => {
    expect(formatApiErrorDetail('   ', 'Connexion impossible.')).toBe(
      'Connexion impossible.'
    );
  });

  it('keeps a non-empty API detail', () => {
    expect(formatApiErrorDetail('  Accès refusé  ', 'Erreur')).toBe('Accès refusé');
  });
});
