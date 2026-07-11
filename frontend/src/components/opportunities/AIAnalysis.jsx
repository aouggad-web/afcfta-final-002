/**
 * AI Trade Analysis — powered by Anthropic Claude
 * Reproduces AI Studio app quality: SH2/SH4/SH6 hierarchy, corrected GAI anchors,
 * leadTimeSavings, priceCompetitiveness, rulesOfOrigin
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Sparkles, Globe, TrendingUp, TrendingDown, Factory,
  Loader2, AlertCircle, Target, DollarSign, ArrowRight,
  ChevronDown, ChevronUp, Info, CheckCircle, AlertTriangle,
  Zap, Clock, Tag, ShieldCheck, BarChart2, Lightbulb,
  XCircle, Award, ListChecks, BadgeCheck, Database, Truck,
} from 'lucide-react';

import TradeSankeyDiagram from './TradeSankeyDiagram';
import { DataFreshnessIndicator } from '../ui/data-freshness-indicator';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// ── Formatters ────────────────────────────────────────────────────────────────
const fmtMUSD = (v) => {
  if (!v || isNaN(v)) return '$0';
  if (v >= 1000) return `$${(v / 1000).toFixed(2)}B`;
  if (v >= 1) return `$${Number(v).toFixed(0)}M`;
  return `$${(v * 1000).toFixed(0)}K`;
};

const fmtPct = (v) => (v != null && !isNaN(v) ? `${Number(v).toFixed(1)}%` : '—');

// ── HS Hierarchy Badge ────────────────────────────────────────────────────────
const HSBadge = ({ product }) => {
  if (!product) return null;
  const hs6 = product.hs6Code || product.hs_code;
  const hs4 = product.hs4Code || (hs6 && hs6.slice(0, 4));
  const hs2 = product.hs2Code || (hs6 && hs6.slice(0, 2));
  const hs2Name = product.hs2Name;
  const hs4Name = product.hs4Name;
  const hs6Name = product.hs6Name;

  return (
    <div className="space-y-1 text-[11px]">
      {hs2 && (
        <div className="flex items-center gap-1.5 text-[var(--afcfta-muted)]">
          <span className="font-mono bg-[var(--afcfta-bg)] px-1.5 py-0.5 rounded border border-[var(--afcfta-border)] text-[10px]">
            SH{hs2}
          </span>
          {hs2Name && <span className="truncate">{hs2Name}</span>}
        </div>
      )}
      {hs4 && hs4 !== hs2 && (
        <div className="flex items-center gap-1.5 text-[var(--afcfta-muted)]">
          <span className="font-mono bg-[var(--afcfta-bg)] px-1.5 py-0.5 rounded border border-[var(--afcfta-border)] text-[10px]">
            SH{hs4}
          </span>
          {hs4Name && <span className="truncate">{hs4Name}</span>}
        </div>
      )}
      {hs6 && (
        <div className="flex items-center gap-1.5 font-medium text-[var(--text)]">
          <span className="font-mono bg-[rgba(var(--gold-rgb,212,137,26),0.12)] text-[var(--gold)] px-1.5 py-0.5 rounded border border-[rgba(var(--gold-rgb,212,137,26),0.25)] text-[10px]">
            SH{hs6}
          </span>
          {hs6Name && <span className="truncate">{hs6Name}</span>}
        </div>
      )}
    </div>
  );
};

// ── Advantage Metrics strip ───────────────────────────────────────────────────
const AdvantageMetrics = ({ leadTimeSavings, priceCompetitiveness, rulesOfOrigin, hs6Code, lang }) => {
  if (!leadTimeSavings && !priceCompetitiveness && !rulesOfOrigin) return null;
  return (
    <div className="grid grid-cols-3 gap-2 pt-3 border-t border-[var(--afcfta-border)] text-center text-[11px]">
      {leadTimeSavings != null && (
        <div className="flex flex-col items-center gap-0.5">
          <Clock className="h-3.5 w-3.5 text-[var(--afcfta-muted)]" />
          <span className="font-bold text-[var(--text)]">-{leadTimeSavings}j</span>
          <span className="text-[var(--afcfta-muted)]">{lang === 'fr' ? 'Délai' : 'Lead time'}</span>
        </div>
      )}
      {priceCompetitiveness != null && (
        <div className="flex flex-col items-center gap-0.5">
          <BarChart2 className="h-3.5 w-3.5 text-[var(--green)]" />
          <span className="font-bold text-[var(--green)]">-{fmtPct(priceCompetitiveness)}</span>
          <span className="text-[var(--afcfta-muted)]">{lang === 'fr' ? 'Coût' : 'Cost'}</span>
        </div>
      )}
      {rulesOfOrigin && (
        <div className="flex flex-col items-center gap-0.5 col-span-3 text-left mt-1 border-t border-[var(--afcfta-border)] pt-2">
          <div className="flex items-center gap-1 text-[var(--afcfta-muted)]">
            <ShieldCheck className="h-3 w-3 flex-shrink-0" />
            <span className="font-medium">{lang === 'fr' ? 'Règles d\'origine ZLECAf' : 'AfCFTA Rules of Origin'}:</span>
          </div>
          <span className="text-[var(--text)] text-[11px] leading-tight">{rulesOfOrigin}</span>
          <OfficialRuleOfOrigin hs6Code={hs6Code} lang={lang} />
        </div>
      )}
    </div>
  );
};

// ── Official Rules of Origin (backend dataset, not AI-generated) ─────────────
// Module-level cache so opportunity cards sharing an HS6 code (or re-renders)
// don't each fire their own request — this data is static per code+lang.
const ruleOfOriginCache = new Map();

const OfficialRuleOfOrigin = ({ hs6Code, lang }) => {
  const [rule, setRule] = useState(null);

  useEffect(() => {
    if (!hs6Code) return;
    const cacheKey = `${hs6Code}|${lang}`;
    if (ruleOfOriginCache.has(cacheKey)) {
      setRule(ruleOfOriginCache.get(cacheKey));
      return;
    }
    let cancelled = false;
    axios.get(`${API}/rules-of-origin/${hs6Code}`, { params: { lang } })
      .then(r => {
        ruleOfOriginCache.set(cacheKey, r.data);
        if (!cancelled) setRule(r.data);
      })
      .catch(() => { if (!cancelled) setRule(null); });
    return () => { cancelled = true; };
  }, [hs6Code, lang]);

  const primaryRule = rule?.rules?.primary_rule;
  if (!primaryRule || !primaryRule.explanation) return null;

  return (
    <div style={{
      marginTop: 6,
      padding: '8px 10px',
      background: 'rgba(26,122,74,0.06)',
      border: '1px solid rgba(26,122,74,0.15)',
      borderRadius: 6,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
        <ShieldCheck style={{ width: 11, height: 11, color: 'var(--green)', flexShrink: 0 }} />
        <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--green)' }}>
          {primaryRule.name || primaryRule.code}
        </span>
        {rule.status === 'YTB' && (
          <span style={{ fontSize: 9, fontWeight: 700, color: 'var(--gold)' }}>
            {lang === 'fr' ? '· en négociation' : '· under negotiation'}
          </span>
        )}
      </div>
      <p style={{ fontSize: 11, color: 'var(--afcfta-muted)', lineHeight: 1.4, margin: 0 }}>
        {primaryRule.explanation}
      </p>
    </div>
  );
};

// ── OEC Data Badge ────────────────────────────────────────────────────────────
const OECBadge = ({ oecData, lang }) => {
  if (!oecData) return null;
  const verified = oecData.data_quality === 'verified';
  const score = oecData.confidence_score;
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      fontSize: 10, fontWeight: 700,
      padding: '2px 8px', borderRadius: 12,
      background: verified ? 'rgba(26,122,74,0.10)' : 'rgba(212,137,26,0.10)',
      color: verified ? 'var(--green)' : 'var(--gold)',
      border: `1px solid ${verified ? 'rgba(26,122,74,0.22)' : 'rgba(212,137,26,0.22)'}`,
    }}>
      <Database style={{ width: 9, height: 9 }} />
      {verified
        ? `OEC ✓ ${oecData.verified_trade_value != null ? fmtMUSD(oecData.verified_trade_value) : ''}`
        : (lang === 'fr' ? 'Estimation' : 'Estimate')}
      {!verified && score && ` ${Math.round(score * 100)}%`}
    </div>
  );
};

// ── Entry Strategy Section ────────────────────────────────────────────────────
const EntryStrategy = ({ strategy, lang }) => {
  if (!strategy) return null;
  const { quickWins = [], keyBarriers = [], certifications = [], priorityActions = [], timelineMonths } = strategy;
  if (!quickWins.length && !keyBarriers.length && !priorityActions.length) return null;

  return (
    <div style={{
      marginTop: 14,
      borderTop: '2px solid rgba(212,137,26,0.20)',
      paddingTop: 14,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 7,
        fontSize: 12, fontWeight: 800,
        color: 'var(--gold)',
        marginBottom: 12,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
      }}>
        <Lightbulb style={{ width: 14, height: 14 }} />
        {lang === 'fr' ? "Stratégie d'entrée" : 'Entry Strategy'}
        {timelineMonths && (
          <span style={{
            marginLeft: 'auto', fontSize: 10, fontWeight: 600,
            background: 'rgba(212,137,26,0.12)',
            padding: '1px 7px', borderRadius: 8,
            color: 'var(--gold)',
          }}>
            ~{timelineMonths} {lang === 'fr' ? 'mois' : 'mo.'}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>

        {/* Quick wins */}
        {quickWins.length > 0 && (
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--green)', marginBottom: 5, display: 'flex', alignItems: 'center', gap: 4 }}>
              <Zap style={{ width: 10, height: 10 }} />
              {lang === 'fr' ? 'Actions rapides' : 'Quick Wins'}
            </div>
            {quickWins.map((w, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, fontSize: 12, color: 'var(--text)', marginBottom: 3 }}>
                <CheckCircle style={{ width: 11, height: 11, color: 'var(--green)', flexShrink: 0, marginTop: 2 }} />
                <span style={{ lineHeight: 1.45 }}>{w}</span>
              </div>
            ))}
          </div>
        )}

        {/* Priority actions */}
        {priorityActions.length > 0 && (
          <div>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--terra, #c84b1a)', marginBottom: 5, display: 'flex', alignItems: 'center', gap: 4 }}>
              <ListChecks style={{ width: 10, height: 10 }} />
              {lang === 'fr' ? 'Actions prioritaires' : 'Priority Actions'}
            </div>
            {priorityActions.map((a, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 6, fontSize: 12, color: 'var(--text)', marginBottom: 3 }}>
                <span style={{
                  minWidth: 16, height: 16, borderRadius: '50%',
                  background: 'rgba(200,75,26,0.12)',
                  color: 'var(--terra, #c84b1a)',
                  fontSize: 9, fontWeight: 800,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, marginTop: 1,
                }}>{i + 1}</span>
                <span style={{ lineHeight: 1.45 }}>{a}</span>
              </div>
            ))}
          </div>
        )}

        {/* Barriers + certifications */}
        {(keyBarriers.length > 0 || certifications.length > 0) && (
          <div style={{ display: 'grid', gridTemplateColumns: keyBarriers.length && certifications.length ? '1fr 1fr' : '1fr', gap: 8 }}>
            {keyBarriers.length > 0 && (
              <div style={{ background: 'rgba(200,16,46,0.06)', borderRadius: 6, padding: '8px 10px' }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: '#e05070', marginBottom: 5, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <XCircle style={{ width: 10, height: 10 }} />
                  {lang === 'fr' ? 'Obstacles' : 'Barriers'}
                </div>
                {keyBarriers.map((b, i) => (
                  <div key={i} style={{ fontSize: 11, color: 'var(--text)', marginBottom: 2, lineHeight: 1.4 }}>• {b}</div>
                ))}
              </div>
            )}
            {certifications.length > 0 && (
              <div style={{ background: 'rgba(79,142,247,0.07)', borderRadius: 6, padding: '8px 10px' }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: '#4f8ef7', marginBottom: 5, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Award style={{ width: 10, height: 10 }} />
                  {lang === 'fr' ? 'Certifications' : 'Certifications'}
                </div>
                {certifications.map((c, i) => (
                  <div key={i} style={{ fontSize: 11, color: 'var(--text)', marginBottom: 2, lineHeight: 1.4 }}>• {c}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ── Production Capacity Section (FAO / USGS / UNIDO) ──────────────────────────
const fmtBig = (v, unit) => {
  if (v == null || isNaN(v)) return '—';
  if (unit === 'USD') {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(2)} Md`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(1)} M`;
    return `$${Number(v).toLocaleString()}`;
  }
  if (unit === 'tonnes') {
    if (v >= 1e6) return `${(v / 1e6).toFixed(2)} Mt`;
    if (v >= 1e3) return `${(v / 1e3).toFixed(1)} kt`;
    return `${Number(v).toLocaleString()} t`;
  }
  // Unités naturelles (1000 b/d, bcm, carats, têtes…) : afficher tel quel
  return `${Number(v).toLocaleString(undefined, { maximumFractionDigits: 1 })} ${unit || ''}`.trim();
};

const SOURCE_BADGE = {
  agri: { label: 'FAO · FAOSTAT', color: 'var(--green)', bg: 'rgba(26,122,74,0.10)' },
  mining: { label: 'USGS · MCS', color: '#c84b1a', bg: 'rgba(200,75,26,0.10)' },
  manufacturing: { label: 'UNIDO · INDSTAT4', color: '#4f8ef7', bg: 'rgba(79,142,247,0.10)' },
};

const LogisticsSizing = ({ logistics, lang }) => {
  if (!logistics || !logistics.available) return null;
  const fr = lang === 'fr';
  const { containers_needed, container_type, total_freight_usd, estimated_weight_kg, accessibility_index } = logistics;

  return (
    <div style={{ marginTop: 14, borderTop: '2px solid rgba(79,142,247,0.20)', paddingTop: 14 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 7,
        fontSize: 12, fontWeight: 800, color: '#4f8ef7',
        marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em',
      }}>
        <Truck style={{ width: 14, height: 14 }} />
        {fr ? 'Logistique estimée' : 'Estimated logistics'}
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {containers_needed != null && (
          <div style={{ flex: '1 1 110px', background: 'var(--afcfta-bg)', borderRadius: 8, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginBottom: 2 }}>
              {fr ? 'Conteneurs' : 'Containers'}
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text)' }}>
              {containers_needed} × {container_type === 'feu' ? "40′" : "20′"}
            </div>
          </div>
        )}
        {total_freight_usd != null && (
          <div style={{ flex: '1 1 110px', background: 'var(--afcfta-bg)', borderRadius: 8, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginBottom: 2 }}>
              {fr ? 'Fret total estimé' : 'Est. total freight'}
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text)' }}>
              {fmtBig(total_freight_usd, 'USD')}
            </div>
          </div>
        )}
        {accessibility_index != null && (
          <div style={{ flex: '1 1 90px', background: 'var(--afcfta-bg)', borderRadius: 8, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginBottom: 2 }}>
              {fr ? 'Accessibilité' : 'Accessibility'}
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--gold)' }}>
              {Math.round(accessibility_index * 100)}%
            </div>
          </div>
        )}
      </div>
      {estimated_weight_kg != null && (
        <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginTop: 6 }}>
          {fr ? 'Poids estimé depuis la valeur potentielle' : 'Weight estimated from potential value'}:{' '}
          {Math.round(estimated_weight_kg).toLocaleString()} kg
        </div>
      )}
    </div>
  );
};

const ProductionCapacity = ({ capacity, lang }) => {
  if (!capacity || !capacity.available) return null;
  const fr = lang === 'fr';
  const { commodity, unit, dimension, latest_value, latest_year, cagr_pct,
          continental = {}, integration_scenarios = {}, source = {},
          is_proxy, proxy_caveat, measure, match_level } = capacity;
  const badge = is_proxy
    ? { label: source.institution || 'OEC / BACI', bg: '#fef3c7', color: '#92400e' }
    : (SOURCE_BADGE[dimension] || SOURCE_BADGE.agri);
  const rank = continental.rank;
  const share = continental.country_share_pct;
  const scenarioList = Object.values(integration_scenarios).filter(s => s.annual_growth_pct != null);
  const trendUp = (cagr_pct || 0) >= 0;

  return (
    <div style={{ marginTop: 14, borderTop: '2px solid rgba(26,122,74,0.20)', paddingTop: 14 }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 7,
        fontSize: 12, fontWeight: 800, color: 'var(--green)',
        marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em',
      }}>
        <Factory style={{ width: 14, height: 14 }} />
        {is_proxy
          ? (fr ? 'Capacité de production — proxy export' : 'Production capacity — export proxy')
          : (fr ? 'Capacité de production' : 'Production capacity')}
        <span style={{
          marginLeft: 'auto', fontSize: 9, fontWeight: 700,
          background: badge.bg, color: badge.color,
          padding: '2px 7px', borderRadius: 8,
        }}>
          {badge.label}
        </span>
      </div>

      {/* Headline metrics */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 110px', background: 'var(--afcfta-bg)', borderRadius: 8, padding: '8px 10px' }}>
          <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginBottom: 2 }}>
            {is_proxy
              ? `${fr ? 'Exports' : 'Exports'}${match_level ? ` ${match_level}` : ''} · ${latest_year}`
              : `${commodity} · ${latest_year}`}
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text)' }}>
            {fmtBig(latest_value, unit)}
          </div>
          {is_proxy && measure && (
            <div style={{ fontSize: 9, color: 'var(--afcfta-muted)', marginTop: 2 }}>
              {measure}
            </div>
          )}
        </div>
        {cagr_pct != null && (
          <div style={{ flex: '1 1 90px', background: 'var(--afcfta-bg)', borderRadius: 8, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginBottom: 2 }}>
              {fr ? 'Tendance' : 'Trend'} 21–{String(latest_year).slice(2)}
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, color: trendUp ? 'var(--green)' : '#e05070', display: 'flex', alignItems: 'center', gap: 4 }}>
              {trendUp ? <TrendingUp style={{ width: 14, height: 14 }} /> : <TrendingDown style={{ width: 14, height: 14 }} />}
              {cagr_pct > 0 ? '+' : ''}{cagr_pct}%
            </div>
          </div>
        )}
        {rank != null && (
          <div style={{ flex: '1 1 90px', background: 'var(--afcfta-bg)', borderRadius: 8, padding: '8px 10px' }}>
            <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', marginBottom: 2 }}>
              {fr ? 'Rang africain' : 'African rank'}
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--gold)' }}>
              {rank}<span style={{ fontSize: 11, color: 'var(--afcfta-muted)' }}>/{continental.total_countries}</span>
              {share != null && <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--afcfta-muted)', marginLeft: 6 }}>{share}%</span>}
            </div>
          </div>
        )}
      </div>

      {/* Continental context */}
      {continental.leader && (
        <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginBottom: 10, lineHeight: 1.4 }}>
          <Globe style={{ width: 11, height: 11, display: 'inline', marginRight: 4, color: 'var(--green)' }} />
          {fr ? 'Leader continental' : 'Continental leader'}: <strong style={{ color: 'var(--text)' }}>{continental.leader.country_name}</strong>
          {' '}({fmtBig(continental.leader.value, unit)})
          {continental.continental_total != null && (
            <> · {fr ? 'Total Afrique' : 'Africa total'}: {fmtBig(continental.continental_total, unit)}</>
          )}
        </div>
      )}

      {is_proxy && proxy_caveat && (
        <div style={{
          fontSize: 10.5, color: '#92400e', background: '#fef3c7',
          border: '1px solid #fde68a', borderRadius: 6, padding: '6px 9px',
          marginBottom: 10, lineHeight: 1.4,
        }}>
          ⚠ {proxy_caveat}
        </div>
      )}

      {continental.coverage_caveat && (
        <div style={{
          fontSize: 10.5, color: '#92400e', background: '#fef3c7',
          border: '1px solid #fde68a', borderRadius: 6, padding: '6px 9px',
          marginBottom: 10, lineHeight: 1.4,
        }}>
          ⚠ {continental.coverage_caveat}
        </div>
      )}

      {/* Integration scenarios */}
      {scenarioList.length > 0 && (
        <div>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--green)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
            <BarChart2 style={{ width: 10, height: 10 }} />
            {fr ? "Scénarios d'intégration africaine — horizon 2030" : 'African integration scenarios — 2030 horizon'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {scenarioList.map((s, i) => (
              <div key={i} title={s.hypothesis} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: i === 2 ? 'rgba(26,122,74,0.08)' : 'var(--afcfta-bg)',
                borderRadius: 6, padding: '6px 9px',
                border: i === 2 ? '1px solid rgba(26,122,74,0.20)' : '1px solid var(--afcfta-border)',
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {s.label}
                  </div>
                </div>
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--gold)', whiteSpace: 'nowrap' }}>
                  +{s.annual_growth_pct}%/an
                </div>
                <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--green)', whiteSpace: 'nowrap', minWidth: 64, textAlign: 'right' }}>
                  {fmtBig(s.horizon_2030, unit)}
                </div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 9, color: 'var(--afcfta-muted)', marginTop: 6, fontStyle: 'italic', lineHeight: 1.4 }}>
            {fr
              ? `Projections dérivées du CAGR réel observé. Production: ${source.institution}. Scénarios ≠ prévisions.`
              : `Projections derived from observed real CAGR. Production: ${source.institution}. Scenarios ≠ forecasts.`}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Opportunity Card ──────────────────────────────────────────────────────────
const OpportunityCard = ({ opp, mode, lang, index }) => {
  const [expanded, setExpanded] = useState(false);
  const isExport = mode === 'export';
  const isIndustrial = mode === 'industrial';

  const product = opp.product || {};
  const productName = product.name || opp.output_product || opp.product_name || '';

  const partner = isExport
    ? (opp.potentialPartner || opp.potential_partner)
    : isIndustrial
    ? (opp.targetMarkets || opp.target_markets || []).slice(0, 2).join(', ')
    : (opp.potentialSupplier || opp.potential_supplier);

  const currentSource = opp.currentSource || opp.current_source;

  const value = isExport
    ? (opp.potentialTradeValue || opp.potential_value_musd || opp.potential_trade_value || 0)
    : isIndustrial
    ? (opp.potentialTradeValue || opp.potential_value_musd || 0)
    : (opp.substitutionPotential || opp.substitution_potential_musd || opp.currentImportValue || 0);

  const tariff = opp.tariffReductionPotential || opp.tariff_reduction || opp.tariff_reduction_potential;
  const rationale = isIndustrial
    ? (opp.valueAdditionLogic || opp.value_addition_logic || opp.transformation_logic || opp.rationale || '')
    : (opp.rationale || '');

  const leadTimeSavings = opp.leadTimeSavings || opp.lead_time_savings;
  const priceComp = opp.priceCompetitiveness || opp.price_competitiveness;
  const roo = opp.rulesOfOrigin || opp.rules_of_origin;
  const entryStrategy = opp.entryStrategy || opp.entry_strategy;
  const oecData = opp.oec_data;
  const productionCapacity = opp.production_capacity || opp.productionCapacity;
  const logistics = opp.logistics;

  // Industrial input
  const input = opp.industrialInput || opp.industrial_input || {};
  const inputName = input.name || opp.input_product || '';
  const inputVolume = input.importVolume || input.import_volume || '';

  return (
    <div className="afcfta-card" style={{ padding: '18px 20px', borderLeft: '3px solid var(--gold)' }}>
      {/* Rank + HS code header + OEC badge */}
      <div className="flex items-start justify-between mb-3">
        <HSBadge product={product} />
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <span style={{ fontSize: 11, color: 'var(--afcfta-muted)', fontWeight: 700 }}>
            #{index + 1}
          </span>
          <OECBadge oecData={oecData} lang={lang} />
        </div>
      </div>

      {/* Product name */}
      <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', lineHeight: 1.3, marginBottom: 8 }}>
        {productName || '—'}
      </h3>

      {/* Direction */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--afcfta-muted)', marginBottom: 14 }}>
        <Globe style={{ width: 14, height: 14, color: 'var(--green)' }} />
        <span>
          {isExport
            ? (lang === 'fr' ? 'Vers' : 'To')
            : isIndustrial
            ? (lang === 'fr' ? 'Marchés cibles' : 'Target markets')
            : (lang === 'fr' ? 'De' : 'From')}
          {': '}
          <strong style={{ color: 'var(--text)' }}>{partner || '—'}</strong>
        </span>
      </div>

      {/* Value + Tariff */}
      <div style={{
        background: 'rgba(26,122,74,0.08)',
        border: '1px solid rgba(26,122,74,0.18)',
        borderRadius: 8,
        padding: '10px 14px',
        marginBottom: 12,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--green)', fontWeight: 600, marginBottom: 2 }}>
            {isExport
              ? (lang === 'fr' ? 'Potentiel' : 'Potential')
              : isIndustrial
              ? (lang === 'fr' ? 'Valeur potentielle' : 'Potential value')
              : (lang === 'fr' ? 'Substitution potentielle' : 'Substitution potential')}
          </div>
          <div style={{
            fontSize: 22,
            fontWeight: 800,
            color: 'var(--green)',
            fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)",
          }}>
            {fmtMUSD(value)}
          </div>
        </div>
        {tariff != null && tariff > 0 && (
          <div style={{
            background: 'rgba(26,122,74,0.15)',
            borderRadius: 6,
            padding: '4px 10px',
            fontSize: 12,
            fontWeight: 700,
            color: 'var(--green)',
          }}>
            -{fmtPct(tariff)} {lang === 'fr' ? 'tarif' : 'tariff'}
          </div>
        )}
      </div>

      {/* Current source badge */}
      {currentSource && (
        <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 4 }}>
          <Tag style={{ width: 11, height: 11 }} />
          {lang === 'fr' ? 'Source actuelle' : 'Current source'}: <strong style={{ color: 'var(--text)' }}>{currentSource}</strong>
        </div>
      )}

      {/* Industrial input chain */}
      {isIndustrial && inputName && (
        <div style={{
          background: 'rgba(79,142,247,0.08)',
          border: '1px solid rgba(79,142,247,0.18)',
          borderRadius: 8,
          padding: '10px 14px',
          marginBottom: 12,
        }}>
          <div style={{ fontSize: 11, color: '#4f8ef7', fontWeight: 700, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {lang === 'fr' ? 'Chaîne de valeur' : 'Value chain'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <div>
              <div style={{ color: 'var(--afcfta-muted)' }}>{inputName}</div>
              {input.hs6Code && (
                <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', fontFamily: 'monospace' }}>
                  SH{input.hs6Code}
                </div>
              )}
            </div>
            <ArrowRight style={{ width: 14, height: 14, color: '#4f8ef7', flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 700, color: 'var(--text)' }}>{productName}</div>
              {product.hs6Code && (
                <div style={{ fontSize: 10, color: 'var(--afcfta-muted)', fontFamily: 'monospace' }}>
                  SH{product.hs6Code}
                </div>
              )}
            </div>
          </div>
          {inputVolume && (
            <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginTop: 6 }}>
              {lang === 'fr' ? 'Volume importé' : 'Import volume'}: {inputVolume}
            </div>
          )}
        </div>
      )}

      {/* Rationale expandable */}
      {rationale && (
        <>
          <button
            onClick={() => setExpanded(e => !e)}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--afcfta-muted)',
              fontSize: 11,
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              padding: '6px 0',
            }}
          >
            <span>{isIndustrial ? (lang === 'fr' ? 'Logique de transformation' : 'Transformation logic') : (lang === 'fr' ? 'Justification' : 'Rationale')}</span>
            {expanded ? <ChevronUp style={{ width: 14, height: 14 }} /> : <ChevronDown style={{ width: 14, height: 14 }} />}
          </button>
          {expanded && (
            <div style={{
              marginTop: 6,
              padding: '10px 12px',
              background: 'var(--afcfta-bg)',
              borderRadius: 8,
              fontSize: 13,
              color: 'var(--text)',
              lineHeight: 1.6,
            }}>
              {rationale}
              {(opp.year || opp.data_year) && (
                <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', marginTop: 6, fontStyle: 'italic' }}>
                  {lang === 'fr' ? 'Données' : 'Data'}: {opp.year || opp.data_year}
                </div>
              )}
              {(opp.sourceUrl || opp.source_url || opp.data_source) && (
                <div style={{ fontSize: 11, color: 'var(--afcfta-muted)', fontStyle: 'italic' }}>
                  {lang === 'fr' ? 'Source' : 'Source'}: {opp.sourceUrl || opp.source_url || opp.data_source}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Advantage metrics strip */}
      <AdvantageMetrics
        leadTimeSavings={leadTimeSavings}
        priceCompetitiveness={priceComp}
        rulesOfOrigin={roo}
        hs6Code={product.hs6Code || product.hs_code}
        lang={lang}
      />

      {/* Production Capacity — données réelles FAO/USGS/UNIDO + scénarios */}
      <ProductionCapacity capacity={productionCapacity} lang={lang} />

      {/* Logistique — conteneurs dimensionnés depuis la valeur potentielle */}
      <LogisticsSizing logistics={logistics} lang={lang} />

      {/* Entry Strategy — section clé manquante */}
      <EntryStrategy strategy={entryStrategy} lang={lang} />
    </div>
  );
};

// ── Expected Results panel ────────────────────────────────────────────────────
const ExpectedResults = ({ data, mode, lang }) => {
  if (!data) return null;
  const s3 = data.scenario_3_years;
  const s5 = data.scenario_5_years;
  if (!s3 && !s5) return null;

  const label3 = lang === 'fr' ? '3 ans — Court terme' : '3 Years — Short term';
  const label5 = lang === 'fr' ? '5 ans — Moyen terme' : '5 Years — Medium term';

  const rows3 = [];
  const rows5 = [];

  if (s3) {
    if (s3.export_growth_percent) rows3.push([lang === 'fr' ? 'Croissance exports' : 'Export growth', `+${fmtPct(s3.export_growth_percent)}`]);
    if (s3.import_substitution_percent) rows3.push([lang === 'fr' ? 'Substitution imports' : 'Import substitution', fmtPct(s3.import_substitution_percent)]);
    if (s3.savings_musd) rows3.push([lang === 'fr' ? 'Économies' : 'Savings', fmtMUSD(s3.savings_musd)]);
    if (s3.new_jobs_created) rows3.push([lang === 'fr' ? 'Emplois créés' : 'Jobs created', s3.new_jobs_created.toLocaleString()]);
    if (s3.industrial_value_added_musd) rows3.push([lang === 'fr' ? 'Valeur ajoutée' : 'Value added', fmtMUSD(s3.industrial_value_added_musd)]);
    if (s3.total_export_value_musd) rows3.push([lang === 'fr' ? 'Valeur totale' : 'Total value', fmtMUSD(s3.total_export_value_musd)]);
    if (s3.new_market_penetration) rows3.push([lang === 'fr' ? 'Nouveaux marchés' : 'New markets', s3.new_market_penetration]);
  }
  if (s5) {
    if (s5.export_growth_percent) rows5.push([lang === 'fr' ? 'Croissance exports' : 'Export growth', `+${fmtPct(s5.export_growth_percent)}`]);
    if (s5.import_substitution_percent) rows5.push([lang === 'fr' ? 'Substitution totale' : 'Total substitution', fmtPct(s5.import_substitution_percent)]);
    if (s5.total_savings_musd) rows5.push([lang === 'fr' ? 'Économies totales' : 'Total savings', fmtMUSD(s5.total_savings_musd)]);
    if (s5.new_jobs_created) rows5.push([lang === 'fr' ? 'Emplois totaux' : 'Total jobs', s5.new_jobs_created.toLocaleString()]);
    if (s5.afcfta_market_share_percent) rows5.push(['AfCFTA %', fmtPct(s5.afcfta_market_share_percent)]);
    if (s5.afcfta_share_percent) rows5.push(['AfCFTA %', fmtPct(s5.afcfta_share_percent)]);
    if (s5.total_export_value_musd) rows5.push([lang === 'fr' ? 'Valeur totale' : 'Total value', fmtMUSD(s5.total_export_value_musd)]);
  }

  return (
    <div className="afcfta-card" style={{ padding: '18px 22px' }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
        <TrendingUp style={{ width: 16, height: 16, color: 'var(--green)' }} />
        {lang === 'fr' ? 'Résultats attendus' : 'Expected results'}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {rows3.length > 0 && (
          <div style={{ background: 'var(--afcfta-bg)', borderRadius: 8, padding: '12px 14px' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--green)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ background: 'var(--green)', color: '#fff', borderRadius: 4, padding: '1px 7px', fontSize: 10 }}>3</span>
              {label3}
            </div>
            {rows3.map(([k, v], i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                <span style={{ color: 'var(--afcfta-muted)' }}>{k}</span>
                <span style={{ fontWeight: 700, color: 'var(--text)' }}>{v}</span>
              </div>
            ))}
            {s3?.key_milestones?.length > 0 && (
              <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--afcfta-border)' }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--afcfta-muted)', marginBottom: 4 }}>
                  {lang === 'fr' ? 'Jalons' : 'Milestones'}
                </div>
                {s3.key_milestones.map((m, i) => (
                  <div key={i} style={{ fontSize: 11, color: 'var(--text)', marginBottom: 2 }}>• {m}</div>
                ))}
              </div>
            )}
          </div>
        )}
        {rows5.length > 0 && (
          <div style={{ background: 'var(--afcfta-bg)', borderRadius: 8, padding: '12px 14px' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#4f8ef7', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ background: '#4f8ef7', color: '#fff', borderRadius: 4, padding: '1px 7px', fontSize: 10 }}>5</span>
              {label5}
            </div>
            {rows5.map(([k, v], i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                <span style={{ color: 'var(--afcfta-muted)' }}>{k}</span>
                <span style={{ fontWeight: 700, color: 'var(--text)' }}>{v}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ── Summary KPI Strip ─────────────────────────────────────────────────────────
const SummaryStrip = ({ data, mode, lang }) => {
  const opps = data?.opportunities || [];
  if (!opps.length) return null;

  const totalValue = opps.reduce((sum, o) => {
    const v = mode === 'export'
      ? (o.potentialTradeValue || o.potential_value_musd || o.potential_trade_value || 0)
      : mode === 'import'
      ? (o.substitutionPotential || o.substitution_potential_musd || o.currentImportValue || 0)
      : (o.potentialTradeValue || o.potential_value_musd || 0);
    return sum + Number(v);
  }, 0);

  const topSectors = data?.summary?.top_sectors || [];
  const quality = data?.summary?.data_quality || 'verified';

  const kpis = [
    {
      icon: Target,
      label: lang === 'fr' ? 'Opportunités' : 'Opportunities',
      value: opps.length,
      color: 'var(--terra)',
    },
    {
      icon: DollarSign,
      label: lang === 'fr' ? 'Potentiel total' : 'Total potential',
      value: fmtMUSD(totalValue),
      color: 'var(--green)',
    },
    {
      icon: quality === 'verified' ? CheckCircle : AlertTriangle,
      label: lang === 'fr' ? 'Qualité données' : 'Data quality',
      value: quality === 'verified'
        ? (lang === 'fr' ? 'Vérifiées' : 'Verified')
        : quality === 'estimated'
        ? (lang === 'fr' ? 'Estimations' : 'Estimated')
        : 'Mixed',
      color: quality === 'verified' ? 'var(--green)' : 'var(--gold)',
    },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 4 }}>
      {kpis.map(({ icon: Icon, label, value, color }) => (
        <div key={label} className="afcfta-kpiCard" style={{ padding: '14px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 8,
              background: `${color}22`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Icon style={{ width: 18, height: 18, color }} />
            </div>
            <span className="afcfta-kpiCard-title">{label}</span>
          </div>
          <div className="afcfta-kpiCard-value" style={{ color }}>
            {value}
          </div>
        </div>
      ))}
      {topSectors.length > 0 && (
        <div style={{ gridColumn: '1 / -1', display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--afcfta-muted)', fontWeight: 600 }}>
            {lang === 'fr' ? 'Secteurs prioritaires' : 'Priority sectors'}:
          </span>
          {topSectors.map((s, i) => (
            <span key={i} style={{
              fontSize: 11,
              background: 'rgba(212,137,26,0.12)',
              color: 'var(--gold)',
              borderRadius: 4,
              padding: '2px 8px',
              border: '1px solid rgba(212,137,26,0.22)',
            }}>
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Main Component ────────────────────────────────────────────────────────────
export default function AIAnalysis({ language = 'fr' }) {
  const { i18n } = useTranslation();
  const lang = i18n.language || language;

  const [mode, setMode] = useState('export');
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [aiHealthy, setAiHealthy] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);

  const txt = {
    fr: {
      title: 'Analyse IA des Opportunités',
      subtitle: 'Propulsé par Claude AI — Sources OEC, UN Comtrade, IMF, UNCTAD',
      selectCountry: 'Sélectionnez un pays',
      analyze: 'Analyser avec Claude',
      exportMode: 'Export',
      importMode: 'Import',
      industrialMode: 'Industriel',
      loading: 'Analyse Claude en cours…',
      steps: [
        'Synchronisation données ZLECAf…',
        'Analyse flux commerciaux IMF 2024…',
        'Extraction patterns OEC / UN Comtrade…',
        'Calcul hiérarchie SH2/SH4/SH6…',
        'Évaluation compétitivité tarifaire…',
        'Cartographie des opportunités…',
      ],
      noData: 'Sélectionnez un pays pour lancer l\'analyse Claude',
      aiReady: 'Claude opérationnel',
      aiNotReady: 'ANTHROPIC_API_KEY non configurée',
      sources: 'Sources',
    },
    en: {
      title: 'AI Trade Opportunity Analysis',
      subtitle: 'Powered by Claude AI — OEC, UN Comtrade, IMF, UNCTAD sources',
      selectCountry: 'Select a country',
      analyze: 'Analyze with Claude',
      exportMode: 'Export',
      importMode: 'Import',
      industrialMode: 'Industrial',
      loading: 'Claude analysis in progress…',
      steps: [
        'Synchronizing AfCFTA data…',
        'Analyzing IMF 2024 trade flows…',
        'Extracting OEC / UN Comtrade patterns…',
        'Computing SH2/SH4/SH6 hierarchy…',
        'Evaluating tariff competitiveness…',
        'Mapping opportunities…',
      ],
      noData: 'Select a country to start Claude analysis',
      aiReady: 'Claude operational',
      aiNotReady: 'ANTHROPIC_API_KEY not set',
      sources: 'Sources',
    },
  }[lang] || {
    title: 'Analyse IA', subtitle: '', selectCountry: 'Pays', analyze: 'Analyser',
    exportMode: 'Export', importMode: 'Import', industrialMode: 'Industriel',
    loading: '…', steps: ['…'], noData: '—', aiReady: '✓', aiNotReady: '✗', sources: 'Sources',
  };

  // Rotate loading step
  useEffect(() => {
    if (!loading) return;
    const id = setInterval(() => setLoadingStep(s => (s + 1) % txt.steps.length), 2000);
    return () => clearInterval(id);
  }, [loading, txt.steps.length]);

  // Health check
  useEffect(() => {
    axios.get(`${API}/ai/health`)
      .then(r => setAiHealthy(r.data.status === 'operational'))
      .catch(() => setAiHealthy(false));
  }, []);

  // Countries
  useEffect(() => {
    axios.get(`${API}/substitution/countries?lang=${lang}`)
      .then(r => setCountries(r.data.countries || []))
      .catch(() => {});
  }, [lang]);

  const runAnalysis = useCallback(async () => {
    if (!selectedCountry) return;
    setLoading(true);
    setError(null);
    setData(null);
    setLoadingStep(0);

    const countryObj = countries.find(c => c.iso3 === selectedCountry);
    const countryName = countryObj?.name || selectedCountry;

    try {
      const res = await axios.get(
        `${API}/ai/opportunities/${encodeURIComponent(countryName)}`,
        { params: { mode, lang } }
      );
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || (lang === 'fr' ? 'Erreur lors de l\'analyse' : 'Analysis error'));
    } finally {
      setLoading(false);
    }
  }, [selectedCountry, mode, lang, countries]);

  // ── Render ──
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>

      {/* Header */}
      <div style={{ textAlign: 'center', paddingBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 6 }}>
          <Sparkles style={{ width: 24, height: 24, color: 'var(--gold)' }} />
          <h2 style={{
            fontSize: 'clamp(18px,2.2vw,26px)',
            fontWeight: 800,
            color: 'var(--text)',
            letterSpacing: '-0.01em',
          }}>
            {txt.title}
          </h2>
        </div>
        <p style={{ fontSize: 13, color: 'var(--afcfta-muted)' }}>{txt.subtitle}</p>

        {/* AI status badge */}
        {aiHealthy !== null && (
          <div style={{ marginTop: 8 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              fontSize: 11, fontWeight: 600,
              padding: '3px 10px', borderRadius: 20,
              background: aiHealthy ? 'rgba(26,122,74,0.12)' : 'rgba(200,16,46,0.10)',
              color: aiHealthy ? 'var(--green)' : '#e05070',
              border: `1px solid ${aiHealthy ? 'rgba(26,122,74,0.22)' : 'rgba(200,16,46,0.20)'}`,
            }}>
              {aiHealthy
                ? <><CheckCircle style={{ width: 11, height: 11 }} />{txt.aiReady}</>
                : <><AlertCircle style={{ width: 11, height: 11 }} />{txt.aiNotReady}</>}
            </span>
          </div>
        )}
      </div>

      {/* Controls card */}
      <div className="afcfta-card" style={{ padding: '18px 22px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Mode tabs */}
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--afcfta-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {lang === 'fr' ? 'Mode d\'analyse' : 'Analysis mode'}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                { value: 'export', label: txt.exportMode, icon: TrendingUp },
                { value: 'import', label: txt.importMode, icon: TrendingDown },
                { value: 'industrial', label: txt.industrialMode, icon: Factory },
              ].map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  onClick={() => setMode(value)}
                  style={{
                    flex: 1,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                    padding: '9px 12px',
                    borderRadius: 8,
                    fontSize: 13, fontWeight: mode === value ? 700 : 500,
                    border: mode === value
                      ? '1px solid var(--gold)'
                      : '1px solid var(--afcfta-border)',
                    background: mode === value
                      ? 'rgba(212,137,26,0.10)'
                      : 'var(--afcfta-bg)',
                    color: mode === value ? 'var(--gold)' : 'var(--afcfta-muted)',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <Icon style={{ width: 14, height: 14 }} />
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Country + Analyze */}
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--afcfta-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {txt.selectCountry}
              </div>
              <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger style={{ background: 'var(--afcfta-bg)', border: '1px solid var(--afcfta-border)', color: 'var(--text)' }}>
                  <SelectValue placeholder={txt.selectCountry} />
                </SelectTrigger>
                <SelectContent>
                  {countries.map(c => (
                    <SelectItem key={c.iso3} value={c.iso3}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <button
              onClick={runAnalysis}
              disabled={!selectedCountry || loading}
              style={{
                display: 'flex', alignItems: 'center', gap: 7,
                padding: '10px 20px',
                borderRadius: 8,
                fontSize: 13, fontWeight: 700,
                border: 'none', cursor: (!selectedCountry || loading) ? 'not-allowed' : 'pointer',
                background: (!selectedCountry || loading)
                  ? 'rgba(212,137,26,0.3)'
                  : 'var(--gold)',
                color: '#fff',
                opacity: (!selectedCountry || loading) ? 0.65 : 1,
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              }}
            >
              {loading
                ? <Loader2 style={{ width: 14, height: 14, animation: 'spin 1s linear infinite' }} />
                : <Sparkles style={{ width: 14, height: 14 }} />}
              {txt.analyze}
            </button>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="afcfta-card" style={{
          padding: '48px 24px',
          textAlign: 'center',
          background: 'linear-gradient(135deg, rgba(212,137,26,0.04), rgba(26,122,74,0.04))',
        }}>
          <div style={{ position: 'relative', width: 64, height: 64, margin: '0 auto 20px' }}>
            <div style={{
              position: 'absolute', inset: 0,
              border: '3px solid rgba(212,137,26,0.15)',
              borderRadius: '50%',
            }} />
            <div style={{
              position: 'absolute', inset: 0,
              border: '3px solid transparent',
              borderTopColor: 'var(--gold)',
              borderRadius: '50%',
              animation: 'spin 0.9s linear infinite',
            }} />
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Sparkles style={{ width: 24, height: 24, color: 'var(--gold)' }} />
            </div>
          </div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', marginBottom: 6 }}>
            {txt.loading}
          </div>
          <div style={{ fontSize: 13, color: 'var(--gold)', fontWeight: 500 }}>
            {txt.steps[loadingStep]}
          </div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="afcfta-card" style={{
          padding: '24px',
          background: 'rgba(200,16,46,0.06)',
          borderLeft: '3px solid rgba(200,16,46,0.4)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertCircle style={{ width: 18, height: 18, color: '#e05070', flexShrink: 0 }} />
            <span style={{ fontSize: 14, color: 'var(--text)' }}>{error}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {!loading && !error && data && (
        <>
          <SummaryStrip data={data} mode={mode} lang={lang} />

          {/* Sankey */}
          {data.opportunities?.length > 0 && (
            <TradeSankeyDiagram
              opportunities={data.opportunities.map(o => ({ ...o, country: data.country, exportingCountry: data.country }))}
              mode={mode}
              language={lang}
            />
          )}

          <ExpectedResults data={data.expected_results} mode={mode} lang={lang} />

          {/* Opportunity cards grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
            {(data.opportunities || []).map((opp, i) => (
              <OpportunityCard key={i} opp={opp} mode={mode} lang={lang} index={i} />
            ))}
          </div>

          {/* Sources footer */}
          {data.sources && (
            <div style={{
              padding: '12px 18px',
              borderRadius: 8,
              background: 'var(--afcfta-bg)',
              border: '1px solid var(--afcfta-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 8,
              fontSize: 12,
              color: 'var(--afcfta-muted)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Info style={{ width: 13, height: 13 }} />
                <span><strong>{txt.sources}:</strong> {data.sources.join(' · ')}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {data.data_freshness && <DataFreshnessIndicator freshness={data.data_freshness} language={lang} />}
                {data.generated_by && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Zap style={{ width: 11, height: 11 }} />
                    {data.generated_by}
                  </span>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!loading && !error && !data && (
        <div style={{
          textAlign: 'center',
          padding: '64px 24px',
          color: 'var(--afcfta-muted)',
        }}>
          <Sparkles style={{ width: 48, height: 48, margin: '0 auto 16px', opacity: 0.25, color: 'var(--gold)' }} />
          <p style={{ fontSize: 14 }}>{txt.noData}</p>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
