/**
 * Country Comparison — AfCFTA trade complementarity analysis between two countries
 * Powered by Claude AI
 */
import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import {
  Sparkles, ArrowLeftRight, Loader2, AlertCircle, Info,
  TrendingUp, TrendingDown, Scale, Zap,
} from 'lucide-react';
import { DataFreshnessIndicator } from '../ui/data-freshness-indicator';
import OpportunityPdfExport from './OpportunityPdfExport';
import { opportunityPdfFilename } from '../../utils/opportunityPdf';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const fmtMUSD = (v) => {
  if (!v || isNaN(v)) return '$0';
  if (v >= 1000) return `$${(v / 1000).toFixed(2)}B`;
  if (v >= 1) return `$${Number(v).toFixed(0)}M`;
  return `$${(v * 1000).toFixed(0)}K`;
};

const fmtPct = (v) => (v != null && !isNaN(v) ? `${Number(v).toFixed(1)}%` : '—');

const AFCFTA_COUNTRIES = [
  { iso3: 'DZA', name: 'Algeria' }, { iso3: 'AGO', name: 'Angola' },
  { iso3: 'BEN', name: 'Benin' }, { iso3: 'BWA', name: 'Botswana' },
  { iso3: 'BFA', name: 'Burkina Faso' }, { iso3: 'BDI', name: 'Burundi' },
  { iso3: 'CMR', name: 'Cameroon' }, { iso3: 'CPV', name: 'Cabo Verde' },
  { iso3: 'CAF', name: 'Central African Republic' }, { iso3: 'TCD', name: 'Chad' },
  { iso3: 'COM', name: 'Comoros' }, { iso3: 'COG', name: 'Congo' },
  { iso3: 'COD', name: 'DR Congo' }, { iso3: 'DJI', name: 'Djibouti' },
  { iso3: 'EGY', name: 'Egypt' }, { iso3: 'GNQ', name: 'Equatorial Guinea' },
  { iso3: 'ERI', name: 'Eritrea' }, { iso3: 'SWZ', name: 'Eswatini' },
  { iso3: 'ETH', name: 'Ethiopia' }, { iso3: 'GAB', name: 'Gabon' },
  { iso3: 'GMB', name: 'Gambia' }, { iso3: 'GHA', name: 'Ghana' },
  { iso3: 'GIN', name: 'Guinea' }, { iso3: 'GNB', name: 'Guinea-Bissau' },
  { iso3: 'CIV', name: "Côte d'Ivoire" }, { iso3: 'KEN', name: 'Kenya' },
  { iso3: 'LSO', name: 'Lesotho' }, { iso3: 'LBR', name: 'Liberia' },
  { iso3: 'LBY', name: 'Libya' }, { iso3: 'MDG', name: 'Madagascar' },
  { iso3: 'MWI', name: 'Malawi' }, { iso3: 'MLI', name: 'Mali' },
  { iso3: 'MRT', name: 'Mauritania' }, { iso3: 'MUS', name: 'Mauritius' },
  { iso3: 'MAR', name: 'Morocco' }, { iso3: 'MOZ', name: 'Mozambique' },
  { iso3: 'NAM', name: 'Namibia' }, { iso3: 'NER', name: 'Niger' },
  { iso3: 'NGA', name: 'Nigeria' }, { iso3: 'RWA', name: 'Rwanda' },
  { iso3: 'STP', name: 'São Tomé and Príncipe' }, { iso3: 'SEN', name: 'Senegal' },
  { iso3: 'SLE', name: 'Sierra Leone' }, { iso3: 'SOM', name: 'Somalia' },
  { iso3: 'ZAF', name: 'South Africa' }, { iso3: 'SSD', name: 'South Sudan' },
  { iso3: 'SDN', name: 'Sudan' }, { iso3: 'TZA', name: 'Tanzania' },
  { iso3: 'TGO', name: 'Togo' }, { iso3: 'TUN', name: 'Tunisia' },
  { iso3: 'UGA', name: 'Uganda' }, { iso3: 'ZMB', name: 'Zambia' },
  { iso3: 'ZWE', name: 'Zimbabwe' },
];

const KpiChip = ({ label, valueA, valueB, countryA, countryB, format = v => v, color = 'var(--text)' }) => (
  <div style={{
    background: 'var(--afcfta-bg)',
    borderRadius: 10,
    padding: '12px 16px',
    border: '1px solid var(--afcfta-border)',
  }}>
    <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
      {label}
    </div>
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
      <div>
        <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginBottom: 2 }}>{countryA}</div>
        <div style={{ fontSize: 18, fontWeight: 800, color, fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
          {format(valueA)}
        </div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginBottom: 2 }}>{countryB}</div>
        <div style={{ fontSize: 18, fontWeight: 800, color, fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
          {format(valueB)}
        </div>
      </div>
    </div>
  </div>
);

const ProductFlowRow = ({ item, lang }) => (
  <div style={{
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '8px 0', borderBottom: '1px solid var(--afcfta-border)', fontSize: 13,
  }}>
    <div>
      <div style={{ fontWeight: 600, color: 'var(--text)' }}>{item.product}</div>
      {item.hs6Code && (
        <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'var(--afcfta-muted)' }}>SH{item.hs6Code}</div>
      )}
    </div>
    <div style={{
      fontSize: 14, fontWeight: 700, color: 'var(--green)',
      fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)",
    }}>
      {fmtMUSD(item.potential_musd)}
    </div>
  </div>
);

export default function CountryComparison({ language = 'fr' }) {
  const lang = language;
  const [countryA, setCountryA] = useState('');
  const [countryB, setCountryB] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const txt = {
    fr: {
      title: 'Comparaison Pays',
      subtitle: 'Analyse de complémentarité commerciale entre deux nations AfCFTA',
      selectA: 'Pays A',
      selectB: 'Pays B',
      compare: 'Comparer',
      loading: 'Analyse comparative en cours…',
      bilateral: 'Commerce bilatéral',
      economic: 'Indicateurs économiques',
      complementarity: 'Complémentarité commerciale',
      afcftaPotential: 'Potentiel AfCFTA',
      aToB: 'A → B peut fournir',
      bToA: 'B → A peut fournir',
      sources: 'Sources',
      gdp: 'PIB (Mds USD)',
      growth: 'Croissance PIB',
      hdi: 'IDH (UNDP 2023)',
      gai: 'GAI 2025',
      inflation: 'Inflation',
      score: 'Score complémentarité',
      tariffSavings: 'Économies tarifaires',
      totalPotential: 'Potentiel total',
      barriers: 'Obstacles identifiés',
      opportunities: 'Opportunités clés',
    },
    en: {
      title: 'Country Comparison',
      subtitle: 'Trade complementarity analysis between two AfCFTA nations',
      selectA: 'Country A',
      selectB: 'Country B',
      compare: 'Compare',
      loading: 'Comparative analysis in progress…',
      bilateral: 'Bilateral trade',
      economic: 'Economic indicators',
      complementarity: 'Trade complementarity',
      afcftaPotential: 'AfCFTA potential',
      aToB: 'A → B can supply',
      bToA: 'B → A can supply',
      sources: 'Sources',
      gdp: 'GDP (USD Bn)',
      growth: 'GDP growth',
      hdi: 'HDI (UNDP 2023)',
      gai: 'GAI 2025',
      inflation: 'Inflation',
      score: 'Complementarity score',
      tariffSavings: 'Tariff savings',
      totalPotential: 'Total potential',
      barriers: 'Identified barriers',
      opportunities: 'Key opportunities',
    },
  }[lang] || {};

  const run = useCallback(async () => {
    if (!countryA || !countryB || countryA === countryB) return;
    setLoading(true);
    setError(null);
    setData(null);

    const nameA = AFCFTA_COUNTRIES.find(c => c.iso3 === countryA)?.name || countryA;
    const nameB = AFCFTA_COUNTRIES.find(c => c.iso3 === countryB)?.name || countryB;

    try {
      const res = await axios.get(`${API}/ai/compare`, {
        params: { country_a: nameA, country_b: nameB, lang },
      });
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || (lang === 'fr' ? 'Erreur analyse' : 'Analysis error'));
    } finally {
      setLoading(false);
    }
  }, [countryA, countryB, lang]);

  const bilateral = data?.bilateral_trade || {};
  const econ = data?.economic_comparison || {};
  const comp = data?.trade_complementarity || {};
  const afcfta = data?.afcfta_potential || {};

  const nameA = AFCFTA_COUNTRIES.find(c => c.iso3 === countryA)?.name || countryA || 'A';
  const nameB = AFCFTA_COUNTRIES.find(c => c.iso3 === countryB)?.name || countryB || 'B';

  // Rapport PDF de la comparaison : commerce bilatéral + indicateurs économiques.
  const buildPdfSpec = () => {
    if (!data) return null;
    const fr = lang !== 'en';
    const pair = (label, va, vb) => ({
      title: label,
      keyValues: [
        { label: nameA, value: va ?? '—' },
        { label: nameB, value: vb ?? '—' },
      ],
    });
    return {
      badge: fr ? 'COMPARAISON PAYS' : 'COUNTRY COMPARISON',
      title: `${nameA} ⇄ ${nameB}`,
      subtitle: txt.subtitle || txt.title,
      sections: [
        (bilateral.exports_a_to_b_musd != null || bilateral.exports_b_to_a_musd != null) && {
          title: fr ? 'Commerce bilatéral' : 'Bilateral trade',
          keyValues: [
            { label: `${nameA} → ${nameB}`, value: fmtMUSD(bilateral.exports_a_to_b_musd) },
            { label: `${nameB} → ${nameA}`, value: fmtMUSD(bilateral.exports_b_to_a_musd) },
          ],
        },
        pair(txt.gdp, econ.gdp_a_billion, econ.gdp_b_billion),
        pair(txt.growth, econ.gdp_growth_a != null ? `${econ.gdp_growth_a}%` : null, econ.gdp_growth_b != null ? `${econ.gdp_growth_b}%` : null),
        pair(txt.hdi, econ.hdi_a, econ.hdi_b),
        pair(txt.inflation, econ.inflation_a != null ? `${econ.inflation_a}%` : null, econ.inflation_b != null ? `${econ.inflation_b}%` : null),
        data.note && { title: fr ? 'Note' : 'Note', paragraphs: [data.note] },
      ].filter(Boolean),
      source: data.sources ? data.sources.join(' · ') : 'IMF, UNDP, OEC',
      filename: opportunityPdfFilename('Comparaison', `${countryA}_${countryB}`),
    };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ textAlign: 'center', paddingBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 6 }}>
          <ArrowLeftRight style={{ width: 22, height: 22, color: 'var(--gold)' }} />
          <h2 style={{ fontSize: 'clamp(18px,2.2vw,26px)', fontWeight: 800, color: 'var(--text)' }}>
            {txt.title}
          </h2>
        </div>
        <p style={{ fontSize: 13, color: 'var(--afcfta-muted)' }}>{txt.subtitle}</p>
      </div>

      {/* Controls */}
      <div className="afcfta-card" style={{ padding: '18px 22px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr auto', gap: 12, alignItems: 'end' }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--afcfta-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {txt.selectA}
            </div>
            <Select value={countryA} onValueChange={setCountryA}>
              <SelectTrigger style={{ background: 'var(--afcfta-bg)', border: '1px solid var(--afcfta-border)', color: 'var(--text)' }}>
                <SelectValue placeholder={txt.selectA} />
              </SelectTrigger>
              <SelectContent>
                {AFCFTA_COUNTRIES.filter(c => c.iso3 !== countryB).map(c => (
                  <SelectItem key={c.iso3} value={c.iso3}>{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', paddingBottom: 2 }}>
            <ArrowLeftRight style={{ width: 18, height: 18, color: 'var(--afcfta-muted)' }} />
          </div>

          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--afcfta-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {txt.selectB}
            </div>
            <Select value={countryB} onValueChange={setCountryB}>
              <SelectTrigger style={{ background: 'var(--afcfta-bg)', border: '1px solid var(--afcfta-border)', color: 'var(--text)' }}>
                <SelectValue placeholder={txt.selectB} />
              </SelectTrigger>
              <SelectContent>
                {AFCFTA_COUNTRIES.filter(c => c.iso3 !== countryA).map(c => (
                  <SelectItem key={c.iso3} value={c.iso3}>{c.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <button
            onClick={run}
            disabled={!countryA || !countryB || countryA === countryB || loading}
            style={{
              display: 'flex', alignItems: 'center', gap: 7,
              padding: '10px 18px',
              borderRadius: 8, fontSize: 13, fontWeight: 700,
              border: 'none', cursor: (!countryA || !countryB || countryA === countryB || loading) ? 'not-allowed' : 'pointer',
              background: (!countryA || !countryB || countryA === countryB || loading) ? 'rgba(212,137,26,0.3)' : 'var(--gold)',
              color: '#fff',
              opacity: (!countryA || !countryB || countryA === countryB || loading) ? 0.65 : 1,
              whiteSpace: 'nowrap',
            }}
          >
            {loading
              ? <Loader2 style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} />
              : <Sparkles style={{ width: 14, height: 14 }} />}
            {txt.compare}
          </button>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="afcfta-card" style={{ padding: '40px', textAlign: 'center' }}>
          <Loader2 style={{ width: 36, height: 36, color: 'var(--gold)', margin: '0 auto 12px', animation: 'spin 1s linear infinite' }} />
          <div style={{ fontSize: 14, color: 'var(--afcfta-muted)' }}>{txt.loading}</div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="afcfta-card" style={{ padding: '20px', borderLeft: '3px solid rgba(200,16,46,0.4)', background: 'rgba(200,16,46,0.06)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text)' }}>
            <AlertCircle style={{ width: 16, height: 16, color: '#e05070', flexShrink: 0 }} />
            {error}
          </div>
        </div>
      )}

      {/* Results */}
      {!loading && !error && data && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <OpportunityPdfExport getSpec={buildPdfSpec} language={lang} />
          </div>
          {/* Data-status notice (e.g. OEC trade flows temporarily unavailable) */}
          {data.note && (
            <div className="afcfta-card" style={{ padding: '12px 16px', borderLeft: '3px solid var(--gold)', background: 'rgba(212,137,26,0.06)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text)' }}>
                <Info style={{ width: 15, height: 15, color: 'var(--gold)', flexShrink: 0 }} />
                {data.note}
              </div>
            </div>
          )}

          {/* Bilateral trade */}
          {(bilateral.exports_a_to_b_musd != null || bilateral.exports_b_to_a_musd != null) && (
            <div className="afcfta-card" style={{ padding: '18px 22px' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Scale style={{ width: 16, height: 16, color: 'var(--gold)' }} />
                {txt.bilateral} {bilateral.year ? `(${bilateral.year})` : ''}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14 }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginBottom: 4 }}>{nameA} → {nameB}</div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--green)', fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
                    {fmtMUSD(bilateral.exports_a_to_b_musd)}
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginBottom: 4 }}>{lang === 'fr' ? 'Balance' : 'Balance'}</div>
                  <div style={{
                    fontSize: 22, fontWeight: 800,
                    color: bilateral.balance_musd >= 0 ? 'var(--green)' : '#e05070',
                    fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)",
                  }}>
                    {bilateral.balance_musd >= 0 ? '+' : ''}{fmtMUSD(bilateral.balance_musd)}
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginBottom: 4 }}>{nameB} → {nameA}</div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#4f8ef7', fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
                    {fmtMUSD(bilateral.exports_b_to_a_musd)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Economic comparison */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 14 }}>
            <KpiChip label={txt.gdp} valueA={econ.gdp_a_billion} valueB={econ.gdp_b_billion}
              countryA={nameA} countryB={nameB}
              format={v => v ? `$${Number(v).toFixed(1)}Bn` : '—'} color="var(--text)" />
            <KpiChip label={txt.growth} valueA={econ.gdp_growth_a} valueB={econ.gdp_growth_b}
              countryA={nameA} countryB={nameB}
              format={v => v != null ? `${Number(v).toFixed(1)}%` : '—'} color="var(--green)" />
            <KpiChip label={txt.hdi} valueA={econ.hdi_a} valueB={econ.hdi_b}
              countryA={nameA} countryB={nameB}
              format={v => v != null ? Number(v).toFixed(3) : '—'} color="#4f8ef7" />
            <KpiChip label={txt.inflation} valueA={econ.inflation_a} valueB={econ.inflation_b}
              countryA={nameA} countryB={nameB}
              format={v => v != null ? `${Number(v).toFixed(1)}%` : '—'}
              color={Math.max(econ.inflation_a || 0, econ.inflation_b || 0) > 15 ? '#e05070' : 'var(--gold)'} />
          </div>

          {/* Trade complementarity */}
          {(comp.a_can_supply_to_b?.length > 0 || comp.b_can_supply_to_a?.length > 0) && (
            <div className="afcfta-card" style={{ padding: '18px 22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <TrendingUp style={{ width: 16, height: 16, color: 'var(--gold)' }} />
                  {txt.complementarity}
                </div>
                {comp.score != null && (
                  <div style={{
                    fontSize: 12, fontWeight: 700,
                    background: 'rgba(212,137,26,0.12)',
                    color: 'var(--gold)',
                    padding: '3px 12px', borderRadius: 6,
                    border: '1px solid rgba(212,137,26,0.22)',
                  }}>
                    {txt.score}: {Number(comp.score).toFixed(1)}/10
                  </div>
                )}
              </div>

              {comp.explanation && (
                <p style={{ fontSize: 13, color: 'var(--afcfta-muted)', marginBottom: 16, lineHeight: 1.6 }}>
                  {comp.explanation}
                </p>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {comp.a_can_supply_to_b?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--green)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {nameA} → {nameB}
                    </div>
                    {comp.a_can_supply_to_b.map((item, i) => (
                      <ProductFlowRow key={i} item={item} lang={lang} />
                    ))}
                  </div>
                )}
                {comp.b_can_supply_to_a?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 700, color: '#4f8ef7', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {nameB} → {nameA}
                    </div>
                    {comp.b_can_supply_to_a.map((item, i) => (
                      <ProductFlowRow key={i} item={item} lang={lang} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AfCFTA Potential */}
          {(afcfta.total_potential_musd || afcfta.key_opportunities?.length > 0) && (
            <div className="afcfta-card" style={{ padding: '18px 22px', borderLeft: '3px solid var(--green)' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Zap style={{ width: 16, height: 16, color: 'var(--green)' }} />
                {txt.afcftaPotential}
              </div>
              <div style={{ display: 'flex', gap: 24, marginBottom: 14, flexWrap: 'wrap' }}>
                {afcfta.total_potential_musd && (
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginBottom: 2 }}>{txt.totalPotential}</div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--green)', fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
                      {fmtMUSD(afcfta.total_potential_musd)}
                    </div>
                  </div>
                )}
                {afcfta.tariff_savings_musd && (
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginBottom: 2 }}>{txt.tariffSavings}</div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--gold)', fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
                      {fmtMUSD(afcfta.tariff_savings_musd)}
                    </div>
                  </div>
                )}
              </div>
              {afcfta.key_opportunities?.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--afcfta-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {txt.opportunities}
                  </div>
                  {afcfta.key_opportunities.map((o, i) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--text)', marginBottom: 4 }}>• {o}</div>
                  ))}
                </div>
              )}
              {afcfta.barriers?.length > 0 && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--afcfta-border)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#e05070', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {txt.barriers}
                  </div>
                  {afcfta.barriers.map((b, i) => (
                    <div key={i} style={{ fontSize: 13, color: 'var(--afcfta-muted)', marginBottom: 4 }}>• {b}</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Sources */}
          {data.sources && (
            <div style={{
              padding: '10px 16px', borderRadius: 8,
              background: 'var(--afcfta-bg)', border: '1px solid var(--afcfta-border)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
              fontSize: 12, color: 'var(--afcfta-muted)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Info style={{ width: 13, height: 13 }} />
                <strong>{txt.sources}:</strong> {data.sources.join(' · ')}
              </div>
              {data.data_freshness && <DataFreshnessIndicator freshness={data.data_freshness} language={lang} />}
            </div>
          )}
        </>
      )}

      {/* Empty */}
      {!loading && !error && !data && (
        <div style={{ textAlign: 'center', padding: '64px 24px', color: 'var(--afcfta-muted)' }}>
          <ArrowLeftRight style={{ width: 48, height: 48, margin: '0 auto 16px', opacity: 0.2, color: 'var(--gold)' }} />
          <p style={{ fontSize: 14 }}>
            {lang === 'fr'
              ? 'Sélectionnez deux pays AfCFTA pour analyser leur complémentarité commerciale'
              : 'Select two AfCFTA countries to analyze their trade complementarity'}
          </p>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
