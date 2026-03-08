/**
 * useRealTimeData - WebSocket hook for real-time AfCFTA platform data
 *
 * Connects to the AfCFTA WebSocket channels and exposes live data as
 * React state. Reconnects automatically on disconnect.
 *
 * Usage:
 *   const { data, status, error } = useRealTimeData('regional_metrics', { bloc: 'EAC' });
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE = (() => {
  const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
  if (!backendUrl) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}`;
  }
  return backendUrl.replace(/^http/, 'ws');
})();

const CHANNEL_PATHS = {
  investment_alerts:    '/api/ws/investment-alerts',
  tariff_updates:       '/api/ws/tariff-updates',
  regional_metrics:     '/api/ws/regional-metrics',
  system_notifications: '/api/ws/system-notifications',
};

const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;
const PING_INTERVAL_MS = 25000;

/**
 * @param {string} channel - One of the CHANNEL_PATHS keys
 * @param {object} params  - Query parameters for the WebSocket URL
 * @param {object} options - { enabled: boolean, onMessage: fn }
 */
export function useRealTimeData(channel, params = {}, options = {}) {
  const { enabled = true, onMessage } = options;

  const [data, setData]     = useState(null);
  const [status, setStatus] = useState('disconnected'); // connecting | connected | disconnected | error
  const [error, setError]   = useState(null);

  const wsRef             = useRef(null);
  const reconnectRef      = useRef(0);
  const pingIntervalRef   = useRef(null);
  const mountedRef        = useRef(true);

  const buildUrl = useCallback(() => {
    const path = CHANNEL_PATHS[channel];
    if (!path) return null;
    const qs = Object.entries(params)
      .filter(([, v]) => v !== null && v !== undefined)
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    return `${WS_BASE}${path}${qs ? '?' + qs : ''}`;
  }, [channel, params]); // eslint-disable-line react-hooks/exhaustive-deps

  const connect = useCallback(() => {
    if (!enabled || !mountedRef.current) return;

    const url = buildUrl();
    if (!url) {
      setError(`Unknown channel: ${channel}`);
      setStatus('error');
      return;
    }

    setStatus('connecting');
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      reconnectRef.current = 0;
      setStatus('connected');
      setError(null);

      // Heartbeat
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, PING_INTERVAL_MS);
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'pong' || msg.type === 'connection_ack') return;
        setData(msg);
        if (onMessage) onMessage(msg);
      } catch {
        /* ignore malformed messages */
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setError('WebSocket connection error');
      setStatus('error');
    };

    ws.onclose = () => {
      clearInterval(pingIntervalRef.current);
      if (!mountedRef.current) return;
      setStatus('disconnected');

      if (reconnectRef.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectRef.current += 1;
        const delay = RECONNECT_DELAY_MS * reconnectRef.current;
        setTimeout(connect, delay);
      }
    };
  }, [buildUrl, channel, enabled, onMessage]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearInterval(pingIntervalRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const send = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  return { data, status, error, send };
}

/**
 * Convenience hook for investment alerts channel.
 */
export function useInvestmentAlerts({ userId, sector, riskTolerance } = {}) {
  return useRealTimeData('investment_alerts', { user_id: userId, sector, risk_tolerance: riskTolerance });
}

/**
 * Convenience hook for live regional metrics.
 */
export function useLiveRegionalMetrics(bloc, intervalSeconds = 30) {
  return useRealTimeData('regional_metrics', { bloc, interval_s: intervalSeconds });
}
