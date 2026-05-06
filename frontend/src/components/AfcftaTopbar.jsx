import React, { useState } from "react";
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
  Menu,
  Moon,
  Sun,
  X,
} from "lucide-react";

/* ─── Flat nav items ─────────────────────────────────────────── */
const NAV_ITEMS = (isFrench) => [
  { id: "dashboard",  label: isFrench ? "Tableau de bord" : "Dashboard",        icon: LayoutDashboard },
  { id: "calculator", label: isFrench ? "Calculateur"      : "Calculator",       icon: Calculator },
  { id: "stats",      label: isFrench ? "Statistiques"     : "Statistics",       icon: BarChart3 },
  { id: "opps",       label: isFrench ? "Opportunités"     : "Opportunities",    icon: Target },
  { id: "production", label: isFrench ? "Production"       : "Production",       icon: Factory },
  { id: "logistics",  label: isFrench ? "Logistique"       : "Logistics",        icon: Ship },
  { id: "banking",    label: isFrench ? "Banque"           : "Banking",          icon: Landmark },
  { id: "tools",      label: isFrench ? "Outils"           : "Tools",            icon: Wrench },
  { id: "roo",        label: isFrench ? "Règles d'Origine" : "Rules of Origin",  icon: FileCheck },
  { id: "profiles",   label: isFrench ? "Profils Pays"     : "Country Profiles", icon: Globe2 },
];

/* ─── Horizontal topbar component ───────────────────────────── */
export default function AfcftaTopbar({ active = "dashboard", onTabChange, language = "fr", theme = "dark", onThemeToggle }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const isFrench = language === "fr";
  const isLight = theme === "light";
  const items = NAV_ITEMS(isFrench);

  const handleTab = (id) => {
    onTabChange && onTabChange("tab", id);
    setMobileOpen(false);
  };

  return (
    <header className="afcfta-topHeader" role="banner">
      {/* ── Brand + language bar ── */}
      <div className="afcfta-topHeader__bar">
        <div className="afcfta-topHeader__brand">
          <div className="afcfta-topHeader__brandIcon">🌍</div>
          <span className="afcfta-topHeader__brandName">
            {isFrench ? "ZLECAf Intelligence" : "AfCFTA Intelligence"}
          </span>
        </div>

        {/* Mobile menu toggle */}
        <button
          className="afcfta-btn-sm afcfta-btn-secondary afcfta-topHeader__menuBtn"
          onClick={() => setMobileOpen((o) => !o)}
          aria-label={mobileOpen ? "Fermer le menu" : "Ouvrir le menu"}
          style={{ padding: "8px", borderRadius: "8px" }}
          aria-expanded={mobileOpen}
          aria-controls="afcfta-mobile-nav"
          id="afcfta-mobile-menu-btn"
        >
          {mobileOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        <div className="afcfta-topHeader__lang">
          {onThemeToggle && (
            <button
              className="afcfta-themeToggle"
              onClick={onThemeToggle}
              aria-label={isFrench
                ? (isLight ? "Activer le mode sombre" : "Activer le mode clair")
                : (isLight ? "Switch to dark mode" : "Switch to light mode")}
              title={isFrench
                ? (isLight ? "Mode sombre" : "Mode clair")
                : (isLight ? "Dark mode" : "Light mode")}
              data-testid="theme-toggle-btn"
            >
              {isLight ? <Moon size={16} /> : <Sun size={16} />}
            </button>
          )}
          <button
            className={`afcfta-langBtn ${isFrench ? "active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "fr")}
            aria-pressed={isFrench}
          >
            🇫🇷 FR
          </button>
          <button
            className={`afcfta-langBtn ${!isFrench ? "active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "en")}
            aria-pressed={!isFrench}
          >
            🇬🇧 EN
          </button>
        </div>
      </div>

      {/* ── Horizontal nav tabs ── */}
      <nav
        className="afcfta-topHeader__nav"
        aria-label={isFrench ? "Navigation principale" : "Main navigation"}
      >
        {items.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => handleTab(id)}
            className={`afcfta-navTab ${active === id ? "active" : ""}`}
            role="tab"
            aria-selected={active === id}
          >
            <Icon size={15} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      {/* ── Mobile dropdown nav ── */}
      {mobileOpen && (
        <>
          <div
            className="afcfta-sidebar-overlay"
            onClick={() => setMobileOpen(false)}
            style={{
              position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
              zIndex: 49, backdropFilter: "blur(2px)",
            }}
          />
          <div
            id="afcfta-mobile-nav"
            className="afcfta-mobile-nav-dropdown"
            style={{ display: "block" }}
          >
            <div className="afcfta-mobile-nav-list">
              {items.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => handleTab(id)}
                  className={`afcfta-mobile-nav-item ${active === id ? "active" : ""}`}
                  role="tab"
                  aria-selected={active === id}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </header>
  );
}
