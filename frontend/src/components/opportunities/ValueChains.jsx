/**
 * Value Chains Component
 * Analyzes African value chains and industrial transformation opportunities
 * NOW CONNECTED TO REAL AI DATA from Gemini API
 */
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  ResponsiveContainer, PieChart, Pie, Cell, Legend, Tooltip
} from 'recharts';
import {
  ArrowRight, TrendingUp, Loader2, ChevronRight, Layers, Sparkles, AlertCircle,
  Search, X, PackageSearch, BarChart3, Globe, Award, ShieldCheck
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const COLORS = ['#059669', '#0891b2', '#7c3aed', '#dc2626', '#ea580c', '#ca8a04', '#16a34a', '#2563eb', '#9333ea', '#e11d48'];

// Default Value Chain definitions (fallback)
const DEFAULT_VALUE_CHAINS = {
  coffee: {
    id: 'coffee',
    name: { fr: 'Café', en: 'Coffee' },
    icon: '☕',
    hsCode: '0901',
    color: '#7c3aed',
    stages: [
      { name: { fr: 'Production', en: 'Production' }, countries: ['ETH', 'UGA', 'KEN', 'TZA', 'RWA'], value: 2.8 },
      { name: { fr: 'Transformation', en: 'Processing' }, countries: ['ETH', 'KEN', 'CIV'], value: 1.2 },
      { name: { fr: 'Torréfaction', en: 'Roasting' }, countries: ['ZAF', 'EGY', 'MAR'], value: 0.8 },
      { name: { fr: 'Exportation', en: 'Export' }, countries: ['ETH', 'UGA', 'KEN'], value: 3.5 }
    ],
    topProducers: [
      { country: 'Éthiopie', iso3: 'ETH', production: 496000, share: 42 },
      { country: 'Ouganda', iso3: 'UGA', production: 288000, share: 24 },
      { country: 'Kenya', iso3: 'KEN', production: 42000, share: 4 },
      { country: 'Tanzanie', iso3: 'TZA', production: 55000, share: 5 },
      { country: 'Rwanda', iso3: 'RWA', production: 22000, share: 2 }
    ],
    intraAfricanPotential: 450,
    globalExports: 3200
  },
  cocoa: {
    id: 'cocoa',
    name: { fr: 'Cacao', en: 'Cocoa' },
    icon: '🍫',
    hsCode: '1801',
    color: '#dc2626',
    stages: [
      { name: { fr: 'Production', en: 'Production' }, countries: ['CIV', 'GHA', 'CMR', 'NGA'], value: 5.2 },
      { name: { fr: 'Fermentation', en: 'Fermentation' }, countries: ['CIV', 'GHA'], value: 4.8 },
      { name: { fr: 'Transformation', en: 'Processing' }, countries: ['CIV', 'GHA', 'NGA'], value: 2.1 },
      { name: { fr: 'Exportation', en: 'Export' }, countries: ['CIV', 'GHA', 'CMR'], value: 8.5 }
    ],
    topProducers: [
      { country: "Côte d'Ivoire", iso3: 'CIV', production: 2200000, share: 45 },
      { country: 'Ghana', iso3: 'GHA', production: 800000, share: 16 },
      { country: 'Cameroun', iso3: 'CMR', production: 290000, share: 6 },
      { country: 'Nigeria', iso3: 'NGA', production: 280000, share: 6 }
    ],
    intraAfricanPotential: 680,
    globalExports: 12500
  },
  cotton: {
    id: 'cotton',
    name: { fr: 'Coton & Textile', en: 'Cotton & Textile' },
    icon: '👕',
    hsCode: '5201',
    color: '#0891b2',
    stages: [
      { name: { fr: 'Culture', en: 'Cultivation' }, countries: ['MLI', 'BFA', 'BEN', 'TCD'], value: 1.8 },
      { name: { fr: 'Égrenage', en: 'Ginning' }, countries: ['MLI', 'BFA', 'CIV'], value: 1.5 },
      { name: { fr: 'Filature', en: 'Spinning' }, countries: ['EGY', 'MAR', 'TUN', 'ETH'], value: 2.2 },
      { name: { fr: 'Confection', en: 'Manufacturing' }, countries: ['ETH', 'KEN', 'MAR', 'MUS'], value: 3.8 }
    ],
    topProducers: [
      { country: 'Mali', iso3: 'MLI', production: 780000, share: 18 },
      { country: 'Burkina Faso', iso3: 'BFA', production: 600000, share: 14 },
      { country: 'Bénin', iso3: 'BEN', production: 550000, share: 13 },
      { country: "Côte d'Ivoire", iso3: 'CIV', production: 450000, share: 11 },
      { country: 'Égypte', iso3: 'EGY', production: 120000, share: 3 }
    ],
    intraAfricanPotential: 890,
    globalExports: 4200
  },
  petroleum: {
    id: 'petroleum',
    name: { fr: 'Pétrole & Gaz', en: 'Oil & Gas' },
    icon: '⛽',
    hsCode: '2709',
    color: '#ea580c',
    stages: [
      { name: { fr: 'Extraction', en: 'Extraction' }, countries: ['NGA', 'AGO', 'DZA', 'LBY', 'EGY'], value: 85 },
      { name: { fr: 'Raffinage', en: 'Refining' }, countries: ['NGA', 'ZAF', 'EGY', 'DZA'], value: 32 },
      { name: { fr: 'Pétrochimie', en: 'Petrochemicals' }, countries: ['ZAF', 'EGY', 'NGA'], value: 12 },
      { name: { fr: 'Distribution', en: 'Distribution' }, countries: ['ZAF', 'NGA', 'KEN'], value: 45 }
    ],
    topProducers: [
      { country: 'Nigeria', iso3: 'NGA', production: 1800000, share: 28 },
      { country: 'Angola', iso3: 'AGO', production: 1200000, share: 19 },
      { country: 'Algérie', iso3: 'DZA', production: 1000000, share: 16 },
      { country: 'Libye', iso3: 'LBY', production: 900000, share: 14 },
      { country: 'Égypte', iso3: 'EGY', production: 600000, share: 9 }
    ],
    intraAfricanPotential: 15000,
    globalExports: 95000
  },
  minerals: {
    id: 'minerals',
    name: { fr: 'Minéraux & Métaux', en: 'Minerals & Metals' },
    icon: '💎',
    hsCode: '71',
    color: '#059669',
    stages: [
      { name: { fr: 'Extraction', en: 'Mining' }, countries: ['ZAF', 'COD', 'ZMB', 'GHA', 'BWA'], value: 42 },
      { name: { fr: 'Concentration', en: 'Concentration' }, countries: ['ZAF', 'ZMB', 'COD'], value: 28 },
      { name: { fr: 'Raffinage', en: 'Refining' }, countries: ['ZAF', 'ZMB'], value: 18 },
      { name: { fr: 'Fabrication', en: 'Manufacturing' }, countries: ['ZAF', 'EGY', 'MAR'], value: 15 }
    ],
    topProducers: [
      { country: 'Afrique du Sud', iso3: 'ZAF', production: 25000, share: 35 },
      { country: 'RD Congo', iso3: 'COD', production: 18000, share: 25 },
      { country: 'Zambie', iso3: 'ZMB', production: 8000, share: 11 },
      { country: 'Ghana', iso3: 'GHA', production: 5000, share: 7 },
      { country: 'Botswana', iso3: 'BWA', production: 4500, share: 6 }
    ],
    intraAfricanPotential: 8500,
    globalExports: 65000
  },
  automotive: {
    id: 'automotive',
    name: { fr: 'Automobile', en: 'Automotive' },
    icon: '🚗',
    hsCode: '87',
    color: '#16a34a',
    stages: [
      { name: { fr: 'Composants', en: 'Components' }, countries: ['ZAF', 'MAR', 'EGY'], value: 8.5 },
      { name: { fr: 'Assemblage', en: 'Assembly' }, countries: ['ZAF', 'MAR', 'EGY', 'KEN'], value: 12.2 },
      { name: { fr: 'Distribution', en: 'Distribution' }, countries: ['ZAF', 'NGA', 'KEN', 'EGY'], value: 6.8 },
      { name: { fr: 'Services', en: 'Services' }, countries: ['ZAF', 'NGA', 'KEN'], value: 3.2 }
    ],
    topProducers: [
      { country: 'Afrique du Sud', iso3: 'ZAF', production: 450000, share: 58 },
      { country: 'Maroc', iso3: 'MAR', production: 180000, share: 23 },
      { country: 'Égypte', iso3: 'EGY', production: 85000, share: 11 },
      { country: 'Kenya', iso3: 'KEN', production: 12000, share: 2 }
    ],
    intraAfricanPotential: 4200,
    globalExports: 18500
  }
};

// Value Chain Card Component
const ValueChainCard = ({ chain, language, onClick, isSelected }) => {
  const name = chain.name[language] || chain.name.en || chain.name;
  
  return (
    <Card 
      className={`cursor-pointer transition-all hover:shadow-lg ${
        isSelected 
          ? 'ring-2 ring-emerald-500 shadow-lg' 
          : 'hover:border-slate-300'
      }`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{chain.icon}</span>
          <div className="flex-1">
            <h3 className="font-bold text-slate-900">{name}</h3>
            <p className="text-xs text-slate-500">HS {chain.hsCode || chain.hs_code}</p>
          </div>
          <ChevronRight className={`h-5 w-5 text-slate-400 transition-transform ${isSelected ? 'rotate-90' : ''}`} />
        </div>
        <div className="mt-3 flex gap-2">
          <Badge variant="outline" className="text-xs">
            {chain.topProducers?.length || chain.top_producers?.length || 0} pays producteurs
          </Badge>
          <Badge className="text-xs bg-emerald-100 text-emerald-700">
            ${chain.intraAfricanPotential || chain.intra_african_potential_musd || 0}M potentiel
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};

// Stage Flow Component
const StageFlow = ({ stages, language, color }) => {
  return (
    <div className="flex items-center justify-between overflow-x-auto pb-4">
      {stages.map((stage, index) => {
        const stageName = stage.name[language] || stage.name.en || stage.name;
        const stageCountries = stage.countries || [];
        const stageValue = stage.value || stage.value_billion || 0;
        
        return (
          <React.Fragment key={index}>
            <div className="flex flex-col items-center min-w-[120px]">
              <div 
                className="w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg"
                style={{ backgroundColor: color }}
              >
                {index + 1}
              </div>
              <p className="mt-2 text-sm font-medium text-slate-700 text-center">
                {stageName}
              </p>
              <p className="text-xs text-slate-500">${stageValue}B</p>
              <div className="flex flex-wrap gap-1 mt-1 justify-center max-w-[100px]">
                {stageCountries.slice(0, 3).map(iso => (
                  <Badge key={iso} variant="outline" className="text-[10px] px-1">
                    {iso}
                  </Badge>
                ))}
              </div>
            </div>
            {index < stages.length - 1 && (
              <ArrowRight className="h-6 w-6 text-slate-300 flex-shrink-0 mx-2" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

// HS6 Search Result Panel
const HS6SearchResult = ({ result, language, onClear }) => {
  const product = result.product || {};
  const summary = result.african_trade_summary || {};
  const exporters = result.top_african_exporters || [];
  const importers = result.top_african_importers || [];
  const capacities = result.production_capacities || [];
  const trends = result.market_share_trends || {};
  const specs = result.technical_specs || {};
  const prod = result.production_data || null;

  const fmtProd = (v, unit) => {
    if (v == null) return '—';
    if (unit === 'USD') return v >= 1e9 ? `$${(v / 1e9).toFixed(2)} Md` : `$${(v / 1e6).toFixed(1)} M`;
    if (v >= 1e6) return `${(v / 1e6).toFixed(2)} Mt`;
    if (v >= 1e3) return `${(v / 1e3).toFixed(1)} kt`;
    return `${Number(v).toLocaleString()} t`;
  };

  const score = trends.afcfta_opportunity_score || 0;
  const scoreColor = score >= 7 ? '#059669' : score >= 4 ? '#d97706' : '#dc2626';

  const trendIcon = (t) => t === 'growing' ? '↑' : t === 'declining' ? '↓' : '→';
  const trendColor = (t) => t === 'growing' ? 'text-emerald-600' : t === 'declining' ? 'text-red-500' : 'text-slate-500';

  const titles = {
    fr: {
      product: 'Produit analysé',
      exports: 'Export africain total',
      imports: 'Import africain total',
      intra: 'Commerce intra-africain',
      exporters: 'Principaux exportateurs africains',
      importers: 'Principaux importateurs africains',
      capacities: 'Capacités de production',
      score: 'Score opportunité ZLECAf',
      fastGrow: 'Croissance la plus rapide',
      dependency: 'Dépendance import principale',
      certs: 'Certifications requises',
      notes: 'Analyse',
      close: 'Fermer la recherche',
      substitutes: 'Produits liés',
    },
    en: {
      product: 'Analyzed product',
      exports: 'Total African exports',
      imports: 'Total African imports',
      intra: 'Intra-African trade',
      exporters: 'Top African exporters',
      importers: 'Top African importers',
      capacities: 'Production capacities',
      score: 'AfCFTA opportunity score',
      fastGrow: 'Fastest growing',
      dependency: 'Main import dependency',
      certs: 'Required certifications',
      notes: 'Analysis',
      close: 'Close search',
      substitutes: 'Related products',
    },
  };
  const t = titles[language] || titles.fr;

  return (
    <div className="border-2 border-emerald-400 rounded-2xl overflow-hidden shadow-xl bg-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-700 to-emerald-500 px-6 py-4 flex items-center justify-between text-white">
        <div className="flex items-center gap-3">
          <PackageSearch className="h-6 w-6" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-200">{t.product}</p>
            <h3 className="font-black text-lg leading-tight">
              {product.hs6Name || product.description || `HS ${product.hs6Code}`}
            </h3>
            <p className="text-xs text-emerald-200 mt-0.5">
              HS {product.hs6Code} · {product.hs4Name} · {product.hs2Name}
            </p>
          </div>
        </div>
        <button
          onClick={onClear}
          className="p-2 rounded-full hover:bg-white/20 transition-colors"
          title={t.close}
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="p-6 space-y-6">
        {/* Trade summary stats */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: t.exports, value: summary.total_african_exports_musd, icon: Globe, color: 'text-emerald-600' },
            { label: t.imports, value: summary.total_african_imports_musd, icon: BarChart3, color: 'text-blue-600' },
            { label: t.intra, value: summary.intra_african_trade_musd, icon: ArrowRight, color: 'text-purple-600' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="text-center p-3 bg-slate-50 rounded-xl border border-slate-200">
              <Icon className={`h-5 w-5 mx-auto mb-1 ${color}`} />
              <p className="text-xs text-slate-500 leading-tight">{label}</p>
              <p className="font-black text-lg text-slate-800">${(value || 0).toLocaleString()}M</p>
              <p className="text-xs text-slate-400">{summary.year || 2023}</p>
            </div>
          ))}
        </div>

        {/* AfCFTA score */}
        {score > 0 && (
          <div className="flex items-center gap-4 p-3 rounded-xl border" style={{ borderColor: scoreColor + '44', backgroundColor: scoreColor + '11' }}>
            <div
              className="w-14 h-14 rounded-full flex items-center justify-center text-white font-black text-xl flex-shrink-0"
              style={{ backgroundColor: scoreColor }}
            >
              {score.toFixed(1)}
            </div>
            <div className="flex-1">
              <p className="font-bold text-slate-800">{t.score} <span className="font-normal text-slate-500">/ 10</span></p>
              {trends.notes && <p className="text-sm text-slate-600 mt-0.5">{trends.notes}</p>}
              <div className="flex flex-wrap gap-3 mt-1 text-xs">
                {trends.fastest_growing_exporter && (
                  <span className="text-emerald-700">↑ {trends.fastest_growing_exporter}</span>
                )}
                {trends.largest_import_dependency && (
                  <span className="text-amber-700">⚠ {trends.largest_import_dependency}</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Exporters & Importers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {exporters.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">{t.exporters}</h4>
              <div className="space-y-2">
                {exporters.slice(0, 5).map((exp, i) => (
                  <div key={exp.iso3 || i} className="flex items-center gap-2">
                    <span className="text-xs font-black text-slate-300 w-4">{i + 1}</span>
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-0.5">
                        <span className="text-sm font-medium text-slate-700">{exp.country}</span>
                        <span className={`text-xs font-semibold ${trendColor(exp.trend)}`}>
                          {trendIcon(exp.trend)} {exp.share_percent || 0}%
                        </span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${Math.min(exp.share_percent || 0, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {importers.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">{t.importers}</h4>
              <div className="space-y-2">
                {importers.slice(0, 5).map((imp, i) => (
                  <div key={imp.iso3 || i} className="flex items-center gap-2">
                    <span className="text-xs font-black text-slate-300 w-4">{i + 1}</span>
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-0.5">
                        <span className="text-sm font-medium text-slate-700">{imp.country}</span>
                        <span className="text-xs text-slate-500">{imp.share_percent || 0}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-400 rounded-full"
                          style={{ width: `${Math.min(imp.share_percent || 0, 100)}%` }}
                        />
                      </div>
                      {imp.main_source && (
                        <p className="text-[10px] text-slate-400">Source: {imp.main_source}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Real production data (FAO / USGS / UNIDO) */}
        {prod && prod.top_producers?.length > 0 && (
          <div className="border border-emerald-300 bg-emerald-50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                <BarChart3 className="h-3 w-3" />
                {language === 'fr' ? 'Production réelle' : 'Real production'} · {prod.commodity}
              </h4>
              <Badge className="text-[10px] bg-emerald-700 text-white">
                {prod.source?.institution} {prod.year}
              </Badge>
            </div>
            <div className="space-y-1.5">
              {prod.top_producers.slice(0, 6).map((p, i) => (
                <div key={p.country_iso3 || i} className="flex items-center gap-2">
                  <span className="text-xs font-black text-emerald-300 w-4">{i + 1}</span>
                  <span className="flex-1 text-sm text-slate-700 font-medium">{p.country_name}</span>
                  <span className="text-xs text-slate-500">{fmtProd(p.value, prod.unit)}</span>
                  <span className="text-xs font-bold text-emerald-700 w-12 text-right">{p.share_pct}%</span>
                </div>
              ))}
            </div>
            <p className="text-[10px] text-emerald-600 mt-2 italic">
              {prod.source?.dataset} · {language === 'fr' ? 'Total Afrique' : 'Africa total'}: {fmtProd(prod.continental_total, prod.unit)}
            </p>
          </div>
        )}

        {/* Production capacities */}
        {capacities.length > 0 && (
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">{t.capacities}</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {capacities.slice(0, 6).map((cap, i) => (
                <div key={cap.iso3 || i} className="p-2 bg-slate-50 rounded-lg border border-slate-200">
                  <p className="font-semibold text-sm text-slate-800">{cap.country} <span className="text-slate-400 text-xs">({cap.iso3})</span></p>
                  <p className="text-xs text-slate-600 mt-0.5">{cap.capacity}</p>
                  {cap.notes && <p className="text-[10px] text-slate-400 mt-0.5">{cap.notes}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Certifications */}
        {(specs.key_certifications?.length > 0 || specs.quality_standards?.length > 0) && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl">
            <h4 className="text-xs font-bold text-blue-700 uppercase tracking-wider flex items-center gap-1 mb-2">
              <Award className="h-3 w-3" /> {t.certs}
            </h4>
            <div className="flex flex-wrap gap-2">
              {[...(specs.key_certifications || []), ...(specs.quality_standards || [])].map((c, i) => (
                <Badge key={i} className="text-xs bg-blue-100 text-blue-700 border-blue-300">{c}</Badge>
              ))}
            </div>
            {specs.phytosanitary_requirements && (
              <p className="text-xs text-blue-600 mt-2 flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 flex-shrink-0" /> {specs.phytosanitary_requirements}
              </p>
            )}
          </div>
        )}

        {/* Related products */}
        {(result.substitutes || []).length > 0 && (
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{t.substitutes}</h4>
            <div className="flex flex-wrap gap-2">
              {(result.substitutes || []).map((s, i) => (
                <Badge key={i} variant="outline" className="text-xs">
                  HS {s.hs6Code} · {s.name}
                  <span className="ml-1 text-slate-400">({s.relationship})</span>
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Sources */}
        {(result.sources || []).length > 0 && (
          <p className="text-xs text-slate-400 italic">
            Sources: {result.sources.join(' · ')}
          </p>
        )}
      </div>
    </div>
  );
};

export default function ValueChains({ language = 'fr' }) {
  const { t } = useTranslation();
  const [selectedChain, setSelectedChain] = useState('coffee');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [valueChains, setValueChains] = useState(DEFAULT_VALUE_CHAINS);
  const [isAiGenerated, setIsAiGenerated] = useState(false);

  // HS6 search state
  const [hsQuery, setHsQuery] = useState('');
  const [hsSearchResult, setHsSearchResult] = useState(null);
  const [hsSearchLoading, setHsSearchLoading] = useState(false);
  const [hsSearchError, setHsSearchError] = useState(null);

  // Fetch value chains data from AI API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const aiResponse = await axios.get(`${API}/ai/value-chains?lang=${language}`)
          .catch(err => {
            console.warn('AI value chains not available, using defaults:', err.message);
            return { data: null };
          });

        if (aiResponse.data && aiResponse.data.value_chains && aiResponse.data.value_chains.length > 0) {
          setIsAiGenerated(true);
          
          // Convert AI response to our format
          const chainsMap = {};
          aiResponse.data.value_chains.forEach(vc => {
            const id = vc.id || vc.name?.en?.toLowerCase().replace(/[^a-z]/g, '') || 'unknown';
            chainsMap[id] = {
              id: id,
              name: vc.name || { fr: id, en: id },
              icon: vc.icon || '📦',
              hsCode: vc.hs_code || vc.hsCode || '',
              color: vc.color || '#059669',
              stages: (vc.stages || []).map(s => ({
                name: s.name || { fr: 'Étape', en: 'Stage' },
                countries: s.countries || [],
                value: s.value_billion || s.value || 0
              })),
              topProducers: (vc.top_producers || []).map(p => ({
                country: p.country,
                iso3: p.iso3,
                production: p.production_tonnes || p.production || 0,
                share: p.market_share_percent || p.share || 0
              })),
              intraAfricanPotential: vc.intra_african_potential_musd || vc.intraAfricanPotential || 0,
              globalExports: vc.global_exports_musd || vc.globalExports || 0,
              afcftaOpportunities: vc.afcfta_opportunities || []
            };
          });
          
          // Merge with defaults to ensure all chains exist
          setValueChains({ ...DEFAULT_VALUE_CHAINS, ...chainsMap });
        } else {
          setValueChains(DEFAULT_VALUE_CHAINS);
        }
        
        setError(null);
      } catch (err) {
        console.error('Error fetching value chains:', err);
        setValueChains(DEFAULT_VALUE_CHAINS);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [language]);

  const handleHsSearch = async (e) => {
    e.preventDefault();
    const code = hsQuery.trim().replace(/\D/g, '');
    if (!code || ![2, 4, 6].includes(code.length)) {
      setHsSearchError(language === 'fr'
        ? 'Entrez un code SH valide (2, 4 ou 6 chiffres)'
        : 'Enter a valid HS code (2, 4 or 6 digits)');
      return;
    }
    setHsSearchError(null);
    setHsSearchResult(null);
    setHsSearchLoading(true);
    try {
      // Fetch AI analysis + real production data (FAO/USGS) in parallel
      const [aiResp, prodResp] = await Promise.all([
        axios.get(`${API}/ai/product/${code}?lang=${language}`),
        axios.get(`${API}/production/capacity/${code}`).catch(() => ({ data: null })),
      ]);
      const merged = { ...aiResp.data };
      if (prodResp.data && prodResp.data.available) {
        merged.production_data = prodResp.data;
      }
      setHsSearchResult(merged);
    } catch (err) {
      setHsSearchError(
        err.response?.data?.detail ||
        (language === 'fr' ? 'Erreur lors de l\'analyse du produit' : 'Error analyzing product')
      );
    } finally {
      setHsSearchLoading(false);
    }
  };

  const texts = {
    fr: {
      title: "Chaînes de Valeur Africaines",
      subtitle: "Analyse des opportunités de transformation industrielle et d'intégration régionale",
      selectChain: "Sélectionnez une chaîne de valeur",
      stagesTitle: "Étapes de la Chaîne de Valeur",
      topProducers: "Principaux Producteurs",
      valueAddedPotential: "Potentiel de Valeur Ajoutée",
      intraAfricanTrade: "Commerce Intra-Africain",
      globalExports: "Exportations Mondiales",
      production: "Production (tonnes)",
      share: "Part (%)",
      opportunities: "Opportunités ZLECAf",
      aiGenerated: "Données enrichies par IA",
      source: "Sources: FAOSTAT 2024, UNCTAD 2024, ITC Trade Map, Données sectorielles",
      searchPlaceholder: "Entrez un code SH (ex: 090111, 1801, 72)",
      searchBtn: "Analyser",
      searchTitle: "Recherche par code SH",
      searchSub: "Analysez n'importe quel produit : chaîne de valeur, opportunités ZLECAf, marchés africains"
    },
    en: {
      title: "African Value Chains",
      subtitle: "Analysis of industrial transformation and regional integration opportunities",
      selectChain: "Select a value chain",
      stagesTitle: "Value Chain Stages",
      topProducers: "Top Producers",
      valueAddedPotential: "Value Added Potential",
      intraAfricanTrade: "Intra-African Trade",
      globalExports: "Global Exports",
      production: "Production (tonnes)",
      share: "Share (%)",
      opportunities: "AfCFTA Opportunities",
      aiGenerated: "AI-enhanced data",
      source: "Sources: FAOSTAT 2024, UNCTAD 2024, ITC Trade Map, Sector data",
      searchPlaceholder: "Enter HS code (e.g. 090111, 1801, 72)",
      searchBtn: "Analyze",
      searchTitle: "Search by HS code",
      searchSub: "Analyze any product: value chain, AfCFTA opportunities, African markets"
    }
  };

  const txt = texts[language] || texts.fr;
  const chain = valueChains[selectedChain];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
        <span className="ml-3 text-slate-600">Chargement des chaînes de valeur...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="value-chains">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <Layers className="h-8 w-8 text-emerald-600" />
          <h2 className="text-3xl font-black text-slate-900 uppercase tracking-tight">
            {txt.title}
          </h2>
        </div>
        <p className="text-slate-500">{txt.subtitle}</p>
        {isAiGenerated && (
          <Badge className="mt-2 bg-purple-100 text-purple-700 border-purple-200">
            <Sparkles className="h-3 w-3 mr-1" />
            {txt.aiGenerated}
          </Badge>
        )}
      </div>

      {/* HS6 Code Search */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center gap-2 mb-1">
          <Search className="h-5 w-5 text-emerald-400" />
          <h3 className="font-bold text-white">{txt.searchTitle}</h3>
        </div>
        <p className="text-slate-400 text-sm mb-4">{txt.searchSub}</p>
        <form onSubmit={handleHsSearch} className="flex gap-2">
          <input
            type="text"
            value={hsQuery}
            onChange={(e) => { setHsQuery(e.target.value); setHsSearchError(null); }}
            placeholder={txt.searchPlaceholder}
            maxLength={8}
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-700 border border-slate-600 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm font-mono tracking-widest"
          />
          <button
            type="submit"
            disabled={hsSearchLoading}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold rounded-xl transition-colors flex items-center gap-2 text-sm"
          >
            {hsSearchLoading
              ? <Loader2 className="h-4 w-4 animate-spin" />
              : <Search className="h-4 w-4" />
            }
            {txt.searchBtn}
          </button>
        </form>
        {hsSearchError && (
          <p className="mt-2 text-red-400 text-xs flex items-center gap-1">
            <AlertCircle className="h-3 w-3" /> {hsSearchError}
          </p>
        )}
        {/* Preset shortcut chips */}
        <div className="flex flex-wrap gap-2 mt-3">
          {[
            { code: '090111', label: '090111 · Café Arabica' },
            { code: '180100', label: '180100 · Cacao' },
            { code: '520100', label: '520100 · Coton' },
            { code: '270900', label: '270900 · Pétrole brut' },
            { code: '720100', label: '720100 · Fer & Acier' },
            { code: '870322', label: '870322 · Véhicules' },
          ].map(({ code, label }) => (
            <button
              key={code}
              type="button"
              onClick={() => { setHsQuery(code); setHsSearchError(null); setHsSearchResult(null); }}
              className="text-xs px-2.5 py-1 rounded-full bg-slate-700 hover:bg-emerald-700 text-slate-300 hover:text-white transition-colors font-mono"
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* HS6 Search Result */}
      {hsSearchLoading && (
        <div className="flex items-center justify-center py-12 gap-3 text-slate-500">
          <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
          <span>{language === 'fr' ? 'Analyse en cours...' : 'Analyzing...'}</span>
        </div>
      )}
      {hsSearchResult && !hsSearchLoading && (
        <HS6SearchResult
          result={hsSearchResult}
          language={language}
          onClear={() => { setHsSearchResult(null); setHsQuery(''); }}
        />
      )}

      {/* Value Chain Selection Grid */}
      <div>
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
          {txt.selectChain}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.values(valueChains).map((vc) => (
            <ValueChainCard
              key={vc.id}
              chain={vc}
              language={language}
              isSelected={selectedChain === vc.id}
              onClick={() => setSelectedChain(vc.id)}
            />
          ))}
        </div>
      </div>

      {/* Selected Chain Details */}
      {chain && (
        <Card className="shadow-xl border-slate-200 overflow-hidden">
          <CardHeader 
            className="text-white"
            style={{ background: `linear-gradient(135deg, ${chain.color}, ${chain.color}dd)` }}
          >
            <div className="flex items-center gap-4">
              <span className="text-5xl">{chain.icon}</span>
              <div>
                <CardTitle className="text-2xl">
                  {chain.name[language] || chain.name.en || chain.name}
                </CardTitle>
                <CardDescription className="text-white/80">
                  Code HS: {chain.hsCode || chain.hs_code} | Potentiel intra-africain: ${chain.intraAfricanPotential || chain.intra_african_potential_musd}M
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="p-6 space-y-8">
            {/* Stages Flow */}
            <div>
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
                {txt.stagesTitle}
              </h3>
              <StageFlow stages={chain.stages || []} language={language} color={chain.color} />
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Producers */}
              <div>
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
                  {txt.topProducers}
                </h3>
                <div className="space-y-3">
                  {(chain.topProducers || chain.top_producers || []).map((producer, idx) => (
                    <div key={producer.iso3} className="flex items-center gap-3">
                      <span className="font-black text-slate-300 w-6">{idx + 1}</span>
                      <div className="flex-1">
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-medium text-slate-700">{producer.country}</span>
                          <span className="text-sm text-slate-500">{producer.share || producer.market_share_percent}%</span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all"
                            style={{ 
                              width: `${producer.share || producer.market_share_percent}%`,
                              backgroundColor: chain.color 
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Trade Potential Chart */}
              <div>
                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
                  {txt.valueAddedPotential}
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: txt.intraAfricanTrade, value: chain.intraAfricanPotential || chain.intra_african_potential_musd || 0 },
                        { name: txt.globalExports, value: (chain.globalExports || chain.global_exports_musd || 0) - (chain.intraAfricanPotential || chain.intra_african_potential_musd || 0) }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      <Cell fill={chain.color} />
                      <Cell fill="#e2e8f0" />
                    </Pie>
                    <Tooltip formatter={(v) => `$${v}M`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
                <div className="text-center mt-4">
                  <Badge className="text-sm" style={{ backgroundColor: chain.color }}>
                    {(((chain.intraAfricanPotential || chain.intra_african_potential_musd || 0) / (chain.globalExports || chain.global_exports_musd || 1)) * 100).toFixed(1)}% du marché potentiel
                  </Badge>
                </div>
              </div>
            </div>

            {/* AfCFTA Opportunities */}
            <Card className="bg-emerald-50 border-emerald-200">
              <CardContent className="p-4">
                <h4 className="font-bold text-emerald-800 flex items-center gap-2 mb-2">
                  <TrendingUp className="h-5 w-5" />
                  {txt.opportunities}
                </h4>
                <ul className="text-sm text-emerald-700 space-y-1">
                  {(chain.afcftaOpportunities && chain.afcftaOpportunities.length > 0) ? (
                    chain.afcftaOpportunities.map((opp, idx) => (
                      <li key={idx}>• {opp}</li>
                    ))
                  ) : (
                    <>
                      <li>• Réduction des tarifs douaniers jusqu'à 90% d'ici 2034</li>
                      <li>• Règles d'origine favorisant la transformation locale</li>
                      <li>• Harmonisation des normes et standards</li>
                      <li>• Facilitation du commerce et réduction des délais aux frontières</li>
                    </>
                  )}
                </ul>
              </CardContent>
            </Card>
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
