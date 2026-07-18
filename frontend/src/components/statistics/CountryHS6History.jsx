/**
 * CountryHS6History — Recherche commerce par pays + HS6, sur N dernières années.
 * Source : OEC / BACI (HS Rev. 2017).
 */
import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Line, ComposedChart,
} from 'recharts';
import { Search, Loader2, TrendingUp, TrendingDown, Minus, FileDown, Moon } from 'lucide-react';
import { buildTradeReportPdf, tradeReportFilename } from '../../utils/tradeReportPdf';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const fmtUSD = (v) => {
  if (v == null || isNaN(v)) return '—';
  const abs = Math.abs(v);
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};

// Volume BACI (poids net, tonnes métriques) — affiché à côté de la valeur USD.
const fmtTonnes = (v) => {
  if (v == null || isNaN(v) || v <= 0) return '—';
  if (v >= 1e6) return `${(v / 1e6).toFixed(2)}M t`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K t`;
  return `${v.toFixed(v < 10 ? 1 : 0)} t`;
};

const MATCH_LEVEL_LABEL = {
  fr: { hs6: 'SH6 exact', hs4: 'Aggrégat SH4', hs2: 'Chapitre SH2', none: 'Aucune correspondance' },
  en: { hs6: 'Exact HS6', hs4: 'HS4 aggregate', hs2: 'HS2 chapter', none: 'No match' },
};

const LEVEL_LEN = { hs2: 2, hs4: 4, hs6: 6 };
const LEVEL_EXAMPLE = { hs2: '27', hs4: '2710', hs6: '270900' };

const TXT = {
  fr: {
    title: 'Commerce par Pays & HS6 — 5 dernières années',
    subtitle: 'Source : OEC / BACI (HS Rev. 2017). Données officielles douanières (USD)',
    country: 'Pays',
    hsCode: 'Code SH6',
    hsPlaceholder: 'ex: 271019, 870321, 760900',
    years: 'Années',
    fetch: 'Rechercher',
    loading: 'Chargement des données OEC…',
    selectCountry: 'Choisir un pays',
    year: 'Année',
    exports: 'Exports',
    imports: 'Imports',
    balance: 'Balance',
    totalExports: 'Exports cumulés',
    totalImports: 'Imports cumulés',
    cumulativeBalance: 'Balance cumulée',
    avgGrowth: 'Croissance moy.',
    qtyExports: 'Vol. exports',
    qtyImports: 'Vol. imports',
    qtyNote: 'Volumes : poids net (tonnes) — source BACI',
    noData: 'Aucune donnée OEC pour ce code dans ce pays.',
    error: 'Erreur de récupération',
    inputError: 'Saisir un code SH valide puis cliquer Rechercher.',
    hs4Label: 'SH4',
    hs6Label: 'SH6',
    productsFound: 'sous-positions trouvées',
    tabHs2: 'Chapitre (SH2)', tabHs4: 'Position (SH4)', tabHs6: 'Sous-position (SH6)', tabLabel: 'Intitulé',
    labelTitle: 'Intitulé du code SH sélectionné', chapterLbl: 'Chapitre', headingLbl: 'Position', subheadingLbl: 'Sous-position',
    categoryLbl: 'Catégorie', sensitivityLbl: 'Sensibilité', noLabel: 'Aucun intitulé trouvé pour ce code.', enOnly: 'EN',
    hintByLevel: { hs2: '2 chiffres (ex: 27)', hs4: '4 chiffres (ex: 2710)', hs6: '6 chiffres (ex: 270900)' },
    selectCodePrompt: 'Sélectionnez un code dans un onglet SH2 / SH4 / SH6 pour voir son intitulé.',
  },
  en: {
    title: 'Trade by Country & HS6 — Last 5 years',
    subtitle: 'Source: OEC / BACI (HS Rev. 2017). Official customs data (USD)',
    country: 'Country',
    hsCode: 'HS6 Code',
    hsPlaceholder: 'e.g. 271019, 870321, 760900',
    years: 'Years',
    fetch: 'Search',
    loading: 'Loading OEC data…',
    selectCountry: 'Choose a country',
    year: 'Year',
    exports: 'Exports',
    imports: 'Imports',
    balance: 'Balance',
    totalExports: 'Total exports',
    totalImports: 'Total imports',
    cumulativeBalance: 'Cumulative balance',
    avgGrowth: 'Avg growth',
    qtyExports: 'Export vol.',
    qtyImports: 'Import vol.',
    qtyNote: 'Volumes: net weight (metric tons) — BACI source',
    noData: 'No OEC data for this HS in this country.',
    error: 'Fetch error',
    inputError: 'Enter a valid HS code then click Search.',
    hs4Label: 'HS4',
    hs6Label: 'HS6',
    productsFound: 'sub-headings found',
    tabHs2: 'Chapter (HS2)', tabHs4: 'Heading (HS4)', tabHs6: 'Sub-heading (HS6)', tabLabel: 'Title',
    labelTitle: 'Title of the selected HS code', chapterLbl: 'Chapter', headingLbl: 'Heading', subheadingLbl: 'Sub-heading',
    categoryLbl: 'Category', sensitivityLbl: 'Sensitivity', noLabel: 'No title found for this code.', enOnly: 'EN',
    hintByLevel: { hs2: '2 digits (e.g. 27)', hs4: '4 digits (e.g. 2710)', hs6: '6 digits (e.g. 270900)' },
    selectCodePrompt: 'Select a code in an HS2 / HS4 / HS6 tab to view its title.',
  },
};

export default function CountryHS6History({ language = 'fr' }) {
  const t = TXT[language] || TXT.fr;
  const [countries, setCountries] = useState([]);
  const [iso3, setIso3] = useState('DZA');
  const [searchLevel, setSearchLevel] = useState('hs6');     // 'hs2' | 'hs4' | 'hs6'
  const [view, setView] = useState('search');                // 'search' | 'label'
  const [hsCode, setHsCode] = useState('270900');
  const [years, setYears] = useState(5);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [labelData, setLabelData] = useState(null);
  const [labelLoading, setLabelLoading] = useState(false);
  const [exportingTheme, setExportingTheme] = useState(null); // null | 'light' | 'dark'

  useEffect(() => {
    let cancelled = false;
    fetch(`${API}/countries`)
      .then((r) => (r.ok ? r.json() : []))
      .then((rows) => {
        if (cancelled) return;
        const list = (Array.isArray(rows) ? rows : [])
          .filter((c) => c.iso3_code || c.iso3)
          .map((c) => ({
            iso3: c.iso3_code || c.iso3,
            name: c.name || c.country_name || c.iso3_code,
          }))
          .sort((a, b) => a.name.localeCompare(b.name));
        setCountries(list);
      })
      .catch(() => setCountries([]));
    return () => { cancelled = true; };
  }, []);

  const runQuery = async (lvl = searchLevel, codeStr = hsCode) => {
    const need = LEVEL_LEN[lvl];
    const cleanHs = String(codeStr).replace(/\D/g, '').slice(0, need);
    if (cleanHs.length !== need) {
      setError(t.inputError);
      return;
    }
    setError('');
    setLoading(true);
    setData(null);
    try {
      const r = await axios.get(`${API}/oec/country/${iso3}/hs6/${cleanHs}/history`, {
        params: { years, level: lvl },
      });
      setData(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || t.error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLabel = async (lvl = searchLevel, codeStr = hsCode) => {
    const need = LEVEL_LEN[lvl];
    const cleanHs = String(codeStr).replace(/\D/g, '').slice(0, need);
    if (cleanHs.length !== need) { setLabelData(null); return; }
    setLabelLoading(true);
    try {
      const r = await axios.get(`${API}/hs-codes/label/${cleanHs}`);
      setLabelData(r.data);
    } catch {
      setLabelData(null);
    } finally {
      setLabelLoading(false);
    }
  };

  // Switch search level: truncate/seed the code and run the query for that level
  const switchLevel = (lvl) => {
    const need = LEVEL_LEN[lvl];
    let next = String(hsCode).replace(/\D/g, '').slice(0, need);
    if (next.length < need) next = LEVEL_EXAMPLE[lvl];
    setHsCode(next);
    setSearchLevel(lvl);
    setView('search');
    runQuery(lvl, next);
  };

  const openLabelTab = () => {
    setView('label');
    fetchLabel();
  };

  // Handoff vers le module Opportunités : pays + code SH courant, repris par
  // OpportunityReportTab (S3 besoin national, signal d'import OEC activé).
  // Les deux modules partagent désormais le même canal OEC (cache commun).
  const analyzeInOpportunities = () => {
    const need = LEVEL_LEN[searchLevel];
    const cleanHs = String(hsCode).replace(/\D/g, '').slice(0, need);
    if (!cleanHs) return;
    try {
      sessionStorage.setItem(
        'zlecaf_opportunites_handoff',
        JSON.stringify({ country: iso3, hsCode: cleanHs, k: Date.now() }),
      );
    } catch { /* stockage indisponible : la navigation reste utile */ }
    window.dispatchEvent(new CustomEvent('zlecaf:goto-tab', { detail: { tab: 'reports' } }));
  };

  // Rapport PDF natif (voir utils/tradeReportPdf.js) : tracé vectoriel, deux
  // variantes thématiques reprenant la palette réelle de l'appli (theme.css /
  // theme-light.css) — claire pour l'impression, sombre pour l'écran.
  const exportToPDF = async (themeName) => {
    if (!data || !data.chart_rows || data.chart_rows.length === 0) return;
    setExportingTheme(themeName);
    try {
      const doc = buildTradeReportPdf({
        data,
        totals,
        language,
        levelLen: LEVEL_LEN[searchLevel],
        matchLevelLabel: (MATCH_LEVEL_LABEL[language] || MATCH_LEVEL_LABEL.fr)[data.match_level] || '',
        fmtUSD,
        fmtTonnes,
        theme: themeName,
      });
      doc.save(`${tradeReportFilename(data)}_${themeName}.pdf`);
    } catch (err) {
      console.error('PDF export failed:', err);
    } finally {
      setExportingTheme(null);
    }
  };

  const submit = () => (view === 'label' ? fetchLabel() : runQuery());

  // Auto-run on mount (deferred to avoid synchronous setState in effect)
  useEffect(() => {
    const id = setTimeout(() => runQuery(), 0);
    return () => clearTimeout(id);
  }, []);

  const totals = useMemo(() => {
    if (!data?.chart_rows) return null;
    const exp = data.chart_rows.reduce((s, r) => s + (r.exports || 0), 0);
    const imp = data.chart_rows.reduce((s, r) => s + (r.imports || 0), 0);
    const first = data.chart_rows[0]?.exports || 0;
    const last = data.chart_rows[data.chart_rows.length - 1]?.exports || 0;
    const cagr =
      first > 0 && last > 0
        ? (Math.pow(last / first, 1 / Math.max(1, data.chart_rows.length - 1)) - 1) * 100
        : null;
    return { exports: exp, imports: imp, balance: exp - imp, cagr };
  }, [data]);

  return (
    <div className="stats-chart-card" data-testid="country-hs6-history">
      <div className="stats-chart-header gold">
        <div className="stats-chart-title gold">
          <Search style={{ width: 18, height: 18 }} />
          {t.title}
        </div>
        <div className="stats-chart-subtitle">{t.subtitle}</div>
      </div>

      {/* Onglets niveau SH (SH2 / SH4 / SH6) + Intitulé */}
      <div style={{ display: 'flex', gap: 6, padding: '12px 16px 0', flexWrap: 'wrap' }} data-testid="hs-level-tabs">
        {[['hs2', t.tabHs2], ['hs4', t.tabHs4], ['hs6', t.tabHs6]].map(([lvl, lbl]) => (
          <button
            key={lvl}
            data-testid={`hs-tab-${lvl}`}
            onClick={() => switchLevel(lvl)}
            style={tabStyle(view === 'search' && searchLevel === lvl)}
          >
            {lbl}
          </button>
        ))}
        <button data-testid="hs-tab-label" onClick={openLabelTab} style={tabStyle(view === 'label')}>
          {t.tabLabel}
        </button>
      </div>

      <div style={{ padding: '14px 16px 6px', display: 'grid', gridTemplateColumns: '1.5fr 1.2fr 0.8fr auto', gap: 10, alignItems: 'end' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 11, color: 'rgba(142,155,174,0.85)', fontWeight: 700, letterSpacing: 0.4 }}>{t.country}</span>
          <select
            data-testid="hs6-country-select"
            value={iso3}
            onChange={(e) => setIso3(e.target.value)}
            style={{ padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(212,175,55,0.22)', color: 'var(--text)', fontSize: 13, fontWeight: 600 }}
          >
            {countries.length === 0 && <option value={iso3}>{iso3}</option>}
            {countries.map((c) => (
              <option key={c.iso3} value={c.iso3}>
                {c.name} ({c.iso3})
              </option>
            ))}
          </select>
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 11, color: 'rgba(142,155,174,0.85)', fontWeight: 700, letterSpacing: 0.4 }}>
            {`Code SH${LEVEL_LEN[searchLevel]}`}
          </span>
          <input
            data-testid="hs6-code-input"
            value={hsCode}
            onChange={(e) => setHsCode(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            placeholder={t.hintByLevel[searchLevel]}
            inputMode="numeric"
            maxLength={LEVEL_LEN[searchLevel]}
            style={{ padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(212,175,55,0.22)', color: 'var(--text)', fontSize: 13, fontWeight: 600, letterSpacing: 1.2 }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 11, color: 'rgba(142,155,174,0.85)', fontWeight: 700, letterSpacing: 0.4 }}>{t.years}</span>
          <select
            data-testid="hs6-years-select"
            value={years}
            onChange={(e) => setYears(Number(e.target.value))}
            style={{ padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(212,175,55,0.22)', color: 'var(--text)', fontSize: 13, fontWeight: 600 }}
          >
            {[3, 5, 7, 10].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
        <button
          data-testid="hs6-search-btn"
          onClick={submit}
          disabled={loading || labelLoading}
          style={{
            padding: '8px 16px',
            borderRadius: 8,
            border: '1px solid rgba(212,175,55,0.45)',
            background: 'linear-gradient(180deg, rgba(212,175,55,0.85) 0%, rgba(180,140,40,0.9) 100%)',
            color: '#0b0f1a',
            fontWeight: 700,
            fontSize: 13,
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          {(loading || labelLoading) ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          {t.fetch}
        </button>
      </div>

      {error && (
        <div style={{ padding: '10px 16px', color: '#fca5a5', fontSize: 13 }} data-testid="hs6-error">
          {error}
        </div>
      )}

      {loading && (
        <div style={{ padding: 30, textAlign: 'center', color: 'rgba(142,155,174,0.85)' }}>
          <Loader2 className="animate-spin" style={{ display: 'inline', marginRight: 8 }} />
          {t.loading}
        </div>
      )}

      {/* ─── Onglet INTITULÉ ─── */}
      {view === 'label' && (
        <div style={{ padding: '6px 16px 16px' }} data-testid="hs-label-panel">
          {labelLoading ? (
            <div style={{ padding: 24, textAlign: 'center', color: 'rgba(142,155,174,0.85)' }}>
              <Loader2 className="animate-spin" style={{ display: 'inline', marginRight: 8 }} />
              {t.loading}
            </div>
          ) : labelData ? (
            <div style={{ padding: '14px 16px', borderRadius: 10, background: 'rgba(212,175,55,0.07)', border: '1px solid rgba(212,175,55,0.22)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <span style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.8, background: 'rgba(212,175,55,0.2)', color: 'rgba(212,175,55,0.95)', borderRadius: 6, padding: '4px 9px' }}>
                  SH{LEVEL_LEN[labelData.level]} · {labelData.code}
                </span>
                <span style={{ fontSize: 11, color: 'rgba(142,155,174,0.85)', fontWeight: 600 }}>{t.labelTitle}</span>
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', lineHeight: 1.4, marginBottom: 4 }} data-testid="hs-label-fr">
                {labelData.label_fr || labelData.label_en || '—'}
                {labelData.label_lang === 'en' && (
                  <span style={{ marginLeft: 8, fontSize: 10, fontWeight: 700, color: 'rgba(142,155,174,0.7)', border: '1px solid rgba(142,155,174,0.35)', borderRadius: 4, padding: '1px 5px' }}>{t.enOnly}</span>
                )}
              </div>
              {labelData.label_en && labelData.label_lang === 'both' && labelData.label_en !== labelData.label_fr && (
                <div style={{ fontSize: 12.5, color: 'rgba(142,155,174,0.9)', fontStyle: 'italic', marginBottom: 8 }}>
                  {labelData.label_en}
                </div>
              )}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 16px', paddingTop: 10, borderTop: '1px solid rgba(212,175,55,0.15)', marginTop: 8 }}>
                <LabelMeta k={t.chapterLbl} v={`${labelData.chapter} — ${language === 'fr' ? labelData.chapter_name_fr : labelData.chapter_name_en}`} />
                {labelData.heading && <LabelMeta k={t.headingLbl} v={`${labelData.heading}${labelData.heading_name_en ? ' — ' + labelData.heading_name_en : ''}`} />}
                {labelData.category && <LabelMeta k={t.categoryLbl} v={labelData.category} />}
                {labelData.sensitivity && <LabelMeta k={t.sensitivityLbl} v={labelData.sensitivity} />}
              </div>
              <p className="stats-source-note" style={{ margin: '10px 0 0' }}>{labelData.source}</p>
            </div>
          ) : (
            <div style={{ padding: 24, textAlign: 'center', color: 'rgba(142,155,174,0.85)' }} data-testid="hs-label-empty">
              {t.selectCodePrompt}
            </div>
          )}
        </div>
      )}

      {view === 'search' && !loading && data && (
        <>
          {/* ─── Bannière produit HS4 / HS6 ─── */}
          {data.hs_labels && data.hs_labels.length > 0 && (
            <div style={{
              margin: '6px 16px 2px',
              padding: '10px 14px',
              borderRadius: 10,
              background: 'rgba(212,175,55,0.07)',
              border: '1px solid rgba(212,175,55,0.22)',
            }}>
              {/* Ligne HS4 */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: data.hs_labels.length > 1 ? 6 : 0 }}>
                <span style={{
                  fontSize: 10, fontWeight: 800, letterSpacing: 0.8,
                  background: 'rgba(212,175,55,0.18)', color: 'rgba(212,175,55,0.95)',
                  borderRadius: 5, padding: '2px 6px', flexShrink: 0,
                }}>
                  SH{LEVEL_LEN[data.level] || 6} {data.hs_query || data.hs4_code}
                </span>
                <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text)', lineHeight: 1.3 }}>
                  {data.hs_labels[0].label}
                </span>
                {data.match_level && (
                  <span style={{
                    marginLeft: 'auto', fontSize: 10, fontWeight: 700, letterSpacing: 0.5,
                    color: data.match_level === 'hs6' ? '#10b981' : data.match_level === 'hs4' ? '#fbbf24' : '#f43f5e',
                    background: data.match_level === 'hs6' ? 'rgba(16,185,129,0.12)' : data.match_level === 'hs4' ? 'rgba(251,191,36,0.12)' : 'rgba(244,63,94,0.12)',
                    borderRadius: 5, padding: '2px 7px', flexShrink: 0,
                  }}>
                    {(MATCH_LEVEL_LABEL[language] || MATCH_LEVEL_LABEL.fr)[data.match_level]}
                  </span>
                )}
              </div>

              {/* Sous-positions HS6 (si plusieurs) */}
              {data.hs_labels.length > 1 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px 8px', paddingTop: 4, borderTop: '1px solid rgba(212,175,55,0.12)' }}>
                  {data.hs_labels.slice(0, 12).map((item) => (
                    <span key={item.hs6_id} style={{
                      display: 'inline-flex', alignItems: 'center', gap: 5,
                      fontSize: 11, color: 'rgba(142,155,174,0.9)',
                    }}>
                      <span style={{
                        fontSize: 9.5, fontWeight: 800, letterSpacing: 0.5,
                        background: 'rgba(255,255,255,0.07)', borderRadius: 4,
                        padding: '1px 5px', color: 'rgba(212,175,55,0.75)',
                      }}>
                        {t.hs6Label} {String(item.hs6_id).slice(-6)}
                      </span>
                      {item.label}
                    </span>
                  ))}
                  {data.hs_labels.length > 12 && (
                    <span style={{ fontSize: 11, color: 'rgba(142,155,174,0.7)', fontWeight: 700 }}>
                      +{data.hs_labels.length - 12} {t.productsFound}
                    </span>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ─── Stat strip ─── */}
          {totals && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, padding: '8px 16px' }}>
              <StatBox label={t.totalExports} value={fmtUSD(totals.exports)} icon={<TrendingUp size={14} color="#10b981" />} />
              <StatBox label={t.totalImports} value={fmtUSD(totals.imports)} icon={<TrendingDown size={14} color="#f43f5e" />} />
              <StatBox label={t.cumulativeBalance} value={fmtUSD(totals.balance)} icon={totals.balance >= 0 ? <TrendingUp size={14} color="#10b981" /> : <TrendingDown size={14} color="#f43f5e" />} accent={totals.balance >= 0 ? '#10b981' : '#f43f5e'} />
              <StatBox label={t.avgGrowth} value={totals.cagr != null ? `${totals.cagr.toFixed(1)}%` : '—'} icon={totals.cagr != null && totals.cagr >= 0 ? <TrendingUp size={14} color="#10b981" /> : <Minus size={14} />} />
            </div>
          )}

          {/* ─── Chart ─── */}
          {data.chart_rows && data.chart_rows.length > 0 ? (
            <div style={{ padding: '8px 8px 4px' }}>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={data.chart_rows} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(142,155,174,0.15)" />
                  <XAxis dataKey="year" tick={{ fontSize: 12, fill: 'rgba(142,155,174,0.85)', fontWeight: 700 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: 'rgba(142,155,174,0.85)' }} axisLine={false} tickLine={false} tickFormatter={(v) => fmtUSD(v)} width={62} />
                  <Tooltip
                    contentStyle={{ background: '#1a2332', border: '1px solid rgba(212,137,26,0.4)', borderRadius: 8, color: '#e2e8f0' }}
                    formatter={(value, name, entry) => {
                      const row = entry?.payload || {};
                      if (name === t.exports && row.exports_quantity > 0) {
                        return [`${fmtUSD(value)} · ${fmtTonnes(row.exports_quantity)}`, name];
                      }
                      if (name === t.imports && row.imports_quantity > 0) {
                        return [`${fmtUSD(value)} · ${fmtTonnes(row.imports_quantity)}`, name];
                      }
                      return [fmtUSD(value), name];
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="exports" name={t.exports} fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="imports" name={t.imports} fill="#f43f5e" radius={[4, 4, 0, 0]} />
                  <Line type="monotone" dataKey="balance" name={t.balance} stroke="#fbbf24" strokeWidth={2.5} dot={{ r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ padding: 24, textAlign: 'center', color: 'rgba(142,155,174,0.85)' }} data-testid="hs6-empty">
              {t.noData}
            </div>
          )}

          {/* ─── Table ─── */}
          {data.chart_rows && data.chart_rows.length > 0 && (
            <div style={{ padding: '4px 16px 16px', overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(212,175,55,0.25)' }}>
                    <th style={{ textAlign: 'left', padding: '6px 4px', color: 'rgba(212,175,55,0.9)', fontWeight: 700 }}>{t.year}</th>
                    <th style={{ textAlign: 'right', padding: '6px 4px', color: '#10b981', fontWeight: 700 }}>{t.exports}</th>
                    <th style={{ textAlign: 'right', padding: '6px 4px', color: '#34d399', fontWeight: 600, fontSize: 12 }}>{t.qtyExports}</th>
                    <th style={{ textAlign: 'right', padding: '6px 4px', color: '#f43f5e', fontWeight: 700 }}>{t.imports}</th>
                    <th style={{ textAlign: 'right', padding: '6px 4px', color: '#fb7185', fontWeight: 600, fontSize: 12 }}>{t.qtyImports}</th>
                    <th style={{ textAlign: 'right', padding: '6px 4px', color: '#fbbf24', fontWeight: 700 }}>{t.balance}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.chart_rows.map((row) => (
                    <tr key={row.year} style={{ borderBottom: '1px solid rgba(142,155,174,0.10)' }}>
                      <td style={{ padding: '6px 4px', fontWeight: 700 }}>{row.year}</td>
                      <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace' }}>{fmtUSD(row.exports)}</td>
                      <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace', fontSize: 12, color: 'rgba(52,211,153,0.85)' }} data-testid={`qty-exp-${row.year}`}>{fmtTonnes(row.exports_quantity)}</td>
                      <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace' }}>{fmtUSD(row.imports)}</td>
                      <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace', fontSize: 12, color: 'rgba(251,113,133,0.85)' }} data-testid={`qty-imp-${row.year}`}>{fmtTonnes(row.imports_quantity)}</td>
                      <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace', color: row.balance >= 0 ? '#10b981' : '#f43f5e' }}>
                        {fmtUSD(row.balance)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="stats-source-note" style={{ margin: '6px 0 0' }}>{t.qtyNote}</p>
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', padding: '0 16px 14px' }}>
            <p className="stats-source-note" style={{ margin: 0, flex: '1 1 auto' }}>
              {data.source} · {data.country_name} · HS {data.hs_code} · {data.currency}
            </p>
            <button
              data-testid="hs6-export-pdf-light"
              onClick={() => exportToPDF('light')}
              disabled={exportingTheme != null}
              title={language === 'fr' ? 'Fiche PDF claire — optimisée impression' : 'Light PDF sheet — optimized for printing'}
              style={{
                padding: '7px 14px',
                borderRadius: 8,
                border: '1px solid rgba(212,175,55,0.45)',
                background: 'rgba(212,175,55,0.12)',
                color: 'rgba(212,175,55,0.95)',
                fontWeight: 700,
                fontSize: 12.5,
                cursor: exportingTheme != null ? 'not-allowed' : 'pointer',
                flexShrink: 0,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                opacity: exportingTheme != null ? 0.6 : 1,
              }}
            >
              {exportingTheme === 'light' ? <Loader2 size={14} className="animate-spin" /> : <FileDown size={14} />}
              {language === 'fr' ? 'PDF · Clair' : 'PDF · Light'}
            </button>
            <button
              data-testid="hs6-export-pdf-dark"
              onClick={() => exportToPDF('dark')}
              disabled={exportingTheme != null}
              title={language === 'fr' ? 'Fiche PDF sombre — aligné sur le rendu à l’écran' : 'Dark PDF sheet — matches the on-screen look'}
              style={{
                padding: '7px 14px',
                borderRadius: 8,
                border: '1px solid rgba(212,175,55,0.45)',
                background: 'rgba(212,175,55,0.12)',
                color: 'rgba(212,175,55,0.95)',
                fontWeight: 700,
                fontSize: 12.5,
                cursor: exportingTheme != null ? 'not-allowed' : 'pointer',
                flexShrink: 0,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                opacity: exportingTheme != null ? 0.6 : 1,
              }}
            >
              {exportingTheme === 'dark' ? <Loader2 size={14} className="animate-spin" /> : <Moon size={14} />}
              {language === 'fr' ? 'PDF · Sombre' : 'PDF · Dark'}
            </button>
            <button
              data-testid="hs6-to-opportunities"
              onClick={analyzeInOpportunities}
              style={{
                padding: '7px 14px',
                borderRadius: 8,
                border: '1px solid rgba(212,175,55,0.45)',
                background: 'rgba(212,175,55,0.12)',
                color: 'rgba(212,175,55,0.95)',
                fontWeight: 700,
                fontSize: 12.5,
                cursor: 'pointer',
                flexShrink: 0,
              }}
            >
              {language === 'fr' ? 'Analyser dans Opportunités ▸' : 'Analyze in Opportunities ▸'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function tabStyle(active) {
  return {
    padding: '7px 14px',
    borderRadius: '8px 8px 0 0',
    border: '1px solid rgba(212,175,55,0.28)',
    borderBottom: active ? '2px solid rgba(212,175,55,0.95)' : '1px solid rgba(212,175,55,0.12)',
    background: active ? 'rgba(212,175,55,0.16)' : 'rgba(255,255,255,0.03)',
    color: active ? 'rgba(212,175,55,0.98)' : 'rgba(142,155,174,0.9)',
    fontWeight: 700,
    fontSize: 12.5,
    letterSpacing: 0.3,
    cursor: 'pointer',
    transition: 'background-color 0.2s, color 0.2s',
  };
}

function LabelMeta({ k, v }) {
  return (
    <span style={{ fontSize: 12, color: 'rgba(142,155,174,0.95)' }}>
      <span style={{ fontWeight: 800, color: 'rgba(212,175,55,0.8)', textTransform: 'uppercase', fontSize: 10, letterSpacing: 0.5, marginRight: 5 }}>{k}</span>
      {v}
    </span>
  );
}

function StatBox({ label, value, icon, accent }) {
  return (
    <div
      style={{
        padding: 10,
        borderRadius: 10,
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(212,175,55,0.18)',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'rgba(142,155,174,0.85)', fontSize: 10.5, fontWeight: 700, letterSpacing: 0.4, textTransform: 'uppercase' }}>
        {icon}
        {label}
      </div>
      <div style={{ fontSize: 17, fontWeight: 800, color: accent || 'var(--text)', fontFamily: 'monospace' }}>{value}</div>
    </div>
  );
}
