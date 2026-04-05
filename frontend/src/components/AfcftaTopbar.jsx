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
  Menu,
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
  { id: "profiles", label: isFrench ? "Profils pays" : "Country Profiles", icon: Globe2 },
];

export default function AfcftaTopbar({
  active = "dashboard",
  onTabChange,
  language = "fr",
  mobileOpen = false,
  onMobileOpen,
}) {
  const isFrench = language === "fr";
  const navItems = NAV_ITEMS(isFrench);

  const handleTab = (id) => {
    onTabChange && onTabChange("tab", id);
  };

  return (
    <>
      {/* Mobile strip */}
      <div className="afcfta-mobile-topbar">
        <button
          onClick={onMobileOpen}
          className="afcfta-mobile-menuBtn"
          aria-label={isFrench ? "Ouvrir le menu" : "Open menu"}
        >
          <Menu size={18} />
        </button>

        <div className="afcfta-mobile-brand">
          <div className="afcfta-mobile-brandIcon">🌍</div>
          <div className="afcfta-mobile-brandText">
            <div className="afcfta-mobile-brandTitle">
              {isFrench ? "Accord de la ZLECAf" : "AfCFTA Agreement"}
            </div>
            <div className="afcfta-mobile-brandSub">
              {isFrench ? "Trade Intelligence Platform" : "Trade Intelligence Platform"}
            </div>
          </div>
        </div>

        <div className="afcfta-mobile-lang">
          <button
            className={`afcfta-langBtn ${isFrench ? "active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "fr")}
          >
            FR
          </button>
          <button
            className={`afcfta-langBtn ${!isFrench ? "active" : ""}`}
            onClick={() => onTabChange && onTabChange("language", "en")}
          >
            EN
          </button>
        </div>
      </div>

      {/* Desktop top header */}
      <header className="afcfta-topHeader">
        <div className="afcfta-topHeader-main">
          <div className="afcfta-topHeader-left">
            <div className="afcfta-topHeader-brandRow">
              <div className="afcfta-topHeader-logo">🌍</div>

              <div className="afcfta-topHeader-brandText">
                <h1>{isFrench ? "Accord de la ZLECAf" : "AfCFTA Agreement"}</h1>
                <p>
                  {isFrench
                    ? "Plateforme d'intelligence commerciale africaine — droits, TVA, taxes totales et analyses."
                    : "African trade intelligence platform — duties, VAT, total taxes and analytics."}
                </p>
              </div>
            </div>

            <div className="afcfta-topHeader-badges">
              <span className="afcfta-topHeader-badge">
                {isFrench ? "54 signataires ZLECAf" : "54 AfCFTA signatories"}
              </span>
              <span className="afcfta-topHeader-badge">
                {isFrench ? "1,3 Md+ habitants" : "1.3B+ inhabitants"}
              </span>
              <span className="afcfta-topHeader-badge">
                {isFrench ? "Données actualisées" : "Updated data"}
              </span>
            </div>
          </div>

          <div className="afcfta-topHeader-right">
            <button
              className={`afcfta-langSwitchBtn ${isFrench ? "active" : ""}`}
              onClick={() => onTabChange && onTabChange("language", "fr")}
            >
              🇫🇷 {isFrench ? "Français" : "French"}
            </button>
            <button
              className={`afcfta-langSwitchBtn ${!isFrench ? "active" : ""}`}
              onClick={() => onTabChange && onTabChange("language", "en")}
            >
              🇬🇧 English
            </button>
          </div>
        </div>

        <nav
          className="afcfta-topHeader-nav"
          aria-label={isFrench ? "Navigation principale" : "Main navigation"}
        >
          {navItems.map(({ id, label, icon: Icon }) => {
            const isActive = active === id;
            return (
              <button
                key={id}
                onClick={() => handleTab(id)}
                className={`afcfta-topNav-item ${isActive ? "active" : ""}`}
                aria-selected={isActive}
                role="tab"
                title={label}
              >
                <Icon size={15} />
                <span>{label}</span>
              </button>
            );
          })}
        </nav>
      </header>
    </>
  );
}
