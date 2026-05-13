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
import { Search, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const fmtUSD = (v) => {
  if (v == null || isNaN(v)) return '—';
  const abs = Math.abs(v);
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};

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
    noData: 'Aucune donnée OEC pour ce code dans ce pays.',
    error: 'Erreur de récupération',
    inputError: 'Saisir un code SH (4 à 6 chiffres) puis cliquer Rechercher.',
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
    noData: 'No OEC data for this HS in this country.',
    error: 'Fetch error',
    inputError: 'Enter a 4-6 digit HS code then click Search.',
  },
};

export default function CountryHS6History({ language = 'fr' }) {
  const t = TXT[language] || TXT.fr;
  const [countries, setCountries] = useState([]);
  const [iso3, setIso3] = useState('DZA');
  const [hsCode, setHsCode] = useState('271019');
  const [years, setYears] = useState(5);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

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

  const runQuery = async () => {
    const cleanHs = String(hsCode).replace(/\D/g, '').slice(0, 6);
    if (!cleanHs || cleanHs.length < 4) {
      setError(t.inputError);
      return;
    }
    setError('');
    setLoading(true);
    setData(null);
    try {
      const r = await axios.get(`${API}/oec/country/${iso3}/hs6/${cleanHs}/history`, {
        params: { years },
      });
      setData(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || t.error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-run on mount
  useEffect(() => {
    runQuery();
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
          <span style={{ fontSize: 11, color: 'rgba(142,155,174,0.85)', fontWeight: 700, letterSpacing: 0.4 }}>{t.hsCode}</span>
          <input
            data-testid="hs6-code-input"
            value={hsCode}
            onChange={(e) => setHsCode(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && runQuery()}
            placeholder={t.hsPlaceholder}
            inputMode="numeric"
            maxLength={6}
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
          onClick={runQuery}
          disabled={loading}
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
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
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

      {!loading && data && (
        <>
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
                    formatter={(value, name) => [fmtUSD(value), name]}
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
                    <th style={{ textAlign: 'right', padding: '6px 4px', color: '#f43f5e', fontWeight: 700 }}>{t.imports}</th>
                    <th style={{ textAlign: 'right', padding: '6px 4px', color: '#fbbf24', fontWeight: 700 }}>{t.balance}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.chart_rows.map((row) => (
                    <tr key={row.year} style={{ borderBottom: '1px solid rgba(142,155,174,0.10)' }}>
                      <td style={{ padding: '6px 4px', fontWeight: 700 }}>{row.year}</td>
                      <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace' }}>{fmtUSD(row.exports)}</td>
                      <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace' }}>{fmtUSD(row.imports)}</td>
                      <td style={{ padding: '6px 4px', textAlign: 'right', fontFamily: 'monospace', color: row.balance >= 0 ? '#10b981' : '#f43f5e' }}>
                        {fmtUSD(row.balance)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="stats-source-note" style={{ padding: '0 16px 14px', margin: 0 }}>
            {data.source} · {data.country_name} · HS {data.hs_code} · {data.currency}
          </p>
        </>
      )}
    </div>
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
