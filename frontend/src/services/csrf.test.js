import axios from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { csrfFetch, getCsrfToken, installAxiosCsrf } from './csrf';

const MUTATING_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

describe('CSRF request integration', () => {
  beforeEach(() => {
    document.cookie = 'csrf_token=test-token; Path=/';
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

  it('persists a token returned in the health response before mutation', async () => {
    document.cookie = 'csrf_token=; Path=/; Max-Age=0';
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'X-CSRF-Token': 'fresh-token' }),
    });

    await csrfFetch('/api/auth/register', { method: 'POST' });

    expect(document.cookie).toContain('csrf_token=fresh-token');
    const [healthUrl, healthOptions] = fetch.mock.calls[0];
    expect(healthUrl).toContain('_csrf=');
    expect(healthOptions.cache).toBe('no-store');
    expect(new Headers(healthOptions.headers).has('Cache-Control')).toBe(false);

    const [, options] = fetch.mock.calls[1];
    expect(options.headers.get('X-CSRF-Token')).toBe('fresh-token');
  });

  it('refreshes the token once when the server rejects a stale CSRF pair', async () => {
    document.cookie = 'csrf_token=stale-token; Path=/';
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'X-CSRF-Token': 'fresh-token' }),
    });

    let attempts = 0;
    const instance = axios.create({
      adapter: async (config) => {
        attempts += 1;
        if (attempts === 1) {
          return Promise.reject({
            config,
            response: {
              status: 403,
              data: { detail: 'CSRF token missing' },
            },
          });
        }
        return {
          data: { status: 'ok' },
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        };
      },
    });
    installAxiosCsrf(instance);

    const response = await instance.post('/api/auth/register', {});

    expect(attempts).toBe(2);
    expect(response.config.headers.get('X-CSRF-Token')).toBe('fresh-token');
    expect(document.cookie).toContain('csrf_token=fresh-token');
  });
});

describe('CSRF cookie SameSite attribute', () => {
  const originalLocation = window.location;

  function stubProtocol(protocol) {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, protocol },
      writable: true,
      configurable: true,
    });
  }

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    });
    vi.restoreAllMocks();
  });

  it('writes SameSite=None; Secure when served over HTTPS (iframe-safe)', async () => {
    stubProtocol('https:');
    const cookieSetter = vi.spyOn(document, 'cookie', 'set');
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'X-CSRF-Token': 'https-token' }),
    });

    // jsdom's own cookie jar enforces the Secure flag against the test
    // environment's real http:// origin regardless of the stubbed protocol
    // above, so the app's post-write readback can fail here even though the
    // correct attributes were assigned — assert on the written string itself
    // (captured before that readback runs) rather than the round trip.
    await getCsrfToken({ forceRefresh: true }).catch(() => {});

    const written = cookieSetter.mock.calls.map(([value]) => value).join(' | ');
    expect(written).toContain('SameSite=None; Secure; Partitioned');
  });

  it('writes SameSite=Lax without Secure over plain HTTP (local dev)', async () => {
    stubProtocol('http:');
    const cookieSetter = vi.spyOn(document, 'cookie', 'set');
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: new Headers({ 'X-CSRF-Token': 'http-token' }),
    });

    await getCsrfToken({ forceRefresh: true });

    const written = cookieSetter.mock.calls.map(([value]) => value).join(' | ');
    expect(written).toContain('SameSite=Lax');
    expect(written).not.toContain('Secure');
  });
});
