import React, { useState } from "react";
import {
  LayoutDashboard, Calculator, BarChart3, Factory, Ship,
  Landmark, Wrench, FileCheck, Globe2, ChevronLeft, ChevronRight,
  Moon, Sun, TrendingUp,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = (isFrench) => [
  { id: "dashboard",  label: isFrench ? "Tableau de bord" : "Dashboard",       icon: LayoutDashboard },
  { id: "calculator", label: isFrench ? "Calculateur"     : "Calculator",      icon: Calculator },
  { id: "stats",      label: isFrench ? "Statistiques"    : "Statistics",      icon: BarChart3 },
  { id: "production", label: isFrench ? "Production"      : "Production",      icon: Factory },
  { id: "logistics",  label: isFrench ? "Logistique"      : "Logistics",       icon: Ship },
  { id: "banking",    label: isFrench ? "Finance"         : "Finance",         icon: Landmark },
  { id: "tools",      label: isFrench ? "Outils"          : "Tools",           icon: Wrench },
  { id: "roo",        label: isFrench ? "R. d'Origine"   : "Rules of Origin", icon: FileCheck },
  { id: "profiles",   label: isFrench ? "Profils"         : "Profiles",        icon: Globe2 },
  { id: "reports",    label: isFrench ? "Opportunités"    : "Opportunities",   icon: TrendingUp },
  { id: "contact",    label: isFrench ? "Contact"         : "Contact",         icon: Mail },
];

export default function AfcftaSidebar({
  active = "dashboard",
  onTabChange,
  language = "fr",
  theme = "dark",
  onThemeToggle,
  onOpenAuth,
}) {
  const [collapsed, setCollapsed] = useState(false);
  const isFrench = language === "fr";
  const isLight = theme === "light";
  const items = NAV_ITEMS(isFrench);
  const { user, logout } = useAuth() || {};

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
            data-testid={`sidebar-nav-${id}`}
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
        {/* Account */}
        {user ? (
          <div className="afcfta-nav-item" style={{ marginBottom: 8, cursor: "default" }} data-testid="sidebar-user-info">
            <span className="afcfta-nav-icon"><User size={16} strokeWidth={1.7} /></span>
            <span className="afcfta-nav-label" style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>{user.name}</span>
            <button
              onClick={logout}
              aria-label={isFrench ? "Se déconnecter" : "Log out"}
              title={isFrench ? "Se déconnecter" : "Log out"}
              data-testid="sidebar-logout-btn"
              style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", padding: 4 }}
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <button
            className="afcfta-nav-item"
            onClick={onOpenAuth}
            style={{ marginBottom: 8, width: "100%" }}
            data-testid="sidebar-login-btn"
          >
            <span className="afcfta-nav-icon"><User size={16} strokeWidth={1.7} /></span>
            <span className="afcfta-nav-label">{isFrench ? "Connexion" : "Login"}</span>
          </button>
        )}

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
