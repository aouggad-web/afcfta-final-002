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
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, PieChart, Pie, Cell, Legend
} from 'recharts';
import TradeSankeyDiagram from './TradeSankeyDiagram';
import OpportunityPdfExport from './OpportunityPdfExport';
import { opportunityPdfFilename } from '../../utils/opportunityPdf';
import {
  TrendingUp, TrendingDown, Globe, Package, Factory, Ship,
  ArrowRight, ArrowLeftRight, Loader2, AlertCircle, Search,
  DollarSign, Target, MapPin, ChevronRight, ChevronDown, Sparkles,
  BarChart3, ShieldCheck
} from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const COLORS = ['#059669', '#0891b2', '#7c3aed', '#dc2626', '#ea580c', '#ca8a04', '#16a34a', '#2563eb'];

// Sous-module « faisabilité de substitution » (services/substitution_feasibility_service.py) :
// tous les dollars importés ne sont pas également substituables par une offre africaine — l'effet
// marque, l'écart technologique, le réseau après-vente et la certification bornent la part
// réalistement adressable. Le backend calcule déjà coefficient + barrières + justification
// (champ `substitution_feasibility` sur chaque opportunité d'import) ; ce bloc les affiche.
const FEASIBILITY_TXT = {
  fr: {
    title: 'Faisabilité de substitution',
    coefficient: 'Part réalistement adressable',
    bindingCapacity: 'Facteur limitant : capacité africaine (offre insuffisante)',
    bindingExporterCapacity: "Facteur limitant : capacité d'export du pays",
    bindingFeasibility: 'Facteur limitant : substituabilité (marque / technologie)',
    barriers: 'Barrières non tarifaires',
    brand_effect: 'Effet marque',
    technology_gap: 'Écart technologique',
    after_sales_network: 'Réseau après-vente',
    certification: 'Certification',
    intensityLabel: { faible: 'Faible', moyen: 'Moyen', fort: 'Fort' },
  },
  en: {
    title: 'Substitution feasibility',
    coefficient: 'Realistically addressable share',
    bindingCapacity: 'Binding constraint: African capacity (insufficient supply)',
    bindingExporterCapacity: "Binding constraint: the country's export capacity",
    bindingFeasibility: 'Binding constraint: substitutability (brand / technology)',
    barriers: 'Non-tariff barriers',
    brand_effect: 'Brand effect',
    technology_gap: 'Technology gap',
    after_sales_network: 'After-sales network',
    certification: 'Certification',
    intensityLabel: { faible: 'Low', moyen: 'Medium', fort: 'High' },
  },
};

// Production africaine VÉRIFIÉE (FAOSTAT / UNIDO / USGS) : le backend joint à
// chaque opportunité la production physique réelle du produit sur le continent
// (champ `verified_production`) — la preuve matérielle derrière les flux
// commerciaux. Bloc + textes du panneau d'analyse transversal et du drill-down
// chapitre (SH2) -> position (SH4) -> produit (SH6).
const ENRICHED_TXT = {
  fr: {
    verifiedTitle: 'Production africaine vérifiée',
    verifiedNone: 'Produit non couvert par le référentiel production (FAOSTAT / UNIDO / USGS)',
    analysisTitle: "Synthèse d'analyse",
    avgCoef: 'Substituabilité moyenne (pondérée par la valeur)',
    constraints: 'Facteurs limitants',
    difficulties: 'Difficulté',
    verifiedCount: 'Opportunités adossées à une production vérifiée',
    hierarchyTitle: 'Priorités par chapitre — affiner en SH4 puis SH6',
    hierarchyHint: 'Cliquez un chapitre pour le détailler en positions SH4, puis en produits SH6.',
    opportunitiesCount: 'opportunités',
  },
  en: {
    verifiedTitle: 'Verified African production',
    verifiedNone: 'Product not covered by the production reference (FAOSTAT / UNIDO / USGS)',
    analysisTitle: 'Analysis summary',
    avgCoef: 'Average substitutability (value-weighted)',
    constraints: 'Binding constraints',
    difficulties: 'Difficulty',
    verifiedCount: 'Opportunities backed by verified production',
    hierarchyTitle: 'Priorities by chapter — refine to HS4 then HS6',
    hierarchyHint: 'Click a chapter to break it down into HS4 headings, then HS6 products.',
    opportunitiesCount: 'opportunities',
  },
};

// Valeur de production : l'unité varie selon le référentiel (tonnes FAOSTAT,
// USD de valeur ajoutée UNIDO, tonnes/carats USGS) — formater en conséquence.
const fmtProduction = (value, unit) => {
  if (value == null || isNaN(value)) return '—';
  if (unit === 'USD') return formatValue(value);
  const n = value >= 1e6 ? `${(value / 1e6).toFixed(1)}M` : value >= 1e3 ? `${(value / 1e3).toFixed(0)}K` : `${Math.round(value)}`;
  return `${n} ${unit || ''}`.trim();
};

// Positionnement prix (opportunités d'export) : le backend compare le prix
// moyen d'export du pays ($/t, valeur unitaire BACI) au prix moyen que le
// marché cible paie déjà à ses fournisseurs actuels — l'information dont un
// exportateur a besoin pour savoir s'il peut se placer sur un marché.
const fmtPerTonne = (v) => {
  if (v == null || isNaN(v)) return '—';
  return `$${Math.round(v).toLocaleString('en-US')}/t`;
};

const POSITIONING_CHIP = {
  'compétitif': 'bg-emerald-100 text-emerald-700',
  'aligné': 'bg-blue-100 text-blue-700',
  'premium': 'bg-amber-100 text-amber-700',
};

const POSITIONING_LABEL = {
  fr: { 'compétitif': 'Compétitif', 'aligné': 'Aligné', 'premium': 'Premium' },
  en: { 'compétitif': 'Competitive', 'aligné': 'Aligned', 'premium': 'Premium' },
};

const coefficientColor = (coef) => {
  if (coef >= 0.7) return { bar: 'bg-emerald-500', text: 'text-emerald-700', chip: 'bg-emerald-100 text-emerald-700' };
  if (coef >= 0.4) return { bar: 'bg-amber-500', text: 'text-amber-700', chip: 'bg-amber-100 text-amber-700' };
  return { bar: 'bg-red-500', text: 'text-red-700', chip: 'bg-red-100 text-red-700' };
};

const intensityChipColor = (intensity) => {
  if (intensity === 'fort') return 'bg-red-100 text-red-700';
  if (intensity === 'moyen') return 'bg-amber-100 text-amber-700';
  return 'bg-slate-100 text-slate-600';
};

// Affiche le coefficient de substituabilité, le facteur limitant et le détail
// des barrières non tarifaires. Utilisé sur les deux chemins : substitution
// d'imports (facteur limitant « capacité africaine » vs « substituabilité »)
// et opportunités d'export (« capacité exportateur » vs « substituabilité ») —
// real_substitution_service.py applique désormais la même borne aux deux.
const BINDING_LABEL_KEY = {
  'capacité africaine': 'bindingCapacity',
  'capacité exportateur': 'bindingExporterCapacity',
  'substituabilité': 'bindingFeasibility',
};

const FeasibilityBlock = ({ feasibility, bindingConstraint, language }) => {
  if (!feasibility) return null;
  const txt = FEASIBILITY_TXT[language] || FEASIBILITY_TXT.fr;
  const coef = feasibility.coefficient;
  const colors = coefficientColor(coef);
  const barriers = feasibility.barriers;
  const bindingLabel = txt[BINDING_LABEL_KEY[bindingConstraint]] || null;

  return (
    <div className="mb-4 bg-slate-50 rounded-lg p-3" data-testid="substitution-feasibility">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-slate-500">{txt.coefficient}</span>
        <span className={`text-sm font-bold ${colors.text}`}>{Math.round(coef * 100)}%</span>
      </div>
      <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden mb-2">
        <div className={`h-full rounded-full ${colors.bar}`} style={{ width: `${Math.round(coef * 100)}%` }} />
      </div>
      {bindingLabel && <p className="text-[11px] text-slate-500 mb-2">{bindingLabel}</p>}
      {barriers && (
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(barriers).map(([key, intensity]) => (
            <span
              key={key}
              className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${intensityChipColor(intensity)}`}
              title={feasibility.rationale}
            >
              {txt[key] || key} · {txt.intensityLabel[intensity] || intensity}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

// Production africaine réelle du produit (FAOSTAT / UNIDO / USGS) : commodité,
// année, institution source et top producteurs mesurés — avec le garde-fou de
// couverture quand le référentiel n'ingère qu'une poignée de pays.
const VerifiedProductionBlock = ({ production, language }) => {
  if (!production) return null;
  const txt = ENRICHED_TXT[language] || ENRICHED_TXT.fr;
  return (
    <div className="mb-4 bg-emerald-50/60 border border-emerald-100 rounded-lg p-3" data-testid="verified-production">
      <div className="flex items-center gap-1.5 mb-1.5">
        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
        <span className="text-xs font-semibold text-emerald-800">{txt.verifiedTitle}</span>
        <span className="text-[10px] text-emerald-600 ml-auto">
          {production.institution} · {production.year}
        </span>
      </div>
      <p className="text-[11px] text-slate-600 mb-1.5">{production.commodity}</p>
      <div className="flex flex-wrap gap-1.5">
        {(production.top_producers || []).map((p) => (
          <span key={p.country_iso3} className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-white border border-emerald-200 text-emerald-800">
            {p.country_name} · {fmtProduction(p.value, production.unit)}
            {p.share_pct != null && ` (${p.share_pct}%)`}
          </span>
        ))}
      </div>
      {production.coverage_caveat && (
        <p className="mt-1.5 text-[10px] text-amber-700" data-testid="verified-production-caveat">
          ⚠ {production.coverage_caveat}
        </p>
      )}
    </div>
  );
};

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

// Opportunity Card Component (exportée pour test unitaire direct — évite de
// devoir mocker tout le cycle de fetch axios de SubstitutionAnalysis pour
// vérifier l'affichage difficulté/faisabilité).
export const OpportunityCard = ({ opportunity, type, language }) => {
  const isImport = type === 'import';
  const product = isImport ? opportunity.imported_product : (opportunity.exportable_product || opportunity.export_product);
  const targets = isImport ? opportunity.african_suppliers : (opportunity.target_markets || opportunity.potential_markets);
  
  // _assess_difficulty (real_substitution_service.py) renvoie directement les
  // libellés français "Facile"/"Modéré"/"Difficile"/"Très difficile" — les
  // comparer à des clés anglaises ('easy'/'moderate'/'difficult') ne matchait
  // jamais, donc toutes les cartes s'affichaient en "Difficile"/ambre par
  // défaut quel que soit le niveau réel.
  const difficultyColors = {
    'Facile': "bg-emerald-100 text-emerald-700",
    'Modéré': "bg-amber-100 text-amber-700",
    'Difficile': "bg-orange-100 text-orange-700",
    'Très difficile': "bg-red-100 text-red-700",
  };
  const difficultyLabelEn = {
    'Facile': 'Easy', 'Modéré': 'Moderate', 'Difficile': 'Difficult', 'Très difficile': 'Very difficult',
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
            <Badge className={difficultyColors[opportunity.difficulty] || difficultyColors['Modéré']}>
              {language === 'en' ? (difficultyLabelEn[opportunity.difficulty] || opportunity.difficulty) : opportunity.difficulty}
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
              {isImport ? "Import actuel" : "Marché potentiel"}
            </p>
            <p className="font-bold text-lg text-slate-900">
              {formatValue(isImport ? product?.import_value : opportunity.total_market_potential)}
            </p>
          </div>
          <div className="bg-emerald-50 rounded-lg p-3">
            <p className="text-xs text-emerald-600 mb-1">
              {isImport ? "Potentiel substitution" : "Avantage ZLECAf"}
            </p>
            <p className="font-bold text-lg text-emerald-700">
              {isImport ? formatValue(opportunity.substitution_potential) : (opportunity.afcfta_advantage || '-')}
            </p>
          </div>
        </div>

        {/* Feasibility — coefficient, binding constraint, barriers (both flows) */}
        <FeasibilityBlock
          feasibility={opportunity.substitution_feasibility}
          bindingConstraint={opportunity.binding_constraint}
          language={language}
        />

        {/* Real African production of this product (FAOSTAT / UNIDO / USGS) */}
        <VerifiedProductionBlock
          production={opportunity.verified_production}
          language={language}
        />

        {/* Current Source (for imports) */}
        {isImport && product?.current_source && (
          <div className="mb-4 flex items-center gap-2 text-sm text-slate-500">
            <Globe className="h-4 w-4" />
            <span>Source actuelle: <strong className="text-slate-700">{product.current_source}</strong></span>
          </div>
        )}

        {/* Average export price + market-match caveat (exports only) */}
        {!isImport && opportunity.exporter_avg_price_usd_per_tonne != null && (
          <div className="mb-3 flex items-center gap-2 text-sm text-slate-600" data-testid="exporter-avg-price">
            <DollarSign className="h-4 w-4 text-slate-400" />
            <span>
              {language === 'en' ? 'Average export price' : "Prix moyen à l'export"} :{' '}
              <strong className="text-slate-800">{fmtPerTonne(opportunity.exporter_avg_price_usd_per_tonne)}</strong>
            </span>
          </div>
        )}
        {!isImport && opportunity.market_match_level === 'hs4' && (
          <p className="mb-3 text-[11px] text-amber-700 bg-amber-50 rounded-md px-2.5 py-1.5" data-testid="market-match-caveat">
            {language === 'en'
              ? 'Markets estimated at HS4 level (this exact HS6 product is absent from the top imports of the countries surveyed).'
              : "Marchés estimés au niveau SH4 (ce produit SH6 exact est absent des top-imports des pays sondés)."}
          </p>
        )}

        {/* Suppliers/Markets */}
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
            {isImport ? "Fournisseurs africains potentiels" : "Marchés cibles"}
          </p>
          <div className="space-y-2">
            {targets?.slice(0, 3).map((target, idx) => (
              <div key={idx} className="bg-slate-50 rounded-lg px-3 py-2">
                <div className="flex items-center justify-between">
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
                    {formatValue(isImport ? (target.export_value || target.production_capacity) : target.market_size)}
                  </span>
                </div>
                {/* Positionnement prix (export) : prix moyen payé par le marché
                    à ses fournisseurs actuels vs prix moyen d'export du pays. */}
                {!isImport && target.price_positioning && (
                  <div className="mt-1.5 flex items-center justify-between gap-2" data-testid="price-positioning">
                    <span className="text-[11px] text-slate-500">
                      {language === 'en' ? 'Market pays' : 'Le marché paie'}{' '}
                      <strong>{fmtPerTonne(target.price_positioning.market_avg_price_usd_per_tonne)}</strong>
                      {' · '}
                      {target.price_positioning.price_delta_pct > 0 ? '+' : ''}
                      {target.price_positioning.price_delta_pct}%
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${POSITIONING_CHIP[target.price_positioning.positioning] || POSITIONING_CHIP['aligné']}`}>
                      {(POSITIONING_LABEL[language] || POSITIONING_LABEL.fr)[target.price_positioning.positioning] || target.price_positioning.positioning}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Panneau « synthèse d'analyse » : lecture transversale du portefeuille
// d'opportunités calculée par le backend (summary.analysis) — substituabilité
// moyenne pondérée, répartition difficulté / facteur limitant, couverture du
// référentiel production.
const AnalysisSummaryPanel = ({ analysis, language }) => {
  if (!analysis || Object.keys(analysis).length === 0) return null;
  const txt = ENRICHED_TXT[language] || ENRICHED_TXT.fr;
  const feasTxt = FEASIBILITY_TXT[language] || FEASIBILITY_TXT.fr;
  const difficultyLabelEn = {
    'Facile': 'Easy', 'Modéré': 'Moderate', 'Difficile': 'Difficult', 'Très difficile': 'Very difficult',
  };
  const constraintLabels = {
    fr: { 'capacité africaine': 'Capacité africaine', 'capacité exportateur': 'Capacité exportateur', 'substituabilité': 'Substituabilité' },
    en: { 'capacité africaine': 'African capacity', 'capacité exportateur': 'Exporter capacity', 'substituabilité': 'Substitutability' },
  };
  const cLabels = constraintLabels[language] || constraintLabels.fr;

  return (
    <Card className="shadow-lg border-slate-200" data-testid="analysis-summary">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-emerald-600" />
          {txt.analysisTitle}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1">{txt.avgCoef}</p>
          <p className="text-2xl font-bold text-slate-900">
            {analysis.avg_feasibility_coefficient != null
              ? `${Math.round(analysis.avg_feasibility_coefficient * 100)}%`
              : '—'}
          </p>
        </div>
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1.5">{txt.difficulties}</p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(analysis.difficulty_distribution || {}).map(([label, count]) => (
              <span key={label} className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700">
                {language === 'en' ? (difficultyLabelEn[label] || label) : label} · {count}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-slate-50 rounded-lg p-3">
          <p className="text-xs text-slate-500 mb-1.5">{txt.constraints}</p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(analysis.binding_constraint_distribution || {}).map(([label, count]) => (
              <span key={label} className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700">
                {cLabels[label] || label} · {count}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-emerald-50 rounded-lg p-3">
          <p className="text-xs text-emerald-600 mb-1">{txt.verifiedCount}</p>
          <p className="text-2xl font-bold text-emerald-700">
            {analysis.verified_production_count ?? 0}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

// Drill-down chapitre (SH2) -> position (SH4) -> produit (SH6) calculé par le
// backend (summary.product_hierarchy) : l'utilisateur repère le chapitre
// porteur, l'ouvre en positions SH4, puis lit les codes SH6 exacts — la
// granularité où se prend la décision.
const ProductHierarchyPanel = ({ hierarchy, language }) => {
  const [openChapter, setOpenChapter] = useState(null);
  const [openHs4, setOpenHs4] = useState(null);
  if (!hierarchy?.length) return null;
  const txt = ENRICHED_TXT[language] || ENRICHED_TXT.fr;

  return (
    <Card className="shadow-lg" data-testid="product-hierarchy">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-bold">{txt.hierarchyTitle}</CardTitle>
        <CardDescription className="text-xs">{txt.hierarchyHint}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {hierarchy.map((chapter) => {
          const isOpen = openChapter === chapter.chapter;
          return (
            <div key={chapter.chapter} className="border border-slate-200 rounded-lg overflow-hidden">
              <button
                type="button"
                onClick={() => { setOpenChapter(isOpen ? null : chapter.chapter); setOpenHs4(null); }}
                className="w-full flex items-center gap-2 px-3 py-2.5 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
                data-testid={`hierarchy-chapter-${chapter.chapter}`}
              >
                {isOpen ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
                <Badge variant="outline" className="font-mono text-xs">SH {chapter.chapter}</Badge>
                <span className="font-medium text-sm text-slate-800 flex-1">{chapter.name}</span>
                <span className="text-xs text-slate-500">{chapter.opportunity_count} {txt.opportunitiesCount}</span>
                <span className="text-sm font-bold text-emerald-700">{formatValue(chapter.total_value)}</span>
              </button>
              {isOpen && (
                <div className="divide-y divide-slate-100">
                  {(chapter.hs4 || []).map((hs4) => {
                    const hs4Open = openHs4 === hs4.hs4_code;
                    return (
                      <div key={hs4.hs4_code}>
                        <button
                          type="button"
                          onClick={() => setOpenHs4(hs4Open ? null : hs4.hs4_code)}
                          className="w-full flex items-center gap-2 pl-9 pr-3 py-2 hover:bg-slate-50 transition-colors text-left"
                          data-testid={`hierarchy-hs4-${hs4.hs4_code}`}
                        >
                          {hs4Open ? <ChevronDown className="h-3.5 w-3.5 text-slate-400" /> : <ChevronRight className="h-3.5 w-3.5 text-slate-400" />}
                          <Badge variant="outline" className="font-mono text-[10px]">SH {hs4.hs4_code}</Badge>
                          <span className="text-sm text-slate-700 flex-1 truncate">{hs4.representative_name}</span>
                          <span className="text-xs font-semibold text-emerald-600">{formatValue(hs4.total_value)}</span>
                        </button>
                        {hs4Open && (
                          <div className="pl-16 pr-3 pb-2 space-y-1">
                            {(hs4.products || []).map((p) => (
                              <div key={p.hs_code} className="flex items-center gap-2 py-1 text-sm" data-testid={`hierarchy-hs6-${p.hs_code}`}>
                                <Badge className="font-mono text-[10px] bg-emerald-100 text-emerald-800 hover:bg-emerald-100">SH6 {p.hs_code}</Badge>
                                <span className="text-slate-600 flex-1 truncate">{p.name}</span>
                                {p.feasibility_coefficient != null && (
                                  <span className="text-[10px] text-slate-500">{Math.round(p.feasibility_coefficient * 100)}%</span>
                                )}
                                <span className="text-xs font-semibold text-slate-800">{formatValue(p.value)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
};

// Main Component
export default function SubstitutionAnalysis({ language = 'fr', initialCountry = null }) {
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
      source: "Sources: UN Comtrade, OEC, UNCTAD, Offices nationaux de statistiques",
      outsideAfrica: "Hors Afrique",
      product: "Produit",
      afcftaMarkets: "Marchés ZLECAf",
      tradeFlows: "Flux Commerciaux"
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
      source: "Sources: UN Comtrade, OEC, UNCTAD, National statistics offices",
      outsideAfrica: "Outside Africa",
      product: "Product",
      afcftaMarkets: "AfCFTA Markets",
      tradeFlows: "Trade Flows"
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

  // Pré-remplissage venu d'un autre module (voir OpportunitiesTab.jsx) : le
  // pays du handoff déclenche l'analyse via l'effet auto-analyze ci-dessous.
  useEffect(() => {
    if (initialCountry?.iso3) {
      setActiveTab('import');
      setSelectedCountry(initialCountry.iso3);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialCountry?.iso3, initialCountry?.k]);

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

  // Get selected country name for Sankey diagram
  const countryName = useMemo(() => {
    const found = countries.find(c => c.iso3 === selectedCountry);
    return found?.name || selectedCountry;
  }, [countries, selectedCountry]);

  // Spécification du rapport PDF du sous-module (voir utils/opportunityPdf.js) :
  // décrit en données l'onglet actif — le bâtisseur commun gère la mise en page.
  const buildPdfSpec = useCallback(() => {
    if (!currentData) return null;
    const isImport = activeTab === 'import';
    const fr = currentLang !== 'en';
    const summary = currentData.summary || {};
    const kpis = [
      { label: txt.totalOpportunities, value: String(summary.total_opportunities ?? 0), accent: 'gold' },
      {
        label: isImport ? txt.substitutableValue : (fr ? 'Potentiel de marché' : 'Market potential'),
        value: formatValue(isImport ? summary.total_substitutable_value : summary.total_market_potential),
        accent: 'green',
      },
    ];
    if (isImport && summary.total_imports_from_outside) {
      kpis.push({ label: txt.outsideAfrica, value: formatValue(summary.total_imports_from_outside), accent: 'red' });
    }

    const sections = [];
    // Synthèse d'analyse (mêmes chiffres que le panneau à l'écran).
    const analysis = summary.analysis || {};
    if (Object.keys(analysis).length) {
      const enr = ENRICHED_TXT[fr ? 'fr' : 'en'];
      sections.push({
        title: enr.analysisTitle,
        keyValues: [
          { label: enr.avgCoef, value: analysis.avg_feasibility_coefficient != null ? `${Math.round(analysis.avg_feasibility_coefficient * 100)}%` : '—' },
          { label: enr.difficulties, value: Object.entries(analysis.difficulty_distribution || {}).map(([k, v]) => `${k}: ${v}`).join(' · ') || '—' },
          { label: enr.constraints, value: Object.entries(analysis.binding_constraint_distribution || {}).map(([k, v]) => `${k}: ${v}`).join(' · ') || '—' },
          { label: enr.verifiedCount, value: String(analysis.verified_production_count ?? 0) },
        ],
      });
    }
    if (isImport) {
      sections.push({
        title: fr ? 'Opportunités de substitution d’imports' : 'Import substitution opportunities',
        table: {
          columns: [
            { key: 'hs', label: 'SH', width: 0.7 },
            { key: 'name', label: fr ? 'Produit' : 'Product', width: 2.6 },
            { key: 'imp', label: fr ? 'Import actuel' : 'Current import', align: 'right', width: 1.1 },
            { key: 'coef', label: fr ? 'Substituabilité' : 'Substitutability', align: 'right', width: 1.0 },
            { key: 'pot', label: fr ? 'Potentiel' : 'Potential', align: 'right', width: 1.1 },
            { key: 'constraint', label: fr ? 'Contrainte' : 'Constraint', width: 1.2 },
          ],
          rows: opportunities.map((o) => ({
            hs: o.imported_product?.hs_code || '—',
            name: o.imported_product?.name || '—',
            imp: formatValue(o.imported_product?.import_value),
            coef: o.substitution_feasibility ? `${Math.round(o.substitution_feasibility.coefficient * 100)}%` : '—',
            pot: formatValue(o.substitution_potential),
            constraint: o.binding_constraint || '—',
          })),
        },
      });
    } else {
      sections.push({
        title: fr ? 'Opportunités d’export (niveau produit SH6)' : 'Export opportunities (SH6 product level)',
        table: {
          columns: [
            { key: 'hs', label: 'SH', width: 0.7 },
            { key: 'name', label: fr ? 'Produit' : 'Product', width: 2.4 },
            { key: 'price', label: fr ? 'Prix export' : 'Export price', align: 'right', width: 1.0 },
            { key: 'coef', label: fr ? 'Substituabilité' : 'Substitutability', align: 'right', width: 1.0 },
            { key: 'pot', label: fr ? 'Potentiel' : 'Potential', align: 'right', width: 1.1 },
            { key: 'constraint', label: fr ? 'Contrainte' : 'Constraint', width: 1.2 },
          ],
          rows: opportunities.map((o) => ({
            hs: o.export_product?.hs_code || '—',
            name: o.export_product?.name || '—',
            price: o.exporter_avg_price_usd_per_tonne != null ? fmtPerTonne(o.exporter_avg_price_usd_per_tonne) : '—',
            coef: o.substitution_feasibility ? `${Math.round(o.substitution_feasibility.coefficient * 100)}%` : '—',
            pot: formatValue(o.total_market_potential),
            constraint: o.binding_constraint || '—',
          })),
        },
      });
      // Détail marchés avec positionnement prix — la donnée décisive pour se placer.
      const marketRows = opportunities.flatMap((o) =>
        (o.potential_markets || []).map((m) => ({
          product: `${o.export_product?.hs_code || ''} ${o.export_product?.name || ''}`.trim(),
          market: m.country_name,
          size: formatValue(m.market_size),
          marketPrice: m.price_positioning ? fmtPerTonne(m.price_positioning.market_avg_price_usd_per_tonne) : '—',
          delta: m.price_positioning ? `${m.price_positioning.price_delta_pct > 0 ? '+' : ''}${m.price_positioning.price_delta_pct}%` : '—',
          positioning: m.price_positioning
            ? (POSITIONING_LABEL[currentLang] || POSITIONING_LABEL.fr)[m.price_positioning.positioning] || m.price_positioning.positioning
            : '—',
        })),
      );
      if (marketRows.length) {
        sections.push({
          title: fr ? 'Marchés cibles et positionnement prix' : 'Target markets and price positioning',
          table: {
            columns: [
              { key: 'product', label: fr ? 'Produit' : 'Product', width: 2.2 },
              { key: 'market', label: fr ? 'Marché' : 'Market', width: 1.2 },
              { key: 'size', label: fr ? 'Taille' : 'Size', align: 'right', width: 0.9 },
              { key: 'marketPrice', label: fr ? 'Prix marché' : 'Market price', align: 'right', width: 1.0 },
              { key: 'delta', label: fr ? 'Écart' : 'Delta', align: 'right', width: 0.7 },
              { key: 'positioning', label: fr ? 'Position' : 'Position', width: 1.0 },
            ],
            rows: marketRows,
          },
        });
      }
    }

    // Production africaine vérifiée (FAOSTAT / UNIDO / USGS) par produit.
    const enr2 = ENRICHED_TXT[fr ? 'fr' : 'en'];
    const verifiedRows = opportunities
      .filter((o) => o.verified_production)
      .map((o) => {
        const vp = o.verified_production;
        const product = isImport ? o.imported_product : o.export_product;
        return {
          hs: product?.hs_code || '—',
          commodity: vp.commodity || '—',
          producers: (vp.top_producers || [])
            .map((p) => `${p.country_name} (${fmtProduction(p.value, vp.unit)})`)
            .join(' · '),
          source: `${vp.institution || '—'} ${vp.year || ''}`.trim(),
        };
      });
    if (verifiedRows.length) {
      sections.push({
        title: enr2.verifiedTitle,
        table: {
          columns: [
            { key: 'hs', label: 'SH', width: 0.7 },
            { key: 'commodity', label: fr ? 'Commodité' : 'Commodity', width: 1.8 },
            { key: 'producers', label: fr ? 'Top producteurs réels' : 'Top real producers', width: 3.0 },
            { key: 'source', label: 'Source', width: 0.9 },
          ],
          rows: verifiedRows,
        },
      });
    }
    // Drill-down chapitre -> SH4 -> SH6 (aplati en tableau).
    const hierarchyRows = (summary.product_hierarchy || []).flatMap((ch) =>
      (ch.hs4 || []).flatMap((h4) =>
        (h4.products || []).map((p) => ({
          chapter: `${ch.chapter} — ${ch.name}`,
          hs4: h4.hs4_code,
          hs6: p.hs_code,
          name: p.name || '—',
          value: formatValue(p.value),
        })),
      ),
    );
    if (hierarchyRows.length) {
      sections.push({
        title: enr2.hierarchyTitle,
        table: {
          columns: [
            { key: 'chapter', label: fr ? 'Chapitre' : 'Chapter', width: 1.7 },
            { key: 'hs4', label: 'SH4', width: 0.6 },
            { key: 'hs6', label: 'SH6', width: 0.7 },
            { key: 'name', label: fr ? 'Produit' : 'Product', width: 2.4 },
            { key: 'value', label: fr ? 'Valeur' : 'Value', align: 'right', width: 0.9 },
          ],
          rows: hierarchyRows,
        },
      });
    }

    return {
      badge: 'SUBSTITUTION',
      title: `${isImport ? (fr ? 'Substitution d’imports' : 'Import substitution') : (fr ? 'Opportunités d’export' : 'Export opportunities')} — ${countryName}`,
      subtitle: currentData.is_estimation
        ? (fr ? 'Estimation (repli statique — OEC indisponible)' : 'Estimate (static fallback — OEC unavailable)')
        : (fr ? 'Flux réels OEC / BACI' : 'Real OEC / BACI flows'),
      kpis,
      sections,
      source: currentData.data_source || 'OEC BACI',
      filename: opportunityPdfFilename('Substitution', `${selectedCountry}_${activeTab}`),
    };
  }, [currentData, activeTab, currentLang, countryName, opportunities, selectedCountry, txt]);

  // Transform substitution data for TradeSankeyDiagram
  // Converts nested API structure to flat format expected by Sankey
  const sankeyOpportunities = useMemo(() => {
    if (!opportunities.length) return [];

    return opportunities.flatMap(opp => {
      if (activeTab === 'import') {
        // Import mode: african_suppliers[] → potential_supplier → product → importingCountry
        const suppliers = opp.african_suppliers || [];
        if (!suppliers.length) return [];
        
        return suppliers.map(supplier => ({
          potential_supplier: supplier.country_name,
          product_name: opp.imported_product?.name || txt.product,
          importingCountry: countryName,
          substitution_potential_musd: (supplier.export_value || supplier.production_capacity || 0) / 1e6,
        }));
      } else {
        // Export mode: potential_markets[] → exportingCountry → product → potential_partner
        const markets = opp.target_markets || opp.potential_markets || [];
        if (!markets.length) return [];
        
        const productName = opp.exportable_product?.name || opp.export_product?.name || txt.product;
        
        return markets.map(market => ({
          exportingCountry: countryName,
          product_name: productName,
          potential_partner: market.country_name || market.name,
          potential_value_musd: (market.market_size || market.capture_potential || market.import_value || 0) / 1e6,
        }));
      }
    }).filter(item => {
      // Filter out entries with very low values
      const value = activeTab === 'import' 
        ? item.substitution_potential_musd 
        : item.potential_value_musd;
      return value > 0.1; // At least $100K
    });
  }, [opportunities, activeTab, countryName, txt.product]);

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
            <div className="flex flex-wrap items-center justify-center gap-3">
              <TabsList className="grid grid-cols-2 max-w-md">
                <TabsTrigger value="import" className="flex items-center gap-2" data-testid="import-tab">
                  <TrendingDown className="h-4 w-4" />
                  {txt.importTab}
                </TabsTrigger>
                <TabsTrigger value="export" className="flex items-center gap-2" data-testid="export-tab">
                  <TrendingUp className="h-4 w-4" />
                  {txt.exportTab}
                </TabsTrigger>
              </TabsList>
              <OpportunityPdfExport getSpec={buildPdfSpec} language={currentLang} />
            </div>

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

            {/* Analyse transversale du portefeuille (summary.analysis) */}
            <AnalysisSummaryPanel
              analysis={currentData?.summary?.analysis}
              language={currentLang}
            />

            {/* Opportunities Grid */}
            <TabsContent value="import" className="mt-0">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {importData?.opportunities?.slice(0, 12).map((opp, idx) => (
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
                {exportData?.opportunities?.slice(0, 12).map((opp, idx) => (
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

          {/* Drill-down chapitre (SH2) -> position (SH4) -> produit (SH6) */}
          <ProductHierarchyPanel
            hierarchy={currentData?.summary?.product_hierarchy}
            language={currentLang}
          />

          {/* Top Sectors Chart — imports ET exports (le backend fournit
              top_sectors pour les deux flux ; dataKey aligné sur total_value,
              le champ réellement renvoyé — "value" traçait des barres vides) */}
          {currentData?.summary?.top_sectors?.length > 0 && (
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
                    <Bar dataKey="total_value" fill="#10b981" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Trade Sankey Diagram - Flow visualization */}
          {sankeyOpportunities.length > 0 && (
            <TradeSankeyDiagram
              opportunities={sankeyOpportunities}
              mode={activeTab}
              language={currentLang}
            />
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
