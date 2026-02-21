/**
 * AI Trade Summary Component
 * Quick AI-generated trade analysis for country profiles
 */
import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Sparkles, Loader2, TrendingUp, TrendingDown, 
  Globe, AlertTriangle, ChevronDown, ChevronUp,
  BarChart3
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Cell
} from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const formatValue = (value) => {
  if (!value || isNaN(value)) return '$0';
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}B`;
  return `$${value.toFixed(0)}M`;
};

export default function AITradeSummary({ countryName, language = 'fr' }) {
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [tradeData, setTradeData] = useState(null);
  const [error, setError] = useState(null);

  const texts = {
    fr: {
      title: "Analyse IA du Commerce",
      generateBtn: "Générer l'analyse IA",
      loading: "Analyse en cours...",
      topExports: "Top Opportunités Export",
      topImports: "Opportunités de Substitution",
      tradeBalance: "Balance Commerciale",
      exports: "Exports",
      imports: "Imports",
      balance: "Balance",
      trend: "Tendance",
      potential: "Potentiel",
      estimation: "ESTIMATION",
      viewMore: "Voir plus",
      viewLess: "Voir moins",
      noData: "Cliquez pour générer une analyse",
      sources: "Sources",
      poweredBy: "Alimenté par Gemini AI"
    },
    en: {
      title: "AI Trade Analysis",
      generateBtn: "Generate AI Analysis",
      loading: "Analyzing...",
      topExports: "Top Export Opportunities",
      topImports: "Substitution Opportunities",
      tradeBalance: "Trade Balance",
      exports: "Exports",
      imports: "Imports",
      balance: "Balance",
      trend: "Trend",
      potential: "Potential",
      estimation: "ESTIMATION",
      viewMore: "View more",
      viewLess: "View less",
      noData: "Click to generate analysis",
      sources: "Sources",
      poweredBy: "Powered by Gemini AI"
    }
  };
  const txt = texts[language] || texts.fr;

  const fetchAnalysis = useCallback(async () => {
    if (!countryName) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Fetch export opportunities and trade balance in parallel
      const [exportRes, balanceRes] = await Promise.all([
        axios.get(`${API}/ai/opportunities/${encodeURIComponent(countryName)}`, {
          params: { mode: 'export', lang: language }
        }),
        axios.get(`${API}/ai/balance/${encodeURIComponent(countryName)}`, {
          params: { lang: language }
        })
      ]);

      setTradeData({
        exports: exportRes.data,
        balance: balanceRes.data
      });
      setExpanded(true);
    } catch (err) {
      console.error('AI Analysis error:', err);
      setError(err.response?.data?.detail || 'Erreur lors de l\'analyse');
    } finally {
      setLoading(false);
    }
  }, [countryName, language]);

  // Prepare chart data from balance
  const balanceChartData = React.useMemo(() => {
    if (!tradeData?.balance?.trade_balance_history) return [];
    return tradeData.balance.trade_balance_history.map(item => ({
      year: item.year,
      exports: item.total_exports_musd || 0,
      imports: item.total_imports_musd || 0,
      balance: item.balance_musd || 0,
      isEstimation: item.is_estimation
    }));
  }, [tradeData]);

  return (
    <Card className="shadow-lg border-t-4 border-t-purple-600" data-testid="ai-trade-summary">
      <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold text-purple-700 flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            {txt.title}
          </CardTitle>
          
          {!tradeData && !loading && (
            <Button
              onClick={fetchAnalysis}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
              data-testid="generate-ai-analysis-btn"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {txt.generateBtn}
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {/* Loading state */}
        {loading && (
          <div className="text-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-purple-500 mx-auto mb-2" />
            <p className="text-purple-600 font-medium">{txt.loading}</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="text-center py-4 text-red-600">
            <AlertTriangle className="h-6 w-6 mx-auto mb-2" />
            <p>{error}</p>
            <Button variant="outline" size="sm" onClick={fetchAnalysis} className="mt-2">
              {txt.retryBtn || 'Réessayer'}
            </Button>
          </div>
        )}

        {/* No data state */}
        {!loading && !error && !tradeData && (
          <p className="text-center text-slate-400 py-4 italic">{txt.noData}</p>
        )}

        {/* Results */}
        {tradeData && (
          <div className="space-y-6">
            {/* Trade Balance Chart */}
            {balanceChartData.length > 0 && (
              <div>
                <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-purple-500" />
                  {txt.tradeBalance} (2020-2024)
                </h4>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={balanceChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}B`} />
                      <Tooltip 
                        formatter={(value) => formatValue(value)}
                        labelFormatter={(label) => `Year: ${label}`}
                      />
                      <Bar dataKey="exports" fill="#10b981" name={txt.exports} />
                      <Bar dataKey="imports" fill="#f97316" name={txt.imports} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Trend analysis */}
                {tradeData.balance?.analysis && (
                  <div className="mt-3 p-3 bg-slate-50 rounded-lg text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      {tradeData.balance.analysis.trend === 'surplus' ? (
                        <Badge className="bg-emerald-100 text-emerald-700">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          {txt.trend}: Excédent
                        </Badge>
                      ) : (
                        <Badge className="bg-orange-100 text-orange-700">
                          <TrendingDown className="h-3 w-3 mr-1" />
                          {txt.trend}: Déficit
                        </Badge>
                      )}
                    </div>
                    {tradeData.balance.analysis.outlook && (
                      <p className="text-slate-600 text-xs mt-1">
                        {tradeData.balance.analysis.outlook}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Top Export Opportunities */}
            {tradeData.exports?.opportunities && (
              <div>
                <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                  {txt.topExports}
                </h4>
                <div className="space-y-2">
                  {tradeData.exports.opportunities.slice(0, expanded ? 5 : 3).map((opp, idx) => (
                    <div 
                      key={idx}
                      className={`flex items-center justify-between p-3 rounded-lg ${
                        opp.is_estimation ? 'bg-amber-50 border border-amber-200' : 'bg-emerald-50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-mono text-slate-500">HS {opp.hs_code}</span>
                        <span className="font-medium text-slate-800">{opp.product_name}</span>
                        {opp.is_estimation && (
                          <Badge className="bg-amber-200 text-amber-800 text-[10px]">
                            {txt.estimation}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1 text-sm text-slate-500">
                          <Globe className="h-3 w-3" />
                          {opp.potential_partner}
                        </div>
                        <span className="font-bold text-emerald-600">
                          {formatValue(opp.potential_value_musd)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                
                {tradeData.exports.opportunities.length > 3 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setExpanded(!expanded)}
                    className="w-full mt-2 text-slate-500"
                  >
                    {expanded ? (
                      <>
                        <ChevronUp className="h-4 w-4 mr-1" />
                        {txt.viewLess}
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4 mr-1" />
                        {txt.viewMore}
                      </>
                    )}
                  </Button>
                )}
              </div>
            )}

            {/* Footer */}
            <div className="pt-3 border-t border-slate-200 text-xs text-slate-400 flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                {txt.poweredBy}
              </span>
              {tradeData.exports?.sources && (
                <span>{txt.sources}: {tradeData.exports.sources.slice(0, 3).join(', ')}</span>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
