import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const texts = {
  fr: {
    title: '💱 Stratégies de Couverture FX',
    subtitle: 'Recommandations de hedging (Option 3)',
    countryLabel: 'Pays',
    amountLabel: 'Montant (USD)',
    daysLabel: 'Horizon (jours)',
    submit: 'Analyser',
    loading: 'Analyse en cours…',
    error: 'Erreur',
    necessity: 'Nécessité',
    recommended: 'Recommandée',
    strategies: 'Stratégies classées',
    cost: 'Coût',
    effectiveness: 'Efficacité',
    netBenefit: 'Bénéfice net',
    explanation: 'Explication',
  },
  en: {
    title: '💱 FX Hedging Strategies',
    subtitle: 'Hedging recommendations for your transaction (Option 3)',
    countryLabel: 'Country',
    amountLabel: 'Amount (USD)',
    daysLabel: 'Horizon (days)',
    submit: 'Analyze',
    loading: 'Analyzing…',
    error: 'Error',
    necessity: 'Necessity',
    recommended: 'Recommended',
    strategies: 'Ranked strategies',
    cost: 'Cost',
    effectiveness: 'Effectiveness',
    netBenefit: 'Net benefit',
    explanation: 'Explanation',
  },
};

export default function FXHedging({ language = 'en' }) {
  const t = texts[language] || texts.en;
  const [countryCode, setCountryCode] = useState('DZ');
  const [amount, setAmount] = useState(1000000);
  const [days, setDays] = useState(90);
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
        `${API}/banking/forex/hedging-strategy`,
        {
          country_code: countryCode.toUpperCase(),
          amount_usd: parseFloat(amount),
          transaction_days: parseInt(days),
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
            <div className="grid grid-cols-3 gap-4">
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
              <div>
                <label className="block text-sm font-medium">{t.daysLabel}</label>
                <input
                  type="number"
                  value={days}
                  onChange={(e) => setDays(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  min="1"
                  max="730"
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
              {/* Necessity */}
              <Card className="bg-blue-50">
                <CardContent className="pt-4">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{t.necessity}:</span>
                    <Badge className="capitalize">
                      {result.hedging_necessity}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-700 mt-2">{result.explanation}</p>
                </CardContent>
              </Card>

              {/* Recommended Strategy */}
              {result.recommended_strategy && (
                <Card className="bg-green-50 border-green-300">
                  <CardHeader>
                    <CardTitle className="text-base">{t.recommended}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-lg font-semibold">{result.recommended_strategy}</div>
                  </CardContent>
                </Card>
              )}

              {/* All Strategies */}
              {result.all_strategies && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">{t.strategies}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {result.all_strategies.map((strat, i) => (
                      <div key={i} className="p-2 bg-gray-50 rounded text-sm">
                        <div className="font-medium">{strat.name}</div>
                        <div className="grid grid-cols-3 gap-2 mt-1 text-xs text-gray-600">
                          <div>{t.cost}: {strat.cost_pct}%</div>
                          <div>{t.effectiveness}: {strat.effectiveness_pct}%</div>
                          <div>{t.netBenefit}: {strat.net_benefit_pct}%</div>
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
