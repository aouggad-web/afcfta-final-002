import React from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";
import "./index.css";
import App from "./App";
import AdminProjectsPage from "./components/admin/AdminProjectsPage";

// Light/dark theme bootstrap (also applied in App for non-admin routes)
const _persistedTheme = localStorage.getItem('zlecaf_theme') || 'dark';
if (_persistedTheme === 'light') {
  document.documentElement.classList.add('theme-light');
  document.body.classList.add('theme-light');
}
import 'leaflet/dist/leaflet.css';

// Import i18n configuration
import './i18n';

// Import mobile responsive styles
import './styles/mobile.css';

// ZLECAF Design System v1.1
import './styles/design-system.css';

// --- Inject X-API-Key on every backend request ----------------------------
const API_KEY = process.env.REACT_APP_API_KEY || '';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

if (API_KEY) {
  // axios default header
  axios.defaults.headers.common['X-API-Key'] = API_KEY;

  // monkey-patch fetch() so calls hitting the backend also include the key.
  // Components that pass their own X-API-Key (e.g. admin pages) win — we never
  // override a header that's already set.
  const _origFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    try {
      const url =
        typeof input === 'string'
          ? input
          : input && input.url
          ? input.url
          : '';
      const isBackend =
        url.startsWith('/api') ||
        (BACKEND_URL && url.startsWith(BACKEND_URL));
      if (isBackend) {
        // Detect existing X-API-Key (case-insensitive) from raw init.headers.
        let hasKey = false;
        const rawHeaders = init.headers;
        if (rawHeaders) {
          if (rawHeaders instanceof Headers) {
            hasKey = rawHeaders.has('X-API-Key');
          } else if (Array.isArray(rawHeaders)) {
            hasKey = rawHeaders.some(([k]) => String(k).toLowerCase() === 'x-api-key');
          } else if (typeof rawHeaders === 'object') {
            hasKey = Object.keys(rawHeaders).some(
              (k) => k.toLowerCase() === 'x-api-key'
            );
          }
        }
        if (!hasKey) {
          const headers = new Headers(rawHeaders || {});
          headers.set('X-API-Key', API_KEY);
          init = { ...init, headers };
        }
      }
    } catch (_) {
      /* noop */
    }
    return _origFetch(input, init);
  };
}
// --------------------------------------------------------------------------

// Fix complet pour ResizeObserver errors
// Supprime complètement les erreurs ResizeObserver
window.addEventListener('error', e => {
  if (e.message === 'ResizeObserver loop limit exceeded' || 
      e.message === 'ResizeObserver loop completed with undelivered notifications.') {
    const resizeObserverErrDiv = document.getElementById('webpack-dev-server-client-overlay-div');
    const resizeObserverErr = document.getElementById('webpack-dev-server-client-overlay');
    if (resizeObserverErr) {
      resizeObserverErr.setAttribute('style', 'display: none');
    }
    if (resizeObserverErrDiv) {
      resizeObserverErrDiv.setAttribute('style', 'display: none');
    }
    e.stopImmediatePropagation();
    e.preventDefault();
  }
});

// Patch global pour ResizeObserver
const debounce = (callback, delay) => {
  let tid;
  return function (...args) {
    const ctx = this;
    tid && clearTimeout(tid);
    tid = setTimeout(() => {
      callback.apply(ctx, args);
    }, delay);
  };
};

const _ = window.ResizeObserver;
window.ResizeObserver = class ResizeObserver extends _ {
  constructor(callback) {
    callback = debounce(callback, 20);
    super(callback);
  }
};

// Register PWA Service Worker
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js', { scope: '/' })
      .then((registration) => {
        console.log('[PWA] Service worker registered:', registration.scope);
      })
      .catch((err) => {
        console.warn('[PWA] Service worker registration failed:', err);
      });
  });
}

const root = ReactDOM.createRoot(document.getElementById("root"));
const isAdminProjectsRoute = window.location.pathname.startsWith('/admin/projects');
root.render(
  isAdminProjectsRoute
    ? <AdminProjectsPage />
    : <React.StrictMode><App /></React.StrictMode>
);
