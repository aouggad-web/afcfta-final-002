const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

/**
 * Default request timeout in milliseconds.
 */
const DEFAULT_TIMEOUT_MS = 30000;

/**
 * Enhanced API fetch with timeout, detailed error handling, and content-type validation.
 */
async function apiFetch(path, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      signal: controller.signal,
      ...options,
    });

    if (!response.ok) {
      let message = `API error ${response.status}`;
      try {
        const body = await response.json();
        if (body?.detail) {
          message = Array.isArray(body.detail)
            ? body.detail.map((d) => d.msg || d).join('; ')
            : String(body.detail);
        }
      } catch {
        // ignore JSON parse errors on error responses
      }
      const error = new Error(message);
      error.status = response.status;
      throw error;
    }

    // Reject HTML responses (e.g. SPA 404 fallback pages)
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('text/html')) {
      const error = new Error('Received HTML instead of JSON – is the backend running?');
      error.status = 0;
      throw error;
    }

    return response.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      const error = new Error(`Request timed out after ${timeoutMs / 1000}s`);
      error.status = 408;
      throw error;
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

export const apiV2 = {
  comprehensiveSearch: (query, filters = {}, pagination = { page: 1, limit: 10 }) =>
    apiFetch('/api/v2/search/comprehensive', {
      method: 'POST',
      body: JSON.stringify({ query, filters, pagination }),
    }),

  bulkTariffCalculation: (products, routes) =>
    apiFetch('/api/v2/tariffs/bulk', {
      method: 'POST',
      body: JSON.stringify({ products, routes }),
    }),

  bulkInvestmentAnalysis: (opportunities, criteria) =>
    apiFetch('/api/v2/investment/bulk-analysis', {
      method: 'POST',
      body: JSON.stringify({ opportunities, criteria }),
    }),

  getDashboardAnalytics: () => apiFetch('/api/v2/analytics/dashboard'),

  getAIRecommendations: (userProfile) =>
    apiFetch('/api/v2/ai/recommendations', {
      method: 'POST',
      body: JSON.stringify({ userProfile }),
    }),

  mobileQuickLookup: (hsCode, country) =>
    apiFetch(
      `/api/v2/mobile/lookup?hs_code=${encodeURIComponent(hsCode)}&country=${encodeURIComponent(country)}`
    ),
};
