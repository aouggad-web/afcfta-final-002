import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const CSRF_COOKIE = 'csrf_token';
const CSRF_HEADER = 'X-CSRF-Token';
const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
const CSRF_ERRORS = new Set(['CSRF token missing', 'CSRF token invalid']);

let tokenRequest;

function readCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`;
  const cookie = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix));

  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null;
}

function persistReadableToken(token) {
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie =
    `${encodeURIComponent(CSRF_COOKIE)}=${encodeURIComponent(token)}` +
    `; Path=/; SameSite=Strict; Max-Age=3600${secure}`;
}

function setCsrfHeader(config, token) {
  if (config.headers?.set) {
    config.headers.set(CSRF_HEADER, token);
  } else {
    config.headers = { ...config.headers, [CSRF_HEADER]: token };
  }
}

function isCsrfRejection(error) {
  return (
    error.response?.status === 403 &&
    CSRF_ERRORS.has(error.response?.data?.detail)
  );
}

export async function getCsrfToken({ forceRefresh = false } = {}) {
  const cookieToken = readCookie(CSRF_COOKIE);
  if (cookieToken && !forceRefresh) return cookieToken;

  if (!tokenRequest) {
    const separator = `${BACKEND_URL}/api/health`.includes('?') ? '&' : '?';
    const healthUrl =
      `${BACKEND_URL}/api/health${separator}_csrf=${Date.now()}`;

    tokenRequest = fetch(healthUrl, {
      credentials: 'include',
      cache: 'no-store',
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Unable to initialize CSRF protection (${response.status})`);
        }

        const responseToken = response.headers.get(CSRF_HEADER);
        const token = responseToken || readCookie(CSRF_COOKIE);
        if (!token) throw new Error('CSRF token was not provided by the server');

        // Some preview/browser combinations expose the response header before
        // committing Set-Cookie. Persist the same non-secret double-submit
        // token so the next mutation sends a matching cookie and header.
        if (readCookie(CSRF_COOKIE) !== token) {
          persistReadableToken(token);
        }
        if (readCookie(CSRF_COOKIE) !== token) {
          throw new Error('CSRF cookie could not be initialized');
        }

        return token;
      })
      .finally(() => {
        tokenRequest = null;
      });
  }

  return tokenRequest;
}

export async function csrfFetch(input, init = {}) {
  const method = (init.method || 'GET').toUpperCase();
  const headers = new Headers(init.headers || {});

  if (MUTATING_METHODS.has(method)) {
    headers.set(CSRF_HEADER, await getCsrfToken());
  }

  return fetch(input, {
    ...init,
    credentials: 'include',
    headers,
  });
}

export function installAxiosCsrf(instance = axios) {
  const requestInterceptor = instance.interceptors.request.use(async (config) => {
    const method = (config.method || 'get').toUpperCase();
    if (MUTATING_METHODS.has(method)) {
      setCsrfHeader(config, await getCsrfToken());
    }
    config.withCredentials = true;
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const config = error.config;
      if (!config || config.__csrfRetried || !isCsrfRejection(error)) {
        return Promise.reject(error);
      }

      config.__csrfRetried = true;
      setCsrfHeader(config, await getCsrfToken({ forceRefresh: true }));
      config.withCredentials = true;
      return instance.request(config);
    }
  );

  return requestInterceptor;
}

installAxiosCsrf();
