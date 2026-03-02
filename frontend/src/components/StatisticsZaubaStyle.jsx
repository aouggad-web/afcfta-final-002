import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API_URL = BACKEND_URL || '';

const StatisticsZaubaStyle = ({ language = 'fr' }) => {
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState(null);
  const [africaTotals, setAfricaTotals] = useState(null);
  const [selectedYear, setSelectedYear] = useState('2024');
  const [selectedFilter, setSelectedFilter] = useState('all');

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
  }, []);

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
    return <div className="text-center py-10">{t.loading}</div>;
  }

  if (!statistics) {
    return <div className="text-center py-10">{t.noData}</div>;
  }

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

  return (
    <div className="space-y-6">
      {/* Section Résumé - Style Zauba */}
      <div className="bg-white p-6 rounded-lg shadow-lg border-2 border-gray-200">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">
          📊 {t.analysisTitle}
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {/* Valeur Totale */}
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 p-4 rounded-lg border border-blue-200">
            <p className="text-xs font-semibold text-gray-600 mb-1">{t.totalTradeValue}</p>
            <p className="text-3xl font-extrabold text-blue-700">
              ${statistics.overview?.estimated_combined_gdp ? 
                (statistics.overview.estimated_combined_gdp / 1000000000).toFixed(0) : '2706'}B
            </p>
            <p className="text-xs text-gray-500 mt-1">{t.combinedGDP}</p>
          </div>

          {/* Volume Total */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg border border-green-200">
            <p className="text-xs font-semibold text-gray-600 mb-1">{t.totalExports}</p>
            <p className="text-3xl font-extrabold text-green-700">
              ${africaTotals?.exports_billions ? africaTotals.exports_billions.toFixed(0) : '720'}B
            </p>
            <p className="text-xs text-gray-500 mt-1">{t.estimated2024}</p>
          </div>

          {/* Prix Moyen */}
          <div className="bg-gradient-to-br from-orange-50 to-amber-50 p-4 rounded-lg border border-orange-200">
            <p className="text-xs font-semibold text-gray-600 mb-1">{t.totalImports}</p>
            <p className="text-3xl font-extrabold text-orange-700">
              ${africaTotals?.imports_billions ? africaTotals.imports_billions.toFixed(0) : '761'}B
            </p>
            <p className="text-xs text-gray-500 mt-1">{t.estimated2024}</p>
          </div>

          {/* Nombre de pays */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg border border-purple-200">
            <p className="text-xs font-semibold text-gray-600 mb-1">{t.memberCountries}</p>
            <p className="text-3xl font-extrabold text-purple-700">
              {statistics.overview?.african_countries_members || 54}
            </p>
            <p className="text-xs text-gray-500 mt-1">AfCFTA</p>
          </div>
        </div>

        {/* Top Exportateurs et Importateurs côte à côte */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Top Exportateurs */}
          <div>
            <h3 className="text-lg font-bold mb-3 text-green-700 flex items-center gap-2">
              <span>📤</span>
              <span>{t.top10Exporters}</span>
            </h3>
            <div className="space-y-2">
              {statistics.top_exporters_2024?.slice(0, 10).map((exporter, index) => (
                <div key={index} className="flex justify-between items-center p-2 bg-green-50 rounded hover:bg-green-100 transition-colors border-l-4 border-green-500">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-green-600 text-white text-xs">{index + 1}</Badge>
                    <span className="text-sm font-semibold text-gray-800">{translateCountry(exporter.name)}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-green-700">${(exporter.exports_2024 / 1000000000).toFixed(1)}B</p>
                    <p className="text-xs text-gray-500">{exporter.share_pct}% {t.ofTotal}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Importateurs */}
          <div>
            <h3 className="text-lg font-bold mb-3 text-blue-700 flex items-center gap-2">
              <span>📥</span>
              <span>{t.top10Importers}</span>
            </h3>
            <div className="space-y-2">
              {statistics.top_importers_2024?.slice(0, 10).map((importer, index) => (
                <div key={index} className="flex justify-between items-center p-2 bg-blue-50 rounded hover:bg-blue-100 transition-colors border-l-4 border-blue-500">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-blue-600 text-white text-xs">{index + 1}</Badge>
                    <span className="text-sm font-semibold text-gray-800">{translateCountry(importer.name)}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-blue-700">${(importer.imports_2024 / 1000000000).toFixed(1)}B</p>
                    <p className="text-xs text-gray-500">{importer.share_pct}% {t.ofTotal}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Top 10 PIB Africains 2024 avec Projections 2025 */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-amber-50 to-yellow-50">
          <CardTitle className="text-xl font-bold flex items-center gap-2">
            💰 {language === 'fr' ? 'Top 10 PIB Africains 2024' : 'Top 10 African GDP 2024'}
          </CardTitle>
          <CardDescription className="text-sm">
            {language === 'fr' ? 'Avec projections de croissance 2025 (Source: FMI, Banque Mondiale)' : 'With 2025 growth projections (Source: IMF, World Bank)'}
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-amber-200 bg-amber-50">
                  <th className="text-left py-2 px-3 font-bold text-gray-700">#</th>
                  <th className="text-left py-2 px-3 font-bold text-gray-700">{language === 'fr' ? 'Pays' : 'Country'}</th>
                  <th className="text-right py-2 px-3 font-bold text-gray-700">{language === 'fr' ? 'PIB 2024' : 'GDP 2024'}</th>
                  <th className="text-right py-2 px-3 font-bold text-gray-700">{language === 'fr' ? 'Croissance 2024' : 'Growth 2024'}</th>
                  <th className="text-right py-2 px-3 font-bold text-amber-700">{language === 'fr' ? 'Projection 2025' : 'Projection 2025'}</th>
                </tr>
              </thead>
              <tbody>
                {statistics.top_10_gdp_2024?.map((country, index) => (
                  <tr key={index} className={`border-b ${index % 2 === 0 ? 'bg-white' : 'bg-amber-50/30'} hover:bg-amber-100/50 transition-colors`}>
                    <td className="py-2 px-3">
                      <Badge className={`text-xs ${index < 3 ? 'bg-amber-500' : 'bg-gray-400'} text-white`}>
                        {country.rank}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 font-semibold text-gray-800">{translateCountry(country.country)}</td>
                    <td className="py-2 px-3 text-right font-bold text-amber-700">${country.gdp_2024_billion?.toFixed(1)}B</td>
                    <td className="py-2 px-3 text-right">
                      <span className={`font-semibold ${parseFloat(country.growth_2024) >= 5 ? 'text-green-600' : parseFloat(country.growth_2024) >= 3 ? 'text-blue-600' : 'text-orange-600'}`}>
                        {typeof country.growth_2024 === 'number' ? country.growth_2024.toFixed(1) : country.growth_2024}%
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className={`font-bold px-2 py-1 rounded ${country.growth_projection_2025 !== 'N/A' ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-500'}`}>
                        {country.growth_projection_2025 || 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-500 mt-3 italic">
            {language === 'fr' 
              ? '📊 Données officielles FMI WEO Octobre 2025, Banque Mondiale. Certaines valeurs marquées "estimée" sont des extrapolations officielles.' 
              : '📊 Official IMF WEO October 2025, World Bank data. Values marked "estimated" are official extrapolations.'}
          </p>
        </CardContent>
      </Card>

      {/* Graphique Évolution Commerce */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
          <CardTitle className="text-xl font-bold">📈 {t.intraAfricanEvolution}</CardTitle>
          <CardDescription className="text-sm">{t.trend2023_2030}</CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {statistics.trade_evolution && (
            <div style={{ minHeight: '320px' }}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={[
                  { année: '2023', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2023) },
                  { année: '2024', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2024) },
                  { année: '2025', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.12 },
                  { année: '2030', valeur: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.52 }
                ]} margin={{ left: 60, right: 20, top: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="année" tick={{ fontSize: 12, fontWeight: 'bold' }} />
                  <YAxis tick={{ fontSize: 11 }} label={{ value: t.billionUSD, angle: -90, position: 'insideLeft', offset: -10, style: { fontSize: 11 } }} />
                  <Tooltip formatter={(value) => [`$${value.toFixed(1)}B`, language === 'en' ? 'Trade' : 'Commerce']} />
                  <Legend />
                  <Line type="monotone" dataKey="valeur" stroke="#10b981" strokeWidth={3} name={t.intraAfricanTrade} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* NOUVEAU: Top 5 PIB - Commerce Monde vs Intra-Africain */}
      {statistics.top_5_gdp_trade_comparison && statistics.top_5_gdp_trade_comparison.length > 0 && (
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
            <CardTitle className="text-xl font-bold">💰 {t.top5GDP}</CardTitle>
            <CardDescription className="text-sm">{t.worldVsIntraAfrican}</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Graphique Barres Comparatif */}
              <div style={{ minHeight: '360px' }}>
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
                    margin={{ left: 10, right: 30, top: 10, bottom: 30 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      type="number" 
                      label={{ value: t.billionUSD, position: 'insideBottom', offset: -10, style: { fontSize: 11, fontWeight: 'bold' } }}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis 
                      type="category" 
                      dataKey="pays" 
                      width={110} 
                      tick={{ fontSize: 11, fontWeight: 'bold' }}
                    />
                    <Tooltip 
                      formatter={(value) => `$${value.toFixed(1)}B`}
                      contentStyle={{ 
                        backgroundColor: '#f9fafb', 
                        border: '2px solid #3b82f6',
                        borderRadius: '8px',
                        fontSize: '12px'
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', fontWeight: 'bold' }} />
                    <Bar dataKey={t.exportsWorld} fill="#10b981" radius={[0, 4, 4, 0]} />
                    <Bar dataKey={t.exportsIntraAfr} fill="#6ee7b7" radius={[0, 4, 4, 0]} />
                    <Bar dataKey={t.importsWorld} fill="#3b82f6" radius={[0, 4, 4, 0]} />
                    <Bar dataKey={t.importsIntraAfr} fill="#93c5fd" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Tableau Détaillé */}
              <div>
                <h4 className="text-sm font-bold mb-3 text-gray-700">{t.detailByCountry}</h4>
                <div className="space-y-2">
                  {statistics.top_5_gdp_trade_comparison.map((country, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded-lg border-l-4 border-blue-500">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-bold text-gray-800">{translateCountry(country.country)}</span>
                        <Badge className="bg-purple-600 text-white text-xs">{language === 'en' ? 'GDP' : 'PIB'}: ${country.gdp_2024}B</Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <p className="text-gray-500">{t.expWorld}:</p>
                          <p className="font-bold text-green-700">${country.exports_world.toFixed(1)}B</p>
                        </div>
                        <div>
                          <p className="text-gray-500">{t.expIntraAfr}:</p>
                          <p className="font-bold text-green-600">${country.exports_intra_african.toFixed(1)}B ({country.intra_african_percentage}%)</p>
                        </div>
                        <div>
                          <p className="text-gray-500">{t.impWorld}:</p>
                          <p className="font-bold text-blue-700">${country.imports_world.toFixed(1)}B</p>
                        </div>
                        <div>
                          <p className="text-gray-500">{t.impIntraAfr}:</p>
                          <p className="font-bold text-blue-600">${country.imports_intra_african.toFixed(1)}B</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Répartition par Secteur - Pie Chart */}
      {statistics.sector_performance && Object.keys(statistics.sector_performance).length > 0 && (
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-indigo-50 to-blue-50">
            <CardTitle className="text-xl font-bold">🏭 {t.sectorPerformance}</CardTitle>
            <CardDescription className="text-sm">{t.sectorDistribution}</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div style={{ minHeight: '300px' }}>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={Object.entries(statistics.sector_performance).slice(0, 8).map(([key, value]) => {
                        const shareValue = typeof value === 'object' && value.share ? value.share : 
                                          typeof value === 'object' && value.value_2024 ? value.value_2024 : 
                                          parseFloat(value) || 10;
                        return {
                          name: key.replace(/_/g, ' '),
                          value: parseFloat(shareValue)
                        };
                      })}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {Object.entries(statistics.sector_performance).slice(0, 8).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-bold mb-3 text-gray-700">{t.sectorDetails}</h4>
                {Object.entries(statistics.sector_performance).slice(0, 8).map(([key, value], index) => {
                  const shareValue = typeof value === 'object' && value.share ? value.share : 
                                    typeof value === 'object' && value.value_2024 ? value.value_2024 : 
                                    parseFloat(value) || 10;
                  const displayName = key.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                  
                  return (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded" 
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="text-xs font-semibold">{displayName}</span>
                      </div>
                      <Badge className="text-xs">{parseFloat(shareValue).toFixed(1)}%</Badge>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Source Indicator Footer */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="py-3">
          <p className="text-xs text-gray-500 text-center">
            {language === 'en' 
              ? 'Sources: IMF World Economic Outlook 2024 | World Bank WDI | UNCTAD COMTRADE | AfCFTA Secretariat | African Development Bank'
              : 'Sources: FMI World Economic Outlook 2024 | Banque Mondiale WDI | UNCTAD COMTRADE | Secrétariat ZLECAf | Banque Africaine de Développement'
            }
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default StatisticsZaubaStyle;
