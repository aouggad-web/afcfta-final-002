import { describe, expect, it } from 'vitest';
import { shouldUseLegacyCalculator } from './calculatorFallback';

describe('calculator source fallback', () => {
  it('allows a legacy server with no authentic route', () => {
    expect(shouldUseLegacyCalculator({ response: {
      status: 404, data: { detail: 'Not Found' },
    } })).toBe(true);
  });

  it.each([400, 401, 403, 409, 422, 429, 500, 502, 503, 504])(
    'preserves HTTP %s instead of changing the calculation source', (status) => {
      expect(shouldUseLegacyCalculator({ response: {
        status, data: { detail: 'Not Found' },
      } })).toBe(false);
    },
  );

  it.each([
    { detail: { status: 'NOT_RECRAWLED' } },
    { detail: 'No tariff found for ZZZ/000000' },
    { detail: 'National position missing' },
    {},
  ])('does not treat unavailable data as a missing route: %j', (data) => {
    expect(shouldUseLegacyCalculator({ response: { status: 404, data } })).toBe(false);
  });

  it.each([undefined, {}, { code: 'ERR_NETWORK' }, { code: 'ECONNABORTED' }])(
    'preserves network and timeout failures', (error) => {
      expect(shouldUseLegacyCalculator(error)).toBe(false);
    },
  );
});
