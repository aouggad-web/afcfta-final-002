/**
 * Strategic Flows — sous-module « flux stratégiques » (intelligence industrielle)
 * ------------------------------------------------------------------------------
 * Reproduit la logique de l'app de référence : une capacité de production avérée
 * (champions industriels + projets structurants) fait d'un produit une
 * opportunité d'export sous la ZLECAf, même quand les flux actuels sont modestes.
 *
 * Consomme GET /api/strategic/flows/{iso3} et affiche :
 *  - une vue agrégée (flux identifiés, potentiel total, partenaires & commodités
 *    prioritaires) ;
 *  - une carte de flux stratégique PAR PRODUIT (rationale, intrant -> extrant,
 *    avantage ZLECAf, règles d'origine, potentiel), listant tous les marchés
 *    africains importateurs avec leur volume d'import réel — au lieu d'une
 *    carte dupliquée par (produit × marché).
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import {
  Loader2, AlertCircle, TrendingUp, MapPin, ArrowRight, Factory,
  ShieldCheck, Percent, Package, Sparkles,
} from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const T = {
  fr: {
    title: 'Flux stratégiques',
    subtitle: "Opportunités d'export pilotées par la capacité industrielle et débloquées par la ZLECAf",
    selectCountry: 'Sélectionnez un pays',
    noData: 'Sélectionnez un pays pour lancer l\'analyse',
    loading: 'Analyse des capacités industrielles…',
    identifiedFlows: 'Flux identifiés',
    totalPotential: 'Potentiel total',
    topPartners: 'Partenaires prioritaires',
    priorityCommodities: 'Commodités prioritaires',
    flows: 'Nombre de flux',
    rationale: 'Rationale stratégique',
    transformation: 'Stratégie de transformation industrielle',
    inputSource: 'Intrant',
    outputTarget: 'Extrant (capacité)',
    advantage: 'Avantage économique ZLECAf',
    tariffEdge: 'Écart tarifaire ZLECAf',
    leadTime: 'Délai logistique',
    priceComp: 'Compétitivité prix',
    roo: "Règles d'origine",
    potential: 'Potentiel',
    days: 'j',
    mfnPref: 'NPF → Taux préférentiel ZLECAf',
    estimate: 'estimation',
    emerging: 'Capacité à venir',
    operational: 'Opérationnel',
    noFlows: 'Aucun flux stratégique identifié pour ce pays.',
    discovered: 'Découverte UNIDO',
    capacityEvidence: 'Capacité manufacturière (UNIDO)',
    valueAdded: 'valeur ajoutée',
    importMarkets: "Marchés africains importateurs",
    imports: 'importe',
    priorityMarkets: 'Marchés prioritaires',
    markets: 'marchés',
  },
  en: {
    title: 'Strategic Flows',
    subtitle: 'Export opportunities driven by industrial capacity and unlocked by AfCFTA',
    selectCountry: 'Select a country',
    noData: 'Select a country to start the analysis',
    loading: 'Analysing industrial capacities…',
    identifiedFlows: 'Identified flows',
    totalPotential: 'Total potential',
    topPartners: 'Top partners',
    priorityCommodities: 'Priority commodities',
    flows: 'Number of flows',
    rationale: 'Strategic rationale',
    transformation: 'Industrial transformation strategy',
    inputSource: 'Input',
    outputTarget: 'Output (capacity)',
    advantage: 'AfCFTA economic advantage',
    tariffEdge: 'AfCFTA tariff edge',
    leadTime: 'Lead time',
    priceComp: 'Price competitiveness',
    roo: 'Rules of origin',
    potential: 'Potential',
    days: 'd',
    mfnPref: 'MFN → AfCFTA preferential rate',
    estimate: 'estimate',
    emerging: 'Upcoming capacity',
    operational: 'Operational',
    noFlows: 'No strategic flow identified for this country.',
    discovered: 'UNIDO discovery',
    capacityEvidence: 'Manufacturing capacity (UNIDO)',
    valueAdded: 'value added',
    importMarkets: 'African importing markets',
    imports: 'imports',
    priorityMarkets: 'Priority markets',
    markets: 'markets',
  },
};

// Même convention d'affichage que le reste du module Opportunités
// (formatValue de SubstitutionAnalysis) : $B / $M / $K.
const fmtUsd = (v) => {
  const n = Number(v) || 0;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n.toLocaleString()}`;
};

// Volume d'import compact pour la liste des marchés.
const fmtImport = (v) => {
  const n = Number(v) || 0;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n.toLocaleString()}`;
};

const fmtQty = (cap) => {
  if (!cap || cap.value == null) return null;
  const v = Number(cap.value);
  const unit = cap.unit || '';
  const disp = v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `${(v / 1e3).toFixed(0)}K` : `${v}`;
  return `${disp} ${unit}`.trim();
};

function SignalBadge({ signal, emerging, t }) {
  const isGrowth = signal === 'High Growth';
  const bg = isGrowth ? 'rgba(5,150,105,0.14)' : 'rgba(100,116,139,0.14)';
  const color = isGrowth ? '#059669' : 'var(--afcfta-muted)';
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 9px',
        borderRadius: 999, background: bg, color, fontSize: 11, fontWeight: 700,
      }}>
        <TrendingUp style={{ width: 12, height: 12 }} />
        {signal || '—'}
      </span>
      <span style={{
        padding: '3px 8px', borderRadius: 999, fontSize: 10, fontWeight: 600,
        background: emerging ? 'rgba(202,138,4,0.14)' : 'rgba(37,99,235,0.12)',
        color: emerging ? '#ca8a04' : '#2563eb',
      }}>
        {emerging ? t.emerging : t.operational}
      </span>
    </span>
  );
}

function MarketList({ markets, t }) {
  const rows = markets || [];
  if (rows.length === 0) return null;
  const max = Math.max(...rows.map((m) => m.import_usd || 0), 1);
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 700, color: 'var(--afcfta-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
        <MapPin style={{ width: 13, height: 13 }} />{t.importMarkets}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }} data-testid="flow-market-list">
        {rows.map((m) => (
          <div key={m.iso3} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ flex: '0 0 34%', display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 13, fontWeight: 600, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <MapPin style={{ width: 12, height: 12, color: '#059669', flexShrink: 0 }} />{m.name}
            </span>
            <span style={{ flex: 1, height: 6, borderRadius: 3, background: 'var(--afcfta-bg)' }}>
              <span style={{ display: 'block', height: '100%', width: `${Math.max(5, ((m.import_usd || 0) / max) * 100)}%`, borderRadius: 3, background: 'linear-gradient(90deg,#059669,#0891b2)' }} />
            </span>
            <span style={{ flex: '0 0 auto', fontSize: 12, color: 'var(--afcfta-muted)', whiteSpace: 'nowrap' }}>
              {t.imports} <strong style={{ color: 'var(--text)' }}>{fmtImport(m.import_usd)}</strong>
              {m.lead_time_days != null && <span> · {m.lead_time_days} {t.days}</span>}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AdvantageChip({ icon: Icon, label, value, sub }) {
  if (value == null || value === '') return null;
  return (
    <div style={{
      flex: '1 1 120px', minWidth: 110, padding: '10px 12px', borderRadius: 10,
      background: 'var(--afcfta-bg)', border: '1px solid var(--afcfta-border)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--afcfta-muted)', fontSize: 11, marginBottom: 3 }}>
        <Icon style={{ width: 13, height: 13 }} />
        {label}
      </div>
      <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text)' }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: 'var(--afcfta-muted)' }}>{sub}</div>}
    </div>
  );
}

function FlowCard({ flow, t }) {
  const tr = flow.transformation || {};
  const adv = flow.advantage || {};
  const edge = adv.afcfta_tariff_edge || {};
  const roo = adv.rules_of_origin || {};
  const inQty = fmtQty(tr.input_target);
  const outQty = fmtQty(tr.output_target);

  return (
    <div style={{
      border: '1px solid var(--afcfta-border)', borderRadius: 14, background: 'var(--afcfta-card)',
      padding: 18, display: 'flex', flexDirection: 'column', gap: 14,
    }} data-testid="strategic-flow-card">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <code style={{ fontSize: 12, color: 'var(--afcfta-muted)', fontWeight: 700 }}>{flow.hs_code}</code>
            <SignalBadge signal={flow.signal} emerging={flow.is_emerging} t={t} />
            {flow.discovery_tier === 'unido' && (
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px',
                borderRadius: 999, background: 'rgba(147,51,234,0.12)', color: '#9333ea',
                fontSize: 10, fontWeight: 700,
              }}>
                <Sparkles style={{ width: 11, height: 11 }} />{t.discovered}
              </span>
            )}
          </div>
          <div style={{ fontSize: 17, fontWeight: 800, color: 'var(--text)' }}>{flow.product}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11, color: 'var(--afcfta-muted)' }}>{t.potential}</div>
          <div style={{ fontSize: 22, fontWeight: 900, color: '#059669' }}>{fmtUsd(flow.potential_usd)}</div>
        </div>
      </div>

      {/* Origine + nombre de marchés */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, flexWrap: 'wrap' }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontWeight: 700, color: 'var(--text)' }}>
          <MapPin style={{ width: 14, height: 14, color: 'var(--gold)' }} />{flow.from?.name}
        </span>
        <ArrowRight style={{ width: 16, height: 16, color: 'var(--afcfta-muted)' }} />
        <span style={{ fontSize: 13, color: 'var(--afcfta-muted)' }}>
          {(flow.markets || []).length} {t.markets}
        </span>
      </div>

      {/* Rationale */}
      {flow.strategic_rationale && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--afcfta-muted)', textTransform: 'uppercase', marginBottom: 4 }}>{t.rationale}</div>
          <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.5 }}>{flow.strategic_rationale}</div>
        </div>
      )}

      {/* Transformation */}
      {(tr.champion || tr.process) && (
        <div style={{ padding: 12, borderRadius: 10, background: 'var(--afcfta-bg)', border: '1px solid var(--afcfta-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 700, color: 'var(--afcfta-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
            <Factory style={{ width: 13, height: 13 }} />{t.transformation}
            {tr.champion && <span style={{ fontWeight: 600, textTransform: 'none' }}>· {tr.champion}</span>}
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
            {tr.input_source && (
              <div style={{ flex: '1 1 160px' }}>
                <div style={{ fontSize: 10, color: 'var(--afcfta-muted)' }}>{t.inputSource}</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
                  {tr.input_source}
                  <ArrowRight style={{ width: 12, height: 12, color: 'var(--afcfta-muted)', margin: '0 5px', verticalAlign: 'middle' }} />
                  <span style={{ color: '#059669' }}>{flow.product}</span>
                </div>
                {inQty && <div style={{ fontSize: 11, color: 'var(--afcfta-muted)' }}>{inQty}</div>}
              </div>
            )}
            {(tr.output_target?.product || outQty) && (
              <div style={{ flex: '1 1 160px' }}>
                <div style={{ fontSize: 10, color: 'var(--afcfta-muted)' }}>{t.outputTarget}</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{tr.output_target?.product || '—'}</div>
                {outQty && <div style={{ fontSize: 11, color: 'var(--afcfta-muted)' }}>{outQty}</div>}
              </div>
            )}
          </div>
          {tr.process && <div style={{ fontSize: 12, fontStyle: 'italic', color: 'var(--afcfta-muted)', lineHeight: 1.5 }}>« {tr.process} »</div>}
          {flow.capacity_evidence?.value_added_usd != null && (
            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#9333ea', fontWeight: 600 }}>
              <Factory style={{ width: 12, height: 12 }} />
              {t.capacityEvidence} · {flow.capacity_evidence.isic_label} : {fmtUsd(flow.capacity_evidence.value_added_usd)} {t.valueAdded}
            </div>
          )}
        </div>
      )}

      {/* Marchés africains importateurs (volume d'import réel) */}
      <MarketList markets={flow.markets} t={t} />

      {/* Advantage chips */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <AdvantageChip
          icon={Percent}
          label={t.tariffEdge}
          value={edge.edge_pct != null ? `-${edge.edge_pct}%` : null}
          sub={t.mfnPref}
        />
        <AdvantageChip icon={Sparkles} label={t.priceComp} value={adv.price_competitiveness} />
        <AdvantageChip icon={ShieldCheck} label={t.roo} value={roo.rule_name || roo.rule_type} />
      </div>
    </div>
  );
}

export default function StrategicFlows({ language = 'fr', initialCountry = null }) {
  const { i18n } = useTranslation();
  const lang = (i18n.language || language).startsWith('en') ? 'en' : 'fr';
  const t = T[lang];

  const [countries, setCountries] = useState([]);
  const [selected, setSelected] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get(`${API}/substitution/countries?lang=${lang}`);
        setCountries(r.data.countries || []);
      } catch {
        /* liste pays indisponible : le sélecteur restera vide */
      }
    })();
  }, [lang]);

  useEffect(() => {
    if (initialCountry?.iso3) setSelected(initialCountry.iso3);
  }, [initialCountry]);

  const analyze = useCallback(async (iso3) => {
    if (!iso3) return;
    setLoading(true);
    setError(null);
    try {
      const r = await axios.get(`${API}/strategic/flows/${iso3}?lang=${lang}&limit=40`);
      setData(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || String(e));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [lang]);

  useEffect(() => {
    if (selected) analyze(selected);
  }, [selected, analyze]);

  const summary = data?.summary;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }} data-testid="strategic-flows">
      {/* Header + selector */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 900, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingUp style={{ width: 20, height: 20, color: 'var(--gold)' }} />{t.title}
          </h2>
          <p style={{ fontSize: 13, color: 'var(--afcfta-muted)', marginTop: 2 }}>{t.subtitle}</p>
        </div>
        <div style={{ minWidth: 240 }}>
          <Select value={selected} onValueChange={setSelected}>
            <SelectTrigger data-testid="strategic-country-select"><SelectValue placeholder={t.selectCountry} /></SelectTrigger>
            <SelectContent>
              {countries.map((c) => (
                <SelectItem key={c.iso3} value={c.iso3}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'center', padding: 40, color: 'var(--afcfta-muted)' }}>
          <Loader2 style={{ width: 20, height: 20 }} className="animate-spin" />{t.loading}
        </div>
      )}

      {error && !loading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 16, borderRadius: 10, background: 'rgba(220,38,38,0.08)', color: '#dc2626' }}>
          <AlertCircle style={{ width: 18, height: 18 }} />{error}
        </div>
      )}

      {!selected && !loading && (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--afcfta-muted)' }}>{t.noData}</div>
      )}

      {/* Summary */}
      {summary && !loading && (
        <>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 160px', padding: 16, borderRadius: 12, background: 'var(--afcfta-card)', border: '1px solid var(--afcfta-border)' }}>
              <div style={{ fontSize: 12, color: 'var(--afcfta-muted)' }}>{t.identifiedFlows}</div>
              <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--text)' }}>{summary.identified_flows}</div>
            </div>
            <div style={{ flex: '1 1 160px', padding: 16, borderRadius: 12, background: 'var(--afcfta-card)', border: '1px solid var(--afcfta-border)' }}>
              <div style={{ fontSize: 12, color: 'var(--afcfta-muted)' }}>{t.totalPotential}</div>
              <div style={{ fontSize: 28, fontWeight: 900, color: '#059669' }}>{fmtUsd(summary.total_potential_usd)}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {/* Priority commodities */}
            <div style={{ flex: '1 1 280px', padding: 14, borderRadius: 12, background: 'var(--afcfta-card)', border: '1px solid var(--afcfta-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: 'var(--afcfta-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                <Package style={{ width: 14, height: 14 }} />{t.priorityCommodities}
              </div>
              {(summary.priority_commodities || []).slice(0, 8).map((c, i) => (
                <div key={c.hs_code} style={{ display: 'flex', justifyContent: 'space-between', gap: 8, padding: '5px 0', borderBottom: i < 7 ? '1px solid var(--afcfta-border)' : 'none' }}>
                  <span style={{ fontSize: 12, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <span style={{ color: 'var(--afcfta-muted)', fontWeight: 700, marginRight: 6 }}>{String(i + 1).padStart(2, '0')}</span>{c.product}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--afcfta-muted)', whiteSpace: 'nowrap' }}>{c.market_count} {t.markets}</span>
                </div>
              ))}
            </div>
            {/* Top partners */}
            <div style={{ flex: '1 1 280px', padding: 14, borderRadius: 12, background: 'var(--afcfta-card)', border: '1px solid var(--afcfta-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: 'var(--afcfta-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                <MapPin style={{ width: 14, height: 14 }} />{t.topPartners}
              </div>
              {(summary.top_partners || []).slice(0, 8).map((p, i) => {
                const max = summary.top_partners[0]?.potential_usd || 1;
                return (
                  <div key={p.iso3} style={{ padding: '5px 0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
                      <span style={{ color: 'var(--text)', fontWeight: 600 }}>{p.name}</span>
                      <span style={{ color: 'var(--afcfta-muted)' }}>{fmtUsd(p.potential_usd)}</span>
                    </div>
                    <div style={{ height: 5, borderRadius: 3, background: 'var(--afcfta-bg)' }}>
                      <div style={{ height: '100%', width: `${Math.max(4, (p.potential_usd / max) * 100)}%`, borderRadius: 3, background: 'linear-gradient(90deg,#059669,#0891b2)' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Flow cards */}
          {(data.flows || []).length === 0 ? (
            <div style={{ padding: 30, textAlign: 'center', color: 'var(--afcfta-muted)' }}>{t.noFlows}</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 14 }}>
              {(data.flows || []).map((f, i) => <FlowCard key={`${f.hs_code}-${i}`} flow={f} t={t} />)}
            </div>
          )}
        </>
      )}
    </div>
  );
}
