import React, { useState } from 'react';
import axios from 'axios';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { TrendingDown, Calculator, Info } from 'lucide-react';
import { getAllCountries } from '../../utils/countryCodes';

const TEXTS = {
  fr: {
    title: 'Simulateur d’impact ZLECAf',
    subtitle: 'Économie de droits de douane année par année selon le calendrier officiel de démantèlement',
    importer: 'Pays importateur (marché de destination)',
    hs6: 'Code produit (HS6)',
    value: 'Valeur annuelle échangée (USD)',
    npfOverride: 'Taux NPF (%) — optionnel',
    npfHint: 'Laisser vide pour auto-détection depuis les données tarifaires',
    simulate: 'Simuler l’impact',
    loading: 'Calcul en cours…',
    error: 'Impossible de calculer l’impact pour ces paramètres.',
    category: 'Catégorie ZLECAf',
    npfRate: 'Taux NPF',
    currentRate: 'Taux ZLECAf actuel',
    savingNow: 'Économie annuelle actuelle',
    fullYear: 'Pleine libéralisation',
    totalSaving: 'Économie cumulée sur la période',
    chartTitle: 'Économie cumulée de droits de douane',
    tableYear: 'Année',
    tableRate: 'Taux ZLECAf',
    tableDutyNpf: 'Droit NPF',
    tableDutyZlecaf: 'Droit ZLECAf',
    tableSaving: 'Économie',
    tableCum: 'Cumul',
    sourceAuto: 'auto-détecté',
    excluded: 'Produit exclu (Catégorie C) — aucune réduction tarifaire prévue.',
    placeholderHs6: 'ex. 520100',
  },
  en: {
    title: 'AfCFTA Impact Simulator',
    subtitle: 'Year-by-year customs-duty savings under the official tariff dismantlement schedule',
    importer: 'Importing country (destination market)',
    hs6: 'Product code (HS6)',
    value: 'Annual traded value (USD)',
    npfOverride: 'MFN rate (%) — optional',
    npfHint: 'Leave empty to auto-detect from tariff data',
    simulate: 'Simulate impact',
    loading: 'Computing…',
    error: 'Could not compute the impact for these parameters.',
    category: 'AfCFTA category',
    npfRate: 'MFN rate',
    currentRate: 'Current AfCFTA rate',
    savingNow: 'Current annual saving',
    fullYear: 'Full liberalization',
    totalSaving: 'Cumulative saving over the period',
    chartTitle: 'Cumulative customs-duty savings',
    tableYear: 'Year',
    tableRate: 'AfCFTA rate',
    tableDutyNpf: 'MFN duty',
    tableDutyZlecaf: 'AfCFTA duty',
    tableSaving: 'Saving',
    tableCum: 'Cumulative',
    sourceAuto: 'auto-detected',
    excluded: 'Excluded product (Category C) — no tariff reduction scheduled.',
    placeholderHs6: 'e.g. 520100',
  },
};

const fmtUSD = (v) =>
  v == null ? '—' : `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;

const ZlecafImpactSimulator = ({ language = 'fr' }) => {
  const t = TEXTS[language] || TEXTS.fr;
  const countries = getAllCountries(language === 'en' ? 'en' : 'fr');

  const [importer, setImporter] = useState('');
  const [hs6, setHs6] = useState('');
  const [value, setValue] = useState('');
  const [npf, setNpf] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const canRun = importer && /^\d{6}$/.test(hs6) && Number(value) > 0;

  const runSimulation = () => {
    if (!canRun) return;
    setLoading(true);
    setError(false);
    setResult(null);
    const params = { trade_value: Number(value), language };
    if (npf !== '' && !Number.isNaN(Number(npf))) params.npf_rate = Number(npf);
    axios
      .get(`/api/dismantlement/impact/${importer}/${hs6}`, { params })
      .then((res) => setResult(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  const chartData = (result?.projection || []).map((r) => ({
    calendar_year: r.calendar_year,
    cumulative_saving: r.cumulative_saving,
    annual_saving: r.annual_saving,
  }));

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Calculator className="w-5 h-5 text-emerald-400" />
          {t.title}
        </CardTitle>
        <p className="text-sm text-slate-400">{t.subtitle}</p>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* ── Formulaire ─────────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t.importer}</span>
            <select
              value={importer}
              onChange={(e) => setImporter(e.target.value)}
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
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t.value}</span>
            <input
              value={value}
              onChange={(e) => setValue(e.target.value.replace(/[^\d.]/g, ''))}
              placeholder="1000000"
              inputMode="decimal"
              className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t.npfOverride}</span>
            <input
              value={npf}
              onChange={(e) => setNpf(e.target.value.replace(/[^\d.]/g, ''))}
              placeholder="—"
              inputMode="decimal"
              className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
            <span className="text-[11px] text-slate-500">{t.npfHint}</span>
          </label>
        </div>

        <button
          onClick={runSimulation}
          disabled={!canRun || loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold"
        >
          <Calculator className="w-4 h-4" />
          {loading ? t.loading : t.simulate}
        </button>

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <Info className="w-4 h-4" />
            {t.error}
          </div>
        )}

        {/* ── Résultats ──────────────────────────────────────────── */}
        {result && (
          <div className="space-y-5">
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700">
                <p className="text-[11px] text-slate-400">{t.npfRate}</p>
                <p className="text-lg font-bold text-white">{result.npf_rate}%</p>
                <p className="text-[10px] text-slate-500">
                  {result.npf_rate_source === 'fourni par l’utilisateur' ? '' : t.sourceAuto}
                </p>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700">
                <p className="text-[11px] text-slate-400">{t.currentRate}</p>
                <p className="text-lg font-bold text-emerald-400">{result.current_zlecaf_rate}%</p>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700">
                <p className="text-[11px] text-slate-400">{t.savingNow}</p>
                <p className="text-lg font-bold text-emerald-400">{fmtUSD(result.annual_saving_now)}</p>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700">
                <p className="text-[11px] text-slate-400">{t.fullYear}</p>
                <p className="text-lg font-bold text-white">{result.full_liberalization_year || '—'}</p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-300">{t.totalSaving}:</span>
              <span className="font-bold text-emerald-400">{fmtUSD(result.total_saving_over_schedule)}</span>
            </div>

            {result.category === 'C' && (
              <div className="flex items-center gap-2 text-amber-400 text-sm">
                <Info className="w-4 h-4" />
                {t.excluded}
              </div>
            )}

            {/* Graphique cumul */}
            {chartData.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 mb-2">{t.chartTitle}</p>
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 4 }}>
                    <defs>
                      <linearGradient id="savingGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#34d399" stopOpacity={0.6} />
                        <stop offset="95%" stopColor="#34d399" stopOpacity={0.04} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="calendar_year" tick={{ fontSize: 11, fill: 'rgba(148,163,184,0.8)' }} axisLine={false} tickLine={false} />
                    <YAxis tickFormatter={fmtUSD} tick={{ fontSize: 10, fill: 'rgba(148,163,184,0.7)' }} axisLine={false} tickLine={false} width={70} />
                    <Tooltip
                      formatter={(v) => fmtUSD(v)}
                      contentStyle={{ background: 'rgba(15,23,42,0.97)', border: '1px solid rgba(52,211,153,0.3)', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: '#e2e8f0', fontWeight: 700 }}
                    />
                    <Area type="monotone" dataKey="cumulative_saving" stroke="#34d399" strokeWidth={2.5} fill="url(#savingGrad)" name={t.tableCum} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Tableau */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 text-xs border-b border-slate-700">
                    <th className="text-left py-2 px-2">{t.tableYear}</th>
                    <th className="text-right py-2 px-2">{t.tableRate}</th>
                    <th className="text-right py-2 px-2">{t.tableDutyNpf}</th>
                    <th className="text-right py-2 px-2">{t.tableDutyZlecaf}</th>
                    <th className="text-right py-2 px-2">{t.tableSaving}</th>
                    <th className="text-right py-2 px-2">{t.tableCum}</th>
                  </tr>
                </thead>
                <tbody>
                  {result.projection.map((r) => (
                    <tr key={r.year} className="border-b border-slate-800">
                      <td className="py-1.5 px-2 text-slate-300">{r.calendar_year}</td>
                      <td className="py-1.5 px-2 text-right text-slate-200">{r.zlecaf_rate}%</td>
                      <td className="py-1.5 px-2 text-right text-slate-400">{fmtUSD(r.duty_npf)}</td>
                      <td className="py-1.5 px-2 text-right text-slate-200">{fmtUSD(r.duty_zlecaf)}</td>
                      <td className="py-1.5 px-2 text-right text-emerald-400 font-medium">{fmtUSD(r.annual_saving)}</td>
                      <td className="py-1.5 px-2 text-right text-emerald-300 font-semibold">{fmtUSD(r.cumulative_saving)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ZlecafImpactSimulator;
