import React from "react";

const KPI_CONFIG = {
  gdp: {
    icon: BarChart3,
    accent: "var(--gold)",
  },
  trade: {
    icon: TrendingUp,
    accent: "#4f8ef7",
  },
  port: {
    icon: Ship,
    accent: "#20c997",
  },
  progress: {
    icon: ShieldCheck,
    accent: "#d4891a",
  },
};

export default function KpiRow({ language = "fr", stats }) {
  const kpis = [
    {
      type: "gdp",
      title: language === "fr" ? "PIB combiné Afrique" : "Combined Africa GDP",
      value: stats?.gdp || "$2.7T",
      subtext:
        language === "fr"
          ? "54 signataires / 48 ratifications"
          : "54 signatories / 48 ratifications",
      meta: language === "fr" ? "Macro" : "Macro",
    },
    {
      type: "trade",
      title: language === "fr" ? "Commerce intra-africain" : "Intra-African Trade",
      value: stats?.trade || "$235B",
      subtext:
        language === "fr" ? "Croissance 2024: +7.7%" : "2024 Growth: +7.7%",
      meta: "+7.7%",
    },
    {
      type: "port",
      title: language === "fr" ? "Ports majeurs" : "Major Ports",
      value: stats?.ports || "68",
      subtext: "35.5M TEU/an",
      meta: language === "fr" ? "Logistique" : "Logistics",
    },
    {
      type: "progress",
      title: language === "fr" ? "Progression ZLECAf" : "AfCFTA Progress",
      value: stats?.progress || "57%",
      subtext:
        language === "fr" ? "Phase 2 en cours" : "Phase 2 ongoing",
      meta: language === "fr" ? "Mise en œuvre" : "Implementation",
    },
  ];

  return (
    <div className="stats-strip">
      {kpis.map((kpi, idx) => {
        const Icon = KPI_CONFIG[kpi.type]?.icon;
        return (
          <div key={idx} className="stat-cell">
            <div className="stat-value">{kpi.value}</div>
            <div className="stat-label">{kpi.title}</div>
            <div style={{ fontSize: 10, color: "rgba(245,237,214,0.22)", marginTop: 3 }}>
              {kpi.subtext}
            </div>
          </div>
        );
      })}
    </div>
  );
}
