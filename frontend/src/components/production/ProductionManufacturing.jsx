import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';
import { Factory, TrendingUp, Award, Building2, Package, Loader2, AlertTriangle, Info, DollarSign, Users, Download } from 'lucide-react';
import { buildProductionPdf, productionPdfFilename } from '../../utils/productionPdf';

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
    share_mva_pct: 'Part de la MVA (estimée)',
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
    share_mva_pct: 'Share of MVA (estimated)',
  },
};

// Ordre d'affichage stable des indicateurs (IDSB puis INDSTAT).
const ISIC4_INDICATOR_ORDER = [
  'output_usd', 'imports_world_usd', 'exports_world_usd', 'apparent_consumption_usd',
  'output_usd_official', 'value_added_usd', 'establishments', 'employees',
  'female_employees', 'wages_salaries_usd', 'gross_fixed_capital_formation_usd',
  'share_mva_pct',
];

// Indicateur mis en avant sur la ligne repliée, par ordre de préférence : c'est
// le chiffre qui permet de situer la classe d'un coup d'œil. La ligne affichait
// jusqu'ici un décompte d'indicateurs, qui ne renseignait sur rien.
const HEADLINE_INDICATORS = [
  'value_added_usd', 'output_usd_official', 'output_usd', 'apparent_consumption_usd',
  'establishments', 'employees',
  // En dernier recours : la part de MVA estimée. Les classes dont la division
  // n'a pas de valeur monétaire publiée ne portent QUE cet indicateur ; sans
  // lui, la ligne affichait « — » alors qu'une valeur existe. Le mettre en fin
  // de liste garde la préférence aux grandeurs mesurées.
  'share_mva_pct',
];

const PERCENT_INDICATORS = new Set(['share_mva_pct']);

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
  // Nature de ce que sert l'API : mesuré par UNIDO, ou structure estimée à
  // partir des divisions ISIC2 pour les 34 pays absents du jeu au niveau classe.
  const [isic4Basis, setIsic4Basis] = useState(null);
  const [isic4Method, setIsic4Method] = useState(null);
  const [pdfBusy, setPdfBusy] = useState(false);
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
    setIsic4Basis(null);
    setIsic4Method(null);
    try {
      const response = await axios.get(`${API}/production/isic4/${requestedCountry}`);
      if (isic4RequestCountry.current !== requestedCountry) return; // stale, country changed since
      setIsic4Sectors(response.data.sectors || []);
      setIsic4DataQuality(response.data.data_quality || null);
      setIsic4Basis(response.data.data_basis || null);
      setIsic4Method({
        methodology: response.data.methodology || null,
        coverage: response.data.coverage || null,
        source: response.data.source || null,
      });
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
    // Les pays servis par estimation n'ont aucune série temporelle : appeler la
    // route ferait un 404 et afficherait une erreur là où il n'y a qu'une
    // absence de donnée, ce qui n'est pas la même chose.
    if (isic4Basis === 'ESTIMATED_FROM_ISIC2') return;
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

  // Export PDF : le rapport reprend les encadrés ISIC2 tels qu'affichés, et
  // porte la nature de la donnée — un tableau détaché de l'écran doit dire
  // lui-même s'il est mesuré ou estimé.
  const exportIsic4Pdf = async () => {
    setPdfBusy(true);
    try {
      // Le détail par classe n'est chargé à l'écran qu'au clic, une classe à la
      // fois. Le PDF le veut en entier : une seule requête groupée plutôt que
      // 130 appels. Un échec ici ne doit pas priver du rapport — on produit
      // alors la vue d'ensemble seule, et le document le dit.
      let timeseries = null;
      let detailUnavailable = false;
      if (isic4Basis === 'UNIDO_MEASURED') {
        try {
          const res = await axios.get(`${API}/production/isic4/${selectedCountry}/timeseries`);
          timeseries = res.data?.classes || null;
          detailUnavailable = !timeseries;
        } catch (error) {
          console.error('Détail ISIC4 indisponible pour le PDF:', error);
          // Le document le dira : un export amputé qui se tait est indiscernable
          // d'un export complet.
          detailUnavailable = true;
        }
      }
      const doc = buildProductionPdf({
        countryIso3: selectedCountry,
        // unidoData vient d'une requête distincte, sans garde contre une
        // réponse périmée : si la table ISIC4 arrive la première après un
        // changement de pays, le PDF porterait le nom du pays précédent.
        // On ne s'en sert que si la charge utile désigne bien le pays courant.
        countryName:
          (unidoData?.country_iso3 || unidoData?.country_code) === selectedCountry
            ? unidoData?.country_name || selectedCountry
            : selectedCountry,
        language,
        dataBasis: isic4Basis,
        divisions: groupIsic4ByDivision(),
        source: isic4Method?.source,
        formatIndicatorValue,
        indicatorLabels: ISIC4_INDICATOR_LABELS[language] || ISIC4_INDICATOR_LABELS.fr,
        headlineOrder: HEADLINE_INDICATORS,
        indicatorOrder: ISIC4_INDICATOR_ORDER,
        timeseries,
        detailUnavailable,
      });
      doc.save(`${productionPdfFilename(selectedCountry, isic4Basis)}.pdf`);
    } finally {
      setPdfBusy(false);
    }
  };

  const formatIndicatorValue = (field, value) => {
    if (value === null || value === undefined) return '—';
    if (PERCENT_INDICATORS.has(field)) return `${value.toLocaleString()} %`;
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
                    {/* Trois natures distinctes, jamais deux pastilles à la fois :
                        structure estimée hors couverture, estimations dérivées
                        UNIDO, ou statistiques mesurées. Afficher « Mesuré » à côté
                        de « estimations dérivées » présentait de l'estimé comme du
                        mesuré. */}
                    {isic4Basis === 'ESTIMATED_FROM_ISIC2' ? (
                      <Badge className="text-xs bg-amber-500 hover:bg-amber-500 text-white">
                        {language === 'fr' ? 'Structure estimée' : 'Estimated structure'}
                      </Badge>
                    ) : isic4DataQuality?.is_fully_estimated ? (
                      <Badge className="text-xs bg-sky-600 hover:bg-sky-600 text-white">
                        {language === 'fr' ? 'Estimations dérivées UNIDO' : 'UNIDO derived estimates'}
                      </Badge>
                    ) : (
                      <Badge className="text-xs bg-emerald-600 hover:bg-emerald-600 text-white">
                        {language === 'fr' ? 'Mesuré (UNIDO)' : 'Measured (UNIDO)'}
                      </Badge>
                    )}
                    <button
                      type="button"
                      onClick={exportIsic4Pdf}
                      disabled={pdfBusy}
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md border border-blue-300 text-blue-700 hover:bg-blue-100 transition disabled:opacity-60 disabled:cursor-wait"
                    >
                      {pdfBusy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                      {pdfBusy
                        ? (language === 'fr' ? 'Génération...' : 'Generating...')
                        : (language === 'fr' ? 'Exporter en PDF' : 'Export to PDF')}
                    </button>
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
              {isic4Status === 'ready' && isic4Basis === 'ESTIMATED_FROM_ISIC2' && (
                <div className="mb-5 rounded-lg border-l-4 border-amber-500 bg-amber-50 px-4 py-3">
                  <p className="text-sm font-semibold text-amber-900 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    {language === 'fr'
                      ? 'Ces chiffres sont des estimations de structure, pas des mesures.'
                      : 'These figures are structural estimates, not measurements.'}
                  </p>
                  <ul className="text-xs text-amber-900/90 mt-2 space-y-1 list-disc list-inside">
                    <li>
                      {language === 'fr'
                        ? "UNIDO ne publie pas de statistiques au niveau de la classe ISIC 4 chiffres pour ce pays. La part de valeur ajoutée manufacturière de chaque division ISIC 2 chiffres — celle-là réelle — est répartie à parts égales entre les classes de la division."
                        : 'UNIDO publishes no ISIC 4-digit class statistics for this country. Each ISIC 2-digit division\u2019s manufacturing value-added share \u2014 that figure being real \u2014 is split equally across the classes of the division.'}
                    </li>
                    <li>
                      {language === 'fr'
                        ? "Toutes les classes d'une même division portent donc la même valeur : ces chiffres situent un secteur, ils ne permettent pas de comparer deux classes entre elles."
                        : 'Every class within a division therefore carries the same value: these figures place a sector, they cannot rank two classes against each other.'}
                    </li>
                    <li>
                      {language === 'fr'
                        ? "Seuls les secteurs principaux du pays sont couverts, pas les 24 divisions manufacturières 10-33. Une division absente n'est pas nulle : elle n'est pas renseignée."
                        : 'Only the country\u2019s main sectors are covered, not all 24 manufacturing divisions 10-33. A missing division is not zero: it is not documented.'}
                    </li>
                    <li>
                      {language === 'fr'
                        ? "Aucune série temporelle n'existe à ce niveau pour ce pays."
                        : 'No time series exists at this level for this country.'}
                    </li>
                  </ul>
                  {isic4Method?.source && (
                    <p className="text-[11px] text-amber-800/80 mt-2">
                      {language === 'fr' ? 'Source : ' : 'Source: '}{isic4Method.source}
                    </p>
                  )}
                </div>
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
                        <table className="w-full text-sm border-collapse">
                          <thead>
                            <tr className="border-b-2 border-gray-300 text-left text-gray-600">
                              <th className="py-2.5 pl-4 pr-3 font-semibold w-20">ISIC 4</th>
                              <th className="py-2.5 pr-3 font-semibold">{language === 'fr' ? 'Libellé' : 'Label'}</th>
                              <th className="py-2.5 pr-3 font-semibold text-right whitespace-nowrap">
                                {language === 'fr' ? 'Indicateur principal' : 'Headline indicator'}
                              </th>
                              <th className="py-2.5 pr-3 font-semibold text-center w-24">{language === 'fr' ? 'Nature' : 'Nature'}</th>
                              <th className="py-2.5 pr-4 font-semibold text-right w-28">{language === 'fr' ? 'Détail' : 'Detail'}</th>
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
                                dataBasis={isic4Basis}
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

function IsicRow({ sector, isExpanded, onToggle, timeseries, onRetry, language, formatIndicatorValue, dataBasis }) {
  const indicators = sector.indicators || {};
  const indicatorFields = Object.keys(indicators);
  const isEstimatedCountry = dataBasis === 'ESTIMATED_FROM_ISIC2';

  // Chiffre mis en avant : le premier disponible dans l'ordre de préférence.
  // Une ligne qui affiche « 3 off. · 4 est. » ne dit rien du secteur.
  const headlineField = HEADLINE_INDICATORS.find((f) => indicators[f]?.value !== undefined && indicators[f]?.value !== null);
  const headline = headlineField ? indicators[headlineField] : null;
  const labels = ISIC4_INDICATOR_LABELS[language] || ISIC4_INDICATOR_LABELS.fr;

  // La pastille qualifie le chiffre AFFICHÉ à côté d'elle, pas la classe.
  // La calculer sur « un indicateur officiel existe quelque part » étiquetait
  // « officiel » une valeur dérivée choisie comme indicateur principal.
  const headlineOfficial = headline?.data_nature === 'OFFICIAL_STATISTICS';
  const natureLabel = isEstimatedCountry
    ? (language === 'fr' ? 'estimé' : 'estimated')
    : !headline
      ? '—'
      : headlineOfficial
        ? (language === 'fr' ? 'officiel' : 'official')
        : (language === 'fr' ? 'dérivé' : 'derived');
  const natureClass = isEstimatedCountry
    ? 'bg-amber-100 text-amber-800'
    : !headline
      ? 'bg-gray-100 text-gray-500'
      : headlineOfficial
        ? 'bg-emerald-100 text-emerald-800'
        : 'bg-sky-100 text-sky-800';

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
        className={`border-b border-gray-100 cursor-pointer transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${isExpanded ? 'bg-blue-50' : 'hover:bg-blue-50/60'}`}
        onClick={onToggle}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle();
          }
        }}
      >
        <td className="py-2.5 pl-4 pr-3 font-mono font-semibold text-blue-700 whitespace-nowrap align-top">{sector.isic4}</td>
        <td className="py-2.5 pr-3 text-gray-800 leading-snug">
          {sector.isic_description || sector.description || (
            <span className="text-gray-400 italic">
              {language === 'fr' ? 'libellé non publié' : 'label not published'}
            </span>
          )}
          {sector.division_name && (
            <span className="block text-xs text-gray-500 mt-0.5">{sector.division_name}</span>
          )}
        </td>
        <td className="py-2.5 pr-3 text-right align-top whitespace-nowrap tabular-nums">
          {headline ? (
            <>
              <span className="font-semibold text-gray-900">
                {formatIndicatorValue(headlineField, headline.value)}
              </span>
              <span className="block text-xs text-gray-500">
                {labels[headlineField] || headlineField}
                {headline.year ? ` · ${headline.year}` : ''}
              </span>
            </>
          ) : (
            <span className="text-gray-400">—</span>
          )}
        </td>
        <td className="py-2.5 pr-3 text-center align-top">
          <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${natureClass}`}>
            {natureLabel}
          </span>
        </td>
        <td className="py-2.5 pr-4 text-right align-top text-blue-600 font-medium whitespace-nowrap">
          {isExpanded
            ? (language === 'fr' ? 'Masquer' : 'Hide')
            : isEstimatedCountry
              ? (language === 'fr' ? 'Voir' : 'View')
              : (language === 'fr' ? 'Historique' : 'History')}
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={5} className="p-0">
            <div className="bg-slate-50 px-4 py-4 border-b-2 border-blue-200" onClick={(e) => e.stopPropagation()}>
              {isEstimatedCountry ? (
                <EstimatedDetail
                  indicators={indicators}
                  labels={labels}
                  language={language}
                  formatIndicatorValue={formatIndicatorValue}
                />
              ) : (
                <>
                  {status === 'loading' && (
                    <p className="text-sm text-gray-500 py-3">
                      <Loader2 className="w-4 h-4 inline animate-spin mr-2" />
                      {language === 'fr' ? 'Chargement...' : 'Loading...'}
                    </p>
                  )}
                  {status === 'error' && (
                    <div className="text-sm text-red-600 flex items-center justify-between gap-2 py-2">
                      <span>{language === 'fr' ? "Erreur lors du chargement de l'historique." : 'Failed to load history.'}</span>
                      <button type="button" className="underline hover:no-underline" onClick={onRetry}>
                        {language === 'fr' ? 'Réessayer' : 'Retry'}
                      </button>
                    </div>
                  )}
                  {status === 'ready' && presentFields.length === 0 && (
                    <p className="text-sm text-gray-500 py-2">
                      {language === 'fr' ? 'Aucune série temporelle disponible.' : 'No time series available.'}
                    </p>
                  )}
                  {status === 'ready' && presentFields.length > 0 && (
                    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
                      <table className="text-sm border-collapse w-full">
                        <thead>
                          <tr className="bg-gray-100 text-gray-700">
                            <th className="py-2 px-3 font-semibold text-left sticky left-0 bg-gray-100 z-10 min-w-[200px]">
                              {language === 'fr' ? 'Indicateur' : 'Indicator'}
                            </th>
                            {allYears.map((year) => (
                              <th key={year} className="py-2 px-3 font-semibold text-right whitespace-nowrap">{year}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {presentFields.map((field, i) => {
                            const byYear = Object.fromEntries(series[field].map((p) => [p.year, p]));
                            const nature = series[field][0]?.data_nature;
                            const official = nature === 'OFFICIAL_STATISTICS';
                            return (
                              <tr key={field} className={i % 2 ? 'bg-slate-50/60' : 'bg-white'}>
                                <td className={`py-2 px-3 text-gray-800 whitespace-nowrap sticky left-0 z-10 border-r border-gray-200 ${i % 2 ? 'bg-slate-50/60' : 'bg-white'}`}>
                                  {labels[field] || field}
                                  {nature && (
                                    <span
                                      className={`ml-2 rounded px-1.5 py-0.5 text-[10px] font-medium ${official ? 'bg-emerald-100 text-emerald-800' : 'bg-sky-100 text-sky-800'}`}
                                    >
                                      {official
                                        ? (language === 'fr' ? 'officiel' : 'official')
                                        : (language === 'fr' ? 'dérivé' : 'derived')}
                                    </span>
                                  )}
                                </td>
                                {allYears.map((year) => (
                                  <td key={year} className="py-2 px-3 text-right text-gray-900 whitespace-nowrap tabular-nums">
                                    {byYear[year] ? formatIndicatorValue(field, byYear[year].value) : <span className="text-gray-300">—</span>}
                                  </td>
                                ))}
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                  <p className="text-xs text-gray-500 italic pt-3">
                    {language === 'fr'
                      ? 'UNIDO IDSB (imports, exports, consommation apparente, production — estimations dérivées) et INDSTAT (production, valeur ajoutée, emplois — statistiques officielles), 2018-2024.'
                      : 'UNIDO IDSB (imports, exports, apparent consumption, output — derived estimates) and INDSTAT (output, value added, employment — official statistics), 2018-2024.'}
                  </p>
                </>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// Détail d'une classe pour un pays servi par estimation : pas de série
// temporelle, seulement les valeurs dérivées de la division, et le rappel
// explicite de ce qu'elles valent.
function EstimatedDetail({ indicators, labels, language, formatIndicatorValue }) {
  const fields = ISIC4_INDICATOR_ORDER.filter((f) => indicators[f]?.value !== undefined && indicators[f]?.value !== null);
  if (fields.length === 0) {
    return (
      <p className="text-sm text-gray-500 py-2">
        {language === 'fr'
          ? "Aucune valeur estimée pour cette classe : la division dont elle relève n'a pas de valeur monétaire publiée."
          : 'No estimated value for this class: its division has no published monetary value.'}
      </p>
    );
  }
  return (
    <>
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="text-sm border-collapse w-full">
          <thead>
            <tr className="bg-gray-100 text-gray-700">
              <th className="py-2 px-3 font-semibold text-left">{language === 'fr' ? 'Indicateur' : 'Indicator'}</th>
              <th className="py-2 px-3 font-semibold text-right">{language === 'fr' ? 'Valeur estimée' : 'Estimated value'}</th>
              <th className="py-2 px-3 font-semibold text-left">{language === 'fr' ? 'Nature' : 'Nature'}</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((field, i) => (
              <tr key={field} className={i % 2 ? 'bg-slate-50/60' : 'bg-white'}>
                <td className="py-2 px-3 text-gray-800">{labels[field] || field}</td>
                <td className="py-2 px-3 text-right text-gray-900 font-semibold tabular-nums whitespace-nowrap">
                  {formatIndicatorValue(field, indicators[field].value)}
                </td>
                <td className="py-2 px-3">
                  <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                    {language === 'fr' ? 'estimation de structure' : 'structural estimate'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-amber-800 italic pt-3">
        {language === 'fr'
          ? "Valeur obtenue en divisant la part de MVA réelle de la division ISIC 2 chiffres par son nombre de classes. Toutes les classes de cette division portent donc le même chiffre : il situe le secteur, il ne le mesure pas."
          : 'Value obtained by dividing the real ISIC 2-digit division MVA share by its number of classes. Every class of this division therefore carries the same figure: it places the sector, it does not measure it.'}
      </p>
    </>
  );
}


export default ProductionManufacturing;
