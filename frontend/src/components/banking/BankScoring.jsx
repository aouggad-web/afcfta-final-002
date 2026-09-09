import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const texts = {
  fr: {
    title: '🏦 Scoring Bancaire Avancé',
    subtitle: 'Score et classement des banques (Option 2)',
    countryLabel: 'Pays',
    amountLabel: 'Montant (USD)',
    typeLabel: 'Type',
    submit: 'Évaluer',
    loading: 'Évaluation en cours…',
    error: 'Erreur',
    banks: 'Banques classées',
    score: 'Score',
    suitability: 'Aptitude',
    strengths: 'Points forts',
    services: 'Services',
    correspondents: 'Correspondants',
  },
  en: {
    title: '🏦 Advanced Bank Scoring',
    subtitle: 'Score and rank banks for your transaction (Option 2)',
    countryLabel: 'Country',
    amountLabel: 'Amount (USD)',
    typeLabel: 'Type',
    submit: 'Evaluate',
    loading: 'Evaluating…',
    error: 'Error',
    banks: 'Ranked banks',
    score: 'Score',
    suitability: 'Suitability',
    strengths: 'Strengths',
    services: 'Services',
    correspondents: 'Correspondents',
  },
};

export default function BankScoring({ language = 'en' }) {
  const t = texts[language] || texts.en;
  const [countryCode, setCountryCode] = useState('NG');
  const [amount, setAmount] = useState(1000000);
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
        `${API}/banking/banks/score`,
        {
          country_code: countryCode.toUpperCase(),
          amount_usd: parseFloat(amount),
          transaction_type: 'export',
          limit: 5,
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
            <div className="mt-6 space-y-3">
              <div className="text-sm text-gray-600">
                {t.banks}: <strong>{result.banks_scored}</strong>
              </div>

              {result.banks && result.banks.map((bank, i) => (
                <Card key={i} className={i === 0 ? 'border-green-300 bg-green-50' : ''}>
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold">{bank.name}</div>
                          <div className="text-xs text-gray-600">{bank.abbreviation}</div>
                        </div>
                        <Badge variant={i === 0 ? 'default' : 'outline'}>
                          {bank.score}/10
                        </Badge>
                      </div>

                      <div className="text-sm">
                        <div className="text-gray-700">
                          {t.suitability}: <strong>{bank.suitability_level}</strong>
                        </div>
                      </div>

                      {bank.key_strengths && (
                        <div className="text-xs bg-white p-2 rounded border">
                          <strong>{t.strengths}:</strong>
                          <ul className="mt-1 space-y-1">
                            {bank.key_strengths.map((s, j) => (
                              <li key={j}>• {s}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {bank.correspondents_count > 0 && (
                        <div className="text-xs text-gray-600">
                          {t.correspondents}: {bank.correspondents_count}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
