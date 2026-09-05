/**
 * AIInvestmentDashboard
 * =====================
 * AI-powered investment scoring, recommendations, and risk assessment UI.
 * Integrates with the AfCFTA AI Intelligence Engine backend.
 */

import React, { useState } from 'react';
import { useInvestmentRecommendations, useInvestmentScore } from '../../hooks/useInvestmentRecommendations';

// Colour helpers
const gradeColor = (grade) => {
  if (!grade) return '#6B7280';
  if (grade.startsWith('A')) return '#10B981';
  if (grade.startsWith('B')) return '#3B82F6';
  if (grade.startsWith('C')) return '#F59E0B';
  return '#EF4444';
};

const scoreBar = (score) => (
  <div style={{ background: '#E2E8F0', borderRadius: '4px', height: '8px', width: '100%', overflow: 'hidden' }}>
    <div style={{
      width: `${Math.round(score * 100)}%`,
      height: '100%',
      background: score >= 0.75 ? '#10B981' : score >= 0.60 ? '#3B82F6' : score >= 0.45 ? '#F59E0B' : '#EF4444',
      transition: 'width 0.5s ease',
    }} />
  </div>
);

// ---------------------------------------------------------------------------
// Recommendation Card
// ---------------------------------------------------------------------------
function RecommendationCard({ rec, rank }) {
  const [expanded, setExpanded] = useState(false);
  const score = rec.score || {};

  return (
    <div
      style={{
        background: '#fff',
        border: '1px solid #E2E8F0',
        borderRadius: '12px',
        padding: '1rem 1.25rem',
        cursor: 'pointer',
        transition: 'box-shadow 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.1)'}
      onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
      onClick={() => setExpanded(e => !e)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{
            background: '#1A365D',
            color: '#fff',
            borderRadius: '50%',
            width: '28px',
            height: '28px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: '0.8rem',
            flexShrink: 0,
          }}>
            #{rank}
          </span>
          <div>
            <div style={{ fontWeight: 700, color: '#1A365D' }}>{rec.country}</div>
            <div style={{ fontSize: '0.75rem', color: '#6B7280', textTransform: 'capitalize' }}>
              {rec.sector}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{
            background: gradeColor(score.grade) + '22',
            color: gradeColor(score.grade),
            border: `1.5px solid ${gradeColor(score.grade)}`,
            borderRadius: '6px',
            padding: '0.2rem 0.5rem',
            fontWeight: 700,
            fontSize: '0.85rem',
          }}>
            {score.grade || 'N/A'}
          </span>
          <span style={{ color: '#1A365D', fontWeight: 700, fontSize: '0.9rem' }}>
            {score.overall_score ? `${(score.overall_score * 100).toFixed(0)}%` : '—'}
          </span>
          <span style={{ color: '#94A3B8' }}>{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Score bar */}
      <div style={{ marginTop: '0.6rem' }}>
        {scoreBar(score.overall_score || 0)}
      </div>

      {/* Expanded details */}
      {expanded && (
        <div style={{ marginTop: '1rem', borderTop: '1px solid #F1F5F9', paddingTop: '0.75rem' }}>
          <p style={{ fontSize: '0.85rem', color: '#4A5568', marginBottom: '0.75rem' }}>
            {rec.rationale}
          </p>

          {(rec.key_advantages || []).length > 0 && (
            <div style={{ marginBottom: '0.75rem' }}>
              <strong style={{ fontSize: '0.75rem', color: '#1A365D', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Key Advantages
              </strong>
              <ul style={{ margin: '0.4rem 0 0', paddingLeft: '1.2rem', fontSize: '0.8rem', color: '#4A5568' }}>
                {rec.key_advantages.map((adv, i) => <li key={i}>{adv}</li>)}
              </ul>
            </div>
          )}

          {(score.risk_factors || []).length > 0 && (
            <div>
              <strong style={{ fontSize: '0.75rem', color: '#EF4444', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Risk Factors
              </strong>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.4rem' }}>
                {score.risk_factors.map((r, i) => (
                  <span key={i} style={{
                    background: '#FEE2E2',
                    color: '#991B1B',
                    borderRadius: '6px',
                    padding: '0.15rem 0.5rem',
                    fontSize: '0.7rem',
                    fontWeight: 600,
                  }}>
                    {r.name?.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sector Score Widget
// ---------------------------------------------------------------------------
function SectorScoreWidget({ country, sector }) {
  const { score, loading, error } = useInvestmentScore(country, sector);

  if (loading) return <div style={{ color: '#94A3B8', fontSize: '0.85rem' }}>Calculating…</div>;
  if (error)   return <div style={{ color: '#EF4444', fontSize: '0.85rem' }}>Score unavailable</div>;
  if (!score)  return null;

  return (
    <div style={{ background: '#F8FAFC', borderRadius: '10px', padding: '0.75rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
        <span style={{ fontWeight: 600, color: '#1A365D', textTransform: 'capitalize' }}>{sector}</span>
        <span style={{
          color: gradeColor(score.grade),
          fontWeight: 700,
          fontSize: '1.1rem',
        }}>
          {score.grade}
        </span>
      </div>
      {scoreBar(score.overall_score)}
      <div style={{ fontSize: '0.7rem', color: '#6B7280', marginTop: '0.3rem', textAlign: 'right' }}>
        {(score.overall_score * 100).toFixed(1)}% · {score.recommendation_strength?.replace(/_/g, ' ')}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Dashboard Component
// ---------------------------------------------------------------------------

const SECTORS = ['general', 'agriculture', 'manufacturing', 'ict', 'energy', 'logistics', 'textiles'];

export default function AIInvestmentDashboard({ language = 'fr' }) {
  const [userProfile, setUserProfile] = useState({
    sector: 'general',
    riskTolerance: 'medium',
    preferredRegions: [],
  });
  const [profileDraft, setProfileDraft] = useState(userProfile);
  const [limit, setLimit] = useState(8);
  const [previewCountry, setPreviewCountry] = useState('MAR');

  const { recommendations, loading, error, lastFetched, refresh } =
    useInvestmentRecommendations(userProfile, limit);

  const labels = {
    fr: {
      title: 'Intelligence Investissement IA',
      sector: 'Secteur',
      risk: 'Tolérance au Risque',
      apply: 'Appliquer',
      refresh: 'Actualiser',
      recs: 'Recommandations Personnalisées',
      preview: 'Prévisualisation Pays',
      loading: 'Analyse en cours…',
      noRecs: 'Aucune recommandation disponible',
      lastUpdated: 'Mis à jour :',
    },
    en: {
      title: 'AI Investment Intelligence',
      sector: 'Sector',
      risk: 'Risk Tolerance',
      apply: 'Apply',
      refresh: 'Refresh',
      recs: 'Personalised Recommendations',
      preview: 'Country Preview',
      loading: 'Analysing…',
      noRecs: 'No recommendations available',
      lastUpdated: 'Last updated:',
    },
  };
  const t = labels[language] || labels.en;

  return (
    <div style={{ padding: 'var(--spacing-md, 1rem)', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ color: '#1A365D', marginBottom: '1.5rem' }}>🤖 {t.title}</h2>

      {/* Filter Panel */}
      <div style={{
        background: '#fff',
        border: '1px solid #E2E8F0',
        borderRadius: '12px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        gap: '1rem',
        flexWrap: 'wrap',
        alignItems: 'flex-end',
      }}>
        <div style={{ flex: '1', minWidth: '140px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#4A5568', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
            {t.sector}
          </label>
          <select
            value={profileDraft.sector}
            onChange={e => setProfileDraft(p => ({ ...p, sector: e.target.value }))}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}
          >
            {SECTORS.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
          </select>
        </div>

        <div style={{ flex: '1', minWidth: '140px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#4A5568', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
            {t.risk}
          </label>
          <select
            value={profileDraft.riskTolerance}
            onChange={e => setProfileDraft(p => ({ ...p, riskTolerance: e.target.value }))}
            style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #E2E8F0' }}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        <div style={{ flex: '0 0 auto' }}>
          <button
            onClick={() => { setUserProfile(profileDraft); }}
            style={{ background: '#1A365D', color: '#fff', border: 'none', borderRadius: '8px', padding: '0.55rem 1.25rem', cursor: 'pointer', fontWeight: 600, minHeight: '44px' }}
          >
            {t.apply}
          </button>
        </div>

        <div style={{ flex: '0 0 auto' }}>
          <button
            onClick={refresh}
            style={{ background: '#3B82F6', color: '#fff', border: 'none', borderRadius: '8px', padding: '0.55rem 1rem', cursor: 'pointer', fontWeight: 600, minHeight: '44px' }}
          >
            🔄 {t.refresh}
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: '1.5rem' }}>
        {/* Recommendations list */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, color: '#1A365D' }}>📋 {t.recs}</h3>
            {lastFetched && (
              <span style={{ fontSize: '0.7rem', color: '#94A3B8' }}>
                {t.lastUpdated} {new Date(lastFetched).toLocaleTimeString()}
              </span>
            )}
          </div>

          {loading && (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#6B7280' }}>⏳ {t.loading}</div>
          )}

          {error && (
            <div style={{ background: '#FEE2E2', color: '#991B1B', padding: '1rem', borderRadius: '8px' }}>
              ⚠️ {error}
            </div>
          )}

          {!loading && !error && recommendations.length === 0 && (
            <div style={{ textAlign: 'center', color: '#6B7280', padding: '2rem' }}>{t.noRecs}</div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {recommendations.map((rec, i) => (
              <RecommendationCard
                key={`${rec.country}-${rec.sector}`}
                rec={rec}
                rank={rec.rank || i + 1}
              />
            ))}
          </div>
        </div>

        {/* Country Preview Panel */}
        <div>
          <h3 style={{ color: '#1A365D', marginBottom: '1rem' }}>🔍 {t.preview}</h3>
          <div style={{
            background: '#fff',
            border: '1px solid #E2E8F0',
            borderRadius: '12px',
            padding: '1rem',
          }}>
            <input
              value={previewCountry}
              onChange={e => setPreviewCountry(e.target.value.toUpperCase().slice(0, 3))}
              placeholder="Country code (e.g. MAR)"
              style={{
                width: '100%',
                padding: '0.6rem',
                borderRadius: '8px',
                border: '1px solid #E2E8F0',
                marginBottom: '1rem',
                fontFamily: 'monospace',
                fontSize: '1rem',
                letterSpacing: '0.1em',
              }}
            />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {SECTORS.slice(0, 5).map(s => (
                <SectorScoreWidget key={s} country={previewCountry} sector={s} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Load more */}
      {recommendations.length >= limit && (
        <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
          <button
            onClick={() => setLimit(l => l + 8)}
            style={{ background: '#F1F5F9', color: '#1A365D', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '0.6rem 1.5rem', cursor: 'pointer', fontWeight: 600 }}
          >
            Load More
          </button>
        </div>
      )}
    </div>
  );
}
