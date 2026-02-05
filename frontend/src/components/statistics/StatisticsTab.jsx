/**
 * Statistics Tab - Refactored with Sub-tabs
 * Includes: OEC Stats, Trade Products, Comparisons, Multi-Country Comparison
 */
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { ResponsiveContainer, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { BarChart3, Scale, Globe, TrendingUp, Package } from 'lucide-react';

// Sub-components
import StatisticsZaubaStyle from '../StatisticsZaubaStyle';
import TradeComparison from '../TradeComparison';
import TradeProductsTable from '../TradeProductsTable';
import OECTradeStats from '../stats/OECTradeStats';
import MultiCountryComparison from './MultiCountryComparison';
import { PDFExportButton } from '../common/ExportTools';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function StatisticsTab({ language = 'fr' }) {
  const { t } = useTranslation();
  const [statistics, setStatistics] = useState(null);
  const [activeSubTab, setActiveSubTab] = useState('overview');
  const contentRef = useRef(null);

  const texts = {
    fr: {
      title: "Statistiques Commerciales",
      subtitle: "Données et analyses du commerce africain",
      overview: "Vue d'ensemble",
      products: "Produits",
      trends: "Tendances",
      comparison: "Comparaison Pays",
      topExporters: "Top 10 Exportateurs",
      topImporters: "Top 10 Importateurs",
      exports: "Exportations 2024",
      imports: "Importations 2024",
      exportsEvolution: "Volume des exportations en milliards USD",
      importsVolume: "Volume des importations en milliards USD"
    },
    en: {
      title: "Trade Statistics",
      subtitle: "African trade data and analysis",
      overview: "Overview",
      products: "Products",
      trends: "Trends",
      comparison: "Country Comparison",
      topExporters: "Top 10 Exporters",
      topImporters: "Top 10 Importers",
      exports: "Exports 2024",
      imports: "Imports 2024",
      exportsEvolution: "Export volume in billion USD",
      importsVolume: "Import volume in billion USD"
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

  return (
    <div className="space-y-6" data-testid="statistics-tab">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="h-7 w-7 text-emerald-600" />
            {txt.title}
          </h2>
          <p className="text-slate-500 mt-1">{txt.subtitle}</p>
        </div>
        <PDFExportButton
          targetRef={contentRef}
          filename="statistics"
          title={txt.title}
          language={language}
        />
      </div>

      {/* Sub-tabs Navigation */}
      <Tabs value={activeSubTab} onValueChange={setActiveSubTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 max-w-2xl">
          <TabsTrigger value="overview" className="flex items-center gap-2" data-testid="stats-overview-tab">
            <Globe className="h-4 w-4" />
            {txt.overview}
          </TabsTrigger>
          <TabsTrigger value="products" className="flex items-center gap-2" data-testid="stats-products-tab">
            <Package className="h-4 w-4" />
            {txt.products}
          </TabsTrigger>
          <TabsTrigger value="trends" className="flex items-center gap-2" data-testid="stats-trends-tab">
            <TrendingUp className="h-4 w-4" />
            {txt.trends}
          </TabsTrigger>
          <TabsTrigger value="comparison" className="flex items-center gap-2" data-testid="stats-comparison-tab">
            <Scale className="h-4 w-4" />
            {txt.comparison}
          </TabsTrigger>
        </TabsList>

        <div ref={contentRef}>
          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-8">
            {/* OEC Trade Statistics */}
            <OECTradeStats language={language} />
            
            {/* Zauba Style Stats */}
            <StatisticsZaubaStyle language={language} />

            {/* Top Exporters/Importers Charts */}
            {statistics && statistics.top_exporters_2024 && statistics.top_importers_2024 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="shadow-xl" data-testid="top-exporters-chart">
                  <CardHeader className="bg-gradient-to-r from-emerald-50 to-green-100 pb-2">
                    <CardTitle className="text-lg font-bold text-emerald-700 flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      {txt.topExporters}
                    </CardTitle>
                    <CardDescription className="text-emerald-600 text-xs">
                      {txt.exportsEvolution}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        data={statistics.top_exporters_2024?.slice(0, 10)}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis 
                          type="number" 
                          tickFormatter={(value) => `$${(value / 1e9).toFixed(0)}B`}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis 
                          dataKey="name" 
                          type="category" 
                          tick={{ fontSize: 11 }}
                          width={75}
                        />
                        <Tooltip 
                          formatter={(value) => [`$${(value / 1e9).toFixed(1)}B`, txt.exports]}
                          contentStyle={{ borderRadius: '8px' }}
                        />
                        <Bar 
                          dataKey="exports_2024" 
                          fill="#10b981" 
                          radius={[0, 4, 4, 0]}
                          barSize={18}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card className="shadow-xl" data-testid="top-importers-chart">
                  <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-100 pb-2">
                    <CardTitle className="text-lg font-bold text-blue-700 flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 rotate-180" />
                      {txt.topImporters}
                    </CardTitle>
                    <CardDescription className="text-blue-600 text-xs">
                      {txt.importsVolume}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        data={statistics.top_importers_2024?.slice(0, 10)}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis 
                          type="number" 
                          tickFormatter={(value) => `$${(value / 1e9).toFixed(0)}B`}
                          tick={{ fontSize: 10 }}
                        />
                        <YAxis 
                          dataKey="name" 
                          type="category" 
                          tick={{ fontSize: 11 }}
                          width={75}
                        />
                        <Tooltip 
                          formatter={(value) => [`$${(value / 1e9).toFixed(1)}B`, txt.imports]}
                          contentStyle={{ borderRadius: '8px' }}
                        />
                        <Bar 
                          dataKey="imports_2024" 
                          fill="#3b82f6" 
                          radius={[0, 4, 4, 0]}
                          barSize={18}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-8">
            <TradeProductsTable language={language} />
          </TabsContent>

          {/* Trends Tab */}
          <TabsContent value="trends" className="space-y-8">
            <TradeComparison language={language} />
          </TabsContent>

          {/* Multi-Country Comparison Tab */}
          <TabsContent value="comparison" className="space-y-8">
            <MultiCountryComparison language={language} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
