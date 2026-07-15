import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const PRODUCT_TYPES = [
  { value: 'export_credit', fr: 'Crédit export', en: 'Export credit' },
  { value: 'political_risk', fr: 'Risque politique', en: 'Political risk' },
  { value: 'performance_guarantee', fr: 'Garantie de performance', en: 'Performance guarantee' },
  { value: 'advance_payment', fr: 'Garantie de restitution', en: 'Advance payment' },
  { value: 'tender', fr: "Garantie d'appel d'offres", en: 'Tender guarantee' },
  { value: 'transport', fr: 'Assurance transport', en: 'Transport insurance' },
];

const texts = {
  fr: {
    title: '🛡️ Assurance Commerce Extérieur',
    subtitle: 'Devis de primes et comparaison des assureurs',
    countryLabel: 'Pays acheteur',
    amountLabel: 'Valeur du contrat (USD)',
    productLabel: 'Produit',
    sectorLabel: 'Secteur (optionnel)',
    submit: 'Obtenir un devis',
    submitBatch: 'Comparer tous les produits',
    loading: 'Calcul en cours…',
    error: 'Erreur',
    profile: 'Profil pays',
    riskLevel: 'Niveau de risque',
    insurers: 'Assureurs disponibles',
    products: 'Produits disponibles',
    quote: 'Devis',
    basePremium: 'Prime de base',
    finalPremium: 'Prime finale',
    coverage: 'Couverture',
    deductible: 'Franchise',
    adjustment: 'Ajustement risque',
    notes: 'Notes',
    comparison: 'Comparaison des produits',
    rating: 'Notation',
    capacity: 'Capacité',
  },
  en: {
    title: '🛡️ Trade Insurance',
    subtitle: 'Premium quotes and insurer comparison',
    countryLabel: 'Buyer country',
    amountLabel: 'Contract value (USD)',
    productLabel: 'Product',
    sectorLabel: 'Sector (optional)',
    submit: 'Get a quote',
    submitBatch: 'Compare all products',
    loading: 'Calculating…',
    error: 'Error',
    profile: 'Country profile',
    riskLevel: 'Risk level',
    insurers: 'Available insurers',
    products: 'Available products',
    quote: 'Quote',
    basePremium: 'Base premium',
    finalPremium: 'Final premium',
    coverage: 'Coverage',
    deductible: 'Deductible',
    adjustment: 'Risk adjustment',
    notes: 'Notes',
    comparison: 'Product comparison',
    rating: 'Rating',
    capacity: 'Capacity',
  },
};

export default function Insurance({ language = 'en' }) {
  const t = texts[language] || texts.en;
  const [countryCode, setCountryCode] = useState('DZ');
  const [amount, setAmount] = useState(500000);
  const [productType, setProductType] = useState('export_credit');
  const [sector, setSector] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [profile, setProfile] = useState(null);
  const [quote, setQuote] = useState(null);
  const [batch, setBatch] = useState(null);

  const fetchProfile = async (code) => {
    try {
      const res = await axios.get(`${API}/insurance/countries/${code.toUpperCase()}/profile`);
      if (res.data.success) setProfile(res.data.profile);
    } catch (err) {
      // profile is best-effort context; quote errors surface separately
      setProfile(null);
    }
  };

  const handleQuote = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setQuote(null);
    setBatch(null);

    try {
      await fetchProfile(countryCode);
      const res = await axios.post(`${API}/insurance/quote`, {
        country_code: countryCode.toUpperCase(),
        product_type: productType,
        contract_value_usd: parseFloat(amount),
        sector: sector || null,
      });
      if (res.data.success) {
        setQuote(res.data.quote);
      } else {
        setError(res.data.detail || t.error);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBatch = async () => {
    setLoading(true);
    setError(null);
    setQuote(null);
    setBatch(null);

    try {
      await fetchProfile(countryCode);
      const res = await axios.post(`${API}/insurance/quotes/batch`, {
        country_code: countryCode.toUpperCase(),
        contract_value_usd: parseFloat(amount),
      });
      if (res.data.success) {
        setBatch(res.data.quotes);
      } else {
        setError(res.data.detail || t.error);
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
          <form onSubmit={handleQuote} className="space-y-4">
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
                  min="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium">{t.productLabel}</label>
                <select
                  value={productType}
                  onChange={(e) => setProductType(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                >
                  {PRODUCT_TYPES.map((p) => (
                    <option key={p.value} value={p.value}>
                      {language === 'fr' ? p.fr : p.en}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium">{t.sectorLabel}</label>
                <input
                  type="text"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="manufacturing…"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? t.loading : t.submit}
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={loading}
                onClick={handleBatch}
                className="flex-1"
              >
                {t.submitBatch}
              </Button>
            </div>
          </form>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
              <p className="text-red-800">
                {t.error}: {error}
              </p>
            </div>
          )}

          {profile && (
            <Card className="mt-6 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-base">{t.profile}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>{t.riskLevel}:</span>
                  <Badge className="capitalize">{profile.risk_level}</Badge>
                </div>
                <div>
                  {t.insurers}: {profile.available_insurers?.length || 0}
                </div>
                <div>
                  {t.products}: {profile.available_products?.length || 0}
                </div>
                {profile.available_insurers?.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {profile.available_insurers.slice(0, 3).map((ins, i) => (
                      <li key={i} className="text-xs text-gray-700">
                        • {ins.name} ({t.rating}: {ins.credit_rating || 'N/A'}
                        {ins.total_capacity_usd_bn
                          ? `, ${t.capacity}: $${ins.total_capacity_usd_bn}bn`
                          : ''}
                        )
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          )}

          {quote && (
            <Card className="mt-4 bg-green-50 border-green-300">
              <CardHeader>
                <CardTitle className="text-base">{t.quote}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>{t.basePremium}:</span>
                  <strong>${quote.base_premium_usd?.toLocaleString()}</strong>
                </div>
                <div className="flex justify-between">
                  <span>{t.finalPremium}:</span>
                  <strong>${quote.final_premium_usd?.toLocaleString()}</strong>
                </div>
                <div className="flex justify-between">
                  <span>{t.coverage}:</span>
                  <span>${quote.coverage_usd?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t.deductible}:</span>
                  <span>${quote.deductible_usd?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t.adjustment}:</span>
                  <span>{quote.risk_adjustment_percent}%</span>
                </div>
                {quote.notes && (
                  <p className="text-xs text-gray-600 mt-2 italic">{quote.notes}</p>
                )}
              </CardContent>
            </Card>
          )}

          {batch && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-base">{t.comparison}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {Object.entries(batch)
                  .sort((a, b) => a[1].final_premium_usd - b[1].final_premium_usd)
                  .map(([type, q], i) => (
                    <div
                      key={type}
                      className={`p-2 rounded text-sm ${i === 0 ? 'bg-green-50' : 'bg-gray-50'}`}
                    >
                      <div className="flex justify-between">
                        <span className="font-medium capitalize">{type.replace('_', ' ')}</span>
                        <Badge variant={i === 0 ? 'default' : 'outline'}>
                          ${q.final_premium_usd?.toLocaleString()}
                        </Badge>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {t.coverage}: ${q.coverage_usd?.toLocaleString()}
                      </div>
                    </div>
                  ))}
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
