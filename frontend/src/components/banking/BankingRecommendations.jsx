import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const texts = {
  fr: {
    title: '🎯 Recommandations Intelligentes',
    subtitle: 'Recommandations complètes pour vos transactions (Option 1)',
    countryLabel: 'Pays partenaire',
    amountLabel: 'Montant (USD)',
    sectorLabel: 'Secteur (optionnel)',
    typeLabel: 'Type',
    submit: 'Analyser',
    loading: 'Analyse en cours…',
    error: 'Erreur',
    noData: 'Aucune donnée',
    instruments: 'Instruments recommandés',
    insurance: 'Assurance',
    banks: 'Banques',
    compliance: 'Conformité',
    risk: 'Risque pays',
    rating: 'Note',
    recommendation: 'Recommandation',
  },
  en: {
    title: '🎯 Intelligent Recommendations',
    subtitle: 'Complete recommendations for your transactions (Option 1)',
    countryLabel: 'Partner country',
    amountLabel: 'Amount (USD)',
    sectorLabel: 'Sector (optional)',
    typeLabel: 'Type',
    submit: 'Analyze',
    loading: 'Analyzing…',
    error: 'Error',
    noData: 'No data',
    instruments: 'Recommended instruments',
    insurance: 'Insurance',
    banks: 'Banks',
    compliance: 'Compliance',
    risk: 'Country risk',
    rating: 'Rating',
    recommendation: 'Recommendation',
  },
};

export default function BankingRecommendations({ language = 'en' }) {
  const t = texts[language] || texts.en;
  const [countryCode, setCountryCode] = useState('DZ');
  const [amount, setAmount] = useState(1000000);
  const [sector, setSector] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(
        `${API}/banking/recommendations`,
        {
          country_code: countryCode.toUpperCase(),
          amount_usd: parseFloat(amount),
          sector: sector || null,
          transaction_type: 'export',
        }
      );

      if (response.data.success) {
        setResult(response.data);
      } else {
        setError(response.data.detail || t.error);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{t.title}</CardTitle>
          <p className="text-sm text-gray-600">{t.subtitle}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium">{t.countryLabel}</label>
                <input
                  type="text"
                  maxLength="2"
                  value={countryCode}
                  onChange={(e) => setCountryCode(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="DZ"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">{t.amountLabel}</label>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  min="10000"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium">{t.sectorLabel}</label>
                <input
                  type="text"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="manufacturing, agriculture…"
                />
              </div>
            </div>
            <Button disabled={loading} className="w-full">
              {loading ? t.loading : t.submit}
            </Button>
          </form>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
              <p className="text-red-800">{t.error}: {error}</p>
            </div>
          )}

          {result && (
            <div className="mt-6 space-y-4">
              {/* Risk Profile */}
              <Card className="bg-blue-50">
                <CardHeader>
                  <CardTitle className="text-base">{t.risk}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span>{t.rating}:</span>
                    <Badge>{result.risk_profile?.rating}</Badge>
                  </div>
                  <div className="text-sm text-gray-600">
                    <div>Forex: {result.risk_profile?.forex_risk}</div>
                    <div>Political: {result.risk_profile?.political_risk}</div>
                  </div>
                </CardContent>
              </Card>

              {/* Instruments */}
              {result.instruments && result.instruments.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">{t.instruments}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {result.instruments.map((inst, i) => (
                      <div key={i} className="p-2 bg-gray-50 rounded">
                        <div className="font-medium">{inst.name}</div>
                        <div className="text-xs text-gray-600">
                          {inst.typical_cost_pct}% cost • {inst.risk_coverage} coverage
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Insurance */}
              {result.insurance && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">{t.insurance}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1 text-sm">
                      <div>
                        <strong>{result.insurance.product_name_en}</strong>
                      </div>
                      <div>Coverage: {result.insurance.coverage_percent}%</div>
                      <div>Rate: {result.insurance.typical_premium_rate_pct}%</div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Banks */}
              {result.banks && result.banks.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">{t.banks}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {result.banks.slice(0, 3).map((bank, i) => (
                      <div key={i} className="p-2 bg-gray-50 rounded">
                        <div className="font-medium">{bank.name}</div>
                        <div className="text-xs text-gray-600">
                          Score: {bank.recommendation_score}/10 • {bank.suitability}
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
