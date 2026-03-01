import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

// Import du nouveau thème
import './styles/theme.css';

// Import des nouveaux composants de layout
import AfcftaTopbar from './components/AfcftaTopbar';
import KpiRow from './components/KpiRow';
import SectionHeader from './components/SectionHeader';

// Import des composants de contenu
import CalculatorTab from './components/calculator/CalculatorTab';
import StatisticsTab from './components/statistics/StatisticsTab';
import ProductionTab from './components/production/ProductionTab';
import LogisticsTab from './components/logistics/LogisticsTab';
import ToolsTab from './components/tools/ToolsTab';
import RulesTab from './components/rules/RulesTab';
import CountryProfilesTab from './components/profiles/CountryProfilesTab';
import DashboardTabNew from './components/dashboard/DashboardTabNew';
import OpportunitiesTab from './components/opportunities/OpportunitiesTab';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Interceptor: reject responses that are not valid JSON objects/arrays
// (prevents HTML fallback pages from SPA static servers being stored in state)
axios.interceptors.response.use(
  (response) => {
    const ct = response.headers['content-type'] || '';
    if (!ct.includes('application/json') && !ct.includes('application/')) {
      return Promise.reject(new Error('Non-JSON response'));
    }
    return response;
  },
  (error) => Promise.reject(error)
);

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
    authenticData: "32 pays · données authentiques",
    tariffPositions: "229 519 positions tarifaires",
  },
  en: {
    title: "AfCFTA Agreement",
    subtitle: "Africa's Development Lever",
    memberCountries: "54 Countries",
    population: "1.3B+ Pop.",
    authenticData: "32 countries · authentic data",
    tariffPositions: "229,519 tariff positions",
  },
};

function App() {
  const { i18n } = useTranslation();
  const [countries, setCountries] = useState([]);
  const [activeTab, setActiveTab] = useState('calculator');
  const [language, setLanguage] = useState(i18n.language || 'fr');
  const [stats, setStats] = useState(null);

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  const handleTabChange = (type, value) => {
    if (type === 'tab') {
      // Map les IDs du topbar vers les IDs internes
      const tabMapping = {
        'dashboard': 'dashboard',
        'calculator': 'calculator',
        'stats': 'statistics',
        'opps': 'opportunities',
        'production': 'production',
        'logistics': 'logistics',
        'tools': 'tools',
        'roo': 'rules',
        'profiles': 'profiles'
      };
      setActiveTab(tabMapping[value] || value);
    } else if (type === 'language') {
      handleLanguageChange(value);
    }
  };

  // Map inverse pour le topbar
  const getTopbarActiveTab = () => {
    const reverseMapping = {
      'dashboard': 'dashboard',
      'calculator': 'calculator',
      'statistics': 'stats',
      'opportunities': 'opps',
      'production': 'production',
      'logistics': 'logistics',
      'tools': 'tools',
      'rules': 'roo',
      'profiles': 'profiles'
    };
    return reverseMapping[activeTab] || activeTab;
  };
  const t = texts[language] || texts.fr;

  useEffect(() => {
    fetchCountries(language);
    fetchStats();
  }, [language]);

  const fetchCountries = async (lang) => {
    try {
      const response = await axios.get(`${API}/countries?lang=${lang}`);
      const data = response.data;
      const countriesArray = Array.isArray(data)
        ? data
        : Array.isArray(data?.countries)
        ? data.countries
        : [];
      setCountries(countriesArray);
    } catch (error) {
      console.error('Error loading countries:', error);
      toast({
        title: "Erreur",
        description: "Impossible de charger la liste des pays",
        variant: "destructive"
      });
    }
  };

  const fetchStats = async () => {
    try {
      // Placeholder - could fetch real stats from API
      setStats({
        gdp: "$2.7T",
        trade: "$235B",
        ports: "68",
        progress: "57%"
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <DashboardTabNew language={language} />
          </div>
        );
      case 'calculator':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader 
              title={language === 'fr' ? "Calculateur de Tarifs Douaniers" : "Customs Tariff Calculator"}
              subtitle={language === 'fr' ? "Calculs basés sur les données officielles des administrations douanières" : "Calculations based on official customs data"}
              dotColor="copper"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <CalculatorTab countries={countries} language={language} />
            </div>
          </div>
        );
      case 'statistics':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader 
              title={language === 'fr' ? "Statistiques Commerciales" : "Trade Statistics"}
              subtitle={language === 'fr' ? "Données OEC, COMTRADE, UNCTAD" : "OEC, COMTRADE, UNCTAD Data"}
              dotColor="info"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <StatisticsTab language={language} />
            </div>
          </div>
        );
      case 'opportunities':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader 
              title={language === 'fr' ? "Opportunités Commerciales" : "Trade Opportunities"}
              subtitle={language === 'fr' ? "Analyse des marchés et substitution d'importations" : "Market analysis and import substitution"}
              dotColor="success"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <OpportunitiesTab language={language} />
            </div>
          </div>
        );
      case 'production':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader 
              title={language === 'fr' ? "Production Africaine" : "African Production"}
              subtitle={language === 'fr' ? "Données FAOSTAT et capacités industrielles" : "FAOSTAT data and industrial capacity"}
              dotColor="warning"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <ProductionTab language={language} />
            </div>
          </div>
        );
      case 'logistics':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader 
              title={language === 'fr' ? "Logistique & Infrastructure" : "Logistics & Infrastructure"}
              subtitle={language === 'fr' ? "Ports, corridors, connectivité maritime" : "Ports, corridors, maritime connectivity"}
              dotColor="info"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <LogisticsTab language={language} />
            </div>
          </div>
        );
      case 'tools':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader 
              title={language === 'fr' ? "Outils d'Analyse" : "Analysis Tools"}
              subtitle={language === 'fr' ? "Convertisseurs, recherche HS, IA" : "Converters, HS search, AI"}
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <ToolsTab language={language} />
            </div>
          </div>
        );
      case 'rules':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader 
              title={language === 'fr' ? "Règles d'Origine ZLECAf" : "AfCFTA Rules of Origin"}
              subtitle={language === 'fr' ? "Critères d'éligibilité au tarif préférentiel" : "Preferential tariff eligibility criteria"}
              dotColor="copper"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <RulesTab language={language} />
            </div>
          </div>
        );
      case 'profiles':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader 
              title={language === 'fr' ? "Profils Pays" : "Country Profiles"}
              subtitle={language === 'fr' ? "Données économiques et commerciales par pays" : "Economic and trade data by country"}
              dotColor="success"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <CountryProfilesTab language={language} />
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="afcfta-shell">
      <Toaster />
      
      {/* Header avec navigation */}
      <AfcftaTopbar 
        active={getTopbarActiveTab()} 
        onTabChange={handleTabChange}
        language={language}
      />
      
      {/* KPI Row - visible uniquement sur le dashboard */}
      {activeTab === 'dashboard' && (
        <KpiRow language={language} stats={stats} />
      )}
      
      {/* Contenu principal */}
      {renderContent()}
    </div>
  );
}

export default App;
