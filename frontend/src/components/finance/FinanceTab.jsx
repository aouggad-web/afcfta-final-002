import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Landmark, ShieldCheck, Sparkles, BarChart3, ArrowLeftRight, Grid3x3 } from 'lucide-react';

import BankingInfoPanel from '../banking/BankingInfoPanel';
import BankingRecommendations from '../banking/BankingRecommendations';
import BankScoring from '../banking/BankScoring';
import FXHedging from '../banking/FXHedging';
import FinancingMatrix from '../banking/FinancingMatrix';
import Insurance from './Insurance';

const texts = {
  fr: {
    banking: 'Banque',
    insurance: 'Assurance',
    bankingInfo: 'Infos & Réglementation',
    recommendations: 'Recommandations',
    scoring: 'Scoring Banques',
    hedging: 'Couverture FX',
    matrix: 'Matrice Financement',
  },
  en: {
    banking: 'Banking',
    insurance: 'Insurance',
    bankingInfo: 'Info & Regulation',
    recommendations: 'Recommendations',
    scoring: 'Bank Scoring',
    hedging: 'FX Hedging',
    matrix: 'Financing Matrix',
  },
};

export default function FinanceTab({ language = 'en', countries = [] }) {
  const t = texts[language] || texts.en;

  return (
    <div className="space-y-5" data-testid="finance-tab">
      <Tabs defaultValue="banking" className="space-y-5">
        <TabsList className="tabs-list-boxed cols-2">
          <TabsTrigger value="banking" className="tab-trigger-enhanced tab-blue">
            <Landmark className="tab-icon" />
            <span>{t.banking}</span>
          </TabsTrigger>
          <TabsTrigger value="insurance" className="tab-trigger-enhanced tab-blue">
            <ShieldCheck className="tab-icon" />
            <span>{t.insurance}</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="banking">
          <Tabs defaultValue="info" className="space-y-5">
            <TabsList className="tabs-list-boxed cols-5">
              <TabsTrigger value="info" className="tab-trigger-enhanced tab-blue">
                <Landmark className="tab-icon" />
                <span>{t.bankingInfo}</span>
              </TabsTrigger>
              <TabsTrigger value="recommendations" className="tab-trigger-enhanced tab-blue">
                <Sparkles className="tab-icon" />
                <span>{t.recommendations}</span>
              </TabsTrigger>
              <TabsTrigger value="scoring" className="tab-trigger-enhanced tab-blue">
                <BarChart3 className="tab-icon" />
                <span>{t.scoring}</span>
              </TabsTrigger>
              <TabsTrigger value="hedging" className="tab-trigger-enhanced tab-blue">
                <ArrowLeftRight className="tab-icon" />
                <span>{t.hedging}</span>
              </TabsTrigger>
              <TabsTrigger value="matrix" className="tab-trigger-enhanced tab-blue">
                <Grid3x3 className="tab-icon" />
                <span>{t.matrix}</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="info">
              <div className="afcfta-card">
                <BankingInfoPanel language={language} countries={countries} />
              </div>
            </TabsContent>
            <TabsContent value="recommendations">
              <BankingRecommendations language={language} />
            </TabsContent>
            <TabsContent value="scoring">
              <BankScoring language={language} />
            </TabsContent>
            <TabsContent value="hedging">
              <FXHedging language={language} />
            </TabsContent>
            <TabsContent value="matrix">
              <FinancingMatrix language={language} />
            </TabsContent>
          </Tabs>
        </TabsContent>

        <TabsContent value="insurance">
          <Insurance language={language} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
