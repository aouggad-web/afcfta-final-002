import React, { useState } from "react";
import axios from "axios";

const API = `${import.meta.env.VITE_BACKEND_URL || ""}/api`;

/* Honest formatter: null / undefined -> "—" (never invented). */
const dash = (v, suffix = "") =>
  v === null || v === undefined || v === "" ? "—" : `${v}${suffix}`;

const pct = (v) => (v === null || v === undefined ? "—" : `${Math.round(v * 100)}%`);

const money = (v) =>
  v === null || v === undefined
    ? "—"
    : `$${Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

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

/* ── Mode 1: producer looking for markets ─────────────────────────────────── */
function MarketSeekingView({ fr }) {
  const [hsCode, setHsCode] = useState("1801");
  const [year, setYear] = useState("2022");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rep, setRep] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setRep(null);
    try {
      const params = new URLSearchParams({ hs_code: hsCode, year, lang: fr ? "fr" : "en" });
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
        <div>
          <div style={label}>{fr ? "Année" : "Year"}</div>
          <input
            value={year}
            onChange={(e) => setYear(e.target.value)}
            data-testid="ms-year"
            style={{ padding: "8px 10px", borderRadius: 8, width: 100 }}
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
function BilateralView({ countries, fr }) {
  const [origin, setOrigin] = useState("CIV");
  const [destination, setDestination] = useState("NGA");
  const [hsCode, setHsCode] = useState("1801");
  const [goodsValue, setGoodsValue] = useState("50000");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const params = new URLSearchParams({ hs_code: hsCode, origin, destination, mode: "ultra_fine" });
      if (goodsValue) params.set("goods_value_usd", goodsValue);
      const res = await axios.get(`${API}/reports/opportunity?${params.toString()}`);
      setReport(res.data);
    } catch (e) {
      setError(fr ? "Impossible de générer le rapport." : "Could not generate report.");
    } finally {
      setLoading(false);
    }
  };

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
  const risk = fin.country_risk || {};
  const tf = fin.trade_finance || {};
  const pay = fin.payment_coverage || {};

  // Ultra-fine sections
  const exec = report?.executive_summary || null;
  const narr = report?.narrative_analysis || {};
  const need = report?.national_need || {};
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
                    )}`
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
                      <td style={td}>{b.component}</td>
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
                {fr
                  ? "Le potentiel de marché par produit (flux OEC) requiert une API payante — exclu, jamais estimé."
                  : "Per-product market potential (OEC flows) needs a paid API — excluded, never estimated."}
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
                    </div>
                  )}
                  <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>{need.method}</div>
                </>
              ) : (
                <div style={{ color: "var(--afcfta-muted,#667)" }}>{need.note || "—"}</div>
              )}
            </div>
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
                  <div>
                    {fr ? "Droit national" : "National duty"} {dash(tariff.national_rate_pct, " %")} → ZLECAf{" "}
                    {dash(tariff.zlecaf_rate_pct, " %")}
                  </div>
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
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {factors.map((f) => (
                    <div key={f.factor} style={{ display: "flex", alignItems: "baseline", gap: 8, fontSize: 13 }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          color:
                            f.category === "opportunity" ? "#1a7f37" : f.category === "risk" ? "#c8102e" : "#8b949e",
                        }}
                      >
                        {f.category === "opportunity" ? "▲" : f.category === "risk" ? "▼" : "■"}
                      </span>
                      <span style={{ fontWeight: 600, minWidth: 130 }}>{f.factor}</span>
                      <span style={{ color: "var(--afcfta-muted,#667)" }}>{f.rationale}</span>
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
                      <td style={td}>{num(p.production_volume, topProducers.year ? "" : "")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 8 }}>
                {srcText(topProducers.source)}{topProducers.year ? ` · ${topProducers.year}` : ""}
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

export default function OpportunityReportTab({ countries = [], language = "fr" }) {
  const fr = language === "fr";
  const [mode, setMode] = useState("market");

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
      </div>
      {mode === "market" ? (
        <MarketSeekingView fr={fr} />
      ) : (
        <BilateralView countries={countries} fr={fr} />
      )}
    </div>
  );
}
