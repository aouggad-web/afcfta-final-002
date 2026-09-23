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

const COLORS = ['var(--series-1)', 'var(--series-2)', 'var(--series-3)', 'var(--series-4)', 'var(--series-5)', 'var(--series-6)', 'var(--series-7)', 'var(--series-8)'];

// Sous-module « faisabilité de substitution » (services/substitution_feasibility_service.py) :
// tous les dollars importés ne sont pas également substituables par une offre africaine — l'effet
// marque, l'écart technologique, le réseau après-vente et la certification bornent la part
// réalistement adressable. Le backend calcule déjà coefficient + barrières + justification
// (champ `substitution_feasibility` sur chaque opportunité d'import) ; ce bloc les affiche.

// Production africaine VÉRIFIÉE (FAOSTAT / UNIDO / USGS) : le backend joint à
// chaque opportunité la production physique réelle du produit sur le continent
// (champ `verified_production`) — la preuve matérielle derrière les flux
// commerciaux. Bloc + textes du panneau d'analyse transversal et du drill-down
// chapitre (SH2) -> position (SH4) -> produit (SH6).

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
  'compétitif': 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]',
  'aligné': 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)]',
  'premium': 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]',
};


const coefficientColor = (coef) => {
  if (coef >= 0.7) return { bar: 'bg-emerald-500', text: 'text-[var(--success)]', chip: 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]' };
  if (coef >= 0.4) return { bar: 'bg-amber-500', text: 'text-[var(--gold)]', chip: 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]' };
  return { bar: 'bg-red-500', text: 'text-[var(--danger)]', chip: 'bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] text-[var(--danger)]' };
};

const intensityChipColor = (intensity) => {
  if (intensity === 'fort') return 'bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] text-[var(--danger)]';
  if (intensity === 'moyen') return 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]';
  return 'bg-[var(--afcfta-card2)] text-[var(--afcfta-muted)]';
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

const FeasibilityBlock = ({ feasibility, bindingConstraint }) => {
  const { t } = useTranslation();
  if (!feasibility) return null;
  const coef = feasibility.coefficient;
  const colors = coefficientColor(coef);
  const barriers = feasibility.barriers;
  const bindingKey = BINDING_LABEL_KEY[bindingConstraint];
  const bindingLabel = bindingKey
    ? t(`opportunities.substitutionAnalysis.feasibility.${bindingKey}`)
    : null;

  return (
    <div className="mb-4 bg-[var(--afcfta-card2)] rounded-lg p-3" data-testid="substitution-feasibility">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-[var(--afcfta-muted)]">{t('opportunities.substitutionAnalysis.feasibility.coefficient')}</span>
        <span className={`text-sm font-bold ${colors.text}`}>{Math.round(coef * 100)}%</span>
      </div>
      <div className="h-1.5 w-full bg-[var(--afcfta-card2)] rounded-full overflow-hidden mb-2">
        <div className={`h-full rounded-full ${colors.bar}`} style={{ width: `${Math.round(coef * 100)}%` }} />
      </div>
      {bindingLabel && <p className="text-[11px] text-[var(--afcfta-muted)] mb-2">{bindingLabel}</p>}
      {barriers && (
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(barriers).map(([key, intensity]) => (
            <span
              key={key}
              className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${intensityChipColor(intensity)}`}
              title={feasibility.rationale}
            >
              {t(`opportunities.substitutionAnalysis.feasibility.${key}`, { defaultValue: key })} · {t(`opportunities.substitutionAnalysis.feasibility.intensityLabel.${intensity}`, { defaultValue: intensity })}
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
const VerifiedProductionBlock = ({ production }) => {
  const { t } = useTranslation();
  if (!production) return null;
  return (
    <div className="mb-4 bg-emerald-50/60 border border-[color-mix(in_srgb,var(--success)_30%,transparent)] rounded-lg p-3" data-testid="verified-production">
      <div className="flex items-center gap-1.5 mb-1.5">
        <ShieldCheck className="h-3.5 w-3.5 text-[var(--success)]" />
        <span className="text-xs font-semibold text-[var(--success)]">{t('opportunities.substitutionAnalysis.enriched.verifiedTitle')}</span>
        <span className="text-[11px] text-[var(--success)] ml-auto">
          {production.institution} · {production.year}
        </span>
      </div>
      <p className="text-[11px] text-[var(--afcfta-muted)] mb-1.5">{production.commodity}</p>
      <div className="flex flex-wrap gap-1.5">
        {(production.top_producers || []).map((p) => (
          <span key={p.country_iso3} className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-[var(--afcfta-card)] border border-[color-mix(in_srgb,var(--success)_30%,transparent)] text-[var(--success)]">
            {p.country_name} · {fmtProduction(p.value, production.unit)}
            {p.share_pct != null && ` (${p.share_pct}%)`}
          </span>
        ))}
      </div>
      {production.coverage_caveat && (
        <p className="mt-1.5 text-[11px] text-[var(--gold)]" data-testid="verified-production-caveat">
          ⚠ {production.coverage_caveat}
        </p>
      )}
      {production.commodity_caveat && (
        <p className="mt-1.5 text-[11px] text-[var(--gold)]" data-testid="verified-production-commodity-caveat">
          ⚠ {production.commodity_caveat}
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
    emerald: "bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]",
    blue: "bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)]",
    purple: "bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] text-[var(--violet)]",
    orange: "bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)]",
    red: "bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] text-[var(--danger)]"
  };

  return (
    <Card className="bg-[var(--afcfta-card)] border-[var(--afcfta-border)] shadow-lg hover:shadow-xl transition-shadow">
      <CardContent className="p-5">
        <div className="flex items-center gap-4">
          <div className={`flex-shrink-0 h-12 w-12 flex items-center justify-center rounded-full ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-[var(--afcfta-muted)] truncate">{title}</p>
            <p className="text-2xl font-bold text-[var(--text)]">{value}</p>
            {subtitle && <p className="text-xs text-[var(--afcfta-muted)] mt-0.5">{subtitle}</p>}
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
  const { t } = useTranslation();
  const isImport = type === 'import';
  const product = isImport ? opportunity.imported_product : (opportunity.exportable_product || opportunity.export_product);
  const targets = isImport ? opportunity.african_suppliers : (opportunity.target_markets || opportunity.potential_markets);
  
  // Le serveur émet désormais un CODE (`difficulty_code`), pas un libellé.
  // Il émettait auparavant le français directement, et cet écran comparait
  // ce texte d'affichage à des clés anglaises : rien ne correspondait, et
  // toutes les cartes sortaient « Difficile » en ambre quel que soit le
  // niveau réel. Un texte d'affichage est un mauvais identifiant.
  // `difficulty` reste lu en repli, le temps que d'anciens clients passent.
  const difficultyColors = {
    easy: "bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]",
    moderate: "bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]",
    difficult: "bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)]",
    very_difficult: "bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] text-[var(--danger)]",
  };

  const competitivenessColors = {
    highly_competitive: "bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]",
    competitive: "bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)]",
    developing: "bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]"
  };

  return (
    <Card className="bg-[var(--afcfta-card)] border-[var(--afcfta-border)] shadow hover:shadow-lg transition-all">
      <CardContent className="p-5">
        {/* Product Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <Badge variant="outline" className="mb-2 font-mono text-xs">
              HS {product.hs_code}
            </Badge>
            <h3 className="font-bold text-[var(--text)] text-lg leading-tight">
              {product.name}
            </h3>
          </div>
          {isImport ? (
            <Badge className={difficultyColors[opportunity.difficulty_code] || difficultyColors.moderate}>
              {opportunity.difficulty_code
                ? t(`opportunities.substitutionAnalysis.difficulty.${opportunity.difficulty_code}`, {
                    defaultValue: opportunity.difficulty,
                  })
                : opportunity.difficulty}
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
          <div className="bg-[var(--afcfta-card2)] rounded-lg p-3">
            <p className="text-xs text-[var(--afcfta-muted)] mb-1">
              {isImport ? "Import actuel" : "Marché potentiel"}
            </p>
            <p className="font-bold text-lg text-[var(--text)]">
              {formatValue(isImport ? product?.import_value : opportunity.total_market_potential)}
            </p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] rounded-lg p-3">
            <p className="text-xs text-[var(--success)] mb-1">
              {isImport ? "Potentiel substitution" : "Avantage ZLECAf"}
            </p>
            <p className="font-bold text-lg text-[var(--success)]">
              {isImport ? formatValue(opportunity.substitution_potential) : (opportunity.afcfta_advantage || '-')}
            </p>
          </div>
        </div>

        {/* Feasibility — coefficient, binding constraint, barriers (both flows) */}
        <FeasibilityBlock
          feasibility={opportunity.substitution_feasibility}
          bindingConstraint={opportunity.binding_constraint}
        />

        {/* Real African production of this product (FAOSTAT / UNIDO / USGS) */}
        <VerifiedProductionBlock production={opportunity.verified_production} />

        {/* Current Source (for imports) */}
        {isImport && product?.current_source && (
          <div className="mb-4 flex items-center gap-2 text-sm text-[var(--afcfta-muted)]">
            <Globe className="h-4 w-4" />
            <span>Source actuelle: <strong className="text-[var(--text)]">{product.current_source}</strong></span>
          </div>
        )}

        {/* Average export price + market-match caveat (exports only) */}
        {!isImport && opportunity.exporter_avg_price_usd_per_tonne != null && (
          <div className="mb-3 flex items-center gap-2 text-sm text-[var(--afcfta-muted)]" data-testid="exporter-avg-price">
            <DollarSign className="h-4 w-4 text-[var(--afcfta-muted)]" />
            <span>
              {t('opportunities.substitutionAnalysis.averageExportPrice')} :{' '}
              <strong className="text-[var(--text)]">{fmtPerTonne(opportunity.exporter_avg_price_usd_per_tonne)}</strong>
            </span>
          </div>
        )}
        {!isImport && opportunity.market_match_level === 'hs4' && (
          <p className="mb-3 text-[11px] text-[var(--gold)] bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] rounded-md px-2.5 py-1.5" data-testid="market-match-caveat">
            {t('opportunities.substitutionAnalysis.marketsEstimatedAtHs4')}
          </p>
        )}

        {/* Suppliers/Markets */}
        <div>
          <p className="text-xs font-medium text-[var(--afcfta-muted)] uppercase tracking-wider mb-2">
            {isImport ? "Fournisseurs africains potentiels" : "Marchés cibles"}
          </p>
          <div className="space-y-2">
            {targets?.slice(0, 3).map((target, idx) => (
              <div key={idx} className="bg-[var(--afcfta-card2)] rounded-lg px-3 py-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-[var(--text)]">
                      {target.country_name}
                    </span>
                    {target.quality && (
                      <Badge variant="outline" className="text-[11px]">
                        {target.quality}
                      </Badge>
                    )}
                  </div>
                  <span className="text-sm font-semibold text-[var(--success)]">
                    {formatValue(isImport ? (target.export_value || target.production_capacity) : target.market_size)}
                  </span>
                </div>
                {/* Positionnement prix (export) : prix moyen payé par le marché
                    à ses fournisseurs actuels vs prix moyen d'export du pays. */}
                {!isImport && target.price_positioning && (
                  <div className="mt-1.5 flex items-center justify-between gap-2" data-testid="price-positioning">
                    <span className="text-[11px] text-[var(--afcfta-muted)]">
                      {t('opportunities.substitutionAnalysis.marketPays')}{' '}
                      <strong>{fmtPerTonne(target.price_positioning.market_avg_price_usd_per_tonne)}</strong>
                      {' · '}
                      {target.price_positioning.price_delta_pct > 0 ? '+' : ''}
                      {target.price_positioning.price_delta_pct}%
                    </span>
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${POSITIONING_CHIP[target.price_positioning.positioning] || POSITIONING_CHIP['aligné']}`}>
                      {t(`opportunities.substitutionAnalysis.positioning.${target.price_positioning.positioning}`, { defaultValue: target.price_positioning.positioning })}
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
  const { t } = useTranslation();
  if (!analysis || Object.keys(analysis).length === 0) return null;

  return (
    <Card className="shadow-lg border-[var(--afcfta-border)]" data-testid="analysis-summary">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-[var(--success)]" />
          {t('opportunities.substitutionAnalysis.enriched.analysisTitle')}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[var(--afcfta-card2)] rounded-lg p-3">
          <p className="text-xs text-[var(--afcfta-muted)] mb-1">{t('opportunities.substitutionAnalysis.enriched.avgCoef')}</p>
          <p className="text-2xl font-bold text-[var(--text)]">
            {analysis.avg_feasibility_coefficient != null
              ? `${Math.round(analysis.avg_feasibility_coefficient * 100)}%`
              : '—'}
          </p>
        </div>
        <div className="bg-[var(--afcfta-card2)] rounded-lg p-3">
          <p className="text-xs text-[var(--afcfta-muted)] mb-1.5">{t('opportunities.substitutionAnalysis.enriched.difficulties')}</p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(analysis.difficulty_distribution || {}).map(([code, count]) => (
              <span key={code} className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-[var(--afcfta-card)] border border-[var(--afcfta-border)] text-[var(--text)]">
                {t(`opportunities.substitutionAnalysis.difficulty.${code}`, { defaultValue: code })}
                {' · '}{count}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-[var(--afcfta-card2)] rounded-lg p-3">
          <p className="text-xs text-[var(--afcfta-muted)] mb-1.5">{t('opportunities.substitutionAnalysis.enriched.constraints')}</p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(analysis.binding_constraint_distribution || {}).map(([label, count]) => (
              <span key={label} className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-[var(--afcfta-card)] border border-[var(--afcfta-border)] text-[var(--text)]">
                {t(`opportunities.substitutionAnalysis.constraintLabels.${label}`, { defaultValue: label })} · {count}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] rounded-lg p-3">
          <p className="text-xs text-[var(--success)] mb-1">{t('opportunities.substitutionAnalysis.enriched.verifiedCount')}</p>
          <p className="text-2xl font-bold text-[var(--success)]">
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
const ProductHierarchyPanel = ({ hierarchy }) => {
  const { t } = useTranslation();
  const [openChapter, setOpenChapter] = useState(null);
  const [openHs4, setOpenHs4] = useState(null);
  if (!hierarchy?.length) return null;

  return (
    <Card className="shadow-lg" data-testid="product-hierarchy">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-bold">{t('opportunities.substitutionAnalysis.enriched.hierarchyTitle')}</CardTitle>
        <CardDescription className="text-xs">{t('opportunities.substitutionAnalysis.enriched.hierarchyHint')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {hierarchy.map((chapter) => {
          const isOpen = openChapter === chapter.chapter;
          return (
            <div key={chapter.chapter} className="border border-[var(--afcfta-border)] rounded-lg overflow-hidden">
              <button
                type="button"
                onClick={() => { setOpenChapter(isOpen ? null : chapter.chapter); setOpenHs4(null); }}
                className="w-full flex items-center gap-2 px-3 py-2.5 bg-[var(--afcfta-card2)] hover:bg-[var(--afcfta-card2)] transition-colors text-left"
                data-testid={`hierarchy-chapter-${chapter.chapter}`}
              >
                {isOpen ? <ChevronDown className="h-4 w-4 text-[var(--afcfta-muted)]" /> : <ChevronRight className="h-4 w-4 text-[var(--afcfta-muted)]" />}
                <Badge variant="outline" className="font-mono text-xs">SH {chapter.chapter}</Badge>
                <span className="font-medium text-sm text-[var(--text)] flex-1">{chapter.name}</span>
                <span className="text-xs text-[var(--afcfta-muted)]">{chapter.opportunity_count} {t('opportunities.substitutionAnalysis.enriched.opportunitiesCount')}</span>
                <span className="text-sm font-bold text-[var(--success)]">{formatValue(chapter.total_value)}</span>
              </button>
              {isOpen && (
                <div className="divide-y divide-[var(--afcfta-border)]">
                  {(chapter.hs4 || []).map((hs4) => {
                    const hs4Open = openHs4 === hs4.hs4_code;
                    return (
                      <div key={hs4.hs4_code}>
                        <button
                          type="button"
                          onClick={() => setOpenHs4(hs4Open ? null : hs4.hs4_code)}
                          className="w-full flex items-center gap-2 pl-9 pr-3 py-2 hover:bg-[var(--afcfta-card2)] transition-colors text-left"
                          data-testid={`hierarchy-hs4-${hs4.hs4_code}`}
                        >
                          {hs4Open ? <ChevronDown className="h-3.5 w-3.5 text-[var(--afcfta-muted)]" /> : <ChevronRight className="h-3.5 w-3.5 text-[var(--afcfta-muted)]" />}
                          <Badge variant="outline" className="font-mono text-[11px]">SH {hs4.hs4_code}</Badge>
                          <span className="text-sm text-[var(--text)] flex-1 truncate">{hs4.representative_name}</span>
                          <span className="text-xs font-semibold text-[var(--success)]">{formatValue(hs4.total_value)}</span>
                        </button>
                        {hs4Open && (
                          <div className="pl-16 pr-3 pb-2 space-y-1">
                            {(hs4.products || []).map((p) => (
                              <div key={p.hs_code} className="flex items-center gap-2 py-1 text-sm" data-testid={`hierarchy-hs6-${p.hs_code}`}>
                                <Badge className="font-mono text-[11px] bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] hover:bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))]">SH6 {p.hs_code}</Badge>
                                <span className="text-[var(--afcfta-muted)] flex-1 truncate">{p.name}</span>
                                {p.feasibility_coefficient != null && (
                                  <span className="text-[11px] text-[var(--afcfta-muted)]">{Math.round(p.feasibility_coefficient * 100)}%</span>
                                )}
                                <span className="text-xs font-semibold text-[var(--text)]">{formatValue(p.value)}</span>
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
      { label: t('opportunities.substitutionAnalysis.totalOpportunities'), value: String(summary.total_opportunities ?? 0), accent: 'gold' },
      {
        label: isImport ? t('opportunities.substitutionAnalysis.substitutableValue') : t('opportunities.substitutionAnalysis.marketPotential'),
        value: formatValue(isImport ? summary.total_substitutable_value : summary.total_market_potential),
        accent: 'green',
      },
    ];
    if (isImport && summary.total_imports_from_outside) {
      kpis.push({ label: t('opportunities.substitutionAnalysis.outsideAfrica'), value: formatValue(summary.total_imports_from_outside), accent: 'red' });
    }

    const sections = [];
    // Synthèse d'analyse (mêmes chiffres que le panneau à l'écran).
    const analysis = summary.analysis || {};
    if (Object.keys(analysis).length) {
      sections.push({
        title: t('opportunities.substitutionAnalysis.enriched.analysisTitle'),
        keyValues: [
          { label: t('opportunities.substitutionAnalysis.enriched.avgCoef'), value: analysis.avg_feasibility_coefficient != null ? `${Math.round(analysis.avg_feasibility_coefficient * 100)}%` : '—' },
          { label: t('opportunities.substitutionAnalysis.enriched.difficulties'), value: Object.entries(analysis.difficulty_distribution || {}).map(([k, v]) => `${t(`opportunities.substitutionAnalysis.difficulty.${k}`, { defaultValue: k })}: ${v}`).join(' · ') || '—' },
          { label: t('opportunities.substitutionAnalysis.enriched.constraints'), value: Object.entries(analysis.binding_constraint_distribution || {}).map(([k, v]) => `${k}: ${v}`).join(' · ') || '—' },
          { label: t('opportunities.substitutionAnalysis.enriched.verifiedCount'), value: String(analysis.verified_production_count ?? 0) },
        ],
      });
    }
    if (isImport) {
      sections.push({
        title: t('opportunities.substitutionAnalysis.importSubstitutionOpportunities'),
        table: {
          columns: [
            { key: 'hs', label: 'SH', width: 0.7 },
            { key: 'name', label: t('opportunities.substitutionAnalysis.product'), width: 2.6 },
            { key: 'imp', label: t('opportunities.substitutionAnalysis.currentImport'), align: 'right', width: 1.1 },
            { key: 'coef', label: t('opportunities.substitutionAnalysis.substitutability'), align: 'right', width: 1.0 },
            { key: 'pot', label: t('opportunities.substitutionAnalysis.potential'), align: 'right', width: 1.1 },
            { key: 'constraint', label: t('opportunities.substitutionAnalysis.constraint'), width: 1.2 },
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
        title: t('opportunities.substitutionAnalysis.exportOpportunitiesSh6Product'),
        table: {
          columns: [
            { key: 'hs', label: 'SH', width: 0.7 },
            { key: 'name', label: t('opportunities.substitutionAnalysis.product'), width: 2.4 },
            { key: 'price', label: t('opportunities.substitutionAnalysis.exportPrice'), align: 'right', width: 1.0 },
            { key: 'coef', label: t('opportunities.substitutionAnalysis.substitutability'), align: 'right', width: 1.0 },
            { key: 'pot', label: t('opportunities.substitutionAnalysis.potential'), align: 'right', width: 1.1 },
            { key: 'constraint', label: t('opportunities.substitutionAnalysis.constraint'), width: 1.2 },
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
            ? t(`opportunities.substitutionAnalysis.positioning.${m.price_positioning.positioning}`, { defaultValue: m.price_positioning.positioning })
            : '—',
        })),
      );
      if (marketRows.length) {
        sections.push({
          title: t('opportunities.substitutionAnalysis.targetMarketsPricePositioning'),
          table: {
            columns: [
              { key: 'product', label: t('opportunities.substitutionAnalysis.product'), width: 2.2 },
              { key: 'market', label: t('opportunities.substitutionAnalysis.market'), width: 1.2 },
              { key: 'size', label: t('opportunities.substitutionAnalysis.size'), align: 'right', width: 0.9 },
              { key: 'marketPrice', label: t('opportunities.substitutionAnalysis.marketPrice'), align: 'right', width: 1.0 },
              { key: 'delta', label: t('opportunities.substitutionAnalysis.delta'), align: 'right', width: 0.7 },
              { key: 'positioning', label: t('opportunities.substitutionAnalysis.position'), width: 1.0 },
            ],
            rows: marketRows,
          },
        });
      }
    }

    // Production africaine vérifiée (FAOSTAT / UNIDO / USGS) par produit.
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
        title: t('opportunities.substitutionAnalysis.enriched.verifiedTitle'),
        table: {
          columns: [
            { key: 'hs', label: 'SH', width: 0.7 },
            { key: 'commodity', label: t('opportunities.substitutionAnalysis.commodity'), width: 1.8 },
            { key: 'producers', label: t('opportunities.substitutionAnalysis.topRealProducers'), width: 3.0 },
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
        title: t('opportunities.substitutionAnalysis.enriched.hierarchyTitle'),
        table: {
          columns: [
            { key: 'chapter', label: t('opportunities.substitutionAnalysis.chapter'), width: 1.7 },
            { key: 'hs4', label: 'SH4', width: 0.6 },
            { key: 'hs6', label: 'SH6', width: 0.7 },
            { key: 'name', label: t('opportunities.substitutionAnalysis.product'), width: 2.4 },
            { key: 'value', label: t('opportunities.substitutionAnalysis.value'), align: 'right', width: 0.9 },
          ],
          rows: hierarchyRows,
        },
      });
    }

    return {
      badge: 'SUBSTITUTION',
      title: `${isImport ? t('opportunities.substitutionAnalysis.importSubstitution') : t('opportunities.substitutionAnalysis.exportOpportunities')} — ${countryName}`,
      subtitle: currentData.is_estimation
        ? t('opportunities.substitutionAnalysis.estimateStaticFallbackOec')
        : t('opportunities.substitutionAnalysis.realOecBaciFlows'),
      kpis,
      sections,
      source: currentData.data_source || 'OEC BACI',
      filename: opportunityPdfFilename('Substitution', `${selectedCountry}_${activeTab}`),
    };
  }, [currentData, activeTab, currentLang, countryName, opportunities, selectedCountry, t]);

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
          product_name: opp.imported_product?.name || t('opportunities.substitutionAnalysis.product'),
          importingCountry: countryName,
          substitution_potential_musd: (supplier.export_value || supplier.production_capacity || 0) / 1e6,
        }));
      } else {
        // Export mode: potential_markets[] → exportingCountry → product → potential_partner
        const markets = opp.target_markets || opp.potential_markets || [];
        if (!markets.length) return [];
        
        const productName = opp.exportable_product?.name || opp.export_product?.name || t('opportunities.substitutionAnalysis.product');
        
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
  }, [opportunities, activeTab, countryName, t('opportunities.substitutionAnalysis.product')]);

  return (
    <div className="space-y-6" data-testid="substitution-analysis">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <ArrowLeftRight className="h-8 w-8 text-[var(--success)]" />
          <h2 className="text-3xl font-black text-[var(--text)] uppercase tracking-tight">
            {t('opportunities.substitutionAnalysis.title')}
          </h2>
        </div>
        <p className="text-[var(--afcfta-muted)]">{t('opportunities.substitutionAnalysis.subtitle')}</p>
      </div>

      {/* Country Selection */}
      <Card className="shadow-lg">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-[var(--text)]">{t('opportunities.substitutionAnalysis.selectCountry')}</label>
              <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger className="w-full" data-testid="country-select-substitution">
                  <SelectValue placeholder={t('opportunities.substitutionAnalysis.selectCountry')} />
                </SelectTrigger>
                <SelectContent>
                  {countries.map((country) => (
                    <SelectItem key={country.iso3} value={country.iso3}>
                      <span className="flex items-center gap-2">
                        {country.name}
                        {country.has_trade_data && (
                          <Sparkles className="h-3 w-3 text-[var(--gold)]" />
                        )}
                        {!country.has_trade_data && (
                          <span className="text-xs text-[var(--afcfta-muted)]">(pas de données)</span>
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
              {t('opportunities.substitutionAnalysis.analyze')}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--success)]" />
          <span className="ml-3 text-[var(--afcfta-muted)]">{t('opportunities.substitutionAnalysis.loading')}</span>
        </div>
      )}

      {error && (
        <Card className="bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--danger)_30%,transparent)]">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-8 w-8 text-[var(--danger)] mx-auto mb-2" />
            <p className="text-[var(--danger)]">{error}</p>
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
                  {t('opportunities.substitutionAnalysis.importTab')}
                </TabsTrigger>
                <TabsTrigger value="export" className="flex items-center gap-2" data-testid="export-tab">
                  <TrendingUp className="h-4 w-4" />
                  {t('opportunities.substitutionAnalysis.exportTab')}
                </TabsTrigger>
              </TabsList>
              <OpportunityPdfExport getSpec={buildPdfSpec} language={currentLang} />
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title={t('opportunities.substitutionAnalysis.totalOpportunities')}
                value={currentData.summary?.total_opportunities || 0}
                icon={Target}
                color="emerald"
              />
              <StatCard
                title={t('opportunities.substitutionAnalysis.substitutableValue')}
                value={formatValue(
                  activeTab === 'import' 
                    ? currentData.summary?.total_substitutable_value 
                    : currentData.summary?.total_market_potential
                )}
                icon={DollarSign}
                color="blue"
              />
              <StatCard
                title={activeTab === 'import' ? t('opportunities.substitutionAnalysis.potentialSavings') : "Marchés cibles"}
                value={activeTab === 'import' 
                  ? `${currentData.summary?.potential_savings_percent?.toFixed(1) || 0}%`
                  : currentData.summary?.top_markets?.length || 0
                }
                icon={activeTab === 'import' ? Sparkles : MapPin}
                color="purple"
              />
              <StatCard
                title={t('opportunities.substitutionAnalysis.topSectors')}
                value={activeTab === 'import'
                  ? currentData.summary?.top_sectors?.length || 0
                  : currentData.summary?.top_products?.length || 0
                }
                icon={Package}
                color="orange"
              />
            </div>

            {/* Description */}
            <Card className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
              <CardContent className="py-4 px-6">
                <p className="text-sm text-[var(--success)]">
                  {activeTab === 'import' ? t('opportunities.substitutionAnalysis.importSubtitle') : t('opportunities.substitutionAnalysis.exportSubtitle')}
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
          <ProductHierarchyPanel hierarchy={currentData?.summary?.product_hierarchy} />

          {/* Top Sectors Chart — imports ET exports (le backend fournit
              top_sectors pour les deux flux ; dataKey aligné sur total_value,
              le champ réellement renvoyé — "value" traçait des barres vides) */}
          {currentData?.summary?.top_sectors?.length > 0 && (
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg font-bold">{t('opportunities.substitutionAnalysis.topSectors')}</CardTitle>
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
            />
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && !error && !currentData && (
        <Card className="bg-[var(--afcfta-card2)] border-[var(--afcfta-border)]">
          <CardContent className="py-16 text-center">
            <Globe className="h-16 w-16 text-[var(--text)] mx-auto mb-4" />
            <p className="text-[var(--afcfta-muted)]">{t('opportunities.substitutionAnalysis.noData')}</p>
          </CardContent>
        </Card>
      )}

      {/* Source Footer */}
      <div className="text-center">
        <p className="text-xs text-[var(--afcfta-muted)] italic">{t('opportunities.substitutionAnalysis.source')}</p>
      </div>
    </div>
  );
}
