import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Area, AreaChart,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { TrendingDown, Calendar, Info } from 'lucide-react';

// ---------------------------------------------------------------------------
// Tooltip personnalisé
// ---------------------------------------------------------------------------
const CustomTooltip = ({ active, payload, language }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl text-sm">
      <p className="text-slate-300 font-semibold">
        {language === 'fr' ? `Année ${d.year}` : `Year ${d.year}`} — {d.calendar_year}
      </p>
      <p className="text-emerald-400 font-bold text-base">{d.rate.toFixed(2)}%</p>
      {d.reduction_pct > 0 && (
        <p className="text-slate-400 text-xs">
          {language === 'fr' ? 'Réduction cumulée' : 'Cumulative reduction'}: {d.reduction_pct.toFixed(1)}%
        </p>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Badge catégorie
// ---------------------------------------------------------------------------
const CategoryBadge = ({ category, label }) => {
  const colors = {
    A: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    B: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    C: 'bg-red-500/20 text-red-400 border-red-500/30',
    D: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors[category] || colors.A}`}>
      {label || `Catégorie ${category}`}
    </span>
  );
};

// ---------------------------------------------------------------------------
// Composant principal
// ---------------------------------------------------------------------------
const DismantlementSchedule = ({ countryIso3, hs6, npfRate, language = 'fr' }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!countryIso3 || !hs6 || npfRate === undefined || npfRate === null) return;
    if (npfRate === 0) {
      // Taux déjà à 0 — pas besoin d'appel API
      setData({ category: 'D', npf_rate: 0, current_zlecaf_rate: 0,
                fully_liberalized: true, schedule: [], is_ldc: false });
      return;
    }

    setLoading(true);
    setError(null);

    axios.get(`/api/dismantlement/${countryIso3}/${hs6}`, {
      params: { npf_rate: npfRate, language },
    })
      .then(res => setData(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [countryIso3, hs6, npfRate, language]);

  if (!countryIso3 || !hs6 || npfRate === undefined) return null;
  if (loading) return (
    <div className="flex items-center gap-2 py-4 text-slate-400 text-sm">
      <div className="w-4 h-4 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
      {language === 'fr' ? 'Chargement du schéma de démantèlement…' : 'Loading dismantlement schedule…'}
    </div>
  );
  if (error || !data) return null;

  // Taux déjà à 0%
  if (data.category === 'D' || npfRate === 0) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="pt-4 pb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <TrendingDown className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">
                {language === 'fr' ? 'Déjà en franchise ZLECAf (0%)' : 'Already duty-free under AfCFTA (0%)'}
              </p>
              <p className="text-xs text-slate-400">
                {language === 'fr' ? 'Catégorie D — consolidé immédiatement à 0%' : 'Category D — immediately bound at 0%'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Produits exclus — Catégorie C
  if (data.category === 'C') {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="pt-4 pb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-500/10 rounded-lg border border-red-500/20">
              <Info className="w-4 h-4 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">
                {language === 'fr' ? 'Produit exclu du démantèlement ZLECAf' : 'Product excluded from AfCFTA dismantlement'}
              </p>
              <p className="text-xs text-slate-400">
                {language === 'fr' ? 'Catégorie C — taux NPF maintenu' : 'Category C — MFN rate maintained'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const schedule = data.schedule || [];
  const currentYear = data.current_implementation_year;
  const currentCalendarYear = data.current_calendar_year;

  // Indicateurs résumés
  const savings = data.npf_rate - data.current_zlecaf_rate;
  const savingsPct = data.npf_rate > 0 ? (savings / data.npf_rate * 100) : 0;

  return (
    <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
              <TrendingDown className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <CardTitle className="text-lg text-white">
                {language === 'fr' ? 'Schéma de Démantèlement ZLECAf' : 'AfCFTA Dismantlement Schedule'}
              </CardTitle>
              <p className="text-xs text-slate-400 mt-0.5">
                {language === 'fr'
                  ? 'Annexe 1, Protocole sur le Commerce des Marchandises — UA 2018'
                  : 'Annex 1, Protocol on Trade in Goods — AU 2018'}
              </p>
            </div>
          </div>
          <CategoryBadge category={data.category} label={data.category_label} />
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Indicateurs clés */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* Taux NPF */}
          <div className="bg-red-500/10 rounded-xl p-3 border border-red-500/20 text-center">
            <p className="text-red-400/70 text-xs uppercase tracking-wide">
              {language === 'fr' ? 'Taux NPF' : 'MFN Rate'}
            </p>
            <p className="text-2xl font-bold text-red-400 mt-1">{data.npf_rate.toFixed(1)}%</p>
          </div>

          {/* Taux actuel ZLECAf */}
          <div className="bg-emerald-500/10 rounded-xl p-3 border border-emerald-500/20 text-center">
            <p className="text-emerald-400/70 text-xs uppercase tracking-wide">
              {language === 'fr' ? `ZLECAf ${currentCalendarYear}` : `AfCFTA ${currentCalendarYear}`}
            </p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">
              {data.current_zlecaf_rate.toFixed(1)}%
            </p>
          </div>

          {/* Économie actuelle */}
          <div className="bg-amber-500/10 rounded-xl p-3 border border-amber-500/20 text-center">
            <p className="text-amber-400/70 text-xs uppercase tracking-wide">
              {language === 'fr' ? 'Gain actuel' : 'Current gain'}
            </p>
            <p className="text-2xl font-bold text-amber-400 mt-1">
              -{savingsPct.toFixed(0)}%
            </p>
          </div>

          {/* Année finale */}
          <div className="bg-blue-500/10 rounded-xl p-3 border border-blue-500/20 text-center">
            <p className="text-blue-400/70 text-xs uppercase tracking-wide">
              {language === 'fr' ? 'Franchise totale' : 'Full duty-free'}
            </p>
            <p className="text-2xl font-bold text-blue-400 mt-1">
              {data.target_calendar_year
                ? (data.fully_liberalized
                    ? (language === 'fr' ? 'Atteint' : 'Reached')
                    : data.target_calendar_year)
                : '—'}
            </p>
          </div>
        </div>

        {/* Graphique */}
        {schedule.length > 1 && (
          <div>
            <p className="text-xs text-slate-400 mb-3 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              {language === 'fr'
                ? `Réductions linéaires annuelles — ${data.is_ldc ? 'PMA' : 'Non-PMA'}`
                : `Annual linear reductions — ${data.is_ldc ? 'LDC' : 'Non-LDC'}`}
            </p>
            <div className="w-full" style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={schedule} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="rateGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis
                    dataKey="calendar_year"
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    tickLine={false}
                    tickFormatter={v => `${v}%`}
                    domain={[0, Math.ceil(data.npf_rate * 1.1)]}
                  />
                  <Tooltip content={<CustomTooltip language={language} />} />
                  {/* Ligne "aujourd'hui" */}
                  <ReferenceLine
                    x={currentCalendarYear}
                    stroke="#f59e0b"
                    strokeDasharray="4 2"
                    label={{
                      value: language === 'fr' ? "Auj." : "Today",
                      fill: '#f59e0b',
                      fontSize: 10,
                      position: 'top',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="rate"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    fill="url(#rateGradient)"
                    dot={(props) => {
                      const { cx, cy, payload } = props;
                      const isCurrent = payload.calendar_year === currentCalendarYear;
                      if (!isCurrent) return <g key={payload.year} />;
                      return (
                        <circle
                          key={payload.year}
                          cx={cx} cy={cy} r={5}
                          fill="#f59e0b" stroke="#1e293b" strokeWidth={2}
                        />
                      );
                    }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Tableau annuel — affichage compact */}
        <details className="group">
          <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-300 select-none">
            {language === 'fr' ? '▶ Voir le calendrier annuel complet' : '▶ View full annual schedule'}
          </summary>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="pb-2 text-slate-400 font-medium pr-4">
                    {language === 'fr' ? 'Année ZLECAf' : 'AfCFTA Year'}
                  </th>
                  <th className="pb-2 text-slate-400 font-medium pr-4">
                    {language === 'fr' ? 'Calendrier' : 'Calendar'}
                  </th>
                  <th className="pb-2 text-slate-400 font-medium pr-4">
                    {language === 'fr' ? 'Taux DD' : 'Duty Rate'}
                  </th>
                  <th className="pb-2 text-slate-400 font-medium">
                    {language === 'fr' ? 'Réduction' : 'Reduction'}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {schedule.map((row) => {
                  const isCurrent = row.calendar_year === currentCalendarYear;
                  return (
                    <tr
                      key={row.year}
                      className={isCurrent
                        ? 'bg-amber-500/10 font-semibold'
                        : 'hover:bg-slate-700/30'}
                    >
                      <td className="py-1.5 pr-4 text-slate-300">
                        {row.year === 0
                          ? (language === 'fr' ? 'Avant EIV' : 'Pre-EIF')
                          : `An ${row.year}`}
                        {isCurrent && (
                          <span className="ml-1 text-amber-400">←</span>
                        )}
                      </td>
                      <td className="py-1.5 pr-4 text-slate-300">{row.calendar_year}</td>
                      <td className={`py-1.5 pr-4 font-mono ${row.rate === 0 ? 'text-emerald-400' : 'text-white'}`}>
                        {row.rate.toFixed(2)}%
                      </td>
                      <td className="py-1.5 text-slate-400">
                        {row.reduction_pct > 0 ? `-${row.reduction_pct.toFixed(1)}%` : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </details>

        {/* Note légale */}
        <p className="text-xs text-slate-500 border-t border-slate-700 pt-3">
          {language === 'fr'
            ? `Source: Annexe 1, Protocole sur le Commerce des Marchandises, Union Africaine (2018). EIV: 1er janvier 2021. Statut: ${data.is_ldc ? 'PMA' : 'Non-PMA'}.`
            : `Source: Annex 1, Protocol on Trade in Goods, African Union (2018). EIF: January 1, 2021. Status: ${data.is_ldc ? 'LDC' : 'Non-LDC'}.`}
        </p>
      </CardContent>
    </Card>
  );
};

export default DismantlementSchedule;
