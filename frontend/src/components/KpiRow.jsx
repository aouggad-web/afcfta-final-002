import React from "react";

export default function KpiRow({ language = "fr", stats }) {
  const kpis = [
    {
      type: "gdp",
      title: language === 'fr' ? "PIB combiné Afrique" : "Combined Africa GDP",
      value: stats?.gdp || "$2.7T",
      subtext: language === 'fr' ? "55 pays membres" : "55 member countries"
    },
    {
      type: "trade",
      title: language === 'fr' ? "Commerce intra-africain" : "Intra-African Trade",
      value: stats?.trade || "$235B",
      subtext: language === 'fr' ? "Croissance 2024: +7.7%" : "2024 Growth: +7.7%"
    },
    {
      type: "port",
      title: language === 'fr' ? "Ports majeurs" : "Major Ports",
      value: stats?.ports || "68",
      subtext: "35.5M TEU/an"
    },
    {
      type: "progress",
      title: language === 'fr' ? "Progression ZLECAf" : "AfCFTA Progress",
      value: stats?.progress || "57%",
      subtext: language === 'fr' ? "Phase 2 en cours" : "Phase 2 ongoing"
    }
  ];

  return (
    <div className="afcfta-grid-4" style={{ marginTop: 18 }}>
      {kpis.map((kpi, idx) => (
        <div key={idx} className={`afcfta-card afcfta-kpi ${kpi.type}`}>
          <h3>{kpi.title}</h3>
          <div className="value">{kpi.value}</div>
          <div className="subvalue">{kpi.subtext}</div>
        </div>
      ))}
    </div>
  );
}
