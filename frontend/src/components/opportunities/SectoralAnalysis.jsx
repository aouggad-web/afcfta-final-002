import React, { useState, useEffect } from "react";
import axios from "axios";

const API = `${import.meta.env.VITE_BACKEND_URL || ""}/api`;

const card = {
  background: "var(--afcfta-card, #fff)",
  border: "1px solid var(--afcfta-border, rgba(0,0,0,0.08))",
  borderRadius: 12,
  padding: 16,
};

const label = { fontSize: 12, color: "var(--afcfta-muted, #667)", marginBottom: 4 };
const th = { padding: "4px 8px", textAlign: "left", color: "var(--afcfta-muted,#667)", fontSize: 12 };
const td = { padding: "4px 8px", fontSize: 12 };

const dash = (v, suffix = "") =>
  v === null || v === undefined || v === "" ? "—" : `${v}${suffix}`;

const money = (v) =>
  v === null || v === undefined
    ? "—"
    : `$${Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;

/* Compact USD (e.g. $3.3B, $46B, $120M) for large industrial aggregates. */
const moneyShort = (v) => {
  if (v === null || v === undefined) return "—";
  const n = Number(v);
  const abs = Math.abs(n);
  if (abs >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  return money(n);
};

const intFmt = (v) =>
  v === null || v === undefined ? "—" : Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 });

/* Provenance micro-badge: IDSB values are UNIDO DERIVED ESTIMATES, INDSTAT values
   are OFFICIAL statistics. Never conflate the two — show each metric's real nature. */
const provMeta = (nature, fr) => {
  if (nature === "official")
    return {
      t: "off.",
      title: fr ? "INDSTAT — statistique officielle UNIDO" : "INDSTAT — UNIDO official statistic",
      fg: "#1a7f37",
      bg: "rgba(26,127,55,0.12)",
    };
  if (nature === "derived_estimate")
    return {
      t: "est.",
      title: fr ? "IDSB — estimation dérivée UNIDO" : "IDSB — UNIDO derived estimate",
      fg: "#9a6700",
      bg: "rgba(154,103,0,0.12)",
    };
  if (nature === "mixed")
    return {
      t: fr ? "mixte" : "mixed",
      title: fr ? "Sources mêlées (officielle + estimation)" : "Mixed sources (official + estimate)",
      fg: "#667",
      bg: "rgba(102,102,102,0.12)",
    };
  return null;
};

function Prov({ nature, fr }) {
  const m = provMeta(nature, fr);
  if (!m) return null;
  return (
    <sup
      title={m.title}
      style={{
        marginLeft: 4,
        fontSize: 9,
        fontWeight: 700,
        padding: "1px 4px",
        borderRadius: 4,
        background: m.bg,
        color: m.fg,
      }}
    >
      {m.t}
    </sup>
  );
}

/* Colour per demand-supply verdict (IDSB reading). */
const BALANCE_STYLE = {
  supply_and_demand: { bg: "rgba(26,127,55,0.12)", fg: "#1a7f37" },
  demand_without_supply: { bg: "rgba(154,103,0,0.12)", fg: "#9a6700" },
  supply_without_demand: { bg: "rgba(154,103,0,0.12)", fg: "#9a6700" },
  insufficient_data: { bg: "rgba(102,102,102,0.12)", fg: "#667" },
};

function Chip({ ok, children }) {
  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 700,
        padding: "2px 8px",
        borderRadius: 999,
        background: ok ? "rgba(26,127,55,0.12)" : "rgba(102,102,102,0.12)",
        color: ok ? "#1a7f37" : "#667",
      }}
    >
      {children}
    </span>
  );
}

function SectoralAnalysis({ hsCode, origin, destination, fr }) {
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    if (!hsCode || !origin || !destination) return;
    let cancelled = false;

    const fetchAnalysis = async () => {
      try {
        const params = new URLSearchParams({
          hs_code: hsCode,
          origin,
          destination,
          lang: fr ? "fr" : "en",
        });
        const res = await axios.get(`${API}/reports/sectoral-analysis?${params.toString()}`);
        if (!cancelled) setAnalysis(res.data);
      } catch (e) {
        if (!cancelled) setAnalysis(null);
      }
    };

    fetchAnalysis();
    return () => {
      cancelled = true;
    };
  }, [hsCode, origin, destination, fr]);

  // Non-manufacturing products (primary agri/extractive) are covered by the
  // production/supply views elsewhere — this industrial lens doesn't apply.
  if (!analysis || !analysis.available) return null;

  const {
    isic4,
    product_label,
    transformation_chain,
    industrial_base,
    market_demand,
    demand_supply_balance,
    diversification_products,
    coverage,
    sources,
  } = analysis;

  const bal = demand_supply_balance || {};
  const balStyle = BALANCE_STYLE[bal.verdict] || BALANCE_STYLE.insufficient_data;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* ISIC4 classification + transformation chain */}
      <div style={card}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
          <span style={{ ...label, margin: 0, fontWeight: 700 }}>
            {fr ? "Classification industrielle ISIC Rev.4" : "ISIC Rev.4 industrial classification"}
          </span>
          <span
            style={{
              fontSize: 12,
              fontWeight: 700,
              padding: "2px 10px",
              borderRadius: 999,
              background: "rgba(9,105,218,0.12)",
              color: "#0969da",
            }}
          >
            ISIC {isic4?.code}
          </span>
        </div>
        <div style={{ fontSize: 15, fontWeight: 700 }}>
          {isic4?.label}
          {product_label ? (
            <span style={{ fontSize: 13, fontWeight: 400, color: "var(--afcfta-muted,#667)" }}>
              {" "}
              · {product_label} (SH {hsCode})
            </span>
          ) : null}
        </div>

        {transformation_chain && (
          <div style={{ display: "flex", alignItems: "stretch", gap: 12, flexWrap: "wrap", marginTop: 14 }}>
            {[
              { k: "input", t: fr ? "Intrant" : "Input" },
              { k: "process", t: fr ? "Procédé" : "Process" },
              { k: "output", t: fr ? "Extrant" : "Output" },
            ].map((seg, i) => (
              <React.Fragment key={seg.k}>
                {i > 0 && (
                  <div style={{ display: "flex", alignItems: "center", fontSize: 20, color: "var(--afcfta-muted,#667)" }}>
                    →
                  </div>
                )}
                <div style={{ flex: "1 1 150px", minWidth: 130 }}>
                  <div style={label}>{seg.t}</div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{dash(transformation_chain[seg.k])}</div>
                </div>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Demand-supply balance (IDSB reading) */}
      {demand_supply_balance && (
        <div style={card}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 10 }}>
            <span style={{ ...label, margin: 0, fontWeight: 700 }}>
              {fr ? "Équilibre offre-demande (UNIDO IDSB)" : "Demand–supply balance (UNIDO IDSB)"}
            </span>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: 999,
                background: balStyle.bg,
                color: balStyle.fg,
                textTransform: "uppercase",
              }}
            >
              {(bal.verdict || "—").replace(/_/g, " ")}
            </span>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
            <Chip ok={bal.supply_measured}>
              {fr ? "Offre" : "Supply"} {bal.supply_measured ? (fr ? "attestée ✓" : "recorded ✓") : fr ? "non attestée" : "not recorded"}
            </Chip>
            <Chip ok={bal.demand_measured}>
              {fr ? "Demande" : "Demand"} {bal.demand_measured ? (fr ? "attestée ✓" : "recorded ✓") : fr ? "non attestée" : "not recorded"}
            </Chip>
            {bal.origin_exports_division && (
              <Chip ok>{fr ? "Origine exporte déjà" : "Origin already exports"}</Chip>
            )}
            {bal.hs_import_demand_usd != null && (
              <Chip ok>
                {fr ? "Imports OEC (SH exact)" : "OEC imports (exact HS)"} · {money(bal.hs_import_demand_usd)}
              </Chip>
            )}
          </div>
          <div style={{ fontSize: 13, color: "var(--afcfta-muted,#667)", lineHeight: 1.6 }}>
            {bal.interpretation}
          </div>
        </div>
      )}

      {/* Origin industrial base + destination demand side by side */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
        {/* Origin industrial base (real UNIDO IDSB/INDSTAT) */}
        <div style={card}>
          <div style={{ ...label, marginBottom: 10, fontWeight: 700 }}>
            {fr ? `Base industrielle — origine ${origin}` : `Industrial base — origin ${origin}`}
          </div>
          {industrial_base?.available ? (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
                <div>
                  <div style={label}>{fr ? "Production" : "Output"}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(industrial_base.output_usd)}
                    <Prov nature={industrial_base.provenance?.output_usd} fr={fr} />
                  </div>
                </div>
                <div>
                  <div style={label}>{fr ? "Valeur ajoutée" : "Value added"}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(industrial_base.value_added_usd)}
                    <Prov nature={industrial_base.provenance?.value_added_usd} fr={fr} />
                  </div>
                </div>
                <div>
                  <div style={label}>{fr ? "Exports mondiaux" : "World exports"}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(industrial_base.exports_world_usd)}
                    <Prov nature={industrial_base.provenance?.exports_world_usd} fr={fr} />
                  </div>
                </div>
                <div>
                  <div style={label}>{fr ? "Emplois" : "Employees"}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {intFmt(industrial_base.employees)}
                    <Prov nature={industrial_base.provenance?.employees} fr={fr} />
                  </div>
                </div>
              </div>
              {industrial_base.top_subsectors?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={label}>{fr ? "Principaux sous-secteurs (production)" : "Top sub-sectors (output)"}</div>
                  <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                    <thead>
                      <tr>
                        <th style={th} scope="col">{fr ? "ISIC" : "ISIC"}</th>
                        <th style={th} scope="col">{fr ? "Sous-secteur" : "Sub-sector"}</th>
                        <th style={{ ...th, textAlign: "right" }} scope="col">{fr ? "Production" : "Output"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {industrial_base.top_subsectors.map((sub) => (
                        <tr key={sub.isic4} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                          <td style={{ ...td, fontWeight: 600, whiteSpace: "nowrap" }}>{sub.isic4}</td>
                          <td style={td}>{sub.label}</td>
                          <td style={{ ...td, textAlign: "right", fontWeight: 600 }}>{moneyShort(sub.output_usd)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 10 }}>
                {industrial_base.source}
                {industrial_base.year_range ? ` · ${industrial_base.year_range}` : ""}
              </div>
              <div style={{ fontSize: 10, color: "var(--afcfta-muted,#667)", marginTop: 4 }}>
                {fr
                  ? "est. = estimation dérivée UNIDO (IDSB) · off. = statistique officielle (INDSTAT)"
                  : "est. = UNIDO derived estimate (IDSB) · off. = official statistic (INDSTAT)"}
              </div>
            </>
          ) : (
            <div style={{ fontSize: 13, color: "var(--afcfta-muted,#667)" }}>
              {industrial_base?.reason === "country_not_in_unido_idsb_coverage"
                ? fr
                  ? `${origin} hors couverture UNIDO IDSB (20 pays africains) — non estimé.`
                  : `${origin} outside UNIDO IDSB coverage (20 African countries) — not estimated.`
                : fr
                ? "Aucune donnée industrielle UNIDO pour cette division — non estimée."
                : "No UNIDO industrial data for this division — not estimated."}
            </div>
          )}
        </div>

        {/* Destination market demand (real UNIDO IDSB) */}
        <div style={card}>
          <div style={{ ...label, marginBottom: 10, fontWeight: 700 }}>
            {fr ? `Demande du marché — destination ${destination}` : `Market demand — destination ${destination}`}
          </div>
          {market_demand?.available ? (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
                <div>
                  <div style={label}>{fr ? "Consommation apparente" : "Apparent consumption"}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(market_demand.apparent_consumption_usd)}
                    <Prov nature={market_demand.provenance?.apparent_consumption_usd} fr={fr} />
                  </div>
                </div>
                <div>
                  <div style={label}>{fr ? "Imports mondiaux" : "World imports"}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(market_demand.imports_world_usd)}
                    <Prov nature={market_demand.provenance?.imports_world_usd} fr={fr} />
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 10 }}>
                {market_demand.source}
                {market_demand.year_range ? ` · ${market_demand.year_range}` : ""}
              </div>
            </>
          ) : (
            <div style={{ fontSize: 13, color: "var(--afcfta-muted,#667)" }}>
              {market_demand?.reason === "country_not_in_unido_idsb_coverage"
                ? fr
                  ? `${destination} hors couverture UNIDO IDSB (20 pays africains) — non estimé.`
                  : `${destination} outside UNIDO IDSB coverage (20 African countries) — not estimated.`
                : fr
                ? "Aucune donnée de demande UNIDO pour cette division — non estimée."
                : "No UNIDO demand data for this division — not estimated."}
            </div>
          )}
        </div>
      </div>

      {/* Diversification products (same ISIC capability) */}
      {diversification_products && diversification_products.length > 0 && (
        <div style={card}>
          <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
            {fr
              ? "Diversification — mêmes intrants et procédé (division ISIC)"
              : "Diversification — same inputs and process (ISIC division)"}
          </div>
          <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={th}>{fr ? "Code SH" : "HS code"}</th>
                <th style={th}>{fr ? "Produit exportable" : "Exportable product"}</th>
              </tr>
            </thead>
            <tbody>
              {diversification_products.map((p) => (
                <tr key={p.hs4} style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                  <td style={{ ...td, fontWeight: 600 }}>{p.hs4}</td>
                  <td style={td}>{p.label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)" }}>
        {sources?.classification} · {sources?.industrial_data}
        {coverage && !coverage.origin_in_idsb && !coverage.destination_in_idsb ? (
          <>
            {" "}
            ·{" "}
            {fr
              ? "aucun des deux pays n'est dans la couverture UNIDO IDSB"
              : "neither country is in UNIDO IDSB coverage"}
          </>
        ) : null}
      </div>
    </div>
  );
}

export default SectoralAnalysis;
