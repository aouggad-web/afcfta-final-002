// Setup global pour les tests Vitest + React Testing Library
import '@testing-library/jest-dom';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// Nettoie le DOM après chaque test pour éviter les fuites entre cas
afterEach(() => {
  cleanup();
});
