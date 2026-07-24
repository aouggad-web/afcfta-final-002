import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { csrfFetch, installAxiosCsrf } from './csrf';

const MUTATING_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

describe('CSRF request integration', () => {
  beforeEach(() => {
    document.cookie = 'csrf_token=test-token';
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }));
  });

  it.each(MUTATING_METHODS)('adds the CSRF token to %s fetch calls', async (method) => {
    await csrfFetch('/api/resource', { method });

    const [, options] = fetch.mock.calls[0];
    expect(options.credentials).toBe('include');
    expect(options.headers.get('X-CSRF-Token')).toBe('test-token');
  });

  it.each(MUTATING_METHODS)('adds the CSRF token to %s axios calls', async (method) => {
    const instance = axios.create({
      adapter: async (config) => ({
        data: {},
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      }),
    });
    installAxiosCsrf(instance);

    const response = await instance.request({ url: '/api/resource', method });

    expect(response.config.withCredentials).toBe(true);
    expect(response.config.headers.get('X-CSRF-Token')).toBe('test-token');
  });
});
