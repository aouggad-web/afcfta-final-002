/**
 * Multi-Country Comparison Component
 * Compare up to 4 African countries side by side
 * Features: Economic indicators, trade volumes, radar chart, bar charts
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { 
  BarChart3, TrendingUp, Globe, DollarSign, Users, 
  Loader2, AlertCircle, Plus, X, RefreshCw, Scale
} from 'lucide-react';
import { DataFreshnessIndicator } from '../ui/data-freshness-indicator';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Color palette for countries
const COUNTRY_COLORS = ['#059669', '#0891b2', '#7c3aed', '#dc2626'];

// Format currency values
const formatValue = (value) => {
  if (!value || isNaN(value)) return '-';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
};

// Format percentage
const formatPercent = (value) => {
  if (!value || isNaN(value)) return '-';
  return `${value.toFixed(1)}%`;
};

// Normalize value for radar chart (0-100 scale)
const normalizeForRadar = (value, max) => {
  if (!value || !max) return 0;
  return Math.min(100, (value / max) * 100);
};

/* High inflation threshold for color-coding (8% as per IMF classification for "high inflation") */
const HIGH_INFLATION_THRESHOLD = 8;

export default function MultiCountryComparison({ language = 'fr' }) {
  const [availableCountries, setAvailableCountries] = useState([]);
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [countryData, setCountryData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dataFreshness, setDataFreshness] = useState(null);

  const MAX_COUNTRIES = 4;

  const texts = {
    fr: {
      title: "Comparaison Multi-Pays",
      subtitle: "Comparez jusqu'à 4 pays africains côte à côte",
      selectCountry: "Ajouter un pays",
      compare: "Comparer",
      reset: "Réinitialiser",
      loading: "Chargement des données...",
      noSelection: "Sélectionnez au moins 2 pays pour comparer",
      economicIndicators: "Indicateurs Économiques",
      tradeIndicators: "Indicateurs Commerciaux",
      developmentIndices: "Indices de Développement",
      radarComparison: "Comparaison Radar",
      barComparison: "Comparaison par Barres",
      gdp: "PIB",
      gdpPerCapita: "PIB/Habitant",
      inflation: "Inflation",
      unemployment: "Chômage",
      exports: "Exportations",
      imports: "Importations",
      tradeBalance: "Balance",
      intraAfrican: "Commerce Intra-Africain",
      hdi: "IDH",
      gai: "GAI",
      population: "Population",
      indicator: "Indicateur",
      source: "Sources: IMF WEO 2024, World Bank, UNDP, OEC",
      sourceEconomic: "Source : Banque Mondiale (WB Open Data) + FMI WEO 2024",
      sourceTrade: "Source : OEC — Observatoire de la Complexité Économique (atlas.cid.harvard.edu)",
      sourceDevelopment: "Source : PNUD (HDI 2024) + Mo Ibrahim Foundation (GAI 2024)"
    },
    en: {
      title: "Multi-Country Comparison",
      subtitle: "Compare up to 4 African countries side by side",
      selectCountry: "Add a country",
      compare: "Compare",
      reset: "Reset",
      loading: "Loading data...",
      noSelection: "Select at least 2 countries to compare",
      economicIndicators: "Economic Indicators",
      tradeIndicators: "Trade Indicators",
      developmentIndices: "Development Indices",
      radarComparison: "Radar Comparison",
      barComparison: "Bar Comparison",
      gdp: "GDP",
      gdpPerCapita: "GDP/Capita",
      inflation: "Inflation",
      unemployment: "Unemployment",
      exports: "Exports",
      imports: "Imports",
      tradeBalance: "Balance",
      intraAfrican: "Intra-African Trade",
      hdi: "HDI",
      gai: "GAI",
      population: "Population",
      indicator: "Indicator",
      source: "Sources: IMF WEO 2024, World Bank, UNDP, OEC",
      sourceEconomic: "Source: World Bank (WB Open Data) + IMF WEO 2024",
      sourceTrade: "Source: OEC — Observatory of Economic Complexity (atlas.cid.harvard.edu)",
      sourceDevelopment: "Source: UNDP (HDI 2024) + Mo Ibrahim Foundation (GAI 2024)"
    }
  };

  const txt = texts[language] || texts.fr;

  // Fetch available countries
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const response = await axios.get(`${API}/countries?lang=${language}`);
        const countries = response.data.countries || response.data || [];
        setAvailableCountries(countries.sort((a, b) => 
          (a.name_fr || a.name || '').localeCompare(b.name_fr || b.name || '')
        ));
      } catch (err) {
        console.error('Error fetching countries:', err);
      }
    };
    fetchCountries();
  }, [language]);

  // Add country to selection
  const addCountry = (countryIso) => {
    if (selectedCountries.length < MAX_COUNTRIES && !selectedCountries.includes(countryIso)) {
      setSelectedCountries([...selectedCountries, countryIso]);
    }
  };

  // Remove country from selection
  const removeCountry = (countryIso) => {
    setSelectedCountries(selectedCountries.filter(c => c !== countryIso));
    const newData = { ...countryData };
    delete newData[countryIso];
    setCountryData(newData);
  };

  // Reset selection
  const resetSelection = () => {
    setSelectedCountries([]);
    setCountryData({});
    setError(null);
  };

  // Fetch data for all selected countries
  const fetchComparisonData = useCallback(async () => {
    if (selectedCountries.length < 2) return;

    setLoading(true);
    setError(null);

    try {
      const dataPromises = selectedCountries.map(async (iso) => {
        const countryInfo = availableCountries.find(c => c.iso3 === iso || c.code === iso);
        const countryName = countryInfo?.name_fr || countryInfo?.name || iso;
        
        // Try AI profile first, fallback to country-profile endpoint
        try {
          const profileRes = await axios.get(`${API}/ai/profile/${countryName}?lang=${language}`);
          return { iso, data: profileRes.data, source: 'ai' };
        } catch {
          // Fallback to country-profile endpoint with full economic data
          try {
            const countryProfileRes = await axios.get(`${API}/country-profile/${iso}`);
            // Transform country-profile data to match AI format
            const profile = countryProfileRes.data;
            const transformedData = {
              country_name: profile.country_name,
              economic_indicators: {
                gdp_billion_usd: profile.gdp_usd ? profile.gdp_usd / 1e9 : 0,
                gdp_per_capita_usd: profile.gdp_per_capita || 0,
                inflation_percent: profile.inflation_rate || 0,
                unemployment_percent: profile.unemployment_rate || 0,
                population_millions: profile.population_millions || (profile.population ? profile.population / 1e6 : 0)
              },
              development_indices: {
                hdi_score: profile.hdi || profile.projections?.development_index || 0,
                hdi_world_rank: profile.hdi_rank || '-',
                gai_score: profile.projections?.gai_score || 0,
                gai_world_rank: profile.projections?.gai_rank || '-'
              },
              trade_summary: {
                total_exports_musd: (profile.projections?.exports_2024_billion_usd || 0) * 1000,
                total_imports_musd: (profile.projections?.imports_2024_billion_usd || 0) * 1000,
                trade_balance_musd: (profile.projections?.trade_balance_2024_billion_usd || 0) * 1000
              }
            };
            return { iso, data: transformedData, source: 'profile' };
          } catch {
            // Final fallback to basic country endpoint
            const basicRes = await axios.get(`${API}/countries/${iso}?lang=${language}`);
            return { iso, data: basicRes.data, source: 'basic' };
          }
        }
      });

      const results = await Promise.all(dataPromises);
      
      const newData = {};
      results.forEach(({ iso, data, source }) => {
        newData[iso] = { ...data, source };
        if (data.data_freshness) {
          setDataFreshness(data.data_freshness);
        }
      });
      
      setCountryData(newData);
    } catch (err) {
      console.error('Error fetching comparison data:', err);
      setError(language === 'fr' ? 'Erreur lors du chargement des données' : 'Error loading data');
    } finally {
      setLoading(false);
    }
  }, [selectedCountries, availableCountries, language]);

  // Get country name
  const getCountryName = (iso) => {
    const country = availableCountries.find(c => c.iso3 === iso || c.code === iso);
    return country?.name_fr || country?.name || iso;
  };

  // Extract economic indicators for comparison
  const getEconomicData = () => {
    return selectedCountries.map((iso, idx) => {
      const data = countryData[iso] || {};
      const eco = data.economic_indicators || data.economics || {};
      return {
        name: getCountryName(iso),
        color: COUNTRY_COLORS[idx],
        gdp: eco.gdp_billion_usd || eco.gdp || 0,
        gdpPerCapita: eco.gdp_per_capita_usd || eco.gdp_per_capita || 0,
        inflation: eco.inflation_percent || eco.inflation || 0,
        unemployment: eco.unemployment_percent || eco.unemployment || 0,
        population: eco.population_millions || (eco.population ? eco.population / 1e6 : 0)
      };
    });
  };

  // Extract trade data for comparison
  const getTradeData = () => {
    return selectedCountries.map((iso, idx) => {
      const data = countryData[iso] || {};
      const trade = data.trade_summary || data.trade || {};
      return {
        name: getCountryName(iso),
        color: COUNTRY_COLORS[idx],
        exports: trade.total_exports_musd || trade.exports || 0,
        imports: trade.total_imports_musd || trade.imports || 0,
        balance: trade.trade_balance_musd || trade.balance || 0,
        intraAfrican: trade.intra_african_trade_percent || trade.intra_african || 0
      };
    });
  };

  // Get development indices for comparison
  const getDevelopmentData = () => {
    return selectedCountries.map((iso, idx) => {
      const data = countryData[iso] || {};
      const dev = data.development_indices || data.development || {};
      return {
        name: getCountryName(iso),
        color: COUNTRY_COLORS[idx],
        hdi: dev.hdi_score || dev.hdi || 0,
        hdiRank: dev.hdi_world_rank || dev.hdi_rank || '-',
        gai: dev.gai_score || dev.gai || 0,
        gaiRank: dev.gai_world_rank || dev.gai_rank || '-'
      };
    });
  };

  // Prepare radar chart data
  const getRadarData = () => {
    const ecoData = getEconomicData();
    const tradeData = getTradeData();
    const devData = getDevelopmentData();

    // Find max values for normalization
    const maxGdp = Math.max(...ecoData.map(d => d.gdp));
    const maxExports = Math.max(...tradeData.map(d => d.exports));
    const maxImports = Math.max(...tradeData.map(d => d.imports));

    const indicators = [
      { name: txt.gdp, key: 'gdp' },
      { name: txt.exports, key: 'exports' },
      { name: txt.imports, key: 'imports' },
      { name: txt.hdi, key: 'hdi' },
      { name: txt.gai, key: 'gai' },
      { name: txt.intraAfrican, key: 'intraAfrican' }
    ];

    return indicators.map(ind => {
      const point = { indicator: ind.name };
      selectedCountries.forEach((iso, idx) => {
        const eco = ecoData[idx] || {};
        const trade = tradeData[idx] || {};
        const dev = devData[idx] || {};
        
        let value = 0;
        switch (ind.key) {
          case 'gdp': value = normalizeForRadar(eco.gdp, maxGdp); break;
          case 'exports': value = normalizeForRadar(trade.exports, maxExports); break;
          case 'imports': value = normalizeForRadar(trade.imports, maxImports); break;
          case 'hdi': value = (dev.hdi || 0) * 100; break;
          case 'gai': value = dev.gai || 0; break;
          case 'intraAfrican': value = trade.intraAfrican || 0; break;
          default: value = 0;
        }
        point[getCountryName(iso)] = Math.round(value);
      });
      return point;
    });
  };

  // Prepare bar chart data for GDP comparison
  const getGdpBarData = () => {
    return getEconomicData().map(d => ({
      name: d.name,
      [txt.gdp]: d.gdp,
      fill: d.color
    }));
  };

  // Prepare bar chart data for trade comparison
  const getTradeBarData = () => {
    return getTradeData().map(d => ({
      name: d.name,
      [txt.exports]: d.exports,
      [txt.imports]: d.imports,
      fill: d.color
    }));
  };

  const hasData = Object.keys(countryData).length >= 2;

  return (
    <div className="space-y-6" data-testid="multi-country-comparison">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="stats-hero">
        <div className="flex items-center gap-3 mb-2">
          <Scale style={{ width: 26, height: 26, color: '#D4891A', flexShrink: 0 }} />
          <div>
            <h2 className="stats-hero-title">{txt.title}</h2>
            <p className="stats-hero-subtitle">{txt.subtitle}</p>
          </div>
        </div>
        <div className="stats-kente-bar" style={{ width: 220, marginTop: 10 }} />
      </div>

      {/* ── Country Selection ──────────────────────────────────── */}
      <div className="stats-chart-card" style={{ padding: '20px 24px' }}>
        <div className="flex flex-wrap items-center gap-3">
          {/* Selected country tags */}
          <div className="flex flex-wrap gap-2 flex-1 min-w-0">
            {selectedCountries.map((iso, idx) => (
              <span
                key={iso}
                className="stats-country-tag"
                style={{ background: `color-mix(in srgb, ${COUNTRY_COLORS[idx]} 13%, transparent)`, borderColor: `color-mix(in srgb, ${COUNTRY_COLORS[idx]} 33%, transparent)`, color: COUNTRY_COLORS[idx] }}
              >
                {getCountryName(iso)}
                <button onClick={() => removeCountry(iso)}>
                  <X style={{ width: 13, height: 13 }} />
                </button>
              </span>
            ))}

            {selectedCountries.length < MAX_COUNTRIES && (
              <Select onValueChange={addCountry}>
                <SelectTrigger
                  className="w-[180px] h-8 text-sm"
                  data-testid="add-country-select"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(212,137,26,0.25)', color: '#EAE0D0', borderRadius: 8 }}
                >
                  <SelectValue placeholder={txt.selectCountry} />
                </SelectTrigger>
                <SelectContent>
                  {availableCountries
                    .filter(c => !selectedCountries.includes(c.iso3 || c.code))
                    .map((country) => (
                      <SelectItem key={country.iso3 || country.code} value={country.iso3 || country.code}>
                        {country.name_fr || country.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex gap-2 flex-shrink-0">
            <Button
              onClick={fetchComparisonData}
              disabled={selectedCountries.length < 2 || loading}
              data-testid="compare-btn"
              style={{
                background: selectedCountries.length < 2
                  ? 'rgba(155,110,245,0.2)'
                  : 'linear-gradient(135deg,#7c3aed,#9B6EF5)',
                border: '1px solid rgba(155,110,245,0.4)',
                color: '#EAE0D0', borderRadius: 8,
                padding: '6px 14px', fontSize: '0.82rem', fontWeight: 700,
                opacity: selectedCountries.length < 2 ? 0.5 : 1,
              }}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <BarChart3 className="h-4 w-4 mr-2" />
              )}
              {txt.compare}
            </Button>
            <Button
              variant="outline"
              onClick={resetSelection}
              disabled={selectedCountries.length === 0}
              style={{ border: '1px solid rgba(255,255,255,0.12)', background: 'transparent', color: 'rgba(234,224,208,0.7)', borderRadius: 8, padding: '6px 12px', fontSize: '0.82rem' }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {txt.reset}
            </Button>
          </div>
        </div>

        {/* Max countries hint */}
        <p style={{ fontSize: '0.7rem', color: 'rgba(142,155,174,0.5)', marginTop: 10 }}>
          {language === 'fr'
            ? `${selectedCountries.length} / ${MAX_COUNTRIES} pays sélectionnés`
            : `${selectedCountries.length} / ${MAX_COUNTRIES} countries selected`}
        </p>
      </div>

      {/* ── Loading ────────────────────────────────────────────── */}
      {loading && (
        <div className="stats-loading">
          <div className="stats-spinner" />
          <span style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.875rem' }}>{txt.loading}</span>
        </div>
      )}

      {/* ── Error ─────────────────────────────────────────────── */}
      {error && (
        <div className="stats-chart-card" style={{ padding: '32px 24px', textAlign: 'center' }}>
          <AlertCircle style={{ width: 32, height: 32, color: '#f87171', margin: '0 auto 12px' }} />
          <p style={{ color: '#f87171', fontWeight: 600 }}>{error}</p>
        </div>
      )}

      {/* ── Empty State ────────────────────────────────────────── */}
      {!loading && !error && selectedCountries.length < 2 && (
        <div className="stats-chart-card">
          <div className="stats-empty-state">
            <div className="stats-empty-icon">
              <Globe style={{ width: 28, height: 28, color: '#D4891A' }} />
            </div>
            <p style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.9rem' }}>{txt.noSelection}</p>
            <p style={{ color: 'rgba(142,155,174,0.4)', fontSize: '0.78rem', marginTop: 6 }}>
              {language === 'fr'
                ? 'Ajoutez au moins 2 pays africains pour commencer la comparaison'
                : 'Add at least 2 African countries to start the comparison'}
            </p>
          </div>
        </div>
      )}

      {/* ── Results ────────────────────────────────────────────── */}
      {!loading && !error && hasData && (
        <>
          {/* Radar Chart */}
          <div className="stats-chart-card">
            <div className="stats-chart-header" style={{ borderBottomColor: 'rgba(155,110,245,0.2)' }}>
              <div className="stats-chart-title violet">
                <TrendingUp style={{ width: 18, height: 18 }} />
                {txt.radarComparison}
              </div>
              <div className="stats-chart-subtitle">
                {language === 'fr'
                  ? 'Comparaison normalisée des indicateurs clés (0-100)'
                  : 'Normalized comparison of key indicators (0-100)'}
              </div>
            </div>
            <div style={{ padding: '16px 8px' }}>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={getRadarData()}>
                  <PolarGrid stroke="rgba(255,255,255,0.08)" />
                  <PolarAngleAxis dataKey="indicator" tick={{ fill: 'rgba(234,224,208,0.75)', fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: 'rgba(142,155,174,0.5)', fontSize: 10 }} axisLine={false} />
                  {selectedCountries.map((iso, idx) => (
                    <Radar
                      key={iso}
                      name={getCountryName(iso)}
                      dataKey={getCountryName(iso)}
                      stroke={COUNTRY_COLORS[idx]}
                      fill={COUNTRY_COLORS[idx]}
                      fillOpacity={0.15}
                      strokeWidth={2}
                    />
                  ))}
                  <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'rgba(142,155,174,0.8)' }} />
                  <Tooltip
                    contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                    labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Economic Indicators Table */}
          <div className="stats-chart-card">
            <div className="stats-chart-header">
              <div className="stats-chart-title" style={{ color: '#34d399' }}>
                <DollarSign style={{ width: 18, height: 18 }} />
                {txt.economicIndicators}
              </div>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="stats-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>{txt.indicator}</th>
                    {selectedCountries.map((iso, idx) => (
                      <th key={iso} style={{ textAlign: 'right', color: COUNTRY_COLORS[idx] }}>{getCountryName(iso)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: `${txt.gdp} (Mrd $)`, render: (d) => d.gdp ? <strong style={{ color: '#fbbf24' }}>${d.gdp.toFixed(1)}B</strong> : '-' },
                    { label: txt.gdpPerCapita, render: (d) => d.gdpPerCapita ? formatValue(d.gdpPerCapita) : '-' },
                    { label: txt.inflation, render: (d) => d.inflation ? <span className={`stats-chip ${d.inflation > HIGH_INFLATION_THRESHOLD ? 'down' : 'up'}`}>{formatPercent(d.inflation)}</span> : '-' },
                    { label: txt.unemployment, render: (d) => d.unemployment ? formatPercent(d.unemployment) : '-' },
                    { label: `${txt.population} (M)`, render: (d) => d.population ? `${d.population.toFixed(1)}M` : '-' },
                  ].map((row, ri) => (
                    <tr key={ri}>
                      <td style={{ fontWeight: 600, color: 'rgba(234,224,208,0.8)' }}>{row.label}</td>
                      {getEconomicData().map((d, idx) => (
                        <td key={idx} style={{ textAlign: 'right' }}>{row.render(d)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Trade Bar Chart */}
          <div className="stats-chart-card">
            <div className="stats-chart-header blue">
              <div className="stats-chart-title blue">
                <Globe style={{ width: 18, height: 18 }} />
                {txt.barComparison} — {txt.tradeIndicators}
              </div>
            </div>
            <div style={{ padding: '16px 8px' }}>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getTradeBarData()}>
                  <defs>
                    <linearGradient id="mcGradExp" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1A7A4A" /><stop offset="100%" stopColor="#34d399" />
                    </linearGradient>
                    <linearGradient id="mcGradImp" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1A6B8A" /><stop offset="100%" stopColor="#38bdf8" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'rgba(234,224,208,0.75)' }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={(v) => `$${v}M`} tick={{ fontSize: 10, fill: 'rgba(142,155,174,0.7)' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    formatter={(value) => [`$${value.toFixed(0)}M`, '']}
                    contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                    labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
                  />
                  <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'rgba(142,155,174,0.8)' }} />
                  <Bar dataKey={txt.exports} fill="url(#mcGradExp)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey={txt.imports} fill="url(#mcGradImp)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trade Indicators Table */}
          <div className="stats-chart-card">
            <div className="stats-chart-header blue">
              <div className="stats-chart-title blue">
                <Globe style={{ width: 18, height: 18 }} />
                {txt.tradeIndicators}
              </div>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="stats-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>{txt.indicator}</th>
                    {selectedCountries.map((iso, idx) => (
                      <th key={iso} style={{ textAlign: 'right', color: COUNTRY_COLORS[idx] }}>{getCountryName(iso)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{txt.exports} (M$)</td>
                    {getTradeData().map((d, idx) => (
                      <td key={idx} style={{ textAlign: 'right', fontWeight: 700, color: '#34d399' }}>
                        {d.exports ? `$${d.exports.toFixed(0)}M` : '-'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{txt.imports} (M$)</td>
                    {getTradeData().map((d, idx) => (
                      <td key={idx} style={{ textAlign: 'right', fontWeight: 700, color: '#38bdf8' }}>
                        {d.imports ? `$${d.imports.toFixed(0)}M` : '-'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{txt.tradeBalance}</td>
                    {getTradeData().map((d, idx) => (
                      <td key={idx} style={{ textAlign: 'right', fontWeight: 700, color: d.balance >= 0 ? '#34d399' : '#f87171' }}>
                        {d.balance ? `${d.balance >= 0 ? '+' : ''}$${d.balance.toFixed(0)}M` : '-'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{txt.intraAfrican}</td>
                    {getTradeData().map((d, idx) => (
                      <td key={idx} style={{ textAlign: 'right' }}>
                        {d.intraAfrican ? formatPercent(d.intraAfrican) : '-'}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Development Indices */}
          <div className="stats-chart-card">
            <div className="stats-chart-header" style={{ borderBottomColor: 'rgba(155,110,245,0.2)' }}>
              <div className="stats-chart-title violet">
                <Users style={{ width: 18, height: 18 }} />
                {txt.developmentIndices}
              </div>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="stats-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>{txt.indicator}</th>
                    {selectedCountries.map((iso, idx) => (
                      <th key={iso} style={{ textAlign: 'right', color: COUNTRY_COLORS[idx] }}>{getCountryName(iso)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{txt.hdi} (Score)</td>
                    {getDevelopmentData().map((d, idx) => (
                      <td key={idx} style={{ textAlign: 'right', fontWeight: 700 }}>
                        {d.hdi ? d.hdi.toFixed(3) : '-'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{txt.hdi} ({language === 'fr' ? 'Rang' : 'Rank'})</td>
                    {getDevelopmentData().map((d, idx) => (
                      <td key={idx} style={{ textAlign: 'right', color: 'rgba(142,155,174,0.8)' }}>
                        #{d.hdiRank}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{txt.gai} (Score)</td>
                    {getDevelopmentData().map((d, idx) => (
                      <td key={idx} style={{ textAlign: 'right', fontWeight: 700 }}>
                        {d.gai ? d.gai.toFixed(1) : '-'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td style={{ fontWeight: 600 }}>{txt.gai} ({language === 'fr' ? 'Rang' : 'Rank'})</td>
                    {getDevelopmentData().map((d, idx) => (
                      <td key={idx} style={{ textAlign: 'right', color: 'rgba(142,155,174,0.8)' }}>
                        #{d.gaiRank}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Source Footer */}
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <p className="stats-source-note" style={{ margin: 0 }}>{txt.source}</p>
            <DataFreshnessIndicator freshness={dataFreshness} language={language} />
          </div>
        </>
      )}
    </div>
  );
}
