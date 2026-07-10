/**
 * useHsLabel - Resolves the official label of a HS (Harmonized System) code
 * as the user types it, via GET /api/hs-codes/label/{code}.
 *
 * Accepts 2, 4 or 6-digit codes (chapter / heading / sub-position). Debounced
 * so it doesn't fire on every keystroke, and self-cancels stale requests.
 *
 * Usage:
 *   const { label, loading } = useHsLabel(hsCode, language);
 *   {label && <span className="text-xs text-slate-400">{label}</span>}
 */

import { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL) || '';
const API = `${BACKEND_URL}/api`;

const VALID_LENGTHS = [2, 4, 6];

export function useHsLabel(hsCode, language = 'fr') {
  const [label, setLabel] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const clean = String(hsCode || '').replace(/\D/g, '');
    if (!VALID_LENGTHS.includes(clean.length)) {
      setLabel(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    const timer = setTimeout(() => {
      axios
        .get(`${API}/hs-codes/label/${clean}`, { signal: controller.signal })
        .then((res) => {
          const data = res.data || {};
          setLabel(language === 'en' ? data.label_en || data.label_fr : data.label_fr || data.label_en);
          setLoading(false);
        })
        .catch((err) => {
          // A request aborted by the next keystroke's cleanup is not a real
          // failure — its own effect run already owns `loading`/`label`, so
          // updating state here would race it back to a stale value.
          if (axios.isCancel(err)) return;
          setLabel(null);
          setLoading(false);
        });
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [hsCode, language]);

  return { label, loading };
}

export default useHsLabel;
