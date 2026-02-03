/**
 * AI Trade Analysis Component
 * Uses Gemini AI for intelligent trade opportunity analysis
 * Includes Sankey diagram visualization
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
  CartesianGrid, Tooltip, Legend
} from 'recharts';
import { 
  Sparkles, Globe, TrendingUp, TrendingDown, Factory,
  Package, Loader2, AlertCircle, Search, Target,
  DollarSign, ArrowRight, ChevronDown, ChevronUp,
  Info, CheckCircle, AlertTriangle, Zap
} from 'lucide-react';

import TradeSankeyDiagram from './TradeSankeyDiagram';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Format currency
const formatValue = (value) => {
  if (!value || isNaN(value)) return '$0';
  if (value >= 1000) return `$${(value / 1000).toFixed(2)}B`;
  if (value >= 1) return `$${value.toFixed(0)}M`;
  return `$${(value * 1000).toFixed(0)}K`;
};

// AI Opportunity Card
const AIOpportunityCard = ({ opportunity, mode, language, index }) => {
  const [expanded, setExpanded] = useState(false);
  
  const isExport = mode === 'export';
  const isIndustrial = mode === 'industrial';
  
  // Handle different response formats - API returns nested product object
  const product = opportunity.product || {};
  
  const productName = isIndustrial 
    ? (product.name || opportunity.output_product || opportunity.product_name)
    : (product.name || opportunity.product_name);
  
  const hsCode = isIndustrial 
    ? (product.hs_code || opportunity.output_hs_code || opportunity.hs_code)
    : (product.hs_code || opportunity.hs_code);
  
  const partner = isExport 
    ? (opportunity.potential_partner || opportunity.target_markets?.[0])
    : (opportunity.potential_supplier || opportunity.target_markets?.[0]);
  
  // Value calculation - handle all possible field names
  let value = 0;
  if (mode === 'export') {
    value = opportunity.potential_value_musd || opportunity.current_value_musd || 0;
  } else if (mode === 'import') {
    value = opportunity.substitution_potential_musd || opportunity.import_value_musd || 0;
  } else if (mode === 'industrial') {
    value = opportunity.potential_value_musd || 0;
  }
  
  const isEstimation = opportunity.is_estimation;
  
  // Industrial mode specific fields
  const industrialInput = opportunity.industrial_input || {};
  const inputProduct = industrialInput.name || opportunity.input_product || '';
  const inputHsCode = industrialInput.hs_code || opportunity.input_hs_code || '';
  const inputVolume = industrialInput.import_volume || opportunity.input_import_volume || '';
  const transformationLogic = opportunity.transformation_logic || opportunity.rationale || '';
  const targetMarkets = opportunity.target_markets || [];

  return (
    <Card className={`bg-white border-slate-200 shadow hover:shadow-lg transition-all ${
      isEstimation ? 'border-l-4 border-l-amber-400' : ''
    }`}>
      <CardContent className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-mono text-xs">
              HS {hsCode || '----'}
            </Badge>
            {isEstimation && (
              <Badge className="bg-amber-100 text-amber-700 text-[10px]">
                <AlertTriangle className="h-3 w-3 mr-1" />
                ESTIMATION
              </Badge>
            )}
          </div>
          <span className="text-xs font-bold text-slate-400">#{index + 1}</span>
        </div>

        {/* Product name */}
        <h3 className="font-bold text-slate-900 text-lg leading-tight mb-2">
          {productName || 'Produit'}
        </h3>

        {/* Partner/Supplier */}
        <div className="flex items-center gap-2 text-sm text-slate-600 mb-4">
          <Globe className="h-4 w-4 text-emerald-500" />
          <span>
            {isExport ? 'Vers' : isIndustrial ? 'Marchés cibles' : 'De'}: 
            <strong className="text-slate-800 ml-1">
              {isIndustrial && targetMarkets.length > 0 
                ? targetMarkets.slice(0, 3).join(', ')
                : partner || 'Non spécifié'}
            </strong>
          </span>
        </div>

        {/* Value */}
        <div className="bg-emerald-50 rounded-lg p-3 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-emerald-600 font-medium">
              {isExport ? 'Potentiel' : isIndustrial ? 'Valeur potentielle' : 'Valeur substituable'}
            </span>
            <span className="text-xl font-black text-emerald-700">
              {formatValue(value)}
            </span>
          </div>
          {(opportunity.tariff_reduction || opportunity.tariff_advantage) && (
            <div className="mt-2 pt-2 border-t border-emerald-200 flex items-center justify-between">
              <span className="text-xs text-emerald-600">Avantage tarifaire ZLECAf</span>
              <Badge className="bg-emerald-600 text-white">
                -{opportunity.tariff_reduction || opportunity.tariff_advantage}%
              </Badge>
            </div>
          )}
        </div>

        {/* Industrial mode extras */}
        {isIndustrial && inputProduct && (
          <div className="bg-blue-50 rounded-lg p-3 mb-4">
            <p className="text-xs font-bold text-blue-600 uppercase mb-2">
              Chaîne de valeur
            </p>
            <div className="flex items-center gap-2 text-sm">
              <div className="flex flex-col">
                <span className="text-slate-600">{inputProduct}</span>
                {inputHsCode && (
                  <span className="text-[10px] text-slate-400">HS {inputHsCode}</span>
                )}
              </div>
              <ArrowRight className="h-4 w-4 text-blue-400 flex-shrink-0" />
              <div className="flex flex-col">
                <span className="font-bold text-slate-800">{productName}</span>
                {hsCode && (
                  <span className="text-[10px] text-slate-400">HS {hsCode}</span>
                )}
              </div>
            </div>
            {inputVolume && (
              <p className="text-xs text-slate-500 mt-2">
                Volume importé: {inputVolume}
              </p>
            )}
          </div>
        )}

        {/* Rationale (expandable) */}
        {(opportunity.rationale || transformationLogic) && (
          <>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="w-full justify-between text-slate-500 hover:text-slate-700"
            >
              <span className="text-xs font-bold uppercase">
                {isIndustrial ? 'Logique de transformation' : 'Justification'}
              </span>
              {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            {expanded && (
              <div className="mt-2 p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-700 leading-relaxed">
                  {isIndustrial ? transformationLogic : opportunity.rationale}
                </p>
                {(opportunity.data_year || opportunity.year) && (
                  <p className="text-xs text-slate-400 mt-2 italic">
                    Données: {opportunity.data_year || opportunity.year}
                  </p>
                )}
                {opportunity.data_source && (
                  <p className="text-xs text-slate-400 italic">
                    Source: {opportunity.data_source}
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

// Main Component
export default function AIAnalysis({ language = 'fr' }) {
  const { i18n } = useTranslation();
  const currentLang = i18n.language || language;

  const [mode, setMode] = useState('export');
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [aiHealthy, setAiHealthy] = useState(null);

  const texts = {
    fr: {
      title: "Analyse IA des Opportunités",
      subtitle: "Powered by Gemini AI - Données officielles IMF, UNCTAD, OEC",
      selectCountry: "Sélectionnez un pays",
      analyze: "Analyser avec IA",
      exportMode: "Export",
      importMode: "Import",
      industrialMode: "Industriel",
      loading: "Analyse IA en cours...",
      loadingMessages: [
        "Synchronisation des données ZLECAf...",
        "Analyse des flux commerciaux IMF 2024...",
        "Extraction des patterns UNCTAD...",
        "Calcul des potentiels tarifaires...",
        "Cartographie des opportunités..."
      ],
      noData: "Sélectionnez un pays pour lancer l'analyse IA",
      opportunities: "Opportunités identifiées",
      totalPotential: "Potentiel total",
      topSectors: "Secteurs prioritaires",
      estimation: "Contient des estimations",
      verified: "Données vérifiées",
      sources: "Sources",
      aiStatus: "Statut IA",
      aiReady: "Gemini prêt",
      aiNotReady: "IA non configurée"
    },
    en: {
      title: "AI Trade Opportunity Analysis",
      subtitle: "Powered by Gemini AI - Official IMF, UNCTAD, OEC data",
      selectCountry: "Select a country",
      analyze: "Analyze with AI",
      exportMode: "Export",
      importMode: "Import",
      industrialMode: "Industrial",
      loading: "AI analysis in progress...",
      loadingMessages: [
        "Synchronizing AfCFTA data...",
        "Analyzing IMF 2024 trade flows...",
        "Extracting UNCTAD patterns...",
        "Computing tariff potentials...",
        "Mapping opportunities..."
      ],
      noData: "Select a country to start AI analysis",
      opportunities: "Opportunities identified",
      totalPotential: "Total potential",
      topSectors: "Priority sectors",
      estimation: "Contains estimations",
      verified: "Verified data",
      sources: "Sources",
      aiStatus: "AI Status",
      aiReady: "Gemini ready",
      aiNotReady: "AI not configured"
    }
  };
  const txt = texts[currentLang] || texts.fr;

  // Loading message animation
  const [loadingMessage, setLoadingMessage] = useState(0);
  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setLoadingMessage(prev => (prev + 1) % txt.loadingMessages.length);
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [loading, txt.loadingMessages.length]);

  // Check AI health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await axios.get(`${API}/ai/health`);
        setAiHealthy(res.data.status === 'operational');
      } catch {
        setAiHealthy(false);
      }
    };
    checkHealth();
  }, []);

  // Fetch countries
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const res = await axios.get(`${API}/substitution/countries?lang=${currentLang}`);
        setCountries(res.data.countries || []);
      } catch (err) {
        console.error('Error fetching countries:', err);
      }
    };
    fetchCountries();
  }, [currentLang]);

  // Analyze function
  const runAnalysis = useCallback(async () => {
    if (!selectedCountry) return;

    setLoading(true);
    setError(null);
    setAnalysisData(null);

    // Find country name from ISO3
    const countryObj = countries.find(c => c.iso3 === selectedCountry);
    const countryName = countryObj?.name || selectedCountry;

    try {
      const res = await axios.get(
        `${API}/ai/opportunities/${encodeURIComponent(countryName)}`,
        { params: { mode, lang: currentLang } }
      );
      setAnalysisData(res.data);
    } catch (err) {
      console.error('AI Analysis error:', err);
      setError(err.response?.data?.detail || 'Erreur lors de l\'analyse IA');
    } finally {
      setLoading(false);
    }
  }, [selectedCountry, mode, currentLang, countries]);

  // Calculate summary stats
  const summaryStats = React.useMemo(() => {
    if (!analysisData?.opportunities) return null;

    const opps = analysisData.opportunities;
    const totalValue = opps.reduce((sum, opp) => {
      let val = 0;
      if (mode === 'export') {
        val = opp.potential_value_musd || 0;
      } else if (mode === 'import') {
        val = opp.substitution_potential_musd || opp.import_value_musd || 0;
      } else if (mode === 'industrial') {
        // Industrial mode: parse estimated_output which may be string like "1800 MUSD"
        const outputStr = opp.estimated_output || '';
        const match = outputStr.match(/(\d+)/);
        val = match ? parseFloat(match[1]) : 0;
      }
      return sum + val;
    }, 0);

    const hasEstimations = opps.some(opp => opp.is_estimation);

    return {
      count: opps.length,
      totalValue,
      hasEstimations
    };
  }, [analysisData, mode]);

  return (
    <div className="space-y-6" data-testid="ai-analysis">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <Sparkles className="h-8 w-8 text-purple-600" />
          <h2 className="text-3xl font-black text-slate-900 uppercase tracking-tight">
            {txt.title}
          </h2>
        </div>
        <p className="text-slate-500">{txt.subtitle}</p>
        
        {/* AI Status badge */}
        <div className="mt-2">
          {aiHealthy !== null && (
            <Badge className={aiHealthy ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}>
              {aiHealthy ? (
                <>
                  <CheckCircle className="h-3 w-3 mr-1" />
                  {txt.aiReady}
                </>
              ) : (
                <>
                  <AlertCircle className="h-3 w-3 mr-1" />
                  {txt.aiNotReady}
                </>
              )}
            </Badge>
          )}
        </div>
      </div>

      {/* Controls */}
      <Card className="shadow-lg">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4 items-end">
            {/* Mode selection */}
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">Mode d'analyse</label>
              <Tabs value={mode} onValueChange={setMode} className="w-full">
                <TabsList className="grid grid-cols-3 w-full">
                  <TabsTrigger value="export" className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    {txt.exportMode}
                  </TabsTrigger>
                  <TabsTrigger value="import" className="flex items-center gap-2">
                    <TrendingDown className="h-4 w-4" />
                    {txt.importMode}
                  </TabsTrigger>
                  <TabsTrigger value="industrial" className="flex items-center gap-2">
                    <Factory className="h-4 w-4" />
                    {txt.industrialMode}
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            {/* Country selection */}
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">{txt.selectCountry}</label>
              <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger className="w-full" data-testid="ai-country-select">
                  <SelectValue placeholder={txt.selectCountry} />
                </SelectTrigger>
                <SelectContent>
                  {countries.map(country => (
                    <SelectItem key={country.iso3} value={country.iso3}>
                      {country.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Analyze button */}
            <Button
              onClick={runAnalysis}
              disabled={!selectedCountry || loading || !aiHealthy}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
              data-testid="ai-analyze-btn"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4 mr-2" />
              )}
              {txt.analyze}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Loading state */}
      {loading && (
        <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200">
          <CardContent className="py-16 text-center">
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className="absolute inset-0 border-4 border-purple-200 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-t-purple-500 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <Sparkles className="h-8 w-8 text-purple-500" />
              </div>
            </div>
            <p className="text-xl font-bold text-slate-800 mb-2">{txt.loading}</p>
            <p className="text-purple-600 font-medium text-sm animate-pulse">
              {txt.loadingMessages[loadingMessage]}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Error state */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {!loading && !error && analysisData && (
        <>
          {/* Summary Stats */}
          {summaryStats && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="bg-white shadow-lg">
                <CardContent className="p-5">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 flex items-center justify-center rounded-full bg-purple-100 text-purple-600">
                      <Target className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">{txt.opportunities}</p>
                      <p className="text-2xl font-bold text-slate-900">{summaryStats.count}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-lg">
                <CardContent className="p-5">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 flex items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                      <DollarSign className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">{txt.totalPotential}</p>
                      <p className="text-2xl font-bold text-emerald-600">
                        {formatValue(summaryStats.totalValue)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white shadow-lg">
                <CardContent className="p-5">
                  <div className="flex items-center gap-4">
                    <div className={`h-12 w-12 flex items-center justify-center rounded-full ${
                      summaryStats.hasEstimations 
                        ? 'bg-amber-100 text-amber-600' 
                        : 'bg-emerald-100 text-emerald-600'
                    }`}>
                      {summaryStats.hasEstimations ? (
                        <AlertTriangle className="h-6 w-6" />
                      ) : (
                        <CheckCircle className="h-6 w-6" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-slate-500">Fiabilité</p>
                      <p className="text-lg font-bold text-slate-900">
                        {summaryStats.hasEstimations ? txt.estimation : txt.verified}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Sankey Diagram */}
          {analysisData.opportunities?.length > 0 && (
            <TradeSankeyDiagram
              opportunities={analysisData.opportunities.map(opp => ({
                ...opp,
                country: analysisData.country,
                exportingCountry: analysisData.country
              }))}
              mode={mode}
              language={currentLang}
            />
          )}

          {/* Opportunities Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {analysisData.opportunities?.slice(0, 10).map((opp, idx) => (
              <AIOpportunityCard
                key={idx}
                opportunity={opp}
                mode={mode}
                language={currentLang}
                index={idx}
              />
            ))}
          </div>

          {/* Sources footer */}
          {analysisData.sources && (
            <Card className="bg-slate-50 border-slate-200">
              <CardContent className="py-4 px-6">
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Info className="h-4 w-4" />
                  <span className="font-medium">{txt.sources}:</span>
                  <span>{analysisData.sources.join(', ')}</span>
                </div>
                {analysisData.generated_by && (
                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    Generated by {analysisData.generated_by}
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Empty state */}
      {!loading && !error && !analysisData && (
        <Card className="bg-slate-50 border-slate-200">
          <CardContent className="py-16 text-center">
            <Sparkles className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">{txt.noData}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
