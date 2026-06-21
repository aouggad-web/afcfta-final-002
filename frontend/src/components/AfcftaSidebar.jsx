import React, { useState } from "react";
import {
  LayoutDashboard, Calculator, BarChart3, Target, Factory, Ship,
  Landmark, Wrench, FileCheck, Globe2, ChevronLeft, ChevronRight,
  Moon, Sun,
} from "lucide-react";
import { getAppLastUpdateLabel, getLastUpdateDateTime } from "./common/appLastUpdateLabel";

const NAV_ITEMS = (isFrench) => [
  { id: "dashboard",  label: isFrench ? "Tableau de bord" : "Dashboard",       icon: LayoutDashboard },
  { id: "calculator", label: isFrench ? "Calculateur"     : "Calculator",      icon: Calculator },
  { id: "stats",      label: isFrench ? "Statistiques"    : "Statistics",      icon: BarChart3 },
  { id: "opps",       label: isFrench ? "Opportunités"    : "Opportunities",   icon: Target },
  { id: "production", label: isFrench ? "Production"      : "Production",      icon: Factory },
  { id: "logistics",  label: isFrench ? "Logistique"      : "Logistics",       icon: Ship },
  { id: "banking",    label: isFrench ? "Banque"          : "Banking",         icon: Landmark },
  { id: "tools",      label: isFrench ? "Outils"          : "Tools",           icon: Wrench },
  { id: "roo",        label: isFrench ? "R. d'Origine"   : "Rules of Origin", icon: FileCheck },
  { id: "profiles",   label: isFrench ? "Profils"         : "Profiles",        icon: Globe2 },
];

export default function AfcftaSidebar({
  active = "dashboard",
  onTabChange,
  language = "fr",
  theme = "dark",
  onThemeToggle,
}) {
  const [collapsed, setCollapsed] = useState(false);
  const isFrench = language === "fr";
  const isLight = theme === "light";
  const appLastChange = import.meta.env.VITE_APP_LAST_CHANGE;
  const lastUpdateLabel = getAppLastUpdateLabel(language);
  const lastUpdateDateTime = getLastUpdateDateTime(appLastChange);
  const items = NAV_ITEMS(isFrench);

  const handleTab = (id) => {
    onTabChange && onTabChange("tab", id);
  };

  return (
    <aside className={`afcfta-sidebar${collapsed ? " collapsed" : ""}`}>
      {/* Logo */}
      <div className="afcfta-sidebar-logo">
        <div className="afcfta-sidebar-icon">🌍</div>
        <div className="afcfta-sidebar-title">
          <h1>{isFrench ? "ZLECAf" : "AfCFTA"}</h1>
          <p>{isFrench ? "Intelligence commerciale" : "Trade Intelligence"}</p>
          {appLastChange && (
            <p className="afcfta-appLastChange">
              {lastUpdateLabel} <time dateTime={lastUpdateDateTime}>{appLastChange}</time>
            </p>
          )}
        </div>
      </div>

      {/* Nav */}
      <nav className="afcfta-sidebar-nav" aria-label={isFrench ? "Navigation principale" : "Main navigation"}>
        {items.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => handleTab(id)}
            className={`afcfta-nav-item${active === id ? " active" : ""}`}
            role="tab"
            aria-selected={active === id}
            title={collapsed ? label : undefined}
          >
            <span className="afcfta-nav-icon">
              <Icon size={16} strokeWidth={1.7} />
            </span>
            <span className="afcfta-nav-label">{label}</span>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="afcfta-sidebar-footer">
        {/* Language + theme */}
        <div className="afcfta-lang-switch" style={{ marginBottom: 8 }}>
          <button
            className={`afcfta-langBtn${isFrench ? " active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "fr")}
            aria-pressed={isFrench}
          >FR</button>
          <button
            className={`afcfta-langBtn${!isFrench ? " active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "en")}
            aria-pressed={!isFrench}
          >EN</button>
          {onThemeToggle && (
            <button
              className="afcfta-themeToggle"
              onClick={onThemeToggle}
              aria-label={isFrench ? (isLight ? "Mode sombre" : "Mode clair") : (isLight ? "Dark mode" : "Light mode")}
              style={{ marginLeft: "auto" }}
            >
              {isLight ? <Moon size={14} /> : <Sun size={14} />}
            </button>
          )}
        </div>

        {/* Collapse toggle */}
        <button
          className="afcfta-sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? (isFrench ? "Développer" : "Expand") : (isFrench ? "Réduire" : "Collapse")}
        >
          {collapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
          <span className="afcfta-sidebar-toggle-label">
            {isFrench ? "Réduire" : "Collapse"}
          </span>
        </button>
      </div>
    </aside>
  );
}
