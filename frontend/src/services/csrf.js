import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const CSRF_COOKIE = 'csrf_token';
const CSRF_HEADER = 'X-CSRF-Token';
const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

let tokenRequest;

function readCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`;
  const cookie = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix));

  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null;
}

export async function getCsrfToken() {
  const cookieToken = readCookie(CSRF_COOKIE);
  if (cookieToken) return cookieToken;

  if (!tokenRequest) {
    tokenRequest = fetch(`${BACKEND_URL}/api/health`, {
      credentials: 'include',
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Unable to initialize CSRF protection (${response.status})`);
        }

        const token = readCookie(CSRF_COOKIE) || response.headers.get(CSRF_HEADER);
        if (!token) throw new Error('CSRF token was not provided by the server');
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
  instance.defaults.withCredentials = true;

  return instance.interceptors.request.use(async (config) => {
    const method = (config.method || 'get').toUpperCase();
    if (MUTATING_METHODS.has(method)) {
      const token = await getCsrfToken();
      if (config.headers?.set) {
        config.headers.set(CSRF_HEADER, token);
      } else {
        config.headers = { ...config.headers, [CSRF_HEADER]: token };
      }
    }
    config.withCredentials = true;
    return config;
  });
}

installAxiosCsrf();
