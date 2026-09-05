import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import AfcftaSidebar from './components/AfcftaSidebar';
import { Production } from './components/production';
import { AuthProvider } from './context/AuthContext';
import AuthModal from './components/auth/AuthModal';
import FinanceTab from './components/finance/FinanceTab';
import ContactTab from './components/contact/ContactTab';
import OpportunityReportTab from './components/reports/OpportunityReportTab';
import BusinessAtlasModule from './components/tools/BusinessAtlasModule';
import RegulatoryComplianceTab from './components/regulatory/RegulatoryComplianceTab';
import './styles/index.css';

// Placeholder for modules not yet implemented
const ModulePlaceholder = ({ name }) => (
  <div style={{ padding: '40px', textAlign: 'center' }}>
    <h2>{name}</h2>
    <p>Module en développement — Intégration en cours</p>
  </div>
);

function App() {
  const [activeTab, setActiveTab] = useState('production');
  const [language, setLanguage] = useState(() => localStorage.getItem('language') || 'fr');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [authModalOpen, setAuthModalOpen] = useState(false);

  useEffect(() => {
    document.documentElement.className = `theme-${theme}`;
  }, [theme]);

  const handleTabChange = (type, value) => {
    if (type === 'tab') {
      setActiveTab(value);
    } else if (type === 'language') {
      setLanguage(value);
      localStorage.setItem('language', value);
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <ModulePlaceholder name="Tableau de bord" />;
      case 'calculator':
        return <ModulePlaceholder name="Calculateur ZLECAf" />;
      case 'stats':
        return <ModulePlaceholder name="Statistiques Commerciales" />;
      case 'production':
        return <Production />;
      case 'logistics':
        return <ModulePlaceholder name="Logistique et Transport" />;
      case 'banking':
        return <FinanceTab />;
      case 'tools':
        return <BusinessAtlasModule />;
      case 'roo':
        return <RegulatoryComplianceTab />;
      case 'profiles':
        return <ModulePlaceholder name="Profils Pays" />;
      case 'reports':
        return <OpportunityReportTab />;
      case 'contact':
        return <ContactTab />;
      default:
        return <ModulePlaceholder name={activeTab} />;
    }
  };

  return (
    <div className={`app theme-${theme}`}>
      <AfcftaSidebar
        active={activeTab}
        onTabChange={handleTabChange}
        language={language}
        theme={theme}
        onThemeToggle={toggleTheme}
        onOpenAuth={() => setAuthModalOpen(true)}
      />
      <main className="app-content">
        {renderContent()}
      </main>
      <AuthModal
        open={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        language={language}
      />
    </div>
  );
}

const root = createRoot(document.getElementById('root'));
root.render(
  <AuthProvider>
    <App />
  </AuthProvider>
);
