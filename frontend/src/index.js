import React from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";
import "./index.css";
import App from "./App";
import 'leaflet/dist/leaflet.css';

// Inject default X-API-Key header for all backend calls (frontend-public key)
const _apiKey = process.env.REACT_APP_API_KEY;
if (_apiKey) {
  axios.defaults.headers.common['X-API-Key'] = _apiKey;

  // Monkey-patch window.fetch to also include the API key for /api/* calls
  const _backendUrl = process.env.REACT_APP_BACKEND_URL || '';
  const _origFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    try {
      const url = typeof input === 'string' ? input : input.url;
      const isApi = url && (url.startsWith('/api') || (_backendUrl && url.startsWith(`${_backendUrl}/api`)));
      if (isApi) {
        const headers = new Headers(init.headers || (typeof input !== 'string' ? input.headers : undefined));
        if (!headers.has('X-API-Key')) {
          headers.set('X-API-Key', _apiKey);
        }
        return _origFetch(input, { ...init, headers });
      }
    } catch (_) { /* fall through */ }
    return _origFetch(input, init);
  };
}

// Import i18n configuration
import './i18n';

// Import mobile responsive styles
import './styles/mobile.css';

// ZLECAF Design System v1.1
import './styles/design-system.css';

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
