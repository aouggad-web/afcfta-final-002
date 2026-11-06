import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
// En HTTPS, le serveur nomme le cookie __Host-csrf_token (audit INFO-4,
// backend/middlewares/csrf_protection.py) : le navigateur refuse alors tout
// cookie de ce nom posé par un sous-domaine ou une réponse http. Le préfixe
// exige Secure, d'où csrf_token en http local. Calculé à chaque appel.
function csrfCookieName() {
  return window.location.protocol === 'https:' ? '__Host-csrf_token' : 'csrf_token';
}
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
  // SameSite=None (not Strict): the app can be viewed inside the Emergent
  // preview iframe, where the top-level document is a different site — a
  // Strict cookie would be dropped for our own origin's fetches there.
  // SameSite=None requires Secure, so it only applies over HTTPS; plain HTTP
  // (local dev) falls back to Lax, which still works same-site.
  // Partitioned (CHIPS) is also required in that iframe case: Chrome's
  // third-party cookie phase-out drops SameSite=None cookies without it.
  const isHttps = window.location.protocol === 'https:';
  const attrs = isHttps ? 'SameSite=None; Secure; Partitioned' : 'SameSite=Lax';
  document.cookie =
    `${encodeURIComponent(csrfCookieName())}=${encodeURIComponent(token)}` +
    `; Path=/; ${attrs}; Max-Age=3600`;
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
  const cookieToken = readCookie(csrfCookieName());
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
        const token = responseToken || readCookie(csrfCookieName());
        if (!token) throw new Error('CSRF token was not provided by the server');

        // Some preview/browser combinations expose the response header before
        // committing Set-Cookie. Persist the same non-secret double-submit
        // token so the next mutation sends a matching cookie and header.
        if (readCookie(csrfCookieName()) !== token) {
          persistReadableToken(token);
        }
        if (readCookie(csrfCookieName()) !== token) {
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

async function isCsrfRejectionResponse(response) {
  if (response.status !== 403) return false;
  try {
    const body = await response.clone().json();
    return CSRF_ERRORS.has(body?.detail);
  } catch {
    return false;
  }
}

export async function csrfFetch(input, init = {}) {
  const method = (init.method || 'GET').toUpperCase();
  const headers = new Headers(init.headers || {});
  const mutating = MUTATING_METHODS.has(method);

  if (mutating) {
    headers.set(CSRF_HEADER, await getCsrfToken());
  }

  const send = () => fetch(input, { ...init, credentials: 'include', headers });
  const response = await send();

  // Une seule relance après un refus CSRF, comme l'intercepteur axios : un
  // jeton périmé ou un cookie d'avant un changement de nom se réamorcent.
  if (mutating && (await isCsrfRejectionResponse(response))) {
    headers.set(CSRF_HEADER, await getCsrfToken({ forceRefresh: true }));
    return send();
  }
  return response;
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
