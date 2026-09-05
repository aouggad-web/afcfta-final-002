import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import AfcftaSidebar from './components/AfcftaSidebar';
import { Production } from './components/production';
import './styles/index.css';

function App() {
  const [activeTab, setActiveTab] = useState('production');
  const [language, setLanguage] = useState('fr');
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
  }, []);

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
      default:
        return (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <h2>Module {activeTab}</h2>
            <p>Ce module est en développement.</p>
          </div>
        );
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
root.render(<App />);
