import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { TrendingDown, Calculator, Info } from 'lucide-react';
import { getAllCountries } from '../../utils/countryCodes';
import { useHsLabel } from '../../hooks/useHsLabel';
import OpportunityPdfExport from './OpportunityPdfExport';
import { opportunityPdfFilename } from '../../utils/opportunityPdf';


const fmtUSD = (v) =>
  v == null ? '—' : `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;

const ZlecafImpactSimulator = ({ language = 'fr' }) => {
  const { t } = useTranslation();
  const countries = getAllCountries(language === 'en' ? 'en' : 'fr');

  const [importer, setImporter] = useState('');
  const [hs6, setHs6] = useState('');
  const [value, setValue] = useState('');
  const [npf, setNpf] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const { label: hs6Label } = useHsLabel(hs6, language);

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

  // Rapport PDF du simulateur : KPIs + projection année par année.
  const buildPdfSpec = () => {
    if (!result) return null;
    const fr = language !== 'en';
    return {
      badge: t('opportunities.zlecafImpactSimulator.afcftaSimulator'),
      title: `${t('opportunities.zlecafImpactSimulator.title')} — ${importer} · SH6 ${hs6}`,
      subtitle: `${t('opportunities.zlecafImpactSimulator.subtitle')}`,
      kpis: [
        { label: t('opportunities.zlecafImpactSimulator.npfRate'), value: `${result.npf_rate}%`, accent: 'red' },
        { label: t('opportunities.zlecafImpactSimulator.currentRate'), value: `${result.current_zlecaf_rate}%`, accent: 'green' },
        { label: t('opportunities.zlecafImpactSimulator.savingNow'), value: fmtUSD(result.annual_saving_now), accent: 'green' },
        { label: t('opportunities.zlecafImpactSimulator.totalSaving'), value: fmtUSD(result.total_saving_over_schedule), accent: 'gold' },
      ],
      sections: [
        {
          title: t('opportunities.zlecafImpactSimulator.chartTitle'),
          table: {
            columns: [
              { key: 'calendar_year', label: t('opportunities.zlecafImpactSimulator.tableYear'), width: 0.8 },
              { key: 'zlecaf_rate', label: t('opportunities.zlecafImpactSimulator.tableRate'), align: 'right', width: 0.9, fmt: (v) => `${v}%` },
              { key: 'duty_npf', label: t('opportunities.zlecafImpactSimulator.tableDutyNpf'), align: 'right', width: 1.1, fmt: fmtUSD },
              { key: 'duty_zlecaf', label: t('opportunities.zlecafImpactSimulator.tableDutyZlecaf'), align: 'right', width: 1.1, fmt: fmtUSD },
              { key: 'annual_saving', label: t('opportunities.zlecafImpactSimulator.tableSaving'), align: 'right', width: 1.1, fmt: fmtUSD },
              { key: 'cumulative_saving', label: t('opportunities.zlecafImpactSimulator.tableCum'), align: 'right', width: 1.1, fmt: fmtUSD },
            ],
            rows: result.projection || [],
          },
        },
      ],
      source: t('opportunities.zlecafImpactSimulator.officialAfcftaDismantlementSchedule'),
      filename: opportunityPdfFilename('Simulateur', `${importer}_${hs6}`),
    };
  };

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2 text-white">
            <Calculator className="w-5 h-5 text-emerald-400" />
            {t('opportunities.zlecafImpactSimulator.title')}
          </CardTitle>
          {result && <OpportunityPdfExport getSpec={buildPdfSpec} language={language} />}
        </div>
        <p className="text-sm text-slate-400">{t('opportunities.zlecafImpactSimulator.subtitle')}</p>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* ── Formulaire ─────────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t('opportunities.zlecafImpactSimulator.importer')}</span>
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
            <span className="text-xs font-semibold text-slate-400">{t('opportunities.zlecafImpactSimulator.hs6')}</span>
            <input
              value={hs6}
              onChange={(e) => setHs6(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder={t('opportunities.zlecafImpactSimulator.placeholderHs6')}
              inputMode="numeric"
              className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
            {hs6Label && (
              <span className="text-xs text-emerald-400 truncate" title={hs6Label}>
                {hs6Label}
              </span>
            )}
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t('opportunities.zlecafImpactSimulator.value')}</span>
            <input
              value={value}
              onChange={(e) => setValue(e.target.value.replace(/[^\d.]/g, ''))}
              placeholder="1000000"
              inputMode="decimal"
              className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold text-slate-400">{t('opportunities.zlecafImpactSimulator.npfOverride')}</span>
            <input
              value={npf}
              onChange={(e) => setNpf(e.target.value.replace(/[^\d.]/g, ''))}
              placeholder="—"
              inputMode="decimal"
              className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
            />
            <span className="text-[11px] text-slate-500">{t('opportunities.zlecafImpactSimulator.npfHint')}</span>
          </label>
        </div>

        <button
          onClick={runSimulation}
          disabled={!canRun || loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold"
        >
          <Calculator className="w-4 h-4" />
          {loading ? t('opportunities.zlecafImpactSimulator.loading') : t('opportunities.zlecafImpactSimulator.simulate')}
        </button>

        {error && (
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <Info className="w-4 h-4" />
            {t('opportunities.zlecafImpactSimulator.error')}
          </div>
        )}

        {/* ── Résultats ──────────────────────────────────────────── */}
        {result && (
          <div className="space-y-5">
            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700">
                <p className="text-[11px] text-slate-400">{t('opportunities.zlecafImpactSimulator.npfRate')}</p>
                <p className="text-lg font-bold text-white">{result.npf_rate}%</p>
                <p className="text-[10px] text-slate-500">
                  {result.npf_auto_detected ? t('opportunities.zlecafImpactSimulator.sourceAuto') : ''}
                </p>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700">
                <p className="text-[11px] text-slate-400">{t('opportunities.zlecafImpactSimulator.currentRate')}</p>
                <p className="text-lg font-bold text-emerald-400">{result.current_zlecaf_rate}%</p>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700">
                <p className="text-[11px] text-slate-400">{t('opportunities.zlecafImpactSimulator.savingNow')}</p>
                <p className="text-lg font-bold text-emerald-400">{fmtUSD(result.annual_saving_now)}</p>
              </div>
              <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-700">
                <p className="text-[11px] text-slate-400">{t('opportunities.zlecafImpactSimulator.fullYear')}</p>
                <p className="text-lg font-bold text-white">{result.full_liberalization_year || '—'}</p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-300">{t('opportunities.zlecafImpactSimulator.totalSaving')}:</span>
              <span className="font-bold text-emerald-400">{fmtUSD(result.total_saving_over_schedule)}</span>
            </div>

            {result.category === 'C' && (
              <div className="flex items-center gap-2 text-amber-400 text-sm">
                <Info className="w-4 h-4" />
                {t('opportunities.zlecafImpactSimulator.excluded')}
              </div>
            )}

            {/* Graphique cumul */}
            {chartData.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 mb-2">{t('opportunities.zlecafImpactSimulator.chartTitle')}</p>
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
                      contentStyle={{ background: 'var(--afcfta-card)', border: '1px solid var(--afcfta-border)', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: 'var(--text)', fontWeight: 700 }}
                    />
                    <Area type="monotone" dataKey="cumulative_saving" stroke="#34d399" strokeWidth={2.5} fill="url(#savingGrad)" name={t('opportunities.zlecafImpactSimulator.tableCum')} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Tableau */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 text-xs border-b border-slate-700">
                    <th className="text-left py-2 px-2">{t('opportunities.zlecafImpactSimulator.tableYear')}</th>
                    <th className="text-right py-2 px-2">{t('opportunities.zlecafImpactSimulator.tableRate')}</th>
                    <th className="text-right py-2 px-2">{t('opportunities.zlecafImpactSimulator.tableDutyNpf')}</th>
                    <th className="text-right py-2 px-2">{t('opportunities.zlecafImpactSimulator.tableDutyZlecaf')}</th>
                    <th className="text-right py-2 px-2">{t('opportunities.zlecafImpactSimulator.tableSaving')}</th>
                    <th className="text-right py-2 px-2">{t('opportunities.zlecafImpactSimulator.tableCum')}</th>
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
