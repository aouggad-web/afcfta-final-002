import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
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

/* Source may be a plain string or {institution, dataset, url}. */
const srcText = (s) =>
  !s
    ? ""
    : typeof s === "string"
    ? s
    : [s.institution, s.dataset].filter(Boolean).join(" · ");

/* Provenance micro-badge: IDSB values are UNIDO DERIVED ESTIMATES, INDSTAT values
   are OFFICIAL statistics. Never conflate the two — show each metric's real nature. */
const provMeta = (nature, t) => {
  if (nature === "official")
    return {
      t: "off.",
      title: t("opportunities.sectoralAnalysis.indstatUnidoOfficialStatistic"),
      fg: "#1a7f37",
      bg: "rgba(26,127,55,0.12)",
    };
  if (nature === "derived_estimate")
    return {
      t: "est.",
      title: t("opportunities.sectoralAnalysis.idsbUnidoDerivedEstimate"),
      fg: "#9a6700",
      bg: "rgba(154,103,0,0.12)",
    };
  if (nature === "mixed")
    return {
      t: t("opportunities.sectoralAnalysis.mixed"),
      title: t("opportunities.sectoralAnalysis.mixedSourcesOfficialEstimate"),
      fg: "#667",
      bg: "rgba(102,102,102,0.12)",
    };
  return null;
};

function Prov({ nature }) {
  const { t } = useTranslation();
  const m = provMeta(nature, t);
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

/* Localized label per verdict — never show the raw wire-format enum. */
// Le verdict arrive du serveur sous sa forme machine ; le repli rend cette
// forme lisible plutôt que la clé i18n, qu'i18next renverrait telle quelle.
const verdictLabel = (verdict, t) =>
  t(`opportunities.sectoralAnalysis.verdict.${verdict}`, {
    defaultValue: (verdict || "—").replace(/_/g, " "),
  });

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
  const { t } = useTranslation();
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    // Clear any prior result immediately, so changing the submitted report or
    // the language never leaves a stale corridor/language analysis visible next
    // to the new report while the new request runs — and an emptied input leaves
    // nothing lingering.
    setAnalysis(null);
    setError(false);
    if (!hsCode || !origin || !destination) {
      return () => {
        cancelled = true;
      };
    }

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
        // Distinguish a real request failure from the loading / no-section case,
        // so users don't mistake an unavailable service for "no sectoral data".
        if (!cancelled) setError(true);
      }
    };

    fetchAnalysis();
    return () => {
      cancelled = true;
    };
  }, [hsCode, origin, destination, fr]);

  // Request failed — surface it instead of silently vanishing like loading does.
  if (error) {
    return (
      <div style={{ ...card, color: "#9a6700", fontSize: 13, lineHeight: 1.6 }}>
        <div style={{ ...label, marginBottom: 4, fontWeight: 700 }}>
          {t("opportunities.sectoralAnalysis.sectoralAnalysisIsic4Idsb")}
        </div>
        {t("opportunities.sectoralAnalysis.serviceTemporarilyUnavailableSectoral")}
      </div>
    );
  }

  // No request yet / still loading — render nothing.
  if (!analysis) return null;

  // Not applicable (uncatalogued HS code, ambiguous ISIC mapping…): surface the
  // honest note rather than silently dropping the whole section.
  if (!analysis.available) {
    return analysis.note ? (
      <div style={{ ...card, color: "var(--afcfta-muted,#667)", fontSize: 13, lineHeight: 1.6 }}>
        <div style={{ ...label, marginBottom: 4, fontWeight: 700 }}>
          {t("opportunities.sectoralAnalysis.sectoralAnalysisIsic4Idsb")}
        </div>
        {analysis.note}
      </div>
    ) : null;
  }

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
            {t("opportunities.sectoralAnalysis.isicRev4Industrial")}
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
              { k: "input", t: t("opportunities.sectoralAnalysis.input") },
              { k: "process", t: t("opportunities.sectoralAnalysis.process") },
              { k: "output", t: t("opportunities.sectoralAnalysis.output") },
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
              {t("opportunities.sectoralAnalysis.demandSupplyBalanceUnido")}
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
              {verdictLabel(bal.verdict, t)}
            </span>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
            <Chip ok={bal.supply_measured}>
              {t("opportunities.sectoralAnalysis.supply")} {bal.supply_measured ? t("opportunities.sectoralAnalysis.recorded") : t("opportunities.sectoralAnalysis.notRecorded")}
            </Chip>
            <Chip ok={bal.demand_measured}>
              {t("opportunities.sectoralAnalysis.demand")} {bal.demand_measured ? t("opportunities.sectoralAnalysis.recorded") : t("opportunities.sectoralAnalysis.notRecorded")}
            </Chip>
            {bal.origin_exports_division && (
              <Chip ok>{t("opportunities.sectoralAnalysis.originAlreadyExports")}</Chip>
            )}
            {bal.hs_import_demand?.value != null && (
              <Chip ok>
                {t("opportunities.sectoralAnalysis.oecImportsExactHs")} · {money(bal.hs_import_demand.value)}
                {bal.hs_import_demand.year ? ` (${bal.hs_import_demand.year})` : ""}
              </Chip>
            )}
          </div>
          <div style={{ fontSize: 13, color: "var(--afcfta-muted,#667)", lineHeight: 1.6 }}>
            {bal.interpretation}
          </div>
          {bal.hs_import_demand?.source && (
            <div style={{ fontSize: 11, color: "var(--afcfta-muted,#667)", marginTop: 6 }}>
              {t("opportunities.sectoralAnalysis.demandSourceExactHs")} :{" "}
              {srcText(bal.hs_import_demand.source)}
              {bal.hs_import_demand.year ? ` · ${bal.hs_import_demand.year}` : ""}
            </div>
          )}
        </div>
      )}

      {/* Origin industrial base + destination demand side by side */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
        {/* Origin industrial base (real UNIDO IDSB/INDSTAT) */}
        <div style={card}>
          <div style={{ ...label, marginBottom: 10, fontWeight: 700 }}>
            {t("opportunities.sectoralAnalysis.industrialBaseOrigin", { origin })}
          </div>
          {industrial_base?.available ? (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
                <div>
                  <div style={label}>{t("opportunities.sectoralAnalysis.output2")}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(industrial_base.output_usd)}
                    <Prov nature={industrial_base.provenance?.output_usd} />
                  </div>
                </div>
                <div>
                  <div style={label}>{t("opportunities.sectoralAnalysis.valueAdded")}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(industrial_base.value_added_usd)}
                    <Prov nature={industrial_base.provenance?.value_added_usd} />
                  </div>
                </div>
                <div>
                  <div style={label}>{t("opportunities.sectoralAnalysis.worldExports")}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(industrial_base.exports_world_usd)}
                    <Prov nature={industrial_base.provenance?.exports_world_usd} />
                  </div>
                </div>
                <div>
                  <div style={label}>{t("opportunities.sectoralAnalysis.employees")}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {intFmt(industrial_base.employees)}
                    <Prov nature={industrial_base.provenance?.employees} />
                  </div>
                </div>
                {/* Establishments counts toward "supply recorded" on the backend,
                    so it must be visible — otherwise a division with only this
                    metric shows every value as — yet claims supply. */}
                {industrial_base.establishments != null && (
                  <div>
                    <div style={label}>{t("opportunities.sectoralAnalysis.establishments")}</div>
                    <div style={{ fontSize: 17, fontWeight: 700 }}>
                      {intFmt(industrial_base.establishments)}
                      <Prov nature={industrial_base.provenance?.establishments} />
                    </div>
                  </div>
                )}
              </div>
              {industrial_base.top_subsectors?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={label}>{t("opportunities.sectoralAnalysis.topSubSectorsOutput")}</div>
                  <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                    <thead>
                      <tr>
                        <th style={th} scope="col">{t("opportunities.sectoralAnalysis.isic")}</th>
                        <th style={th} scope="col">{t("opportunities.sectoralAnalysis.subSector")}</th>
                        <th style={{ ...th, textAlign: "right" }} scope="col">{t("opportunities.sectoralAnalysis.output2")}</th>
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
                {t("opportunities.sectoralAnalysis.estUnidoDerivedEstimate")}
              </div>
            </>
          ) : (
            <div style={{ fontSize: 13, color: "var(--afcfta-muted,#667)" }}>
              {industrial_base?.reason === "country_not_in_unido_idsb_coverage"
                ? t("opportunities.sectoralAnalysis.outsideUnidoIdsbCoverage", { origin })
                : t("opportunities.sectoralAnalysis.noUnidoIndustrialData")}
            </div>
          )}
        </div>

        {/* Destination market demand (real UNIDO IDSB) */}
        <div style={card}>
          <div style={{ ...label, marginBottom: 10, fontWeight: 700 }}>
            {t("opportunities.sectoralAnalysis.marketDemandDestination", { destination })}
          </div>
          {market_demand?.available ? (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
                <div>
                  <div style={label}>{t("opportunities.sectoralAnalysis.apparentConsumption")}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(market_demand.apparent_consumption_usd)}
                    <Prov nature={market_demand.provenance?.apparent_consumption_usd} />
                  </div>
                </div>
                <div>
                  <div style={label}>{t("opportunities.sectoralAnalysis.worldImports")}</div>
                  <div style={{ fontSize: 17, fontWeight: 700 }}>
                    {moneyShort(market_demand.imports_world_usd)}
                    <Prov nature={market_demand.provenance?.imports_world_usd} />
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
                ? t("opportunities.sectoralAnalysis.outsideUnidoIdsbCoverage2", { destination })
                : t("opportunities.sectoralAnalysis.noUnidoDemandData")}
            </div>
          )}
        </div>
      </div>

      {/* Diversification products (same ISIC capability) */}
      {diversification_products && diversification_products.length > 0 && (
        <div style={card}>
          <div style={{ ...label, marginBottom: 8, fontWeight: 700 }}>
            {t("opportunities.sectoralAnalysis.diversificationSameInputsProcess")}
          </div>
          <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={th} scope="col">{t("opportunities.sectoralAnalysis.hsCode")}</th>
                <th style={th} scope="col">{t("opportunities.sectoralAnalysis.exportableProduct")}</th>
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
            {t("opportunities.sectoralAnalysis.neitherCountryIsUnido")}
          </>
        ) : null}
      </div>
    </div>
  );
}

export default SectoralAnalysis;
