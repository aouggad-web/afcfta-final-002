const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const error = new Error(`API error ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
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
    apiFetch(`/api/v2/mobile/lookup?hs_code=${encodeURIComponent(hsCode)}&country=${encodeURIComponent(country)}`),
};
