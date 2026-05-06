import React from "react";
import {
  LayoutDashboard,
  Calculator,
  BarChart3,
  Target,
  Factory,
  Ship,
  Landmark,
  Wrench,
  FileCheck,
  Globe2,
} from "lucide-react";

const NAV_ITEMS = (isFrench) => [
  { id: "dashboard", label: isFrench ? "Tableau de bord" : "Dashboard", icon: LayoutDashboard },
  { id: "calculator", label: isFrench ? "Calculateur" : "Calculator", icon: Calculator },
  { id: "stats", label: isFrench ? "Statistiques" : "Statistics", icon: BarChart3 },
  { id: "opps", label: isFrench ? "Opportunités" : "Opportunities", icon: Target },
  { id: "production", label: isFrench ? "Production" : "Production", icon: Factory },
  { id: "logistics", label: isFrench ? "Logistique" : "Logistics", icon: Ship },
  { id: "banking", label: isFrench ? "Banque" : "Banking", icon: Landmark },
  { id: "tools", label: isFrench ? "Outils" : "Tools", icon: Wrench },
  { id: "roo", label: isFrench ? "Règles d'Origine" : "Rules of Origin", icon: FileCheck },
  { id: "profiles", label: isFrench ? "Profils Pays" : "Country Profiles", icon: Globe2 },
];

export default function TopHeader({ 
  active = "dashboard", 
  onTabChange, 
  language = "fr" 
}) {
  const isFrench = language === "fr";
  const navItems = NAV_ITEMS(isFrench);

  const handleTab = (id) => {
    onTabChange && onTabChange("tab", id);
  };

  const now = new Date();
  const dateStr = now.toLocaleDateString(isFrench ? "fr-FR" : "en-US", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
  const timeStr = now.toLocaleTimeString(isFrench ? "fr-FR" : "en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <header className="afcfta-topHeader">
      {/* Top bar with timestamp and platform name */}
      <div className="afcfta-topHeader__bar">
        <div className="afcfta-topHeader__timestamp">
          {dateStr}, {timeStr}
        </div>
        <div className="afcfta-topHeader__brand">
          <span className="afcfta-topHeader__brandIcon">☀</span>
          <span className="afcfta-topHeader__brandName">
            AfCFTA Intelligence Platform
          </span>
        </div>
        <div className="afcfta-topHeader__lang">
          <button
            className={`afcfta-langBtn ${isFrench ? "active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "fr")}
          >
            Français
          </button>
          <button
            className={`afcfta-langBtn ${!isFrench ? "active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "en")}
          >
            English
          </button>
        </div>
      </div>

      {/* Navigation tabs in a horizontal line */}
      <nav className="afcfta-topHeader__nav">
        {navItems.map(({ id, label, icon: Icon }) => {
          const isActive = active === id;
          return (
            <button
              key={id}
              onClick={() => handleTab(id)}
              className={`afcfta-navTab ${isActive ? "active" : ""}`}
              role="tab"
              aria-selected={isActive}
            >
              <Icon size={16} />
              <span>{label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
}
