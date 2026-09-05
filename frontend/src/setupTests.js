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
if (!window.PointerEvent) {
  // jsdom has no PointerEvent; Radix branches on pointer-specific metadata
  // (pointerType/pointerId/isPrimary), so a bare MouseEvent alias would
  // silently take the wrong code path in components under test.
  class PointerEventPolyfill extends MouseEvent {
    constructor(type, params = {}) {
      super(type, params);
      this.pointerId = params.pointerId ?? 1;
      this.pointerType = params.pointerType ?? 'mouse';
      this.isPrimary = params.isPrimary ?? true;
    }
  }
  window.PointerEvent = PointerEventPolyfill;
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

// Nettoie le DOM après chaque test pour éviter les fuites entre cas
afterEach(() => {
  cleanup();
});
