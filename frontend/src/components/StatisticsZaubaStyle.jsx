import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, Area, AreaChart } from 'recharts';
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Globe, Users, ArrowUpRight } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API_URL = BACKEND_URL || '';

const StatisticsZaubaStyle = ({ language = 'fr' }) => {
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState(null);
  const [africaTotals, setAfricaTotals] = useState(null);
  const [selectedYear, setSelectedYear] = useState('2024');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [gdpHistory, setGdpHistory] = useState(null);
  const [gdpChartMode, setGdpChartMode] = useState('absolute'); // 'absolute' | 'index'

  const texts = {
    fr: {
      loading: "Chargement des statistiques...",
      noData: "Aucune donnée disponible",
      analysisTitle: "Analyse du Commerce Africain - ZLECAf 2024",
      totalTradeValue: "Valeur Totale Commerce",
      combinedGDP: "PIB Combiné",
      totalExports: "Exportations Totales",
      totalImports: "Importations Totales",
      estimated2024: "2024 Estimé",
      memberCountries: "Pays Membres",
      top10Exporters: "Top 10 Exportateurs",
      top10Importers: "Top 10 Importateurs",
      ofTotal: "du total",
      intraAfricanEvolution: "Évolution du Commerce Intra-Africain",
      trend2023_2030: "Tendance 2023-2024 avec projections 2025-2030",
      billionUSD: "Milliards USD",
      intraAfricanTrade: "Commerce Intra-Africain",
      top5GDP: "Top 5 PIB Africains - Comparaison Commerce",
      worldVsIntraAfrican: "Commerce Mondial vs Commerce Intra-Africain (2024)",
      detailByCountry: "Détail par Pays (Milliards USD)",
      expWorld: "Exp. Monde",
      expIntraAfr: "Exp. Intra-Afr",
      impWorld: "Imp. Monde",
      impIntraAfr: "Imp. Intra-Afr",
      sectorPerformance: "Performance par Secteur",
      sectorDistribution: "Distribution des exportations par secteur économique",
      sectorDetails: "Détail des Secteurs",
      exportsWorld: "Exports Monde",
      exportsIntraAfr: "Exports Intra-Afr.",
      importsWorld: "Imports Monde",
      importsIntraAfr: "Imports Intra-Afr."
    },
    en: {
      loading: "Loading statistics...",
      noData: "No data available",
      analysisTitle: "African Trade Analysis - AfCFTA 2024",
      totalTradeValue: "Total Trade Value",
      combinedGDP: "Combined GDP",
      totalExports: "Total Exports",
      totalImports: "Total Imports",
      estimated2024: "2024 Estimated",
      memberCountries: "Member Countries",
      top10Exporters: "Top 10 Exporters",
      top10Importers: "Top 10 Importers",
      ofTotal: "of total",
      intraAfricanEvolution: "Intra-African Trade Evolution",
      trend2023_2030: "2023-2024 trend with 2025-2030 projections",
      billionUSD: "Billion USD",
      intraAfricanTrade: "Intra-African Trade",
      top5GDP: "Top 5 African GDP - Trade Comparison",
      worldVsIntraAfrican: "World Trade vs Intra-African Trade (2024)",
      detailByCountry: "Detail by Country (Billion USD)",
      expWorld: "Exp. World",
      expIntraAfr: "Exp. Intra-Afr",
      impWorld: "Imp. World",
      impIntraAfr: "Imp. Intra-Afr",
      sectorPerformance: "Sector Performance",
      sectorDistribution: "Export distribution by economic sector",
      sectorDetails: "Sector Details",
      exportsWorld: "World Exports",
      exportsIntraAfr: "Intra-Afr. Exports",
      importsWorld: "World Imports",
      importsIntraAfr: "Intra-Afr. Imports"
    }
  };

  // Country name translations
  const countryNames = {
    fr: {
      "South Africa": "Afrique du Sud",
      "Egypt": "Égypte",
      "Nigeria": "Nigéria",
      "Algeria": "Algérie",
      "Morocco": "Maroc",
      "Ethiopia": "Éthiopie",
      "Kenya": "Kenya",
      "Angola": "Angola",
      "Ghana": "Ghana",
      "Tanzania": "Tanzanie",
      "Côte d'Ivoire": "Côte d'Ivoire",
      "Tunisia": "Tunisie",
      "DR Congo": "RD Congo",
      "Cameroon": "Cameroun",
      "Uganda": "Ouganda"
    },
    en: {
      "Afrique du Sud": "South Africa",
      "Égypte": "Egypt",
      "Nigéria": "Nigeria",
      "Algérie": "Algeria",
      "Maroc": "Morocco",
      "Éthiopie": "Ethiopia",
      "Kenya": "Kenya",
      "Angola": "Angola",
      "Ghana": "Ghana",
      "Tanzanie": "Tanzania",
      "Côte d'Ivoire": "Côte d'Ivoire",
      "Tunisie": "Tunisia",
      "RD Congo": "DR Congo",
      "Cameroun": "Cameroon",
      "Ouganda": "Uganda"
    }
  };

  const t = texts[language];

  const translateCountry = (name) => {
    if (language === 'en' && countryNames.en[name]) {
      return countryNames.en[name];
    }
    return name;
  };

  useEffect(() => {
    fetchStatistics();
    fetchAfricaTotals();
    fetchGdpHistory();
  }, []);

  const fetchGdpHistory = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/statistics/gdp-history-top10`);
      setGdpHistory(response.data || null);
    } catch (e) {
      // Silent — chart will be hidden if data is unavailable.
      setGdpHistory(null);
    }
  };

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/statistics`);
      const data = response.data;
      setStatistics(typeof data === 'object' && data !== null && !Array.isArray(data) ? data : null);
      setLoading(false);
    } catch (error) {
      console.error('Erreur:', error);
      setLoading(false);
    }
  };

  const fetchAfricaTotals = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/oec/africa/totals?year=2024`);
      setAfricaTotals(response.data);
    } catch (error) {
      console.error('Erreur OEC Africa Totals:', error);
    }
  };

  if (loading) {
    return (
      <div className="stats-loading">
        <div className="stats-spinner" />
        <p style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.875rem' }}>{t.loading}</p>
      </div>
    );
  }

  if (!statistics) {
    return (
      <div className="stats-empty-state">
        <div className="stats-empty-icon">
          <BarChart3 style={{ width: 28, height: 28, color: '#D4891A' }} />
        </div>
        <p>{t.noData}</p>
      </div>
    );
  }

  /* ── African-themed palette for charts ───────────────────── */
  const COLORS = ['#1A7A4A', '#1A6B8A', '#D4891A', '#C8531A', '#9B6EF5', '#C8102E', '#0E8A7A', '#D4522A'];

  /* ── Custom tooltip ─────────────────────────────────────── */
  const AfricaTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, padding: '10px 14px', fontSize: '0.8rem' }}>
        <p style={{ color: '#EAE0D0', fontWeight: 700, marginBottom: 4 }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color, margin: '2px 0' }}>
            {p.name}: <strong>{typeof p.value === 'number' ? `$${p.value.toFixed(1)}B` : p.value}</strong>
          </p>
        ))}
      </div>
    );
  };

  /* ── Max export value for progress bars ─────────────────── */
  const maxExport = Math.max(...(statistics.top_exporters_2024?.slice(0, 10).map(e => e.exports_2024 / 1e9) || [1]));
  const maxImport = Math.max(...(statistics.top_importers_2024?.slice(0, 10).map(i => i.imports_2024 / 1e9) || [1]));

  const getRankClass = (i) => i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : i === 2 ? 'rank-3' : 'rank-n';

  return (
    <div className="space-y-6">
      {/* ── Section Résumé — KPI Cards ─────────────────────────── */}
      <div className="stats-chart-card" style={{ padding: '24px' }}>
        {/* Section title with kente accent */}
        <div className="flex items-center gap-3 mb-6">
          <BarChart3 style={{ width: 22, height: 22, color: '#D4891A', flexShrink: 0 }} />
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#EAE0D0', margin: 0 }}>
              {t.analysisTitle}
            </h2>
            <div className="stats-kente-bar" style={{ width: 160, marginTop: 6 }} />
          </div>
        </div>

        {/* KPI Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {/* PIB Combiné */}
          <div className="stats-kpi-card atlantic">
            <svg className="stats-kpi-ornament" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <polygon points="24,4 28,16 40,12 32,20 44,24 32,28 40,36 28,32 24,44 20,32 8,36 16,28 4,24 16,20 8,12 20,16" stroke="rgba(212,137,26,1)" strokeWidth="0.8"/>
              <rect x="14" y="14" width="20" height="20" transform="rotate(45 24 24)" stroke="rgba(212,137,26,1)" strokeWidth="0.6"/>
            </svg>
            <p className="stats-kpi-label">{t.totalTradeValue}</p>
            <p className="stats-kpi-value atlantic">
              ${statistics.overview?.estimated_combined_gdp
                ? (statistics.overview.estimated_combined_gdp / 1e9).toFixed(0)
                : '2706'}B
            </p>
            <p className="stats-kpi-footer">
              <DollarSign style={{ width: 12, height: 12 }} />
              {t.combinedGDP}
            </p>
          </div>

          {/* Exportations */}
          <div className="stats-kpi-card green">
            <svg className="stats-kpi-ornament" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <polygon points="24,4 28,16 40,12 32,20 44,24 32,28 40,36 28,32 24,44 20,32 8,36 16,28 4,24 16,20 8,12 20,16" stroke="rgba(212,137,26,1)" strokeWidth="0.8"/>
            </svg>
            <p className="stats-kpi-label">{t.totalExports}</p>
            <p className="stats-kpi-value green">
              ${africaTotals?.exports_billions ? africaTotals.exports_billions.toFixed(0) : '720'}B
            </p>
            <p className="stats-kpi-footer">
              <TrendingUp style={{ width: 12, height: 12 }} />
              {t.estimated2024}
            </p>
          </div>

          {/* Importations */}
          <div className="stats-kpi-card terra">
            <svg className="stats-kpi-ornament" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <polygon points="24,4 28,16 40,12 32,20 44,24 32,28 40,36 28,32 24,44 20,32 8,36 16,28 4,24 16,20 8,12 20,16" stroke="rgba(212,137,26,1)" strokeWidth="0.8"/>
            </svg>
            <p className="stats-kpi-label">{t.totalImports}</p>
            <p className="stats-kpi-value terra">
              ${africaTotals?.imports_billions ? africaTotals.imports_billions.toFixed(0) : '761'}B
            </p>
            <p className="stats-kpi-footer">
              <TrendingDown style={{ width: 12, height: 12 }} />
              {t.estimated2024}
            </p>
          </div>

          {/* Pays Membres */}
          <div className="stats-kpi-card violet">
            <svg className="stats-kpi-ornament" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <polygon points="24,4 28,16 40,12 32,20 44,24 32,28 40,36 28,32 24,44 20,32 8,36 16,28 4,24 16,20 8,12 20,16" stroke="rgba(212,137,26,1)" strokeWidth="0.8"/>
            </svg>
            <p className="stats-kpi-label">{t.memberCountries}</p>
            <p className="stats-kpi-value violet">
              {statistics.overview?.african_countries_members || 54}
            </p>
            <p className="stats-kpi-footer">
              <Globe style={{ width: 12, height: 12 }} />
              AfCFTA
            </p>
          </div>
        </div>

        {/* Top 10 Exportateurs / Importateurs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Exportateurs */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp style={{ width: 16, height: 16, color: '#34d399' }} />
              <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#34d399', margin: 0 }}>
                {t.top10Exporters}
              </h3>
            </div>
            <div className="space-y-1">
              {statistics.top_exporters_2024?.slice(0, 10).map((exporter, index) => {
                const val = (exporter.exports_2024 / 1e9).toFixed(1);
                const pct = Math.min(100, (exporter.exports_2024 / 1e9 / maxExport) * 100);
                return (
                  <div key={index} className="stats-rank-item green">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`stats-rank-badge ${getRankClass(index)}`}>{index + 1}</span>
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#EAE0D0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {translateCountry(exporter.name)}
                      </span>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <p style={{ fontSize: '0.82rem', fontWeight: 700, color: '#34d399', margin: 0 }}>${val}B</p>
                      <p style={{ fontSize: '0.68rem', color: 'rgba(142,155,174,0.7)', margin: 0 }}>{exporter.share_pct}% {t.ofTotal}</p>
                      <div className="stats-progress-bar" style={{ width: 64 }}>
                        <div className="stats-progress-fill green" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Importateurs */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingDown style={{ width: 16, height: 16, color: '#38bdf8' }} />
              <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#38bdf8', margin: 0 }}>
                {t.top10Importers}
              </h3>
            </div>
            <div className="space-y-1">
              {statistics.top_importers_2024?.slice(0, 10).map((importer, index) => {
                const val = (importer.imports_2024 / 1e9).toFixed(1);
                const pct = Math.min(100, (importer.imports_2024 / 1e9 / maxImport) * 100);
                return (
                  <div key={index} className="stats-rank-item blue">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`stats-rank-badge ${getRankClass(index)}`}>{index + 1}</span>
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#EAE0D0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {translateCountry(importer.name)}
                      </span>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <p style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8', margin: 0 }}>${val}B</p>
                      <p style={{ fontSize: '0.68rem', color: 'rgba(142,155,174,0.7)', margin: 0 }}>{importer.share_pct}% {t.ofTotal}</p>
                      <div className="stats-progress-bar" style={{ width: 64 }}>
                        <div className="stats-progress-fill blue" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* ── Top 10 PIB Africains 2024 ──────────────────────────── */}
      <div className="stats-chart-card">
        <div className="stats-chart-header gold">
          <div className="stats-chart-title gold">
            <DollarSign style={{ width: 18, height: 18 }} />
            {language === 'fr' ? 'Top 10 PIB Africains 2024' : 'Top 10 African GDP 2024'}
          </div>
          <div className="stats-chart-subtitle">
            {language === 'fr'
              ? 'Avec projections de croissance 2025 — Source: FMI, Banque Mondiale'
              : 'With 2025 growth projections — Source: IMF, World Bank'}
          </div>
        </div>
        <div style={{ padding: '0 0 16px', overflowX: 'auto' }}>
          <table className="stats-table">
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>#</th>
                <th style={{ textAlign: 'left' }}>{language === 'fr' ? 'Pays' : 'Country'}</th>
                <th style={{ textAlign: 'right' }}>{language === 'fr' ? 'PIB 2024' : 'GDP 2024'}</th>
                <th style={{ textAlign: 'right' }}>{language === 'fr' ? 'Croissance' : 'Growth'}</th>
                <th style={{ textAlign: 'right' }}>{language === 'fr' ? 'Proj. 2025' : 'Proj. 2025'}</th>
              </tr>
            </thead>
            <tbody>
              {statistics.top_10_gdp_2024?.map((country, index) => (
                <tr key={index}>
                  <td>
                    <span className={`stats-rank-badge ${getRankClass(index)}`}>{country.rank}</span>
                  </td>
                  <td style={{ fontWeight: 600 }}>{translateCountry(country.country)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 700, color: '#fbbf24' }}>
                    ${country.gdp_2024_billion?.toFixed(1)}B
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className={`stats-chip ${parseFloat(country.growth_2024) >= 3 ? 'up' : 'down'}`}>
                      {typeof country.growth_2024 === 'number' ? country.growth_2024.toFixed(1) : country.growth_2024}%
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 700, padding: '2px 8px', borderRadius: 6, background: country.growth_projection_2025 !== 'N/A' ? 'rgba(212,137,26,0.15)' : 'rgba(255,255,255,0.06)', color: country.growth_projection_2025 !== 'N/A' ? '#fbbf24' : 'rgba(142,155,174,0.6)' }}>
                      {country.growth_projection_2025 || 'N/A'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="stats-source-note">
            {language === 'fr'
              ? 'Données officielles FMI WEO Octobre 2025, Banque Mondiale.'
              : 'Official IMF WEO October 2025, World Bank data.'}
          </p>
        </div>
      </div>

      {/* ── Évolution du Commerce Intra-Africain ───────────────── */}
      <div className="stats-chart-card">
        <div className="stats-chart-header" style={{ borderBottomColor: 'rgba(155,110,245,0.2)' }}>
          <div className="stats-chart-title violet">
            <TrendingUp style={{ width: 18, height: 18 }} />
            {t.intraAfricanEvolution}
          </div>
          <div className="stats-chart-subtitle">{t.trend2023_2030}</div>
        </div>
        <div style={{ padding: '16px 8px' }}>
          {statistics.trade_evolution && (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart
                data={[
                  { année: '2023', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2023) },
                  { année: '2024', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2024) },
                  { année: '2025', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.12, proj: true },
                  { année: '2027', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.30, proj: true },
                  { année: '2030', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.52, proj: true },
                ]}
                margin={{ left: 60, right: 20, top: 10, bottom: 10 }}
              >
                <defs>
                  <linearGradient id="gradIntra" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#9B6EF5" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#9B6EF5" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="année" tick={{ fontSize: 12, fill: 'rgba(142,155,174,0.8)', fontWeight: 600 }} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fontSize: 11, fill: 'rgba(142,155,174,0.7)' }}
                  axisLine={false} tickLine={false}
                  label={{ value: t.billionUSD, angle: -90, position: 'insideLeft', offset: -10, style: { fontSize: 10, fill: 'rgba(142,155,174,0.6)' } }}
                />
                <Tooltip content={<AfricaTooltip />} />
                <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'rgba(142,155,174,0.8)' }} />
                <Area
                  type="monotone"
                  dataKey="valeur"
                  stroke="#9B6EF5"
                  strokeWidth={2.5}
                  fill="url(#gradIntra)"
                  name={t.intraAfricanTrade}
                  dot={{ fill: '#9B6EF5', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#a78bfa' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── Top 5 PIB — Commerce Monde vs Intra-Africain ──────── */}
      {statistics.top_5_gdp_trade_comparison && statistics.top_5_gdp_trade_comparison.length > 0 && (
        <div className="stats-chart-card">
          <div className="stats-chart-header blue">
            <div className="stats-chart-title blue">
              <Globe style={{ width: 18, height: 18 }} />
              {t.top5GDP}
            </div>
            <div className="stats-chart-subtitle">{t.worldVsIntraAfrican}</div>
          </div>
          <div style={{ padding: '16px 8px' }}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Graphique Barres */}
              <ResponsiveContainer width="100%" height={340}>
                <BarChart
                  data={statistics.top_5_gdp_trade_comparison.map(country => ({
                    pays: translateCountry(country.country),
                    [t.exportsWorld]: parseFloat(country.exports_world),
                    [t.exportsIntraAfr]: parseFloat(country.exports_intra_african),
                    [t.importsWorld]: parseFloat(country.imports_world),
                    [t.importsIntraAfr]: parseFloat(country.imports_intra_african)
                  }))}
                  layout="vertical"
                  margin={{ left: 10, right: 30, top: 10, bottom: 10 }}
                >
                  <defs>
                    <linearGradient id="gExpWorld" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#1A7A4A" /><stop offset="100%" stopColor="#34d399" />
                    </linearGradient>
                    <linearGradient id="gExpIntra" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#0E8A7A" /><stop offset="100%" stopColor="#6ee7b7" />
                    </linearGradient>
                    <linearGradient id="gImpWorld" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#1A6B8A" /><stop offset="100%" stopColor="#38bdf8" />
                    </linearGradient>
                    <linearGradient id="gImpIntra" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#1B6CA8" /><stop offset="100%" stopColor="#93c5fd" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis
                    type="number"
                    label={{ value: t.billionUSD, position: 'insideBottom', offset: -8, style: { fontSize: 10, fill: 'rgba(142,155,174,0.6)', fontWeight: 600 } }}
                    tick={{ fontSize: 10, fill: 'rgba(142,155,174,0.7)' }}
                    axisLine={false} tickLine={false}
                  />
                  <YAxis
                    type="category" dataKey="pays" width={110}
                    tick={{ fontSize: 11, fontWeight: 700, fill: '#EAE0D0' }}
                    axisLine={false} tickLine={false}
                  />
                  <Tooltip
                    formatter={(value) => `$${value.toFixed(1)}B`}
                    contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                    labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
                  />
                  <Legend wrapperStyle={{ fontSize: '0.72rem', color: 'rgba(142,155,174,0.8)' }} />
                  <Bar dataKey={t.exportsWorld}    fill="url(#gExpWorld)" radius={[0, 4, 4, 0]} maxBarSize={14} />
                  <Bar dataKey={t.exportsIntraAfr} fill="url(#gExpIntra)" radius={[0, 4, 4, 0]} maxBarSize={14} />
                  <Bar dataKey={t.importsWorld}    fill="url(#gImpWorld)" radius={[0, 4, 4, 0]} maxBarSize={14} />
                  <Bar dataKey={t.importsIntraAfr} fill="url(#gImpIntra)" radius={[0, 4, 4, 0]} maxBarSize={14} />
                </BarChart>
              </ResponsiveContainer>

              {/* Tableau Détaillé */}
              <div>
                <p style={{ fontSize: '0.78rem', fontWeight: 700, color: 'rgba(142,155,174,0.8)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
                  {t.detailByCountry}
                </p>
                <div className="space-y-3">
                  {statistics.top_5_gdp_trade_comparison.map((country, index) => (
                    <div key={index} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: '12px 14px', borderLeft: '3px solid #1A6B8A' }}>
                      <div className="flex justify-between items-center mb-2">
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#EAE0D0' }}>{translateCountry(country.country)}</span>
                        <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '2px 8px', borderRadius: 100, background: 'rgba(155,110,245,0.18)', color: '#a78bfa', border: '1px solid rgba(155,110,245,0.25)' }}>
                          {language === 'en' ? 'GDP' : 'PIB'}: ${country.gdp_2024}B
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <p style={{ fontSize: '0.68rem', color: 'rgba(142,155,174,0.6)', margin: 0 }}>{t.expWorld}</p>
                          <p style={{ fontSize: '0.82rem', fontWeight: 700, color: '#34d399', margin: 0 }}>${country.exports_world.toFixed(1)}B</p>
                        </div>
                        <div>
                          <p style={{ fontSize: '0.68rem', color: 'rgba(142,155,174,0.6)', margin: 0 }}>{t.expIntraAfr}</p>
                          <p style={{ fontSize: '0.82rem', fontWeight: 700, color: '#6ee7b7', margin: 0 }}>${country.exports_intra_african.toFixed(1)}B <span style={{ fontSize: '0.68rem', color: 'rgba(142,155,174,0.6)' }}>({country.intra_african_percentage}%)</span></p>
                        </div>
                        <div>
                          <p style={{ fontSize: '0.68rem', color: 'rgba(142,155,174,0.6)', margin: 0 }}>{t.impWorld}</p>
                          <p style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8', margin: 0 }}>${country.imports_world.toFixed(1)}B</p>
                        </div>
                        <div>
                          <p style={{ fontSize: '0.68rem', color: 'rgba(142,155,174,0.6)', margin: 0 }}>{t.impIntraAfr}</p>
                          <p style={{ fontSize: '0.82rem', fontWeight: 700, color: '#93c5fd', margin: 0 }}>${country.imports_intra_african.toFixed(1)}B</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Répartition par Secteur ────────────────────────────── */}
      {statistics.sector_performance && Object.keys(statistics.sector_performance).length > 0 && (
        <div className="stats-chart-card">
          <div className="stats-chart-header terra">
            <div className="stats-chart-title terra">
              <BarChart3 style={{ width: 18, height: 18 }} />
              {t.sectorPerformance}
            </div>
            <div className="stats-chart-subtitle">{t.sectorDistribution}</div>
          </div>
          <div style={{ padding: '16px 8px' }}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={Object.entries(statistics.sector_performance).slice(0, 8).map(([key, value]) => {
                      const shareValue = typeof value === 'object' && value.share ? value.share
                                       : typeof value === 'object' && value.value_2024 ? value.value_2024
                                       : parseFloat(value) || 10;
                      return { name: key.replace(/_/g, ' '), value: parseFloat(shareValue) };
                    })}
                    cx="50%" cy="50%"
                    outerRadius={100}
                    innerRadius={36}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {Object.entries(statistics.sector_performance).slice(0, 8).map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0.3)" strokeWidth={1} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => [`${parseFloat(value).toFixed(1)}%`, '']}
                    contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                    labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
                  />
                  <Legend wrapperStyle={{ fontSize: '0.72rem', color: 'rgba(142,155,174,0.8)' }} />
                </PieChart>
              </ResponsiveContainer>

              <div>
                <p style={{ fontSize: '0.78rem', fontWeight: 700, color: 'rgba(142,155,174,0.8)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
                  {t.sectorDetails}
                </p>
                <div className="space-y-2">
                  {Object.entries(statistics.sector_performance).slice(0, 8).map(([key, value], index) => {
                    const shareValue = typeof value === 'object' && value.share ? value.share
                                     : typeof value === 'object' && value.value_2024 ? value.value_2024
                                     : parseFloat(value) || 10;
                    const displayName = key.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                    const pct = parseFloat(shareValue).toFixed(1);
                    return (
                      <div key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 10, height: 10, borderRadius: 2, background: COLORS[index % COLORS.length], flexShrink: 0 }} />
                          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#EAE0D0' }}>{displayName}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="stats-progress-bar" style={{ width: 60 }}>
                            <div style={{ height: '100%', borderRadius: 2, background: COLORS[index % COLORS.length], width: `${Math.min(100, parseFloat(pct) * 5)}%` }} />
                          </div>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: COLORS[index % COLORS.length], minWidth: 32, textAlign: 'right' }}>{pct}%</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Source Footer ──────────────────────────────────────── */}
      <div className="stats-source-note" style={{ background: 'rgba(18,24,32,0.5)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)' }}>
        {language === 'en'
          ? 'Sources: IMF World Economic Outlook 2024 · World Bank WDI · UNCTAD COMTRADE · AfCFTA Secretariat · African Development Bank'
          : 'Sources: FMI World Economic Outlook 2024 · Banque Mondiale WDI · UNCTAD COMTRADE · Secrétariat ZLECAf · Banque Africaine de Développement'}
      </div>
    </div>
  );
};

export default StatisticsZaubaStyle;
