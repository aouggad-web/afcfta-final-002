import React from "react";
import { BarChart3, TrendingUp, Ship, ShieldCheck } from "lucide-react";

const KPI_CONFIG = {
  gdp:      { icon: BarChart3,   accent: "var(--gold)",    accentSoft: "rgba(212,137,26,0.16)",  colorClass: "progress" },
  trade:    { icon: TrendingUp,  accent: "#4f8ef7",        accentSoft: "rgba(79,142,247,0.16)",  colorClass: "trade"    },
  port:     { icon: Ship,        accent: "var(--green)",   accentSoft: "rgba(26,122,74,0.16)",   colorClass: "port"     },
  progress: { icon: ShieldCheck, accent: "var(--terra)",   accentSoft: "rgba(200,83,26,0.16)",   colorClass: "terra"    },
};

export default function KpiRow({ language = "fr", stats }) {
  const kpis = [
    {
      type: "gdp",
      title: language === "fr" ? "PIB combiné Afrique" : "Combined Africa GDP",
      value: stats?.gdp || "$2.7T",
      subtext: language === "fr" ? "54 signataires · 48 ratifications" : "54 signatories · 48 ratifications",
      meta: language === "fr" ? "Macro" : "Macro",
    },
    {
      type: "trade",
      title: language === "fr" ? "Commerce intra-africain" : "Intra-African Trade",
      value: stats?.trade || "$235B",
      subtext: language === "fr" ? "Croissance 2024 : +7.7 %" : "2024 Growth: +7.7%",
      meta: "▲ +7.7 %",
      metaPositive: true,
    },
    {
      type: "port",
      title: language === "fr" ? "Ports majeurs" : "Major Ports",
      value: stats?.ports || "68",
      subtext: "35.5 M TEU / an",
      meta: language === "fr" ? "Logistique" : "Logistics",
    },
    {
      type: "progress",
      title: language === "fr" ? "Progression ZLECAf" : "AfCFTA Progress",
      value: stats?.progress || "57 %",
      subtext: language === "fr" ? "Phase 2 en cours" : "Phase 2 ongoing",
      meta: language === "fr" ? "Mise en œuvre" : "Implementation",
    },
  ];

  return (
    <div className="afcfta-kpiRow">
      {kpis.map((kpi) => {
        const cfg = KPI_CONFIG[kpi.type];
        const Icon = cfg.icon;
        return (
          <div key={kpi.type} className="afcfta-kpiCard">
            <div className="afcfta-kpiCard-top">
              <div>
                <div className="afcfta-kpiCard-title">{kpi.title}</div>
                <div className="afcfta-kpiCard-value">{kpi.value}</div>
              </div>
              <div
                className="afcfta-kpiCard-icon"
                style={{ background: cfg.accentSoft, borderColor: cfg.accent + "44" }}
              >
                <Icon size={22} color={cfg.accent} strokeWidth={1.6} />
              </div>
            </div>
            <div className="afcfta-kpiCard-bottom">
              <div className="afcfta-kpiCard-subvalue">{kpi.subtext}</div>
              <div
                className="afcfta-kpiCard-meta"
                style={kpi.metaPositive ? { color: "var(--success)" } : {}}
              >
                {kpi.meta}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
