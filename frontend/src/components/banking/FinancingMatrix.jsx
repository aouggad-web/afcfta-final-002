import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const texts = {
  fr: {
    title: '💰 Matrice Financement',
    subtitle: 'Analyse comparative et optimisation (Option 4)',
    countryLabel: 'Pays',
    amountLabel: 'Montant (USD)',
    submit: 'Analyser',
    loading: 'Analyse en cours…',
    error: 'Erreur',
    costBenefit: 'Analyse Coûts-Bénéfices',
    instrument: 'Instrument',
    cost: 'Coût',
    protection: 'Protection',
    netBenefit: 'Bénéfice net',
    roi: 'ROI',
    recommendation: 'Recommandation',
    instruments: 'Tous les instruments',
    riskMatrix: 'Matrice par risque',
    sizeMatrix: 'Matrice par taille',
    tabs: {
      comparison: 'Comparaison',
      costBenefit: 'Coûts-Bénéfices',
      riskMatrix: 'Risque',
      sizeMatrix: 'Taille',
    },
  },
  en: {
    title: '💰 Financing Matrix',
    subtitle: 'Comparative analysis and optimization (Option 4)',
    countryLabel: 'Country',
    amountLabel: 'Amount (USD)',
    submit: 'Analyze',
    loading: 'Analyzing…',
    error: 'Error',
    costBenefit: 'Cost-Benefit Analysis',
    instrument: 'Instrument',
    cost: 'Cost',
    protection: 'Protection',
    netBenefit: 'Net benefit',
    roi: 'ROI',
    recommendation: 'Recommendation',
    instruments: 'All instruments',
    riskMatrix: 'Risk matrix',
    sizeMatrix: 'Size matrix',
    tabs: {
      comparison: 'Comparison',
      costBenefit: 'Cost-Benefit',
      riskMatrix: 'Risk',
      sizeMatrix: 'Size',
    },
  },
};

export default function FinancingMatrix({ language = 'en' }) {
  const t = texts[language] || texts.en;
  const [countryCode, setCountryCode] = useState('NG');
  const [amount, setAmount] = useState(1000000);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('costBenefit');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const [costBenefit, instruments, riskMatrix, sizeMatrix] = await Promise.all([
        axios.post(`${API}/banking/finance/matrix/cost-benefit`, null, {
          params: {
            country_code: countryCode.toUpperCase(),
            amount_usd: parseFloat(amount),
          },
        }),
        axios.get(`${API}/banking/finance/matrix/instruments`),
        axios.get(`${API}/banking/finance/matrix/by-risk`),
        axios.get(`${API}/banking/finance/matrix/by-size`),
      ]);

      setResult({
        costBenefit: costBenefit.data,
        instruments: instruments.data,
        riskMatrix: riskMatrix.data,
        sizeMatrix: sizeMatrix.data,
      });
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
                  placeholder="NG"
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
            <div className="mt-6">
              {/* Tabs */}
              <div className="flex gap-2 mb-4 border-b">
                {Object.entries(t.tabs).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key)}
                    className={`px-4 py-2 text-sm ${
                      activeTab === key
                        ? 'border-b-2 border-blue-500 font-semibold'
                        : 'text-gray-600 hover:text-gray-800'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {/* Cost-Benefit Tab */}
              {activeTab === 'costBenefit' && result.costBenefit?.analysis && (
                <div className="space-y-2">
                  {Object.entries(result.costBenefit.analysis)
                    .sort(
                      (a, b) =>
                        (b[1].net_benefit_usd || 0) - (a[1].net_benefit_usd || 0)
                    )
                    .slice(0, 5)
                    .map(([code, inst], i) => (
                      <Card key={code} className={i === 0 ? 'bg-green-50' : ''}>
                        <CardContent className="pt-4">
                          <div className="flex justify-between items-start mb-2">
                            <div className="font-semibold">{inst.instrument}</div>
                            <Badge variant={i === 0 ? 'default' : 'outline'}>
                              ROI: {inst.roi_pct}%
                            </Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                            <div>{t.cost}: ${inst.total_cost_usd.toLocaleString()}</div>
                            <div>Protection: ${inst.risk_protection_value_usd.toLocaleString()}</div>
                            <div>{t.netBenefit}: ${inst.net_benefit_usd.toLocaleString()}</div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                </div>
              )}

              {/* Risk Matrix Tab */}
              {activeTab === 'riskMatrix' && result.riskMatrix?.matrix && (
                <div className="space-y-3">
                  {['A1', 'A2', 'A3', 'A4', 'B', 'C', 'D'].map((risk) => {
                    const riskData = result.riskMatrix.matrix[risk];
                    if (!riskData) return null;
                    return (
                      <Card key={risk}>
                        <CardHeader>
                          <CardTitle className="text-sm">
                            Rating {risk}: {riskData.description}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-xs space-y-1">
                            {riskData.recommended_instruments?.map((inst) => (
                              <div key={inst.code}>
                                • {inst.name}: {inst.cost_pct}% cost
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}

              {/* Size Matrix Tab */}
              {activeTab === 'sizeMatrix' && result.sizeMatrix?.matrix && (
                <div className="space-y-3">
                  {Object.entries(result.sizeMatrix.matrix).map(([size, data]) => (
                    <Card key={size}>
                      <CardHeader>
                        <CardTitle className="text-sm">{size}</CardTitle>
                        <p className="text-xs text-gray-600">{data.size_range_usd}</p>
                      </CardHeader>
                      <CardContent>
                        <div className="text-xs space-y-1">
                          <div>
                            <strong>Instruments:</strong>{' '}
                            {data.recommended_instruments?.slice(0, 3).join(', ')}
                          </div>
                          <div>
                            <strong>Cost:</strong> {data.typical_cost_range_pct}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
