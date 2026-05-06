import React from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";
import "./index.css";
import App from "./App";
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

  // monkey-patch fetch() so calls hitting the backend also include the key
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
        const headers = new Headers(init.headers || {});
        if (!headers.has('X-API-Key')) headers.set('X-API-Key', API_KEY);
        init = { ...init, headers };
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
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
