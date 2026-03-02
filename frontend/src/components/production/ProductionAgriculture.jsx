import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';
import { 
  Wheat, Beef, Fish, TrendingUp, Award, AlertTriangle, Loader2, 
  Info, Globe, BarChart3, RefreshCw, Search
} from 'lucide-react';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const CHART_COLORS = ['#10b981', '#059669', '#047857', '#065f46', '#064e3b', '#22c55e', '#16a34a', '#15803d', '#f59e0b', '#ef4444'];

function ProductionAgriculture({ language = 'fr' }) {
  const [selectedCountry, setSelectedCountry] = useState('CIV');
  const [faostatData, setFaostatData] = useState(null);
  const [faostatStats, setFaostatStats] = useState(null);
  const [commodities, setCommodities] = useState([]);
  const [topProducers, setTopProducers] = useState(null);
  const [selectedCommodity, setSelectedCommodity] = useState('661'); // Cocoa by default
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingTopProducers, setLoadingTopProducers] = useState(false);
  const [activeTab, setActiveTab] = useState('country');

  // Translations
  const texts = {
    fr: {
      title: "Production Agricole FAO 2024",
      subtitle: "Données officielles FAOSTAT - Production agricole africaine (2022-2024)",
      countries: "pays africains",
      products: "produits agricoles",
      loading: "Chargement des données FAO...",
      noData: "Données non disponibles",
      noDataDesc: "Aucune donnée disponible pour ce pays.",
      data: "Données",
      countryTab: "Par Pays",
      commodityTab: "Par Produit",
      compareTab: "Comparaison",
      selectCountry: "Sélectionner un pays",
      selectCommodity: "Sélectionner un produit",
      productionByYear: "Production par Année",
      tonnes: "tonnes",
      africa: "Afrique",
      topProducers: "Top Producteurs Africains",
      rank: "Rang",
      country: "Pays",
      production: "Production",
      year: "Année",
      trend: "Tendance",
      increasing: "En hausse",
      decreasing: "En baisse",
      stable: "Stable",
      change: "Variation",
      source: "Source: FAOSTAT (FAO) - Données 2024",
      refresh: "Actualiser",
      viewTopProducers: "Voir les Top Producteurs",
      commodityOverview: "Aperçu du Produit",
      countryProduction: "Production du Pays",
      noProductionData: "Pas de données de production pour ce pays",
      evolutionTitle: "Évolution de la Production",
      radarComparison: "Comparaison Multi-Produits"
    },
    en: {
      title: "FAO Agricultural Production 2024",
      subtitle: "Official FAOSTAT data - African agricultural production (2022-2024)",
      countries: "African countries",
      products: "agricultural products",
      loading: "Loading FAO data...",
      noData: "Data not available",
      noDataDesc: "No data available for this country.",
      data: "Data",
      countryTab: "By Country",
      commodityTab: "By Product",
      compareTab: "Comparison",
      selectCountry: "Select a country",
      selectCommodity: "Select a product",
      productionByYear: "Production by Year",
      tonnes: "tonnes",
      africa: "Africa",
      topProducers: "Top African Producers",
      rank: "Rank",
      country: "Country",
      production: "Production",
      year: "Year",
      trend: "Trend",
      increasing: "Increasing",
      decreasing: "Decreasing",
      stable: "Stable",
      change: "Change",
      source: "Source: FAOSTAT (FAO) - 2024 Data",
      refresh: "Refresh",
      viewTopProducers: "View Top Producers",
      commodityOverview: "Product Overview",
      countryProduction: "Country Production",
      noProductionData: "No production data for this country",
      evolutionTitle: "Production Evolution",
      radarComparison: "Multi-Product Comparison"
    }
  };
  const t = texts[language] || texts.fr;

  // Fetch FAOSTAT statistics on mount
  useEffect(() => {
    fetchFaostatStats();
    fetchCommodities();
  }, [language]);

  // Fetch country data when selected country changes
  useEffect(() => {
    if (selectedCountry) {
      fetchCountryData(selectedCountry);
    }
  }, [selectedCountry, language]);

  // Fetch top producers when commodity changes
  useEffect(() => {
    if (selectedCommodity) {
      fetchTopProducers(selectedCommodity);
    }
  }, [selectedCommodity, language]);

  const fetchFaostatStats = async () => {
    try {
      const response = await axios.get(`${API}/faostat/statistics`);
      setFaostatStats(response.data);
    } catch (error) {
      console.error('Error fetching FAOSTAT statistics:', error);
    }
  };

  const fetchCommodities = async () => {
    try {
      const response = await axios.get(`${API}/faostat/commodities?language=${language}`);
      setCommodities(response.data.commodities || []);
    } catch (error) {
      console.error('Error fetching commodities:', error);
    }
  };

  const fetchCountryData = async (countryIso3) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/faostat/production/${countryIso3}?language=${language}`);
      const d = response.data;
      const validData = typeof d === 'object' && d !== null && !Array.isArray(d) ? d : null;
      setFaostatData(validData);
      
      // Fetch trends for main commodity if available
      if (validData?.commodities && Object.keys(validData.commodities).length > 0) {
        const firstCommodity = Object.values(validData.commodities)[0];
        if (firstCommodity?.commodity_code) {
          fetchTrends(countryIso3, firstCommodity.commodity_code);
        }
      }
    } catch (error) {
      console.error('Error fetching country data:', error);
      setFaostatData(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchTopProducers = async (commodityCode) => {
    setLoadingTopProducers(true);
    try {
      const response = await axios.get(`${API}/faostat/top-producers/${commodityCode}?year=2024&limit=10&language=${language}`);
      setTopProducers(response.data);
    } catch (error) {
      console.error('Error fetching top producers:', error);
      setTopProducers(null);
    } finally {
      setLoadingTopProducers(false);
    }
  };

  const fetchTrends = async (countryIso3, commodityCode) => {
    try {
      const response = await axios.get(`${API}/faostat/trends/${countryIso3}/${commodityCode}?language=${language}`);
      setTrends(response.data);
    } catch (error) {
      console.error('Error fetching trends:', error);
      setTrends(null);
    }
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num.toLocaleString();
  };

  const getTrendBadge = (trend) => {
    switch(trend) {
      case 'increasing':
        return <Badge className="bg-green-500 text-white"><TrendingUp className="w-3 h-3 mr-1" />{t.increasing}</Badge>;
      case 'decreasing':
        return <Badge className="bg-red-500 text-white"><TrendingUp className="w-3 h-3 mr-1 rotate-180" />{t.decreasing}</Badge>;
      default:
        return <Badge className="bg-gray-500 text-white">{t.stable}</Badge>;
    }
  };

  // Prepare chart data for country production
  const prepareCountryChartData = () => {
    if (!faostatData?.commodities) return [];
    
    return Object.entries(faostatData.commodities).map(([name, data], index) => {
      const latestYear = Object.keys(data.years || {}).sort().pop();
      return {
        name: name.length > 15 ? name.substring(0, 15) + '...' : name,
        fullName: name,
        value: data.years?.[latestYear] || 0,
        year: latestYear,
        fill: CHART_COLORS[index % CHART_COLORS.length]
      };
    }).sort((a, b) => b.value - a.value);
  };

  // Prepare evolution data
  const prepareEvolutionData = () => {
    if (!faostatData?.commodities) return [];
    
    const years = faostatData.years_available || [2022, 2023, 2024];
    return years.map(year => {
      const dataPoint = { year };
      Object.entries(faostatData.commodities).forEach(([name, data]) => {
        if (data.years?.[year]) {
          dataPoint[name] = data.years[year];
        }
      });
      return dataPoint;
    });
  };

  // Prepare top producers chart data
  const prepareTopProducersData = () => {
    if (!topProducers?.top_producers) return [];
    
    return topProducers.top_producers.map((producer, index) => ({
      name: producer.country_name,
      value: producer.value,
      rank: producer.rank,
      fill: CHART_COLORS[index % CHART_COLORS.length]
    }));
  };

  return (
    <div className="space-y-6" data-testid="production-agriculture">
      {/* Header */}
      <Card className="bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 text-white shadow-xl overflow-hidden">
        <CardHeader>
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <CardTitle className="text-3xl font-bold flex items-center gap-3">
                <Wheat className="w-8 h-8" />
                {t.title}
              </CardTitle>
              <CardDescription className="text-green-100 text-lg mt-2">
                {t.subtitle}
              </CardDescription>
            </div>
            {faostatStats && (
              <div className="text-right">
                <Badge className="bg-white/20 text-white hover:bg-white/30 text-lg px-4 py-2">
                  {faostatStats.total_african_countries} {t.countries}
                </Badge>
                <p className="text-sm text-green-200 mt-2">
                  {faostatStats.commodities_with_data} {t.products}
                </p>
                <p className="text-xs text-green-300 mt-1">
                  {faostatStats.years_available?.join(', ')}
                </p>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 bg-green-100 p-1 h-auto">
          <TabsTrigger value="country" className="data-[state=active]:bg-green-600 data-[state=active]:text-white py-3" data-testid="country-tab">
            <Globe className="w-4 h-4 mr-2" /> {t.countryTab}
          </TabsTrigger>
          <TabsTrigger value="commodity" className="data-[state=active]:bg-green-600 data-[state=active]:text-white py-3" data-testid="commodity-tab">
            <Wheat className="w-4 h-4 mr-2" /> {t.commodityTab}
          </TabsTrigger>
          <TabsTrigger value="compare" className="data-[state=active]:bg-green-600 data-[state=active]:text-white py-3" data-testid="compare-tab">
            <BarChart3 className="w-4 h-4 mr-2" /> {t.compareTab}
          </TabsTrigger>
        </TabsList>

        {/* Country Tab */}
        <TabsContent value="country" className="space-y-6">
          {/* Country Selector */}
          <Card className="border-2 border-green-200 shadow-lg" style={{ overflow: 'visible' }}>
            <CardContent className="pt-6" style={{ overflow: 'visible' }}>
              <EnhancedCountrySelector
                value={selectedCountry}
                onChange={setSelectedCountry}
                label={t.selectCountry}
                variant="prominent"
                language={language}
              />
            </CardContent>
          </Card>

          {/* Loading State */}
          {loading && (
            <Card className="animate-pulse">
              <CardContent className="flex items-center justify-center h-48">
                <div className="text-center">
                  <Loader2 className="w-12 h-12 animate-spin text-green-600 mx-auto" />
                  <p className="mt-4 text-gray-600">{t.loading}</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Country Data */}
          {!loading && faostatData && (
            <>
              {/* Country Header */}
              <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div>
                      <CardTitle className="text-2xl text-green-800 flex items-center gap-3">
                        <span className="text-4xl">🌍</span>
                        {faostatData.country_name}
                      </CardTitle>
                      <CardDescription className="text-green-700 mt-2">
                        <Badge variant="outline" className="border-green-500 text-green-700 mr-2">
                          {faostatData.total_commodities} {t.products}
                        </Badge>
                        <Badge variant="outline" className="border-green-500 text-green-700">
                          {t.data} {faostatData.data_source}
                        </Badge>
                      </CardDescription>
                    </div>
                    {trends && (
                      <div className="text-right">
                        <p className="text-sm text-gray-600">{trends.commodity}</p>
                        {getTrendBadge(trends.trend)}
                        <p className="text-xs text-gray-500 mt-1">
                          {t.change}: {trends.change_percent > 0 ? '+' : ''}{trends.change_percent}%
                        </p>
                      </div>
                    )}
                  </div>
                </CardHeader>
              </Card>

              {/* Production Charts */}
              {faostatData.commodities && Object.keys(faostatData.commodities).length > 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Bar Chart */}
                  <Card className="shadow-lg">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-700 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-green-600" />
                        {t.countryProduction} 2024
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={350}>
                        <BarChart data={prepareCountryChartData()} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" tickFormatter={formatNumber} />
                          <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
                          <Tooltip 
                            formatter={(value) => [formatNumber(value) + ' ' + t.tonnes, t.production]}
                            labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                          />
                          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                            {prepareCountryChartData().map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.fill} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Pie Chart */}
                  <Card className="shadow-lg">
                    <CardHeader>
                      <CardTitle className="text-lg text-gray-700">{t.productionByYear}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={350}>
                        <PieChart>
                          <Pie
                            data={prepareCountryChartData().slice(0, 6)}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={120}
                            paddingAngle={2}
                            dataKey="value"
                          >
                            {prepareCountryChartData().slice(0, 6).map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.fill} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => formatNumber(value) + ' ' + t.tonnes} />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <Card className="border-l-4 border-l-amber-500">
                  <CardContent className="flex items-center gap-4 py-8">
                    <AlertTriangle className="w-12 h-12 text-amber-500" />
                    <div>
                      <h3 className="font-bold text-lg text-gray-800">{t.noData}</h3>
                      <p className="text-gray-600">{t.noProductionData}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Evolution Chart */}
              {faostatData.commodities && Object.keys(faostatData.commodities).length > 0 && (
                <Card className="shadow-lg">
                  <CardHeader className="bg-gradient-to-r from-green-50 to-teal-50">
                    <CardTitle className="text-xl text-green-700 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5" /> {t.evolutionTitle} (2022-2024)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <ResponsiveContainer width="100%" height={350}>
                      <LineChart data={prepareEvolutionData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="year" />
                        <YAxis tickFormatter={formatNumber} />
                        <Tooltip formatter={(value) => formatNumber(value) + ' ' + t.tonnes} />
                        <Legend />
                        {Object.keys(faostatData.commodities || {}).slice(0, 5).map((commodity, index) => (
                          <Line 
                            key={commodity}
                            type="monotone" 
                            dataKey={commodity} 
                            stroke={CHART_COLORS[index % CHART_COLORS.length]}
                            strokeWidth={3}
                            dot={{ r: 5 }}
                            activeDot={{ r: 8 }}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              )}

              {/* Production Details Table */}
              {faostatData.commodities && Object.keys(faostatData.commodities).length > 0 && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-lg text-gray-700">{t.countryProduction}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-green-50">
                            <th className="text-left p-3 font-semibold">{t.products}</th>
                            <th className="text-center p-3 font-semibold">2022</th>
                            <th className="text-center p-3 font-semibold">2023</th>
                            <th className="text-center p-3 font-semibold">2024</th>
                            <th className="text-center p-3 font-semibold">{t.trend}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(faostatData.commodities).map(([name, data], index) => {
                            const years = data.years || {};
                            const values = Object.values(years).filter(v => v > 0);
                            let trend = 'stable';
                            if (values.length >= 2) {
                              const change = (values[values.length - 1] - values[0]) / values[0] * 100;
                              trend = change > 5 ? 'increasing' : change < -5 ? 'decreasing' : 'stable';
                            }
                            
                            return (
                              <tr key={name} className="border-b hover:bg-gray-50">
                                <td className="p-3">
                                  <div className="flex items-center gap-2">
                                    <div 
                                      className="w-3 h-3 rounded-full" 
                                      style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
                                    />
                                    <span className="font-medium">{name}</span>
                                  </div>
                                </td>
                                <td className="text-center p-3 font-mono">{formatNumber(years[2022] || 0)}</td>
                                <td className="text-center p-3 font-mono">{formatNumber(years[2023] || 0)}</td>
                                <td className="text-center p-3 font-mono font-bold text-green-700">{formatNumber(years[2024] || 0)}</td>
                                <td className="text-center p-3">{getTrendBadge(trend)}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* Commodity Tab - Top Producers */}
        <TabsContent value="commodity" className="space-y-6">
          {/* Commodity Selector */}
          <Card className="border-2 border-amber-200 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex flex-col md:flex-row gap-4 items-end">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t.selectCommodity}</label>
                  <Select value={selectedCommodity} onValueChange={setSelectedCommodity}>
                    <SelectTrigger className="w-full" data-testid="commodity-select">
                      <SelectValue placeholder={t.selectCommodity} />
                    </SelectTrigger>
                    <SelectContent>
                      {commodities.map((commodity) => (
                        <SelectItem key={commodity.code} value={commodity.code}>
                          {commodity.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button 
                  onClick={() => fetchTopProducers(selectedCommodity)}
                  className="bg-amber-500 hover:bg-amber-600"
                  disabled={loadingTopProducers}
                >
                  {loadingTopProducers ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                  {t.viewTopProducers}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Loading */}
          {loadingTopProducers && (
            <Card className="animate-pulse">
              <CardContent className="flex items-center justify-center h-48">
                <Loader2 className="w-12 h-12 animate-spin text-amber-600" />
              </CardContent>
            </Card>
          )}

          {/* Top Producers Results */}
          {!loadingTopProducers && topProducers && (
            <>
              {/* Header */}
              <Card className="bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
                <CardHeader>
                  <CardTitle className="text-2xl text-amber-800 flex items-center gap-3">
                    <Award className="w-8 h-8 text-amber-500" />
                    {t.topProducers}: {topProducers.commodity_name}
                  </CardTitle>
                  <CardDescription className="text-amber-700">
                    {t.year} {topProducers.year} - {topProducers.data_source}
                  </CardDescription>
                </CardHeader>
              </Card>

              {/* Top Producers Chart */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-lg text-gray-700">{t.topProducers}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={prepareTopProducersData()} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" tickFormatter={formatNumber} />
                        <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                        <Tooltip formatter={(value) => [formatNumber(value) + ' ' + t.tonnes, t.production]} />
                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                          {prepareTopProducersData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Rankings Table */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-lg text-gray-700">{t.topProducers}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {topProducers.top_producers?.map((producer, index) => (
                        <div 
                          key={producer.country_iso3}
                          className={`flex items-center justify-between p-3 rounded-lg ${
                            index === 0 ? 'bg-gradient-to-r from-amber-100 to-yellow-100 border-2 border-amber-300' :
                            index === 1 ? 'bg-gray-100 border border-gray-300' :
                            index === 2 ? 'bg-gradient-to-r from-orange-50 to-amber-50 border border-amber-200' :
                            'bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                              index === 0 ? 'bg-amber-400 text-white' :
                              index === 1 ? 'bg-gray-400 text-white' :
                              index === 2 ? 'bg-amber-600 text-white' :
                              'bg-gray-200 text-gray-700'
                            }`}>
                              {producer.rank}
                            </span>
                            <span className="font-medium text-gray-800">{producer.country_name}</span>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-amber-700">{formatNumber(producer.value)}</p>
                            <p className="text-xs text-gray-500">{producer.unit}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        {/* Compare Tab */}
        <TabsContent value="compare" className="space-y-6">
          <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200">
            <CardHeader>
              <CardTitle className="text-2xl text-purple-800 flex items-center gap-3">
                <BarChart3 className="w-8 h-8 text-purple-600" />
                {t.radarComparison}
              </CardTitle>
              <CardDescription className="text-purple-700">
                {language === 'fr' 
                  ? 'Comparez la production de différents produits pour le pays sélectionné'
                  : 'Compare production of different products for the selected country'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {faostatData?.commodities && Object.keys(faostatData.commodities).length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={Object.entries(faostatData.commodities).slice(0, 6).map(([name, data]) => ({
                    product: name.length > 10 ? name.substring(0, 10) + '...' : name,
                    '2022': data.years?.[2022] || 0,
                    '2023': data.years?.[2023] || 0,
                    '2024': data.years?.[2024] || 0
                  }))}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="product" tick={{ fontSize: 11 }} />
                    <PolarRadiusAxis tickFormatter={formatNumber} />
                    <Radar name="2022" dataKey="2022" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.3} />
                    <Radar name="2023" dataKey="2023" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
                    <Radar name="2024" dataKey="2024" stroke="#10b981" fill="#10b981" fillOpacity={0.5} />
                    <Legend />
                    <Tooltip formatter={(value) => formatNumber(value) + ' ' + t.tonnes} />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Globe className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <p>{t.noProductionData}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Source Information */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="py-4">
          <div className="flex items-center gap-3">
            <Info className="w-5 h-5 text-gray-400" />
            <p className="text-sm text-gray-600">{t.source}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ProductionAgriculture;
