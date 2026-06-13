import React, { useState, useEffect, useRef, useCallback } from "react";
import { Search, X, Calculator, Globe2, Hash } from "lucide-react";

const TAB_LABELS = {
  fr: {
    dashboard: "Tableau de bord", calculator: "Calculateur", stats: "Statistiques",
    opps: "Opportunités", production: "Production", logistics: "Logistique",
    banking: "Banque", tools: "Outils", roo: "R. d'Origine", profiles: "Profils",
  },
  en: {
    dashboard: "Dashboard", calculator: "Calculator", stats: "Statistics",
    opps: "Opportunities", production: "Production", logistics: "Logistics",
    banking: "Banking", tools: "Tools", roo: "Rules of Origin", profiles: "Profiles",
  },
};

const HS_SUGGESTIONS = [
  { code: "0201", label_fr: "Viandes bovines, fraîches ou réfrigérées", label_en: "Bovine meat, fresh or chilled" },
  { code: "0301", label_fr: "Poissons vivants", label_en: "Live fish" },
  { code: "1001", label_fr: "Froment (blé) et méteil", label_en: "Wheat and meslin" },
  { code: "1006", label_fr: "Riz", label_en: "Rice" },
  { code: "1701", label_fr: "Sucres de canne ou de betterave", label_en: "Cane or beet sugar" },
  { code: "2701", label_fr: "Houilles; briquettes, boulets de houille", label_en: "Coal; briquettes, ovoids" },
  { code: "2709", label_fr: "Huiles brutes de pétrole", label_en: "Petroleum oils, crude" },
  { code: "3004", label_fr: "Médicaments pour usage médical", label_en: "Medicaments for therapeutic use" },
  { code: "7601", label_fr: "Aluminium sous formes brutes", label_en: "Unwrought aluminium" },
  { code: "8703", label_fr: "Voitures de tourisme", label_en: "Motor cars and other vehicles" },
  { code: "8517", label_fr: "Téléphones, smartphones", label_en: "Telephones, smartphones" },
  { code: "6101", label_fr: "Manteaux, vêtements, tricotés", label_en: "Overcoats, knitted garments" },
  { code: "6110", label_fr: "Jerseys, pulls, gilets tricotés", label_en: "Jerseys, pullovers, knitted" },
  { code: "0901", label_fr: "Café, même torréfié", label_en: "Coffee, roasted or not" },
  { code: "1801", label_fr: "Cacao en fèves", label_en: "Cocoa beans" },
];

export default function GlobalSearch({ language = "fr", countries = [], onTabChange }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const inputRef = useRef(null);
  const wrapperRef = useRef(null);
  const isFr = language === "fr";

  const search = useCallback((q) => {
    if (!q || q.trim().length < 1) { setResults([]); return; }
    const lower = q.toLowerCase().trim();
    const out = [];

    const tabs = TAB_LABELS[language] || TAB_LABELS.fr;
    Object.entries(tabs).forEach(([id, label]) => {
      if (label.toLowerCase().includes(lower)) {
        out.push({ type: "tab", id, label, icon: "nav" });
      }
    });

    const hsMatches = HS_SUGGESTIONS.filter(
      (s) =>
        s.code.startsWith(lower) ||
        (isFr ? s.label_fr : s.label_en).toLowerCase().includes(lower)
    ).slice(0, 4);
    hsMatches.forEach((s) => {
      out.push({
        type: "hs",
        id: s.code,
        label: `SH ${s.code} — ${isFr ? s.label_fr : s.label_en}`,
        icon: "hs",
      });
    });

    const countryMatches = countries
      .filter(
        (c) =>
          (c.name || "").toLowerCase().includes(lower) ||
          (c.iso3 || "").toLowerCase().includes(lower) ||
          (c.name_fr || "").toLowerCase().includes(lower)
      )
      .slice(0, 5);
    countryMatches.forEach((c) => {
      out.push({
        type: "country",
        id: c.iso3,
        label: c.name_fr || c.name || c.iso3,
        iso3: c.iso3,
        icon: "country",
      });
    });

    setResults(out.slice(0, 8));
  }, [language, countries, isFr]);

  useEffect(() => { search(query); }, [query, search]);

  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
        setTimeout(() => inputRef.current?.focus(), 50);
      }
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleSelect = (item) => {
    setOpen(false);
    setQuery("");
    setResults([]);
    if (item.type === "tab") {
      onTabChange && onTabChange("tab", item.id);
    } else if (item.type === "hs" || item.type === "country") {
      onTabChange && onTabChange("tab", "calculator");
    }
  };

  const IconComp = ({ type }) => {
    if (type === "hs") return <Hash size={14} style={{ color: "var(--gold)", flexShrink: 0 }} />;
    if (type === "country") return <Globe2 size={14} style={{ color: "var(--info)", flexShrink: 0 }} />;
    return <Calculator size={14} style={{ color: "var(--terra)", flexShrink: 0 }} />;
  };

  return (
    <div ref={wrapperRef} style={{ position: "relative" }}>
      <button
        className="gs-trigger"
        onClick={() => { setOpen((o) => !o); setTimeout(() => inputRef.current?.focus(), 50); }}
        aria-label={isFr ? "Recherche globale" : "Global search"}
        title={isFr ? "Rechercher (Ctrl+K)" : "Search (Ctrl+K)"}
      >
        <Search size={15} />
        <span className="gs-trigger-text">{isFr ? "Rechercher..." : "Search..."}</span>
        <kbd className="gs-kbd">Ctrl K</kbd>
      </button>

      {open && (
        <div className="gs-dropdown">
          <div className="gs-input-wrap">
            <Search size={15} className="gs-input-icon" />
            <input
              ref={inputRef}
              className="gs-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={isFr ? "Pays, code SH, module..." : "Country, HS code, module..."}
              autoComplete="off"
              spellCheck={false}
            />
            {query && (
              <button className="gs-clear" onClick={() => { setQuery(""); inputRef.current?.focus(); }}>
                <X size={13} />
              </button>
            )}
          </div>

          {results.length > 0 && (
            <ul className="gs-results" role="listbox">
              {results.map((item, i) => (
                <li
                  key={i}
                  className="gs-result-item"
                  role="option"
                  onClick={() => handleSelect(item)}
                >
                  <IconComp type={item.type} />
                  <span className="gs-result-label">{item.label}</span>
                  {item.type === "tab" && (
                    <span className="gs-result-tag">{isFr ? "Module" : "Module"}</span>
                  )}
                  {item.type === "hs" && (
                    <span className="gs-result-tag gs-tag-hs">SH</span>
                  )}
                  {item.type === "country" && item.iso3 && (
                    <span className="gs-result-tag gs-tag-country">{item.iso3}</span>
                  )}
                </li>
              ))}
            </ul>
          )}

          {query && results.length === 0 && (
            <div className="gs-empty">
              {isFr ? `Aucun résultat pour « ${query} »` : `No results for "${query}"`}
            </div>
          )}

          {!query && (
            <div className="gs-hint">
              {isFr
                ? "Tapez un nom de pays, code SH (ex: 0201) ou nom de module"
                : "Type a country name, HS code (e.g. 0201) or module name"}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
