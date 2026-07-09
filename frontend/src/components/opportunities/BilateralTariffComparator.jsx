import React, { useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { ArrowLeftRight, Scale, TrendingDown, Info } from 'lucide-react';
import { getAllCountries } from '../../utils/countryCodes';
import { useHsLabel } from '../../hooks/useHsLabel';

const TEXTS = {
  fr: {
    title: 'Comparateur tarifaire bilatéral',
    subtitle: 'Traitement tarifaire d’un produit dans les deux sens d’une paire de pays',
    countryA: 'Pays A',
    countryB: 'Pays B',
    hs6: 'Code produit (HS6)',
    compare: 'Comparer',
    loading: 'Comparaison…',
    error: 'Impossible de comparer ces paramètres.',
    sameCountry: 'Choisissez deux pays différents.',
    flowAB: 'A → B (import par {b})',
    flowBA: 'B → A (import par {a})',
    mfn: 'Taux NPF',
    zlecaf: 'Taux ZLECAf',
    margin: 'Marge de préférence',
    best: 'Préférence ZLECAf la plus forte',
    equal: 'Préférence équivalente dans les deux sens',
    placeholderHs6: 'ex. 520100',
  },
  en: {
    title: 'Bilateral tariff comparator',
    subtitle: 'How a product is taxed in both directions of a country pair',
    countryA: 'Country A',
    countryB: 'Country B',
    hs6: 'Product code (HS6)',
    compare: 'Compare',
    loading: 'Comparing…',
    error: 'Could not compare these parameters.',
    sameCountry: 'Pick two different countries.',
    flowAB: 'A → B (imported by {b})',
    flowBA: 'B → A (imported by {a})',
    mfn: 'MFN rate',
    zlecaf: 'AfCFTA rate',
    margin: 'Preference margin',
    best: 'Strongest AfCFTA preference',
    equal: 'Equivalent preference both ways',
    placeholderHs6: 'e.g. 520100',
  },
};

const DirectionCard = ({ title, flow, t, highlight }) => (
  <div
    className={`rounded-lg p-4 border ${
      highlight ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-slate-700 bg-slate-900/50'
    }`}
  >
    <p className="text-xs font-semibold text-slate-300 mb-3">{title}</p>
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{t.mfn}</span>
        <span className="text-slate-200 font-medium">{flow.mfn_rate}%</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{t.zlecaf}</span>
        <span className="text-emerald-400 font-medium">{flow.zlecaf_rate}%</span>
      </div>
      <div className="flex justify-between text-sm border-t border-slate-700 pt-2">
        <span className="text-slate-300 font-semibold">{t.margin}</span>
        <span className="text-emerald-300 font-bold">{flow.preference_margin} pts</span>
      </div>
    </div>
  </div>
);

const BilateralTariffComparator = ({ language = 'fr' }) => {
  const t = TEXTS[language] || TEXTS.fr;
  const countries = getAllCountries(language === 'en' ? 'en' : 'fr');
  // Noms localisés (FR/EN) résolus côté frontend depuis l'ISO3 — l'API ne
  // renvoie que des libellés FR, donc on ne s'y fie pas pour l'affichage.
  const nameByIso3 = Object.fromEntries(countries.map((c) => [c.iso3, c.name]));
  const nameOf = (iso3) => nameByIso3[iso3] || iso3;

  const [a, setA] = useState('');
  const [b, setB] = useState('');
  const [hs6, setHs6] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const { label: hs6Label } = useHsLabel(hs6, language);

  const sameCountry = a && b && a === b;
  const canRun = a && b && !sameCountry && /^\d{6}$/.test(hs6);

  const runCompare = () => {
    if (!canRun) return;
    setLoading(true);
    setError(false);
    setResult(null);
    axios
      .get(`/api/bilateral-tariff/${a}/${b}/${hs6}`)
      .then((res) => setResult(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  const fill = (tpl, vals) => tpl.replace('{a}', vals.a).replace('{b}', vals.b);

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Scale className="w-5 h-5 text-emerald-400" />
          {t.title}
        </CardTitle>
        <p className="text-sm text-slate-400">{t.subtitle}</p>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t.countryA}</span>
            <select
              value={a}
              onChange={(e) => setA(e.target.value)}
              className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="">—</option>
              {countries.map((c) => (
                <option key={c.iso3} value={c.iso3}>
                  {c.flag} {c.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t.countryB}</span>
            <select
              value={b}
              onChange={(e) => setB(e.target.value)}
              className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="">—</option>
              {countries.map((c) => (
                <option key={c.iso3} value={c.iso3}>
                  {c.flag} {c.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t.hs6}</span>
            <input
              value={hs6}
              onChange={(e) => setHs6(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder={t.placeholderHs6}
              inputMode="numeric"
              className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
            {hs6Label && (
              <span className="text-xs text-emerald-400 truncate" title={hs6Label}>
                {hs6Label}
              </span>
            )}
          </label>
        </div>

        {sameCountry && (
          <p className="text-amber-400 text-xs flex items-center gap-1">
            <Info className="w-3.5 h-3.5" />
            {t.sameCountry}
          </p>
        )}

        <button
          onClick={runCompare}
          disabled={!canRun || loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold"
        >
          <ArrowLeftRight className="w-4 h-4" />
          {loading ? t.loading : t.compare}
        </button>

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <Info className="w-4 h-4" />
            {t.error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <DirectionCard
                title={fill(t.flowAB, { a: nameOf(result.country_a), b: nameOf(result.country_b) })}
                flow={result.flow_a_to_b}
                t={t}
                highlight={result.best_preference_direction === 'a_to_b'}
              />
              <DirectionCard
                title={fill(t.flowBA, { a: nameOf(result.country_a), b: nameOf(result.country_b) })}
                flow={result.flow_b_to_a}
                t={t}
                highlight={result.best_preference_direction === 'b_to_a'}
              />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-300">
                {result.best_preference_direction === 'equal'
                  ? t.equal
                  : `${t.best}: ${
                      result.best_preference_direction === 'a_to_b'
                        ? `${nameOf(result.country_a)} → ${nameOf(result.country_b)}`
                        : `${nameOf(result.country_b)} → ${nameOf(result.country_a)}`
                    }`}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default BilateralTariffComparator;
