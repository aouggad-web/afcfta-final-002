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
  Globe2
} from "lucide-react";

export default function AfcftaTopbar({ active = "dashboard", onTabChange, language = "fr" }) {
  const isFrench = language === "fr";

  const tabs = [
    { id: "dashboard", label: isFrench ? "Tableau de bord" : "Dashboard", icon: LayoutDashboard },
    { id: "calculator", label: isFrench ? "Calculateur" : "Calculator", icon: Calculator },
    { id: "stats", label: isFrench ? "Statistiques" : "Statistics", icon: BarChart3 },
    { id: "opps", label: isFrench ? "Opportunités" : "Opportunities", icon: Target },
    { id: "production", label: isFrench ? "Production" : "Production", icon: Factory },
    { id: "logistics", label: isFrench ? "Logistique" : "Logistics", icon: Ship },
    { id: "banking", label: isFrench ? "Banque" : "Banking", icon: Landmark },
    { id: "tools", label: isFrench ? "Outils" : "Tools", icon: Wrench },
    { id: "roo", label: isFrench ? "Règles d'Origine" : "Rules of Origin", icon: FileCheck },
    { id: "profiles", label: isFrench ? "Profils pays" : "Country Profiles", icon: Globe2 }
  ];

  return (
    <div className="afcfta-topbar">
      <div className="afcfta-topbar-head">
        <div className="afcfta-brand">
          <h1 className="afcfta-title">
            <span className="afcfta-title-icon">🌍</span>
            {isFrench ? "Accord de la ZLECAf" : "AfCFTA Agreement"}
          </h1>
          <div className="afcfta-subtitle">
            {isFrench
              ? "Plateforme d'intelligence commerciale africaine — droits, TVA, taxes totales et analyses."
              : "African trade intelligence platform — duties, VAT, total taxes and analytics."}
          </div>
          <div className="afcfta-badges">
            <span className="afcfta-badge">{isFrench ? "54 signataires ZLECAf" : "54 AfCFTA signatories"}</span>
            <span className="afcfta-badge">{isFrench ? "1,3 Md+ habitants" : "1.3B+ population"}</span>
            <span className="afcfta-badge">{isFrench ? "Données actualisées" : "Updated dataset"}</span>
          </div>
        </div>

        <div className="afcfta-lang-switch" aria-label={isFrench ? "Choix de la langue" : "Language selector"}>
          <button
            className={`afcfta-btn-sm ${isFrench ? "afcfta-btn" : "afcfta-btn-secondary"}`}
            onClick={() => onTabChange && onTabChange("language", "fr")}
            style={{ padding: "6px 12px", fontSize: "12px" }}
            type="button"
            aria-pressed={isFrench}
          >
            🇫🇷 Français
          </button>
          <button
            className={`afcfta-btn-sm ${!isFrench ? "afcfta-btn" : "afcfta-btn-secondary"}`}
            onClick={() => onTabChange && onTabChange("language", "en")}
            style={{ padding: "6px 12px", fontSize: "12px" }}
            type="button"
            aria-pressed={!isFrench}
          >
            🇬🇧 English
          </button>
        </div>
      </div>

      <div className="afcfta-tabs" role="tablist" aria-label={isFrench ? "Navigation principale" : "Main navigation"}>
        {tabs.map((t) => {
          const Icon = t.icon;
          const selected = active === t.id;

          return (
            <button
              key={t.id}
              onClick={() => onTabChange && onTabChange("tab", t.id)}
              className={`afcfta-tab ${selected ? "active" : ""}`}
              type="button"
              role="tab"
              aria-selected={selected}
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
