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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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
      source: "Sources: IMF WEO 2024, World Bank, UNDP, OEC"
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
      source: "Sources: IMF WEO 2024, World Bank, UNDP, OEC"
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
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <Scale className="h-8 w-8 text-purple-600" />
          <h2 className="text-3xl font-black text-slate-900 uppercase tracking-tight">
            {txt.title}
          </h2>
        </div>
        <p className="text-slate-500">{txt.subtitle}</p>
      </div>

      {/* Country Selection */}
      <Card className="shadow-lg">
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* Selected Countries */}
            <div className="flex flex-wrap gap-2 flex-1">
              {selectedCountries.map((iso, idx) => (
                <Badge 
                  key={iso} 
                  className="px-3 py-2 text-sm font-medium"
                  style={{ backgroundColor: COUNTRY_COLORS[idx], color: 'white' }}
                >
                  {getCountryName(iso)}
                  <button 
                    onClick={() => removeCountry(iso)}
                    className="ml-2 hover:bg-white/20 rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              
              {selectedCountries.length < MAX_COUNTRIES && (
                <Select onValueChange={addCountry}>
                  <SelectTrigger className="w-[200px]" data-testid="add-country-select">
                    <SelectValue placeholder={txt.selectCountry} />
                  </SelectTrigger>
                  <SelectContent>
                    {availableCountries
                      .filter(c => !selectedCountries.includes(c.iso3 || c.code))
                      .map((country) => (
                        <SelectItem 
                          key={country.iso3 || country.code} 
                          value={country.iso3 || country.code}
                        >
                          {country.name_fr || country.name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                onClick={fetchComparisonData}
                disabled={selectedCountries.length < 2 || loading}
                className="bg-purple-600 hover:bg-purple-700"
                data-testid="compare-btn"
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
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                {txt.reset}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
          <span className="ml-3 text-slate-600">{txt.loading}</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !error && selectedCountries.length < 2 && (
        <Card className="bg-slate-50 border-slate-200">
          <CardContent className="py-16 text-center">
            <Globe className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">{txt.noSelection}</p>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {!loading && !error && hasData && (
        <>
          {/* Radar Chart */}
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-purple-600" />
                {txt.radarComparison}
              </CardTitle>
              <CardDescription>
                {language === 'fr' 
                  ? 'Comparaison normalisée des indicateurs clés (0-100)' 
                  : 'Normalized comparison of key indicators (0-100)'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={getRadarData()}>
                  <PolarGrid stroke="#e2e8f0" />
                  <PolarAngleAxis 
                    dataKey="indicator" 
                    tick={{ fill: '#64748b', fontSize: 12 }}
                  />
                  <PolarRadiusAxis 
                    angle={30} 
                    domain={[0, 100]}
                    tick={{ fill: '#94a3b8', fontSize: 10 }}
                  />
                  {selectedCountries.map((iso, idx) => (
                    <Radar
                      key={iso}
                      name={getCountryName(iso)}
                      dataKey={getCountryName(iso)}
                      stroke={COUNTRY_COLORS[idx]}
                      fill={COUNTRY_COLORS[idx]}
                      fillOpacity={0.2}
                      strokeWidth={2}
                    />
                  ))}
                  <Legend />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Economic Indicators Table */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-emerald-600" />
                {txt.economicIndicators}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{txt.indicator}</TableHead>
                    {selectedCountries.map((iso, idx) => (
                      <TableHead key={iso} style={{ color: COUNTRY_COLORS[idx] }}>
                        {getCountryName(iso)}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">{txt.gdp} (Mrd $)</TableCell>
                    {getEconomicData().map((d, idx) => (
                      <TableCell key={idx} className="font-bold">
                        {d.gdp ? `$${d.gdp.toFixed(1)}B` : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.gdpPerCapita}</TableCell>
                    {getEconomicData().map((d, idx) => (
                      <TableCell key={idx}>
                        {d.gdpPerCapita ? formatValue(d.gdpPerCapita) : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.inflation}</TableCell>
                    {getEconomicData().map((d, idx) => (
                      <TableCell key={idx}>
                        {d.inflation ? formatPercent(d.inflation) : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.unemployment}</TableCell>
                    {getEconomicData().map((d, idx) => (
                      <TableCell key={idx}>
                        {d.unemployment ? formatPercent(d.unemployment) : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.population} (M)</TableCell>
                    {getEconomicData().map((d, idx) => (
                      <TableCell key={idx}>
                        {d.population ? `${d.population.toFixed(1)}M` : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Trade Bar Chart */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-blue-600" />
                {txt.barComparison} - {txt.tradeIndicators}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getTradeBarData()}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tickFormatter={(v) => `$${v}M`} />
                  <Tooltip 
                    formatter={(value) => [`$${value.toFixed(0)}M`, '']}
                    contentStyle={{ borderRadius: '8px' }}
                  />
                  <Legend />
                  <Bar dataKey={txt.exports} fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey={txt.imports} fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Trade Indicators Table */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-blue-600" />
                {txt.tradeIndicators}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{txt.indicator}</TableHead>
                    {selectedCountries.map((iso, idx) => (
                      <TableHead key={iso} style={{ color: COUNTRY_COLORS[idx] }}>
                        {getCountryName(iso)}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">{txt.exports} (M$)</TableCell>
                    {getTradeData().map((d, idx) => (
                      <TableCell key={idx} className="text-emerald-600 font-bold">
                        {d.exports ? `$${d.exports.toFixed(0)}M` : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.imports} (M$)</TableCell>
                    {getTradeData().map((d, idx) => (
                      <TableCell key={idx} className="text-blue-600 font-bold">
                        {d.imports ? `$${d.imports.toFixed(0)}M` : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.tradeBalance}</TableCell>
                    {getTradeData().map((d, idx) => (
                      <TableCell 
                        key={idx} 
                        className={`font-bold ${d.balance >= 0 ? 'text-emerald-600' : 'text-red-600'}`}
                      >
                        {d.balance ? `${d.balance >= 0 ? '+' : ''}$${d.balance.toFixed(0)}M` : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.intraAfrican}</TableCell>
                    {getTradeData().map((d, idx) => (
                      <TableCell key={idx}>
                        {d.intraAfrican ? formatPercent(d.intraAfrican) : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Development Indices */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-purple-600" />
                {txt.developmentIndices}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{txt.indicator}</TableHead>
                    {selectedCountries.map((iso, idx) => (
                      <TableHead key={iso} style={{ color: COUNTRY_COLORS[idx] }}>
                        {getCountryName(iso)}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">{txt.hdi} (Score)</TableCell>
                    {getDevelopmentData().map((d, idx) => (
                      <TableCell key={idx} className="font-bold">
                        {d.hdi ? d.hdi.toFixed(3) : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.hdi} (Rang)</TableCell>
                    {getDevelopmentData().map((d, idx) => (
                      <TableCell key={idx}>
                        #{d.hdiRank}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.gai} (Score)</TableCell>
                    {getDevelopmentData().map((d, idx) => (
                      <TableCell key={idx} className="font-bold">
                        {d.gai ? d.gai.toFixed(1) : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">{txt.gai} (Rang)</TableCell>
                    {getDevelopmentData().map((d, idx) => (
                      <TableCell key={idx}>
                        #{d.gaiRank}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Source Footer */}
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <p className="text-xs text-slate-400 italic">{txt.source}</p>
            <DataFreshnessIndicator freshness={dataFreshness} language={language} />
          </div>
        </>
      )}
    </div>
  );
}
