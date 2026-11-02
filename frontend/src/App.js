import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { DirectionProvider } from '@radix-ui/react-direction';
import { pick, isRtl } from './i18n/lang';
import { toast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';

import './styles/theme.css';
import './styles/theme-light.css';
import './styles/ambiance.css';
import './styles/rtl.css';

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
import OpportunityReportTab from './components/reports/OpportunityReportTab';
import ContactTab from './components/contact/ContactTab';
import AuthModal from './components/auth/AuthModal';
import { AuthProvider, useAuth } from './context/AuthContext';

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

// Onglets atteignables par « ?tab= » (raccourcis du manifest PWA).
const SHORTCUT_TABS = ['dashboard', 'calculator', 'reports'];

function App() {
  const { i18n } = useTranslation();
  const [countries, setCountries] = useState([]);
  // Onglet actif persisté en session : si la page se recharge (ex. websocket
  // HMR coupé par un proxy, mise à jour du service worker...), l'utilisateur
  // revient sur SON module au lieu d'être renvoyé au dashboard. sessionStorage
  // (pas localStorage) : une nouvelle visite repart du dashboard, un simple
  // rechargement conserve la place.
  const [activeTab, setActiveTab] = useState(() => {
    // Raccourcis de l'application installée (manifest.json « shortcuts ») :
    // « /?tab=calculator » ouvre directement le module demandé.
    const params = new URLSearchParams(window.location.search);
    const demande = params.get('tab');
    if (demande && SHORTCUT_TABS.includes(demande)) {
      // Lu une fois : un simple rechargement retrouve ensuite l'onglet de la session.
      params.delete('tab');
      const reste = params.toString();
      window.history.replaceState(
        null, '', window.location.pathname + (reste ? `?${reste}` : '') + window.location.hash
      );
      return demande;
    }
    return sessionStorage.getItem('zlecaf_active_tab') || 'dashboard';
  });
  useEffect(() => {
    sessionStorage.setItem('zlecaf_active_tab', activeTab);
  }, [activeTab]);
  const [language, setLanguage] = useState(i18n.language || 'fr');
  const [stats, setStats] = useState(null);
  const [backendOnline, setBackendOnline] = useState(null);

  // ── Gestion du thème (sombre / clair) ──
  const [theme, setTheme] = useState(() => localStorage.getItem('zlecaf_theme') || 'dark');
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const { recovery } = useAuth() || {};

  // Arrivée par le lien « mot de passe oublié » : ouvrir la modale sur le
  // formulaire de nouveau mot de passe.
  useEffect(() => {
    if (recovery) setAuthModalOpen(true);
  }, [recovery]);

  // Le lien "Démarrer un plan" de pricing.html renvoie ici avec
  // `#auth=login&next=<écran>` quand le visiteur n'est pas connecté. On lit ce
  // fragment au chargement pour ouvrir la modale et mémoriser la destination
  // post-connexion — sans introduire de routage par URL dans une app qui n'en
  // a pas et sans exiger d'écran /login (qui renverrait un 404).
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const raw = window.location.hash.replace(/^#/, '');
    if (!raw) return;
    const params = new URLSearchParams(raw);
    if (params.get('auth') === 'login') {
      setAuthModalOpen(true);
      // Whitelist explicite des destinations post-connexion : stocker « next »
      // brut laisserait la clé indéfiniment dans sessionStorage si la valeur ne
      // correspond à aucun handler, avec des ouvertures ultérieures de la modale
      // pouvant déclencher une navigation surprise. On limite aux cibles
      // effectivement gérées, et on purge sinon pour repartir propre.
      const POST_LOGIN_TARGETS = ['pricing'];
      const next = params.get('next');
      if (next && POST_LOGIN_TARGETS.includes(next)) {
        sessionStorage.setItem('zlecaf_post_login_target', next);
      } else {
        sessionStorage.removeItem('zlecaf_post_login_target');
      }
      // Efface le fragment pour ne pas rouvrir la modale au moindre reload.
      window.history.replaceState(null, '', window.location.pathname + window.location.search);
    }
  }, []);
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
        contact: 'contact',
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
      contact: 'contact',
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
        gdp: 2.7e12,
        trade: 235e9,
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
              title={pick(language, 'Calculateur de Tarifs Douaniers', 'Customs Tariff Calculator', 'حاسبة التعريفات الجمركية')}
              subtitle={
                pick(language, 'Calculs basés sur les données officielles des administrations douanières', 'Calculations based on official customs data', 'حسابات مبنية على البيانات الرسمية لإدارات الجمارك')
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
              title={pick(language, 'Statistiques Commerciales', 'Trade Statistics', 'الإحصائيات التجارية')}
              subtitle={pick(language, 'Données OEC, COMTRADE, UNCTAD', 'OEC, COMTRADE, UNCTAD Data', 'بيانات OEC وCOMTRADE والأونكتاد')}
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
              title={pick(language, 'Production Africaine', 'African Production', 'الإنتاج الأفريقي')}
              subtitle={
                pick(language, 'Données FAOSTAT et capacités industrielles', 'FAOSTAT data and industrial capacity', 'بيانات FAOSTAT والقدرات الصناعية')
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
              title={pick(language, 'Logistique & Infrastructure', 'Logistics & Infrastructure', 'اللوجستيك والبنية التحتية')}
              subtitle={
                pick(language, 'Ports, corridors, connectivité maritime', 'Ports, corridors, maritime connectivity', 'الموانئ والممرات والربط البحري')
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
              title={pick(language, 'Finance – Banque & Assurance', 'Finance – Banking & Insurance', 'التمويل – البنوك والتأمين')}
              subtitle={
                pick(language, 'Change, domiciliation, financement du commerce, assurance-crédit export', 'Forex, domiciliation, trade finance, export credit insurance', 'الصرف، التوطين البنكي، تمويل التجارة، تأمين ائتمان الصادرات')
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
              title={pick(language, "Outils d'Analyse", 'Analysis Tools', 'أدوات التحليل')}
              subtitle={pick(language, 'Convertisseurs, recherche HS, IA', 'Converters, HS search, AI', 'المحوّلات، البحث برمز SH، الذكاء الاصطناعي')}
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
              title={pick(language, "Règles d'Origine ZLECAf", 'AfCFTA Rules of Origin', 'قواعد المنشأ في زليكاف')}
              subtitle={
                pick(language, "Critères d'éligibilité au tarif préférentiel", 'Preferential tariff eligibility criteria', 'معايير الأهلية للتعريفة التفضيلية')
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
              title={pick(language, 'Profils Pays', 'Country Profiles', 'ملفات البلدان')}
              subtitle={
                pick(language, 'Données économiques et commerciales par pays', 'Economic and trade data by country', 'البيانات الاقتصادية والتجارية حسب البلد')
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
              title={pick(language, 'Opportunités', 'Opportunities', 'الفرص')}
              subtitle={
                pick(language, 'Scénarios S1–S4, recherche de marchés, rapport bilatéral et substitution SH6 (S5)', 'S1–S4 scenarios, market finding, bilateral report and HS6 substitution (S5)', 'السيناريوهات S1–S4، البحث عن الأسواق، التقرير الثنائي وإحلال الواردات على مستوى SH6 (S5)')
              }
              dotColor="copper"
            />
            <div style={{ height: 20 }} />
            <div className="afcfta-card">
              <OpportunityReportTab countries={countries} language={language} />
            </div>
          </div>
        );

      case 'contact':
        return (
          <div className="afcfta-section afcfta-fadeIn">
            <SectionHeader
              title={pick(language, 'Contact', 'Contact', 'اتصل بنا')}
              subtitle={
                pick(language, 'Une question, une suggestion ? Écrivez-nous.', 'A question, a suggestion? Write to us.', 'سؤال أو اقتراح؟ راسلونا.')
              }
              dotColor="success"
            />
            <div style={{ height: 20 }} />
            <ContactTab language={language} />
          </div>
        );

      default:
        return null;
    }
  };

  // Les primitives Radix (onglets, listes, menus) se posent en dir="ltr"
  // par défaut : sans ce fournisseur, elles ignoreraient l'arabe.
  return (
    <DirectionProvider dir={isRtl(language) ? 'rtl' : 'ltr'}>
      <div className="kente-band" />
      <div className="afcfta-layout-v2">
        <Toaster />
        <AuthModal
          open={authModalOpen}
          onClose={() => {
            setAuthModalOpen(false);
            // Fermeture volontaire : annule toujours la destination différée.
            sessionStorage.removeItem('zlecaf_post_login_target');
          }}
          onAuthenticated={() => {
            setAuthModalOpen(false);
            // Seule une authentification réussie peut déclencher la navigation
            // différée. La clé est purgée dans tous les cas.
            const target = sessionStorage.getItem('zlecaf_post_login_target');
            sessionStorage.removeItem('zlecaf_post_login_target');
            if (target === 'pricing') {
              window.location.href = '/pricing.html';
            }
          }}
          language={language}
        />

        {/* Desktop sidebar — hidden on mobile via CSS */}
        <AfcftaSidebar
          active={getTopbarActiveTab()}
          onTabChange={handleTabChange}
          language={language}
          theme={theme}
          onThemeToggle={toggleTheme}
          onOpenAuth={() => setAuthModalOpen(true)}
        />

        {/* Horizontal top navigation (mobile + tablet) */}
        <AfcftaTopbar
          active={getTopbarActiveTab()}
          onTabChange={handleTabChange}
          language={language}
          theme={theme}
          onThemeToggle={toggleTheme}
          onOpenAuth={() => setAuthModalOpen(true)}
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
                <strong style={{ color: 'var(--danger)' }}>
                  {pick(language, 'Serveur hors ligne', 'Server offline', 'الخادم غير متصل')}
                </strong>
                {' — '}
                {pick(language, 'Démarrez le backend (port 8000) pour accéder aux données.', 'Start the backend (port 8000) to access data.', 'شغّل الخادم الخلفي (المنفذ 8000) للوصول إلى البيانات.')}
              </span>
            </div>
          )}

          {/* Contenu principal */}
          {renderContent()}
        </div>
      </main>
    </div>
    </DirectionProvider>
  );
}

export default function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}
