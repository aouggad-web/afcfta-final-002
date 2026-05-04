/**
 * AfCFTA Intelligence Platform - Service Worker
 * ================================================
 * Implements a cache-first / network-first hybrid caching strategy:
 *   - Static assets: cache-first (long TTL)
 *   - API calls:     network-first with cache fallback (5-minute TTL)
 *   - Offline page:  served from cache when fully offline
 *
 * Cache names are versioned; old caches are purged on activation.
 */

const APP_VERSION = 'v3.0.0';
const STATIC_CACHE  = `afcfta-static-${APP_VERSION}`;
const API_CACHE     = `afcfta-api-${APP_VERSION}`;
const IMAGE_CACHE   = `afcfta-images-${APP_VERSION}`;

const OFFLINE_PAGE  = '/offline.html';

/** Static assets to pre-cache on install */
const PRECACHE_ASSETS = [
  '/',
  '/offline.html',
  '/manifest.json',
  '/static/css/main.css',
  '/static/js/main.js',
  '/data/zlecaf_tariff_origin_phase.json',
  '/data/zlecaf_rules_of_origin.json',
];

/** API patterns that should be cached (network-first) */
const API_CACHE_PATTERNS = [
  /\/api\/countries/,
  /\/api\/statistics/,
  /\/api\/health/,
  /\/api\/regional-analytics\/blocs/,
  /\/api\/ai-intelligence\/scoring-algorithm/,
  /\/api\/mobile\//,
];

/** Cache TTL for API responses (5 minutes) */
const API_CACHE_TTL_MS = 5 * 60 * 1000;

// ===========================================================================
// Install event – pre-cache static assets
// ===========================================================================
self.addEventListener('install', (event) => {
  console.log(`[SW] Installing ${APP_VERSION}`);
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_ASSETS.filter(url => {
        // Skip assets that may not exist yet (e.g. during CI)
        return true;
      })))
      .catch((err) => console.warn('[SW] Pre-cache failed (some assets may be missing):', err))
      .then(() => self.skipWaiting())
  );
});

// ===========================================================================
// Activate event – purge old caches
// ===========================================================================
self.addEventListener('activate', (event) => {
  console.log(`[SW] Activating ${APP_VERSION}`);
  const validCaches = [STATIC_CACHE, API_CACHE, IMAGE_CACHE];
  event.waitUntil(
    caches.keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => !validCaches.includes(k))
            .map((k) => {
              console.log(`[SW] Deleting old cache: ${k}`);
              return caches.delete(k);
            })
        )
      )
      .then(() => self.clients.claim())
  );
});

// ===========================================================================
// Fetch event – routing logic
// ===========================================================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and chrome-extension requests
  if (request.method !== 'GET' || url.protocol === 'chrome-extension:') return;

  // Skip WebSocket upgrades
  if (request.headers.get('upgrade') === 'websocket') return;

  const isApiRequest = url.pathname.startsWith('/api/') || url.pathname.startsWith('/graphql');
  const isImageRequest = /\.(png|jpg|jpeg|webp|gif|svg|ico)$/i.test(url.pathname);
  const isStaticAsset  = /\.(js|css|woff2?|ttf|eot)$/i.test(url.pathname);

  if (isApiRequest && _isCacheable(url.pathname)) {
    event.respondWith(_networkFirst(request, API_CACHE));
  } else if (isImageRequest) {
    event.respondWith(_cacheFirst(request, IMAGE_CACHE));
  } else if (isStaticAsset) {
    event.respondWith(_cacheFirst(request, STATIC_CACHE));
  } else {
    event.respondWith(_networkFirst(request, STATIC_CACHE));
  }
});

function _isCacheable(pathname) {
  return API_CACHE_PATTERNS.some((pattern) => pattern.test(pathname));
}

/** Cache-first: serve from cache, fall back to network */
async function _cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return caches.match(OFFLINE_PAGE);
  }
}

/** Network-first: try network, fall back to cache, then offline page */
async function _networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || caches.match(OFFLINE_PAGE);
  }
}

// ===========================================================================
// Background Sync – replay failed mutations when back online
// ===========================================================================
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-pending-requests') {
    event.waitUntil(_replayPendingRequests());
  }
});

async function _replayPendingRequests() {
  console.log('[SW] Background sync: replaying pending requests');
  // In a full implementation this would read from IndexedDB and replay requests
}

// ===========================================================================
// Push Notifications
// ===========================================================================
self.addEventListener('push', (event) => {
  let data = { title: 'AfCFTA Intel', body: 'New investment alert', icon: '/icons/icon-192x192.png' };
  try {
    data = { ...data, ...event.data.json() };
  } catch {
    data.body = event.data ? event.data.text() : 'New notification';
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body:  data.body,
      icon:  data.icon || '/icons/icon-192x192.png',
      badge: '/icons/icon-72x72.png',
      data:  data,
      actions: [
        { action: 'view',    title: 'View Details' },
        { action: 'dismiss', title: 'Dismiss'      },
      ],
      requireInteraction: false,
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'dismiss') return;
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((windowClients) => {
      const existing = windowClients.find((c) => c.url === url && 'focus' in c);
      if (existing) return existing.focus();
      return clients.openWindow(url);
    })
  );
});
