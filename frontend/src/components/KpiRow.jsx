import React from "react";
import { BarChart3, TrendingUp, Ship, ShieldCheck } from "lucide-react";
import { montantCompact } from "../utils/nombres";
import { pick } from "../i18n/lang";

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
      title: pick(language, "PIB combiné Afrique", "Combined Africa GDP", "الناتج المحلي الإجمالي المجمّع لأفريقيا"),
      value: montantCompact(stats?.gdp || 2.7e12, language, { T: 1 }),
      subtext: pick(language, "54 signataires · 48 ratifications", "54 signatories · 48 ratifications", "54 دولة موقّعة · 48 مصادقة"),
      meta: pick(language, "Macro", "Macro", "الاقتصاد الكلي"),
    },
    {
      type: "trade",
      title: pick(language, "Commerce intra-africain", "Intra-African Trade", "التجارة البينية الأفريقية"),
      value: montantCompact(stats?.trade || 235e9, language, { B: 0 }),
      subtext: pick(language, "Croissance 2024 : +7.7 %", "2024 Growth: +7.7%", "نمو 2024: ‎+7.7%"),
      meta: "▲ +7.7 %",
      metaPositive: true,
    },
    {
      type: "port",
      title: pick(language, "Ports majeurs", "Major Ports", "الموانئ الرئيسية"),
      value: stats?.ports || "68",
      subtext: pick(language, "35.5 M TEU / an", "35.5 M TEU / an", "35.5 مليون TEU سنويًا"),
      meta: pick(language, "Logistique", "Logistics", "اللوجستيك"),
    },
    {
      type: "progress",
      title: pick(language, "Progression ZLECAf", "AfCFTA Progress", "تقدّم زليكاف"),
      value: stats?.progress || "57 %",
      subtext: pick(language, "Phase 2 en cours", "Phase 2 ongoing", "المرحلة 2 جارية"),
      meta: pick(language, "Mise en œuvre", "Implementation", "التنفيذ"),
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
