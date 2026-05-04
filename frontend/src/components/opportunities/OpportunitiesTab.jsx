/**
 * Opportunities Tab Component
 * Main tab containing AI Analysis, Substitution, Value Chains, and By Product analysis
 */
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Card, CardContent } from '../ui/card';
import { 
  TrendingUp, Layers, Package, BarChart3, ArrowLeftRight, Sparkles
} from 'lucide-react';

import OpportunitySummary from './OpportunitySummary';
import ValueChains from './ValueChains';
import ProductAnalysisView from './ProductAnalysisView';
import SubstitutionAnalysis from './SubstitutionAnalysis';
import AIAnalysis from './AIAnalysis';

export default function OpportunitiesTab({ language = 'fr' }) {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language || language;

  const texts = {
    fr: {
      title: "Opportunités Commerciales",
      subtitle: "Découvrez les opportunités d'échanges intra-africains sous la ZLECAf",
      tabs: {
        ai: "Analyse IA",
        substitution: "Substitution",
        summary: "Vue d'ensemble",
        valueChains: "Chaînes de Valeur",
        byProduct: "Par Produit"
      }
    },
    en: {
      title: "Trade Opportunities",
      subtitle: "Discover intra-African trade opportunities under AfCFTA",
      tabs: {
        ai: "AI Analysis",
        substitution: "Substitution",
        summary: "Overview",
        valueChains: "Value Chains",
        byProduct: "By Product"
      }
    }
  };

  const txt = texts[currentLang] || texts.fr;

  return (
    <div className="space-y-6" data-testid="opportunities-tab">
      {/* Header */}
      <div className="text-center pb-4 border-b border-slate-100">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center justify-center gap-3">
          <TrendingUp className="h-7 w-7 text-emerald-600" />
          {txt.title}
        </h1>
        <p className="text-slate-500 mt-1">{txt.subtitle}</p>
      </div>

      {/* Sub-tabs */}
      <Tabs defaultValue="ai" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 max-w-3xl mx-auto">
          <TabsTrigger 
            value="ai" 
            className="flex items-center gap-2"
            data-testid="opportunities-ai-tab"
          >
            <Sparkles className="h-4 w-4" />
            <span className="hidden sm:inline">{txt.tabs.ai}</span>
          </TabsTrigger>
          <TabsTrigger 
            value="substitution" 
            className="flex items-center gap-2"
            data-testid="opportunities-substitution-tab"
          >
            <ArrowLeftRight className="h-4 w-4" />
            <span className="hidden sm:inline">{txt.tabs.substitution}</span>
          </TabsTrigger>
          <TabsTrigger 
            value="summary" 
            className="flex items-center gap-2"
            data-testid="opportunities-summary-tab"
          >
            <BarChart3 className="h-4 w-4" />
            <span className="hidden sm:inline">{txt.tabs.summary}</span>
          </TabsTrigger>
          <TabsTrigger 
            value="valueChains" 
            className="flex items-center gap-2"
            data-testid="opportunities-valuechains-tab"
          >
            <Layers className="h-4 w-4" />
            <span className="hidden sm:inline">{txt.tabs.valueChains}</span>
          </TabsTrigger>
          <TabsTrigger 
            value="byProduct" 
            className="flex items-center gap-2"
            data-testid="opportunities-byproduct-tab"
          >
            <Package className="h-4 w-4" />
            <span className="hidden sm:inline">{txt.tabs.byProduct}</span>
          </TabsTrigger>
        </TabsList>

        {/* AI Analysis Tab (NEW - Default) */}
        <TabsContent value="ai" className="mt-6">
          <AIAnalysis language={currentLang} />
        </TabsContent>

        {/* Substitution Analysis Tab */}
        <TabsContent value="substitution" className="mt-6">
          <SubstitutionAnalysis language={currentLang} />
        </TabsContent>

        {/* Summary Tab */}
        <TabsContent value="summary" className="mt-6">
          <OpportunitySummary language={currentLang} />
        </TabsContent>

        {/* Value Chains Tab */}
        <TabsContent value="valueChains" className="mt-6">
          <ValueChains language={currentLang} />
        </TabsContent>

        {/* By Product Tab */}
        <TabsContent value="byProduct" className="mt-6">
          <ProductAnalysisView language={currentLang} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
