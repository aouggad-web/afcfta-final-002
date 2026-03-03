import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts';
import { ArrowUpRight, ArrowDownRight, Globe2, TrendingUp, Search, RefreshCw, BarChart3, Filter } from 'lucide-react';
import { getCountryFlag, getCountryInfo } from '../../utils/countryCodes';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Palette de couleurs africaines moderne
const COLORS = ['#059669', '#0891b2', '#7c3aed', '#dc2626', '#ea580c', '#ca8a04', '#16a34a', '#2563eb', '#9333ea', '#e11d48'];

const formatValue = (value) => {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
};

const formatQuantity = (quantity) => {
  if (quantity >= 1e9) return `${(quantity / 1e9).toFixed(2)}B`;
  if (quantity >= 1e6) return `${(quantity / 1e6).toFixed(1)}M`;
  if (quantity >= 1e3) return `${(quantity / 1e3).toFixed(0)}K`;
  return quantity.toFixed(0);
};

/**
 * Extrait le vrai code HS depuis l'identifiant OEC
 * L'ID OEC a un préfixe (1-21) suivi du code HS (2, 4 ou 6 chiffres)
 * Ex: 52711 -> code HS4 = 2711 (Petroleum Gas)
 * Ex: 178704 -> code HS4 = 8704 (Vehicles)
 */
const extractHSCode = (oecId, hsLevel = 'HS4') => {
  if (!oecId) return '-';
  const idStr = String(oecId);
  const digits = hsLevel === 'HS6' ? 6 : hsLevel === 'HS2' ? 2 : 4;
  // Prendre les N derniers chiffres (2 pour HS2, 4 pour HS4, 6 pour HS6)
  return idStr.slice(-digits).padStart(digits, '0');
};

// HS classification levels
const HS_LEVELS = [
  { value: 'HS2', digits: 2 },
  { value: 'HS4', digits: 4 },
  { value: 'HS6', digits: 6 },
];

// Available HS revisions
const HS_REVISIONS = ['2022', '2017', '2012'];

// Popular HS codes by level and language
const POPULAR_HS_CODES = {
  HS2: {
    fr: [
      { code: '09', label: 'Café, thé, épices' },
      { code: '08', label: 'Fruits et noix' },
      { code: '27', label: 'Combustibles' },
      { code: '71', label: 'Métaux précieux' },
      { code: '52', label: 'Coton' },
    ],
    en: [
      { code: '09', label: 'Coffee, tea, spices' },
      { code: '08', label: 'Fruits & nuts' },
      { code: '27', label: 'Fuels' },
      { code: '71', label: 'Precious metals' },
      { code: '52', label: 'Cotton' },
    ],
  },
  HS4: {
    fr: [
      { code: '0901', label: 'Café' },
      { code: '1801', label: 'Cacao' },
      { code: '2709', label: 'Pétrole brut' },
      { code: '7108', label: 'Or' },
      { code: '5201', label: 'Coton non cardé' },
    ],
    en: [
      { code: '0901', label: 'Coffee' },
      { code: '1801', label: 'Cocoa' },
      { code: '2709', label: 'Crude oil' },
      { code: '7108', label: 'Gold' },
      { code: '5201', label: 'Uncarded cotton' },
    ],
  },
  HS6: {
    fr: [
      { code: '090111', label: 'Café non torréfié' },
      { code: '180100', label: 'Fèves de cacao' },
      { code: '270900', label: 'Pétrole brut' },
      { code: '710812', label: 'Or sous forme brute' },
      { code: '520100', label: 'Coton non cardé' },
    ],
    en: [
      { code: '090111', label: 'Unroasted coffee' },
      { code: '180100', label: 'Cocoa beans' },
      { code: '270900', label: 'Crude oil' },
      { code: '710812', label: 'Gold in raw form' },
      { code: '520100', label: 'Uncarded cotton' },
    ],
  },
};

// HS level badge colors
const HS_LEVEL_COLORS = {
  HS2: { badge: 'bg-emerald-100 text-emerald-700', btn: 'bg-emerald-600', indicator: 'text-emerald-600' },
  HS4: { badge: 'bg-blue-100 text-blue-700', btn: 'bg-blue-600', indicator: 'text-blue-600' },
  HS6: { badge: 'bg-violet-100 text-violet-700', btn: 'bg-violet-600', indicator: 'text-violet-600' },
};

export default function OECTradeStats({ language = 'fr' }) {
  const [activeView, setActiveView] = useState('country');
  const [countries, setCountries] = useState([]);
  const [years] = useState([2024, 2023, 2022, 2021, 2020, 2019, 2018]); // Années disponibles pour HS Rev. 2017 (2018-2024)
  const [countryNameToIso3, setCountryNameToIso3] = useState({}); // Mapping name_en -> ISO3
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Filtres
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedYear, setSelectedYear] = useState('2024'); // 2024 par défaut
  const [selectedFlow, setSelectedFlow] = useState('exports');
  const [hsCode, setHsCode] = useState('');
  const [hsCodeName, setHsCodeName] = useState(''); // Dénomination du code HS
  const [secondCountry, setSecondCountry] = useState('');

  // Classification HS
  const [hsLevel, setHsLevel] = useState('HS6'); // HS2 / HS4 / HS6
  const [hsRevision, setHsRevision] = useState('2022'); // 2022 / 2017 / 2012
  
  // Résultats
  const [tradeData, setTradeData] = useState(null);
  const [productData, setProductData] = useState(null);
  const [bilateralData, setBilateralData] = useState(null);

  const texts = {
    fr: {
      title: "Statistiques Commerciales OEC",
      subtitle: "Données en temps réel de l'Observatory of Economic Complexity",
      countryView: "Par Pays",
      productView: "Par Produit",
      bilateralView: "Commerce Bilatéral",
      selectCountry: "Sélectionner un pays",
      selectYear: "Année",
      tradeFlow: "Flux commercial",
      exports: "Exportations",
      imports: "Importations",
      hsCodeLabel: "Code SH6 (6 chiffres)",
      hsCodePlaceholder: "Ex: 090111 (Café non torréfié)",
      search: "Rechercher",
      loading: "Chargement...",
      noData: "Aucune donnée disponible",
      totalValue: "Valeur totale",
      totalVolume: "Volume total",
      volumeUnit: "tonnes",
      topPartners: "Principaux partenaires",
      topProducts: "Principaux produits",
      africanExporters: "Exportateurs africains",
      country: "Pays",
      value: "Valeur",
      volume: "Volume",
      share: "Part",
      sourceLabel: "Source: OEC / BACI Database",
      exporter: "Exportateur",
      importer: "Importateur",
      bilateralTitle: "Commerce bilatéral",
      product: "Produit",
      rank: "Rang",
      dataYear: "Données pour",
      refreshData: "Actualiser",
      popularProducts: "Produits populaires",
      coffee: "Café",
      cocoa: "Cacao", 
      cotton: "Coton",
      gold: "Or",
      oil: "Pétrole",
      diamonds: "Diamants",
      hsLevel: "Niveau de Classification",
      hsRevision: "Version HS",
      hsLevelDesc: "Sélectionnez le niveau de granularité souhaité",
      revisionDesc: "Version de la nomenclature douanière",
      hs2Description: "Chapitres - Vue d'ensemble par secteurs",
      hs4Description: "Positions - Groupes de produits détaillés",
      hs6Description: "Sous-positions - Produits spécifiques"
    },
    en: {
      title: "OEC Trade Statistics",
      subtitle: "Real-time data from the Observatory of Economic Complexity",
      countryView: "By Country",
      productView: "By Product",
      bilateralView: "Bilateral Trade",
      selectCountry: "Select a country",
      selectYear: "Year",
      tradeFlow: "Trade flow",
      exports: "Exports",
      imports: "Imports",
      hsCodeLabel: "HS6 Code (6 digits)",
      hsCodePlaceholder: "Ex: 090111 (Unroasted coffee)",
      search: "Search",
      loading: "Loading...",
      noData: "No data available",
      totalValue: "Total value",
      totalVolume: "Total volume",
      volumeUnit: "tonnes",
      topPartners: "Top partners",
      topProducts: "Top products",
      africanExporters: "African exporters",
      country: "Country",
      value: "Value",
      volume: "Volume",
      share: "Share",
      sourceLabel: "Source: OEC / BACI Database",
      exporter: "Exporter",
      importer: "Importer",
      bilateralTitle: "Bilateral trade",
      product: "Product",
      rank: "Rank",
      dataYear: "Data for",
      refreshData: "Refresh",
      popularProducts: "Popular products",
      coffee: "Coffee",
      cocoa: "Cocoa",
      cotton: "Cotton",
      gold: "Gold",
      oil: "Oil",
      diamonds: "Diamonds",
      hsLevel: "Classification Level",
      hsRevision: "HS Version",
      hsLevelDesc: "Select desired granularity level",
      revisionDesc: "Customs nomenclature version",
      hs2Description: "Chapters - Sector overview",
      hs4Description: "Headings - Detailed product groups",
      hs6Description: "Subheadings - Specific products"
    }
  };

  const t = texts[language];

  // Utility: get popular HS codes for current level and language
  const getPopularHSCodes = (level, lang) => {
    const langKey = lang === 'en' ? 'en' : 'fr';
    return (POPULAR_HS_CODES[level] || POPULAR_HS_CODES.HS6)[langKey] || [];
  };

  // Utility: get adaptive placeholder based on HS level
  const getPlaceholderForLevel = (level, lang) => {
    if (lang === 'en') {
      if (level === 'HS2') return 'Ex: 09 (Coffee, tea, spices)';
      if (level === 'HS4') return 'Ex: 0901 (Coffee)';
      return 'Ex: 090111 (Unroasted coffee)';
    }
    if (level === 'HS2') return 'Ex: 09 (Café, thé, épices)';
    if (level === 'HS4') return 'Ex: 0901 (Café)';
    return 'Ex: 090111 (Café non torréfié)';
  };

  // Get digits count for current HS level
  const hsLevelDigits = { HS2: 2, HS4: 4, HS6: 6 }[hsLevel] || 6;

  // HS level description text
  const hsLevelDescription = { HS2: t.hs2Description, HS4: t.hs4Description, HS6: t.hs6Description }[hsLevel];

  // Charger les pays africains et le mapping name_en -> ISO3
  useEffect(() => {
    const fetchCountriesAndMapping = async () => {
      try {
        // Charger la liste des pays
        const countriesResponse = await axios.get(`${API}/oec/countries?lang=${language}`);
        if (countriesResponse.data.success) {
          setCountries(countriesResponse.data.countries);
        }
      } catch (err) {
        console.error('Error loading countries:', err);
      }
      
      try {
        // Charger le mapping name_en -> ISO3 depuis le backend
        const mappingResponse = await axios.get(`${API}/oec/countries/name-to-iso3`);
        if (mappingResponse.data.success) {
          setCountryNameToIso3(mappingResponse.data.mapping);
        } else {
          // Fallback to empty mapping if request fails
          setCountryNameToIso3({});
        }
      } catch (err) {
        console.error('Error loading country name mapping:', err);
        // Set empty mapping as fallback - flags will show default 🌍
        setCountryNameToIso3({});
      }
    };
    fetchCountriesAndMapping();
  }, [language]);

  // Rechercher la dénomination du code HS quand le code change
  useEffect(() => {
    const fetchHSCodeName = async () => {
      if (hsCode && hsCode.length >= 4) {
        try {
          // Chercher avec l'endpoint search qui retourne la description
          const searchResponse = await axios.get(`${API}/hs6/search`, {
            params: { query: hsCode, limit: 5 }
          });
          
          if (searchResponse.data && searchResponse.data.results && searchResponse.data.results.length > 0) {
            // Chercher le code exact ou le plus proche
            const exactMatch = searchResponse.data.results.find(r => r.code === hsCode.padEnd(6, '0') || r.code.startsWith(hsCode));
            if (exactMatch) {
              setHsCodeName(exactMatch.description || '');
            } else {
              setHsCodeName(searchResponse.data.results[0].description || '');
            }
          } else {
            setHsCodeName('');
          }
        } catch (err) {
          console.error('Error fetching HS code name:', err);
          setHsCodeName('');
        }
      } else {
        setHsCodeName('');
      }
    };
    
    const debounceTimer = setTimeout(fetchHSCodeName, 300);
    return () => clearTimeout(debounceTimer);
  }, [hsCode]);

  // Recherche par pays
  const searchByCountry = useCallback(async () => {
    if (!selectedCountry) return;
    setLoading(true);
    setError(null);
    
    try {
      const endpoint = selectedFlow === 'exports' 
        ? `${API}/oec/exports/${selectedCountry}`
        : `${API}/oec/imports/${selectedCountry}`;
      
      const response = await axios.get(endpoint, {
        params: { year: selectedYear, limit: 20 }
      });
      
      setTradeData(response.data);
    } catch (err) {
      setError(err.message);
      setTradeData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedCountry, selectedYear, selectedFlow]);

  // Recherche par produit
  const searchByProduct = useCallback(async () => {
    if (!hsCode) return;
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API}/oec/product/${hsCode}`, {
        params: { year: selectedYear, trade_flow: selectedFlow, limit: 30, hs_level: hsLevel, hs_revision: hsRevision }
      });
      
      setProductData(response.data);
    } catch (err) {
      setError(err.message);
      setProductData(null);
    } finally {
      setLoading(false);
    }
  }, [hsCode, selectedYear, selectedFlow, hsLevel, hsRevision]);

  // Recherche commerce bilatéral
  const searchBilateral = useCallback(async () => {
    if (!selectedCountry || !secondCountry) return;
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(
        `${API}/oec/bilateral/${selectedCountry}/${secondCountry}`,
        { params: { year: selectedYear, limit: 20 } }
      );
      
      setBilateralData(response.data);
    } catch (err) {
      setError(err.message);
      setBilateralData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedCountry, secondCountry, selectedYear]);

  // Mapping des noms de pays OEC vers ISO3 pour les drapeaux
  // Uses the mapping dynamically loaded from the backend endpoint to avoid hardcoding country name variations in the frontend
  const getCountryFlagFromName = (countryName) => {
    if (!countryName) return '🌍';
    
    // Utiliser le mapping chargé depuis le backend
    const iso3 = countryNameToIso3[countryName];
    return iso3 ? getCountryFlag(iso3) : '🌍';
  };

  // Chart data preparation - adapté selon le contexte
  const prepareChartData = (data, type = 'country', limit = 10) => {
    if (!data || !data.data) return [];
    
    return data.data.slice(0, limit).map((item, index) => {
      let name = '';
      
      if (type === 'country') {
        // Pour la vue par pays : afficher les produits (HS6)
        name = item['HS6'] || item['HS4'] || `Produit #${index + 1}`;
      } else if (type === 'product') {
        // Pour la vue par produit : afficher les pays
        name = item['Exporter Country'] || item['Importer Country'] || `Pays #${index + 1}`;
      } else if (type === 'bilateral') {
        // Pour le commerce bilatéral : afficher les produits
        name = item['HS6'] || item['HS4'] || `Produit #${index + 1}`;
      }
      
      return {
        name: name.length > 25 ? name.substring(0, 22) + '...' : name,
        fullName: name,
        value: item['Trade Value'] || 0,
        fill: COLORS[index % COLORS.length]
      };
    });
  };

  return (
    <div className="space-y-6" data-testid="oec-trade-stats">
      {/* Header moderne et épuré */}
      <Card className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white border-none shadow-2xl overflow-hidden relative">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PHBhdGggZD0iTTM2IDM0djItSDI0di0yaDEyek0zNiAyNHYySDI0di0yaDEyeiIvPjwvZz48L2c+PC9zdmc+')] opacity-50"></div>
        <CardHeader className="relative z-10 pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-emerald-400 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg">
                <Globe2 className="w-8 h-8 text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl font-bold tracking-tight">{t.title}</CardTitle>
                <CardDescription className="text-slate-300 mt-1">{t.subtitle}</CardDescription>
              </div>
            </div>
            <Badge className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1">
              <TrendingUp className="w-3 h-3 mr-1" />
              Live Data
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Navigation par onglets - Design moderne */}
      <Tabs value={activeView} onValueChange={setActiveView} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 bg-slate-100 p-1.5 rounded-xl h-auto">
          <TabsTrigger 
            value="country" 
            className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-slate-900 rounded-lg py-3 font-medium transition-all"
            data-testid="tab-country"
          >
            <Globe2 className="w-4 h-4 mr-2" />
            {t.countryView}
          </TabsTrigger>
          <TabsTrigger 
            value="product"
            className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-slate-900 rounded-lg py-3 font-medium transition-all"
            data-testid="tab-product"
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            {t.productView}
          </TabsTrigger>
          <TabsTrigger 
            value="bilateral"
            className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-slate-900 rounded-lg py-3 font-medium transition-all"
            data-testid="tab-bilateral"
          >
            <ArrowUpRight className="w-4 h-4 mr-2" />
            {t.bilateralView}
          </TabsTrigger>
        </TabsList>

        {/* Vue par Pays */}
        <TabsContent value="country" className="space-y-6 mt-6">
          <Card className="shadow-lg border-slate-200">
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.selectCountry}</Label>
                  <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                    <SelectTrigger data-testid="country-select" className="bg-white">
                      <SelectValue placeholder={t.selectCountry} />
                    </SelectTrigger>
                    <SelectContent>
                      {countries.map((country) => (
                        <SelectItem key={country.iso3} value={country.iso3}>
                          <span className="flex items-center gap-2">
                            <span>{getCountryFlag(country.iso3)}</span>
                            <span>{country.name}</span>
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.selectYear}</Label>
                  <Select value={selectedYear} onValueChange={setSelectedYear}>
                    <SelectTrigger className="bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {years.map((year) => (
                        <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.tradeFlow}</Label>
                  <Select value={selectedFlow} onValueChange={setSelectedFlow}>
                    <SelectTrigger className="bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="exports">{t.exports}</SelectItem>
                      <SelectItem value="imports">{t.imports}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-end">
                  <Button 
                    onClick={searchByCountry}
                    disabled={!selectedCountry || loading}
                    className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium"
                    data-testid="search-country-btn"
                  >
                    {loading ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Search className="w-4 h-4 mr-2" />
                    )}
                    {loading ? t.loading : t.search}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Résultats par pays */}
          {tradeData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Carte récapitulative avec graphique des produits */}
              <Card className="shadow-lg">
                <CardHeader className="bg-gradient-to-r from-emerald-50 to-cyan-50 border-b">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold text-slate-800">
                      {selectedFlow === 'exports' ? t.exports : t.imports} - {tradeData.country?.name_fr || tradeData.country?.name_en || selectedCountry}
                    </CardTitle>
                    <Badge variant="outline" className="text-emerald-700 border-emerald-300">
                      {t.dataYear} {selectedYear}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  {/* Stats avec Valeur et Volume */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="text-center p-3 bg-emerald-50 rounded-lg">
                      <p className="text-xs text-emerald-600 mb-1">{t.totalValue}</p>
                      <p className="text-2xl font-bold text-emerald-800">{formatValue(tradeData.total_value || 0)}</p>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-600 mb-1">{t.totalVolume}</p>
                      <p className="text-2xl font-bold text-blue-800">{formatQuantity(tradeData.total_quantity || 0)} <span className="text-sm font-normal">{t.volumeUnit}</span></p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-500 text-center mb-4">{tradeData.total_products} {t.topProducts}</p>
                  
                  {/* Chart - Produits principaux */}
                  <div className="h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={prepareChartData(tradeData, 'country')} layout="vertical">
                        <XAxis type="number" tickFormatter={(v) => formatValue(v)} />
                        <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 10 }} />
                        <Tooltip 
                          formatter={(v) => formatValue(v)} 
                          labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                        />
                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                          {prepareChartData(tradeData, 'country').map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Table des produits */}
              <Card className="shadow-lg">
                <CardHeader className="border-b">
                  <CardTitle className="text-lg font-semibold">{t.topProducts}</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-96 overflow-auto">
                    <Table>
                      <TableHeader className="sticky top-0 bg-slate-50">
                        <TableRow>
                          <TableHead className="w-12">{t.rank}</TableHead>
                          <TableHead>{t.product} (Code HS)</TableHead>
                          <TableHead className="text-right">{t.value}</TableHead>
                          <TableHead className="text-right">{t.volume}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {tradeData.data?.slice(0, 15).map((item, idx) => (
                          <TableRow key={idx} className="hover:bg-slate-50">
                            <TableCell className="font-medium text-slate-500">{idx + 1}</TableCell>
                            <TableCell>
                              <div className="flex items-start gap-2">
                                <Badge variant="secondary" className="bg-emerald-100 text-emerald-700 font-mono text-xs px-1.5 py-0.5 shrink-0">
                                  {extractHSCode(item['HS6 ID'] || item['HS4 ID'], item['HS6 ID'] ? 'HS6' : 'HS4')}
                                </Badge>
                                <span className="font-medium text-sm">{item['HS6'] || item['HS4'] || '-'}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right font-semibold text-emerald-700">
                              {formatValue(item['Trade Value'] || 0)}
                            </TableCell>
                            <TableCell className="text-right text-sm text-blue-600">
                              {formatQuantity(item['Quantity'] || 0)} t
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Vue par Produit */}
        <TabsContent value="product" className="space-y-6 mt-6">
          {/* Panneau Configuration HS */}
          <Card className="shadow-lg border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold text-slate-800">{t.hsLevel}</CardTitle>
              <CardDescription>{t.hsLevelDesc}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Sélecteur de niveau HS */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.hsLevel}</Label>
                  <div className="flex gap-2">
                    {HS_LEVELS.map((level) => {
                      const colors = HS_LEVEL_COLORS[level.value];
                      const isActive = hsLevel === level.value;
                      return (
                        <button
                          key={level.value}
                          onClick={() => { setHsLevel(level.value); setHsCode(''); setHsCodeName(''); }}
                          data-testid={`hs-level-${level.value.toLowerCase()}`}
                          className={`flex-1 py-2 px-3 rounded-lg text-sm font-semibold border-2 transition-all ${
                            isActive
                              ? `${colors.badge} border-current`
                              : 'bg-slate-50 text-slate-500 border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          {level.value}
                        </button>
                      );
                    })}
                  </div>
                  <p className="text-xs text-slate-500">{hsLevelDescription}</p>
                </div>

                {/* Sélecteur de révision HS */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.hsRevision}</Label>
                  <Select value={hsRevision} onValueChange={setHsRevision}>
                    <SelectTrigger className="bg-white" data-testid="hs-revision-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {HS_REVISIONS.map((rev) => (
                        <SelectItem key={rev} value={rev}>HS {rev}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">{t.revisionDesc}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Filtres de recherche */}
          <Card className="shadow-lg border-slate-200">
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2 md:col-span-2">
                  <div className="flex items-center gap-2">
                    <Label className="text-sm font-medium text-slate-700">{t.hsCodeLabel}</Label>
                    <Badge variant="secondary" className={`${HS_LEVEL_COLORS[hsLevel].badge} font-mono text-xs px-1.5 py-0.5`}>
                      {hsLevel}
                    </Badge>
                  </div>
                  <div className="relative">
                    <Input
                      value={hsCode}
                      onChange={(e) => setHsCode(e.target.value.replace(/\D/g, '').slice(0, hsLevelDigits))}
                      placeholder={getPlaceholderForLevel(hsLevel, language)}
                      className="bg-white"
                      maxLength={hsLevelDigits}
                      data-testid="hs-code-input"
                    />
                    {/* Affichage de la dénomination du code HS */}
                    {hsCodeName && (
                      <div className="mt-1 px-2 py-1.5 bg-violet-50 border border-violet-200 rounded-md">
                        <p className="text-sm text-violet-800 font-medium truncate" title={hsCodeName}>
                          {hsCodeName}
                        </p>
                      </div>
                    )}
                  </div>
                  {/* Quick select buttons */}
                  <div className="flex flex-wrap gap-2 mt-2">
                    <span className="text-xs text-slate-500">{t.popularProducts}:</span>
                    {getPopularHSCodes(hsLevel, language).map((item) => (
                      <button
                        key={item.code}
                        onClick={() => setHsCode(item.code)}
                        className={`text-xs px-2 py-1 rounded-full transition-all ${
                          hsCode === item.code 
                            ? 'bg-slate-900 text-white' 
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.selectYear}</Label>
                  <Select value={selectedYear} onValueChange={setSelectedYear}>
                    <SelectTrigger className="bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {years.map((year) => (
                        <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-end">
                  <Button 
                    onClick={searchByProduct}
                    disabled={!hsCode || loading}
                    className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium"
                    data-testid="search-product-btn"
                  >
                    {loading ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Search className="w-4 h-4 mr-2" />
                    )}
                    {loading ? t.loading : t.search}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Résultats par produit */}
          {productData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Carte récapitulative */}
              <Card className="shadow-lg">
                <CardHeader className="bg-gradient-to-r from-violet-50 to-purple-50 border-b">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className={`${HS_LEVEL_COLORS[hsLevel].badge} font-mono text-xs px-1.5 py-0.5`}>
                        {hsLevel}
                      </Badge>
                      <CardTitle className="text-lg font-semibold text-slate-800">
                        {productData.hs_code} - {selectedFlow === 'exports' ? t.exports : t.imports}
                      </CardTitle>
                    </div>
                    <Badge variant="outline" className="text-violet-700 border-violet-300">
                      {t.dataYear} {selectedYear}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  {/* Stats avec Valeur et Volume */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="text-center p-3 bg-violet-50 rounded-lg">
                      <p className="text-xs text-violet-600 mb-1">{t.totalValue}</p>
                      <p className="text-2xl font-bold text-violet-800">{formatValue(productData.total_value || 0)}</p>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-600 mb-1">{t.totalVolume}</p>
                      <p className="text-2xl font-bold text-blue-800">{formatQuantity(productData.total_quantity || 0)} <span className="text-sm font-normal">{t.volumeUnit}</span></p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-500 text-center mb-4">{productData.total_countries} {t.country}</p>
                  
                  {/* Pie Chart - Pays exportateurs/importateurs */}
                  <div className="h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={prepareChartData(productData, 'product', 8)}
                          cx="50%"
                          cy="50%"
                          innerRadius={45}
                          outerRadius={70}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {prepareChartData(productData, 'product', 8).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(v) => formatValue(v)} />
                        <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Table des pays partenaires */}
              <Card className="shadow-lg">
                <CardHeader className="border-b">
                  <CardTitle className="text-lg font-semibold">
                    {selectedFlow === 'exports' ? t.africanExporters : t.topPartners}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-96 overflow-auto">
                    <Table>
                      <TableHeader className="sticky top-0 bg-slate-50">
                        <TableRow>
                          <TableHead className="w-12">{t.rank}</TableHead>
                          <TableHead>{t.country}</TableHead>
                          <TableHead className="text-right">{t.value}</TableHead>
                          <TableHead className="text-right">{t.volume}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {productData.data?.slice(0, 20).map((item, idx) => {
                          const countryName = item['Exporter Country'] || item['Importer Country'] || '-';
                          return (
                            <TableRow key={idx} className="hover:bg-slate-50">
                              <TableCell className="font-medium text-slate-500">{idx + 1}</TableCell>
                              <TableCell className="font-medium">
                                <span className="flex items-center gap-2">
                                  <span>{getCountryFlagFromName(countryName)}</span>
                                  <span>{countryName}</span>
                                </span>
                              </TableCell>
                              <TableCell className="text-right font-semibold text-violet-700">
                                {formatValue(item['Trade Value'] || 0)}
                              </TableCell>
                              <TableCell className="text-right text-sm text-blue-600">
                                {formatQuantity(item['Quantity'] || 0)} t
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Vue Bilatérale */}
        <TabsContent value="bilateral" className="space-y-6 mt-6">
          <Card className="shadow-lg border-slate-200">
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.exporter}</Label>
                  <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                    <SelectTrigger data-testid="exporter-select" className="bg-white">
                      <SelectValue placeholder={t.selectCountry} />
                    </SelectTrigger>
                    <SelectContent>
                      {countries.map((country) => (
                        <SelectItem key={country.iso3} value={country.iso3}>
                          <span className="flex items-center gap-2">
                            <span>{getCountryFlag(country.iso3)}</span>
                            <span>{country.name}</span>
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.importer}</Label>
                  <Select value={secondCountry} onValueChange={setSecondCountry}>
                    <SelectTrigger data-testid="importer-select" className="bg-white">
                      <SelectValue placeholder={t.selectCountry} />
                    </SelectTrigger>
                    <SelectContent>
                      {countries.filter(c => c.iso3 !== selectedCountry).map((country) => (
                        <SelectItem key={country.iso3} value={country.iso3}>
                          <span className="flex items-center gap-2">
                            <span>{getCountryFlag(country.iso3)}</span>
                            <span>{country.name}</span>
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-slate-700">{t.selectYear}</Label>
                  <Select value={selectedYear} onValueChange={setSelectedYear}>
                    <SelectTrigger className="bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {years.map((year) => (
                        <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-end">
                  <Button 
                    onClick={searchBilateral}
                    disabled={!selectedCountry || !secondCountry || loading}
                    className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium"
                    data-testid="search-bilateral-btn"
                  >
                    {loading ? (
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Search className="w-4 h-4 mr-2" />
                    )}
                    {loading ? t.loading : t.search}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Résultats bilatéraux */}
          {bilateralData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Carte récapitulative */}
              <Card className="shadow-lg">
                <CardHeader className="bg-gradient-to-r from-orange-50 to-amber-50 border-b">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg font-semibold text-slate-800">
                        {t.bilateralTitle}
                      </CardTitle>
                      <CardDescription>
                        {language === 'fr' ? bilateralData.exporter?.name_fr : bilateralData.exporter?.name_en} → {language === 'fr' ? bilateralData.importer?.name_fr : bilateralData.importer?.name_en}
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="text-orange-700 border-orange-300">
                      {t.dataYear} {selectedYear}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  {/* Stats avec Valeur et Volume */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="text-center p-3 bg-orange-50 rounded-lg">
                      <p className="text-xs text-orange-600 mb-1">{t.totalValue}</p>
                      <p className="text-2xl font-bold text-orange-800">{formatValue(bilateralData.total_value || 0)}</p>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-600 mb-1">{t.totalVolume}</p>
                      <p className="text-2xl font-bold text-blue-800">{formatQuantity(bilateralData.total_quantity || 0)} <span className="text-sm font-normal">{t.volumeUnit}</span></p>
                    </div>
                  </div>
                  <div className="flex items-center justify-center gap-2 mb-4">
                    <span className="text-sm font-medium">{language === 'fr' ? bilateralData.exporter?.name_fr : bilateralData.exporter?.name_en}</span>
                    <ArrowUpRight className="w-4 h-4 text-orange-500" />
                    <span className="text-sm font-medium">{language === 'fr' ? bilateralData.importer?.name_fr : bilateralData.importer?.name_en}</span>
                  </div>
                  
                  {/* Bar Chart - Produits échangés */}
                  <div className="h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={prepareChartData(bilateralData, 'bilateral', 8)}>
                        <XAxis dataKey="name" tick={{ fontSize: 9 }} angle={-45} textAnchor="end" height={70} />
                        <YAxis tickFormatter={(v) => formatValue(v)} />
                        <Tooltip 
                          formatter={(v) => formatValue(v)}
                          labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                        />
                        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                          {prepareChartData(bilateralData, 'bilateral', 8).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Table des produits échangés */}
              <Card className="shadow-lg">
                <CardHeader className="border-b">
                  <CardTitle className="text-lg font-semibold">{t.topProducts}</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="max-h-96 overflow-auto">
                    <Table>
                      <TableHeader className="sticky top-0 bg-slate-50">
                        <TableRow>
                          <TableHead className="w-12">{t.rank}</TableHead>
                          <TableHead>{t.product} (Code HS)</TableHead>
                          <TableHead className="text-right">{t.value}</TableHead>
                          <TableHead className="text-right">{t.volume}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {bilateralData.data?.slice(0, 15).map((item, idx) => (
                          <TableRow key={idx} className="hover:bg-slate-50">
                            <TableCell className="font-medium text-slate-500">{idx + 1}</TableCell>
                            <TableCell>
                              <div className="flex items-start gap-2">
                                <Badge variant="secondary" className="bg-orange-100 text-orange-700 font-mono text-xs px-1.5 py-0.5 shrink-0">
                                  {extractHSCode(item['HS6 ID'] || item['HS4 ID'], item['HS6 ID'] ? 'HS6' : 'HS4')}
                                </Badge>
                                <span className="font-medium text-sm">{item['HS6'] || item['HS4'] || '-'}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right font-semibold text-orange-700">
                              {formatValue(item['Trade Value'] || 0)}
                            </TableCell>
                            <TableCell className="text-right text-sm text-blue-600">
                              {formatQuantity(item['Quantity'] || 0)} t
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Message d'erreur */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-4">
            <p className="text-red-700 text-center">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Footer source */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-3">
          <p className="text-xs text-slate-500 text-center">
            {t.sourceLabel}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
