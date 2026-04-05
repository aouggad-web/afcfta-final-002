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
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";

const GROUPS = (isFrench) => [
  {
    label: isFrench ? "Principal" : "Main",
    items: [
      { id: "dashboard", label: isFrench ? "Tableau de bord" : "Dashboard", icon: LayoutDashboard },
      { id: "calculator", label: isFrench ? "Calculateur" : "Calculator", icon: Calculator },
    ],
  },
  {
    label: isFrench ? "Analyses" : "Analytics",
    items: [
      { id: "stats", label: isFrench ? "Statistiques" : "Statistics", icon: BarChart3 },
      { id: "opps", label: isFrench ? "Opportunités" : "Opportunities", icon: Target },
      { id: "production", label: isFrench ? "Production" : "Production", icon: Factory },
    ],
  },
  {
    label: isFrench ? "Opérations" : "Operations",
    items: [
      { id: "logistics", label: isFrench ? "Logistique" : "Logistics", icon: Ship },
      { id: "banking", label: isFrench ? "Banque" : "Banking", icon: Landmark },
      { id: "tools", label: isFrench ? "Outils" : "Tools", icon: Wrench },
    ],
  },
  {
    label: isFrench ? "Référence" : "Reference",
    items: [
      { id: "roo", label: isFrench ? "Règles d'Origine" : "Rules of Origin", icon: FileCheck },
      { id: "profiles", label: isFrench ? "Profils Pays" : "Country Profiles", icon: Globe2 },
    ],
  },
];

export default function AfcftaTopbar({
  active = "dashboard",
  onTabChange,
  language = "fr",
  collapsed = false,
  onToggleCollapse,
  mobileOpen = false,
  onMobileOpen,
  onMobileClose,
}) {
  const isFrench = language === "fr";
  const groups = GROUPS(isFrench);

  const handleTab = (id) => {
    onTabChange && onTabChange("tab", id);
  };

  return (
    <>
      <div className="afcfta-mobile-topbar">
        <button
          onClick={onMobileOpen}
          className="afcfta-btn-sm afcfta-btn-secondary"
          style={{ padding: "8px", borderRadius: "10px", flexShrink: 0 }}
          aria-label={isFrench ? "Ouvrir le menu" : "Open menu"}
        >
          <Menu size={18} />
        </button>

        <div className="afcfta-mobile-topbar__brand">
          <div className="afcfta-mobile-topbar__icon">🌍</div>
          <div className="afcfta-mobile-topbar__text">
            <span className="afcfta-mobile-topbar__title">
              {isFrench ? "ZLECAf Intelligence" : "AfCFTA Intelligence"}
            </span>
            <span className="afcfta-mobile-topbar__subtitle">
              {isFrench ? "Trade · Customs · Logistics" : "Trade · Customs · Logistics"}
            </span>
          </div>
        </div>

        <div className="afcfta-mobile-topbar__lang">
          <button
            className={`afcfta-btn-sm ${isFrench ? "afcfta-btn" : "afcfta-btn-secondary"}`}
            onClick={() => onTabChange && onTabChange("language", "fr")}
            style={{ padding: "5px 8px", fontSize: "11px" }}
          >
            FR
          </button>
          <button
            className={`afcfta-btn-sm ${!isFrench ? "afcfta-btn" : "afcfta-btn-secondary"}`}
            onClick={() => onTabChange && onTabChange("language", "en")}
            style={{ padding: "5px 8px", fontSize: "11px" }}
          >
            EN
          </button>
        </div>
      </div>

      {mobileOpen && <div className="afcfta-sidebar-overlay" onClick={onMobileClose} />}

      <aside
        className={`afcfta-sidebar ${collapsed ? "collapsed" : ""} ${mobileOpen ? "mobile-open" : ""}`}
        role="navigation"
        aria-label={isFrench ? "Menu principal" : "Main menu"}
      >
        <div className="afcfta-sidebar-logo">
          <div className="afcfta-sidebar-icon">🌍</div>

          <div className="afcfta-sidebar-title">
            <h1>{isFrench ? "ZLECAf" : "AfCFTA"}</h1>
            <p>{isFrench ? "Intelligence Commerciale" : "Trade Intelligence"}</p>
          </div>

          <button
            onClick={onMobileClose}
            className="afcfta-mobile-close"
            aria-label={isFrench ? "Fermer" : "Close"}
          >
            <X size={16} />
          </button>
        </div>

        <div className="afcfta-sidebar-badges">
          <span className="afcfta-badge">🌍 {isFrench ? "54 pays ZLECAf" : "54 AfCFTA members"}</span>
          <span className="afcfta-badge">📊 {isFrench ? "229 519 positions" : "229,519 tariff lines"}</span>
          <span className="afcfta-badge">✅ {isFrench ? "Données authentiques" : "Authentic data"}</span>
        </div>

        <nav className="afcfta-sidebar-nav" aria-label={isFrench ? "Navigation principale" : "Main navigation"}>
          {groups.map((group) => (
            <div key={group.label} className="afcfta-nav-group">
              <div className="afcfta-nav-group-label">{group.label}</div>

              {group.items.map(({ id, label, icon: Icon }) => {
                const isActive = active === id;
                return (
                  <button
                    key={id}
                    onClick={() => handleTab(id)}
                    className={`afcfta-nav-item ${isActive ? "active" : ""}`}
                    role="tab"
                    aria-selected={isActive}
                    title={label}
                  >
                    <span className="afcfta-nav-icon">
                      <Icon size={15} />
                    </span>
                    <span className="afcfta-nav-label">{label}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="afcfta-sidebar-footer">
          <div className="afcfta-lang-switch" aria-label={isFrench ? "Langue" : "Language"}>
            <button
              className={`afcfta-btn-sm ${isFrench ? "afcfta-btn" : "afcfta-btn-secondary"}`}
              onClick={() => onTabChange && onTabChange("language", "fr")}
              style={{ flex: 1, padding: "6px 0", fontSize: "12px", textAlign: "center" }}
              aria-pressed={isFrench}
            >
              🇫🇷 FR
            </button>

            <button
              className={`afcfta-btn-sm ${!isFrench ? "afcfta-btn" : "afcfta-btn-secondary"}`}
              onClick={() => onTabChange && onTabChange("language", "en")}
              style={{ flex: 1, padding: "6px 0", fontSize: "12px", textAlign: "center" }}
              aria-pressed={!isFrench}
            >
              🇬🇧 EN
            </button>
          </div>

          <button
            className="afcfta-sidebar-toggle"
            onClick={onToggleCollapse}
            aria-label={collapsed ? (isFrench ? "Développer" : "Expand") : isFrench ? "Réduire" : "Collapse"}
            style={{ marginTop: 6 }}
          >
            {collapsed ? (
              <ChevronRight size={14} />
            ) : (
              <>
                <ChevronLeft size={14} />
                <span className="afcfta-sidebar-toggle-label" style={{ fontSize: 11 }}>
                  {isFrench ? "Réduire" : "Collapse"}
                </span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
