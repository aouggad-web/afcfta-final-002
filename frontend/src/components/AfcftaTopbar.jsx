import React from "react";
import { 
  LayoutDashboard, 
  Calculator, 
  BarChart3, 
  Target, 
  Factory, 
  Ship, 
  Wrench, 
  FileCheck, 
  Globe2 
} from "lucide-react";

export default function AfcftaTopbar({ active = "dashboard", onTabChange, language = "fr" }) {
  const tabs = [
    { id: "dashboard", label: language === 'fr' ? "Dashboard" : "Dashboard", icon: LayoutDashboard },
    { id: "calculator", label: language === 'fr' ? "Calculateur" : "Calculator", icon: Calculator },
    { id: "stats", label: language === 'fr' ? "Statistiques" : "Statistics", icon: BarChart3 },
    { id: "opps", label: language === 'fr' ? "Opportunités" : "Opportunities", icon: Target },
    { id: "production", label: language === 'fr' ? "Production" : "Production", icon: Factory },
    { id: "logistics", label: language === 'fr' ? "Logistique" : "Logistics", icon: Ship },
    { id: "tools", label: language === 'fr' ? "Outils" : "Tools", icon: Wrench },
    { id: "roo", label: language === 'fr' ? "Règles d'Origine" : "Rules of Origin", icon: FileCheck },
    { id: "profiles", label: language === 'fr' ? "Profils Pays" : "Country Profiles", icon: Globe2 },
  ];

  return (
    <div className="afcfta-topbar">
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 className="afcfta-title">
            <span className="afcfta-title-icon">🌍</span>
            Accord de la ZLECAf
          </h1>
          <div className="afcfta-subtitle">
            {language === 'fr' 
              ? "Plateforme d'intelligence commerciale africaine — droits, TVA, taxes totales, analytics."
              : "African trade intelligence platform — duties, VAT, total taxes, analytics."}
          </div>
          <div className="afcfta-badges">
            <span className="afcfta-badge">54 Pays Membres</span>
            <span className="afcfta-badge">1.3B+ Population</span>
          </div>
        </div>
        
        {/* Language switcher */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            className={`afcfta-btn-sm ${language === 'fr' ? 'afcfta-btn' : 'afcfta-btn-secondary'}`}
            onClick={() => onTabChange && onTabChange('language', 'fr')}
            style={{ padding: '6px 12px', fontSize: '12px' }}
          >
            🇫🇷 Français
          </button>
          <button 
            className={`afcfta-btn-sm ${language === 'en' ? 'afcfta-btn' : 'afcfta-btn-secondary'}`}
            onClick={() => onTabChange && onTabChange('language', 'en')}
            style={{ padding: '6px 12px', fontSize: '12px' }}
          >
            🇬🇧 English
          </button>
        </div>
      </div>

      <div className="afcfta-tabs">
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => onTabChange && onTabChange('tab', t.id)}
              className={`afcfta-tab ${active === t.id ? "active" : ""}`}
            >
              <Icon className="icon" size={14} />
              {t.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
