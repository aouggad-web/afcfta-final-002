/**
 * Statistics Tab - Refactored with Sub-tabs
 * Includes: OEC Stats, Trade Products, Comparisons, Multi-Country Comparison
 */
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Cell } from 'recharts';
import { BarChart3, Scale, Globe, TrendingUp, Package, ArrowUpRight, ArrowDownRight, Search, LayoutGrid, Map as MapIcon, Award, Link2, Percent } from 'lucide-react';

// Sub-components
import StatisticsZaubaStyle from '../StatisticsZaubaStyle';
import TradeComparison from '../TradeComparison';
import TradeProductsTable from '../TradeProductsTable';
import OECTradeStats from '../stats/OECTradeStats';
import MultiCountryComparison from './MultiCountryComparison';
import CountryHS6History from './CountryHS6History';
import ProductHSSearch from '../common/ProductHSSearch';
import CountryTradeSeries from './CountryTradeSeries';
import ProductTreemap from './ProductTreemap';
import AfricaTradeMap from './AfricaTradeMap';
import RcaAnalysis from './RcaAnalysis';
import TradeComplementarity from './TradeComplementarity';
import PreferenceMargin from './PreferenceMargin';
import { PDFExportButton } from '../common/ExportTools';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

/* ── Custom tooltip pour les barres ──────────────────────────── */
const AfricaTooltip = ({ active, payload, label, unit }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="stats-tooltip" style={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, padding: '10px 14px', fontSize: '0.8rem' }}>
      <p style={{ color: '#EAE0D0', fontWeight: 700, marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, margin: 0 }}>
          {p.name}: <strong>{`$${(p.value / 1e9).toFixed(1)}B`}</strong>
        </p>
      ))}
      {unit && <p style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.68rem', marginTop: 4 }}>{unit}</p>}
    </div>
  );
};

export default function StatisticsTab({ language = 'fr' }) {
  const { t } = useTranslation();
  const [statistics, setStatistics] = useState(null);
  const [activeSubTab, setActiveSubTab] = useState('overview');
  const contentRef = useRef(null);

  const texts = {
    fr: {
      title: "Statistiques Commerciales",
      subtitle: "Données et analyses du commerce africain — ZLECAf 2024",
      overview: "Vue d'ensemble",
      products: "Produits",
      treemap: "Cartographie",
      map: "Carte",
      rca: "RCA",
      complementarity: "Complémentarité",
      preference: "Préférences ZLECAf",
      trends: "Tendances",
      parPays: "Par Pays & SH6",
      comparison: "Comparaison Pays",
      topExporters: "Top 10 Exportateurs",
      topImporters: "Top 10 Importateurs",
      exports: "Exportations 2024",
      imports: "Importations 2024",
      exportsEvolution: "Volume des exportations (Milliards USD)",
      importsVolume: "Volume des importations (Milliards USD)"
    },
    en: {
      title: "Trade Statistics",
      subtitle: "African trade data and analysis — AfCFTA 2024",
      overview: "Overview",
      products: "Products",
      treemap: "Product Map",
      map: "Map",
      rca: "RCA",
      complementarity: "Complementarity",
      preference: "AfCFTA Preferences",
      trends: "Trends",
      parPays: "By Country & HS6",
      comparison: "Country Comparison",
      topExporters: "Top 10 Exporters",
      topImporters: "Top 10 Importers",
      exports: "Exports 2024",
      imports: "Imports 2024",
      exportsEvolution: "Export volume (Billion USD)",
      importsVolume: "Import volume (Billion USD)"
    }
  };

  const txt = texts[language] || texts.fr;

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API}/statistics`);
      setStatistics(response.data);
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  };

  const tabItems = [
    { value: 'overview',   icon: <Globe className="h-4 w-4"     />, label: txt.overview   },
    { value: 'products',   icon: <Package className="h-4 w-4"   />, label: txt.products   },
    { value: 'treemap',    icon: <LayoutGrid className="h-4 w-4"/>, label: txt.treemap    },
    { value: 'map',        icon: <MapIcon className="h-4 w-4"   />, label: txt.map        },
    { value: 'rca',        icon: <Award className="h-4 w-4"     />, label: txt.rca        },
    { value: 'complementarity', icon: <Link2 className="h-4 w-4" />, label: txt.complementarity },
    { value: 'preference', icon: <Percent className="h-4 w-4"   />, label: txt.preference  },
    { value: 'trends',     icon: <TrendingUp className="h-4 w-4"/>, label: txt.trends     },
    { value: 'par-pays',   icon: <Search className="h-4 w-4"   />, label: txt.parPays   },
    { value: 'comparison', icon: <Scale className="h-4 w-4"     />, label: txt.comparison },
  ];

  return (
    <div className="space-y-6" data-testid="statistics-tab">
      {/* ── Hero Header ──────────────────────────────────────── */}
      <div className="stats-hero">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="stats-hero-title flex items-center gap-2">
              <BarChart3 className="h-7 w-7" style={{ color: '#D4891A' }} />
              {txt.title}
            </h2>
            <p className="stats-hero-subtitle">{txt.subtitle}</p>
            <div className="stats-kente-bar" style={{ width: 200, marginTop: 12 }} />
          </div>
          <PDFExportButton
            targetRef={contentRef}
            filename="statistics"
            title={txt.title}
            language={language}
          />
        </div>
      </div>

      {/* ── Sub-tabs Navigation ─────────────────────────────── */}
      <Tabs value={activeSubTab} onValueChange={setActiveSubTab} className="space-y-6">
        <TabsList
          className="flex flex-wrap h-auto w-full justify-start gap-1 p-1 rounded-xl"
          style={{
            background: 'rgba(18,24,32,0.85)',
            border: '1px solid rgba(212,137,26,0.18)',
          }}
        >
          {tabItems.map(tab => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              data-testid={`stats-${tab.value}-tab`}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                color: activeSubTab === tab.value ? '#EAE0D0' : 'rgba(142,155,174,0.7)',
                background: activeSubTab === tab.value
                  ? 'linear-gradient(135deg,rgba(200,83,26,0.85),rgba(160,60,18,0.9))'
                  : 'transparent',
                boxShadow: activeSubTab === tab.value ? '0 2px 8px rgba(200,83,26,0.35)' : 'none',
              }}
            >
              {tab.icon}
              <span className="hidden sm:inline">{tab.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        <div ref={contentRef}>
          {/* ── Overview Tab ─────────────────────────────────── */}
          <TabsContent value="overview" className="space-y-8">
            <OECTradeStats language={language} />
            <StatisticsZaubaStyle language={language} />

            {/* Top Exporters / Importers Charts */}
            {statistics && statistics.top_exporters_2024 && statistics.top_importers_2024 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Top Exporters */}
                <div className="stats-chart-card" data-testid="top-exporters-chart">
                  <div className="stats-chart-header green">
                    <div className="stats-chart-title green">
                      <TrendingUp className="h-5 w-5" />
                      {txt.topExporters}
                    </div>
                    <div className="stats-chart-subtitle">{txt.exportsEvolution}</div>
                  </div>
                  <div style={{ padding: '16px 8px' }}>
                    <ResponsiveContainer width="100%" height={320}>
                      <BarChart
                        data={statistics.top_exporters_2024?.slice(0, 10)}
                        layout="vertical"
                        margin={{ top: 4, right: 36, left: 80, bottom: 4 }}
                      >
                        <defs>
                          <linearGradient id="gradExport" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="#1A7A4A" />
                            <stop offset="100%" stopColor="#34d399" />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.06)" />
                        <XAxis
                          type="number"
                          tickFormatter={(v) => `$${(v / 1e9).toFixed(0)}B`}
                          tick={{ fontSize: 10, fill: 'rgba(142,155,174,0.8)' }}
                          axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                          tickLine={false}
                        />
                        <YAxis
                          dataKey="name"
                          type="category"
                          tick={{ fontSize: 11, fill: '#EAE0D0' }}
                          width={78}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip content={<AfricaTooltip unit={txt.exportsEvolution} />} />
                        <Bar
                          dataKey="exports_2024"
                          fill="url(#gradExport)"
                          radius={[0, 6, 6, 0]}
                          barSize={16}
                          name={txt.exports}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Top Importers */}
                <div className="stats-chart-card" data-testid="top-importers-chart">
                  <div className="stats-chart-header blue">
                    <div className="stats-chart-title blue">
                      <TrendingUp className="h-5 w-5 rotate-180" />
                      {txt.topImporters}
                    </div>
                    <div className="stats-chart-subtitle">{txt.importsVolume}</div>
                  </div>
                  <div style={{ padding: '16px 8px' }}>
                    <ResponsiveContainer width="100%" height={320}>
                      <BarChart
                        data={statistics.top_importers_2024?.slice(0, 10)}
                        layout="vertical"
                        margin={{ top: 4, right: 36, left: 80, bottom: 4 }}
                      >
                        <defs>
                          <linearGradient id="gradImport" x1="0" y1="0" x2="1" y2="0">
                            <stop offset="0%" stopColor="#1A6B8A" />
                            <stop offset="100%" stopColor="#38bdf8" />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.06)" />
                        <XAxis
                          type="number"
                          tickFormatter={(v) => `$${(v / 1e9).toFixed(0)}B`}
                          tick={{ fontSize: 10, fill: 'rgba(142,155,174,0.8)' }}
                          axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                          tickLine={false}
                        />
                        <YAxis
                          dataKey="name"
                          type="category"
                          tick={{ fontSize: 11, fill: '#EAE0D0' }}
                          width={78}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip content={<AfricaTooltip unit={txt.importsVolume} />} />
                        <Bar
                          dataKey="imports_2024"
                          fill="url(#gradImport)"
                          radius={[0, 6, 6, 0]}
                          barSize={16}
                          name={txt.imports}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}
          </TabsContent>

          {/* ── Products Tab ──────────────────────────────────── */}
          <TabsContent value="products" className="space-y-8">
            <TradeProductsTable language={language} />
          </TabsContent>

          {/* ── Treemap Tab ───────────────────────────────────── */}
          <TabsContent value="treemap" className="space-y-8">
            <ProductTreemap language={language} />
          </TabsContent>

          {/* ── Map Tab ───────────────────────────────────────── */}
          <TabsContent value="map" className="space-y-8">
            <AfricaTradeMap language={language} />
          </TabsContent>

          {/* ── RCA Tab ───────────────────────────────────────── */}
          <TabsContent value="rca" className="space-y-8">
            <RcaAnalysis language={language} />
          </TabsContent>

          {/* ── Complementarity Tab ───────────────────────────── */}
          <TabsContent value="complementarity" className="space-y-8">
            <TradeComplementarity language={language} />
          </TabsContent>

          {/* ── Preference Margin Tab ─────────────────────────── */}
          <TabsContent value="preference" className="space-y-8">
            <PreferenceMargin language={language} />
          </TabsContent>

          {/* ── Trends Tab ────────────────────────────────────── */}
          <TabsContent value="trends" className="space-y-8">
            <CountryTradeSeries language={language} />
            <TradeComparison language={language} />
          </TabsContent>

          {/* ── Par Pays & SH6 Tab ───────────────────────────── */}
          <TabsContent value="par-pays" className="space-y-8">
            {/* Aide à la saisie : retrouver un code SH depuis le nom courant du
                produit (index OMD) pour les utilisateurs sans bagage douanier. */}
            <div className="stats-chart-card" style={{ padding: 16 }}>
              <div className="stats-chart-title" style={{ marginBottom: 10 }}>
                {language === 'en'
                  ? 'Find an HS code from a product name'
                  : 'Trouver un code SH à partir d’un nom de produit'}
              </div>
              <ProductHSSearch language={language} lang={language} />
            </div>
            <CountryHS6History language={language} />
          </TabsContent>

          {/* ── Multi-Country Comparison Tab ─────────────────── */}
          <TabsContent value="comparison" className="space-y-8">
            <MultiCountryComparison language={language} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
