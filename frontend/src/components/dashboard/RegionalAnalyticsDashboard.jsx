/**
 * RegionalAnalyticsDashboard
 * ===========================
 * Interactive comparative analysis dashboard for all African regional blocs.
 * Shows investment heatmaps, trade corridors, and real-time regional metrics.
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL
  ? `${process.env.REACT_APP_BACKEND_URL}/api`
  : '/api';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function BlocCard({ bloc }) {
  const tierColors = {
    tier1: { bg: '#D1FAE5', border: '#10B981', text: '#065F46', label: 'Tier 1 – Excellent' },
    tier2: { bg: '#DBEAFE', border: '#3B82F6', text: '#1E40AF', label: 'Tier 2 – Good' },
    tier3: { bg: '#FEF3C7', border: '#F59E0B', text: '#92400E', label: 'Tier 3 – Developing' },
  };
  const tier = tierColors[bloc.opportunity_tier] || tierColors.tier3;

  return (
    <div style={{
      background: tier.bg,
      border: `2px solid ${tier.border}`,
      borderRadius: '12px',
      padding: '1rem 1.25rem',
      transition: 'transform 0.15s, box-shadow 0.15s',
    }}
      onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'none'}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3 style={{ margin: 0, color: tier.text, fontSize: '1.1rem', fontWeight: 700 }}>
            {bloc.bloc}
          </h3>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: tier.text, opacity: 0.8 }}>
            {bloc.full_name}
          </p>
        </div>
        <span style={{
          background: tier.border,
          color: '#fff',
          borderRadius: '6px',
          padding: '0.15rem 0.5rem',
          fontSize: '0.7rem',
          fontWeight: 700,
        }}>
          {tier.label}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.75rem' }}>
        <Metric label="Investment Score" value={`${(bloc.investment_score * 100).toFixed(0)}%`} />
        <Metric label="Trade Integration" value={`${bloc.trade_integration?.toFixed(1)}%`} />
        <Metric label="GDP (bn USD)" value={`$${bloc.gdp_bn_usd?.toLocaleString()}`} />
        <Metric label="Countries" value={bloc.country_count} />
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: '0.65rem', color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </div>
      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1A365D' }}>
        {value ?? 'N/A'}
      </div>
    </div>
  );
}

function CorridorRow({ corridor }) {
  const growthColor = corridor.growth_pct > 10 ? '#10B981' : corridor.growth_pct > 5 ? '#F59E0B' : '#6B7280';
  return (
    <tr style={{ borderBottom: '1px solid #F1F5F9' }}>
      <td style={{ padding: '0.6rem 0.5rem', fontWeight: 600 }}>
        {corridor.origin} → {corridor.destination}
      </td>
      <td style={{ padding: '0.6rem 0.5rem', textAlign: 'right' }}>
        ${corridor.trade_value_bn?.toFixed(1)}bn
      </td>
      <td style={{ padding: '0.6rem 0.5rem', textAlign: 'right', color: growthColor, fontWeight: 700 }}>
        +{corridor.growth_pct?.toFixed(1)}%
      </td>
      <td style={{ padding: '0.6rem 0.5rem', fontSize: '0.75rem', color: '#6B7280' }}>
        {(corridor.key_products || []).slice(0, 2).join(', ')}
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function RegionalAnalyticsDashboard({ language = 'fr' }) {
  const [heatmap, setHeatmap]     = useState([]);
  const [corridors, setCorridors] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [selectedBloc, setSelectedBloc] = useState(null);
  const [blocDetail, setBlocDetail]     = useState(null);
  const [activeTab, setActiveTab] = useState('heatmap');
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);

  const labels = {
    fr: {
      title: 'Analyse Régionale Comparative',
      heatmap: 'Carte des Opportunités',
      corridors: 'Corridors Commerciaux',
      compare: 'Comparaison des Blocs',
      exportBtn: 'Exporter (Excel)',
      loading: 'Chargement…',
    },
    en: {
      title: 'Regional Comparative Analysis',
      heatmap: 'Investment Heatmap',
      corridors: 'Trade Corridors',
      compare: 'Bloc Comparison',
      exportBtn: 'Export (Excel)',
      loading: 'Loading…',
    },
  };
  const t = labels[language] || labels.en;

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [hmRes, corrRes, cmpRes] = await Promise.all([
        axios.get(`${API}/regional-analytics/heatmap`),
        axios.get(`${API}/regional-analytics/corridors`),
        axios.get(`${API}/regional-analytics/compare`),
      ]);
      setHeatmap(hmRes.data?.heatmap || []);
      setCorridors(corrRes.data?.corridors || []);
      setComparison(cmpRes.data || null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const fetchBlocDetail = useCallback(async (bloc) => {
    if (selectedBloc === bloc) { setSelectedBloc(null); setBlocDetail(null); return; }
    setSelectedBloc(bloc);
    try {
      const { data } = await axios.get(`${API}/regional-analytics/blocs/${bloc}`);
      setBlocDetail(data);
    } catch {
      setBlocDetail(null);
    }
  }, [selectedBloc]);

  const handleExport = useCallback(async (format = 'excel') => {
    try {
      const response = await axios.get(`${API}/regional-analytics/export`, {
        params: { format },
        responseType: 'blob',
      });
      const url = URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `afcfta_analysis.${format === 'excel' ? 'xlsx' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div style={{ padding: 'var(--spacing-md, 1rem)', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <h2 style={{ margin: 0, color: '#1A365D', fontSize: 'var(--font-size-2xl, 1.5rem)' }}>
          🌍 {t.title}
        </h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => handleExport('excel')}
            style={{ background: '#10B981', color: '#fff', border: 'none', borderRadius: '8px', padding: '0.5rem 1rem', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}
          >
            📊 {t.exportBtn}
          </button>
          <button
            onClick={() => handleExport('pdf')}
            style={{ background: '#3B82F6', color: '#fff', border: 'none', borderRadius: '8px', padding: '0.5rem 1rem', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}
          >
            📄 PDF
          </button>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="nav-tabs" style={{ marginBottom: '1.5rem' }}>
        {[['heatmap', t.heatmap], ['corridors', t.corridors], ['compare', t.compare]].map(([id, label]) => (
          <button
            key={id}
            className={`nav-tab${activeTab === id ? ' active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#6B7280' }}>
          ⏳ {t.loading}
        </div>
      )}

      {error && (
        <div style={{ background: '#FEE2E2', color: '#991B1B', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Heatmap tab */}
      {!loading && activeTab === 'heatmap' && (
        <div>
          <div className="dashboard-grid">
            {heatmap.map((bloc) => (
              <div
                key={bloc.bloc}
                style={{ cursor: 'pointer' }}
                onClick={() => fetchBlocDetail(bloc.bloc)}
              >
                <BlocCard bloc={bloc} />
              </div>
            ))}
          </div>

          {/* Bloc detail panel */}
          {blocDetail && (
            <div style={{
              marginTop: '1.5rem',
              background: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '12px',
              padding: '1.25rem',
            }}>
              <h3 style={{ color: '#1A365D', marginBottom: '1rem' }}>
                {blocDetail.full_name} ({blocDetail.bloc})
              </h3>
              <div className="kpi-grid">
                <Metric label="Member Countries" value={blocDetail.member_count} />
                <Metric label="GDP (bn USD)" value={`$${blocDetail.gdp_bn_usd}`} />
                <Metric label="Population (mn)" value={blocDetail.population_mn} />
                <Metric label="Intra-Trade" value={`${blocDetail.intra_trade_pct}%`} />
              </div>
              <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#6B7280' }}>
                Headquarters: {blocDetail.headquarters} · Established: {blocDetail.established}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Corridors tab */}
      {!loading && activeTab === 'corridors' && (
        <div style={{ overflowX: 'auto' }}>
          <table
            className="mobile-optimized-table"
            style={{ width: '100%', borderCollapse: 'collapse', background: '#fff', borderRadius: '10px', overflow: 'hidden' }}
          >
            <thead>
              <tr style={{ background: '#1A365D', color: '#fff' }}>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Corridor</th>
                <th style={{ padding: '0.75rem', textAlign: 'right' }}>Trade Value</th>
                <th style={{ padding: '0.75rem', textAlign: 'right' }}>Growth</th>
                <th style={{ padding: '0.75rem', textAlign: 'left' }}>Key Products</th>
              </tr>
            </thead>
            <tbody>
              {corridors.map((c, i) => (
                <CorridorRow key={i} corridor={c} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Comparison tab */}
      {!loading && activeTab === 'compare' && comparison && (
        <div>
          {Object.entries(comparison.rankings || {}).map(([metric, ranking]) => (
            <div key={metric} style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ color: '#1A365D', textTransform: 'capitalize', marginBottom: '0.75rem' }}>
                {metric.replace(/_/g, ' ')}
              </h3>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {ranking.map((entry) => (
                  <div
                    key={entry.bloc}
                    style={{
                      background: entry.rank === 1 ? '#1A365D' : '#F1F5F9',
                      color: entry.rank === 1 ? '#fff' : '#2D3748',
                      borderRadius: '8px',
                      padding: '0.5rem 0.9rem',
                      fontSize: '0.8rem',
                      fontWeight: entry.rank === 1 ? 700 : 500,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                    }}
                  >
                    <span style={{ opacity: 0.7 }}>#{entry.rank}</span>
                    <span>{entry.bloc}</span>
                    <span style={{ fontWeight: 700 }}>{entry.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
