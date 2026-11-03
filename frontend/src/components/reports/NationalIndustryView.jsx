import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { nomPays } from "../../utils/iso3166";
import { pick, intlLocale } from "../../i18n/lang";
import { reportsNoticeText } from "../tools/entitlementNotice";
import SubscriptionNotice from "../tools/SubscriptionNotice";

const API = `${import.meta.env.VITE_BACKEND_URL || ""}/api`;

/* Montants : « 64,6 Md $ » en français, « $64.6B » en anglais (décision du
   propriétaire). null → « — », jamais une valeur inventée. */
const NBSP = "\u00A0";
export function montant(v, fr) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
  const n = Number(v);
  const a = Math.abs(n);
  const [div, uFr, uEn] =
    a >= 1e9 ? [1e9, "Md", "B"] : a >= 1e6 ? [1e6, "M", "M"] : a >= 1e3 ? [1e3, "k", "K"] : [1, "", ""];
  const chiffre = (n / div)
    .toLocaleString(fr ? "fr-FR" : "en-US", { maximumFractionDigits: div === 1 ? 0 : 1 })
    .replace(/\u202F/g, NBSP);
  if (fr) return `${chiffre}${uFr ? NBSP + uFr : ""}${NBSP}$`;
  return `${n < 0 ? "-" : ""}$${chiffre.replace("-", "")}${uEn}`;
}
const pourcent = (v, fr) =>
  v === null || v === undefined
    ? "—"
    : `${Number(v).toLocaleString(fr ? "fr-FR" : "en-US", { maximumFractionDigits: 1 })}${fr ? NBSP : ""}%`;
const signe = (v, fr) => (v === null || v === undefined ? "—" : `${v > 0 ? "+" : ""}${pourcent(v, fr)}`);

const card = {
  background: "var(--afcfta-card, #fff)",
  border: "1px solid var(--afcfta-border, rgba(0,0,0,0.08))",
  borderRadius: 12,
  padding: 16,
};
const titre = { fontSize: 14, fontWeight: 700, marginBottom: 8 };
const muted = { fontSize: 12, color: "var(--afcfta-muted,#667)" };
const th = { padding: "4px 8px", textAlign: "left", color: "var(--afcfta-muted,#667)", fontWeight: 600 };
const thNum = { ...th, textAlign: "right" };
const td = { padding: "4px 8px" };
const tdNum = { ...td, textAlign: "right", fontVariantNumeric: "tabular-nums" };
const ligne = { borderTop: "1px solid var(--afcfta-border, rgba(0,0,0,0.06))" };

/* Nature d'un chiffre : officiel, calculé à partir de l'officiel, estimation.
   Une estimation ne doit jamais se lire comme une mesure. */
function NatureBadge({ nature, confiance, language }) {
  const estime = nature === "estimation";
  const texte = estime
    ? `${pick(language, "Estimation", "Estimate", "تقدير")}${confiance ? ` · ${pick(language, "confiance", "confidence", "الثقة")} ${confiance}` : ""}`
    : nature === "calcul_officiel"
    ? pick(language, "Calculé (officiel)", "Derived (official)", "محسوب (رسمي)")
    : pick(language, "Officiel", "Official", "رسمي");
  return (
    <span
      data-testid={`nature-${nature}`}
      style={{
        display: "inline-block",
        fontSize: 11,
        fontWeight: 700,
        padding: "2px 8px",
        borderRadius: 999,
        // Jetons du thème : contraste vérifié en clair comme en sombre.
        background: `color-mix(in srgb, var(${estime ? "--warning" : "--success"}) 14%, transparent)`,
        color: estime ? "var(--warning, #8F5C08)" : "var(--success, #136143)",
      }}
    >
      {texte}
    </span>
  );
}

function IndustrieBloc({ ind, fr, language }) {
  const t24 = ind.total["2024"];
  const t25 = ind.total["2025"];
  const branches = [...ind.branches].sort((a, b) => b.annees["2024"].va_musd - a.annees["2024"].va_musd);
  const raff = ind.branches.find((b) => b.code === "19");
  const horsRaffinage = raff ? t24.va_musd - raff.annees["2024"].va_musd : null;
  return (
    <div style={card} data-testid="dza-industrie">
      <div style={titre}>{pick(language, "Industrie manufacturière par branche", "Manufacturing by branch", "الصناعة التحويلية حسب الفرع")}</div>
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 12 }}>
        <div>
          <div style={muted}>{pick(language, "Valeur ajoutée 2024", "Value added 2024", "القيمة المضافة 2024")}</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{montant(t24.va_musd * 1e6, fr)}</div>
          <NatureBadge nature="officiel" language={language} />
        </div>
        <div>
          <div style={muted}>{pick(language, "Hors raffinage", "Excluding refining", "دون التكرير")}</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{montant(horsRaffinage * 1e6, fr)}</div>
          <NatureBadge nature="officiel" language={language} />
        </div>
        <div>
          <div style={muted}>{pick(language, "Production brute 2024", "Gross output 2024", "الإنتاج الإجمالي 2024")}</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{montant(t24.production_brute_musd * 1e6, fr)}</div>
          <NatureBadge nature="officiel" language={language} />
        </div>
        <div>
          <div style={muted}>{pick(language, "Croissance en volume 2025", "Volume growth 2025", "النمو الحجمي 2025")}</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{signe(t25.croissance_volume_pct.central, fr)}</div>
          <div style={muted}>
            {pick(language, "fourchette", "range", "النطاق")} {signe(t25.croissance_volume_pct.bas, fr)} {pick(language, "à", "to", "إلى")}{" "}
            {signe(t25.croissance_volume_pct.haut, fr)}
          </div>
          <NatureBadge nature="estimation" language={language} />
        </div>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ ...th, width: "34%" }}>{pick(language, "Branche", "Branch", "الفرع")}</th>
              <th style={thNum}>{pick(language, "VA 2024", "VA 2024", "القيمة المضافة 2024")}</th>
              <th style={thNum}>{pick(language, "Part privée", "Private share", "حصة القطاع الخاص")}</th>
              <th style={thNum}>{pick(language, "Volume 2024", "Volume 2024", "الحجم 2024")}</th>
              <th style={thNum}>{pick(language, "Volume 2025 (estimation)", "Volume 2025 (estimate)", "الحجم 2025 (تقدير)")}</th>
            </tr>
          </thead>
          <tbody>
            {branches.map((b) => {
              const a24 = b.annees["2024"];
              const e = b.annees["2025"];
              return (
                <tr key={b.code} style={ligne} data-testid={`branche-${b.code}`}>
                  <td style={td}>
                    {b.libelle}
                    <span style={{ ...muted, marginLeft: 6 }}>CITI {b.citi_rev4.join(", ")}</span>
                  </td>
                  <td style={tdNum}>{montant(a24.va_musd * 1e6, fr)}</td>
                  <td style={tdNum}>{pourcent(a24.part_privee_va_pct, fr)}</td>
                  <td style={tdNum}>{signe(a24.croissance_volume_pct, fr)}</td>
                  <td style={tdNum} title={e.indicateurs.join("\n")}>
                    {signe(e.croissance_volume_pct.central, fr)}{" "}
                    <span style={muted}>
                      [{signe(e.croissance_volume_pct.bas, fr)} ; {signe(e.croissance_volume_pct.haut, fr)}]
                    </span>{" "}
                    <NatureBadge nature="estimation" confiance={e.confiance} language={language} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <details style={{ marginTop: 10 }}>
        <summary style={{ ...muted, cursor: "pointer" }}>
          {pick(language, "Méthode de l'estimation 2025, limites et sources", "2025 estimate method, limits and sources", "منهجية تقدير 2025، وحدوده ومصادره")}
        </summary>
        <p style={{ ...muted, lineHeight: 1.5 }}>{ind.methode_2025}</p>
        <ul style={{ ...muted, lineHeight: 1.5, paddingLeft: 18 }}>
          {ind.limites.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
        <ul style={{ ...muted, lineHeight: 1.5, paddingLeft: 18 }}>
          {Object.entries(ind.sources).map(([k, s]) => (
            <li key={k}>
              <a href={s.url} target="_blank" rel="noreferrer">
                {s.titre}
              </a>
            </li>
          ))}
        </ul>
      </details>
      <div style={{ ...muted, marginTop: 8 }}>
        {pick(language, "Source", "Source", "المصدر")} : {ind.sources.ons_comptes.titre}.{" "}
        {pick(language, "Valeurs 2025 aux prix et au taux de change de 2024.", "2025 values at 2024 prices and exchange rate.", "قيم 2025 بأسعار وسعر صرف 2024.")}
      </div>
    </div>
  );
}

/* Fiabilité des preuves (consignes de collecte) : A officiel ou base de référence,
   B presse citant une source officielle ou une entreprise, C ordre de grandeur. */
const FIABILITE = {
  A: { fr: "officiel ou base de référence", en: "official or reference database", ar: "رسمي أو قاعدة بيانات مرجعية" },
  B: { fr: "presse citant une source officielle ou une entreprise", en: "press citing an official or company source", ar: "صحافة تستشهد بمصدر رسمي أو بشركة" },
  C: { fr: "ordre de grandeur", en: "order of magnitude", ar: "رتبة المقدار" },
};

function Chiffre({ c, language }) {
  const valeur =
    typeof c.valeur === "number"
      ? c.valeur.toLocaleString(intlLocale(language), { maximumFractionDigits: 2 }).replace(/\u202F/g, NBSP)
      : c.valeur;
  const f = FIABILITE[c.fiabilite];
  return (
    <li style={{ marginBottom: 4 }}>
      <strong>
        {c.annee} · {valeur} {c.unite}
      </strong>{" "}
      <span style={muted}>
        — {c.perimetre} · {pick(language, "fiabilité", "reliability", "الموثوقية")} {c.fiabilite}
        {f ? ` (${pick(language, f.fr, f.en, f.ar)})` : ""} ·{" "}
        <a href={c.source_url} target="_blank" rel="noreferrer" title={c.extrait}>
          {c.source_titre || (pick(language, "source", "source", "المصدر"))}
        </a>
      </span>
    </li>
  );
}

function FicheFiliere({ f, fr, language }) {
  const liste = (titreListe, chiffres, testid) =>
    chiffres.length ? (
      <div data-testid={testid}>
        <div style={{ ...muted, fontWeight: 600 }}>{titreListe}</div>
        <ul style={{ margin: "4px 0 0", paddingLeft: 18, fontSize: 13 }}>
          {chiffres.map((c, i) => (
            <Chiffre key={i} c={c} language={language} />
          ))}
        </ul>
      </div>
    ) : null;
  return (
    <div
      data-testid="fiche-filiere"
      style={{
        borderLeft: "3px solid var(--info, #175C77)",
        paddingLeft: 12,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <div style={titre}>
        {pick(language, "La filière en Algérie", "The sector in Algeria", "الشعبة في الجزائر")} · {f.libelle}
      </div>
      {f.synthese && <p style={{ fontSize: 13, lineHeight: 1.5, margin: 0 }}>{f.synthese}</p>}
      {/* périmètres, entreprises et écarts ne sont collectés qu'en français */}
      {!fr && (
        <div data-testid="filiere-detail-fr" style={muted}>
          {pick(language, "Details below are available in French only.", "Details below are available in French only.", "التفاصيل أدناه متوفرة بالفرنسية فقط.")}
        </div>
      )}
      {liste(pick(language, "Production", "Production", "الإنتاج"), f.production, "filiere-production")}
      {liste(pick(language, "Capacité installée", "Installed capacity", "القدرة المركَّبة"), f.capacite, "filiere-capacite")}
      {!f.production.length && !f.capacite.length && (
        <div style={muted}>
          — {pick(language, "Aucun chiffre de production ou de capacité sourcé pour 2021-2025.", "No sourced production or capacity figure for 2021-2025.", "لا يوجد رقم موثَّق المصدر للإنتاج أو القدرة للفترة 2021-2025.")}
        </div>
      )}
      {f.entreprises.length > 0 && (
        <div>
          <div style={{ ...muted, fontWeight: 600 }}>{pick(language, "Entreprises", "Companies", "الشركات")}</div>
          <ul style={{ margin: "4px 0 0", paddingLeft: 18, fontSize: 13 }}>
            {f.entreprises.map((e, i) => (
              <li key={i} style={{ marginBottom: 4 }}>
                <strong>{e.nom}</strong> <span style={muted}>({e.role})</span> — {e.chiffre}
                {e.annee ? ` (${e.annee})` : ""}{" "}
                {e.source_url && (
                  <a href={e.source_url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                    {pick(language, "source", "source", "المصدر")}
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      {f.contradictions.length > 0 && (
        <details data-testid="filiere-ecarts">
          <summary style={{ ...muted, cursor: "pointer" }}>
            {pick(language, "Écarts entre sources", "Discrepancies between sources", "الفروق بين المصادر")} ({f.contradictions.length})
          </summary>
          <ul style={{ ...muted, lineHeight: 1.5, paddingLeft: 18 }}>
            {f.contradictions.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function FicheProduit({ fiche, fr, language }) {
  if (!fiche.available) {
    return <div style={{ ...card, ...muted }}>— {fiche.message}</div>;
  }
  const serie = fiche.exportations;
  const max = Math.max(...serie.map((e) => e.valeur_usd || 0), 1);
  const tableMarches = (liste, testid) =>
    liste.length ? (
      <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }} data-testid={testid}>
        <thead>
          <tr>
            <th style={th}>{pick(language, "Pays", "Country", "البلد")}</th>
            <th style={thNum}>{pick(language, "Importations 2024", "Imports 2024", "الواردات 2024")}</th>
            <th style={thNum}>{pick(language, "Depuis 2019", "Since 2019", "منذ 2019")}</th>
            <th style={thNum}>{pick(language, "Part de l'Algérie", "Algeria's share", "حصة الجزائر")}</th>
          </tr>
        </thead>
        <tbody>
          {liste.map((m) => (
            <tr key={m.iso3} style={ligne}>
              <td style={td}>
                {nomPays(m.iso3, m.pays, pick(language, "fr", "en", "ar"))} <span style={muted}>({m.iso3})</span>
              </td>
              <td style={tdNum}>{montant(m.importations_2024_usd, fr)}</td>
              <td style={tdNum}>{signe(m.evolution_2019_2024_pct, fr)}</td>
              <td style={tdNum}>{pourcent(m.part_pays_pct, fr)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    ) : (
      <div style={muted}>— {pick(language, "Aucun marché ne passe le filtre.", "No market passes the filter.", "لا توجد سوق تستوفي معايير التصفية.")}</div>
    );
  return (
    <div style={{ ...card, display: "flex", flexDirection: "column", gap: 14 }} data-testid="fiche-produit">
      <div>
        <div style={{ fontSize: 16, fontWeight: 700 }}>
          {fiche.libelle} <span style={{ ...muted, fontWeight: 400 }}>(SH {fiche.hs6})</span>
        </div>
        <div style={muted}>
          {pick(language, "Libellé", "Label", "التسمية")} : {fiche.libelle_source}
        </div>
      </div>
      {fiche.filiere && <FicheFiliere f={fiche.filiere} fr={fr} language={language} />}
      <div>
        <div style={titre}>{pick(language, "Exportations de l'Algérie", "Algeria's exports", "صادرات الجزائر")}</div>
        <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: "4px 10px", fontSize: 13 }}>
          {serie.map((e) => (
            <React.Fragment key={e.annee}>
              <span style={muted}>{e.annee}</span>
              <span style={{ display: "flex", alignItems: "center" }}>
                <span
                  style={{
                    height: 10,
                    width: `${Math.max(2, (e.valeur_usd / max) * 100)}%`,
                    background: "var(--series-1, #3a6ea5)",
                    borderRadius: "0 4px 4px 0",
                  }}
                />
              </span>
              <span style={{ textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                {montant(e.valeur_usd, fr)}
                {e.tonnes ? <span style={muted}> · {Math.round(e.tonnes).toLocaleString(intlLocale(language))} t</span> : null}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>
      <div>
        <div style={titre}>{pick(language, "Premières destinations en 2024", "Top destinations in 2024", "أهم الوجهات في 2024")}</div>
        <div style={{ fontSize: 13 }}>
          {fiche.destinations_2024.slice(0, 10).map((d, i) => (
            <span key={d.iso3}>
              {i > 0 ? " · " : ""}
              {nomPays(d.iso3, d.pays, pick(language, "fr", "en", "ar"))} {montant(d.valeur_usd, fr)}
            </span>
          ))}
        </div>
      </div>
      <div>
        <div style={titre}>{pick(language, "Marchés où l'Algérie est absente ou marginale — monde", "Markets where Algeria is absent or marginal — world", "الأسواق التي تغيب عنها الجزائر أو يكون حضورها فيها هامشيًا — العالم")}</div>
        {tableMarches(fiche.marches_absents.monde, "absents-monde")}
      </div>
      <div>
        <div style={titre}>{pick(language, "Marchés africains (ZLECAf) où l'Algérie est absente ou marginale", "African (AfCFTA) markets where Algeria is absent or marginal", "الأسواق الأفريقية (زليكاف) التي تغيب عنها الجزائر أو يكون حضورها فيها هامشيًا")}</div>
        {tableMarches(fiche.marches_absents.afrique, "absents-afrique")}
      </div>
      <div style={{ ...muted, lineHeight: 1.5 }}>
        {fiche.marches_absents.critere.note}{" "}
        {pick(language, "Seuils", "Thresholds", "العتبات")} : {montant(fiche.marches_absents.critere.importations_2024_min_usd, fr)},{" "}
        {pourcent(fiche.marches_absents.critere.part_pays_max_pct, fr)}.
      </div>
      <div style={{ ...muted, lineHeight: 1.5 }}>
        {pick(language, "Source", "Source", "المصدر")} : {fiche.source}. {fiche.limites.join(" ")}
      </div>
    </div>
  );
}

export default function NationalIndustryView({ fr, language = fr ? "fr" : "en" }) {
  const lang = language === "en" ? "en" : "fr";
  const [ind, setInd] = useState(null);
  const [exp, setExp] = useState(null);
  const [region, setRegion] = useState("monde");
  const [horsHydro, setHorsHydro] = useState(true);
  const [hs6, setHs6] = useState("");
  const [fiche, setFiche] = useState(null);
  const [erreur, setErreur] = useState(null);
  // Module Opportunités réservé aux abonnements payants (audit E1) : avis
  // localisé avec un lien vers les formules, au lieu de « Données indisponibles ».
  const signalerErreur = (e) => {
    const notice = reportsNoticeText(e, language);
    setErreur(notice ? <SubscriptionNotice text={notice} language={language} /> : pick(language, "Données indisponibles.", "Data unavailable.", "البيانات غير متاحة."));
  };

  useEffect(() => {
    axios
      .get(`${API}/industrie-nationale/DZA?lang=${lang}`)
      .then((r) => setInd(r.data))
      .catch(signalerErreur);
  }, [lang, fr, language]);

  useEffect(() => {
    axios
      .get(
        `${API}/industrie-nationale/DZA/exportations?lang=${lang}&region=${region}&limite=25&hors_hydrocarbures=${horsHydro}`
      )
      .then((r) => setExp(r.data))
      .catch(signalerErreur);
  }, [lang, region, horsHydro, fr, language]);

  const ouvrir = useCallback(
    (code) => {
      const c = String(code || "").replace(/\D/g, "").slice(0, 6);
      if (c.length !== 6) return;
      setHs6(c);
      axios
        .get(`${API}/industrie-nationale/DZA/exportations/${c}?lang=${lang}`)
        .then((r) => setFiche(r.data))
        .catch(signalerErreur);
    },
    [lang, fr, language]
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={muted}>
        {pick(language, "Ce que l'Algérie produit et exporte, et où la demande l'attend : pour les exportateurs algériens et les acheteurs africains.", "What Algeria produces and exports, and where demand awaits: for Algerian exporters and African buyers.", "ما تنتجه الجزائر وتصدّره، وأين ينتظرها الطلب: للمصدِّرين الجزائريين والمشترين الأفارقة.")}
      </div>
      {erreur && <div style={{ ...card, color: "#c8102e" }}>{erreur}</div>}
      {ind?.available && <IndustrieBloc ind={ind} fr={fr} language={language} />}

      <div style={card} data-testid="dza-exportations">
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", marginBottom: 10 }}>
          <div style={{ ...titre, marginBottom: 0 }}>{pick(language, "Exportations par produit en 2024", "Exports by product in 2024", "الصادرات حسب المنتج في 2024")}</div>
          {["monde", "afrique"].map((r) => (
            <button
              key={r}
              data-testid={`region-${r}`}
              onClick={() => setRegion(r)}
              className={`afcfta-btn ${region === r ? "afcfta-btn-primary" : "afcfta-btn-secondary"}`}
              style={{ padding: "4px 12px", borderRadius: 8, fontSize: 12 }}
            >
              {r === "monde" ? (pick(language, "Monde", "World", "العالم")) : pick(language, "Afrique", "Africa", "أفريقيا")}
            </button>
          ))}
          <label
            style={{ ...muted, display: "flex", alignItems: "center", gap: 6, cursor: "pointer", whiteSpace: "nowrap" }}
          >
            <input
              type="checkbox"
              checked={horsHydro}
              onChange={(e) => setHorsHydro(e.target.checked)}
              data-testid="hors-hydrocarbures"
            />
            {pick(language, "Hors hydrocarbures (chapitre 27)", "Excluding hydrocarbons (chapter 27)", "دون المحروقات (الفصل 27)")}
          </label>
          <span style={{ flex: 1 }} />
          <input
            value={hs6}
            onChange={(e) => setHs6(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ouvrir(hs6)}
            placeholder={pick(language, "Code SH6", "HS6 code", "رمز SH6")}
            data-testid="dza-hs6"
            style={{ padding: "6px 10px", borderRadius: 8, width: 110 }}
          />
          <button
            onClick={() => ouvrir(hs6)}
            className="afcfta-btn afcfta-btn-secondary"
            style={{ padding: "4px 12px", borderRadius: 8, fontSize: 12 }}
          >
            {pick(language, "Ouvrir", "Open", "فتح")}
          </button>
          <button
            onClick={() => ouvrir("121292")}
            data-testid="raccourci-caroube"
            className="afcfta-btn afcfta-btn-secondary"
            style={{ padding: "4px 12px", borderRadius: 8, fontSize: 12 }}
          >
            {pick(language, "Exemple agricole : caroube", "Farm example: carob", "مثال زراعي: الخرّوب")}
          </button>
        </div>
        {exp?.available && (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={{ ...th, width: "44%" }}>{pick(language, "Produit", "Product", "المنتج")}</th>
                  <th style={thNum}>{pick(language, "Exportations", "Exports", "الصادرات")}</th>
                  <th style={thNum}>{pick(language, "vers l'Afrique", "to Africa", "نحو أفريقيا")}</th>
                  <th style={thNum}>{pick(language, "Demande mondiale", "World demand", "الطلب العالمي")}</th>
                  <th style={thNum}>{pick(language, "Part de l'Algérie", "Algeria's share", "حصة الجزائر")}</th>
                </tr>
              </thead>
              <tbody>
                {exp.produits.map((p) => (
                  <tr
                    key={p.hs6}
                    style={{ ...ligne, cursor: "pointer" }}
                    onClick={() => ouvrir(p.hs6)}
                    data-testid={`produit-${p.hs6}`}
                  >
                    <td style={td}>
                      {p.libelle} <span style={muted}>({p.hs6})</span>
                      {p.fiche_filiere && (
                        <span
                          style={{ ...muted, marginLeft: 6, fontWeight: 600, color: "var(--info, #175C77)" }}
                          title={pick(language, "Fiche filière : production, capacités, entreprises", "Sector sheet: production, capacity, companies", "بطاقة الشعبة: الإنتاج، والقدرات، والشركات")}
                        >
                          {pick(language, "· fiche filière", "· sector sheet", "· بطاقة الشعبة")}
                        </span>
                      )}
                    </td>
                    <td style={tdNum}>{montant(p.exportations_2024_usd, fr)}</td>
                    <td style={tdNum}>{pourcent(p.part_afrique_2024_pct, fr)}</td>
                    <td style={tdNum}>{montant(p.demande_monde_2024_usd, fr)}</td>
                    <td style={tdNum}>{pourcent(p.part_monde_2024_pct, fr)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ ...muted, marginTop: 8, lineHeight: 1.5 }}>
              {pick(language, "Source", "Source", "المصدر")} : {exp.source}. {exp.limites.join(" ")}
            </div>
          </div>
        )}
      </div>

      {fiche && <FicheProduit fiche={fiche} fr={fr} language={language} />}
    </div>
  );
}
