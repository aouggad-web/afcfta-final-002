import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

import './styles/theme.css';
import './styles/theme-light.css';

import AfcftaTopbar from './components/AfcftaTopbar';
import AfcftaSidebar from './components/AfcftaSidebar';
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
import FinanceTab from './components/finance/FinanceTab';
import OpportunitiesTab from './components/opportunities/OpportunitiesTab';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
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
  // Onglet actif persisté en session : si la page se recharge (ex. websocket
  // HMR coupé par un proxy, mise à jour du service worker...), l'utilisateur
  // revient sur SON module au lieu d'être renvoyé au dashboard. sessionStorage
  // (pas localStorage) : une nouvelle visite repart du dashboard, un simple
  // rechargement conserve la place.
  const [activeTab, setActiveTab] = useState(
    () => sessionStorage.getItem('zlecaf_active_tab') || 'dashboard'
  );
  useEffect(() => {
    sessionStorage.setItem('zlecaf_active_tab', activeTab);
  }, [activeTab]);
  const [language, setLanguage] = useState(i18n.language || 'fr');
  const [stats, setStats] = useState(null);
  const [backendOnline, setBackendOnline] = useState(null);

  // ── Gestion du thème (sombre / clair) ──
  const [theme, setTheme] = useState(() => localStorage.getItem('zlecaf_theme') || 'dark');
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'light') {
      root.classList.add('theme-light');
      document.body.classList.add('theme-light');
    } else {
      root.classList.remove('theme-light');
      document.body.classList.remove('theme-light');
    }
    localStorage.setItem('zlecaf_theme', theme);
  }, [theme]);
  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  const t = texts[language] || texts.fr;

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    i18n.changeLanguage(newLang);
  };

  // Navigation inter-modules (ex.: Statistiques → Opportunités avec pré-remplissage).
  useEffect(() => {
    const onGotoTab = (e) => {
      const tab = e?.detail?.tab;
      if (tab) setActiveTab(tab);
    };
    window.addEventListener('zlecaf:goto-tab', onGotoTab);
    return () => window.removeEventListener('zlecaf:goto-tab', onGotoTab);
  }, []);

  const handleTabChange = (type, value) => {
    if (type === 'tab') {
      const tabMapping = {
        dashboard: 'dashboard',
        calculator: 'calculator',
        stats: 'statistics',
        production: 'production',
        logistics: 'logistics',
        banking: 'banking',
        tools: 'tools',
        roo: 'rules',
        profiles: 'profiles',
        reports: 'reports',
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
      production: 'production',
      logistics: 'logistics',
      banking: 'banking',
      tools: 'tools',
      rules: 'roo',
      profiles: 'profiles',
      reports: 'reports',
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
            <div style={{ height: 20 }} />
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
            <div style={{ height: 20 }} />
            <div className="afcfta-card">
              <StatisticsTab language={language} />
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
            <div style={{ height: 20 }} />
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
            <div style={{ height: 20 }} />
            <div className="afcfta-card">
              <LogisticsTab language={language} />
            </div>
          </div>
        );

      case 'banking':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader
              title={language === 'fr' ? 'Finance – Banque & Assurance' : 'Finance – Banking & Insurance'}
              subtitle={
                language === 'fr'
                  ? 'Change, domiciliation, financement du commerce, assurance-crédit export'
                  : 'Forex, domiciliation, trade finance, export credit insurance'
              }
              dotColor="info"
            />
            <div style={{ height: 20 }} />
            <FinanceTab language={language} countries={countries} />
          </div>
        );

      case 'tools':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader
              title={language === 'fr' ? "Outils d'Analyse" : 'Analysis Tools'}
              subtitle={language === 'fr' ? 'Convertisseurs, recherche HS, IA' : 'Converters, HS search, AI'}
            />
            <div style={{ height: 20 }} />
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
            <div style={{ height: 20 }} />
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
            <div style={{ height: 20 }} />
            <div className="afcfta-card">
              <CountryProfilesTab language={language} />
            </div>
          </div>
        );

      case 'reports':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader
              title={language === 'fr' ? 'Opportunités' : 'Opportunities'}
              subtitle={
                language === 'fr'
                  ? 'Substitution, simulateur ZLECAf, comparateur bilatéral, chaînes de valeur et analyse par produit'
                  : 'Substitution, AfCFTA simulator, bilateral comparator, value chains and product-level analysis'
              }
              dotColor="copper"
            />
            <div style={{ height: 20 }} />
            <div className="afcfta-card">
              <OpportunitiesTab language={language} />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <>
      <div className="kente-band" />
      <div className="afcfta-layout-v2">
        <Toaster />

        {/* Desktop sidebar — hidden on mobile via CSS */}
        <AfcftaSidebar
          active={getTopbarActiveTab()}
          onTabChange={handleTabChange}
          language={language}
          theme={theme}
          onThemeToggle={toggleTheme}
        />

        {/* Horizontal top navigation (mobile + tablet) */}
        <AfcftaTopbar
          active={getTopbarActiveTab()}
          onTabChange={handleTabChange}
          language={language}
          theme={theme}
          onThemeToggle={toggleTheme}
        />

      {/* Main content area */}
      <main className="afcfta-main-v2" id="afcfta-main-content">
        <div className="afcfta-shell zellige-najm">
          {/* KPI Row - dashboard uniquement */}
          {activeTab === 'dashboard' && (
            <KpiRow language={language} stats={stats} />
          )}

          {/* Offline banner — non-dashboard tabs when backend is down */}
          {backendOnline === false && activeTab !== 'dashboard' && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 16px',
              marginBottom: 18,
              borderRadius: 10,
              background: 'rgba(200,16,46,0.08)',
              border: '1px solid rgba(200,16,46,0.20)',
              fontSize: 13,
              color: 'var(--afcfta-muted)',
            }}>
              <span style={{ fontSize: 15 }}>⚡</span>
              <span>
                <strong style={{ color: '#e05070' }}>
                  {language === 'fr' ? 'Serveur hors ligne' : 'Server offline'}
                </strong>
                {' — '}
                {language === 'fr'
                  ? 'Démarrez le backend (port 8000) pour accéder aux données.'
                  : 'Start the backend (port 8000) to access data.'}
              </span>
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
