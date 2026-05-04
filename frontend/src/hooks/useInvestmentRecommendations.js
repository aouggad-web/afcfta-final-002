/**
 * useInvestmentRecommendations - Hook for AI-powered investment recommendations
 *
 * Fetches personalized investment recommendations from the AI Intelligence Engine.
 * Results are cached in component state and refreshed when user profile changes.
 *
 * Usage:
 *   const { recommendations, loading, error, refresh } =
 *     useInvestmentRecommendations({ sector: 'manufacturing', riskTolerance: 'medium' });
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL
  ? `${process.env.REACT_APP_BACKEND_URL}/api`
  : '/api';

/**
 * @param {object} userProfile - { sector, riskTolerance, preferredRegions, investmentSizePref }
 * @param {number} limit        - Maximum recommendations to return (default 10)
 * @param {object} options      - { autoFetch: boolean (default true) }
 */
export function useInvestmentRecommendations(userProfile = {}, limit = 10, options = {}) {
  const { autoFetch = true } = options;

  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading]                 = useState(false);
  const [error, setError]                     = useState(null);
  const [lastFetched, setLastFetched]         = useState(null);

  const abortRef = useRef(null);

  const fetch = useCallback(async (profile = userProfile) => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE}/ai-intelligence/recommendations`,
        {
          sector:               profile.sector            || 'general',
          risk_tolerance:       profile.riskTolerance     || 'medium',
          preferred_regions:    profile.preferredRegions  || [],
          investment_size_pref: profile.investmentSizePref || 'medium',
          limit,
        },
        { signal: abortRef.current.signal }
      );

      const data = response.data;
      setRecommendations(data.recommendations || []);
      setLastFetched(new Date().toISOString());
    } catch (err) {
      if (axios.isCancel(err)) return;
      setError(err.response?.data?.detail || err.message || 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  }, [userProfile, limit]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (autoFetch) fetch();
    return () => abortRef.current?.abort();
  }, [fetch, autoFetch]);

  return {
    recommendations,
    loading,
    error,
    lastFetched,
    refresh: () => fetch(),
  };
}

/**
 * useInvestmentScore - Fetch investment score for a specific country/sector pair.
 */
export function useInvestmentScore(country, sector = 'general', investmentSize = 'medium') {
  const [score, setScore]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState(null);

  useEffect(() => {
    if (!country) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    axios.post(`${API_BASE}/ai-intelligence/score`, {
      country,
      sector,
      investment_size: investmentSize,
    })
      .then((res) => { if (!cancelled) setScore(res.data); })
      .catch((err) => {
        if (!cancelled) setError(err.response?.data?.detail || err.message);
      })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [country, sector, investmentSize]);

  return { score, loading, error };
}

/**
 * useBulkInvestmentScore - Fetch scores for multiple countries simultaneously.
 */
export function useBulkInvestmentScore(countries = [], sector = 'general') {
  const [scores, setScores]   = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => {
    if (!countries.length) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    axios.post(`${API_BASE}/ai-intelligence/bulk-score`, { countries, sector })
      .then((res) => { if (!cancelled) setScores(res.data.scores || []); })
      .catch((err) => {
        if (!cancelled) setError(err.response?.data?.detail || err.message);
      })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [countries, sector]); // eslint-disable-line react-hooks/exhaustive-deps

  return { scores, loading, error };
}
