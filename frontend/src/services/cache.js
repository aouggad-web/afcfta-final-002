class ClientCacheService {
  constructor(maxSize = 100) {
    this.maxSize = maxSize;
    this._store = new Map();
    this._hits = 0;
    this._misses = 0;
  }

  get(key) {
    const entry = this._store.get(key);
    if (!entry) {
      this._misses += 1;
      return null;
    }
    if (Date.now() > entry.expiresAt) {
      this._store.delete(key);
      this._misses += 1;
      return null;
    }
    this._hits += 1;
    return entry.value;
  }

  set(key, value, ttlSeconds = 300) {
    if (this._store.size >= this.maxSize) {
      // Evict the oldest entry
      const firstKey = this._store.keys().next().value;
      this._store.delete(firstKey);
    }
    this._store.set(key, {
      value,
      expiresAt: Date.now() + ttlSeconds * 1000,
    });
  }

  delete(key) {
    this._store.delete(key);
  }

  clear() {
    this._store.clear();
    this._hits = 0;
    this._misses = 0;
  }

  getStats() {
    return {
      size: this._store.size,
      maxSize: this.maxSize,
      hits: this._hits,
      misses: this._misses,
      hitRate: this._hits + this._misses > 0
        ? ((this._hits / (this._hits + this._misses)) * 100).toFixed(1) + '%'
        : 'N/A',
    };
  }
}

export const clientCache = new ClientCacheService();

export const withCache = async (key, fetchFn, ttl = 300) => {
  const cached = clientCache.get(key);
  if (cached !== null) return cached;
  const data = await fetchFn();
  clientCache.set(key, data, ttl);
  return data;
};
