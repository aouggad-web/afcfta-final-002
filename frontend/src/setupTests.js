// Setup global pour les tests Vitest + React Testing Library
import '@testing-library/jest-dom';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// jsdom n'implémente pas ces API DOM utilisées par Radix UI (Select, etc.) ;
// sans ces stubs, tout test cliquant un <Select> Radix lève une TypeError.
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = () => false;
}
if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = () => {};
}
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = () => {};
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

// Nettoie le DOM après chaque test pour éviter les fuites entre cas
afterEach(() => {
  cleanup();
});
