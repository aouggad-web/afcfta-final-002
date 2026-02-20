import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  ArrowDownToLine, ArrowUpFromLine, Globe, Handshake, 
  TrendingUp, TrendingDown, Package, Info, Loader2 
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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
        <Badge className="bg-green-100 text-green-700 font-mono">
          <TrendingUp className="w-3 h-3 mr-1" />
          +{growth}%
        </Badge>
      );
    } else if (growth < 0) {
      return (
        <Badge className="bg-red-100 text-red-700 font-mono">
          <TrendingDown className="w-3 h-3 mr-1" />
          {growth}%
        </Badge>
      );
    }
    return <Badge className="bg-gray-100 text-gray-700">0%</Badge>;
  };

  const renderProductTable = (data, type) => {
    if (!data || !data.products) return null;
    
    const isExport = type.includes('export');
    const isIntra = type.includes('intra');
    
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className={`${isIntra ? 'bg-purple-50' : isExport ? 'bg-green-50' : 'bg-blue-50'}`}>
              <th className="px-3 py-3 text-left font-bold text-gray-700 w-12">#</th>
              <th className="px-3 py-3 text-left font-bold text-gray-700">{t.product}</th>
              <th className="px-3 py-3 text-left font-bold text-gray-700 w-20">{t.hsCode}</th>
              <th className="px-3 py-3 text-right font-bold text-gray-700 w-28">{t.value}</th>
              <th className="px-3 py-3 text-right font-bold text-gray-700 w-20">{t.share}</th>
              <th className="px-3 py-3 text-center font-bold text-gray-700 w-28">{t.growth}</th>
              <th className="px-3 py-3 text-left font-bold text-gray-700">{isExport ? t.topExporters : t.topImporters}</th>
            </tr>
          </thead>
          <tbody>
            {data.products.map((product, index) => (
              <tr 
                key={product.rank} 
                className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${index < 3 ? 'bg-yellow-50/30' : ''}`}
              >
                <td className="px-3 py-3">
                  <span className={`
                    inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold
                    ${index === 0 ? 'bg-yellow-400 text-white' : 
                      index === 1 ? 'bg-gray-300 text-gray-700' : 
                      index === 2 ? 'bg-amber-600 text-white' : 
                      'bg-gray-100 text-gray-600'}
                  `}>
                    {product.rank}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <div className="font-medium text-gray-800">{product.product}</div>
                </td>
                <td className="px-3 py-3">
                  <Badge variant="outline" className="font-mono text-xs">
                    {product.hs_code}
                  </Badge>
                </td>
                <td className="px-3 py-3 text-right">
                  <span className={`font-bold ${isExport ? 'text-green-600' : 'text-blue-600'}`}>
                    {formatValue(product.value_mln_usd)}
                  </span>
                </td>
                <td className="px-3 py-3 text-right">
                  <span className="text-gray-600">{product.share_percent}%</span>
                </td>
                <td className="px-3 py-3 text-center">
                  {renderGrowthBadge(product.growth_2023_2024)}
                </td>
                <td className="px-3 py-3">
                  <div className="flex flex-wrap gap-1">
                    {(isExport ? product.top_exporters : product.top_importers)?.slice(0, 3).map((country, i) => (
                      <Badge key={i} variant="outline" className="text-xs bg-white">
                        {country}
                      </Badge>
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
      <Card className="shadow-xl">
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto" />
            <p className="mt-4 text-gray-600">{t.loading}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl font-bold flex items-center gap-3">
            <Package className="w-8 h-8" />
            {t.title}
          </CardTitle>
          <CardDescription className="text-indigo-100 text-base">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
        {summary && (
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                <p className="text-indigo-200 text-xs uppercase">{t.importWorld}</p>
                <p className="text-2xl font-bold">{formatValue(summary.top_20_imports_world_total_mln_usd)}</p>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                <p className="text-indigo-200 text-xs uppercase">{t.exportWorld}</p>
                <p className="text-2xl font-bold">{formatValue(summary.top_20_exports_world_total_mln_usd)}</p>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                <p className="text-indigo-200 text-xs uppercase">{t.importIntra}</p>
                <p className="text-2xl font-bold">{formatValue(summary.top_20_intra_african_imports_total_mln_usd)}</p>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-xl p-4">
                <p className="text-indigo-200 text-xs uppercase">{t.exportIntra}</p>
                <p className="text-2xl font-bold">{formatValue(summary.top_20_intra_african_exports_total_mln_usd)}</p>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Tabs for different tables */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-gray-100 p-1 h-auto gap-1">
          <TabsTrigger 
            value="imports-world" 
            className="data-[state=active]:bg-blue-600 data-[state=active]:text-white py-3 flex items-center gap-2"
          >
            <ArrowDownToLine className="w-4 h-4" />
            {t.tabImportWorld}
          </TabsTrigger>
          <TabsTrigger 
            value="exports-world" 
            className="data-[state=active]:bg-green-600 data-[state=active]:text-white py-3 flex items-center gap-2"
          >
            <ArrowUpFromLine className="w-4 h-4" />
            {t.tabExportWorld}
          </TabsTrigger>
          <TabsTrigger 
            value="intra-imports" 
            className="data-[state=active]:bg-purple-600 data-[state=active]:text-white py-3 flex items-center gap-2"
          >
            <Handshake className="w-4 h-4" />
            {t.tabImportIntra}
          </TabsTrigger>
          <TabsTrigger 
            value="intra-exports" 
            className="data-[state=active]:bg-pink-600 data-[state=active]:text-white py-3 flex items-center gap-2"
          >
            <Globe className="w-4 h-4" />
            {t.tabExportIntra}
          </TabsTrigger>
        </TabsList>

        {/* Imports from World */}
        <TabsContent value="imports-world">
          <Card className="shadow-lg border-t-4 border-t-blue-500">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
              <CardTitle className="text-xl text-blue-700 flex items-center gap-2">
                <ArrowDownToLine className="w-6 h-6" />
                {language === 'en' ? t.titleImportWorld : importsWorld?.title}
              </CardTitle>
              <CardDescription className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                {t.source}: {importsWorld?.source} | {t.year}: {importsWorld?.year}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {renderProductTable(importsWorld, 'imports-world')}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Exports to World */}
        <TabsContent value="exports-world">
          <Card className="shadow-lg border-t-4 border-t-green-500">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
              <CardTitle className="text-xl text-green-700 flex items-center gap-2">
                <ArrowUpFromLine className="w-6 h-6" />
                {language === 'en' ? t.titleExportWorld : exportsWorld?.title}
              </CardTitle>
              <CardDescription className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                {t.source}: {exportsWorld?.source} | {t.year}: {exportsWorld?.year}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {renderProductTable(exportsWorld, 'exports-world')}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Intra-African Imports */}
        <TabsContent value="intra-imports">
          <Card className="shadow-lg border-t-4 border-t-purple-500">
            <CardHeader className="bg-gradient-to-r from-purple-50 to-violet-50">
              <CardTitle className="text-xl text-purple-700 flex items-center gap-2">
                <Handshake className="w-6 h-6" />
                {language === 'en' ? t.titleImportIntra : intraImports?.title}
              </CardTitle>
              <CardDescription className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                {t.source}: {intraImports?.source} | {t.year}: {intraImports?.year}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {renderProductTable(intraImports, 'intra-imports')}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Intra-African Exports */}
        <TabsContent value="intra-exports">
          <Card className="shadow-lg border-t-4 border-t-pink-500">
            <CardHeader className="bg-gradient-to-r from-pink-50 to-rose-50">
              <CardTitle className="text-xl text-pink-700 flex items-center gap-2">
                <Globe className="w-6 h-6" />
                {language === 'en' ? t.titleExportIntra : intraExports?.title}
              </CardTitle>
              <CardDescription className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                {t.source}: {intraExports?.source} | {t.year}: {intraExports?.year}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {renderProductTable(intraExports, 'intra-exports')}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Footer Info */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="text-sm text-gray-600">
              <p><strong>{language === 'en' ? 'Sources' : 'Sources'}:</strong> {t.footerSources}</p>
              <p className="mt-1">{t.footerNote}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default TradeProductsTable;
