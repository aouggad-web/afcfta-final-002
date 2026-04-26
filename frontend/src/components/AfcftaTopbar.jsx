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
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";

/* ─── Navigation groups ─────────────────────────────────────── */
const GROUPS = (isFrench) => [
  {
    label: isFrench ? "Principal" : "Main",
    items: [
      { id: "dashboard",   label: isFrench ? "Tableau de bord"    : "Dashboard",         icon: LayoutDashboard },
      { id: "calculator",  label: isFrench ? "Calculateur"         : "Calculator",        icon: Calculator },
    ],
  },
  {
    label: isFrench ? "Analyses" : "Analytics",
    items: [
      { id: "stats",       label: isFrench ? "Statistiques"        : "Statistics",        icon: BarChart3 },
      { id: "opps",        label: isFrench ? "Opportunités"        : "Opportunities",     icon: Target },
      { id: "production",  label: isFrench ? "Production"          : "Production",        icon: Factory },
    ],
  },
  {
    label: isFrench ? "Opérations" : "Operations",
    items: [
      { id: "logistics",   label: isFrench ? "Logistique"          : "Logistics",         icon: Ship },
      { id: "banking",     label: isFrench ? "Banque"              : "Banking",           icon: Landmark },
      { id: "tools",       label: isFrench ? "Outils"              : "Tools",             icon: Wrench },
    ],
  },
  {
    label: isFrench ? "Référence" : "Reference",
    items: [
      { id: "roo",         label: isFrench ? "Règles d'Origine"    : "Rules of Origin",   icon: FileCheck },
      { id: "profiles",    label: isFrench ? "Profils Pays"        : "Country Profiles",  icon: Globe2 },
    ],
  },
];

/* ─── Sidebar component ─────────────────────────────────────── */
export default function AfcftaTopbar({ active = "dashboard", onTabChange, language = "fr" }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isFrench = language === "fr";
  const groups = GROUPS(isFrench);

  const handleTab = (id) => {
    onTabChange && onTabChange("tab", id);
    setMobileOpen(false);
  };

  /* ── Mobile topbar strip ── */
  const mobileBar = (
    <div className="afcfta-mobile-topbar">
      <button
        onClick={() => setMobileOpen(true)}
        className="afcfta-btn-sm afcfta-btn-secondary"
        style={{ padding: "8px", borderRadius: "8px", flexShrink: 0 }}
        aria-label="Ouvrir le menu"
      >
        <Menu size={18} />
      </button>

      <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1, overflow: "hidden" }}>
        <div
          style={{
            width: 30, height: 30, flexShrink: 0,
            background: "linear-gradient(135deg,var(--terra),var(--gold))",
            borderRadius: 8,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16,
          }}
        >
          🌍
        </div>
        <span style={{ fontWeight: 800, fontSize: 13, color: "var(--gold)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {isFrench ? "ZLECAf Intelligence" : "AfCFTA Intelligence"}
        </span>
      </div>

      <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
        <button
          className={`afcfta-btn-sm ${isFrench ? "afcfta-btn" : "afcfta-btn-secondary"}`}
          onClick={() => onTabChange && onTabChange("language", "fr")}
          style={{ padding: "5px 8px", fontSize: "11px" }}
        >FR</button>
        <button
          className={`afcfta-btn-sm ${!isFrench ? "afcfta-btn" : "afcfta-btn-secondary"}`}
          onClick={() => onTabChange && onTabChange("language", "en")}
          style={{ padding: "5px 8px", fontSize: "11px" }}
        >EN</button>
      </div>
    </div>
  );

  /* ── Sidebar inner content (shared desktop + mobile) ── */
  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="afcfta-sidebar-logo">
        <div className="afcfta-sidebar-icon">🌍</div>
        <div className="afcfta-sidebar-title">
          <h1>{isFrench ? "ZLECAf" : "AfCFTA"}</h1>
          <p>{isFrench ? "Intelligence Commerciale" : "Trade Intelligence"}</p>
        </div>
        {/* Close button — mobile only */}
        <button
          onClick={() => setMobileOpen(false)}
          style={{
            display: "none", // shown via media query in JSX
            position: "absolute", right: 10, top: 10,
            background: "none", border: "none", color: "var(--afcfta-muted)",
            cursor: "pointer", padding: 4,
          }}
          className="afcfta-mobile-close"
          aria-label="Fermer"
        >
          <X size={16} />
        </button>
      </div>

      {/* Badges */}
      <div className="afcfta-sidebar-badges">
        <span className="afcfta-badge">🌍 {isFrench ? "54 pays ZLECAf" : "54 AfCFTA members"}</span>
        <span className="afcfta-badge">📊 {isFrench ? "229 519 positions" : "229,519 tariff lines"}</span>
        <span className="afcfta-badge">✅ {isFrench ? "Données authentiques" : "Authentic data"}</span>
      </div>

      {/* Nav groups */}
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

      {/* Footer */}
      <div className="afcfta-sidebar-footer">
        {/* Language switch */}
        <div className="afcfta-lang-switch" aria-label={isFrench ? "Langue" : "Language"}>
          <button
            className={`afcfta-langBtn ${isFrench ? "active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "fr")}
            style={{ flex: 1, padding: "6px 0", fontSize: "12px", textAlign: "center" }}
            aria-pressed={isFrench}
          >
            🇫🇷 FR
          </button>
          <button
            className={`afcfta-langBtn ${!isFrench ? "active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "en")}
            style={{ flex: 1, padding: "6px 0", fontSize: "12px", textAlign: "center" }}
            aria-pressed={!isFrench}
          >
            🇬🇧 EN
          </button>
        </div>

        {/* Collapse toggle — desktop only */}
        <button
          className="afcfta-sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          style={{ marginTop: 6 }}
        >
          {collapsed
            ? <ChevronRight size={14} />
            : <><ChevronLeft size={14} /><span className="afcfta-sidebar-toggle-label" style={{ fontSize: 11 }}>{isFrench ? "Réduire" : "Collapse"}</span></>
          }
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile topbar strip */}
      {mobileBar}

      {/* Overlay — mobile */}
      {mobileOpen && (
        <div
          className="afcfta-sidebar-overlay"
          onClick={() => setMobileOpen(false)}
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
            zIndex: 99, backdropFilter: "blur(2px)",
          }}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`afcfta-sidebar ${collapsed ? "collapsed" : ""} ${mobileOpen ? "mobile-open" : ""}`}
        role="navigation"
        aria-label={isFrench ? "Menu principal" : "Main menu"}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
