import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

import './styles/theme.css';

import AfcftaTopbar from './components/AfcftaTopbar';
import KpiRow from './components/KpiRow';
import SectionHeader from './components/SectionHeader';

import CalculatorTab from './components/calculator/CalculatorTab';
import StatisticsTab from './components/statistics/StatisticsTab';
import ProductionTab from './components/production/ProductionTab';
import LogisticsTab from './components/logistics/LogisticsTab';
import ToolsTab from './components/tools/ToolsTab';
import RulesTab from './components/rules/RulesTab';
import CountryProfilesTab from './components/profiles/CountryProfilesTab';
import DashboardTabNew from './components/dashboard/DashboardTabNew';
import OpportunitiesTab from './components/opportunities/OpportunitiesTab';
import BankingInfoPanel from './components/banking/BankingInfoPanel';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

axios.interceptors.response.use(
  (response) => {
    const ct = response.headers['content-type'] || '';
    if (ct.includes('text/html')) {
      return Promise.reject(new Error('Non-JSON response'));
    }
    return response;
  },
  (error) => Promise.reject(error)
);

const texts = {
  fr: {
    title: 'Accord de la ZLECAf',
    subtitle: "Plateforme d'intelligence commerciale africaine — droits, TVA, taxes totales et analyses.",
    ribbon1: '54 signataires ZLECAf',
    ribbon2: '1,3 Md+ habitants',
    ribbon3: 'Données actualisées',
    shellLead: 'Intelligence commerciale, douanière, logistique et réglementaire pour les marchés africains.',
  },
  en: {
    title: 'AfCFTA Agreement',
    subtitle: 'African trade intelligence platform — duties, VAT, total taxes and analytics.',
    ribbon1: '54 AfCFTA signatories',
    ribbon2: '1.3B+ inhabitants',
    ribbon3: 'Updated data',
    shellLead: 'Trade, customs, logistics and regulatory intelligence for African markets.',
  },
};

function App() {
  const { i18n } = useTranslation();
  const [countries, setCountries] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [language, setLanguage] = useState(i18n.language || 'fr');
  const [stats, setStats] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState(null);

  const t = texts[language] || texts.fr;

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  const handleTabChange = (type, value) => {
    if (type === 'tab') {
      const tabMapping = {
        dashboard: 'dashboard',
        calculator: 'calculator',
        stats: 'statistics',
        opps: 'opportunities',
        production: 'production',
        logistics: 'logistics',
        banking: 'banking',
        tools: 'tools',
        roo: 'rules',
        profiles: 'profiles',
      };
      setActiveTab(tabMapping[value] || value);
    } else if (type === 'language') {
      handleLanguageChange(value);
    }
  };

  const getTopbarActiveTab = () => {
    const reverseMapping = {
      dashboard: 'dashboard',
      calculator: 'calculator',
      statistics: 'stats',
      opportunities: 'opps',
      production: 'production',
      logistics: 'logistics',
      banking: 'banking',
      tools: 'tools',
      rules: 'roo',
      profiles: 'profiles',
    };
    return reverseMapping[activeTab] || activeTab;
  };

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
      setBackendOnline(true);
    } catch (error) {
      console.error('Error loading countries:', error);
      setBackendOnline(false);
    }
  };

  const fetchStats = async () => {
    try {
      setStats({
        gdp: '$2.7T',
        trade: '$235B',
        ports: '68',
        progress: '57%',
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
              title={language === 'fr' ? 'Calculateur de Tarifs Douaniers' : 'Customs Tariff Calculator'}
              subtitle={
                language === 'fr'
                  ? 'Calculs basés sur les données officielles des administrations douanières'
                  : 'Calculations based on official customs data'
              }
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
              title={language === 'fr' ? 'Statistiques Commerciales' : 'Trade Statistics'}
              subtitle={language === 'fr' ? 'Données OEC, COMTRADE, UNCTAD' : 'OEC, COMTRADE, UNCTAD Data'}
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
              title={language === 'fr' ? 'Opportunités Commerciales' : 'Trade Opportunities'}
              subtitle={
                language === 'fr'
                  ? "Analyse des marchés et substitution d'importations"
                  : 'Market analysis and import substitution'
              }
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
              title={language === 'fr' ? 'Production Africaine' : 'African Production'}
              subtitle={
                language === 'fr'
                  ? 'Données FAOSTAT et capacités industrielles'
                  : 'FAOSTAT data and industrial capacity'
              }
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
              title={language === 'fr' ? 'Logistique & Infrastructure' : 'Logistics & Infrastructure'}
              subtitle={
                language === 'fr'
                  ? 'Ports, corridors, connectivité maritime'
                  : 'Ports, corridors, maritime connectivity'
              }
              dotColor="info"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <LogisticsTab language={language} />
            </div>
          </div>
        );

      case 'banking':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader
              title={language === 'fr' ? 'Système Bancaire Africain' : 'African Banking System'}
              subtitle={
                language === 'fr'
                  ? 'Change, domiciliation, financement du commerce'
                  : 'Forex, domiciliation, trade finance'
              }
              dotColor="info"
            />
            <div style={{ height: 14 }} />
            <div className="afcfta-card">
              <BankingInfoPanel language={language} countries={countries} />
            </div>
          </div>
        );

      case 'tools':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader
              title={language === 'fr' ? "Outils d'Analyse" : 'Analysis Tools'}
              subtitle={language === 'fr' ? 'Convertisseurs, recherche HS, IA' : 'Converters, HS search, AI'}
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
              title={language === 'fr' ? "Règles d'Origine ZLECAf" : 'AfCFTA Rules of Origin'}
              subtitle={
                language === 'fr'
                  ? "Critères d'éligibilité au tarif préférentiel"
                  : 'Preferential tariff eligibility criteria'
              }
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
              title={language === 'fr' ? 'Profils Pays' : 'Country Profiles'}
              subtitle={
                language === 'fr'
                  ? 'Données économiques et commerciales par pays'
                  : 'Economic and trade data by country'
              }
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

  const sidebarCollapsed =
    typeof window !== 'undefined' &&
    document.querySelector('.afcfta-sidebar.collapsed') !== null;

  return (
    <>
      <div className="kente-band" />
      <div className="afcfta-layout">
        <Toaster />

      {/* Sidebar navigation */}
      <aside style={{position:'fixed',top:0,left:0,height:'100vh',width:228,zIndex:201,background:'linear-gradient(180deg,#0e1620,#0a1018)',borderRight:'1px solid rgba(200,83,26,0.15)',display:'flex',flexDirection:'column',overflowY:'auto',overflowX:'hidden'}}>
        <AfcftaTopbar
          active={getTopbarActiveTab()}
          onTabChange={handleTabChange}
          language={language}
          mobileOpen={mobileMenuOpen}
          onMobileOpen={() => setMobileMenuOpen(true)}
          onMobileClose={() => setMobileMenuOpen(false)}
        />
      </aside>

      {/* Main content area */}
      <main className="afcfta-main" id="afcfta-main-content" style={{ marginLeft: 228 }}>
        <div className="afcfta-shell zellige-najm">
          {/* KPI Row - dashboard uniquement */}
          {activeTab === 'dashboard' && (
            <KpiRow language={language} stats={stats} />
          )}

          {/* Offline banner — non-dashboard tabs when backend is down */}
          {backendOnline === false && activeTab !== 'dashboard' && (
            <div className="info-panel zellige-arabesque" style={{ marginBottom: 20, borderColor: 'rgba(200,16,46,0.25)' }}>
              <div className="info-panel-accent" style={{ background: 'var(--af-red)' }} />
              <div className="info-panel-title">
                {language === 'fr' ? '⚡ Serveur hors ligne' : '⚡ Server offline'}
              </div>
              <div className="info-panel-body">
                {language === 'fr'
                  ? 'Démarrez le backend (port 8000) pour charger les données de ce module. Les données tarifaires, statistiques et outils nécessitent le serveur API.'
                  : 'Start the backend server (port 8000) to load data for this module. Tariff data, statistics and tools require the API server.'}
              </div>
            </div>
          )}

          {/* Contenu principal */}
          {renderContent()}
        </div>
      </main>
    </div>
    </>
  );
}

export default App;
