import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';
import ISIC4DetailTable from './ISIC4DetailTable';
import { Factory, TrendingUp, Award, Building2, Package, Loader2, AlertTriangle, Info, DollarSign, Users } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const CHART_COLORS = ['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#1e3a8a', '#60a5fa', '#93c5fd', '#bfdbfe'];

// Libellés officiels ISIC Rev.4, divisions manufacturières (Section C, 10-33).
const ISIC_DIVISION_LABELS = {
  fr: {
    '10': 'Produits alimentaires', '11': 'Boissons', '12': 'Produits du tabac',
    '13': 'Textiles', '14': "Articles d'habillement", '15': 'Cuir et articles de cuir',
    '16': 'Bois et articles en bois', '17': 'Papier et articles en papier',
    '18': 'Imprimerie et reproduction', '19': 'Cokéfaction et raffinage',
    '20': 'Produits chimiques', '21': 'Produits pharmaceutiques',
    '22': 'Caoutchouc et plastiques', '23': 'Minéraux non métalliques',
    '24': 'Métallurgie de base', '25': 'Ouvrages en métaux',
    '26': 'Produits informatiques et électroniques', '27': 'Équipements électriques',
    '28': 'Machines et équipements', '29': 'Véhicules automobiles',
    '30': 'Autres matériels de transport', '31': 'Meubles',
    '32': 'Autres industries manufacturières', '33': 'Réparation et installation',
  },
  en: {
    '10': 'Food products', '11': 'Beverages', '12': 'Tobacco products',
    '13': 'Textiles', '14': 'Wearing apparel', '15': 'Leather and related products',
    '16': 'Wood and products of wood', '17': 'Paper and paper products',
    '18': 'Printing and reproduction', '19': 'Coke and refined petroleum',
    '20': 'Chemicals', '21': 'Pharmaceuticals',
    '22': 'Rubber and plastics', '23': 'Non-metallic mineral products',
    '24': 'Basic metals', '25': 'Fabricated metal products',
    '26': 'Computer, electronic and optical products', '27': 'Electrical equipment',
    '28': 'Machinery and equipment', '29': 'Motor vehicles',
    '30': 'Other transport equipment', '31': 'Furniture',
    '32': 'Other manufacturing', '33': 'Repair and installation of machinery',
  },
};

// Libellés des indicateurs UNIDO IDSB (estimations dérivées) + INDSTAT (statistiques officielles).
const ISIC4_INDICATOR_LABELS = {
  fr: {
    output_usd: 'Production (IDSB)',
    imports_world_usd: 'Importations mondiales',
    exports_world_usd: 'Exportations mondiales',
    apparent_consumption_usd: 'Consommation apparente',
    establishments: 'Établissements',
    employees: 'Emplois',
    female_employees: 'Emplois (femmes)',
    wages_salaries_usd: 'Salaires et traitements',
    output_usd_official: 'Production (INDSTAT, officiel)',
    value_added_usd: 'Valeur ajoutée',
    gross_fixed_capital_formation_usd: 'FBCF',
  },
  en: {
    output_usd: 'Output (IDSB)',
    imports_world_usd: 'Imports World',
    exports_world_usd: 'Exports World',
    apparent_consumption_usd: 'Apparent Consumption',
    establishments: 'Establishments',
    employees: 'Employees',
    female_employees: 'Female employees',
    wages_salaries_usd: 'Wages and salaries',
    output_usd_official: 'Output (INDSTAT, official)',
    value_added_usd: 'Value added',
    gross_fixed_capital_formation_usd: 'Gross fixed capital formation',
  },
};

// Ordre d'affichage stable des indicateurs (IDSB puis INDSTAT).
const ISIC4_INDICATOR_ORDER = [
  'output_usd', 'imports_world_usd', 'exports_world_usd', 'apparent_consumption_usd',
  'output_usd_official', 'value_added_usd', 'establishments', 'employees',
  'female_employees', 'wages_salaries_usd', 'gross_fixed_capital_formation_usd',
];

const USD_INDICATORS = new Set([
  'output_usd', 'imports_world_usd', 'exports_world_usd', 'apparent_consumption_usd',
  'output_usd_official', 'value_added_usd', 'wages_salaries_usd', 'gross_fixed_capital_formation_usd',
]);

function ProductionManufacturing({ language = 'fr' }) {
  const [selectedCountry, setSelectedCountry] = useState('MAR');
  const [unidoData, setUnidoData] = useState(null);
  const [unidoStats, setUnidoStats] = useState(null);
  const [mvaRanking, setMvaRanking] = useState([]);
  const [loading, setLoading] = useState(false);
  // Table ISIC4 complète (tous les secteurs manufacturiers du pays, pas seulement les principaux)
  const [isic4Sectors, setIsic4Sectors] = useState([]);
  const [isic4DataQuality, setIsic4DataQuality] = useState(null);
  const [isic4Status, setIsic4Status] = useState('idle'); // idle | loading | error | no_data | ready
  const isic4RequestCountry = useRef(null);

  // Historique détaillé (2018-2024, tous indicateurs) par code ISIC4, affiché au clic sur une ligne
  const [expandedIsic4, setExpandedIsic4] = useState(null);
  const [isic4Timeseries, setIsic4Timeseries] = useState({}); // { [isic4code]: { status, series, isic_description } }

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
      detailedIsicTitle: "Détail complet par secteur ISIC 4 chiffres",
      detailedIsicSubtitle: "Données réelles UNIDO (IDSB/INDSTAT), toutes années et tous indicateurs, avec badges réel/estimé",
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
      detailedIsicTitle: "Full breakdown by ISIC 4-digit sector",
      detailedIsicSubtitle: "Real UNIDO data (IDSB/INDSTAT), all years and indicators, with real/estimated badges",
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
    setExpandedIsic4(null);
    setIsic4Timeseries({});
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

  // Table ISIC4 complète (tous les secteurs manufacturiers réels du pays,
  // via UNIDO IDSB/INDSTAT — /api/production/isic4/{country}), pas juste
  // les "top_sectors" agrégés qu'utilise l'aperçu ci-dessus.
  const fetchIsic4Sectors = async (countryIso3) => {
    const requestedCountry = countryIso3;
    isic4RequestCountry.current = requestedCountry;
    setIsic4Status('loading');
    setIsic4Sectors([]);
    setIsic4DataQuality(null);
    try {
      const response = await axios.get(`${API}/production/isic4/${requestedCountry}`);
      if (isic4RequestCountry.current !== requestedCountry) return; // stale, country changed since
      setIsic4Sectors(response.data.sectors || []);
      setIsic4DataQuality(response.data.data_quality || null);
      setIsic4Status('ready');
    } catch (error) {
      if (isic4RequestCountry.current !== requestedCountry) return;
      if (error?.response?.status === 404) {
        setIsic4Status('no_data');
        return;
      }
      console.error('Error fetching ISIC4 sectors:', error);
      setIsic4Status('error');
    }
  };

  useEffect(() => {
    if (selectedCountry) {
      fetchIsic4Sectors(selectedCountry);
    }
  }, [selectedCountry]);

  // Historique complet (2018-2024, tous indicateurs IDSB+INDSTAT) pour une
  // classe ISIC4 donnée, chargé et mis en cache au premier clic sur la ligne.
  const fetchIsic4Timeseries = async (isic4Code) => {
    const requestedCountry = selectedCountry;
    setIsic4Timeseries((prev) => ({
      ...prev,
      [isic4Code]: { ...(prev[isic4Code] || {}), status: 'loading' },
    }));
    try {
      const response = await axios.get(`${API}/production/isic4/${requestedCountry}/${isic4Code}`);
      if (requestedCountry !== selectedCountry) return; // country changed while loading
      setIsic4Timeseries((prev) => ({
        ...prev,
        [isic4Code]: {
          status: 'ready',
          series: response.data.series || {},
          isicDescription: response.data.isic_description,
        },
      }));
    } catch (error) {
      if (requestedCountry !== selectedCountry) return;
      console.error('Error fetching ISIC4 timeseries:', error);
      setIsic4Timeseries((prev) => ({
        ...prev,
        [isic4Code]: { ...(prev[isic4Code] || {}), status: 'error' },
      }));
    }
  };

  const toggleIsic4Row = (isic4Code) => {
    if (expandedIsic4 === isic4Code) {
      setExpandedIsic4(null);
      return;
    }
    setExpandedIsic4(isic4Code);
    const existing = isic4Timeseries[isic4Code];
    if (existing && (existing.status === 'ready' || existing.status === 'loading')) return;
    fetchIsic4Timeseries(isic4Code);
  };

  // Regroupe les secteurs ISIC4 par division 2 chiffres (ex. "10", "21", ...)
  // pour reconstituer les "encadrés ISIC2" — chacun affichant TOUTES ses
  // lignes ISIC4, pas seulement un sous-ensemble.
  const groupIsic4ByDivision = () => {
    const groups = {};
    for (const sector of isic4Sectors) {
      const division = sector.isic4?.slice(0, 2);
      if (!division) continue;
      if (!groups[division]) groups[division] = [];
      groups[division].push(sector);
    }
    return Object.keys(groups)
      .sort()
      .map((division) => ({
        division,
        label: ISIC_DIVISION_LABELS[language]?.[division] || ISIC_DIVISION_LABELS.fr[division] || division,
        sectors: groups[division].sort((a, b) => a.isic4.localeCompare(b.isic4)),
      }));
  };

  const formatNumber = (num) => {
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num?.toLocaleString() || '0';
  };

  const formatIndicatorValue = (field, value) => {
    if (value === null || value === undefined) return '—';
    return USD_INDICATORS.has(field) ? `$${formatNumber(value)}` : value.toLocaleString();
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

          {/* ISIC4 Detail Table — vraies données UNIDO IDSB/INDSTAT, toutes les
              classes ISIC4 groupées par division ISIC2, historique complet au clic */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <CardTitle className="text-xl text-blue-700 flex items-center gap-2">
                  <Award className="w-5 h-5" /> {t.mainIndustrialSectors}
                </CardTitle>
                {isic4Status === 'ready' && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="text-xs">
                      {isic4Sectors.length} {language === 'fr' ? 'classes ISIC 4 chiffres' : 'ISIC 4-digit classes'}
                    </Badge>
                    {isic4DataQuality?.is_fully_estimated && (
                      <Badge variant="outline" className="text-xs border-amber-500 text-amber-700">
                        {language === 'fr' ? 'Entièrement estimé (UNIDO)' : 'Fully estimated (UNIDO)'}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
              <CardDescription className="text-blue-700 text-xs mt-1">
                {language === 'fr'
                  ? 'Source : UNIDO Statistics Data Portal — IDSB (imports/exports/conso. apparente/production, estimations dérivées) + INDSTAT (production/valeur ajoutée/emplois, statistiques officielles), 2018-2024.'
                  : 'Source: UNIDO Statistics Data Portal — IDSB (imports/exports/apparent consumption/output, derived estimates) + INDSTAT (output/value added/employment, official statistics), 2018-2024.'}
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {isic4Status === 'loading' && (
                <p className="text-sm text-gray-500 py-6 text-center">
                  <Loader2 className="w-4 h-4 inline animate-spin mr-2" />
                  {language === 'fr' ? 'Chargement...' : 'Loading...'}
                </p>
              )}
              {isic4Status === 'error' && (
                <div className="text-sm text-red-600 flex items-center justify-between gap-2 py-4">
                  <span>{language === 'fr' ? 'Erreur lors du chargement des données ISIC4.' : 'Failed to load ISIC4 data.'}</span>
                  <button type="button" className="underline hover:no-underline" onClick={() => fetchIsic4Sectors(selectedCountry)}>
                    {language === 'fr' ? 'Réessayer' : 'Retry'}
                  </button>
                </div>
              )}
              {isic4Status === 'no_data' && (
                <p className="text-sm text-gray-500 py-4 flex items-center gap-2">
                  <Info className="w-4 h-4 shrink-0" />
                  {language === 'fr'
                    ? 'Aucune donnée ISIC4 UNIDO IDSB/INDSTAT disponible pour ce pays.'
                    : 'No UNIDO IDSB/INDSTAT ISIC4 data available for this country.'}
                </p>
              )}
              {isic4Status === 'ready' && isic4Sectors.length === 0 && (
                <p className="text-sm text-gray-500 py-4">
                  {language === 'fr' ? 'Aucun secteur ISIC4 pour ce pays.' : 'No ISIC4 sector for this country.'}
                </p>
              )}
              {isic4Status === 'ready' && isic4Sectors.length > 0 && (
                <div className="space-y-5">
                  {groupIsic4ByDivision().map(({ division, label, sectors }) => (
                    <div key={division} className="border border-blue-100 rounded-xl overflow-hidden">
                      <div className="bg-blue-50/70 px-4 py-2 flex items-center justify-between flex-wrap gap-2">
                        <h4 className="font-bold text-gray-800">
                          <span className="font-mono text-blue-700">ISIC {division}</span>
                          <span className="text-gray-400 mx-2">·</span>
                          {label}
                        </h4>
                        <Badge variant="outline" className="text-xs">
                          {sectors.length} {language === 'fr' ? 'lignes ISIC4' : 'ISIC4 rows'}
                        </Badge>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-gray-200 text-left text-gray-500">
                              <th className="py-2 pl-4 pr-3 font-medium">ISIC 4</th>
                              <th className="py-2 pr-3 font-medium">{language === 'fr' ? 'Libellé' : 'Label'}</th>
                              <th className="py-2 pr-3 font-medium text-right">{language === 'fr' ? 'Indicateurs' : 'Indicators'}</th>
                              <th className="py-2 pr-4 font-medium text-right">{language === 'fr' ? 'Détail' : 'Detail'}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sectors.map((sector) => (
                              <IsicRow
                                key={sector.isic4}
                                sector={sector}
                                isExpanded={expandedIsic4 === sector.isic4}
                                onToggle={() => toggleIsic4Row(sector.isic4)}
                                timeseries={isic4Timeseries[sector.isic4]}
                                onRetry={() => fetchIsic4Timeseries(sector.isic4)}
                                language={language}
                                formatIndicatorValue={formatIndicatorValue}
                              />
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

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

          {/* Détail complet ISIC4 réel — UNIDO IDSB/INDSTAT, réel/estimé par indicateur/année */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-slate-50 to-blue-50">
              <CardTitle className="text-xl text-slate-700 flex items-center gap-2">
                <Building2 className="w-5 h-5" /> {t.detailedIsicTitle}
              </CardTitle>
              <CardDescription>{t.detailedIsicSubtitle}</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <ISIC4DetailTable countryISO3={selectedCountry} />
            </CardContent>
          </Card>

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

function IsicRow({ sector, isExpanded, onToggle, timeseries, onRetry, language, formatIndicatorValue }) {
  const indicators = sector.indicators || {};
  const indicatorFields = Object.keys(indicators);
  const officialCount = indicatorFields.filter((f) => indicators[f].data_nature === 'OFFICIAL_STATISTICS').length;
  const estimatedCount = indicatorFields.filter((f) => indicators[f].data_nature === 'UNIDO_DERIVED_ESTIMATE').length;

  const status = timeseries?.status;
  const series = timeseries?.series || {};
  const presentFields = ISIC4_INDICATOR_ORDER.filter((f) => series[f]?.length);
  const allYears = Array.from(
    new Set(presentFields.flatMap((f) => series[f].map((p) => p.year)))
  ).sort((a, b) => a - b);

  return (
    <>
      <tr
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        className="border-b border-gray-100 hover:bg-blue-50/50 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
        onClick={onToggle}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle();
          }
        }}
      >
        <td className="py-1.5 pl-4 pr-3 font-mono text-blue-700 whitespace-nowrap">{sector.isic4}</td>
        <td className="py-1.5 pr-3 text-gray-700">{sector.isic_description}</td>
        <td className="py-1.5 pr-3 text-right text-gray-500 whitespace-nowrap">
          {officialCount > 0 && (
            <span className="text-emerald-600">{officialCount} {language === 'fr' ? 'off.' : 'off.'}</span>
          )}
          {officialCount > 0 && estimatedCount > 0 && ' · '}
          {estimatedCount > 0 && (
            <span className="text-amber-600">{estimatedCount} {language === 'fr' ? 'est.' : 'est.'}</span>
          )}
          {indicatorFields.length === 0 && '—'}
        </td>
        <td className="py-1.5 pr-4 text-right text-blue-500 underline whitespace-nowrap">
          {isExpanded ? (language === 'fr' ? 'Masquer' : 'Hide') : (language === 'fr' ? 'Historique' : 'History')}
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={4} className="p-0">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200" onClick={(e) => e.stopPropagation()}>
              {status === 'loading' && (
                <p className="text-xs text-gray-500 py-3">
                  <Loader2 className="w-3.5 h-3.5 inline animate-spin mr-2" />
                  {language === 'fr' ? 'Chargement...' : 'Loading...'}
                </p>
              )}
              {status === 'error' && (
                <div className="text-xs text-red-600 flex items-center justify-between gap-2 py-2">
                  <span>{language === 'fr' ? 'Erreur lors du chargement de l\'historique.' : 'Failed to load history.'}</span>
                  <button type="button" className="underline hover:no-underline" onClick={onRetry}>
                    {language === 'fr' ? 'Réessayer' : 'Retry'}
                  </button>
                </div>
              )}
              {status === 'ready' && presentFields.length === 0 && (
                <p className="text-xs text-gray-500 py-2">
                  {language === 'fr' ? "Aucune série temporelle disponible." : 'No time series available.'}
                </p>
              )}
              {status === 'ready' && presentFields.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="text-[11px] border-collapse">
                    <thead>
                      <tr className="text-left text-gray-500">
                        <th className="py-1 pr-4 font-medium sticky left-0 bg-gray-50">
                          {language === 'fr' ? 'Indicateur' : 'Indicator'}
                        </th>
                        {allYears.map((year) => (
                          <th key={year} className="py-1 px-3 font-medium text-right">{year}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {presentFields.map((field) => {
                        const byYear = Object.fromEntries(series[field].map((p) => [p.year, p]));
                        const nature = series[field][0]?.data_nature;
                        return (
                          <tr key={field} className="border-t border-gray-200">
                            <td className="py-1 pr-4 text-gray-700 whitespace-nowrap sticky left-0 bg-gray-50">
                              {(ISIC4_INDICATOR_LABELS[language] || ISIC4_INDICATOR_LABELS.fr)[field] || field}
                              {nature && (
                                <span
                                  className={`ml-1.5 text-[9px] uppercase ${nature === 'OFFICIAL_STATISTICS' ? 'text-emerald-600' : 'text-amber-600'}`}
                                >
                                  {nature === 'OFFICIAL_STATISTICS'
                                    ? (language === 'fr' ? 'officiel' : 'official')
                                    : (language === 'fr' ? 'estimé' : 'estimate')}
                                </span>
                              )}
                            </td>
                            {allYears.map((year) => (
                              <td key={year} className="py-1 px-3 text-right text-gray-600 whitespace-nowrap">
                                {byYear[year] ? formatIndicatorValue(field, byYear[year].value) : '—'}
                              </td>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              <p className="text-[10px] text-gray-400 italic pt-2">
                {language === 'fr'
                  ? 'Données réelles UNIDO IDSB (imports/exports/conso. apparente/production — estimations dérivées) et INDSTAT (production/valeur ajoutée/emplois — statistiques officielles), 2018-2024.'
                  : 'Real UNIDO IDSB (imports/exports/apparent consumption/output — derived estimates) and INDSTAT (output/value added/employment — official statistics) data, 2018-2024.'}
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default ProductionManufacturing;
