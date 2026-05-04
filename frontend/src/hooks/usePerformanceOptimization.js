/**
 * usePerformanceOptimization - Performance monitoring and PWA registration hook
 *
 * Provides:
 * - PWA service worker registration with update detection
 * - Cache statistics monitoring
 * - Performance metrics access
 * - Push notification subscription management
 * - Offline/online status tracking
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL
  ? `${process.env.REACT_APP_BACKEND_URL}/api`
  : '/api';

// ===========================================================================
// Service Worker / PWA hook
// ===========================================================================

/**
 * Registers the service worker and exposes update status.
 * Call `applyUpdate()` to reload the page with the new SW.
 */
export function usePWA() {
  const [swStatus, setSwStatus]         = useState('unsupported'); // registering | registered | updateAvailable | error | unsupported
  const [updateAvailable, setUpdateAvail] = useState(false);
  const waitingSwRef                    = useRef(null);

  useEffect(() => {
    if (!('serviceWorker' in navigator)) return;

    setSwStatus('registering');

    navigator.serviceWorker
      .register('/service-worker.js', { scope: '/' })
      .then((registration) => {
        setSwStatus('registered');

        // Listen for update available
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (
              newWorker.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              waitingSwRef.current = newWorker;
              setUpdateAvail(true);
            }
          });
        });

        // Check for updates periodically
        const updateInterval = setInterval(() => registration.update(), 60 * 60 * 1000);
        return () => clearInterval(updateInterval);
      })
      .catch((err) => {
        console.error('[PWA] Service worker registration failed:', err);
        setSwStatus('error');
      });
  }, []);

  const applyUpdate = useCallback(() => {
    if (waitingSwRef.current) {
      waitingSwRef.current.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  }, []);

  return { swStatus, updateAvailable, applyUpdate };
}

// ===========================================================================
// Online / Offline status hook
// ===========================================================================

export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const goOnline  = () => setIsOnline(true);
    const goOffline = () => setIsOnline(false);
    window.addEventListener('online',  goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online',  goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  return isOnline;
}

// ===========================================================================
// Push Notifications hook
// ===========================================================================

/**
 * Manages push notification permission and subscription.
 */
export function usePushNotifications() {
  const [permission, setPermission] = useState(
    'Notification' in window ? Notification.permission : 'not_supported'
  );
  const [subscribed, setSubscribed] = useState(false);

  const requestPermission = useCallback(async () => {
    if (!('Notification' in window)) return 'not_supported';
    const result = await Notification.requestPermission();
    setPermission(result);
    return result;
  }, []);

  const subscribe = useCallback(async () => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return null;
    try {
      const registration = await navigator.serviceWorker.ready;
      // VAPID public key would come from server config in production
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        // applicationServerKey: <base64-encoded VAPID public key>
      });
      setSubscribed(true);
      return subscription;
    } catch (err) {
      console.error('[Push] Subscription failed:', err);
      return null;
    }
  }, []);

  return { permission, subscribed, requestPermission, subscribe };
}

// ===========================================================================
// Cache Statistics hook
// ===========================================================================

/**
 * Polls the backend performance cache stats endpoint every `intervalMs`.
 */
export function useCacheStats(intervalMs = 60000) {
  const [stats, setStats]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/performance/cache/stats`);
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, intervalMs);
    return () => clearInterval(interval);
  }, [fetchStats, intervalMs]);

  return { stats, loading, error, refresh: fetchStats };
}

// ===========================================================================
// Performance Metrics hook
// ===========================================================================

export function usePerformanceMetrics() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/performance/metrics`)
      .then(({ data }) => { setMetrics(data); })
      .catch((err) => { setError(err.message); })
      .finally(() => { setLoading(false); });
  }, []);

  return { metrics, loading, error };
}
