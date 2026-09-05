import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import { getAllCountries } from '../../utils/countryCodes';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

const TEXTS = {
  fr: {
    title: 'Évolution du commerce (2018-2024)',
    subtitle: 'Vraies données annuelles OEC/BACI — exports, imports et balance',
    country: 'Pays',
    loading: 'Chargement de la série…',
    error: 'Données indisponibles pour ce pays.',
    noData: 'Aucune donnée commerciale OEC pour ce pays.',
    exports: 'Exports',
    imports: 'Imports',
    balance: 'Balance',
    billionUsd: 'Milliards USD',
    sourceLabel: 'Source',
  },
  en: {
    title: 'Trade evolution (2018-2024)',
    subtitle: 'Real annual OEC/BACI data — exports, imports and balance',
    country: 'Country',
    loading: 'Loading series…',
    error: 'Data unavailable for this country.',
    noData: 'No OEC trade data for this country.',
    exports: 'Exports',
    imports: 'Imports',
    balance: 'Balance',
    billionUsd: 'Billion USD',
    sourceLabel: 'Source',
  },
};

const toBillion = (v) => (v == null ? 0 : Math.round((v / 1e9) * 100) / 100);

const CountryTradeSeries = ({ language = 'fr', defaultCountry = 'NGA' }) => {
  const t = TEXTS[language] || TEXTS.fr;
  const countries = getAllCountries(language === 'en' ? 'en' : 'fr');

  const [country, setCountry] = useState(defaultCountry);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!country) return;
    setLoading(true);
    setError(false);
    axios
      .get(`${API_URL}/api/oec/country/${country}/trade-series`)
      .then((res) => setData(res.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [country]);

  const chartData = (data?.chart_rows || []).map((r) => ({
    year: r.year,
    exports: toBillion(r.exports),
    imports: toBillion(r.imports),
    balance: toBillion(r.balance),
  }));

  return (
    <div className="stats-chart-card">
      <div className="stats-chart-header green">
        <div className="stats-chart-title green">
          <TrendingUp style={{ width: 18, height: 18 }} />
          {t.title}
        </div>
        <div className="stats-chart-subtitle">{t.subtitle}</div>
      </div>

      <div style={{ padding: '16px 20px' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 4, maxWidth: 280, marginBottom: 16 }}>
          <span style={{ fontSize: 11, color: 'rgba(142,155,174,0.85)', fontWeight: 700 }}>{t.country}</span>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            style={{ padding: '8px 10px', borderRadius: 8, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(212,175,55,0.22)', color: 'var(--text)', fontSize: 13, fontWeight: 600 }}
          >
            {countries.map((c) => (
              <option key={c.iso3} value={c.iso3}>
                {c.flag} {c.name}
              </option>
            ))}
          </select>
        </label>

        {loading && (
          <p style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.85rem' }}>{t.loading}</p>
        )}
        {error && !loading && (
          <p style={{ color: '#f87171', fontSize: '0.85rem' }}>{t.error}</p>
        )}
        {!loading && !error && data && !data.has_data && (
          <p style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.85rem' }}>{t.noData}</p>
        )}

        {!loading && !error && data?.has_data && (data.source_used || data.source) && (
          <div style={{ marginBottom: 10 }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                fontSize: 11,
                fontWeight: 700,
                padding: '3px 10px',
                borderRadius: 100,
                background: 'rgba(52,211,153,0.14)',
                color: '#34d399',
                border: '1px solid rgba(52,211,153,0.3)',
              }}
            >
              {t.sourceLabel}: {data.source_used || data.source}
            </span>
          </div>
        )}

        {!loading && !error && data?.has_data && (
          <ResponsiveContainer width="100%" height={320} debounce={300}>
            <LineChart data={chartData} margin={{ top: 10, right: 24, left: 12, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="year" tick={{ fontSize: 12, fontWeight: 600, fill: '#EAE0D0' }} axisLine={false} tickLine={false} />
              <YAxis
                label={{ value: t.billionUsd, angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: 'rgba(142,155,174,0.6)' } }}
                tick={{ fontSize: 11, fill: 'rgba(142,155,174,0.7)' }}
                axisLine={false} tickLine={false}
              />
              <Tooltip
                formatter={(value) => [`$${value}B`, '']}
                contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
              />
              <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'rgba(142,155,174,0.8)' }} iconType="circle" />
              <Line type="monotone" dataKey="exports" stroke="#34d399" strokeWidth={2.5} name={t.exports} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="imports" stroke="#fb923c" strokeWidth={2.5} name={t.imports} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="balance" stroke="#38bdf8" strokeWidth={2} strokeDasharray="5 5" name={t.balance} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        )}

        {(data?.source_used || data?.source) && (
          <p className="stats-source-note">{data.source_used || data.source}</p>
        )}
      </div>
    </div>
  );
};

export default CountryTradeSeries;
