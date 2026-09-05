import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import AfcftaSidebar from './components/AfcftaSidebar';
import { Production } from './components/production';
import './styles/index.css';

// Simple Auth Context for basic user state management
const AuthContext = React.createContext(null);

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

function useAuth() {
  return React.useContext(AuthContext) || { user: null, setUser: () => {}, logout: () => {} };
}

// Placeholder components for other modules that exist in the codebase
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
  const { user } = useAuth();

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
      case 'production':
        return <Production />;
      case 'calculator':
        return <ModulePlaceholder name="Calculateur ZLECAf" />;
      case 'stats':
        return <ModulePlaceholder name="Statistiques Commerciales" />;
      case 'logistics':
        return <ModulePlaceholder name="Logistique et Transport" />;
      case 'banking':
        return <ModulePlaceholder name="Finance et Banque" />;
      case 'tools':
        return <ModulePlaceholder name="Outils" />;
      case 'roo':
        return <ModulePlaceholder name="Règles d'Origine" />;
      case 'profiles':
        return <ModulePlaceholder name="Profils Pays" />;
      case 'reports':
        return <ModulePlaceholder name="Opportunités" />;
      case 'contact':
        return <ModulePlaceholder name="Contact" />;
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
      />
      <main className="app-content">
        {renderContent()}
      </main>
    </div>
  );
}

const root = createRoot(document.getElementById('root'));
root.render(
  <AuthProvider>
    <App />
  </AuthProvider>
);
