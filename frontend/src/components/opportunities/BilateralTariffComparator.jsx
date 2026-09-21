import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { ArrowLeftRight, Scale, TrendingDown, Info } from 'lucide-react';
import { getAllCountries } from '../../utils/countryCodes';
import { useHsLabel } from '../../hooks/useHsLabel';
import OpportunityPdfExport from './OpportunityPdfExport';
import { opportunityPdfFilename } from '../../utils/opportunityPdf';


const DirectionCard = ({ title, flow, highlight }) => {
  const { t } = useTranslation();
  return (
    <div
      className={`rounded-lg p-4 border ${
        highlight ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-slate-700 bg-slate-900/50'
      }`}
    >
      <p className="text-xs font-semibold text-slate-300 mb-3">{title}</p>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">{t('opportunities.bilateralTariffComparator.mfn')}</span>
          <span className="text-slate-200 font-medium">{flow.mfn_rate}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">{t('opportunities.bilateralTariffComparator.zlecaf')}</span>
          <span className="text-emerald-400 font-medium">{flow.zlecaf_rate}%</span>
        </div>
        <div className="flex justify-between text-sm border-t border-slate-700 pt-2">
          <span className="text-slate-300 font-semibold">{t('opportunities.bilateralTariffComparator.margin')}</span>
          <span className="text-emerald-300 font-bold">{flow.preference_margin} pts</span>
        </div>
      </div>
    </div>
  );
};

const BilateralTariffComparator = ({ language = 'fr' }) => {
  const { t } = useTranslation();
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

  // Rapport PDF : les deux sens de la paire, en clé-valeur.
  const buildPdfSpec = () => {
    if (!result) return null;
    const nA = nameOf(result.country_a);
    const nB = nameOf(result.country_b);
    const flowSection = (label, flow) => ({
      title: label,
      keyValues: [
        { label: t('opportunities.bilateralTariffComparator.mfn'), value: `${flow?.mfn_rate ?? '—'}%` },
        { label: t('opportunities.bilateralTariffComparator.zlecaf'), value: `${flow?.zlecaf_rate ?? '—'}%` },
        { label: t('opportunities.bilateralTariffComparator.margin'), value: `${flow?.preference_margin ?? '—'} pts` },
      ],
    });
    const bestText =
      result.best_preference_direction === 'equal'
        ? t('opportunities.bilateralTariffComparator.equalPreferenceBothDirections')
        : `${t('opportunities.bilateralTariffComparator.best')}: ${result.best_preference_direction === 'a_to_b' ? `${nA} → ${nB}` : `${nB} → ${nA}`}`;
    return {
      badge: t('opportunities.bilateralTariffComparator.bilateralComparator'),
      title: `${nA} ⇄ ${nB} · SH6 ${hs6}`,
      subtitle: t('opportunities.bilateralTariffComparator.subtitle'),
      sections: [
        flowSection(fill(t('opportunities.bilateralTariffComparator.flowAB'), { a: nA, b: nB }), result.flow_a_to_b),
        flowSection(fill(t('opportunities.bilateralTariffComparator.flowBA'), { a: nA, b: nB }), result.flow_b_to_a),
        { title: t('opportunities.bilateralTariffComparator.best'), paragraphs: [bestText] },
      ],
      source: t('opportunities.bilateralTariffComparator.nationalTariffsAfcftaSchedules'),
      filename: opportunityPdfFilename('Comparateur', `${result.country_a}_${result.country_b}_${hs6}`),
    };
  };

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2 text-white">
            <Scale className="w-5 h-5 text-emerald-400" />
            {t('opportunities.bilateralTariffComparator.title')}
          </CardTitle>
          {result && <OpportunityPdfExport getSpec={buildPdfSpec} language={language} />}
        </div>
        <p className="text-sm text-slate-400">{t('opportunities.bilateralTariffComparator.subtitle')}</p>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t('opportunities.bilateralTariffComparator.countryA')}</span>
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
            <span className="text-xs font-semibold text-slate-400">{t('opportunities.bilateralTariffComparator.countryB')}</span>
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
            <span className="text-xs font-semibold text-slate-400">{t('opportunities.bilateralTariffComparator.hs6')}</span>
            <input
              value={hs6}
              onChange={(e) => setHs6(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder={t('opportunities.bilateralTariffComparator.placeholderHs6')}
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
            {t('opportunities.bilateralTariffComparator.sameCountry')}
          </p>
        )}

        <button
          onClick={runCompare}
          disabled={!canRun || loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold"
        >
          <ArrowLeftRight className="w-4 h-4" />
          {loading ? t('opportunities.bilateralTariffComparator.loading') : t('opportunities.bilateralTariffComparator.compare')}
        </button>

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <Info className="w-4 h-4" />
            {t('opportunities.bilateralTariffComparator.error')}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <DirectionCard
                title={fill(t('opportunities.bilateralTariffComparator.flowAB'), { a: nameOf(result.country_a), b: nameOf(result.country_b) })}
                flow={result.flow_a_to_b}
                highlight={result.best_preference_direction === 'a_to_b'}
              />
              <DirectionCard
                title={fill(t('opportunities.bilateralTariffComparator.flowBA'), { a: nameOf(result.country_a), b: nameOf(result.country_b) })}
                flow={result.flow_b_to_a}
                highlight={result.best_preference_direction === 'b_to_a'}
              />
            </div>
            <div className="flex items-center gap-2 text-sm">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-300">
                {result.best_preference_direction === 'equal'
                  ? t('opportunities.bilateralTariffComparator.equal')
                  : `${t('opportunities.bilateralTariffComparator.best')}: ${
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
