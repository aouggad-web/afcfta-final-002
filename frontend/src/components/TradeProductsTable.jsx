import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  ArrowDownToLine, ArrowUpFromLine, Globe, Handshake, 
  TrendingUp, TrendingDown, Package, Info, Loader2 
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

function TradeProductsTable({ language = 'fr' }) {
  const [importsWorld, setImportsWorld] = useState(null);
  const [exportsWorld, setExportsWorld] = useState(null);
  const [intraImports, setIntraImports] = useState(null);
  const [intraExports, setIntraExports] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('imports-world');

  const texts = {
    fr: {
      title: "Top 20 Produits Commerciaux Africains",
      subtitle: "Analyse détaillée des principaux produits échangés (Import/Export Monde & Intra-Africain)",
      importWorld: "Import du Monde (Top 20)",
      exportWorld: "Export vers le Monde (Top 20)",
      importIntra: "Import Intra-Africain (Top 20)",
      exportIntra: "Export Intra-Africain (Top 20)",
      tabImportWorld: "Import Monde",
      tabExportWorld: "Export Monde",
      tabImportIntra: "Import Intra-AF",
      tabExportIntra: "Export Intra-AF",
      loading: "Chargement des données commerciales...",
      product: "Produit",
      hsCode: "Code HS",
      value: "Valeur",
      share: "Part",
      growth: "Croissance",
      topExporters: "Top Exportateurs",
      topImporters: "Top Importateurs",
      source: "Source",
      year: "Année",
      footerSources: "Sources: UNCTAD COMTRADE, ITC Trade Map, African Development Bank, AfCFTA Secretariat",
      footerSources: "Sources: UNCTAD COMTRADE, OEC/BACI 2024, ITC Trade Map, African Development Bank, AfCFTA Secretariat",
      footerNote: "Les données représentent les 20 principaux produits par valeur commerciale. Classification selon le Système Harmonisé (HS). Données 2024.",
      titleImportWorld: "Top 20 Produits Importés par l'Afrique du Monde",
      titleExportWorld: "Top 20 Produits Exportés par l'Afrique vers le Monde",
      titleImportIntra: "Top 20 Produits Importés en Commerce Intra-Africain",
      titleExportIntra: "Top 20 Produits Exportés en Commerce Intra-Africain"
    },
    en: {
      title: "Top 20 African Trade Products",
      subtitle: "Detailed analysis of major traded products (World & Intra-African Import/Export)",
      importWorld: "World Imports (Top 20)",
      exportWorld: "World Exports (Top 20)",
      importIntra: "Intra-African Imports (Top 20)",
      exportIntra: "Intra-African Exports (Top 20)",
      tabImportWorld: "World Import",
      tabExportWorld: "World Export",
      tabImportIntra: "Intra-AF Import",
      tabExportIntra: "Intra-AF Export",
      loading: "Loading trade data...",
      product: "Product",
      hsCode: "HS Code",
      value: "Value",
      share: "Share",
      growth: "Growth",
      topExporters: "Top Exporters",
      topImporters: "Top Importers",
      source: "Source",
      year: "Year",
      footerSources: "Sources: UNCTAD COMTRADE, ITC Trade Map, African Development Bank, AfCFTA Secretariat",
      footerSources: "Sources: UNCTAD COMTRADE, OEC/BACI 2024, ITC Trade Map, African Development Bank, AfCFTA Secretariat",
      footerNote: "Data represents the top 20 products by trade value. Classification according to the Harmonized System (HS). 2024 data.",
      titleImportWorld: "Top 20 Products Imported by Africa from the World",
      titleExportWorld: "Top 20 Products Exported by Africa to the World",
      titleImportIntra: "Top 20 Products Imported in Intra-African Trade",
      titleExportIntra: "Top 20 Products Exported in Intra-African Trade"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchAllData();
  }, [language]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [importsRes, exportsRes, intraImpRes, intraExpRes, summaryRes] = await Promise.all([
        axios.get(`${API}/statistics/trade-products/imports-world?lang=${language}`),
        axios.get(`${API}/statistics/trade-products/exports-world?lang=${language}`),
        axios.get(`${API}/statistics/trade-products/intra-imports?lang=${language}`),
        axios.get(`${API}/statistics/trade-products/intra-exports?lang=${language}`),
        axios.get(`${API}/statistics/trade-products/summary`)
      ]);
      
      setImportsWorld(importsRes.data);
      setExportsWorld(exportsRes.data);
      setIntraImports(intraImpRes.data);
      setIntraExports(intraExpRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Error fetching trade products data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value) => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}B`;
    }
    return `$${value}M`;
  };

  const renderGrowthBadge = (growth) => {
    if (growth > 0) {
      return (
        <span className="stats-chip up">
          <TrendingUp className="w-3 h-3" />
          +{growth}%
        </span>
      );
    } else if (growth < 0) {
      return (
        <span className="stats-chip down">
          <TrendingDown className="w-3 h-3" />
          {growth}%
        </span>
      );
    }
    return <span className="stats-chip flat">0%</span>;
  };

  const renderProductTable = (data, type) => {
    if (!data || !data.products) return null;

    const isExport = type.includes('export');
    const isIntra = type.includes('intra');
    const accentColor = isIntra ? '#9B6EF5' : isExport ? '#1A7A4A' : '#1A6B8A';
    const valueColor  = isIntra ? '#a78bfa'  : isExport ? '#34d399'  : '#38bdf8';

    return (
      <div style={{ overflowX: 'auto' }}>
        <table className="stats-table">
          <thead>
            <tr style={{ borderLeft: `3px solid ${accentColor}` }}>
              <th style={{ textAlign: 'left', width: 42 }}>#</th>
              <th style={{ textAlign: 'left' }}>{t.product}</th>
              <th style={{ textAlign: 'left', width: 80 }}>{t.hsCode}</th>
              <th style={{ textAlign: 'right', width: 110 }}>{t.value}</th>
              <th style={{ textAlign: 'right', width: 72 }}>{t.share}</th>
              <th style={{ textAlign: 'center', width: 100 }}>{t.growth}</th>
              <th style={{ textAlign: 'left' }}>{isExport ? t.topExporters : t.topImporters}</th>
            </tr>
          </thead>
          <tbody>
            {data.products.map((product, index) => (
              <tr key={product.rank}>
                <td>
                  <span className={`stats-rank-badge ${index === 0 ? 'rank-1' : index === 1 ? 'rank-2' : index === 2 ? 'rank-3' : 'rank-n'}`}>
                    {product.rank}
                  </span>
                </td>
                <td style={{ fontWeight: 600, color: '#EAE0D0' }}>{product.product}</td>
                <td>
                  <span style={{ fontFamily: 'monospace', fontSize: '0.7rem', padding: '2px 6px', borderRadius: 4, background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.1)', color: 'rgba(234,224,208,0.7)' }}>
                    {product.hs_code}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <span style={{ fontWeight: 700, color: valueColor }}>
                    {formatValue(product.value_mln_usd)}
                  </span>
                </td>
                <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.8)' }}>
                  {product.share_percent}%
                </td>
                <td style={{ textAlign: 'center' }}>
                  {renderGrowthBadge(product.growth_2023_2024)}
                </td>
                <td>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                    {(isExport ? product.top_exporters : product.top_importers)?.slice(0, 3).map((country, i) => (
                      <span key={i} style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: 100, background: `color-mix(in srgb, ${accentColor} 13%, transparent)`, border: `1px solid color-mix(in srgb, ${accentColor} 27%, transparent)`, color: 'rgba(234,224,208,0.8)' }}>
                        {country}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="stats-loading">
        <div className="stats-spinner" />
        <p style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.875rem' }}>{t.loading}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="stats-hero">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h2 className="stats-hero-title flex items-center gap-2">
              <Package style={{ width: 26, height: 26, color: '#D4891A', flexShrink: 0 }} />
              {t.title}
            </h2>
            <p className="stats-hero-subtitle">{t.subtitle}</p>
            <div className="stats-kente-bar" style={{ width: 180, marginTop: 10 }} />
          </div>
          {summary && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 flex-1 min-w-0" style={{ maxWidth: 540 }}>
              {[
                { label: t.importWorld,  value: formatValue(summary.top_20_imports_world_total_mln_usd),  color: '#38bdf8' },
                { label: t.exportWorld,  value: formatValue(summary.top_20_exports_world_total_mln_usd),  color: '#34d399' },
                { label: t.importIntra,  value: formatValue(summary.top_20_intra_african_imports_total_mln_usd), color: '#a78bfa' },
                { label: t.exportIntra,  value: formatValue(summary.top_20_intra_african_exports_total_mln_usd), color: '#fb923c' },
              ].map((item, i) => (
                <div key={i} style={{ background: 'rgba(255,255,255,0.07)', backdropFilter: 'blur(6px)', borderRadius: 10, padding: '10px 14px', border: `1px solid color-mix(in srgb, ${item.color} 20%, transparent)` }}>
                  <p style={{ fontSize: '0.65rem', color: 'rgba(142,155,174,0.8)', textTransform: 'uppercase', letterSpacing: '0.07em', margin: 0 }}>{item.label}</p>
                  <p style={{ fontSize: '1.2rem', fontWeight: 800, color: item.color, margin: '4px 0 0' }}>{item.value}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Sub-tabs ───────────────────────────────────────────── */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList
          className="inline-flex gap-1 p-1 rounded-xl w-full sm:w-auto"
          style={{ background: 'rgba(18,24,32,0.85)', border: '1px solid rgba(212,137,26,0.18)' }}
        >
          {[
            { value: 'imports-world', icon: <ArrowDownToLine className="w-4 h-4" />, label: t.tabImportWorld,  color: '#1A6B8A', active: '#38bdf8' },
            { value: 'exports-world', icon: <ArrowUpFromLine className="w-4 h-4" />, label: t.tabExportWorld,  color: '#1A7A4A', active: '#34d399' },
            { value: 'intra-imports', icon: <Handshake className="w-4 h-4" />,       label: t.tabImportIntra, color: '#7c3aed', active: '#a78bfa' },
            { value: 'intra-exports', icon: <Globe className="w-4 h-4" />,           label: t.tabExportIntra, color: '#C8531A', active: '#fb923c' },
          ].map(tab => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                background: activeTab === tab.value ? `${tab.color}cc` : 'transparent',
                color: activeTab === tab.value ? '#EAE0D0' : 'rgba(142,155,174,0.65)',
                boxShadow: activeTab === tab.value ? `0 2px 8px ${tab.color}55` : 'none',
              }}
            >
              {tab.icon}
              <span className="hidden sm:inline">{tab.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Imports from World */}
        <TabsContent value="imports-world">
          <div className="stats-chart-card">
            <div className="stats-chart-header blue">
              <div className="stats-chart-title blue">
                <ArrowDownToLine className="w-5 h-5" />
                {language === 'en' ? t.titleImportWorld : importsWorld?.title}
              </div>
              <div className="stats-chart-subtitle">
                <Info className="w-3 h-3 inline mr-1" />
                {t.source}: {importsWorld?.source} | {t.year}: {importsWorld?.year}
              </div>
            </div>
            <div style={{ padding: 0 }}>
              {renderProductTable(importsWorld, 'imports-world')}
            </div>
          </div>
        </TabsContent>

        {/* Exports to World */}
        <TabsContent value="exports-world">
          <div className="stats-chart-card">
            <div className="stats-chart-header" style={{ borderBottomColor: 'rgba(52,211,153,0.2)' }}>
              <div className="stats-chart-title" style={{ color: '#34d399' }}>
                <ArrowUpFromLine className="w-5 h-5" />
                {language === 'en' ? t.titleExportWorld : exportsWorld?.title}
              </div>
              <div className="stats-chart-subtitle">
                <Info className="w-3 h-3 inline mr-1" />
                {t.source}: {exportsWorld?.source} | {t.year}: {exportsWorld?.year}
              </div>
            </div>
            <div style={{ padding: 0 }}>
              {renderProductTable(exportsWorld, 'exports-world')}
            </div>
          </div>
        </TabsContent>

        {/* Intra-African Imports */}
        <TabsContent value="intra-imports">
          <div className="stats-chart-card">
            <div className="stats-chart-header" style={{ borderBottomColor: 'rgba(167,139,250,0.2)' }}>
              <div className="stats-chart-title violet">
                <Handshake className="w-5 h-5" />
                {language === 'en' ? t.titleImportIntra : intraImports?.title}
              </div>
              <div className="stats-chart-subtitle">
                <Info className="w-3 h-3 inline mr-1" />
                {t.source}: {intraImports?.source} | {t.year}: {intraImports?.year}
              </div>
            </div>
            <div style={{ padding: 0 }}>
              {renderProductTable(intraImports, 'intra-imports')}
            </div>
          </div>
        </TabsContent>

        {/* Intra-African Exports */}
        <TabsContent value="intra-exports">
          <div className="stats-chart-card">
            <div className="stats-chart-header terra">
              <div className="stats-chart-title terra">
                <Globe className="w-5 h-5" />
                {language === 'en' ? t.titleExportIntra : intraExports?.title}
              </div>
              <div className="stats-chart-subtitle">
                <Info className="w-3 h-3 inline mr-1" />
                {t.source}: {intraExports?.source} | {t.year}: {intraExports?.year}
              </div>
            </div>
            <div style={{ padding: 0 }}>
              {renderProductTable(intraExports, 'intra-exports')}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Footer Info */}
      <div className="stats-source-note" style={{ background: 'rgba(18,24,32,0.5)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)' }}>
        <Info className="w-4 h-4 inline mr-1 opacity-60" />
        <strong>{language === 'en' ? 'Sources' : 'Sources'}:</strong> {t.footerSources}
        <br />
        <span style={{ opacity: 0.8 }}>{t.footerNote}</span>
      </div>
    </div>
  );
}

export default TradeProductsTable;
