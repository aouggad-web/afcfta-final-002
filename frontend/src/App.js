import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './components/ui/card';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

// Importer les composants refactorisés
import CalculatorTab from './components/calculator/CalculatorTab';
import StatisticsTab from './components/statistics/StatisticsTab';
import ProductionTab from './components/production/ProductionTab';
import LogisticsTab from './components/logistics/LogisticsTab';
import ToolsTab from './components/tools/ToolsTab';
import RulesTab from './components/rules/RulesTab';
import CountryProfilesTab from './components/profiles/CountryProfilesTab';
import DashboardTabNew from './components/dashboard/DashboardTabNew';
import OpportunitiesTab from './components/opportunities/OpportunitiesTab';

import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const { i18n } = useTranslation();
  const [countries, setCountries] = useState([]);
  const [activeTab, setActiveTab] = useState('calculator');
  const [language, setLanguage] = useState(i18n.language || 'fr');

  // Synchronise le state language avec i18next
  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  const texts = {
    fr: {
      title: "Accord de la ZLECAf",
      subtitle: "Levier de développement de l'AFRIQUE",
      dashboardTab: "Dashboard",
      calculatorTab: "Calculateur",
      statisticsTab: "Statistiques", 
      productionTab: "Production",
      rulesTab: "Règles d'Origine",
      profilesTab: "Profils Pays",
      toolsTab: "Outils",
      logisticsTab: "Logistique",
      opportunitiesTab: "Opportunités",
      memberCountries: "55 Pays Membres",
      population: "1.3B+ Population"
    },
    en: {
      title: "AfCFTA Agreement",
      subtitle: "AFRICA's Development Lever",
      dashboardTab: "Dashboard",
      calculatorTab: "Calculator",
      statisticsTab: "Statistics",
      productionTab: "Production",
      rulesTab: "Rules of Origin", 
      profilesTab: "Country Profiles",
      toolsTab: "Tools",
      logisticsTab: "Logistics",
      opportunitiesTab: "Opportunities",
      memberCountries: "54 Member Countries",
      population: "1.3B+ Population"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchCountries(language);
  }, [language]);

  const fetchCountries = async (lang) => {
    try {
      const response = await axios.get(`${API}/countries?lang=${lang}`);
      setCountries(response.data);
    } catch (error) {
      console.error('Error loading countries:', error);
      toast({
        title: "Erreur",
        description: "Impossible de charger la liste des pays",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-red-50">
      <Toaster />
      {/* Header with African-inspired design */}
      <div className="relative bg-gradient-to-r from-red-600 via-yellow-500 to-green-600 shadow-2xl border-b-4 border-yellow-500 overflow-hidden">
        {/* African pattern overlay */}
        <div className="absolute inset-0 opacity-10" style={{
          backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0,0,0,.1) 10px, rgba(0,0,0,.1) 20px),
                           repeating-linear-gradient(-45deg, transparent, transparent 10px, rgba(0,0,0,.1) 10px, rgba(0,0,0,.1) 20px)`
        }}></div>
        
        <div className="container mx-auto px-4 py-8 relative z-10">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-lg border-4 border-yellow-400 transform hover:scale-110 transition-transform">
                <span className="text-4xl">🌍</span>
              </div>
              <div className="text-white">
                <h1 className="text-4xl md:text-5xl font-bold drop-shadow-lg">
                  {t.title}
                </h1>
                <p className="text-yellow-100 mt-2 text-lg font-semibold drop-shadow">
                  {t.subtitle}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge className="bg-white text-green-700 hover:bg-yellow-100">{t.memberCountries}</Badge>
                  <Badge className="bg-white text-red-700 hover:bg-yellow-100">{t.population}</Badge>
                </div>
              </div>
            </div>
            
            {/* Sélecteur de langue avec style amélioré */}
            <div className="flex space-x-2">
              <Button 
                variant={language === 'fr' ? 'default' : 'outline'}
                size="lg"
                className={language === 'fr' ? 'bg-white text-green-700 hover:bg-yellow-100 font-bold shadow-lg' : 'bg-white/20 text-white border-white hover:bg-white/30'}
                onClick={() => handleLanguageChange('fr')}
                data-testid="lang-fr-btn"
              >
                🇫🇷 Français
              </Button>
              <Button 
                variant={language === 'en' ? 'default' : 'outline'}
                size="lg"
                className={language === 'en' ? 'bg-white text-green-700 hover:bg-yellow-100 font-bold shadow-lg' : 'bg-white/20 text-white border-white hover:bg-white/30'}
                onClick={() => handleLanguageChange('en')}
                data-testid="lang-en-btn"
              >
                🇬🇧 English
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-9 bg-gradient-to-r from-red-100 via-yellow-100 to-green-100 p-2 shadow-lg">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-slate-700 data-[state=active]:to-slate-900 data-[state=active]:text-white font-bold">
              📊 {t.dashboardTab}
            </TabsTrigger>
            <TabsTrigger value="calculator" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-green-600 data-[state=active]:to-blue-600 data-[state=active]:text-white font-bold">
              🧮 {t.calculatorTab}
            </TabsTrigger>
            <TabsTrigger value="statistics" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-600 data-[state=active]:to-pink-600 data-[state=active]:text-white font-bold">
              📈 {t.statisticsTab}
            </TabsTrigger>
            <TabsTrigger value="opportunities" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-600 data-[state=active]:to-teal-600 data-[state=active]:text-white font-bold" data-testid="opportunities-tab">
              🎯 {t.opportunitiesTab}
            </TabsTrigger>
            <TabsTrigger value="production" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-600 data-[state=active]:to-purple-600 data-[state=active]:text-white font-bold">
              🏭 {t.productionTab}
            </TabsTrigger>
            <TabsTrigger value="logistics" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-teal-600 data-[state=active]:text-white font-bold">
              🚢 {t.logisticsTab}
            </TabsTrigger>
            <TabsTrigger value="tools" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-600 data-[state=active]:to-purple-600 data-[state=active]:text-white font-bold">
              🛠️ {t.toolsTab}
            </TabsTrigger>
            <TabsTrigger value="rules" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-600 data-[state=active]:to-red-600 data-[state=active]:text-white font-bold">
              📜 {t.rulesTab}
            </TabsTrigger>
            <TabsTrigger value="profiles" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-cyan-600 data-[state=active]:text-white font-bold">
              🌍 {t.profilesTab}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <DashboardTabNew language={language} />
          </TabsContent>

          <TabsContent value="calculator">
            <CalculatorTab countries={countries} language={language} />
          </TabsContent>

          <TabsContent value="statistics">
            <StatisticsTab language={language} />
          </TabsContent>

          <TabsContent value="opportunities">
            <OpportunitiesTab language={language} />
          </TabsContent>

          <TabsContent value="production">
            <ProductionTab language={language} />
          </TabsContent>

          <TabsContent value="logistics">
            <LogisticsTab language={language} />
          </TabsContent>

          <TabsContent value="tools">
            <ToolsTab language={language} />
          </TabsContent>

          <TabsContent value="rules">
            <RulesTab language={language} />
          </TabsContent>

          <TabsContent value="profiles">
            <CountryProfilesTab language={language} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;
