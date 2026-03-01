import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';
import { Factory, TrendingUp, Award, Building2, Package, Loader2, AlertTriangle, Info, DollarSign, Users } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CHART_COLORS = ['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#1e3a8a', '#60a5fa', '#93c5fd', '#bfdbfe'];

function ProductionManufacturing({ language = 'fr' }) {
  const [selectedCountry, setSelectedCountry] = useState('MAR');
  const [unidoData, setUnidoData] = useState(null);
  const [unidoStats, setUnidoStats] = useState(null);
  const [mvaRanking, setMvaRanking] = useState([]);
  const [loading, setLoading] = useState(false);

  // Translations
  const texts = {
    fr: {
      title: "Production Industrielle UNIDO",
      subtitle: "Données UNIDO INDSTAT4 - Valeur Ajoutée Manufacturière (2023)",
      totalMva: "MVA Total",
      countries: "pays",
      loading: "Chargement des données UNIDO...",
      noData: "Données non disponibles",
      noDataDesc: "Aucune donnée UNIDO disponible pour ce pays.",
      mvaLabel: "Valeur Ajoutée Manuf.",
      inAfrica: "en Afrique",
      mvaGdp: "MVA / PIB",
      industrialShare: "Part industrielle du PIB",
      mvaPerCapita: "MVA par habitant",
      industrialization: "Industrialisation per capita",
      growth2023: "Croissance 2023",
      annualGrowth: "Taux de croissance annuel",
      data: "Données",
      industrialZones: "zones industrielles",
      industrialJobs: "Emplois industriels",
      manufExports: "Export. manufacturées",
      keySectors: "Secteurs clés",
      specialZones: "Zones éco. spéciales",
      sectorDistribution: "Répartition Sectorielle (% MVA)",
      sectorValue: "Valeur par Secteur (Millions USD)",
      mainIndustrialSectors: "Principaux Secteurs Industriels",
      keyProducts: "Produits Manufacturés Clés",
      top10Africa: "Top 10 Africain - Valeur Ajoutée Manufacturière",
      otherCountries: "Autres pays",
      selectedCountry: "Pays sélectionné",
      source: "Source:",
      sourceNote: "Les données proviennent de la base UNIDO INDSTAT4 (Organisation des Nations Unies pour le Développement Industriel). La classification sectorielle suit la nomenclature ISIC Rev.4.",
      value: "Valeur"
    },
    en: {
      title: "UNIDO Industrial Production",
      subtitle: "UNIDO INDSTAT4 Data - Manufacturing Value Added (2023)",
      totalMva: "Total MVA",
      countries: "countries",
      loading: "Loading UNIDO data...",
      noData: "Data not available",
      noDataDesc: "No UNIDO data available for this country.",
      mvaLabel: "Manufacturing Value Added",
      inAfrica: "in Africa",
      mvaGdp: "MVA / GDP",
      industrialShare: "Industrial share of GDP",
      mvaPerCapita: "MVA per capita",
      industrialization: "Per capita industrialization",
      growth2023: "2023 Growth",
      annualGrowth: "Annual growth rate",
      data: "Data",
      industrialZones: "industrial zones",
      industrialJobs: "Industrial jobs",
      manufExports: "Manuf. exports",
      keySectors: "Key sectors",
      specialZones: "Special eco. zones",
      sectorDistribution: "Sectoral Distribution (% MVA)",
      sectorValue: "Value by Sector (Millions USD)",
      mainIndustrialSectors: "Main Industrial Sectors",
      keyProducts: "Key Manufactured Products",
      top10Africa: "African Top 10 - Manufacturing Value Added",
      otherCountries: "Other countries",
      selectedCountry: "Selected country",
      source: "Source:",
      sourceNote: "Data comes from the UNIDO INDSTAT4 database (United Nations Industrial Development Organization). Sectoral classification follows the ISIC Rev.4 nomenclature.",
      value: "Value"
    }
  };
  const t = texts[language] || texts.fr;

  useEffect(() => {
    fetchUnidoStats();
    fetchMvaRanking();
  }, []);

  useEffect(() => {
    if (selectedCountry) {
      fetchUnidoData(selectedCountry);
    }
  }, [selectedCountry]);

  const fetchUnidoStats = async () => {
    try {
      const response = await axios.get(`${API}/production/unido/statistics`);
      setUnidoStats(response.data);
    } catch (error) {
      console.error('Error fetching UNIDO statistics:', error);
    }
  };

  const fetchMvaRanking = async () => {
    try {
      const response = await axios.get(`${API}/production/unido/ranking`);
      setMvaRanking(response.data.ranking || []);
    } catch (error) {
      console.error('Error fetching MVA ranking:', error);
    }
  };

  const fetchUnidoData = async (countryIso3) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/production/unido/${countryIso3}`);
      setUnidoData(response.data);
    } catch (error) {
      console.error('Error fetching UNIDO data:', error);
      setUnidoData(null);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num?.toLocaleString() || '0';
  };

  const prepareSectorPieData = () => {
    if (!unidoData?.top_sectors) return [];
    
    return unidoData.top_sectors.map((sector, index) => ({
      name: sector.name,
      value: sector.share_mva,
      fill: CHART_COLORS[index % CHART_COLORS.length]
    }));
  };

  const prepareSectorBarData = () => {
    if (!unidoData?.top_sectors) return [];
    
    return unidoData.top_sectors.map((sector) => ({
      name: sector.name.length > 20 ? sector.name.substring(0, 20) + '...' : sector.name,
      fullName: sector.name,
      value: sector.value_mln_usd || 0,
      share: sector.share_mva
    }));
  };

  const prepareRankingBarData = () => {
    return mvaRanking.slice(0, 10).map((country) => ({
      name: country.country_name.length > 15 ? country.country_name.substring(0, 15) + '...' : country.country_name,
      fullName: country.country_name,
      mva: country.mva_2023_mln_usd,
      isSelected: country.country_iso3 === selectedCountry
    }));
  };

  const getCountryRank = () => {
    const index = mvaRanking.findIndex(c => c.country_iso3 === selectedCountry);
    return index >= 0 ? index + 1 : null;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 text-white shadow-xl overflow-hidden">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-3xl font-bold flex items-center gap-3">
                <Factory className="w-8 h-8" />
                {t.title}
              </CardTitle>
              <CardDescription className="text-blue-100 text-lg mt-2">
                {t.subtitle}
              </CardDescription>
            </div>
            {unidoStats && (
              <div className="text-right">
                <Badge className="bg-white/20 text-white hover:bg-white/30">
                  ${unidoStats.total_mva_bln_usd}B {t.totalMva}
                </Badge>
                <p className="text-xs text-blue-200 mt-1">{unidoStats.total_countries} {t.countries}</p>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Enhanced Country Selector */}
      <div style={{ position: 'relative', zIndex: 100 }}>
        <Card className="border-2 border-blue-200 shadow-lg" style={{ overflow: 'visible' }}>
          <CardContent className="pt-6" style={{ overflow: 'visible' }}>
            <EnhancedCountrySelector
              value={selectedCountry}
              onChange={setSelectedCountry}
              label={language === 'en' ? "Select an African country" : "Sélectionner un pays africain"}
              variant="prominent"
              language={language}
            />
          </CardContent>
        </Card>
      </div>

      {/* Loading State */}
      {loading && (
        <Card className="animate-pulse">
          <CardContent className="flex items-center justify-center h-48">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto" />
              <p className="mt-4 text-gray-600">{t.loading}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Data State */}
      {!loading && (!unidoData || unidoData.message) && (
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="flex items-center gap-4 py-8">
            <AlertTriangle className="w-12 h-12 text-amber-500" />
            <div>
              <h3 className="font-bold text-lg text-gray-800">{t.noData}</h3>
              <p className="text-gray-600">{t.noDataDesc}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      {!loading && unidoData && !unidoData.message && (
        <>
          {/* Key Metrics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm">{t.mvaLabel}</p>
                    <p className="text-3xl font-bold">${formatNumber(unidoData.mva_2023_mln_usd * 1000000)}</p>
                  </div>
                  <DollarSign className="w-10 h-10 text-blue-200" />
                </div>
                {getCountryRank() && (
                  <Badge className="mt-3 bg-white/20 text-white">
                    #{getCountryRank()} {t.inAfrica}
                  </Badge>
                )}
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-emerald-100 text-sm">{t.mvaGdp}</p>
                    <p className="text-3xl font-bold">{unidoData.mva_gdp_percent}%</p>
                  </div>
                  <TrendingUp className="w-10 h-10 text-emerald-200" />
                </div>
                <p className="text-sm text-emerald-100 mt-2">{t.industrialShare}</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-purple-500 to-violet-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-100 text-sm">{t.mvaPerCapita}</p>
                    <p className="text-3xl font-bold">${unidoData.mva_per_capita_usd}</p>
                  </div>
                  <Users className="w-10 h-10 text-purple-200" />
                </div>
                <p className="text-sm text-purple-100 mt-2">{t.industrialization}</p>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-amber-500 to-orange-600 text-white">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-amber-100 text-sm">{t.growth2023}</p>
                    <p className="text-3xl font-bold">
                      {unidoData.growth_rate_2023 > 0 ? '+' : ''}{unidoData.growth_rate_2023}%
                    </p>
                  </div>
                  <TrendingUp className="w-10 h-10 text-amber-200" />
                </div>
                <p className="text-sm text-amber-100 mt-2">{t.annualGrowth}</p>
              </CardContent>
            </Card>
          </div>

          {/* Country Overview */}
          <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-2xl text-blue-800 flex items-center gap-3">
                <Building2 className="w-7 h-7" />
                {unidoData.country_name}
              </CardTitle>
              <CardDescription className="text-blue-700 flex items-center gap-2 flex-wrap">
                <Badge variant="outline" className="border-blue-500 text-blue-700">{unidoData.region}</Badge>
                <Badge variant="outline" className="border-blue-500 text-blue-700">{t.data} {unidoData.data_year}</Badge>
                {unidoData.industrial_zones && (
                  <Badge variant="outline" className="border-blue-500 text-blue-700">
                    <Building2 className="w-3 h-3 mr-1" /> {unidoData.industrial_zones} {t.industrialZones}
                  </Badge>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Additional Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                {unidoData.industry_employment && (
                  <div className="bg-white p-4 rounded-xl shadow-sm border border-blue-100">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">{t.industrialJobs}</p>
                    <p className="text-2xl font-bold text-blue-700">{formatNumber(unidoData.industry_employment)}</p>
                  </div>
                )}
                {unidoData.exports_manuf_mln_usd && (
                  <div className="bg-white p-4 rounded-xl shadow-sm border border-blue-100">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">{t.manufExports}</p>
                    <p className="text-2xl font-bold text-green-700">${formatNumber(unidoData.exports_manuf_mln_usd * 1000000)}</p>
                  </div>
                )}
                {unidoData.top_sectors && (
                  <div className="bg-white p-4 rounded-xl shadow-sm border border-blue-100">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">{t.keySectors}</p>
                    <p className="text-2xl font-bold text-blue-700">{unidoData.top_sectors.length}</p>
                  </div>
                )}
                {unidoData.special_economic_zones && (
                  <div className="bg-white p-4 rounded-xl shadow-sm border border-blue-100">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">{t.specialZones}</p>
                    <p className="text-2xl font-bold text-purple-700">{unidoData.special_economic_zones}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Sector Analysis Charts */}
          {unidoData.top_sectors && unidoData.top_sectors.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pie Chart */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg text-gray-700 flex items-center gap-2">
                    <Package className="w-5 h-5" /> {t.sectorDistribution}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={prepareSectorPieData()}
                        cx="50%"
                        cy="50%"
                        outerRadius={90}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {prepareSectorPieData().map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => value + '% ' + (language === 'en' ? 'of MVA' : 'de la MVA')} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Bar Chart */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg text-gray-700 flex items-center gap-2">
                    <Factory className="w-5 h-5" /> {t.sectorValue}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={prepareSectorBarData()} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" tickFormatter={(v) => `$${formatNumber(v * 1000000)}`} />
                      <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                      <Tooltip 
                        formatter={(value) => [`$${formatNumber(value * 1000000)}`, t.value]}
                        labelFormatter={(label) => prepareSectorBarData().find(d => d.name === label)?.fullName || label}
                      />
                      <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Top Sectors Detail */}
          {unidoData.top_sectors && (
            <Card className="shadow-lg">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
                <CardTitle className="text-xl text-blue-700 flex items-center gap-2">
                  <Award className="w-5 h-5" /> {t.mainIndustrialSectors}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {unidoData.top_sectors.map((sector, index) => (
                    <div 
                      key={sector.isic} 
                      className="bg-gradient-to-br from-white to-blue-50 p-4 rounded-xl border border-blue-100 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <Badge 
                          className="text-xs"
                          style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length], color: 'white' }}
                        >
                          ISIC {sector.isic}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {sector.share_mva}% MVA
                        </Badge>
                      </div>
                      <h4 className="font-bold text-gray-800 mb-2">{sector.name}</h4>
                      {sector.value_mln_usd && (
                        <p className="text-2xl font-bold text-blue-600">
                          ${formatNumber(sector.value_mln_usd * 1000000)}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Key Products */}
          {unidoData.key_products && unidoData.key_products.length > 0 && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-xl text-gray-700 flex items-center gap-2">
                  <Package className="w-5 h-5" /> {t.keyProducts}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-3">
                  {unidoData.key_products.map((product, index) => (
                    <Badge 
                      key={index} 
                      className="text-sm py-2 px-4"
                      style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length], color: 'white' }}
                    >
                      {product}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* African MVA Ranking */}
          {mvaRanking.length > 0 && (
            <Card className="shadow-lg">
              <CardHeader className="bg-gradient-to-r from-amber-50 to-orange-50">
                <CardTitle className="text-xl text-amber-700 flex items-center gap-2">
                  <Award className="w-5 h-5" /> {t.top10Africa}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={prepareRankingBarData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                    <YAxis tickFormatter={(v) => `$${formatNumber(v * 1000000)}`} />
                    <Tooltip 
                      formatter={(value) => [`$${formatNumber(value * 1000000)}`, 'MVA 2023']}
                      labelFormatter={(label) => prepareRankingBarData().find(d => d.name === label)?.fullName || label}
                    />
                    <Bar 
                      dataKey="mva" 
                      radius={[4, 4, 0, 0]}
                    >
                      {prepareRankingBarData().map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.isSelected ? '#f59e0b' : '#3b82f6'} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-4 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-blue-500" />
                    <span className="text-sm text-gray-600">{t.otherCountries}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-amber-500" />
                    <span className="text-sm text-gray-600">{t.selectedCountry}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Source Information */}
          <Card className="bg-gray-50 border-gray-200">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-gray-400 mt-0.5" />
                <div className="text-sm text-gray-600">
                  <p><strong>{t.source}</strong> {unidoData.source}</p>
                  <p className="mt-1">
                    {t.sourceNote}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

export default ProductionManufacturing;
