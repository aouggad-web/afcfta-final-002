import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import SubstitutionAnalysis from "../opportunities/SubstitutionAnalysis";
import StrategicFlows from "../opportunities/StrategicFlows";
import SectoralAnalysis from "../opportunities/SectoralAnalysis";
import NationalIndustryView from "./NationalIndustryView";
import OpportunityPdfExport from "../opportunities/OpportunityPdfExport";
import { opportunityPdfFilename } from "../../utils/opportunityPdf";
import { montant, montantUnite, nombre } from "../../utils/nombres";
import { pick } from "../../i18n/lang";

const API = `${import.meta.env.VITE_BACKEND_URL || ""}/api`;

/* Honest formatter: null / undefined -> "—" (never invented). */
const dash = (v, suffix = "") =>
  v === null || v === undefined || v === "" ? "—" : `${v}${suffix}`;

const pct = (v) => (v === null || v === undefined ? "—" : `${Math.round(v * 100)}%`);

/* « 12 345 $ » en français, « $12,345 » en anglais. */
const money = (v, lang) =>
  v === null || v === undefined ? "—" : montant(v, lang);

/* Volume BACI (poids net, tonnes métriques) — affiché à côté de la valeur. */
const tonnes = (v, lang) =>
  v === null || v === undefined || !(Number(v) > 0)
    ? null
    : `${nombre(v, lang, Number(v) < 10 ? 1 : 0)} t`;

/* Sous-module « faisabilité de substitution » (substitution_feasibility_service.py) :
   libellés des barrières non tarifaires (effet marque, écart technologique...)
   et de leur intensité, fr/en. */
const BARRIER_LABEL = {
  brand_effect: { fr: "Effet marque", en: "Brand effect", ar: "أثر العلامة التجارية" },
  technology_gap: { fr: "Écart technologique", en: "Technology gap", ar: "الفجوة التكنولوجية" },
  after_sales_network: { fr: "Réseau après-vente", en: "After-sales network", ar: "شبكة خدمات ما بعد البيع" },
  certification: { fr: "Certification", en: "Certification", ar: "الاعتماد والشهادات" },
};
const INTENSITY_LABEL = {
  faible: { fr: "Faible", en: "Low", ar: "ضعيف" },
  moyen: { fr: "Moyen", en: "Medium", ar: "متوسط" },
  fort: { fr: "Fort", en: "High", ar: "قوي" },
};

/* Source may be a plain string or an object {institution, dataset, url}. */
const srcText = (s) =>
  !s
    ? ""
    : typeof s === "string"
    ? s
    : [s.institution, s.dataset].filter(Boolean).join(" · ");

const card = {
  background: "var(--afcfta-card, #fff)",
  border: "1px solid var(--afcfta-border, rgba(0,0,0,0.08))",
  borderRadius: 12,
  padding: 16,
};

const label = { fontSize: 12, color: "var(--afcfta-muted, #667)", marginBottom: 4 };
const val = { fontSize: 18, fontWeight: 700 };
const th = { padding: "4px 8px", textAlign: "left", color: "var(--afcfta-muted,#667)" };
const td = { padding: "4px 8px" };

const num = (v, u = "") =>
  v === null || v === undefined ? "—" : `${Number(v).toLocaleString("fr-FR")}${u ? " " + u : ""}`;

/* Human-readable labels for composite components / factors. */
const COMPONENT_LABELS = {
  market_potential: { fr: "Potentiel de marché", en: "Market potential", ar: "إمكانات السوق" },
  market_demand: { fr: "Demande de marché", en: "Market demand", ar: "طلب السوق" },
  supply_capacity: { fr: "Capacité de production", en: "Supply capacity", ar: "القدرة الإنتاجية" },
  logistics_accessibility: { fr: "Accessibilité logistique", en: "Logistics accessibility", ar: "إمكانية الوصول اللوجستي" },
  financing_feasibility: { fr: "Faisabilité de financement", en: "Financing feasibility", ar: "جدوى التمويل" },
  country_risk: { fr: "Risque pays", en: "Country risk", ar: "مخاطر البلد" },
  fx_volatility: { fr: "Volatilité du change", en: "FX volatility", ar: "تقلب سعر الصرف" },
  tariff_advantage: { fr: "Avantage tarifaire", en: "Tariff advantage", ar: "الميزة التعريفية" },
};
const compLabel = (key, lang) => COMPONENT_LABELS[key]?.[pick(lang, "fr", "en", "ar")] || key;

function Metric({ title, value, sub }) {
  return (
    <div style={card}>
      <div style={label}>{title}</div>
      <div style={val}>{value}</div>
      {sub && (
        <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>{sub}</div>
      )}
    </div>
  );
}

/* Reusable country <select> for scenario inputs. */
function Sel({ value, onChange, countries, testid }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-testid={testid}
      style={{ padding: "8px 10px", borderRadius: 8, minWidth: 170 }}
    >
      {countries.map((c) => (
        <option key={c.iso3 || c.code} value={c.iso3 || c.code}>
          {c.name} ({c.iso3 || c.code})
        </option>
      ))}
    </select>
  );
}

/* Estimated/measured badge shared by the need-based views. */
function EstBadge({ isEstimation, level, language }) {
  return (
    <span
      style={{
        display: "inline-block",
        fontSize: 11,
        fontWeight: 700,
        padding: "2px 8px",
        borderRadius: 999,
        background: isEstimation ? "rgba(154,103,0,0.12)" : "rgba(26,127,55,0.12)",
        color: `color-mix(in srgb, ${isEstimation ? "#9a6700" : "#1a7f37"} 40%, var(--text))`,
      }}
    >
      {isEstimation
        ? `${pick(language, "Estimé — niveau", "Estimated — level", "مقدَّر — المستوى")} ${level}`
        : pick(language, "Mesuré", "Measured", "مقيس")}
    </span>
  );
}

/* ── Mode 1: producer looking for markets ─────────────────────────────────── */
function MarketSeekingView({ fr, prefill, language = fr ? "fr" : "en" }) {
  const [hsCode, setHsCode] = useState(prefill?.hsCode || "1801");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rep, setRep] = useState(null);

  const run = async (code) => {
    const target = code || hsCode;
    setLoading(true);
    setError(null);
    setRep(null);
    try {
      const params = new URLSearchParams({ hs_code: target, lang: language === "en" ? "en" : "fr" });
      const res = await axios.get(`${API}/reports/market-seeking?${params.toString()}`);
      setRep(res.data);
    } catch (e) {
      setError(pick(language, "Impossible de générer le rapport.", "Could not generate report.", "تعذّر إنشاء التقرير."));
    } finally {
      setLoading(false);
    }
  };

  // ``setHsCode`` est asynchrone : l'effet de pré-remplissage doit passer le
  // code explicitement, sinon la requête partirait avec l'ancienne valeur.
  const runRef = useRef(null);
  runRef.current = () => run(prefill?.hsCode);

  // Arrivée depuis le module Production : le code SH est déjà choisi, l'utilisateur
  // vient de cliquer « voir les débouchés ». Lui redemander de valider une
  // saisie qu'il n'a pas faite n'aurait pas de sens — on lance la recherche.
  // ``k`` est un jeton d'unicité : deux clics sur le même produit doivent
  // relancer, ce qu'un effet indexé sur le seul code SH ne ferait pas.
  const prefillKey = prefill?.k;
  const prefillHs = prefill?.hsCode;
  useEffect(() => {
    if (!prefillHs) return;
    setHsCode(prefillHs);
    runRef.current?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillHs, prefillKey]);

  const demand = rep?.demand || {};
  const supply = rep?.supply || {};

  // Le PDF reprend les MÊMES tableaux que l'écran (demande importatrice, offre
  // productrice) — pas un squelette : une section `text` n'existe pas dans le
  // bâtisseur (table / keyValues / paragraphs), elle produisait un PDF vide.
  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    const sections = [];
    if (demand.available && demand.markets?.length) {
      sections.push({
        title: pick(language, "Demande — marchés importateurs africains", "Demand — African importing markets", "الطلب — الأسواق المستوردة الأفريقية"),
        table: {
          columns: [
            { key: 'country', label: pick(language, 'Pays', 'Country', "البلد"), width: 1.6 },
            { key: 'imports', label: pick(language, 'Importations', 'Imports', "الواردات"), align: 'right', width: 1.1 },
            { key: 'volume', label: pick(language, 'Volume (t)', 'Volume (t)', "الحجم (طن)"), align: 'right', width: 1 },
            { key: 'share', label: pick(language, 'Part', 'Share', "الحصة"), align: 'right', width: 0.7 },
          ],
          rows: demand.markets.map((m) => ({
            country: `${m.country_name} (${m.country_iso3})`,
            imports: money(m.import_value_usd, language),
            volume: tonnes(m.import_quantity_tonnes, language) || '—',
            share: m.share_pct === null ? '—' : `${m.share_pct}%`,
          })),
        },
      });
    }
    if (supply.available && supply.producers?.length) {
      sections.push({
        title: `${pick(language, "Offre — producteurs africains", "Supply — African producers", "العرض — المنتجون الأفارقة")}${supply.commodity ? ` · ${supply.commodity}` : ''}`,
        table: {
          columns: [
            { key: 'country', label: pick(language, 'Pays', 'Country', "البلد"), width: 1.6 },
            { key: 'production', label: `${pick(language, 'Production', 'Production', "الإنتاج")}${supply.unit ? ` (${supply.unit})` : ''}`, align: 'right', width: 1.2 },
            { key: 'share', label: pick(language, 'Part', 'Share', "الحصة"), align: 'right', width: 0.7 },
          ],
          rows: supply.producers.map((p) => ({
            country: `${p.country_name} (${p.country_iso3})`,
            production: p.value == null ? '—' : Number(p.value).toLocaleString('en-US'),
            share: p.share_pct === null ? '—' : `${p.share_pct}%`,
          })),
        },
      });
    }
    const notes = [
      demand.note,
      supply.commodity_caveat ? `⚠ ${supply.commodity_caveat}` : null,
      rep.data_quality?.note,
    ].filter(Boolean);
    if (notes.length) sections.push({ title: pick(language, 'Notes', 'Notes', "ملاحظات"), paragraphs: notes });
    return {
      badge: pick(language, 'MARCHÉS', 'MARCHÉS', 'الأسواق'),
      title: `${rep.product_name || hsCode} — ${pick(language, 'recherche de marchés', 'find markets', "البحث عن الأسواق")} (SH ${rep.inputs?.hs_code || hsCode})`,
      subtitle: demand.source ? `${pick(language, 'Source demande', 'Demand source', "مصدر الطلب")}: ${demand.source}` : undefined,
      filename: opportunityPdfFilename('Marchés', hsCode),
      kpis: [
        { label: pick(language, "Code produit", "Product code", "رمز المنتج"), value: hsCode, accent: 'gold' },
        { label: pick(language, "Marchés importateurs", "Importing markets", "الأسواق المستوردة"), value: String(demand.markets?.length || 0), accent: 'green' },
        { label: pick(language, "Producteurs africains", "African producers", "المنتجون الأفارقة"), value: String(supply.producers?.length || 0), accent: 'terra' },
      ],
      sections,
      source: [demand.source, srcText(supply.source)].filter(Boolean).join(' · ') || 'FAOSTAT / USGS / UNIDO / OEC',
    };
  }, [rep, hsCode, demand, supply, language]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 18 }}>
        <div>
          <div style={label}>{pick(language, "Produit — Code SH (HS6 ou HS4)", "Product — HS code (HS6 or HS4)", "المنتج — رمز SH (SH6 أو SH4)")}</div>
          <input
            value={hsCode}
            onChange={(e) => setHsCode(e.target.value)}
            data-testid="ms-hs"
            style={{ padding: "8px 10px", borderRadius: 8, width: 160 }}
          />
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="afcfta-btn afcfta-btn-primary"
          data-testid="ms-run"
          style={{ padding: "10px 18px", borderRadius: 8 }}
        >
          {loading ? (pick(language, "Recherche…", "Searching…", "جارٍ البحث…")) : pick(language, "Trouver les marchés", "Find markets", "البحث عن الأسواق")}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={language} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "var(--danger)" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ fontSize: 16, fontWeight: 700 }}>
            {rep.product_name || rep.inputs?.hs_code}{" "}
            <span style={{ fontSize: 13, fontWeight: 400, color: "var(--afcfta-muted,#667)" }}>
              (SH {rep.inputs?.hs_code})
            </span>
          </div>

          {/* Demand: who imports this product */}
          <div style={card}>
            <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
              {pick(language, "Demande — marchés importateurs africains", "Demand — African importing markets", "الطلب — الأسواق المستوردة الأفريقية")}
            </div>
            {demand.available ? (
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={th}>{pick(language, "Pays", "Country", "البلد")}</th>
                    <th style={th}>{pick(language, "Importations", "Imports", "الواردات")}</th>
                    <th style={th}>{pick(language, "Volume (t)", "Volume (t)", "الحجم (طن)")}</th>
                    <th style={th}>{pick(language, "Part", "Share", "الحصة")}</th>
                  </tr>
                </thead>
                <tbody>
                  {demand.markets.map((m) => (
                    <tr key={m.country_iso3} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                      <td style={td}>
                        {m.country_name} ({m.country_iso3})
                      </td>
                      <td style={td}>{money(m.import_value_usd, language)}</td>
                      <td style={td}>{tonnes(m.import_quantity_tonnes, language) || "—"}</td>
                      <td style={td}>{m.share_pct === null ? "—" : `${m.share_pct}%`}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ color: "var(--afcfta-muted,#667)", fontSize: 13 }}>
                — {demand.note}
              </div>
            )}
            {demand.source && (
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                {pick(language, "Source", "Source", "المصدر")} : {demand.source}
              </div>
            )}
          </div>

          {/* Supply: who produces this product */}
          <div style={card}>
            <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
              {pick(language, "Offre — producteurs africains", "Supply — African producers", "العرض — المنتجون الأفارقة")}
              {supply.available && supply.commodity ? ` · ${supply.commodity}` : ""}
            </div>
            {supply.available ? (
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={th}>{pick(language, "Pays", "Country", "البلد")}</th>
                    <th style={th}>
                      {pick(language, "Production", "Production", "الإنتاج")} {supply.unit ? `(${supply.unit})` : ""}
                    </th>
                    <th style={th}>{pick(language, "Part", "Share", "الحصة")}</th>
                  </tr>
                </thead>
                <tbody>
                  {supply.producers.map((p) => (
                    <tr key={p.country_iso3} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                      <td style={td}>
                        {p.country_name} ({p.country_iso3})
                      </td>
                      <td style={td}>
                        {p.value === null || p.value === undefined
                          ? "—"
                          : Number(p.value).toLocaleString("en-US")}
                      </td>
                      <td style={td}>{p.share_pct === null ? "—" : `${p.share_pct}%`}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ color: "var(--afcfta-muted,#667)", fontSize: 13 }}>
                — {pick(language, "Aucune donnée de production pour ce code.", "No production data for this code.", "لا توجد بيانات إنتاج لهذا الرمز.")}
              </div>
            )}
            {supply.source && (
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                {pick(language, "Source", "Source", "المصدر")} : {srcText(supply.source)}
                {supply.year ? ` (${supply.year})` : ""}
              </div>
            )}
            {supply.commodity_caveat && (
              <div style={{
                fontSize: 11, color: "var(--gold)", background: "#fef3c7",
                border: "1px solid #fde68a", borderRadius: 6, padding: "6px 9px",
                marginTop: 8, lineHeight: 1.4,
              }}>
                ⚠ {supply.commodity_caveat}
              </div>
            )}
          </div>

          <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)" }}>{rep.data_quality?.note}</div>
        </div>
      )}
    </div>
  );
}

/* ── Mode 2: bilateral opportunity report ─────────────────────────────────── */
// Exportée pour test direct (évite de simuler toute la navigation par onglets
// du composant top-level juste pour vérifier le rendu d'une carte).
export function BilateralView({ countries, fr, prefill, language = fr ? "fr" : "en" }) {
  const [origin, setOrigin] = useState("CIV");
  const [destination, setDestination] = useState("NGA");
  const [hsCode, setHsCode] = useState("1801");
  const [goodsValue, setGoodsValue] = useState("50000");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);

  const run = async (overrides = {}) => {
    const o = { origin, destination, hsCode, goodsValue, ...overrides };
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const params = new URLSearchParams({
        hs_code: o.hsCode,
        origin: o.origin,
        destination: o.destination,
        mode: "ultra_fine",
      });
      if (o.goodsValue) params.set("goods_value_usd", o.goodsValue);
      const res = await axios.get(`${API}/reports/opportunity?${params.toString()}`);
      setReport(res.data);
    } catch (e) {
      setError(pick(language, "Impossible de générer le rapport.", "Could not generate report.", "تعذّر إنشاء التقرير."));
    } finally {
      setLoading(false);
    }
  };

  // When another scenario hands off (prefill), sync the fields and auto-run.
  useEffect(() => {
    if (!prefill || !prefill.k) return;
    if (prefill.origin) setOrigin(prefill.origin);
    if (prefill.destination) setDestination(prefill.destination);
    if (prefill.hsCode) setHsCode(prefill.hsCode);
    if (prefill.goodsValue) setGoodsValue(prefill.goodsValue);
    run({
      origin: prefill.origin,
      destination: prefill.destination,
      hsCode: prefill.hsCode,
      goodsValue: prefill.goodsValue,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefill?.k]);

  const ci = report?.composite_indicators || {};
  const e2e = ci.end_to_end_score || {};
  const landed = ci.landed_cost || {};
  const logAccess = ci.logistics_accessibility_index || {};
  const finIdx = ci.financing_feasibility_index || {};
  const fin = report?.finance?.profile || {};
  const macro = fin.destination_macro || {};
  const gai = macro.gai || null;
  const fx = macro.fx_reserves || {};
  const cover = macro.import_cover || {};
  const gold = macro.gold_reserves || null;
  const cheapest = report?.logistics?.profile?.cheapest_operational_option || null;
  const freight = report?.logistics?.profile?.freight || {};
  const allOptions = freight?.options || [];
  const seaBulkOptions = allOptions.filter((o) => o.mode === "sea_bulk" && o.available);
  const risk = fin.country_risk || {};
  const tf = fin.trade_finance || {};
  const pay = fin.payment_coverage || {};

  // Ultra-fine sections
  const exec = report?.executive_summary || null;
  const narr = report?.narrative_analysis || {};
  const need = report?.national_need || {};
  const subst = report?.substitution_feasibility || {};
  const intra = report?.intra_african_context || {};
  const bench = report?.benchmarking || {};
  const tariff = bench.tariff_benefit || {};
  const topProducers = bench.top_producers || {};
  const seg = report?.segmentation || {};
  const effort = seg.effort_impact_matrix || {};
  const rr = seg.risk_reward_matrix || {};
  const factors = seg.factor_breakdown || [];
  const tierColor = {
    QUICK_WIN: "#1a7f37",
    STRATEGIC_BET: "#0969da",
    HIGH_REWARD_BET: "#9a6700",
    PASS: "#8b949e",
  };
  const num = (v, u = "") =>
    v === null || v === undefined ? "—" : `${Number(v).toLocaleString("fr-FR")}${u ? " " + u : ""}`;

  const sel = (value, onChange, testid) => (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      data-testid={testid}
      style={{ padding: "8px 10px", borderRadius: 8, minWidth: 180 }}
    >
      {countries.map((c) => (
        <option key={c.iso3 || c.code} value={c.iso3 || c.code}>
          {c.name} ({c.iso3 || c.code})
        </option>
      ))}
    </select>
  );

  // Le PDF reflète le rapport ultra-fin affiché : synthèse exécutive, scores
  // composites, avantage tarifaire ZLECAf, besoin national, substituabilité,
  // financement — pas un squelette (une section `text` n'est pas un type du
  // bâtisseur et produisait un PDF vide).
  const buildPdfSpec = useCallback(() => {
    if (!report) return null;
    const kpis = [];
    if (e2e.available) kpis.push({ label: pick(language, "Score bout en bout", "End-to-end score", "النتيجة الشاملة"), value: pct(e2e.score), accent: 'gold' });
    if (landed.available) kpis.push({ label: pick(language, "Coût rendu", "Landed cost", "التكلفة عند الوصول"), value: money(landed.value_usd, language), accent: 'green' });
    if (logAccess.available) kpis.push({ label: pick(language, "Accessibilité logistique", "Logistics accessibility", "إمكانية الوصول اللوجستي"), value: pct(logAccess.index), accent: 'terra' });
    if (finIdx.available) kpis.push({ label: pick(language, "Faisabilité financement", "Financing feasibility", "جدوى التمويل"), value: pct(finIdx.index), accent: 'red' });

    const sections = [];
    if (exec) {
      sections.push({
        title: `${pick(language, 'Synthèse exécutive', 'Executive summary', "الملخص التنفيذي")} — ${exec.priority_tier || ''}`,
        paragraphs: [...(exec.key_findings || []), exec.recommendation].filter(Boolean),
      });
    }
    const tariffKv = [];
    if (tariff.available) {
      if (tariff.national_rate_pct != null) tariffKv.push({ label: pick(language, 'Taux NPF national', 'National MFN rate', "المعدل الوطني للدولة الأولى بالرعاية (NPF)"), value: `${tariff.national_rate_pct}%` });
      if (tariff.zlecaf_rate_pct != null) tariffKv.push({ label: pick(language, 'Taux ZLECAf', 'AfCFTA rate', "معدل زليكاف"), value: `${tariff.zlecaf_rate_pct}%` });
      if (tariff.tariff_advantage_pct != null) tariffKv.push({ label: pick(language, 'Avantage tarifaire', 'Tariff advantage', "الميزة التعريفية"), value: `${tariff.tariff_advantage_pct}%` });
      if (tariff.savings_per_1000usd != null) tariffKv.push({ label: pick(language, 'Économie / 1000 USD', 'Savings / 1000 USD', "الوفر / 1000 USD"), value: money(tariff.savings_per_1000usd, language) });
      if (tariff.trade_regime) tariffKv.push({ label: pick(language, 'Régime commercial', 'Trade regime', "النظام التجاري"), value: tariff.trade_regime });
    }
    if (tariffKv.length) sections.push({ title: pick(language, 'Avantage tarifaire ZLECAf', 'AfCFTA tariff benefit', "الميزة التعريفية لزليكاف"), keyValues: tariffKv });

    const needKv = [];
    if (need.available) {
      needKv.push({ label: pick(language, 'Besoin estimé', 'Estimated need', "الحاجة المقدَّرة"), value: `${Math.round(need.value || 0).toLocaleString('en-US')} ${need.unit || ''}` });
      if (need.method) needKv.push({ label: pick(language, 'Méthode', 'Method', "المنهجية"), value: need.method });
      if (need.observed_imports?.import_value_usd) needKv.push({ label: pick(language, 'Imports observés', 'Observed imports', "الواردات المرصودة"), value: money(need.observed_imports.import_value_usd, language) });
    }
    if (needKv.length) sections.push({ title: pick(language, `Besoin national — ${destination}`, `National need — ${destination}`, `الحاجة الوطنية — ${destination}`), keyValues: needKv });

    if (subst.coefficient != null) {
      sections.push({
        title: pick(language, 'Faisabilité de substitution', 'Substitution feasibility', "جدوى الإحلال"),
        keyValues: [
          { label: pick(language, 'Part adressable', 'Addressable share', "الحصة القابلة للاستهداف"), value: `${Math.round(subst.coefficient * 100)}%` },
          { label: pick(language, 'Classe produit', 'Product class', "فئة المنتج"), value: subst.product_class || '—' },
        ],
      });
    }
    const finKv = [];
    if (risk.available) finKv.push({ label: pick(language, 'Risque pays', 'Country risk', "مخاطر البلد"), value: `${risk.overall_risk_rating || '—'}${risk.alert_level ? ` (${risk.alert_level})` : ''}` });
    if (gai) finKv.push({ label: 'GAI', value: `${gai.rating || gai.score || '—'}${gai.rank_africa ? ` · #${gai.rank_africa} ${pick(language, 'Afrique', 'Afrique', 'أفريقيا')}` : ''}` });
    if (fx.available) finKv.push({ label: pick(language, 'Réserves de change', 'FX reserves', "احتياطيات الصرف"), value: `${montantUnite(fx.value_busd, 'B', language)} (${fx.year || '—'})` });
    if (cover.available) finKv.push({ label: pick(language, "Couverture d'imports", 'Import cover', "تغطية الواردات"), value: `${cover.months} ${pick(language, 'mois', 'months', "أشهر")}` });
    if (finKv.length) sections.push({ title: pick(language, 'Profil financier de la destination', 'Destination financial profile', "الملف المالي لبلد المقصد"), keyValues: finKv });

    const narrParas = [narr.national_need, narr.supply, narr.logistics, narr.financing].filter(Boolean);
    if (narrParas.length) sections.push({ title: pick(language, 'Analyse narrative', 'Narrative analysis', "التحليل السردي"), paragraphs: narrParas });

    return {
      badge: `${origin} → ${destination}`,
      title: `${pick(language, 'Opportunité bilatérale', 'Bilateral opportunity', "فرصة ثنائية")} SH ${hsCode} — ${origin} → ${destination}`,
      subtitle: report.report_tier === 'ultra_fine' ? (pick(language, 'Rapport ultra-fin', 'Ultra-fine report', "تقرير مفصّل للغاية")) : undefined,
      filename: opportunityPdfFilename('Bilateral', `${origin}_${destination}_${hsCode}`),
      kpis,
      sections,
      source: pick(language, 'OEC BACI · référentiels ZLECAf', 'OEC BACI · référentiels ZLECAf', 'OEC BACI · مراجع زليكاف'),
    };
  }, [report, origin, destination, hsCode, language, e2e, landed, logAccess, finIdx, exec, tariff, need, subst, risk, gai, fx, cover, narr]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 18 }}>
        <div>
          <div style={label}>{pick(language, "Exportateur (origine)", "Exporter (origin)", "المصدِّر (المنشأ)")}</div>
          {sel(origin, setOrigin, "report-origin")}
        </div>
        <div>
          <div style={label}>{pick(language, "Marché (destination)", "Market (destination)", "السوق (المقصد)")}</div>
          {sel(destination, setDestination, "report-destination")}
        </div>
        <div>
          <div style={label}>{pick(language, "Code SH", "HS code", "رمز SH")}</div>
          <input
            value={hsCode}
            onChange={(e) => setHsCode(e.target.value)}
            data-testid="report-hs"
            style={{ padding: "8px 10px", borderRadius: 8, width: 120 }}
          />
        </div>
        <div>
          <div style={label}>{pick(language, "Valeur FOB (USD)", "FOB value (USD)", "القيمة فوب (USD)")}</div>
          <input
            value={goodsValue}
            onChange={(e) => setGoodsValue(e.target.value)}
            data-testid="report-value"
            style={{ padding: "8px 10px", borderRadius: 8, width: 140 }}
          />
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="afcfta-btn afcfta-btn-primary"
          data-testid="report-run"
          style={{ padding: "10px 18px", borderRadius: 8 }}
        >
          {loading ? (pick(language, "Génération…", "Generating…", "جارٍ الإنشاء…")) : pick(language, "Générer le rapport", "Generate report", "إنشاء التقرير")}
        </button>
        {report && <OpportunityPdfExport getSpec={buildPdfSpec} language={language} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "var(--danger)" }}>{error}</div>}

      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {exec && (
            <div style={{ ...card, borderLeft: `4px solid ${tierColor[exec.priority_tier] || "#0969da"}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <span style={{ ...label, margin: 0 }}>{pick(language, "Synthèse exécutive", "Executive summary", "الملخص التنفيذي")}</span>
                <span
                  data-testid="report-priority-tier"
                  style={{
                    background: tierColor[exec.priority_tier] || "#0969da",
                    color: "#fff",
                    padding: "3px 10px",
                    borderRadius: 999,
                    fontSize: 12,
                    fontWeight: 700,
                  }}
                >
                  {exec.priority_tier}
                </span>
              </div>
              {exec.key_findings?.length > 0 && (
                <ul style={{ margin: "10px 0 6px", paddingLeft: 18, fontSize: 14, lineHeight: 1.7 }}>
                  {exec.key_findings.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              )}
              {exec.recommendation && (
                <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>
                  → {exec.recommendation}
                </div>
              )}
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
            <Metric
              title={pick(language, "Score de bout en bout", "End-to-end score", "النتيجة الشاملة")}
              value={e2e.available ? pct(e2e.score) : "—"}
              sub={
                e2e.available
                  ? `${pick(language, "Couverture", "Coverage", "التغطية")} ${pct(e2e.weight_coverage)}`
                  : pick(language, "Aucune composante disponible", "No component available", "لا يتوفر أي مكوّن")
              }
            />
            <Metric
              title={pick(language, "Coût rendu estimé", "Estimated landed cost", "التكلفة المقدَّرة عند الوصول")}
              value={landed.available ? money(landed.value_usd, language) : "—"}
              sub={
                landed.available
                  ? `FOB ${money(landed.breakdown?.goods_value_fob_usd, language)} + ${pick(language, "fret", "freight", "الشحن")} ${money(
                      landed.breakdown?.best_operational_freight_usd, language
                    )} + ${pick(language, "assurance", "insurance", "التأمين")} ${money(landed.breakdown?.insurance_usd, language)}` +
                    (landed.breakdown?.trade_finance_fee_usd
                      ? ` + ${pick(language, "banque", "banking", "البنك")} ${money(landed.breakdown.trade_finance_fee_usd, language)}`
                      : "") +
                    (landed.breakdown?.freight_mode === "sea_bulk"
                      ? ` · ${pick(language, "affrètement vraquier", "bulk charter", "استئجار ناقلة سائبة")}${
                          landed.breakdown.vessel_class
                            ? ` (${landed.breakdown.vessel_class})`
                            : ""
                        }${
                          landed.breakdown.estimated_weight_kg
                            ? ` · ~${Math.round(
                                landed.breakdown.estimated_weight_kg / 1000
                              ).toLocaleString()} t`
                            : ""
                        }`
                      : landed.breakdown?.containers_needed
                      ? ` · ${landed.breakdown.containers_needed} × ${
                          landed.breakdown.container_type === "feu" ? "40′" : "20′"
                        }${
                          landed.breakdown.estimated_weight_kg
                            ? ` (~${Math.round(
                                landed.breakdown.estimated_weight_kg
                              ).toLocaleString()} kg${pick(language, " est.", " est.", " تقديري")})`
                            : ""
                        }`
                      : "")
                  : landed.note
              }
            />
            <Metric
              title={pick(language, "Accessibilité logistique", "Logistics accessibility", "إمكانية الوصول اللوجستي")}
              value={logAccess.available ? pct(logAccess.index) : "—"}
              sub={
                logAccess.available
                  ? `${dash(logAccess.operational_modes)} ${pick(language, "modes opérationnels", "operational modes", "أنماط تشغيلية")}`
                  : undefined
              }
            />
            <Metric
              title={pick(language, "Faisabilité de financement", "Financing feasibility", "جدوى التمويل")}
              value={finIdx.available ? pct(finIdx.index) : "—"}
            />
          </div>

          {landed.available && landed.breakdown && (
            <div style={card} data-testid="report-landed-breakdown">
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {pick(language, "Décomposition du coût rendu", "Landed cost breakdown", "تفصيل التكلفة عند الوصول")}
              </div>
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <tbody>
                  {(() => {
                    const bd = landed.breakdown;
                    const comp = landed.components || {};
                    const freightLabel =
                      bd.freight_excl_port_fees_usd != null
                        ? pick(language, "Fret (hors frais portuaires)", "Freight (excl. port fees)", "الشحن (دون الرسوم المينائية)")
                        : pick(language, "Fret (option la moins chère)", "Freight (cheapest option)", "الشحن (الخيار الأرخص)");
                    const rows = [
                      { l: pick(language, "Valeur marchandises (FOB)", "Goods value (FOB)", "قيمة البضائع فوب (FOB)"), v: bd.goods_value_fob_usd },
                      {
                        l: freightLabel,
                        v: bd.freight_excl_port_fees_usd != null
                          ? bd.freight_excl_port_fees_usd
                          : bd.best_operational_freight_usd,
                      },
                      {
                        l: pick(language, "Frais portuaires — chargement (port d'origine)", "Port fees — loading (origin port)", "الرسوم المينائية — التحميل (ميناء المنشأ)"),
                        v: bd.port_fees_loading_usd,
                      },
                      {
                        l: pick(language, "Frais portuaires — déchargement (port de destination)", "Port fees — discharge (destination port)", "الرسوم المينائية — التفريغ (ميناء المقصد)"),
                        v: bd.port_fees_discharge_usd,
                      },
                      {
                        l: `${pick(language, "Assurance cargo", "Cargo insurance", "تأمين البضائع")} (${
                          comp.insurance?.rate_pct ?? "0,5"
                        } % · ${pick(language, "estimée", "estimated", "تقديري")})`,
                        v: bd.insurance_usd,
                      },
                      {
                        l: bd.trade_finance_instrument
                          ? `${pick(language, "Instrument bancaire recommandé", "Recommended banking instrument", "الأداة المصرفية الموصى بها")} — ${
                              bd.trade_finance_instrument
                            }${
                              comp.trade_finance?.typical_cost_pct != null
                                ? ` (${comp.trade_finance.typical_cost_pct} %)`
                                : ""
                            }`
                          : pick(language, "Instrument bancaire recommandé", "Recommended banking instrument", "الأداة المصرفية الموصى بها"),
                        v: bd.trade_finance_fee_usd,
                      },
                    ].filter((r) => r.v !== null && r.v !== undefined);
                    return (
                      <>
                        {rows.map((r, i) => (
                          <tr key={i} style={{ borderTop: i > 0 ? "1px solid rgba(0,0,0,0.06)" : "none" }}>
                            <td style={td}>{r.l}</td>
                            <td style={{ ...td, textAlign: "right" }}>{money(r.v, language)}</td>
                          </tr>
                        ))}
                        <tr style={{ borderTop: "2px solid rgba(0,0,0,0.15)", fontWeight: 700 }}>
                          <td style={td}>{pick(language, "Coût rendu estimé (total)", "Estimated landed cost (total)", "التكلفة المقدَّرة عند الوصول (الإجمالي)")}</td>
                          <td style={{ ...td, textAlign: "right" }}>{money(landed.value_usd, language)}</td>
                        </tr>
                      </>
                    );
                  })()}
                </tbody>
              </table>
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                {landed.note}
              </div>
            </div>
          )}

          {landed.shipment_sizing?.value_to_weight && (() => {
            const vtw = landed.shipment_sizing.value_to_weight;
            // Trois paliers de fiabilité décroissante — voir shipment_estimator.usd_per_kg_for_hs :
            // cours coté > valeur unitaire réelle observée (flux OEC/BACI pour ce SH précis) >
            // estimation générique par chapitre SH.
            const tierStyle = {
              cours_mondial: { bg: "#dcfce7", fg: "#166534", label: pick(language, "Cours mondial réel", "Real world market price", "السعر العالمي الفعلي") },
              valeur_unitaire_observee: { bg: "#dbeafe", fg: "#1e40af", label: pick(language, "Valeur unitaire réelle observée", "Real observed unit value", "قيمة الوحدة الفعلية المرصودة") },
              estimation_chapitre: { bg: "#fef9c3", fg: "#854d0e", label: pick(language, "Estimation par chapitre SH", "HS-chapter estimate", "تقدير حسب فصل SH") },
            };
            const tier = tierStyle[vtw.classification_source] || tierStyle.estimation_chapitre;
            return (
            <div style={card}>
              <div style={{ ...label, marginBottom: 8 }}>
                {pick(language, "Indice valeur/poids & repère de négociation", "Value/weight index & negotiation reference", "مؤشر القيمة/الوزن ومرجع التفاوض")}
              </div>
              <div style={{ fontSize: 13, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
                <strong>{montant(vtw.usd_per_kg, language, 3)}/kg</strong>
                <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: tier.bg, color: `color-mix(in srgb, ${tier.fg} 40%, var(--text))`}}>
                  {tier.label}
                </span>
              </div>
              {vtw.basis && (
                <div style={{ fontSize: 12, color: "var(--text)", marginTop: 6 }}>
                  {pick(language, "Base", "Basis", "الأساس")} : {vtw.basis}
                  {vtw.raw_quote && ` (${vtw.raw_quote})`}
                </div>
              )}
              <div style={{ fontSize: 12, color: "var(--afcfta-muted)", marginTop: 6 }}>
                {vtw.source}
              </div>
              {landed.shipment_sizing.negotiation_reference ? (
                <div style={{ fontSize: 12, color: "var(--text)", marginTop: 6 }}>
                  {pick(language, "Utilisable comme repère grossier de négociation d'achat. ", "Usable as a rough purchase-negotiation reference. ", "يمكن استخدامه مرجعًا تقريبيًا للتفاوض على الشراء. ")}
                  <span style={{ color: "var(--gold)" }}>
                    {landed.shipment_sizing.negotiation_reference.caveat}
                  </span>
                </div>
              ) : (
                <div style={{ fontSize: 12, color: "var(--gold)", marginTop: 6 }}>
                  {pick(language, "Dimensionnement logistique uniquement — PAS une base de négociation de prix.", "Logistics sizing only — NOT a price-negotiation basis.", "لتحديد الحجم اللوجستي فقط — وليس أساسًا للتفاوض على السعر.")}
                </div>
              )}
              {vtw.discarded_observed_value && (
                <div style={{ fontSize: 11, color: "var(--gold)", background: "#fef3c7", border: "1px solid #fde68a", borderRadius: 6, padding: "6px 9px", marginTop: 8, lineHeight: 1.4 }}>
                  ⚠ {vtw.discarded_observed_value}
                </div>
              )}
            </div>
            );
          })()}

          {e2e.breakdown && (
            <div style={card}>
              <div style={{ ...label, marginBottom: 8 }}>
                {pick(language, "Décomposition du score (pondérations transparentes)", "Score breakdown (transparent weights)", "تفصيل النتيجة (أوزان شفافة)")}
              </div>
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={th}>{pick(language, "Composante", "Component", "المكوّن")}</th>
                    <th style={th}>{pick(language, "Poids", "Weight", "الوزن")}</th>
                    <th style={th}>{pick(language, "Sous-score", "Sub-score", "النتيجة الفرعية")}</th>
                    <th style={th}>{pick(language, "Comptée", "Counted", "محتسَب")}</th>
                  </tr>
                </thead>
                <tbody>
                  {e2e.breakdown.map((b) => (
                    <tr key={b.component} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                      <td style={td}>{compLabel(b.component, language)}</td>
                      <td style={td}>{pct(b.weight)}</td>
                      <td style={td}>{b.subscore === null ? "—" : pct(b.subscore)}</td>
                      <td style={td}>
                        {b.counted ? "✓" : <span style={{ color: "#999" }}>{pick(language, "exclue", "excluded", "مستبعَد")}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                {report?.market_potential?.available
                  ? pick(
                      language,
                      `Potentiel de marché activé via les imports OEC réels du marché (${money(
                        report.market_potential.import_value_usd, language
                      )}/an${
                        tonnes(report.market_potential.import_quantity_tonnes, language)
                          ? ` · ${tonnes(report.market_potential.import_quantity_tonnes, language)}`
                          : ""
                      }).`,
                      `Market potential activated from real OEC imports (${money(
                        report.market_potential.import_value_usd, language
                      )}/yr${
                        tonnes(report.market_potential.import_quantity_tonnes, language)
                          ? ` · ${tonnes(report.market_potential.import_quantity_tonnes, language)}`
                          : ""
                      }).`,
                      `تم تفعيل إمكانات السوق انطلاقًا من واردات OEC الفعلية للسوق (${money(
                        report.market_potential.import_value_usd, language
                      )}/سنويًا${
                        tonnes(report.market_potential.import_quantity_tonnes, language)
                          ? ` · ${tonnes(report.market_potential.import_quantity_tonnes, language)}`
                          : ""
                      }).`
                    )
                  : pick(language, "Le potentiel de marché par produit (flux OEC) est indisponible ici — exclu, jamais estimé.", "Per-product market potential (OEC flows) unavailable here — excluded, never estimated.", "إمكانات السوق حسب المنتج (تدفقات OEC) غير متاحة هنا — مستبعَدة، ولا تُقدَّر أبدًا.")}
              </div>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
            <div style={card}>
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {pick(language, "Logistique — option la moins chère", "Logistics — cheapest option", "اللوجستيك — الخيار الأرخص")}
              </div>
              {cheapest ? (
                <div style={{ fontSize: 14 }}>
                  <div>
                    <strong>{cheapest.label || cheapest.mode}</strong>
                  </div>
                  <div>
                    {pick(language, "Coût", "Cost", "التكلفة")} : {money(cheapest.total_cost_usd, language)}
                  </div>
                  <div>
                    {pick(language, "Délai", "Transit", "المدة")} : {dash(cheapest.transit_days_min)}–{dash(cheapest.transit_days_max)}{" "}
                    {pick(language, "jours", "days", "أيام")}
                  </div>
                  {cheapest.source && (
                    <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>
                      {cheapest.source}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ color: "var(--afcfta-muted,#667)" }}>—</div>
              )}
            </div>

            {seaBulkOptions.length > 0 && (
              <div style={card} data-testid="report-sea-bulk">
                <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                  {pick(language, "Vraquier — affrètement en vrac", "Bulk carrier — charter shipping", "ناقلة سائبة — شحن بالاستئجار")}
                </div>
                <div style={{ fontSize: 13, display: "flex", flexDirection: "column", gap: 10 }}>
                  {seaBulkOptions.map((opt, idx) => {
                    const cb = opt.segments?.[0]?.cost_breakdown || {};
                    return (
                      <div
                        key={idx}
                        style={{
                          borderTop: idx > 0 ? "1px solid rgba(0,0,0,0.08)" : "none",
                          paddingTop: idx > 0 ? 10 : 0,
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                          <span
                            style={{
                              display: "inline-block",
                              fontSize: 11,
                              fontWeight: 700,
                              padding: "2px 8px",
                              borderRadius: 999,
                              background: "rgba(26,115,232,0.12)",
                              color: "#1a73e8",
                              textTransform: "capitalize",
                            }}
                          >
                            🚢 {opt.vessel_class || pick(language, "vraquier", "vraquier", "ناقلة سائبة")}
                          </span>
                          {opt.is_modeled && (
                            <span
                              style={{
                                fontSize: 10,
                                fontWeight: 700,
                                padding: "2px 6px",
                                borderRadius: 999,
                                background: "rgba(154,103,0,0.12)",
                                color: "#9a6700",
                              }}
                            >
                              {pick(language, "Modélisé", "Modeled", "منمذَج")}
                            </span>
                          )}
                          {opt.pricing?.is_live ? (
                            <span
                              title={opt.pricing.source}
                              style={{
                                fontSize: 10,
                                fontWeight: 700,
                                padding: "2px 6px",
                                borderRadius: 999,
                                background: "rgba(26,127,55,0.12)",
                                color: "#1a7f37",
                              }}
                            >
                              {pick(language, "Marché", "Live", "السوق")} · {opt.pricing.as_of}
                            </span>
                          ) : (
                            <span
                              title={opt.pricing?.source}
                              style={{
                                fontSize: 10,
                                fontWeight: 700,
                                padding: "2px 6px",
                                borderRadius: 999,
                                background: "rgba(100,116,139,0.12)",
                                color: "var(--afcfta-muted)",
                              }}
                            >
                              {pick(language, "Calibré 2024", "Calibrated 2024", "معايَر 2024")}
                            </span>
                          )}
                        </div>
                        <div style={{ fontWeight: 700 }}>{money(opt.total_cost_usd, language)}</div>
                        {cb.total_usd_per_t != null && (
                          <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 2 }}>
                            {num(cb.total_usd_per_t)} USD/t
                            {cb.ocean_usd_per_t != null && (
                              <>
                                {" "}({pick(language, "océan", "ocean", "بحري")} {num(cb.ocean_usd_per_t)} +{" "}
                                {pick(language, "chargt", "load", "تحميل")} {num(cb.port_load_usd_per_t)} +{" "}
                                {pick(language, "déchargt", "disch.", "تفريغ")} {num(cb.port_discharge_usd_per_t)})
                              </>
                            )}
                          </div>
                        )}
                        <div style={{ marginTop: 2 }}>
                          {pick(language, "Délai", "Transit", "المدة")}: {dash(opt.transit_days_min)}–{dash(opt.transit_days_max)}{" "}
                          {pick(language, "jours", "days", "أيام")}
                        </div>
                        {opt.co2_kg && (
                          <div>{pick(language, "CO₂", "CO₂", "CO₂")}: {num(Math.round(opt.co2_kg))} kg</div>
                        )}
                        {opt.notes && (
                          <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                            {opt.notes}
                          </div>
                        )}
                        {opt.source && (
                          <div style={{ fontSize: 10, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                            {opt.source}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div style={card}>
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {pick(language, "Finance & paiement", "Finance & payment", "التمويل والدفع")}
              </div>
              <div style={{ fontSize: 14, lineHeight: 1.7 }}>
                <div>
                  PAPSS :{" "}
                  {pay.available
                    ? pay.papss_covered
                      ? pick(language, "Couvert ✓", "Covered ✓", "مغطّى ✓")
                      : pick(language, "Non couvert", "Not covered", "غير مغطّى")
                    : "—"}
                </div>
                <div>
                  {pick(language, "Risque pays", "Country risk", "مخاطر البلد")} :{" "}
                  {risk.available ? `${dash(risk.overall_risk_rating)} (${dash(risk.alert_level)})` : "—"}
                </div>
                <div>
                  {pick(language, "Instruments trade finance", "Trade finance instruments", "أدوات تمويل التجارة")} :{" "}
                  {tf.available && tf.instruments?.length
                    ? tf.instruments
                        .slice(0, 3)
                        .map((i) => i.name_fr || i.name || i.code)
                        .join(", ")
                    : "—"}
                </div>
              </div>
            </div>
          </div>

          <div style={card}>
            <div style={{ ...label, marginBottom: 10, fontWeight: 700 }}>
              {pick(language, "Indicateurs macro du marché", "Market macro indicators", "المؤشرات الكلية للسوق")} — {report.inputs?.destination_iso3}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
              <Metric
                title={pick(language, "GAI (Global Attractiveness Index)", "GAI (Global Attractiveness Index)", "GAI (مؤشر الجاذبية العالمي)")}
                value={gai ? dash(gai.score) : "—"}
                sub={
                  gai
                    ? `${pick(language, "Rang Afrique", "Africa rank", "الترتيب أفريقيًا")} ${dash(gai.rank_africa)} · ${dash(gai.rating)} · ${dash(
                        gai.trend
                      )}`
                    : undefined
                }
              />
              <Metric
                title={pick(language, "Réserves de change", "FX reserves", "احتياطيات الصرف")}
                value={fx.available ? money(fx.value_busd * 1e9, language) : "—"}
                sub={fx.available ? `${pick(language, "Année", "Year", "السنة")} ${dash(fx.year)}` : pick(language, "À produire via ETL BM", "Pending WB ETL", "قيد الإعداد عبر بيانات البنك الدولي")}
              />
              <Metric
                title={pick(language, "Couverture des importations", "Import cover", "تغطية الواردات")}
                value={cover.available ? `${dash(cover.months)} ${pick(language, "mois", "months", "أشهر")}` : "—"}
                sub={cover.available ? `${pick(language, "Année", "Year", "السنة")} ${dash(cover.year)}` : pick(language, "À produire via ETL BM", "Pending WB ETL", "قيد الإعداد عبر بيانات البنك الدولي")}
              />
              <Metric
                title={pick(language, "Réserves d'or", "Gold reserves", "احتياطيات الذهب")}
                value={gold ? `${dash(gold.tonnes)} t` : "—"}
                sub={gold ? `${pick(language, "Rang Afrique", "Africa rank", "الترتيب أفريقيًا")} ${dash(gold.rank_africa)}` : undefined}
              />
            </div>
            {(() => {
              // Show a source only for indicators actually displayed with data.
              const sources = [];
              if (gai?.source) sources.push(gai.source);
              if (gold?.source) sources.push(gold.source);
              if (fx.available || cover.available) {
                const inds = [fx.available && fx.indicator, cover.available && cover.indicator]
                  .filter(Boolean)
                  .join(", ");
                const wb = fx.source || cover.source || "World Bank WDI";
                sources.push(inds ? `${wb} (${inds})` : wb);
              }
              return sources.length ? (
                <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 10 }}>
                  {pick(language, "Sources", "Sources", "المصادر")} : {sources.join(" · ")}
                </div>
              ) : null;
            })()}
          </div>

          {/* ── Segmentation matrices + national need ─────────────────── */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
            <div style={card} data-testid="report-effort-impact">
              <div style={{ ...label, marginBottom: 6, fontWeight: 700 }}>
                {pick(language, "Matrice effort / impact", "Effort / impact matrix", "مصفوفة الجهد / الأثر")}
              </div>
              <div className="first-letter:uppercase" style={{ fontSize: 20, fontWeight: 800 }}>
                {(effort.quadrant || "—").replace(/_/g, " ")}
              </div>
              <div style={{ fontSize: 13, marginTop: 4 }}>
                {pick(language, "Effort", "Effort", "الجهد")} {pct(effort.effort_score)} · {pick(language, "Impact", "Impact", "الأثر")} {pct(effort.impact_score)}
              </div>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>{effort.rationale}</div>
            </div>
            <div style={card} data-testid="report-risk-reward">
              <div style={{ ...label, marginBottom: 6, fontWeight: 700 }}>
                {pick(language, "Matrice risque / récompense", "Risk / reward matrix", "مصفوفة المخاطر / العائد")}
              </div>
              <div className="first-letter:uppercase" style={{ fontSize: 20, fontWeight: 800 }}>
                {(rr.quadrant || "—").replace(/_/g, " ")}
              </div>
              <div style={{ fontSize: 13, marginTop: 4 }}>
                {pick(language, "Risque", "Risk", "المخاطر")} {pct(rr.risk_score)} · {pick(language, "Récompense", "Reward", "العائد")} {pct(rr.reward_score)}
              </div>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>{rr.recommendation}</div>
            </div>
            <div style={card} data-testid="report-national-need">
              <div style={{ ...label, marginBottom: 6, fontWeight: 700 }}>
                {pick(language, "Besoin du marché", "Market need", "حاجة السوق")} — {report.inputs?.destination_iso3}
              </div>
              {need.available ? (
                <>
                  <div style={{ fontSize: 20, fontWeight: 800 }}>
                    {num(need.value, need.unit)}
                  </div>
                  <div
                    style={{
                      display: "inline-block",
                      marginTop: 4,
                      fontSize: 11,
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: 999,
                      background: need.is_estimation ? "rgba(154,103,0,0.12)" : "rgba(26,127,55,0.12)",
                      color: `color-mix(in srgb, ${need.is_estimation ? "#9a6700" : "#1a7f37"} 40%, var(--text))`,
                    }}
                  >
                    {need.is_estimation
                      ? `${pick(language, "Estimé — niveau", "Estimated — level", "مقدَّر — المستوى")} ${need.estimation_level}`
                      : pick(language, "Mesuré", "Measured", "مقيس")}
                  </div>
                  {need.observed_imports?.import_value_usd && (
                    <div style={{ fontSize: 12, marginTop: 6 }}>
                      {pick(language, "Importe déjà", "Already imports", "يستورد حاليًا")} : {money(need.observed_imports.import_value_usd, language)}
                      {tonnes(need.observed_imports.import_quantity_tonnes, language) && (
                        <span style={{ color: "var(--afcfta-muted,#667)" }}>
                          {" "}· {tonnes(need.observed_imports.import_quantity_tonnes, language)}
                        </span>
                      )}
                    </div>
                  )}
                  <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>{need.method}</div>
                </>
              ) : (
                <div style={{ color: "var(--afcfta-muted,#667)" }}>{need.note || "—"}</div>
              )}
            </div>
            {subst.coefficient !== undefined && (
              <div style={card} data-testid="report-substitution-feasibility">
                <div style={{ ...label, marginBottom: 6, fontWeight: 700 }}>
                  {pick(language, "Faisabilité de substitution", "Substitution feasibility", "جدوى الإحلال")}
                </div>
                <div style={{ fontSize: 20, fontWeight: 800 }}>{pct(subst.coefficient)}</div>
                <div style={{ fontSize: 12, marginTop: 2, color: "var(--afcfta-muted,#667)" }}>
                  {pick(language, "part réalistement adressable", "realistically addressable share", "الحصة القابلة للاستهداف واقعيًا")}
                  {subst.product_class ? ` · ${subst.product_class}` : ""}
                </div>
                {subst.barriers && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 8 }}>
                    {Object.entries(subst.barriers).map(([key, intensity]) => (
                      <span
                        key={key}
                        title={subst.rationale}
                        style={{
                          fontSize: 10,
                          fontWeight: 700,
                          padding: "2px 7px",
                          borderRadius: 999,
                          background:
                            intensity === "fort"
                              ? "rgba(200,16,46,0.12)"
                              : intensity === "moyen"
                              ? "rgba(154,103,0,0.12)"
                              : "rgba(102,102,102,0.12)",
                          color: `color-mix(in srgb, ${intensity === "fort" ? "#c8102e" : intensity === "moyen" ? "#9a6700" : "#667"} 40%, var(--text))`,
                        }}
                      >
                        {(BARRIER_LABEL[key]?.[pick(language, "fr", "en", "ar")] || key)} · {(INTENSITY_LABEL[intensity]?.[pick(language, "fr", "en", "ar")] || intensity)}
                      </span>
                    ))}
                  </div>
                )}
                {subst.rationale && (
                  <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>{subst.rationale}</div>
                )}
              </div>
            )}
          </div>

          {/* ── Tariff advantage (real ZLECAf) + factor breakdown ─────── */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
            <div style={card} data-testid="report-tariff">
              <div style={{ ...label, marginBottom: 6, fontWeight: 700 }}>
                {pick(language, "Avantage tarifaire ZLECAf", "AfCFTA tariff advantage", "الميزة التعريفية لزليكاف")}
              </div>
              {tariff.available ? (
                <div style={{ fontSize: 14, lineHeight: 1.7 }}>
                  <div style={{ fontSize: 22, fontWeight: 800 }}>{dash(tariff.tariff_advantage_pct, " %")}</div>
                  {tariff.trade_regime && !["ZLECAF", "CUSTOMS_UNION"].includes(tariff.trade_regime) ? (
                    <div>
                      {pick(language, "Droit national", "National duty", "الرسم الوطني")} {dash(tariff.national_rate_pct, " %")}{" "}
                      {pick(language, "appliqué (NPF)", "applied (MFN)", "المطبَّق (NPF)")}
                    </div>
                  ) : (
                    <div>
                      {pick(language, "Droit national", "National duty", "الرسم الوطني")} {dash(tariff.national_rate_pct, " %")} {pick(language, "→", "→", "←")}{" "}
                      {tariff.trade_regime === "CUSTOMS_UNION" ? (pick(language, "union douanière", "customs union", "الاتحاد الجمركي")) : pick(language, "ZLECAf", "ZLECAf", "زليكاف")}{" "}
                      {dash(tariff.zlecaf_rate_pct, " %")}
                    </div>
                  )}
                  {tariff.trade_regime_note ? (
                    <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                      {tariff.trade_regime_note}
                    </div>
                  ) : null}
                  {tariff.savings_per_1000usd ? (
                    <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)" }}>
                      {money(tariff.savings_per_1000usd, language)} / 1 000 $ CIF
                    </div>
                  ) : null}
                </div>
              ) : (
                <div style={{ color: "var(--afcfta-muted,#667)" }}>{tariff.note || "—"}</div>
              )}
            </div>
            {factors.length > 0 && (
              <div style={card} data-testid="report-factors">
                <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                  {pick(language, "Facteurs — opportunités & risques", "Factors — opportunities & risks", "العوامل — الفرص والمخاطر")}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {factors.map((f) => (
                    <div key={f.factor} style={{ display: "flex", alignItems: "baseline", gap: 8, fontSize: 13 }}>
                      <span
                        style={{
                          flexShrink: 0,
                          fontSize: 11,
                          fontWeight: 700,
                          color:
                            `color-mix(in srgb, ${f.category === "opportunity" ? "#1a7f37" : f.category === "risk" ? "#c8102e" : "#8b949e"} 40%, var(--text))`,
                        }}
                      >
                        {f.category === "opportunity" ? "▲" : f.category === "risk" ? "▼" : "■"}
                      </span>
                      <span style={{ flex: "0 0 150px", fontWeight: 600 }}>{compLabel(f.factor, language)}</span>
                      <span style={{ flex: 1, color: "var(--afcfta-muted,#667)" }}>{f.rationale}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* ── Sectoral Analysis (ISIC4 & IDSB) ──────────────────────── */}
          {/* Ancré sur le rapport SOUMIS (report.inputs), pas sur les champs
              du formulaire encore éditables — sinon cette carte irait chercher
              un autre couloir pendant que le reste du rapport montre l'ancien. */}
          <SectoralAnalysis
            hsCode={report.inputs?.hs_code}
            origin={report.inputs?.origin_iso3}
            destination={report.inputs?.destination_iso3}
            fr={fr}
          />

          {/* ── Top producers benchmark ───────────────────────────────── */}
          {topProducers.available && topProducers.producers?.length > 0 && (
            <div style={card}>
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {pick(language, "Meilleurs producteurs africains", "Top African producers", "أفضل المنتجين الأفارقة")}
              </div>
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={th}>#</th>
                    <th style={th}>{pick(language, "Pays", "Country", "البلد")}</th>
                    <th style={th}>{pick(language, "Part continentale", "Continental share", "الحصة القارية")}</th>
                    <th style={th}>{pick(language, "Production", "Production", "الإنتاج")}</th>
                  </tr>
                </thead>
                <tbody>
                  {topProducers.producers.map((p) => (
                    <tr key={p.country_iso3} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                      <td style={td}>{p.rank}</td>
                      <td style={td}>{p.country_name} ({p.country_iso3})</td>
                      <td style={td}>{dash(p.continental_share_pct, " %")}</td>
                      <td style={td}>{num(p.production_volume, p.unit || "")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                {srcText(topProducers.source)}{topProducers.year ? ` · ${topProducers.year}` : ""}
              </div>
            </div>
          )}

          {/* ── Contexte commerce intra-africain (Afreximbank ATR 2026) ── */}
          {intra.available && (intra.origin?.available || intra.destination?.available) && (
            <div style={card} data-testid="report-intra-african">
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {pick(language, "Contexte commerce intra-africain", "Intra-African trade context", "سياق التجارة البينية الأفريقية")}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
                {[
                  { side: intra.origin, role: pick(language, "Origine (exportateur)", "Origin (exporter)", "المنشأ (المصدِّر)") },
                  { side: intra.destination, role: pick(language, "Destination (marché)", "Destination (market)", "المقصد (السوق)") },
                ].map(({ side, role }, i) =>
                  side?.available ? (
                    <div key={i} style={{ padding: 10, borderRadius: 8, background: "var(--afcfta-subtle,rgba(0,0,0,0.03))" }}>
                      <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>
                        {role} — {side.name} ({side.iso3})
                      </div>
                      {side.intra_african_trade && (
                        <div style={{ fontSize: 13, marginBottom: 4 }}>
                          {pick(language, "Commerce intra-africain 2025", "Intra-African trade 2025", "التجارة البينية الأفريقية 2025")} :{" "}
                          <strong>{dash(side.intra_african_trade.value_2025_busd, " Md$")}</strong>{" "}
                          <span style={{ color: "var(--afcfta-muted,#667)" }}>
                            ({dash(side.intra_african_trade.share_2025_pct, " %")} {pick(language, "du total", "of total", "من الإجمالي")}
                            {side.intra_african_trade.growth_2021_2025_pct != null
                              ? ` · ${side.intra_african_trade.growth_2021_2025_pct >= 0 ? "+" : ""}${side.intra_african_trade.growth_2021_2025_pct}% ${pick(language, "depuis 2021", "since 2021", "منذ 2021")}`
                              : ""})
                          </span>
                        </div>
                      )}
                      {side.merchandise_exports && (
                        <div style={{ fontSize: 13 }}>
                          {pick(language, "Exports marchandises 2025", "Merchandise exports 2025", "صادرات السلع 2025")} :{" "}
                          <strong>{dash(side.merchandise_exports.value_2025_busd, " Md$")}</strong>{" "}
                          <span style={{ color: "var(--afcfta-muted,#667)" }}>
                            ({dash(side.merchandise_exports.share_2025_pct, " %")})
                          </span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div key={i} style={{ padding: 10, fontSize: 12, color: "var(--afcfta-muted,#667)" }}>
                      {role} — {pick(language, "non couvert par l'ATR 2026", "not covered by ATR 2026", "غير مشمول في تقرير ATR 2026")}
                    </div>
                  )
                )}
              </div>
              {intra.continental_2025 && (
                <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                  {pick(language, "Continent 2025", "Continent 2025", "القارة 2025")} :{" "}
                  {dash(intra.continental_2025.intra_african_trade_busd, " Md$")} {pick(language, "de commerce intra-africain", "intra-African trade", "من التجارة البينية الأفريقية")}
                  {intra.continental_2025.intra_african_trade_growth_pct != null
                    ? ` (+${intra.continental_2025.intra_african_trade_growth_pct}%)`
                    : ""}
                </div>
              )}
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>
                {srcText(intra.source)}
              </div>
            </div>
          )}

          {/* ── Narrative analysis ────────────────────────────────────── */}
          {(narr.supply?.narrative || narr.logistics?.narrative || narr.financing?.narrative || narr.national_need?.narrative) && (
            <div style={card} data-testid="report-narratives">
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {pick(language, "Analyse rédigée", "Written analysis", "تحليل مكتوب")}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13, lineHeight: 1.6 }}>
                {[narr.supply, narr.logistics, narr.financing, narr.national_need]
                  .filter((n) => n && n.available && n.narrative)
                  .map((n, i) => (
                    <div key={i}>• {n.narrative}</div>
                  ))}
              </div>
            </div>
          )}

          <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)" }}>{report.data_quality?.note}</div>
        </div>
      )}
    </div>
  );
}

/* ── Mode: S2 — national production → direct export (ranked markets) ───────── */
function DirectExportView({ countries, fr, onAnalyze, language = fr ? "fr" : "en" }) {
  const [hsCode, setHsCode] = useState("1801");
  const [producer, setProducer] = useState("CIV");
  const [topK, setTopK] = useState("5");
  const [goodsValue, setGoodsValue] = useState("50000");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rep, setRep] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setRep(null);
    try {
      const params = new URLSearchParams({ hs_code: hsCode, producer, top_k: topK });
      if (goodsValue) params.set("goods_value_usd", goodsValue);
      const res = await axios.get(`${API}/reports/direct-export?${params.toString()}`);
      setRep(res.data);
    } catch (e) {
      setError(pick(language, "Impossible de générer le scénario.", "Could not generate scenario.", "تعذّر إنشاء السيناريو."));
    } finally {
      setLoading(false);
    }
  };

  const supply = rep?.producer_supply || {};
  const opps = rep?.ranked_opportunities || [];

  // Le PDF reprend le tableau des marchés classés affiché à l'écran — pas un
  // squelette (une section `text` n'est pas un type du bâtisseur : PDF vide).
  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    const sections = [];
    if (supply.available) {
      sections.push({
        title: pick(language, 'Production du producteur', 'Producer supply', "إنتاج المنتِج"),
        keyValues: [
          { label: pick(language, 'Commodité', 'Commodity', "السلعة"), value: supply.commodity || '—' },
          { label: pick(language, 'Part continentale', 'Continental share', "الحصة القارية"), value: supply.continental_share_pct != null ? `${supply.continental_share_pct}%` : '—' },
          { label: pick(language, 'Rang continental', 'Continental rank', "الترتيب القاري"), value: supply.rank ? `#${supply.rank}` : '—' },
        ],
      });
    }
    if (opps.length) {
      sections.push({
        title: pick(language, "Marchés d'export classés", 'Ranked export markets', "أسواق التصدير المرتَّبة"),
        table: {
          columns: [
            { key: 'rank', label: '#', width: 0.4 },
            { key: 'market', label: pick(language, 'Marché', 'Market', "السوق"), width: 0.9 },
            { key: 'score', label: pick(language, 'Score', 'Score', 'النتيجة'), align: 'right', width: 0.8 },
            { key: 'need', label: pick(language, 'Besoin estimé', 'Est. need', "الحاجة المقدَّرة"), align: 'right', width: 1.2 },
            { key: 'tariffAdv', label: pick(language, 'Avantage tarif', 'Tariff adv.', "الميزة التعريفية"), align: 'right', width: 1 },
            { key: 'landedCost', label: pick(language, 'Coût rendu', 'Landed cost', "التكلفة عند الوصول"), align: 'right', width: 1.1 },
          ],
          rows: opps.map((o, i) => ({
            rank: String(i + 1),
            market: o.destination_iso3,
            score: o.score_available ? pct(o.end_to_end_score) : '—',
            need: o.market_need?.available ? `${Math.round(o.market_need.value).toLocaleString('en-US')} ${o.market_need.unit || ''}` : '—',
            tariffAdv: o.tariff_benefit?.available && o.tariff_benefit.tariff_advantage_pct != null ? `${o.tariff_benefit.tariff_advantage_pct}%` : '—',
            landedCost: o.landed_cost?.available ? money(o.landed_cost.value_usd, language) : '—',
          })),
        },
      });
    }
    if (rep.data_quality?.note) sections.push({ title: pick(language, 'Notes', 'Notes', "ملاحظات"), paragraphs: [rep.data_quality.note] });
    return {
      badge: `S2 · ${producer}`,
      title: `${pick(language, 'Export direct', 'Direct export', "التصدير المباشر")} SH ${hsCode} — ${producer}`,
      subtitle: `${rep.candidates_considered ?? '—'} ${pick(language, 'marchés candidats', 'candidate markets', "سوقًا مرشحة")} · ${rep.deep_dived ?? '—'} ${pick(language, 'analysés', 'deep-dived', "محلَّلة")}`,
      filename: opportunityPdfFilename('S2', `${producer}_${hsCode}`),
      kpis: [
        { label: pick(language, "Code produit", "Product code", "رمز المنتج"), value: hsCode, accent: 'gold' },
        { label: pick(language, "Producteur", "Producer", "المنتِج"), value: producer, accent: 'green' },
        { label: pick(language, "Marchés classés", "Ranked markets", "الأسواق المرتَّبة"), value: String(opps.length), accent: 'terra' },
      ],
      sections,
      source: pick(language, 'FAOSTAT / USGS / UNIDO · OEC BACI · tarifs ZLECAf', 'FAOSTAT / USGS / UNIDO · OEC BACI · tarifs ZLECAf', 'FAOSTAT / USGS / UNIDO · OEC BACI · تعريفات زليكاف'),
    };
  }, [rep, hsCode, producer, supply, opps, language]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
        <div>
          <div style={label}>{pick(language, "Producteur", "Producer", "المنتِج")}</div>
          <Sel value={producer} onChange={setProducer} countries={countries} testid="s2-producer" />
        </div>
        <div>
          <div style={label}>{pick(language, "Code SH", "HS code", "رمز SH")}</div>
          <input value={hsCode} onChange={(e) => setHsCode(e.target.value)} data-testid="s2-hs" style={{ padding: "8px 10px", borderRadius: 8, width: 110 }} />
        </div>
        <div>
          <div style={label}>{pick(language, "Nb marchés", "Markets", "عدد الأسواق")}</div>
          <input value={topK} onChange={(e) => setTopK(e.target.value)} data-testid="s2-topk" style={{ padding: "8px 10px", borderRadius: 8, width: 70 }} />
        </div>
        <div>
          <div style={label}>{pick(language, "Valeur FOB (USD)", "FOB value (USD)", "القيمة فوب (USD)")}</div>
          <input value={goodsValue} onChange={(e) => setGoodsValue(e.target.value)} data-testid="s2-value" style={{ padding: "8px 10px", borderRadius: 8, width: 130 }} />
        </div>
        <button onClick={run} disabled={loading} className="afcfta-btn afcfta-btn-primary" data-testid="s2-run" style={{ padding: "10px 18px", borderRadius: 8 }}>
          {loading ? (pick(language, "Analyse…", "Analyzing…", "جارٍ التحليل…")) : pick(language, "Classer les marchés", "Rank markets", "ترتيب الأسواق")}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={language} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "var(--danger)" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={card}>
            <div style={{ ...label, fontWeight: 700 }}>
              {pick(language, "Production du producteur", "Producer supply", "إنتاج المنتِج")} — {rep.inputs?.producer_iso3}
            </div>
            {supply.available ? (
              <div style={{ fontSize: 14, marginTop: 4 }}>
                {supply.commodity} · {dash(supply.continental_share_pct, " %")} {pick(language, "de la production continentale", "of continental production", "من الإنتاج القاري")}
                {supply.rank ? ` · ${pick(language, "rang", "rank", "الترتيب")} #${supply.rank}` : ""}
              </div>
            ) : (
              <div style={{ color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                {pick(language, "Pas de production détectée pour ce produit.", "No production detected for this product.", "لم يُرصد إنتاج لهذا المنتج.")}
              </div>
            )}
            <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>
              {rep.candidates_considered} {pick(language, "marchés candidats · ", "candidate markets · ", "سوقًا مرشحة · ")}
              {rep.deep_dived} {pick(language, "analysés en profondeur", "deep-dived", "محلَّلة بالتفصيل")}
            </div>
          </div>

          <div style={card}>
            <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
              {pick(language, "Marchés d'export classés", "Ranked export markets", "أسواق التصدير المرتَّبة")}
            </div>
            <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={th}>#</th>
                  <th style={th}>{pick(language, "Marché", "Market", "السوق")}</th>
                  <th style={th}>{pick(language, "Score", "Score", "النتيجة")}</th>
                  <th style={th}>{pick(language, "Besoin estimé", "Estimated need", "الحاجة المقدَّرة")}</th>
                  <th style={th}>{pick(language, "Avantage tarif", "Tariff adv.", "الميزة التعريفية")}</th>
                  <th style={th}>{pick(language, "Conteneurs", "Containers", "الحاويات")}</th>
                  <th style={th}>{pick(language, "Coût rendu", "Landed cost", "التكلفة عند الوصول")}</th>
                  <th style={th}></th>
                </tr>
              </thead>
              <tbody>
                {opps.map((o, i) => (
                  <tr key={o.destination_iso3} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                    <td style={td}>{i + 1}</td>
                    <td style={td}>
                      <strong>{o.destination_iso3}</strong>
                    </td>
                    <td style={td}>{o.score_available ? pct(o.end_to_end_score) : "—"}</td>
                    <td style={td}>
                      {o.market_need?.available ? num(Math.round(o.market_need.value), o.market_need.unit) : "—"}
                    </td>
                    <td
                      style={td}
                      title={
                        o.tariff_benefit?.hs6_used
                          ? `${pick(language, "Sous-position", "Sub-heading", "البند الفرعي")} HS6 ${o.tariff_benefit.hs6_used}`
                          : undefined
                      }
                    >
                      {o.tariff_benefit?.available ? dash(o.tariff_benefit.tariff_advantage_pct, " %") : "—"}
                    </td>
                    <td
                      style={td}
                      title={
                        o.landed_cost?.breakdown?.estimated_weight_kg
                          ? `${pick(language, "Poids estimé", "Est. weight", "الوزن المقدَّر")} ${Math.round(
                              o.landed_cost.breakdown.estimated_weight_kg
                            ).toLocaleString()} kg${
                              o.landed_cost.breakdown.weight_source === "estimé"
                                ? pick(language, " (estimé depuis la valeur FOB)", " (estimated from FOB value)", " (مقدَّر انطلاقًا من القيمة فوب)")
                                : ""
                            }`
                          : undefined
                      }
                    >
                      {o.landed_cost?.breakdown?.containers_needed
                        ? `${o.landed_cost.breakdown.containers_needed} × ${
                            o.landed_cost.breakdown.container_type === "feu" ? "40′" : "20′"
                          }`
                        : "—"}
                    </td>
                    <td style={td}>{o.landed_cost?.available ? money(o.landed_cost.value_usd, language) : "—"}</td>
                    <td style={td}>
                      <button
                        onClick={() => onAnalyze && onAnalyze(producer, o.destination_iso3, hsCode, goodsValue)}
                        data-testid={`s2-analyze-${o.destination_iso3}`}
                        className="afcfta-btn afcfta-btn-secondary"
                        style={{ padding: "4px 10px", borderRadius: 6, fontSize: 12 }}
                      >
                        {pick(language, "Analyser ▸", "Analyze ▸", "تحليل ◂")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)" }}>{rep.data_quality?.note}</div>
        </div>
      )}
    </div>
  );
}

/* ── Mode: S1 — import inputs → local production → export ──────────────────── */
function TransformationView({ countries, fr, onAnalyze, language = fr ? "fr" : "en" }) {
  const [inputHs, setInputHs] = useState("1801");
  const [inputOrigin, setInputOrigin] = useState("GHA");
  const [producer, setProducer] = useState("CIV");
  const [finishedHs, setFinishedHs] = useState("1803");
  const [destination, setDestination] = useState("NGA");
  const [inputValue, setInputValue] = useState("40000");
  const [finishedValue, setFinishedValue] = useState("70000");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rep, setRep] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setRep(null);
    try {
      const params = new URLSearchParams({
        input_hs_code: inputHs,
        input_origin: inputOrigin,
        producer,
        finished_hs_code: finishedHs,
        destination,
      });
      if (inputValue) params.set("input_value_usd", inputValue);
      if (finishedValue) params.set("finished_value_usd", finishedValue);
      const res = await axios.get(`${API}/reports/transformation?${params.toString()}`);
      setRep(res.data);
    } catch (e) {
      setError(pick(language, "Impossible de générer le scénario.", "Could not generate scenario.", "تعذّر إنشاء السيناريو."));
    } finally {
      setLoading(false);
    }
  };

  const leg1 = rep?.leg1_input_import || {};
  const leg2 = rep?.leg2_production || {};
  const va = rep?.value_added || {};
  const feas = rep?.feasibility || {};
  const exportScore = feas.export_end_to_end_score;

  // Le PDF détaille les 3 maillons de la chaîne (import intrant, production
  // locale, export fini) + valeur ajoutée — pas un squelette (une section
  // `text` n'est pas un type du bâtisseur : PDF vide).
  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    const sections = [
      {
        title: pick(language, '1 · Import de l’intrant', '1 · Input import', "1 · استيراد المُدخل"),
        keyValues: [
          { label: pick(language, 'Intrant', 'Input', "المُدخل"), value: `SH ${inputHs} — ${inputOrigin}` },
          { label: pick(language, 'Coût rendu intrant', 'Input landed cost', "تكلفة المُدخل عند الوصول"), value: leg1.landed_cost?.available ? money(leg1.landed_cost.value_usd, language) : '—' },
          { label: pick(language, 'Avantage tarifaire intrant', 'Input tariff advantage', "الميزة التعريفية للمُدخل"), value: leg1.tariff?.available && leg1.tariff.tariff_advantage_pct != null ? `${leg1.tariff.tariff_advantage_pct}%` : '—' },
        ],
      },
      {
        title: pick(language, '2 · Production locale', '2 · Local production', "2 · الإنتاج المحلي"),
        keyValues: [
          { label: pick(language, 'Statut', 'Status', "الحالة"), value: leg2.available ? (pick(language, 'Confirmée', 'Confirmed', "مؤكَّد")) : (pick(language, 'Non détectée', 'Not detected', "غير مرصود")) },
          ...(leg2.available ? [
            { label: pick(language, 'Commodité', 'Commodity', "السلعة"), value: leg2.commodity || '—' },
            { label: pick(language, 'Part continentale', 'Continental share', "الحصة القارية"), value: leg2.continental_share_pct != null ? `${leg2.continental_share_pct}%` : '—' },
          ] : []),
        ],
      },
      {
        title: pick(language, '3 · Export du produit fini', '3 · Finished product export', "3 · تصدير المنتج النهائي"),
        keyValues: [
          { label: pick(language, 'Produit fini', 'Finished product', "المنتج النهائي"), value: `SH ${finishedHs} → ${destination}` },
          { label: pick(language, 'Score export', 'Export score', "نتيجة التصدير"), value: exportScore != null ? pct(exportScore) : '—' },
        ],
      },
    ];
    if (va.available) {
      sections.push({
        title: pick(language, 'Valeur ajoutée brute', 'Gross value added', "القيمة المضافة الإجمالية"),
        keyValues: [
          { label: pick(language, 'Valeur ajoutée', 'Value added', "القيمة المضافة"), value: money(va.gross_value_added_usd, language) },
          { label: pick(language, 'Marge brute', 'Gross margin', "الهامش الإجمالي"), value: va.gross_margin_pct != null ? `${va.gross_margin_pct}%` : '—' },
        ],
      });
      if (va.note) sections.push({ title: pick(language, 'Note', 'Note', "ملاحظة"), paragraphs: [va.note] });
    }
    if (rep.data_quality?.note) sections.push({ title: pick(language, 'Qualité des données', 'Data quality', "جودة البيانات"), paragraphs: [rep.data_quality.note] });
    return {
      badge: `S1 · ${producer}`,
      title: `${pick(language, 'Transformation', 'Transformation', "التحويل")} ${inputHs} → ${finishedHs} — ${producer}`,
      subtitle: `${inputOrigin} → ${producer} → ${destination}`,
      filename: opportunityPdfFilename('S1', `${producer}_${finishedHs}`),
      kpis: [
        { label: pick(language, "Produit fini", "Finished product", "المنتج النهائي"), value: finishedHs, accent: 'gold' },
        { label: pick(language, "Valeur ajoutée", "Value added", "القيمة المضافة"), value: va.available ? money(va.gross_value_added_usd, language) : '—', accent: 'green' },
        { label: pick(language, "Score export", "Export score", "نتيجة التصدير"), value: exportScore != null ? pct(exportScore) : '—', accent: 'terra' },
      ],
      sections,
      source: pick(language, 'FAOSTAT / USGS / UNIDO · tarifs ZLECAf · OEC', 'FAOSTAT / USGS / UNIDO · tarifs ZLECAf · OEC', 'FAOSTAT / USGS / UNIDO · تعريفات زليكاف · OEC'),
    };
  }, [rep, finishedHs, inputHs, inputOrigin, producer, destination, leg1, leg2, va, exportScore, language]);

  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
        <div>
          <div style={label}>{pick(language, "Intrant SH", "Input HS", "رمز SH للمُدخل")}</div>
          <input value={inputHs} onChange={(e) => setInputHs(e.target.value)} data-testid="s1-input-hs" style={{ padding: "8px 10px", borderRadius: 8, width: 90 }} />
        </div>
        <div>
          <div style={label}>{pick(language, "Origine intrant", "Input origin", "منشأ المُدخل")}</div>
          <Sel value={inputOrigin} onChange={setInputOrigin} countries={countries} testid="s1-input-origin" />
        </div>
        <div>
          <div style={label}>{pick(language, "Producteur", "Producer", "المنتِج")}</div>
          <Sel value={producer} onChange={setProducer} countries={countries} testid="s1-producer" />
        </div>
        <div>
          <div style={label}>{pick(language, "Produit fini SH", "Finished HS", "رمز SH للمنتج النهائي")}</div>
          <input value={finishedHs} onChange={(e) => setFinishedHs(e.target.value)} data-testid="s1-finished-hs" style={{ padding: "8px 10px", borderRadius: 8, width: 90 }} />
        </div>
        <div>
          <div style={label}>{pick(language, "Marché export", "Export market", "سوق التصدير")}</div>
          <Sel value={destination} onChange={setDestination} countries={countries} testid="s1-destination" />
        </div>
        <div>
          <div style={label}>{pick(language, "Val. intrant", "Input val.", "قيمة المُدخل")}</div>
          <input value={inputValue} onChange={(e) => setInputValue(e.target.value)} data-testid="s1-input-value" style={{ padding: "8px 10px", borderRadius: 8, width: 100 }} />
        </div>
        <div>
          <div style={label}>{pick(language, "Val. fini", "Finished val.", "قيمة المنتج النهائي")}</div>
          <input value={finishedValue} onChange={(e) => setFinishedValue(e.target.value)} data-testid="s1-finished-value" style={{ padding: "8px 10px", borderRadius: 8, width: 100 }} />
        </div>
        <button onClick={run} disabled={loading} className="afcfta-btn afcfta-btn-primary" data-testid="s1-run" style={{ padding: "10px 18px", borderRadius: 8 }}>
          {loading ? (pick(language, "Analyse…", "Analyzing…", "جارٍ التحليل…")) : pick(language, "Analyser la chaîne", "Analyze chain", "تحليل السلسلة")}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={language} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "var(--danger)" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
            <div style={card} data-testid="s1-leg1">
              <div style={{ ...label, fontWeight: 700 }}>1 · {pick(language, "Import intrant", "Import input", "استيراد المُدخل")}</div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>
                {leg1.landed_cost?.available ? money(leg1.landed_cost.value_usd, language) : "—"}
              </div>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                {pick(language, "Coût rendu intrant", "Input landed cost", "تكلفة المُدخل عند الوصول")}
                {leg1.tariff?.available ? ` · ${pick(language, "tarif", "tariff", "التعريفة")} ${dash(leg1.tariff.tariff_advantage_pct, " %")}` : ""}
              </div>
            </div>
            <div style={card} data-testid="s1-leg2">
              <div style={{ ...label, fontWeight: 700 }}>2 · {pick(language, "Production locale", "Local production", "الإنتاج المحلي")}</div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>
                {leg2.available ? (pick(language, "Confirmée ✓", "Confirmed ✓", "مؤكَّد ✓")) : pick(language, "Non détectée", "Not detected", "غير مرصود")}
              </div>
              {leg2.available && (
                <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                  {leg2.commodity} · {dash(leg2.continental_share_pct, " %")}
                </div>
              )}
            </div>
            <div style={card} data-testid="s1-leg3">
              <div style={{ ...label, fontWeight: 700 }}>3 · {pick(language, "Export produit fini", "Export finished", "تصدير المنتج النهائي")}</div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>{exportScore != null ? pct(exportScore) : "—"}</div>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                {pick(language, "Score export → ", "Export score → ", "نتيجة التصدير ← ")}
                {rep.inputs?.destination_iso3}
              </div>
              <button
                onClick={() =>
                  onAnalyze &&
                  onAnalyze(rep.inputs?.producer_iso3, rep.inputs?.destination_iso3, rep.inputs?.finished_hs_code, finishedValue)
                }
                data-testid="s1-analyze-export"
                className="afcfta-btn afcfta-btn-secondary"
                style={{ padding: "4px 10px", borderRadius: 6, fontSize: 12, marginTop: 8 }}
              >
                {pick(language, "Analyser l'export ▸", "Analyze export ▸", "تحليل التصدير ◂")}
              </button>
            </div>
            <div style={card} data-testid="s1-value-added">
              <div style={{ ...label, fontWeight: 700 }}>{pick(language, "Valeur ajoutée brute", "Gross value added", "القيمة المضافة الإجمالية")}</div>
              {va.available ? (
                <>
                  <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>
                    {money(va.gross_value_added_usd, language)}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                    {pick(language, "Marge", "Margin", "الهامش")} {dash(va.gross_margin_pct, " %")}
                  </div>
                </>
              ) : (
                <div style={{ color: "var(--afcfta-muted,#667)", marginTop: 4 }}>—</div>
              )}
            </div>
          </div>
          {va.available && (
            <div style={{ fontSize: 12, color: "#9a6700" }}>⚠ {va.note}</div>
          )}
          <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)" }}>{rep.data_quality?.note}</div>
        </div>
      )}
    </div>
  );
}

/* ── Mode: S3 — national need estimation (transparent cascade) ─────────────── */
function ImportOpportunitiesView({ countries, fr, onAnalyze, language = fr ? "fr" : "en" }) {
  const [country, setCountry] = useState("DZA");
  const [topK, setTopK] = useState("6");
  const [withImports, setWithImports] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rep, setRep] = useState(null);

  const run = async () => {
    // Borne top_k à [1, 20] (contrainte de l'API) et normalise une saisie
    // vide/non numérique à 6 — évite une 422 et un message générique.
    const parsed = parseInt(topK, 10);
    const safeTopK = Number.isNaN(parsed) ? 6 : Math.min(20, Math.max(1, parsed));
    if (String(safeTopK) !== topK) setTopK(String(safeTopK));
    setLoading(true);
    setError(null);
    setRep(null);
    try {
      const params = new URLSearchParams({ country, top_k: String(safeTopK) });
      if (withImports) params.set("with_observed_imports", "true");
      const res = await axios.get(`${API}/reports/import-opportunities?${params.toString()}`);
      setRep(res.data);
    } catch (e) {
      setError(pick(language, "Impossible de générer le scan d'importation.", "Could not run the import scan.", "تعذّر إجراء مسح الواردات."));
    } finally {
      setLoading(false);
    }
  };

  const opps = rep?.ranked_opportunities || [];

  // Le PDF reprend le tableau des opportunités classées de l'écran — pas un
  // squelette (une section `text` n'est pas un type du bâtisseur : PDF vide).
  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    const sections = [];
    if (opps.length) {
      sections.push({
        title: pick(language, `Meilleures opportunités d'importation — ${country}`, `Best import opportunities — ${country}`, `أفضل فرص الاستيراد — ${country}`),
        table: {
          columns: [
            { key: 'product', label: pick(language, 'Produit', 'Product', "المنتج"), width: 2 },
            { key: 'need', label: pick(language, 'Besoin estimé', 'Est. need', "الحاجة المقدَّرة"), align: 'right', width: 1.2 },
            { key: 'supplier', label: pick(language, 'Fournisseur conseillé', 'Suggested supplier', "المورّد المقترح"), width: 1.2 },
            { key: 'tariffAdv', label: pick(language, 'Avantage tarifaire', 'Tariff advantage', "الميزة التعريفية"), align: 'right', width: 1 },
            { key: 'score', label: pick(language, 'Score', 'Score', 'النتيجة'), align: 'right', width: 0.7 },
          ],
          rows: opps.map((o) => ({
            product: `${o.commodity || '—'} (SH ${o.hs_code})`,
            need: o.market_need?.value != null ? `${Math.round(o.market_need.value).toLocaleString('en-US')} ${o.unit || ''}` : '—',
            supplier: `${o.best_supplier?.country_iso3 || '—'}${o.best_supplier?.production_share_pct != null ? ` (${o.best_supplier.production_share_pct}% ${pick(language, 'prod.', 'prod.', 'من الإنتاج')})` : ''}`,
            tariffAdv: o.best_supplier?.tariff_advantage_pct != null ? `${o.best_supplier.tariff_advantage_pct}%` : '—',
            score: o.end_to_end_score ?? '—',
          })),
        },
      });
    }
    return {
      badge: `S4 · ${country}`,
      title: pick(language, `Opportunités d'importation — ${country}`, `Import opportunities — ${country}`, `فرص الاستيراد — ${country}`),
      subtitle: `${rep.products_scanned ?? 0} ${pick(language, 'produits scannés', 'products scanned', "منتجًا ممسوحًا")} · ${rep.candidates_retained ?? 0} ${pick(language, 'retenus', 'retained', "محتفَظ بها")} · ${rep.deep_dived ?? 0} ${pick(language, 'analysés', 'deep-dived', "محلَّلة")}`,
      filename: `s4-importations-${country}`,
      kpis: [
        { label: pick(language, "Pays", "Country", "البلد"), value: country, accent: 'gold' },
        { label: pick(language, "Produits scannés", "Products scanned", "المنتجات الممسوحة"), value: String(rep.products_scanned || 0), accent: 'green' },
        { label: pick(language, "Opportunités classées", "Ranked opportunities", "الفرص المرتَّبة"), value: String(opps.length), accent: 'terra' },
      ],
      sections,
      source: pick(language, 'FAOSTAT / USGS / UNIDO · OEC BACI · tarifs ZLECAf', 'FAOSTAT / USGS / UNIDO · OEC BACI · tarifs ZLECAf', 'FAOSTAT / USGS / UNIDO · OEC BACI · تعريفات زليكاف'),
    };
  }, [rep, country, opps, language]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
        <div>
          <div style={label}>{pick(language, "Pays importateur", "Importing country", "البلد المستورد")}</div>
          <Sel value={country} onChange={setCountry} countries={countries} testid="s4-country" />
        </div>
        <div>
          <div style={label}>{pick(language, "Produits analysés", "Products deep-dived", "المنتجات المحلَّلة")}</div>
          <input value={topK} onChange={(e) => setTopK(e.target.value)} data-testid="s4-topk" style={{ padding: "8px 10px", borderRadius: 8, width: 70 }} />
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
          <input type="checkbox" checked={withImports} onChange={(e) => setWithImports(e.target.checked)} data-testid="s4-imports" />
          {pick(language, "Imports observés (OEC)", "Observed imports (OEC)", "الواردات المرصودة (OEC)")}
        </label>
        <button onClick={run} disabled={loading} className="afcfta-btn afcfta-btn-primary" data-testid="s4-run" style={{ padding: "10px 18px", borderRadius: 8 }}>
          {loading ? (pick(language, "Scan…", "Scanning…", "جارٍ المسح…")) : pick(language, "Scanner les importations", "Scan imports", "مسح الواردات")}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={language} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "var(--danger)" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={card} data-testid="s4-result">
            <div style={{ ...label, marginBottom: 4 }}>
              {pick(language, `Meilleures opportunités d'importation — ${country}`, `Best import opportunities — ${country}`, `أفضل فرص الاستيراد — ${country}`)}
            </div>
            <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginBottom: 10 }}>
              {rep.products_scanned} {pick(language, "produits scannés", "products scanned", "منتجًا ممسوحًا")} · {rep.candidates_retained}{" "}
              {pick(language, "retenus", "retained", "محتفَظ بها")} · {rep.deep_dived} {pick(language, "analysés en profondeur", "deep-dived", "محلَّلة بالتفصيل")}
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: "1px solid var(--afcfta-border,#dde)" }}>
                    <th style={{ padding: "6px 8px" }}>{pick(language, "Produit", "Product", "المنتج")}</th>
                    <th style={{ padding: "6px 8px" }}>{pick(language, "Besoin estimé", "Est. need", "الحاجة المقدَّرة")}</th>
                    <th style={{ padding: "6px 8px" }}>{pick(language, "Fournisseur conseillé", "Suggested supplier", "المورّد المقترح")}</th>
                    <th style={{ padding: "6px 8px" }}>{pick(language, "Avantage tarifaire", "Tariff advantage", "الميزة التعريفية")}</th>
                    <th style={{ padding: "6px 8px" }}>{pick(language, "Score", "Score", "النتيجة")}</th>
                    <th style={{ padding: "6px 8px" }} />
                  </tr>
                </thead>
                <tbody>
                  {opps.map((o) => (
                    <tr key={o.hs_code} style={{ borderBottom: "1px solid var(--afcfta-border,#eee)" }} data-testid={`s4-row-${o.hs_code}`}>
                      <td style={{ padding: "6px 8px" }}>
                        <strong>{o.commodity}</strong>
                        <span style={{ color: "var(--afcfta-muted,#667)", marginLeft: 6, fontSize: 11 }}>SH {o.hs_code}</span>
                        {!o.local_production?.recorded && (
                          <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)" }}>
                            {pick(language, "production locale non enregistrée", "local production not recorded", "الإنتاج المحلي غير مسجَّل")}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: "6px 8px", whiteSpace: "nowrap" }}>
                        {num(Math.round(o.market_need?.value || 0), o.unit)}
                        {o.market_need?.is_estimation && (
                          <span style={{ fontSize: 10, marginLeft: 4, color: "var(--afcfta-muted,#667)" }}>
                            (L{o.market_need.estimation_level})
                          </span>
                        )}
                        {o.observed_imports?.import_value_usd && (
                          <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)" }}>
                            {pick(language, "importe déjà", "already imports", "يستورد حاليًا")} {money(o.observed_imports.import_value_usd, language)}
                            {tonnes(o.observed_imports.import_quantity_tonnes, language) &&
                              ` · ${tonnes(o.observed_imports.import_quantity_tonnes, language)}`}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: "6px 8px" }}>
                        <strong>{o.best_supplier?.country_iso3}</strong>
                        <span style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginLeft: 4 }}>
                          {o.best_supplier?.production_share_pct != null ? `${o.best_supplier.production_share_pct}% ${pick(language, 'prod.', 'prod.', 'من الإنتاج')}` : ""}
                        </span>
                      </td>
                      <td style={{ padding: "6px 8px", whiteSpace: "nowrap" }}>
                        {o.best_supplier?.tariff_advantage_pct != null ? `${o.best_supplier.tariff_advantage_pct} %` : "—"}
                        <div style={{ fontSize: 10, color: "var(--afcfta-muted,#667)" }}>{o.best_supplier?.trade_regime}</div>
                      </td>
                      <td style={{ padding: "6px 8px", fontWeight: 700 }}>{o.end_to_end_score ?? "—"}</td>
                      <td style={{ padding: "6px 8px" }}>
                        {onAnalyze && o.best_supplier?.country_iso3 && (
                          <button
                            onClick={() => onAnalyze(o.best_supplier.country_iso3, country, o.hs_code)}
                            className="afcfta-btn afcfta-btn-secondary"
                            data-testid={`s4-analyze-${o.hs_code}`}
                            style={{ padding: "4px 10px", borderRadius: 6, fontSize: 12 }}
                          >
                            {pick(language, "Analyser ▸", "Analyze ▸", "تحليل ◂")}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 10 }}>
              {rep.data_quality?.note}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function NationalNeedView({ countries, fr, onAnalyze, prefill, language = fr ? "fr" : "en" }) {
  const [hsCode, setHsCode] = useState("180100");
  const [country, setCountry] = useState("NGA");
  const [withImports, setWithImports] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rep, setRep] = useState(null);

  const run = async (overrides = {}) => {
    const o = { hsCode, country, withImports, ...overrides };
    setLoading(true);
    setError(null);
    setRep(null);
    try {
      const params = new URLSearchParams({ hs_code: o.hsCode, country: o.country });
      if (o.withImports) params.set("with_observed_imports", "true");
      const res = await axios.get(`${API}/reports/national-need?${params.toString()}`);
      setRep(res.data);
    } catch (e) {
      setError(pick(language, "Impossible d'estimer le besoin.", "Could not estimate need.", "تعذّر تقدير الحاجة."));
    } finally {
      setLoading(false);
    }
  };

  // Handoff depuis le module Statistiques (recherche SH2/4/6) : pays + code SH
  // pré-remplis, signal d'import OEC activé, exécution automatique.
  useEffect(() => {
    if (!prefill || !prefill.k) return;
    if (prefill.country) setCountry(prefill.country);
    if (prefill.hsCode) setHsCode(prefill.hsCode);
    if (prefill.withImports) setWithImports(true);
    run({ country: prefill.country, hsCode: prefill.hsCode, withImports: !!prefill.withImports });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefill?.k]);

  const inp = rep?.inputs || {};

  // Le PDF détaille l'estimation ET ses intrants de calcul (transparence),
  // comme à l'écran — pas un squelette (une section `text` n'est pas un type
  // du bâtisseur : PDF vide).
  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    const sections = [];
    if (rep.available) {
      const needKv = [
        { label: pick(language, 'Besoin estimé', 'Estimated need', "الحاجة المقدَّرة"), value: `${Math.round(rep.value || 0).toLocaleString('en-US')} ${rep.unit || ''}` },
        { label: pick(language, 'Méthode', 'Method', "المنهجية"), value: rep.method || '—' },
      ];
      if (rep.is_estimation) needKv.push({ label: pick(language, 'Statut', 'Status', "الحالة"), value: `${pick(language, 'Estimation', 'Estimate', "تقدير")}${rep.estimation_level ? ` (L${rep.estimation_level})` : ''}` });
      if (rep.observed_imports?.import_value_usd) needKv.push({ label: pick(language, 'Imports observés', 'Observed imports', "الواردات المرصودة"), value: money(rep.observed_imports.import_value_usd, language) });
      if (rep.suggested_supplier?.iso3) needKv.push({ label: pick(language, 'Fournisseur conseillé', 'Suggested supplier', "المورّد المقترح"), value: rep.suggested_supplier.iso3 });
      sections.push({ title: pick(language, `Besoin national — ${country}`, `National need — ${country}`, `الحاجة الوطنية — ${country}`), keyValues: needKv });

      const inputKv = [
        { label: pick(language, 'Population', 'Population', "السكان"), value: inp.population != null ? Number(inp.population).toLocaleString('en-US') : '—' },
        { label: pick(language, 'Production continentale', 'Continental production', "الإنتاج القاري"), value: inp.continental_production != null ? `${Number(inp.continental_production).toLocaleString('en-US')} ${rep.unit || ''}` : '—' },
        { label: pick(language, 'Réf. par habitant', 'Per-capita ref.', "المرجع للفرد"), value: inp.per_capita_reference != null ? String(inp.per_capita_reference) : '—' },
      ];
      if (inp.continental_imports_tonnes != null) inputKv.push({ label: pick(language, 'Imports continentaux', 'Continental imports', "الواردات القارية"), value: `${Number(inp.continental_imports_tonnes).toLocaleString('en-US')} ${rep.unit || ''}` });
      if (inp.gdp_adjustment_factor != null) inputKv.push({ label: pick(language, 'Facteur PIB/hab', 'GDP/cap factor', "معامل نصيب الفرد من الناتج المحلي الإجمالي"), value: String(inp.gdp_adjustment_factor) });
      sections.push({ title: pick(language, 'Intrants du calcul (transparence)', 'Computation inputs (transparency)', "مُدخلات الحساب (الشفافية)"), keyValues: inputKv });
    }
    if (rep.note) sections.push({ title: pick(language, 'Note', 'Note', "ملاحظة"), paragraphs: [rep.note] });
    return {
      badge: `S3 · ${country}`,
      title: pick(language, `Besoin national SH ${hsCode} — ${country}`, `National need HS ${hsCode} — ${country}`, `الحاجة الوطنية SH ${hsCode} — ${country}`),
      subtitle: rep.available && rep.method ? rep.method : undefined,
      filename: opportunityPdfFilename('S3', `${country}_${hsCode}`),
      kpis: [
        { label: pick(language, "Code produit", "Product code", "رمز المنتج"), value: hsCode, accent: 'gold' },
        { label: pick(language, "Pays", "Country", "البلد"), value: country, accent: 'green' },
        { label: pick(language, "Besoin estimé", "Estimated need", "الحاجة المقدَّرة"), value: rep.available ? `${Math.round(rep.value || 0).toLocaleString('en-US')} ${rep.unit || ''}` : '—', accent: 'terra' },
      ],
      sections,
      source: (rep.sources || []).map((s) => srcText(s)).filter(Boolean).join(' · ') || pick(language, 'FAOSTAT / Banque mondiale / OEC', 'FAOSTAT / Banque mondiale / OEC', 'FAOSTAT / البنك الدولي / OEC'),
    };
  }, [rep, hsCode, country, inp, language]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
        <div>
          <div style={label}>{pick(language, "Pays", "Country", "البلد")}</div>
          <Sel value={country} onChange={setCountry} countries={countries} testid="s3-country" />
        </div>
        <div>
          <div style={label}>{pick(language, "Code SH", "HS code", "رمز SH")}</div>
          <input value={hsCode} onChange={(e) => setHsCode(e.target.value)} data-testid="s3-hs" style={{ padding: "8px 10px", borderRadius: 8, width: 120 }} />
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
          <input type="checkbox" checked={withImports} onChange={(e) => setWithImports(e.target.checked)} data-testid="s3-imports" />
          {pick(language, "Signal d'import (OEC, lent)", "Import signal (OEC, slow)", "إشارة الاستيراد (OEC، بطيئة)")}
        </label>
        <button onClick={() => run()} disabled={loading} className="afcfta-btn afcfta-btn-primary" data-testid="s3-run" style={{ padding: "10px 18px", borderRadius: 8 }}>
          {loading ? (pick(language, "Estimation…", "Estimating…", "جارٍ التقدير…")) : pick(language, "Estimer le besoin", "Estimate need", "تقدير الحاجة")}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={language} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "var(--danger)" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={card} data-testid="s3-result">
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <span style={{ ...label, margin: 0 }}>
                {pick(language, "Besoin national", "National need", "الحاجة الوطنية")} — {country}
              </span>
              {rep.available && (
                <EstBadge isEstimation={rep.is_estimation} level={rep.estimation_level} language={language} />
              )}
            </div>
            {rep.available ? (
              <>
                <div style={{ fontSize: 26, fontWeight: 800, marginTop: 6 }}>
                  {num(Math.round(rep.value), rep.unit)}
                </div>
                {rep.plausibility?.caveat && (
                  <div style={{
                    fontSize: 12, color: "var(--gold)", background: "#fef3c7",
                    border: "1px solid #fbbf24", borderRadius: 6, padding: "8px 10px",
                    marginTop: 8, lineHeight: 1.45,
                  }}>
                    ⚠ {pick(language, "Seuil de vraisemblance", "Plausibility threshold", "عتبة المعقولية")} : {rep.plausibility.caveat}
                  </div>
                )}
                {rep.observed_imports?.import_value_usd && (
                  <div style={{ fontSize: 13, marginTop: 4 }}>
                    {pick(language, "Importe déjà", "Already imports", "يستورد حاليًا")} : {money(rep.observed_imports.import_value_usd, language)}
                    {tonnes(rep.observed_imports.import_quantity_tonnes, language) && (
                      <span style={{ color: "var(--afcfta-muted,#667)" }}>
                        {" "}· {tonnes(rep.observed_imports.import_quantity_tonnes, language)}
                      </span>
                    )}
                  </div>
                )}
                <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                  {pick(language, "Méthode", "Method", "المنهجية")} : {rep.method}
                </div>
                {rep.suggested_supplier?.iso3 && onAnalyze && (
                  <button
                    onClick={() => onAnalyze(rep.suggested_supplier.iso3, country, hsCode)}
                    data-testid="s3-analyze"
                    className="afcfta-btn afcfta-btn-secondary"
                    style={{ padding: "6px 12px", borderRadius: 6, fontSize: 13, marginTop: 10 }}
                  >
                    {pick(language, "Analyser l'opportunité", "Analyze opportunity", "تحليل الفرصة")} : {rep.suggested_supplier.iso3} → {country} ▸
                  </button>
                )}
                {!rep.suggested_supplier?.iso3 && rep.suggested_supplier_suppressed_reason && (
                  <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 10, fontStyle: "italic" }}>
                    {rep.suggested_supplier_suppressed_reason}
                  </div>
                )}
              </>
            ) : (
              <div style={{ color: "var(--afcfta-muted,#667)", marginTop: 6 }}>{rep.note || "—"}</div>
            )}
          </div>

          {rep.available && (
            <div style={card}>
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {pick(language, "Intrants du calcul (transparence)", "Computation inputs (transparency)", "مُدخلات الحساب (الشفافية)")}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, fontSize: 13 }}>
                <div>{pick(language, "Population", "Population", "السكان")} : {num(inp.population)}</div>
                <div>{pick(language, "Production continentale", "Continental production", "الإنتاج القاري")} : {num(inp.continental_production, rep.unit)}</div>
                {inp.continental_imports_tonnes != null && (
                  <div>{pick(language, "Imports continentaux", "Continental imports", "الواردات القارية")} : {num(inp.continental_imports_tonnes, rep.unit)}</div>
                )}
                <div>{pick(language, "Réf. par habitant", "Per-capita ref.", "المرجع للفرد")} : {num(inp.per_capita_reference)}</div>
                {inp.gdp_adjustment_factor != null && (
                  <div>{pick(language, "Facteur PIB/hab", "GDP/cap factor", "معامل نصيب الفرد من الناتج المحلي الإجمالي")} : {num(inp.gdp_adjustment_factor)}</div>
                )}
                {rep.implied_per_capita?.value != null && (
                  <div style={{ fontWeight: 700 }}>
                    {pick(language, "Besoin par habitant", "Need per capita", "الحاجة للفرد")} : {num(rep.implied_per_capita.value)} {rep.implied_per_capita.unit}
                  </div>
                )}
              </div>
              {rep.implied_per_capita?.value != null && (
                <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 6, fontStyle: "italic" }}>
                  {pick(language, `Contrôle de vraisemblance : le besoin ${rep.is_estimation ? "estimé" : "mesuré"} équivaut à ${num(rep.implied_per_capita.value)} ${rep.implied_per_capita.unit}.`, `Plausibility check: the ${rep.is_estimation ? "estimated" : "measured"} need equals ${num(rep.implied_per_capita.value)} ${rep.implied_per_capita.unit}.`, `التحقق من المعقولية: الحاجة ${rep.is_estimation ? "المقدَّرة" : "المقيسة"} تعادل ${num(rep.implied_per_capita.value)} ${rep.implied_per_capita.unit}.`)}
                </div>
              )}
              {rep.sources?.length > 0 && (
                <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                  {pick(language, "Sources", "Sources", "المصادر")} : {rep.sources.map((s) => srcText(s)).filter(Boolean).join(" · ")}
                </div>
              )}
            </div>
          )}
          <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)" }}>{rep.note}</div>
        </div>
      )}
    </div>
  );
}

export default function OpportunityReportTab({ countries = [], language = "fr" }) {
  const fr = language === "fr";
  const [mode, setMode] = useState("market");
  const [prefill, setPrefill] = useState(null);
  const [s3Prefill, setS3Prefill] = useState(null);
  const [marketPrefill, setMarketPrefill] = useState(null);

  // Hand off from a scenario to the full ultra-fine bilateral report.
  const openBilateral = (origin, destination, hsCode, goodsValue) => {
    setPrefill({ origin, destination, hsCode, goodsValue, k: Date.now() });
    setMode("bilateral");
  };

  // Handoff inter-modules : la recherche SH2/4/6 du module Statistiques dépose
  // {country, hsCode} dans sessionStorage puis navigue ici — on ouvre S3
  // (besoin national) pré-rempli avec le signal d'import OEC activé.
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("zlecaf_opportunites_handoff");
      if (!raw) return;
      sessionStorage.removeItem("zlecaf_opportunites_handoff");
      const h = JSON.parse(raw);
      if (h && h.hsCode) {
        const k = h.k || Date.now();
        // Deux intentions arrivent ici, et elles sont opposées :
        //   - « market » vient du module Production — ce pays PRODUIT ce
        //     produit, où le vendre ? C'est la perspective exportateur ;
        //   - « s3 » (défaut historique, module Statistiques) — ce pays a-t-il
        //     un BESOIN de ce produit ? Perspective importateur.
        // Ouvrir S3 pour une intention d'export enverrait le lecteur vers
        // l'écran qui répond à l'autre question.
        if (h.mode === "market") {
          setMarketPrefill({ hsCode: h.hsCode, k });
          setMode("market");
        } else if (h.country) {
          setS3Prefill({ country: h.country, hsCode: h.hsCode, withImports: true, k });
          setMode("s3");
        }
      }
    } catch {
      /* handoff illisible : ignorer */
    }
  }, []);

  const tabBtn = (id, txt) => (
    <button
      onClick={() => setMode(id)}
      data-testid={`mode-${id}`}
      className={`afcfta-btn ${mode === id ? "afcfta-btn-primary" : "afcfta-btn-secondary"}`}
      style={{ padding: "8px 16px", borderRadius: 8 }}
    >
      {txt}
    </button>
  );

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 18, flexWrap: "wrap" }}>
        {tabBtn("market", pick(language, "Trouver des marchés (producteur)", "Find markets (producer)", "البحث عن الأسواق (المنتِج)"))}
        {tabBtn("bilateral", pick(language, "Rapport bilatéral", "Bilateral report", "التقرير الثنائي"))}
        {tabBtn("s2", pick(language, "S2 · Export direct", "S2 · Direct export", "S2 · التصدير المباشر"))}
        {tabBtn("s1", pick(language, "S1 · Transformation", "S1 · Transformation", "S1 · التحويل"))}
        {tabBtn("s3", pick(language, "S3 · Besoin national", "S3 · National need", "S3 · الحاجة الوطنية"))}
        {tabBtn("s4", pick(language, "S4 · Importations", "S4 · Imports", "S4 · الواردات"))}
        {tabBtn("s5", pick(language, "S5 · Substitution", "S5 · Substitution", "S5 · الإحلال"))}
        {tabBtn("s6", pick(language, "S6 · Flux stratégiques", "S6 · Strategic flows", "S6 · التدفقات الاستراتيجية"))}
        {tabBtn("dza", pick(language, "Algérie · industrie et marchés", "Algeria · industry and markets", "الجزائر · الصناعة والأسواق"))}
      </div>
      {mode === "market" && <MarketSeekingView fr={fr} language={language} prefill={marketPrefill} />}
      {mode === "bilateral" && <BilateralView countries={countries} fr={fr} language={language} prefill={prefill} />}
      {mode === "s2" && <DirectExportView countries={countries} fr={fr} language={language} onAnalyze={openBilateral} />}
      {mode === "s1" && <TransformationView countries={countries} fr={fr} language={language} onAnalyze={openBilateral} />}
      {mode === "s3" && <NationalNeedView countries={countries} fr={fr} language={language} onAnalyze={openBilateral} prefill={s3Prefill} />}
      {mode === "s4" && <ImportOpportunitiesView countries={countries} fr={fr} language={language} onAnalyze={openBilateral} />}
      {mode === "s5" && <SubstitutionAnalysis language={language} />}
      {mode === "s6" && <StrategicFlows language={language} />}
      {mode === "dza" && <NationalIndustryView fr={fr} language={language} />}
    </div>
  );
}
