/**
 * Trade Substitution Analysis Component
 * Analyzes intra-African trade substitution opportunities
 * 
 * Features:
 * - Import substitution analysis (what can be sourced from Africa)
 * - Export opportunities (what can be exported to other African countries)
 * - Product-level analysis
 * - Trade flow visualization
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Sankey, PieChart, Pie, Cell, Legend
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Globe, Package, Factory, Ship,
  ArrowRight, ArrowLeftRight, Loader2, AlertCircle, Search,
  DollarSign, Target, MapPin, ChevronRight, Sparkles
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#059669', '#0891b2', '#7c3aed', '#dc2626', '#ea580c', '#ca8a04', '#16a34a', '#2563eb'];

// Format currency values
const formatValue = (value) => {
  if (!value || isNaN(value)) return '$0';
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
};

// Stat Card Component
const StatCard = ({ title, value, icon: Icon, trend, color = "emerald", subtitle }) => {
  const colorClasses = {
    emerald: "bg-emerald-100 text-emerald-600",
    blue: "bg-blue-100 text-blue-600",
    purple: "bg-purple-100 text-purple-600",
    orange: "bg-orange-100 text-orange-600",
    red: "bg-red-100 text-red-600"
  };

  return (
    <Card className="bg-white border-slate-200 shadow-lg hover:shadow-xl transition-shadow">
      <CardContent className="p-5">
        <div className="flex items-center gap-4">
          <div className={`flex-shrink-0 h-12 w-12 flex items-center justify-center rounded-full ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-500 truncate">{title}</p>
            <p className="text-2xl font-bold text-slate-900">{value}</p>
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Opportunity Card Component
const OpportunityCard = ({ opportunity, type, language }) => {
  const isImport = type === 'import';
  const product = isImport ? opportunity.imported_product : opportunity.exportable_product;
  const targets = isImport ? opportunity.african_suppliers : opportunity.target_markets;
  
  const difficultyColors = {
    easy: "bg-emerald-100 text-emerald-700",
    moderate: "bg-amber-100 text-amber-700",
    difficult: "bg-red-100 text-red-700"
  };
  
  const competitivenessColors = {
    highly_competitive: "bg-emerald-100 text-emerald-700",
    competitive: "bg-blue-100 text-blue-700",
    developing: "bg-amber-100 text-amber-700"
  };

  return (
    <Card className="bg-white border-slate-200 shadow hover:shadow-lg transition-all">
      <CardContent className="p-5">
        {/* Product Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <Badge variant="outline" className="mb-2 font-mono text-xs">
              HS {product.hs_code}
            </Badge>
            <h3 className="font-bold text-slate-900 text-lg leading-tight">
              {product.name}
            </h3>
          </div>
          {isImport ? (
            <Badge className={difficultyColors[opportunity.difficulty] || difficultyColors.moderate}>
              {opportunity.difficulty === 'easy' ? 'Facile' : 
               opportunity.difficulty === 'moderate' ? 'Modéré' : 'Difficile'}
            </Badge>
          ) : (
            <Badge className={competitivenessColors[opportunity.competitiveness] || competitivenessColors.competitive}>
              {opportunity.competitiveness === 'highly_competitive' ? 'Très compétitif' :
               opportunity.competitiveness === 'competitive' ? 'Compétitif' : 'En développement'}
            </Badge>
          )}
        </div>

        {/* Value Info */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-slate-50 rounded-lg p-3">
            <p className="text-xs text-slate-500 mb-1">
              {isImport ? "Import actuel" : "Capacité"}
            </p>
            <p className="font-bold text-lg text-slate-900">
              {formatValue(isImport ? product.import_value : product.production_capacity)}
            </p>
          </div>
          <div className="bg-emerald-50 rounded-lg p-3">
            <p className="text-xs text-emerald-600 mb-1">
              {isImport ? "Potentiel substitution" : "Capture estimée"}
            </p>
            <p className="font-bold text-lg text-emerald-700">
              {formatValue(isImport ? opportunity.substitution_potential : opportunity.estimated_capture)}
            </p>
          </div>
        </div>

        {/* Current Source (for imports) */}
        {isImport && product.current_source && (
          <div className="mb-4 flex items-center gap-2 text-sm text-slate-500">
            <Globe className="h-4 w-4" />
            <span>Source actuelle: <strong className="text-slate-700">{product.current_source}</strong></span>
          </div>
        )}

        {/* Suppliers/Markets */}
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
            {isImport ? "Fournisseurs africains potentiels" : "Marchés cibles"}
          </p>
          <div className="space-y-2">
            {targets?.slice(0, 3).map((target, idx) => (
              <div key={idx} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm text-slate-700">
                    {target.country_name}
                  </span>
                  {target.quality && (
                    <Badge variant="outline" className="text-[10px]">
                      {target.quality}
                    </Badge>
                  )}
                </div>
                <span className="text-sm font-semibold text-emerald-600">
                  {formatValue(isImport ? target.production_capacity : target.capture_potential)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Main Component
export default function SubstitutionAnalysis({ language = 'fr' }) {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || language;
  
  const [activeTab, setActiveTab] = useState('import');
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [importData, setImportData] = useState(null);
  const [exportData, setExportData] = useState(null);

  const texts = {
    fr: {
      title: "Analyse de Substitution Commerciale",
      subtitle: "Identifiez les opportunités de commerce intra-africain sous la ZLECAf",
      importTab: "Substitution d'Imports",
      exportTab: "Opportunités d'Export",
      selectCountry: "Sélectionnez un pays",
      analyze: "Analyser",
      totalOpportunities: "Opportunités identifiées",
      substitutableValue: "Valeur substituable",
      potentialSavings: "Économies potentielles",
      topSectors: "Secteurs prioritaires",
      noData: "Sélectionnez un pays pour lancer l'analyse",
      loading: "Analyse en cours...",
      importSubtitle: "Produits actuellement importés hors Afrique pouvant être sourcés localement",
      exportSubtitle: "Produits que ce pays peut exporter vers d'autres pays ZLECAf",
      source: "Sources: UN Comtrade, OEC, UNCTAD, Offices nationaux de statistiques"
    },
    en: {
      title: "Trade Substitution Analysis",
      subtitle: "Identify intra-African trade opportunities under AfCFTA",
      importTab: "Import Substitution",
      exportTab: "Export Opportunities",
      selectCountry: "Select a country",
      analyze: "Analyze",
      totalOpportunities: "Opportunities identified",
      substitutableValue: "Substitutable value",
      potentialSavings: "Potential savings",
      topSectors: "Priority sectors",
      noData: "Select a country to start analysis",
      loading: "Analysis in progress...",
      importSubtitle: "Products currently imported from outside Africa that can be sourced locally",
      exportSubtitle: "Products this country can export to other AfCFTA countries",
      source: "Sources: UN Comtrade, OEC, UNCTAD, National statistics offices"
    }
  };

  const txt = texts[currentLang] || texts.fr;

  // Fetch available countries
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const response = await axios.get(`${API}/substitution/countries?lang=${currentLang}`);
        setCountries(response.data.countries || []);
      } catch (err) {
        console.error('Error fetching countries:', err);
      }
    };
    fetchCountries();
  }, [currentLang]);

  // Analyze function
  const analyzeCountry = useCallback(async () => {
    if (!selectedCountry) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const [importRes, exportRes] = await Promise.all([
        axios.get(`${API}/substitution/opportunities/import/${selectedCountry}?lang=${currentLang}`),
        axios.get(`${API}/substitution/opportunities/export/${selectedCountry}?lang=${currentLang}`)
      ]);
      
      setImportData(importRes.data);
      setExportData(exportRes.data);
    } catch (err) {
      console.error('Error analyzing country:', err);
      setError('Erreur lors de l\'analyse. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  }, [selectedCountry, currentLang]);

  // Auto-analyze when country changes
  useEffect(() => {
    if (selectedCountry) {
      analyzeCountry();
    }
  }, [selectedCountry, analyzeCountry]);

  const currentData = activeTab === 'import' ? importData : exportData;
  const opportunities = currentData?.opportunities || [];

  return (
    <div className="space-y-6" data-testid="substitution-analysis">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <ArrowLeftRight className="h-8 w-8 text-emerald-600" />
          <h2 className="text-3xl font-black text-slate-900 uppercase tracking-tight">
            {txt.title}
          </h2>
        </div>
        <p className="text-slate-500">{txt.subtitle}</p>
      </div>

      {/* Country Selection */}
      <Card className="shadow-lg">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">{txt.selectCountry}</label>
              <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger className="w-full" data-testid="country-select-substitution">
                  <SelectValue placeholder={txt.selectCountry} />
                </SelectTrigger>
                <SelectContent>
                  {countries.map((country) => (
                    <SelectItem key={country.iso3} value={country.iso3}>
                      <span className="flex items-center gap-2">
                        {country.name}
                        {country.has_trade_data && (
                          <Sparkles className="h-3 w-3 text-amber-500" />
                        )}
                        {!country.has_trade_data && (
                          <span className="text-xs text-slate-400">(pas de données)</span>
                        )}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button 
              onClick={analyzeCountry}
              disabled={!selectedCountry || loading}
              className="bg-emerald-600 hover:bg-emerald-700"
              data-testid="analyze-btn"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Search className="h-4 w-4 mr-2" />
              )}
              {txt.analyze}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
          <span className="ml-3 text-slate-600">{txt.loading}</span>
        </div>
      )}

      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {!loading && !error && currentData && (
        <>
          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 max-w-md mx-auto">
              <TabsTrigger value="import" className="flex items-center gap-2" data-testid="import-tab">
                <TrendingDown className="h-4 w-4" />
                {txt.importTab}
              </TabsTrigger>
              <TabsTrigger value="export" className="flex items-center gap-2" data-testid="export-tab">
                <TrendingUp className="h-4 w-4" />
                {txt.exportTab}
              </TabsTrigger>
            </TabsList>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title={txt.totalOpportunities}
                value={currentData.summary?.total_opportunities || 0}
                icon={Target}
                color="emerald"
              />
              <StatCard
                title={txt.substitutableValue}
                value={formatValue(
                  activeTab === 'import' 
                    ? currentData.summary?.total_substitutable_value 
                    : currentData.summary?.total_market_potential
                )}
                icon={DollarSign}
                color="blue"
              />
              <StatCard
                title={activeTab === 'import' ? txt.potentialSavings : "Marchés cibles"}
                value={activeTab === 'import' 
                  ? `${currentData.summary?.potential_savings_percent?.toFixed(1) || 0}%`
                  : currentData.summary?.top_markets?.length || 0
                }
                icon={activeTab === 'import' ? Sparkles : MapPin}
                color="purple"
              />
              <StatCard
                title={txt.topSectors}
                value={activeTab === 'import'
                  ? currentData.summary?.top_sectors?.length || 0
                  : currentData.summary?.top_products?.length || 0
                }
                icon={Package}
                color="orange"
              />
            </div>

            {/* Description */}
            <Card className="bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200">
              <CardContent className="py-4 px-6">
                <p className="text-sm text-emerald-800">
                  {activeTab === 'import' ? txt.importSubtitle : txt.exportSubtitle}
                </p>
              </CardContent>
            </Card>

            {/* Opportunities Grid */}
            <TabsContent value="import" className="mt-0">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {importData?.opportunities?.slice(0, 6).map((opp, idx) => (
                  <OpportunityCard 
                    key={idx} 
                    opportunity={opp} 
                    type="import"
                    language={currentLang}
                  />
                ))}
              </div>
            </TabsContent>

            <TabsContent value="export" className="mt-0">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {exportData?.opportunities?.slice(0, 6).map((opp, idx) => (
                  <OpportunityCard 
                    key={idx} 
                    opportunity={opp} 
                    type="export"
                    language={currentLang}
                  />
                ))}
              </div>
            </TabsContent>
          </Tabs>

          {/* Top Sectors Chart */}
          {activeTab === 'import' && currentData?.summary?.top_sectors?.length > 0 && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg font-bold">{txt.topSectors}</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart 
                    data={currentData.summary.top_sectors}
                    layout="vertical"
                    margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" tickFormatter={(v) => formatValue(v)} />
                    <YAxis dataKey="name" type="category" width={90} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(v) => formatValue(v)} />
                    <Bar dataKey="value" fill="#10b981" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && !error && !currentData && (
        <Card className="bg-slate-50 border-slate-200">
          <CardContent className="py-16 text-center">
            <Globe className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">{txt.noData}</p>
          </CardContent>
        </Card>
      )}

      {/* Source Footer */}
      <div className="text-center">
        <p className="text-xs text-slate-400 italic">{txt.source}</p>
      </div>
    </div>
  );
}
