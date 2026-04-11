const OFFLINE_PREFIX = 'afcfta_offline_';
const syncCallbacks = [];

export const offlineService = {
  isOnline: () => navigator.onLine,

  saveForOffline: async (key, data) => {
    try {
      localStorage.setItem(OFFLINE_PREFIX + key, JSON.stringify({ data, savedAt: Date.now() }));
    } catch (e) {
      // localStorage may be full or unavailable
      console.warn('[offline] saveForOffline failed:', e);
    }
  },

  getOfflineData: (key) => {
    try {
      const raw = localStorage.getItem(OFFLINE_PREFIX + key);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return parsed?.data ?? null;
    } catch {
      return null;
    }
  },

  removeOfflineData: (key) => {
    localStorage.removeItem(OFFLINE_PREFIX + key);
  },

  registerSyncCallback: (callback) => {
    if (typeof callback === 'function') syncCallbacks.push(callback);
  },

  init: () => {
    const handleOnline = () => {
      syncCallbacks.forEach((cb) => {
        try { cb(); } catch { /* ignore */ }
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', () => {
      // Offline detected — no action needed beyond event
    });

    return () => {
      window.removeEventListener('online', handleOnline);
    };
  },
};
