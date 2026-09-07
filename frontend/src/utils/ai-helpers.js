export const aiHelpers = {
  formatConfidenceScore: (score) => {
    if (score == null || isNaN(score)) return 'N/A';
    const pct = Math.round(Number(score) * 100);
    return `${pct}%`;
  },

  getScoreColor: (score) => {
    const val = Number(score);
    if (val >= 0.8) return 'text-green-600';
    if (val >= 0.6) return 'text-yellow-600';
    return 'text-red-500';
  },

  formatROI: (roiString) => {
    if (!roiString) return 'N/A';
    const num = parseFloat(String(roiString).replace(/[^0-9.-]/g, ''));
    if (isNaN(num)) return roiString;
    return `${num > 0 ? '+' : ''}${num.toFixed(1)}%`;
  },

  getRiskLabel: (riskLevel) => {
    const labels = {
      low: { en: 'Low Risk', fr: 'Risque Faible', color: 'text-green-600 bg-green-50' },
      medium: { en: 'Medium Risk', fr: 'Risque Moyen', color: 'text-yellow-600 bg-yellow-50' },
      high: { en: 'High Risk', fr: 'Risque Élevé', color: 'text-red-600 bg-red-50' },
    };
    return labels[String(riskLevel).toLowerCase()] || { en: riskLevel, fr: riskLevel, color: 'text-gray-600 bg-gray-50' };
  },

  formatInvestmentSize: (amount) => {
    const num = Number(amount);
    if (isNaN(num)) return String(amount);
    if (num >= 1_000_000_000) return `$${(num / 1_000_000_000).toFixed(1)}B`;
    if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `$${(num / 1_000).toFixed(1)}K`;
    return `$${num}`;
  },
};
