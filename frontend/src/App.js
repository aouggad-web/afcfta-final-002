import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

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

const TABS = [
  { id: 'dashboard', icon: '📊', fr: 'Dashboard', en: 'Dashboard' },
  { id: 'calculator', icon: '🧮', fr: 'Calculateur', en: 'Calculator' },
  { id: 'statistics', icon: '📈', fr: 'Statistiques', en: 'Statistics' },
  { id: 'opportunities', icon: '🎯', fr: 'Opportunités', en: 'Opportunities' },
  { id: 'production', icon: '🏭', fr: 'Production', en: 'Production' },
  { id: 'logistics', icon: '🚢', fr: 'Logistique', en: 'Logistics' },
  { id: 'tools', icon: '🛠️', fr: 'Outils', en: 'Tools' },
  { id: 'rules', icon: '📜', fr: "Règles d'Origine", en: 'Rules of Origin' },
  { id: 'profiles', icon: '🌍', fr: 'Profils Pays', en: 'Country Profiles' },
];

const texts = {
  fr: {
    title: "Accord de la ZLECAf",
    subtitle: "Levier de développement de l'Afrique",
    memberCountries: "54 Pays",
    population: "1.3B+ Pop.",
  },
  en: {
    title: "AfCFTA Agreement",
    subtitle: "Africa's Development Lever",
    memberCountries: "54 Countries",
    population: "1.3B+ Pop.",
  },
};

function App() {
  const { i18n } = useTranslation();
  const [countries, setCountries] = useState([]);
  const [activeTab, setActiveTab] = useState('calculator');
  const [language, setLanguage] = useState(i18n.language || 'fr');

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  const t = texts[language] || texts.fr;

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

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard': return <DashboardTabNew language={language} />;
      case 'calculator': return <CalculatorTab countries={countries} language={language} />;
      case 'statistics': return <StatisticsTab language={language} />;
      case 'opportunities': return <OpportunitiesTab language={language} />;
      case 'production': return <ProductionTab language={language} />;
      case 'logistics': return <LogisticsTab language={language} />;
      case 'tools': return <ToolsTab language={language} />;
      case 'rules': return <RulesTab language={language} />;
      case 'profiles': return <CountryProfilesTab language={language} />;
      default: return <CalculatorTab countries={countries} language={language} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster />

      {/* Header */}
      <header className="app-header">
        <div className="app-header-inner">
          <div className="app-title-group">
            <div className="app-logo">🌍</div>
            <div>
              <div className="app-title">{t.title}</div>
              <div className="app-subtitle">{t.subtitle}</div>
              <div className="app-badges">
                <span className="app-badge">{t.memberCountries}</span>
                <span className="app-badge">{t.population}</span>
              </div>
            </div>
          </div>

          <div className="lang-switcher">
            <button
              className={`lang-btn ${language === 'fr' ? 'active' : ''}`}
              onClick={() => handleLanguageChange('fr')}
              data-testid="lang-fr-btn"
            >
              FR
            </button>
            <button
              className={`lang-btn ${language === 'en' ? 'active' : ''}`}
              onClick={() => handleLanguageChange('en')}
              data-testid="lang-en-btn"
            >
              EN
            </button>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="nav-tabs-wrapper">
        <div className="nav-tabs-inner">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              data-testid={`${tab.id}-tab`}
            >
              <span className="nav-tab-icon">{tab.icon}</span>
              {tab[language] || tab.fr}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="main-content">
        <div className="tab-panel" key={activeTab}>
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
}

export default App;
