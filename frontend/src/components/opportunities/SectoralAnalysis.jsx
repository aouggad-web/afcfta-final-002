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

const pct = (v) => (v === null || v === undefined ? "—" : `${Math.round(v * 100)}%`);
const dash = (v, suffix = "") =>
  v === null || v === undefined || v === "" ? "—" : `${v}${suffix}`;

function SectoralAnalysis({ hsCode, origin, destination, fr }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!hsCode || !origin || !destination) return;

    const fetchAnalysis = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          hs_code: hsCode,
          origin,
          destination,
          lang: fr ? "fr" : "en",
        });
        const res = await axios.get(`${API}/opportunities/sectoral-analysis?${params.toString()}`);
        setAnalysis(res.data);
      } catch (e) {
        setError(fr ? "Impossible de charger l'analyse sectorielle." : "Could not load sectoral analysis.");
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [hsCode, origin, destination, fr]);

  if (!analysis || !analysis.available) {
    return null;
  }

  const { sector_profile, opportunity_score, transformation_chain, competitiveness_index, sectoral_barriers, recommended_actions } = analysis;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Sector Profile Card */}
      <div style={card}>
        <div style={{ ...label, marginBottom: 12, fontWeight: 700 }}>
          {fr ? "Profil du secteur (ISIC4)" : "Sector profile (ISIC4)"}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12 }}>
          <div>
            <div style={label}>{fr ? "Code ISIC4" : "ISIC4 code"}</div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{sector_profile.isic4_code}</div>
          </div>
          <div>
            <div style={label}>{fr ? "Secteur" : "Sector"}</div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>{sector_profile.label}</div>
          </div>
          <div>
            <div style={label}>{fr ? "Indice manufacturier" : "Manufacturing index"}</div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>
              {dash(sector_profile.manufacturing_index, "/100")}
            </div>
          </div>
          <div>
            <div style={label}>{fr ? "Compétitivité" : "Competitiveness"}</div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>
              {dash(competitiveness_index, "/100")}
            </div>
          </div>
          <div>
            <div style={label}>{fr ? "Préparation export" : "Export readiness"}</div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>
              {dash(sector_profile.export_readiness, "%")}
            </div>
          </div>
          <div>
            <div style={label}>{fr ? "Score opportunité" : "Opportunity score"}</div>
            <div
              style={{
                fontSize: 16,
                fontWeight: 700,
                color: opportunity_score >= 70 ? "#1a7f37" : opportunity_score >= 50 ? "#9a6700" : "#c8102e",
              }}
            >
              {dash(opportunity_score, "/100")}
            </div>
          </div>
        </div>
      </div>

      {/* Transformation Chain */}
      {transformation_chain && (
        <div style={card}>
          <div style={{ ...label, marginBottom: 12, fontWeight: 700 }}>
            {fr ? "Chaîne de transformation" : "Transformation chain"}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap", fontSize: 13 }}>
            <div>
              <div style={label}>{fr ? "Intrants" : "Inputs"}</div>
              <div style={{ fontWeight: 500 }}>{transformation_chain.input}</div>
            </div>
            <div style={{ fontSize: 20, color: "var(--afcfta-muted,#667)" }}>→</div>
            <div>
              <div style={label}>{fr ? "Procédé" : "Process"}</div>
              <div style={{ fontWeight: 500 }}>{transformation_chain.process}</div>
            </div>
            <div style={{ fontSize: 20, color: "var(--afcfta-muted,#667)" }}>→</div>
            <div>
              <div style={label}>{fr ? "Extrants" : "Outputs"}</div>
              <div style={{ fontWeight: 500 }}>{transformation_chain.output}</div>
            </div>
          </div>
        </div>
      )}

      {/* Barriers */}
      {sectoral_barriers && sectoral_barriers.length > 0 && (
        <div style={card}>
          <div style={{ ...label, marginBottom: 12, fontWeight: 700 }}>
            {fr ? "Barrières sectorielles" : "Sectoral barriers"}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {sectoral_barriers.map((barrier, idx) => (
              <div key={idx} style={{ paddingBottom: idx < sectoral_barriers.length - 1 ? 8 : 0, borderBottom: idx < sectoral_barriers.length - 1 ? "1px solid rgba(0,0,0,0.06)" : "none" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, textTransform: "capitalize" }}>
                    {barrier.type}
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      padding: "2px 6px",
                      borderRadius: 999,
                      background:
                        barrier.impact === "fort" || barrier.impact === "high"
                          ? "rgba(200,16,46,0.12)"
                          : "rgba(154,103,0,0.12)",
                      color:
                        barrier.impact === "fort" || barrier.impact === "high"
                          ? "#c8102e"
                          : "#9a6700",
                    }}
                  >
                    {barrier.impact}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: "var(--afcfta-muted,#667)" }}>
                  {barrier.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommended_actions && recommended_actions.length > 0 && (
        <div style={card}>
          <div style={{ ...label, marginBottom: 12, fontWeight: 700 }}>
            {fr ? "Recommandations stratégiques" : "Strategic recommendations"}
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.7 }}>
            {recommended_actions.map((action, idx) => (
              <li key={idx} style={{ marginBottom: 6 }}>
                {action}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sector Metrics Table */}
      {sector_profile && (
        <div style={card}>
          <div style={{ ...label, marginBottom: 12, fontWeight: 700 }}>
            {fr ? "Indicateurs du secteur" : "Sector indicators"}
          </div>
          <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
            <tbody>
              {sector_profile.avg_productivity && (
                <tr style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                  <td style={td}>{fr ? "Productivité moyenne" : "Avg. productivity"}</td>
                  <td style={{ ...td, textAlign: "right", fontWeight: 600 }}>
                    {sector_profile.avg_productivity.toFixed(2)}
                  </td>
                </tr>
              )}
              {sector_profile.skill_level !== undefined && (
                <tr style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                  <td style={td}>{fr ? "Niveau de compétence requis" : "Required skill level"}</td>
                  <td style={{ ...td, textAlign: "right", fontWeight: 600 }}>
                    {sector_profile.skill_level.toFixed(1)}/5
                  </td>
                </tr>
              )}
              {sector_profile.capex_intensity !== undefined && (
                <tr style={{ borderTop: "1px solid rgba(0,0,0,0.06)" }}>
                  <td style={td}>{fr ? "Intensité capitalistique" : "Capital intensity"}</td>
                  <td style={{ ...td, textAlign: "right", fontWeight: 600 }}>
                    {pct(sector_profile.capex_intensity)}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default SectoralAnalysis;
