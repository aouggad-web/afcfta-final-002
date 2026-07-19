import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import SubstitutionAnalysis from "../opportunities/SubstitutionAnalysis";
import OpportunityPdfExport from "../opportunities/OpportunityPdfExport";

const API = `${import.meta.env.VITE_BACKEND_URL || ""}/api`;

/* Honest formatter: null / undefined -> "—" (never invented). */
const dash = (v, suffix = "") =>
  v === null || v === undefined || v === "" ? "—" : `${v}${suffix}`;

const pct = (v) => (v === null || v === undefined ? "—" : `${Math.round(v * 100)}%`);

const money = (v) =>
  v === null || v === undefined
    ? "—"
    : `$${Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

/* Volume BACI (poids net, tonnes métriques) — affiché à côté de la valeur. */
const tonnes = (v) =>
  v === null || v === undefined || !(Number(v) > 0)
    ? null
    : `${Number(v).toLocaleString("en-US", { maximumFractionDigits: Number(v) < 10 ? 1 : 0 })} t`;

/* Sous-module « faisabilité de substitution » (substitution_feasibility_service.py) :
   libellés des barrières non tarifaires (effet marque, écart technologique...)
   et de leur intensité, fr/en. */
const BARRIER_LABEL = {
  brand_effect: { fr: "Effet marque", en: "Brand effect" },
  technology_gap: { fr: "Écart technologique", en: "Technology gap" },
  after_sales_network: { fr: "Réseau après-vente", en: "After-sales network" },
  certification: { fr: "Certification", en: "Certification" },
};
const INTENSITY_LABEL = {
  faible: { fr: "Faible", en: "Low" },
  moyen: { fr: "Moyen", en: "Medium" },
  fort: { fr: "Fort", en: "High" },
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
  market_potential: { fr: "Potentiel de marché", en: "Market potential" },
  market_demand: { fr: "Demande de marché", en: "Market demand" },
  supply_capacity: { fr: "Capacité de production", en: "Supply capacity" },
  logistics_accessibility: { fr: "Accessibilité logistique", en: "Logistics accessibility" },
  financing_feasibility: { fr: "Faisabilité de financement", en: "Financing feasibility" },
  country_risk: { fr: "Risque pays", en: "Country risk" },
  fx_volatility: { fr: "Volatilité du change", en: "FX volatility" },
  tariff_advantage: { fr: "Avantage tarifaire", en: "Tariff advantage" },
};
const compLabel = (key, fr) => COMPONENT_LABELS[key]?.[fr ? "fr" : "en"] || key;

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
function EstBadge({ isEstimation, level, fr }) {
  return (
    <span
      style={{
        display: "inline-block",
        fontSize: 11,
        fontWeight: 700,
        padding: "2px 8px",
        borderRadius: 999,
        background: isEstimation ? "rgba(154,103,0,0.12)" : "rgba(26,127,55,0.12)",
        color: isEstimation ? "#9a6700" : "#1a7f37",
      }}
    >
      {isEstimation
        ? `${fr ? "Estimé — niveau" : "Estimated — level"} ${level}`
        : fr
        ? "Mesuré"
        : "Measured"}
    </span>
  );
}

/* ── Mode 1: producer looking for markets ─────────────────────────────────── */
function MarketSeekingView({ fr }) {
  const [hsCode, setHsCode] = useState("1801");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rep, setRep] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setRep(null);
    try {
      const params = new URLSearchParams({ hs_code: hsCode, lang: fr ? "fr" : "en" });
      const res = await axios.get(`${API}/reports/market-seeking?${params.toString()}`);
      setRep(res.data);
    } catch (e) {
      setError(fr ? "Impossible de générer le rapport." : "Could not generate report.");
    } finally {
      setLoading(false);
    }
  };

  const demand = rep?.demand || {};
  const supply = rep?.supply || {};

  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    return {
      badge: `market-${hsCode}`,
      filename: `recherche-marchés-${hsCode}`,
      kpis: [
        { label: fr ? "Code produit" : "Product code", value: hsCode, accent: 'gold' },
        { label: fr ? "Demande africaine" : "African demand", value: demand.total_import_value_usd ? `$${Number(demand.total_import_value_usd).toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—', accent: 'green' }
      ],
      sections: [{ title: fr ? `Recherche de marchés ${hsCode}` : `Find markets ${hsCode}`, text: '' }]
    };
  }, [rep, hsCode, demand.total_import_value_usd, fr]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 18 }}>
        <div>
          <div style={label}>{fr ? "Produit — Code SH (HS6 ou HS4)" : "Product — HS code (HS6 or HS4)"}</div>
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
          {loading ? (fr ? "Recherche…" : "Searching…") : fr ? "Trouver les marchés" : "Find markets"}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={fr ? 'fr' : 'en'} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "#c8102e" }}>{error}</div>}

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
              {fr ? "Demande — marchés importateurs africains" : "Demand — African importing markets"}
            </div>
            {demand.available ? (
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={th}>{fr ? "Pays" : "Country"}</th>
                    <th style={th}>{fr ? "Importations" : "Imports"}</th>
                    <th style={th}>{fr ? "Volume (t)" : "Volume (t)"}</th>
                    <th style={th}>{fr ? "Part" : "Share"}</th>
                  </tr>
                </thead>
                <tbody>
                  {demand.markets.map((m) => (
                    <tr key={m.country_iso3} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                      <td style={td}>
                        {m.country_name} ({m.country_iso3})
                      </td>
                      <td style={td}>{money(m.import_value_usd)}</td>
                      <td style={td}>{tonnes(m.import_quantity_tonnes) || "—"}</td>
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
                {fr ? "Source" : "Source"} : {demand.source}
              </div>
            )}
          </div>

          {/* Supply: who produces this product */}
          <div style={card}>
            <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
              {fr ? "Offre — producteurs africains" : "Supply — African producers"}
              {supply.available && supply.commodity ? ` · ${supply.commodity}` : ""}
            </div>
            {supply.available ? (
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={th}>{fr ? "Pays" : "Country"}</th>
                    <th style={th}>
                      {fr ? "Production" : "Production"} {supply.unit ? `(${supply.unit})` : ""}
                    </th>
                    <th style={th}>{fr ? "Part" : "Share"}</th>
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
                — {fr ? "Aucune donnée de production pour ce code." : "No production data for this code."}
              </div>
            )}
            {supply.source && (
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                {fr ? "Source" : "Source"} : {srcText(supply.source)}
                {supply.year ? ` (${supply.year})` : ""}
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
export function BilateralView({ countries, fr, prefill }) {
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
      setError(fr ? "Impossible de générer le rapport." : "Could not generate report.");
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

  const buildPdfSpec = useCallback(() => {
    if (!report) return null;
    const kpis = [];
    const ci = report.composite_indicators || {};
    if (ci.end_to_end_score?.score) kpis.push({ label: fr ? "Score bout en bout" : "End-to-end score", value: `${Math.round((ci.end_to_end_score.score || 0) * 100)}%`, accent: 'gold' });
    if (ci.landed_cost?.value_usd) kpis.push({ label: fr ? "Coût débarqué" : "Landed cost", value: `$${Number(ci.landed_cost.value_usd).toLocaleString('en-US', { maximumFractionDigits: 0 })}`, accent: 'green' });
    return {
      badge: `${origin}-${destination}`,
      filename: `rapport-bilateral-${hsCode}`,
      kpis,
      sections: [
        {
          title: fr ? `Opportunité bilatérale ${hsCode}` : `Bilateral opportunity ${hsCode}`,
          text: fr ? `Flux commerce ${origin} → ${destination}` : `Trade flow ${origin} → ${destination}`
        }
      ]
    };
  }, [report, origin, destination, hsCode, fr]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 18 }}>
        <div>
          <div style={label}>{fr ? "Exportateur (origine)" : "Exporter (origin)"}</div>
          {sel(origin, setOrigin, "report-origin")}
        </div>
        <div>
          <div style={label}>{fr ? "Marché (destination)" : "Market (destination)"}</div>
          {sel(destination, setDestination, "report-destination")}
        </div>
        <div>
          <div style={label}>{fr ? "Code SH" : "HS code"}</div>
          <input
            value={hsCode}
            onChange={(e) => setHsCode(e.target.value)}
            data-testid="report-hs"
            style={{ padding: "8px 10px", borderRadius: 8, width: 120 }}
          />
        </div>
        <div>
          <div style={label}>{fr ? "Valeur FOB (USD)" : "FOB value (USD)"}</div>
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
          {loading ? (fr ? "Génération…" : "Generating…") : fr ? "Générer le rapport" : "Generate report"}
        </button>
        {report && <OpportunityPdfExport getSpec={buildPdfSpec} language={fr ? 'fr' : 'en'} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "#c8102e" }}>{error}</div>}

      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {exec && (
            <div style={{ ...card, borderLeft: `4px solid ${tierColor[exec.priority_tier] || "#0969da"}` }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                <span style={{ ...label, margin: 0 }}>{fr ? "Synthèse exécutive" : "Executive summary"}</span>
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
              title={fr ? "Score de bout en bout" : "End-to-end score"}
              value={e2e.available ? pct(e2e.score) : "—"}
              sub={
                e2e.available
                  ? `${fr ? "Couverture" : "Coverage"} ${pct(e2e.weight_coverage)}`
                  : fr
                  ? "Aucune composante disponible"
                  : "No component available"
              }
            />
            <Metric
              title={fr ? "Coût rendu estimé" : "Estimated landed cost"}
              value={landed.available ? money(landed.value_usd) : "—"}
              sub={
                landed.available
                  ? `FOB ${money(landed.breakdown?.goods_value_fob_usd)} + ${fr ? "fret" : "freight"} ${money(
                      landed.breakdown?.best_operational_freight_usd
                    )} + ${fr ? "assurance" : "insurance"} ${money(landed.breakdown?.insurance_usd)}` +
                    (landed.breakdown?.trade_finance_fee_usd
                      ? ` + ${fr ? "banque" : "banking"} ${money(landed.breakdown.trade_finance_fee_usd)}`
                      : "") +
                    (landed.breakdown?.freight_mode === "sea_bulk"
                      ? ` · ${fr ? "affrètement vraquier" : "bulk charter"}${
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
                              ).toLocaleString()} kg${fr ? " est." : " est."})`
                            : ""
                        }`
                      : "")
                  : landed.note
              }
            />
            <Metric
              title={fr ? "Accessibilité logistique" : "Logistics accessibility"}
              value={logAccess.available ? pct(logAccess.index) : "—"}
              sub={
                logAccess.available
                  ? `${dash(logAccess.operational_modes)} ${fr ? "modes opérationnels" : "operational modes"}`
                  : undefined
              }
            />
            <Metric
              title={fr ? "Faisabilité de financement" : "Financing feasibility"}
              value={finIdx.available ? pct(finIdx.index) : "—"}
            />
          </div>

          {landed.available && landed.breakdown && (
            <div style={card} data-testid="report-landed-breakdown">
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {fr ? "Décomposition du coût rendu" : "Landed cost breakdown"}
              </div>
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <tbody>
                  {(() => {
                    const bd = landed.breakdown;
                    const comp = landed.components || {};
                    const freightLabel =
                      bd.freight_excl_port_fees_usd != null
                        ? fr
                          ? "Fret (hors frais portuaires)"
                          : "Freight (excl. port fees)"
                        : fr
                        ? "Fret (option la moins chère)"
                        : "Freight (cheapest option)";
                    const rows = [
                      { l: fr ? "Valeur marchandises (FOB)" : "Goods value (FOB)", v: bd.goods_value_fob_usd },
                      {
                        l: freightLabel,
                        v: bd.freight_excl_port_fees_usd != null
                          ? bd.freight_excl_port_fees_usd
                          : bd.best_operational_freight_usd,
                      },
                      {
                        l: fr
                          ? "Frais portuaires — chargement (port d'origine)"
                          : "Port fees — loading (origin port)",
                        v: bd.port_fees_loading_usd,
                      },
                      {
                        l: fr
                          ? "Frais portuaires — déchargement (port de destination)"
                          : "Port fees — discharge (destination port)",
                        v: bd.port_fees_discharge_usd,
                      },
                      {
                        l: `${fr ? "Assurance cargo" : "Cargo insurance"} (${
                          comp.insurance?.rate_pct ?? "0,5"
                        } % · ${fr ? "estimée" : "estimated"})`,
                        v: bd.insurance_usd,
                      },
                      {
                        l: bd.trade_finance_instrument
                          ? `${fr ? "Instrument bancaire recommandé" : "Recommended banking instrument"} — ${
                              bd.trade_finance_instrument
                            }${
                              comp.trade_finance?.typical_cost_pct != null
                                ? ` (${comp.trade_finance.typical_cost_pct} %)`
                                : ""
                            }`
                          : fr
                          ? "Instrument bancaire recommandé"
                          : "Recommended banking instrument",
                        v: bd.trade_finance_fee_usd,
                      },
                    ].filter((r) => r.v !== null && r.v !== undefined);
                    return (
                      <>
                        {rows.map((r, i) => (
                          <tr key={i} style={{ borderTop: i > 0 ? "1px solid rgba(0,0,0,0.06)" : "none" }}>
                            <td style={td}>{r.l}</td>
                            <td style={{ ...td, textAlign: "right" }}>{money(r.v)}</td>
                          </tr>
                        ))}
                        <tr style={{ borderTop: "2px solid rgba(0,0,0,0.15)", fontWeight: 700 }}>
                          <td style={td}>{fr ? "Coût rendu estimé (total)" : "Estimated landed cost (total)"}</td>
                          <td style={{ ...td, textAlign: "right" }}>{money(landed.value_usd)}</td>
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

          {landed.shipment_sizing?.value_to_weight && (
            <div style={card}>
              <div style={{ ...label, marginBottom: 8 }}>
                {fr
                  ? "Indice valeur/poids & repère de négociation"
                  : "Value/weight index & negotiation reference"}
              </div>
              <div style={{ fontSize: 13, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
                <strong>
                  {landed.shipment_sizing.value_to_weight.usd_per_kg.toLocaleString()} USD/kg
                </strong>
                <span
                  style={{
                    fontSize: 11,
                    padding: "2px 8px",
                    borderRadius: 999,
                    background:
                      landed.shipment_sizing.value_to_weight.classification_source === "cours_mondial"
                        ? "#dcfce7"
                        : "#fef9c3",
                    color:
                      landed.shipment_sizing.value_to_weight.classification_source === "cours_mondial"
                        ? "#166534"
                        : "#854d0e",
                  }}
                >
                  {landed.shipment_sizing.value_to_weight.classification_source === "cours_mondial"
                    ? fr
                      ? "Cours mondial réel"
                      : "Real world market price"
                    : fr
                    ? "Estimation par chapitre SH"
                    : "HS-chapter estimate"}
                </span>
              </div>
              <div style={{ fontSize: 12, color: "#64748b", marginTop: 6 }}>
                {landed.shipment_sizing.value_to_weight.source}
              </div>
              {landed.shipment_sizing.negotiation_reference ? (
                <div style={{ fontSize: 12, color: "#334155", marginTop: 6 }}>
                  {fr
                    ? "Utilisable comme repère grossier de négociation d'achat. "
                    : "Usable as a rough purchase-negotiation reference. "}
                  <span style={{ color: "#b45309" }}>
                    {landed.shipment_sizing.negotiation_reference.caveat}
                  </span>
                </div>
              ) : (
                <div style={{ fontSize: 12, color: "#b45309", marginTop: 6 }}>
                  {fr
                    ? "Dimensionnement logistique uniquement — PAS une base de négociation de prix."
                    : "Logistics sizing only — NOT a price-negotiation basis."}
                </div>
              )}
            </div>
          )}

          {e2e.breakdown && (
            <div style={card}>
              <div style={{ ...label, marginBottom: 8 }}>
                {fr ? "Décomposition du score (pondérations transparentes)" : "Score breakdown (transparent weights)"}
              </div>
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={th}>{fr ? "Composante" : "Component"}</th>
                    <th style={th}>{fr ? "Poids" : "Weight"}</th>
                    <th style={th}>{fr ? "Sous-score" : "Sub-score"}</th>
                    <th style={th}>{fr ? "Comptée" : "Counted"}</th>
                  </tr>
                </thead>
                <tbody>
                  {e2e.breakdown.map((b) => (
                    <tr key={b.component} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                      <td style={td}>{compLabel(b.component, fr)}</td>
                      <td style={td}>{pct(b.weight)}</td>
                      <td style={td}>{b.subscore === null ? "—" : pct(b.subscore)}</td>
                      <td style={td}>
                        {b.counted ? "✓" : <span style={{ color: "#999" }}>{fr ? "exclue" : "excluded"}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                {report?.market_potential?.available
                  ? fr
                    ? `Potentiel de marché activé via les imports OEC réels du marché (${money(
                        report.market_potential.import_value_usd
                      )}/an${
                        tonnes(report.market_potential.import_quantity_tonnes)
                          ? ` · ${tonnes(report.market_potential.import_quantity_tonnes)}`
                          : ""
                      }).`
                    : `Market potential activated from real OEC imports (${money(
                        report.market_potential.import_value_usd
                      )}/yr${
                        tonnes(report.market_potential.import_quantity_tonnes)
                          ? ` · ${tonnes(report.market_potential.import_quantity_tonnes)}`
                          : ""
                      }).`
                  : fr
                  ? "Le potentiel de marché par produit (flux OEC) est indisponible ici — exclu, jamais estimé."
                  : "Per-product market potential (OEC flows) unavailable here — excluded, never estimated."}
              </div>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
            <div style={card}>
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {fr ? "Logistique — option la moins chère" : "Logistics — cheapest option"}
              </div>
              {cheapest ? (
                <div style={{ fontSize: 14 }}>
                  <div>
                    <strong>{cheapest.label || cheapest.mode}</strong>
                  </div>
                  <div>
                    {fr ? "Coût" : "Cost"} : {money(cheapest.total_cost_usd)}
                  </div>
                  <div>
                    {fr ? "Délai" : "Transit"} : {dash(cheapest.transit_days_min)}–{dash(cheapest.transit_days_max)}{" "}
                    {fr ? "jours" : "days"}
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
                  {fr ? "Vraquier — affrètement en vrac" : "Bulk carrier — charter shipping"}
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
                            🚢 {opt.vessel_class || "vraquier"}
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
                              {fr ? "Modélisé" : "Modeled"}
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
                              {fr ? "Marché" : "Live"} · {opt.pricing.as_of}
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
                                color: "#64748b",
                              }}
                            >
                              {fr ? "Calibré 2024" : "Calibrated 2024"}
                            </span>
                          )}
                        </div>
                        <div style={{ fontWeight: 700 }}>{money(opt.total_cost_usd)}</div>
                        {cb.total_usd_per_t != null && (
                          <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 2 }}>
                            {num(cb.total_usd_per_t)} USD/t
                            {cb.ocean_usd_per_t != null && (
                              <>
                                {" "}({fr ? "océan" : "ocean"} {num(cb.ocean_usd_per_t)} +{" "}
                                {fr ? "chargt" : "load"} {num(cb.port_load_usd_per_t)} +{" "}
                                {fr ? "déchargt" : "disch."} {num(cb.port_discharge_usd_per_t)})
                              </>
                            )}
                          </div>
                        )}
                        <div style={{ marginTop: 2 }}>
                          {fr ? "Délai" : "Transit"}: {dash(opt.transit_days_min)}–{dash(opt.transit_days_max)}{" "}
                          {fr ? "jours" : "days"}
                        </div>
                        {opt.co2_kg && (
                          <div>{fr ? "CO₂" : "CO₂"}: {num(Math.round(opt.co2_kg))} kg</div>
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
                {fr ? "Finance & paiement" : "Finance & payment"}
              </div>
              <div style={{ fontSize: 14, lineHeight: 1.7 }}>
                <div>
                  PAPSS :{" "}
                  {pay.available
                    ? pay.papss_covered
                      ? fr
                        ? "Couvert ✓"
                        : "Covered ✓"
                      : fr
                      ? "Non couvert"
                      : "Not covered"
                    : "—"}
                </div>
                <div>
                  {fr ? "Risque pays" : "Country risk"} :{" "}
                  {risk.available ? `${dash(risk.overall_risk_rating)} (${dash(risk.alert_level)})` : "—"}
                </div>
                <div>
                  {fr ? "Instruments trade finance" : "Trade finance instruments"} :{" "}
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
              {fr ? "Indicateurs macro du marché" : "Market macro indicators"} — {report.inputs?.destination_iso3}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
              <Metric
                title="GAI (Global Attractiveness Index)"
                value={gai ? dash(gai.score) : "—"}
                sub={
                  gai
                    ? `${fr ? "Rang Afrique" : "Africa rank"} ${dash(gai.rank_africa)} · ${dash(gai.rating)} · ${dash(
                        gai.trend
                      )}`
                    : undefined
                }
              />
              <Metric
                title={fr ? "Réserves de change" : "FX reserves"}
                value={fx.available ? money(fx.value_busd * 1e9) : "—"}
                sub={fx.available ? `${fr ? "Année" : "Year"} ${dash(fx.year)}` : fr ? "À produire via ETL BM" : "Pending WB ETL"}
              />
              <Metric
                title={fr ? "Couverture des importations" : "Import cover"}
                value={cover.available ? `${dash(cover.months)} ${fr ? "mois" : "months"}` : "—"}
                sub={cover.available ? `${fr ? "Année" : "Year"} ${dash(cover.year)}` : fr ? "À produire via ETL BM" : "Pending WB ETL"}
              />
              <Metric
                title={fr ? "Réserves d'or" : "Gold reserves"}
                value={gold ? `${dash(gold.tonnes)} t` : "—"}
                sub={gold ? `${fr ? "Rang Afrique" : "Africa rank"} ${dash(gold.rank_africa)}` : undefined}
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
                  {fr ? "Sources" : "Sources"} : {sources.join(" · ")}
                </div>
              ) : null;
            })()}
          </div>

          {/* ── Segmentation matrices + national need ─────────────────── */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
            <div style={card} data-testid="report-effort-impact">
              <div style={{ ...label, marginBottom: 6, fontWeight: 700 }}>
                {fr ? "Matrice effort / impact" : "Effort / impact matrix"}
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, textTransform: "uppercase" }}>
                {(effort.quadrant || "—").replace(/_/g, " ")}
              </div>
              <div style={{ fontSize: 13, marginTop: 4 }}>
                {fr ? "Effort" : "Effort"} {pct(effort.effort_score)} · {fr ? "Impact" : "Impact"} {pct(effort.impact_score)}
              </div>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>{effort.rationale}</div>
            </div>
            <div style={card} data-testid="report-risk-reward">
              <div style={{ ...label, marginBottom: 6, fontWeight: 700 }}>
                {fr ? "Matrice risque / récompense" : "Risk / reward matrix"}
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, textTransform: "uppercase" }}>
                {(rr.quadrant || "—").replace(/_/g, " ")}
              </div>
              <div style={{ fontSize: 13, marginTop: 4 }}>
                {fr ? "Risque" : "Risk"} {pct(rr.risk_score)} · {fr ? "Récompense" : "Reward"} {pct(rr.reward_score)}
              </div>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>{rr.recommendation}</div>
            </div>
            <div style={card} data-testid="report-national-need">
              <div style={{ ...label, marginBottom: 6, fontWeight: 700 }}>
                {fr ? "Besoin du marché" : "Market need"} — {report.inputs?.destination_iso3}
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
                      color: need.is_estimation ? "#9a6700" : "#1a7f37",
                    }}
                  >
                    {need.is_estimation
                      ? `${fr ? "Estimé — niveau" : "Estimated — level"} ${need.estimation_level}`
                      : fr
                      ? "Mesuré"
                      : "Measured"}
                  </div>
                  {need.observed_imports?.import_value_usd && (
                    <div style={{ fontSize: 12, marginTop: 6 }}>
                      {fr ? "Importe déjà" : "Already imports"} : {money(need.observed_imports.import_value_usd)}
                      {tonnes(need.observed_imports.import_quantity_tonnes) && (
                        <span style={{ color: "var(--afcfta-muted,#667)" }}>
                          {" "}· {tonnes(need.observed_imports.import_quantity_tonnes)}
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
                  {fr ? "Faisabilité de substitution" : "Substitution feasibility"}
                </div>
                <div style={{ fontSize: 20, fontWeight: 800 }}>{pct(subst.coefficient)}</div>
                <div style={{ fontSize: 12, marginTop: 2, color: "var(--afcfta-muted,#667)" }}>
                  {fr ? "part réalistement adressable" : "realistically addressable share"}
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
                          color: intensity === "fort" ? "#c8102e" : intensity === "moyen" ? "#9a6700" : "#667",
                        }}
                      >
                        {(BARRIER_LABEL[key]?.[fr ? "fr" : "en"] || key)} · {(INTENSITY_LABEL[intensity]?.[fr ? "fr" : "en"] || intensity)}
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
                {fr ? "Avantage tarifaire ZLECAf" : "AfCFTA tariff advantage"}
              </div>
              {tariff.available ? (
                <div style={{ fontSize: 14, lineHeight: 1.7 }}>
                  <div style={{ fontSize: 22, fontWeight: 800 }}>{dash(tariff.tariff_advantage_pct, " %")}</div>
                  {tariff.trade_regime && !["ZLECAF", "CUSTOMS_UNION"].includes(tariff.trade_regime) ? (
                    <div>
                      {fr ? "Droit national" : "National duty"} {dash(tariff.national_rate_pct, " %")}{" "}
                      {fr ? "appliqué (NPF)" : "applied (MFN)"}
                    </div>
                  ) : (
                    <div>
                      {fr ? "Droit national" : "National duty"} {dash(tariff.national_rate_pct, " %")} →{" "}
                      {tariff.trade_regime === "CUSTOMS_UNION" ? (fr ? "union douanière" : "customs union") : "ZLECAf"}{" "}
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
                      {money(tariff.savings_per_1000usd)} / 1 000 $ CIF
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
                  {fr ? "Facteurs — opportunités & risques" : "Factors — opportunities & risks"}
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
                            f.category === "opportunity" ? "#1a7f37" : f.category === "risk" ? "#c8102e" : "#8b949e",
                        }}
                      >
                        {f.category === "opportunity" ? "▲" : f.category === "risk" ? "▼" : "■"}
                      </span>
                      <span style={{ flex: "0 0 150px", fontWeight: 600 }}>{compLabel(f.factor, fr)}</span>
                      <span style={{ flex: 1, color: "var(--afcfta-muted,#667)" }}>{f.rationale}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* ── Top producers benchmark ───────────────────────────────── */}
          {topProducers.available && topProducers.producers?.length > 0 && (
            <div style={card}>
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {fr ? "Meilleurs producteurs africains" : "Top African producers"}
              </div>
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={th}>#</th>
                    <th style={th}>{fr ? "Pays" : "Country"}</th>
                    <th style={th}>{fr ? "Part continentale" : "Continental share"}</th>
                    <th style={th}>{fr ? "Production" : "Production"}</th>
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
                {fr ? "Contexte commerce intra-africain" : "Intra-African trade context"}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
                {[
                  { side: intra.origin, role: fr ? "Origine (exportateur)" : "Origin (exporter)" },
                  { side: intra.destination, role: fr ? "Destination (marché)" : "Destination (market)" },
                ].map(({ side, role }, i) =>
                  side?.available ? (
                    <div key={i} style={{ padding: 10, borderRadius: 8, background: "var(--afcfta-subtle,rgba(0,0,0,0.03))" }}>
                      <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>
                        {role} — {side.name} ({side.iso3})
                      </div>
                      {side.intra_african_trade && (
                        <div style={{ fontSize: 13, marginBottom: 4 }}>
                          {fr ? "Commerce intra-africain 2025" : "Intra-African trade 2025"} :{" "}
                          <strong>{dash(side.intra_african_trade.value_2025_busd, " Md$")}</strong>{" "}
                          <span style={{ color: "var(--afcfta-muted,#667)" }}>
                            ({dash(side.intra_african_trade.share_2025_pct, " %")} {fr ? "du total" : "of total"}
                            {side.intra_african_trade.growth_2021_2025_pct != null
                              ? ` · ${side.intra_african_trade.growth_2021_2025_pct >= 0 ? "+" : ""}${side.intra_african_trade.growth_2021_2025_pct}% ${fr ? "depuis 2021" : "since 2021"}`
                              : ""})
                          </span>
                        </div>
                      )}
                      {side.merchandise_exports && (
                        <div style={{ fontSize: 13 }}>
                          {fr ? "Exports marchandises 2025" : "Merchandise exports 2025"} :{" "}
                          <strong>{dash(side.merchandise_exports.value_2025_busd, " Md$")}</strong>{" "}
                          <span style={{ color: "var(--afcfta-muted,#667)" }}>
                            ({dash(side.merchandise_exports.share_2025_pct, " %")})
                          </span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div key={i} style={{ padding: 10, fontSize: 12, color: "var(--afcfta-muted,#667)" }}>
                      {role} — {fr ? "non couvert par l'ATR 2026" : "not covered by ATR 2026"}
                    </div>
                  )
                )}
              </div>
              {intra.continental_2025 && (
                <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                  {fr ? "Continent 2025" : "Continent 2025"} :{" "}
                  {dash(intra.continental_2025.intra_african_trade_busd, " Md$")} {fr ? "de commerce intra-africain" : "intra-African trade"}
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
                {fr ? "Analyse rédigée" : "Written analysis"}
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
function DirectExportView({ countries, fr, onAnalyze }) {
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
      setError(fr ? "Impossible de générer le scénario." : "Could not generate scenario.");
    } finally {
      setLoading(false);
    }
  };

  const supply = rep?.producer_supply || {};
  const opps = rep?.ranked_opportunities || [];

  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    return {
      badge: `S2-${hsCode}`,
      filename: `s2-export-direct-${hsCode}`,
      kpis: [
        { label: fr ? "Code produit" : "Product code", value: hsCode, accent: 'gold' },
        { label: fr ? "Producteur" : "Producer", value: producer, accent: 'blue' }
      ],
      sections: [{ title: fr ? `S2 · Export direct ${hsCode}` : `S2 · Direct export ${hsCode}`, text: rep.deep_dived ? `${rep.deep_dived} ${fr ? 'marchés analysés' : 'markets analyzed'}` : '' }]
    };
  }, [rep, hsCode, producer, fr]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
        <div>
          <div style={label}>{fr ? "Producteur" : "Producer"}</div>
          <Sel value={producer} onChange={setProducer} countries={countries} testid="s2-producer" />
        </div>
        <div>
          <div style={label}>{fr ? "Code SH" : "HS code"}</div>
          <input value={hsCode} onChange={(e) => setHsCode(e.target.value)} data-testid="s2-hs" style={{ padding: "8px 10px", borderRadius: 8, width: 110 }} />
        </div>
        <div>
          <div style={label}>{fr ? "Nb marchés" : "Markets"}</div>
          <input value={topK} onChange={(e) => setTopK(e.target.value)} data-testid="s2-topk" style={{ padding: "8px 10px", borderRadius: 8, width: 70 }} />
        </div>
        <div>
          <div style={label}>{fr ? "Valeur FOB (USD)" : "FOB value (USD)"}</div>
          <input value={goodsValue} onChange={(e) => setGoodsValue(e.target.value)} data-testid="s2-value" style={{ padding: "8px 10px", borderRadius: 8, width: 130 }} />
        </div>
        <button onClick={run} disabled={loading} className="afcfta-btn afcfta-btn-primary" data-testid="s2-run" style={{ padding: "10px 18px", borderRadius: 8 }}>
          {loading ? (fr ? "Analyse…" : "Analyzing…") : fr ? "Classer les marchés" : "Rank markets"}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={fr ? 'fr' : 'en'} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "#c8102e" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={card}>
            <div style={{ ...label, fontWeight: 700 }}>
              {fr ? "Production du producteur" : "Producer supply"} — {rep.inputs?.producer_iso3}
            </div>
            {supply.available ? (
              <div style={{ fontSize: 14, marginTop: 4 }}>
                {supply.commodity} · {dash(supply.continental_share_pct, " %")} {fr ? "de la production continentale" : "of continental production"}
                {supply.rank ? ` · ${fr ? "rang" : "rank"} #${supply.rank}` : ""}
              </div>
            ) : (
              <div style={{ color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                {fr ? "Pas de production détectée pour ce produit." : "No production detected for this product."}
              </div>
            )}
            <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>
              {rep.candidates_considered} {fr ? "marchés candidats · " : "candidate markets · "}
              {rep.deep_dived} {fr ? "analysés en profondeur" : "deep-dived"}
            </div>
          </div>

          <div style={card}>
            <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
              {fr ? "Marchés d'export classés" : "Ranked export markets"}
            </div>
            <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={th}>#</th>
                  <th style={th}>{fr ? "Marché" : "Market"}</th>
                  <th style={th}>{fr ? "Score" : "Score"}</th>
                  <th style={th}>{fr ? "Besoin estimé" : "Estimated need"}</th>
                  <th style={th}>{fr ? "Avantage tarif" : "Tariff adv."}</th>
                  <th style={th}>{fr ? "Conteneurs" : "Containers"}</th>
                  <th style={th}>{fr ? "Coût rendu" : "Landed cost"}</th>
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
                          ? `${fr ? "Sous-position" : "Sub-heading"} HS6 ${o.tariff_benefit.hs6_used}`
                          : undefined
                      }
                    >
                      {o.tariff_benefit?.available ? dash(o.tariff_benefit.tariff_advantage_pct, " %") : "—"}
                    </td>
                    <td
                      style={td}
                      title={
                        o.landed_cost?.breakdown?.estimated_weight_kg
                          ? `${fr ? "Poids estimé" : "Est. weight"} ${Math.round(
                              o.landed_cost.breakdown.estimated_weight_kg
                            ).toLocaleString()} kg${
                              o.landed_cost.breakdown.weight_source === "estimé"
                                ? fr
                                  ? " (estimé depuis la valeur FOB)"
                                  : " (estimated from FOB value)"
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
                    <td style={td}>{o.landed_cost?.available ? money(o.landed_cost.value_usd) : "—"}</td>
                    <td style={td}>
                      <button
                        onClick={() => onAnalyze && onAnalyze(producer, o.destination_iso3, hsCode, goodsValue)}
                        data-testid={`s2-analyze-${o.destination_iso3}`}
                        className="afcfta-btn afcfta-btn-secondary"
                        style={{ padding: "4px 10px", borderRadius: 6, fontSize: 12 }}
                      >
                        {fr ? "Analyser ▸" : "Analyze ▸"}
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
function TransformationView({ countries, fr, onAnalyze }) {
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
      setError(fr ? "Impossible de générer le scénario." : "Could not generate scenario.");
    } finally {
      setLoading(false);
    }
  };

  const leg1 = rep?.leg1_input_import || {};
  const leg2 = rep?.leg2_production || {};
  const va = rep?.value_added || {};
  const feas = rep?.feasibility || {};
  const exportScore = feas.export_end_to_end_score;

  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    return {
      badge: `S1-${finishedHs}`,
      filename: `s1-transformation-${finishedHs}`,
      kpis: [
        { label: fr ? "Produit fini" : "Finished product", value: finishedHs, accent: 'gold' },
        { label: fr ? "Valeur ajoutée" : "Value added", value: va.percentage ? `${Math.round(va.percentage)}%` : '—', accent: 'green' }
      ],
      sections: [{ title: fr ? `S1 · Transformation (${inputHs} → ${finishedHs})` : `S1 · Transformation (${inputHs} → ${finishedHs})`, text: '' }]
    };
  }, [rep, finishedHs, inputHs, va.percentage, fr]);

  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
        <div>
          <div style={label}>{fr ? "Intrant SH" : "Input HS"}</div>
          <input value={inputHs} onChange={(e) => setInputHs(e.target.value)} data-testid="s1-input-hs" style={{ padding: "8px 10px", borderRadius: 8, width: 90 }} />
        </div>
        <div>
          <div style={label}>{fr ? "Origine intrant" : "Input origin"}</div>
          <Sel value={inputOrigin} onChange={setInputOrigin} countries={countries} testid="s1-input-origin" />
        </div>
        <div>
          <div style={label}>{fr ? "Producteur" : "Producer"}</div>
          <Sel value={producer} onChange={setProducer} countries={countries} testid="s1-producer" />
        </div>
        <div>
          <div style={label}>{fr ? "Produit fini SH" : "Finished HS"}</div>
          <input value={finishedHs} onChange={(e) => setFinishedHs(e.target.value)} data-testid="s1-finished-hs" style={{ padding: "8px 10px", borderRadius: 8, width: 90 }} />
        </div>
        <div>
          <div style={label}>{fr ? "Marché export" : "Export market"}</div>
          <Sel value={destination} onChange={setDestination} countries={countries} testid="s1-destination" />
        </div>
        <div>
          <div style={label}>{fr ? "Val. intrant" : "Input val."}</div>
          <input value={inputValue} onChange={(e) => setInputValue(e.target.value)} data-testid="s1-input-value" style={{ padding: "8px 10px", borderRadius: 8, width: 100 }} />
        </div>
        <div>
          <div style={label}>{fr ? "Val. fini" : "Finished val."}</div>
          <input value={finishedValue} onChange={(e) => setFinishedValue(e.target.value)} data-testid="s1-finished-value" style={{ padding: "8px 10px", borderRadius: 8, width: 100 }} />
        </div>
        <button onClick={run} disabled={loading} className="afcfta-btn afcfta-btn-primary" data-testid="s1-run" style={{ padding: "10px 18px", borderRadius: 8 }}>
          {loading ? (fr ? "Analyse…" : "Analyzing…") : fr ? "Analyser la chaîne" : "Analyze chain"}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={fr ? 'fr' : 'en'} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "#c8102e" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
            <div style={card} data-testid="s1-leg1">
              <div style={{ ...label, fontWeight: 700 }}>1 · {fr ? "Import intrant" : "Import input"}</div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>
                {leg1.landed_cost?.available ? money(leg1.landed_cost.value_usd) : "—"}
              </div>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                {fr ? "Coût rendu intrant" : "Input landed cost"}
                {leg1.tariff?.available ? ` · ${fr ? "tarif" : "tariff"} ${dash(leg1.tariff.tariff_advantage_pct, " %")}` : ""}
              </div>
            </div>
            <div style={card} data-testid="s1-leg2">
              <div style={{ ...label, fontWeight: 700 }}>2 · {fr ? "Production locale" : "Local production"}</div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>
                {leg2.available ? (fr ? "Confirmée ✓" : "Confirmed ✓") : fr ? "Non détectée" : "Not detected"}
              </div>
              {leg2.available && (
                <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                  {leg2.commodity} · {dash(leg2.continental_share_pct, " %")}
                </div>
              )}
            </div>
            <div style={card} data-testid="s1-leg3">
              <div style={{ ...label, fontWeight: 700 }}>3 · {fr ? "Export produit fini" : "Export finished"}</div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>{exportScore != null ? pct(exportScore) : "—"}</div>
              <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                {fr ? "Score export → " : "Export score → "}
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
                {fr ? "Analyser l'export ▸" : "Analyze export ▸"}
              </button>
            </div>
            <div style={card} data-testid="s1-value-added">
              <div style={{ ...label, fontWeight: 700 }}>{fr ? "Valeur ajoutée brute" : "Gross value added"}</div>
              {va.available ? (
                <>
                  <div style={{ fontSize: 15, fontWeight: 700, marginTop: 4 }}>
                    {money(va.gross_value_added_usd)}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                    {fr ? "Marge" : "Margin"} {dash(va.gross_margin_pct, " %")}
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
function ImportOpportunitiesView({ countries, fr, onAnalyze }) {
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
      setError(fr ? "Impossible de générer le scan d'importation." : "Could not run the import scan.");
    } finally {
      setLoading(false);
    }
  };

  const opps = rep?.ranked_opportunities || [];

  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    return {
      badge: `S4-${country}`,
      filename: `s4-importations-${country}`,
      kpis: [
        { label: fr ? "Pays" : "Country", value: country, accent: 'gold' },
        { label: fr ? "Produits scannés" : "Products scanned", value: String(rep.products_scanned || 0), accent: 'blue' }
      ],
      sections: [{ title: fr ? `S4 · Opportunités d'importation` : `S4 · Import opportunities`, text: `${country} · ${rep.candidates_retained || 0} ${fr ? 'retenus' : 'retained'}` }]
    };
  }, [rep, country, fr]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
        <div>
          <div style={label}>{fr ? "Pays importateur" : "Importing country"}</div>
          <Sel value={country} onChange={setCountry} countries={countries} testid="s4-country" />
        </div>
        <div>
          <div style={label}>{fr ? "Produits analysés" : "Products deep-dived"}</div>
          <input value={topK} onChange={(e) => setTopK(e.target.value)} data-testid="s4-topk" style={{ padding: "8px 10px", borderRadius: 8, width: 70 }} />
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
          <input type="checkbox" checked={withImports} onChange={(e) => setWithImports(e.target.checked)} data-testid="s4-imports" />
          {fr ? "Imports observés (OEC)" : "Observed imports (OEC)"}
        </label>
        <button onClick={run} disabled={loading} className="afcfta-btn afcfta-btn-primary" data-testid="s4-run" style={{ padding: "10px 18px", borderRadius: 8 }}>
          {loading ? (fr ? "Scan…" : "Scanning…") : fr ? "Scanner les importations" : "Scan imports"}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={fr ? 'fr' : 'en'} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "#c8102e" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={card} data-testid="s4-result">
            <div style={{ ...label, marginBottom: 4 }}>
              {fr
                ? `Meilleures opportunités d'importation — ${country}`
                : `Best import opportunities — ${country}`}
            </div>
            <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginBottom: 10 }}>
              {rep.products_scanned} {fr ? "produits scannés" : "products scanned"} · {rep.candidates_retained}{" "}
              {fr ? "retenus" : "retained"} · {rep.deep_dived} {fr ? "analysés en profondeur" : "deep-dived"}
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: "1px solid var(--afcfta-border,#dde)" }}>
                    <th style={{ padding: "6px 8px" }}>{fr ? "Produit" : "Product"}</th>
                    <th style={{ padding: "6px 8px" }}>{fr ? "Besoin estimé" : "Est. need"}</th>
                    <th style={{ padding: "6px 8px" }}>{fr ? "Fournisseur conseillé" : "Suggested supplier"}</th>
                    <th style={{ padding: "6px 8px" }}>{fr ? "Avantage tarifaire" : "Tariff advantage"}</th>
                    <th style={{ padding: "6px 8px" }}>Score</th>
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
                            {fr ? "production locale non enregistrée" : "local production not recorded"}
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
                            {fr ? "importe déjà" : "already imports"} {money(o.observed_imports.import_value_usd)}
                            {tonnes(o.observed_imports.import_quantity_tonnes) &&
                              ` · ${tonnes(o.observed_imports.import_quantity_tonnes)}`}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: "6px 8px" }}>
                        <strong>{o.best_supplier?.country_iso3}</strong>
                        <span style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginLeft: 4 }}>
                          {o.best_supplier?.production_share_pct != null ? `${o.best_supplier.production_share_pct}% prod.` : ""}
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
                            {fr ? "Analyser ▸" : "Analyze ▸"}
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

function NationalNeedView({ countries, fr, onAnalyze, prefill }) {
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
      setError(fr ? "Impossible d'estimer le besoin." : "Could not estimate need.");
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

  const buildPdfSpec = useCallback(() => {
    if (!rep) return null;
    return {
      badge: `S3-${hsCode}`,
      filename: `s3-besoin-national-${hsCode}`,
      kpis: [
        { label: fr ? "Code produit" : "Product code", value: hsCode, accent: 'gold' },
        { label: fr ? "Pays" : "Country", value: country, accent: 'blue' }
      ],
      sections: [{ title: fr ? `S3 · Besoin national ${hsCode}` : `S3 · National need ${hsCode}`, text: rep.available ? `${rep.value || '—'} ${rep.unit || ''}` : '' }]
    };
  }, [rep, hsCode, country, fr]);

  return (
    <div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end", marginBottom: 16 }}>
        <div>
          <div style={label}>{fr ? "Pays" : "Country"}</div>
          <Sel value={country} onChange={setCountry} countries={countries} testid="s3-country" />
        </div>
        <div>
          <div style={label}>{fr ? "Code SH" : "HS code"}</div>
          <input value={hsCode} onChange={(e) => setHsCode(e.target.value)} data-testid="s3-hs" style={{ padding: "8px 10px", borderRadius: 8, width: 120 }} />
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
          <input type="checkbox" checked={withImports} onChange={(e) => setWithImports(e.target.checked)} data-testid="s3-imports" />
          {fr ? "Signal d'import (OEC, lent)" : "Import signal (OEC, slow)"}
        </label>
        <button onClick={() => run()} disabled={loading} className="afcfta-btn afcfta-btn-primary" data-testid="s3-run" style={{ padding: "10px 18px", borderRadius: 8 }}>
          {loading ? (fr ? "Estimation…" : "Estimating…") : fr ? "Estimer le besoin" : "Estimate need"}
        </button>
        {rep && <OpportunityPdfExport getSpec={buildPdfSpec} language={fr ? 'fr' : 'en'} />}
      </div>

      {error && <div style={{ ...card, borderColor: "rgba(200,16,46,0.3)", color: "#c8102e" }}>{error}</div>}

      {rep && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={card} data-testid="s3-result">
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <span style={{ ...label, margin: 0 }}>
                {fr ? "Besoin national" : "National need"} — {country}
              </span>
              {rep.available && (
                <EstBadge isEstimation={rep.is_estimation} level={rep.estimation_level} fr={fr} />
              )}
            </div>
            {rep.available ? (
              <>
                <div style={{ fontSize: 26, fontWeight: 800, marginTop: 6 }}>
                  {num(Math.round(rep.value), rep.unit)}
                </div>
                {rep.observed_imports?.import_value_usd && (
                  <div style={{ fontSize: 13, marginTop: 4 }}>
                    {fr ? "Importe déjà" : "Already imports"} : {money(rep.observed_imports.import_value_usd)}
                    {tonnes(rep.observed_imports.import_quantity_tonnes) && (
                      <span style={{ color: "var(--afcfta-muted,#667)" }}>
                        {" "}· {tonnes(rep.observed_imports.import_quantity_tonnes)}
                      </span>
                    )}
                  </div>
                )}
                <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                  {fr ? "Méthode" : "Method"} : {rep.method}
                </div>
                {rep.suggested_supplier?.iso3 && onAnalyze && (
                  <button
                    onClick={() => onAnalyze(rep.suggested_supplier.iso3, country, hsCode)}
                    data-testid="s3-analyze"
                    className="afcfta-btn afcfta-btn-secondary"
                    style={{ padding: "6px 12px", borderRadius: 6, fontSize: 13, marginTop: 10 }}
                  >
                    {fr ? "Analyser l'opportunité" : "Analyze opportunity"} : {rep.suggested_supplier.iso3} → {country} ▸
                  </button>
                )}
              </>
            ) : (
              <div style={{ color: "var(--afcfta-muted,#667)", marginTop: 6 }}>{rep.note || "—"}</div>
            )}
          </div>

          {rep.available && (
            <div style={card}>
              <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
                {fr ? "Intrants du calcul (transparence)" : "Computation inputs (transparency)"}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, fontSize: 13 }}>
                <div>{fr ? "Population" : "Population"} : {num(inp.population)}</div>
                <div>{fr ? "Production continentale" : "Continental production"} : {num(inp.continental_production, rep.unit)}</div>
                {inp.continental_imports_tonnes != null && (
                  <div>{fr ? "Imports continentaux" : "Continental imports"} : {num(inp.continental_imports_tonnes, rep.unit)}</div>
                )}
                <div>{fr ? "Réf. par habitant" : "Per-capita ref."} : {num(inp.per_capita_reference)}</div>
                {inp.gdp_adjustment_factor != null && (
                  <div>{fr ? "Facteur PIB/hab" : "GDP/cap factor"} : {num(inp.gdp_adjustment_factor)}</div>
                )}
              </div>
              {rep.sources?.length > 0 && (
                <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                  {fr ? "Sources" : "Sources"} : {rep.sources.map((s) => srcText(s)).filter(Boolean).join(" · ")}
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
      if (h && h.country && h.hsCode) {
        setS3Prefill({ country: h.country, hsCode: h.hsCode, withImports: true, k: h.k || Date.now() });
        setMode("s3");
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
        {tabBtn("market", fr ? "Trouver des marchés (producteur)" : "Find markets (producer)")}
        {tabBtn("bilateral", fr ? "Rapport bilatéral" : "Bilateral report")}
        {tabBtn("s2", fr ? "S2 · Export direct" : "S2 · Direct export")}
        {tabBtn("s1", fr ? "S1 · Transformation" : "S1 · Transformation")}
        {tabBtn("s3", fr ? "S3 · Besoin national" : "S3 · National need")}
        {tabBtn("s4", fr ? "S4 · Importations" : "S4 · Imports")}
        {tabBtn("s5", fr ? "S5 · Substitution" : "S5 · Substitution")}
      </div>
      {mode === "market" && <MarketSeekingView fr={fr} />}
      {mode === "bilateral" && <BilateralView countries={countries} fr={fr} prefill={prefill} />}
      {mode === "s2" && <DirectExportView countries={countries} fr={fr} onAnalyze={openBilateral} />}
      {mode === "s1" && <TransformationView countries={countries} fr={fr} onAnalyze={openBilateral} />}
      {mode === "s3" && <NationalNeedView countries={countries} fr={fr} onAnalyze={openBilateral} prefill={s3Prefill} />}
      {mode === "s4" && <ImportOpportunitiesView countries={countries} fr={fr} onAnalyze={openBilateral} />}
      {mode === "s5" && <SubstitutionAnalysis language={fr ? "fr" : "en"} />}
    </div>
  );
}
