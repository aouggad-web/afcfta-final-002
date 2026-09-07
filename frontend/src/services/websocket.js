const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

class WebSocketService {
  constructor() {
    this.connections = {};
    this.listeners = {};
    this._reconnectAttempts = {};
  }

  connect(channel, url) {
    if (this.connections[channel]?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);
      this.connections[channel] = ws;
      this._reconnectAttempts[channel] = this._reconnectAttempts[channel] || 0;

      ws.onmessage = (event) => {
        try {
          const { type, data } = JSON.parse(event.data);
          const channelListeners = this.listeners[channel]?.[type] || [];
          channelListeners.forEach((cb) => cb(data));
        } catch (err) {
          console.debug('[ws] malformed message on channel', channel, ':', event.data, err);
        }
      };

      ws.onopen = () => {
        this._reconnectAttempts[channel] = 0;
      };

      ws.onclose = () => {
        if (
          this._reconnectAttempts[channel] < MAX_RECONNECT_ATTEMPTS &&
          this.connections[channel] !== null
        ) {
          this._reconnectAttempts[channel] += 1;
          setTimeout(() => this.connect(channel, url), RECONNECT_DELAY_MS);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // WebSocket not available or bad URL — fail silently
    }
  }

  subscribe(channel, eventType, callback) {
    if (!this.listeners[channel]) this.listeners[channel] = {};
    if (!this.listeners[channel][eventType]) this.listeners[channel][eventType] = [];
    this.listeners[channel][eventType].push(callback);
  }

  unsubscribe(channel, eventType, callback) {
    const listeners = this.listeners[channel]?.[eventType];
    if (!listeners) return;
    this.listeners[channel][eventType] = listeners.filter((cb) => cb !== callback);
  }

  disconnect(channel) {
    const ws = this.connections[channel];
    if (ws) {
      this.connections[channel] = null;
      ws.close();
    }
    delete this.listeners[channel];
    delete this._reconnectAttempts[channel];
  }

  disconnectAll() {
    Object.keys(this.connections).forEach((channel) => this.disconnect(channel));
  }
}

export const wsService = new WebSocketService();

export const WS_CHANNELS = {
  TARIFF_UPDATES: 'tariff_updates',
  INVESTMENT_ALERTS: 'investment_alerts',
  TRADE_STATS: 'trade_stats',
  NEWS_FEED: 'news_feed',
  PORT_STATUS: 'port_status',
};
