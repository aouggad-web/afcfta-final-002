import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, Globe, Award, Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const LPI_DIMENSION_COLORS = {
  lpi_overall: '#3b82f6',
  lpi_customs: '#ef4444',
  lpi_infrastructure: '#f59e0b',
  lpi_logistics_quality: '#10b981',
  lpi_tracking: '#8b5cf6',
  lpi_timeliness: '#06b6d4',
};

export default function WBLogisticsPanel({ language = 'fr' }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('lpi_overall');

  const texts = {
    fr: {
      title: 'Indice de Performance Logistique (LPI)',
      subtitle: 'Banque Mondiale — 54 pays africains comparés sur 6 dimensions',
      loading: 'Chargement des données LPI...',
      error: 'Erreur de chargement',
      rank: 'Rang',
      country: 'Pays',
      overall: 'Score Global',
      customs: 'Douanes',
      infrastructure: 'Infrastructure',
      quality: 'Qualité Log.',
      tracking: 'Traçabilité',
      timeliness: 'Ponctualité',
      source: 'Source: Banque Mondiale — Logistics Performance Index 2022/2023',
      topCountries: 'Top 10 Pays Africains — Score LPI Global',
      sortBy: 'Trier par :',
      allDimensions: 'Toutes les dimensions',
      noData: 'Données LPI non disponibles',
    },
    en: {
      title: 'Logistics Performance Index (LPI)',
      subtitle: 'World Bank — 54 African countries compared on 6 dimensions',
      loading: 'Loading LPI data...',
      error: 'Loading error',
      rank: 'Rank',
      country: 'Country',
      overall: 'Overall Score',
      customs: 'Customs',
      infrastructure: 'Infrastructure',
      quality: 'Log. Quality',
      tracking: 'Tracking',
      timeliness: 'Timeliness',
      source: 'Source: World Bank — Logistics Performance Index 2022/2023',
      topCountries: 'Top 10 African Countries — Overall LPI Score',
      sortBy: 'Sort by:',
      allDimensions: 'All dimensions',
      noData: 'LPI data not available',
    },
  };

  const t = texts[language];

  useEffect(() => {
    setLoading(true);
    setError(null);
    axios.get(`${API}/logistics/lpi`)
      .then(res => setData(res.data))
      .catch(() => setError(texts[language].error))
      .finally(() => setLoading(false));
  }, [language]);

  if (loading) return (
    <Card>
      <CardContent className="flex items-center justify-center h-48">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-blue-600 mx-auto" />
          <p className="mt-3 text-gray-600">{t.loading}</p>
        </div>
      </CardContent>
    </Card>
  );

  if (error || !data) return (
    <Card className="border-l-4 border-l-red-500">
      <CardContent className="py-8 text-center text-red-600">{error || t.noData}</CardContent>
    </Card>
  );

  const countries = data.countries || [];
  const top10 = [...countries].slice(0, 10);

  const scoreColor = (score) => {
    if (!score) return '#9ca3af';
    if (score >= 3.5) return '#16a34a';
    if (score >= 2.5) return '#d97706';
    return '#dc2626';
  };

  const dimLabel = {
    lpi_overall: t.overall,
    lpi_customs: t.customs,
    lpi_infrastructure: t.infrastructure,
    lpi_logistics_quality: t.quality,
    lpi_tracking: t.tracking,
    lpi_timeliness: t.timeliness,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 text-white shadow-xl">
        <CardHeader>
          <CardTitle className="text-xl font-bold flex items-center gap-3">
            <Globe className="w-6 h-6 text-blue-300" />
            {t.title}
          </CardTitle>
          <CardDescription className="text-slate-300">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {Object.entries(dimLabel).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setSortBy(key)}
                className={`p-2 rounded-lg text-center transition-all ${
                  sortBy === key
                    ? 'bg-blue-600 text-white shadow-lg scale-105'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                <p className="text-xs font-semibold">{label}</p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top 10 Chart */}
      <Card className="shadow-lg">
        <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardTitle className="text-lg text-blue-700 flex items-center gap-2">
            <Award className="w-5 h-5" /> {t.topCountries}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={top10.map(c => ({
              name: c.country_name.length > 12 ? c.country_name.slice(0, 11) + '.' : c.country_name,
              fullName: c.country_name,
              score: c[sortBy]?.value,
              rank: c.rank_africa,
            })).filter(d => d.score != null)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 5]} tickFormatter={(v) => v.toFixed(1)} />
              <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value, name, props) => [
                  `${value?.toFixed(2)}/5.0`,
                  props.payload.fullName,
                ]}
                labelFormatter={(label) => {
                  const item = top10.find(c => c.country_name.startsWith(label.replace('.', '')));
                  return item ? `#${item.rank_africa} ${item.country_name}` : label;
                }}
              />
              <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                {top10.map((entry, index) => (
                  <Cell key={index} fill={scoreColor(entry[sortBy]?.value)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Full Table */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            {language === 'fr' ? 'Classement Complet — 54 pays africains' : 'Full Ranking — 54 African countries'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-gray-100 z-10">
                <tr>
                  <th className="text-center p-2 font-bold">{t.rank}</th>
                  <th className="text-left p-2 font-bold">{t.country}</th>
                  <th className="text-center p-2 font-bold text-blue-700">{t.overall}</th>
                  <th className="text-center p-2 font-bold text-red-600">{t.customs}</th>
                  <th className="text-center p-2 font-bold text-yellow-600">{t.infrastructure}</th>
                  <th className="text-center p-2 font-bold text-green-600">{t.quality}</th>
                  <th className="text-center p-2 font-bold text-purple-600">{t.tracking}</th>
                  <th className="text-center p-2 font-bold text-cyan-600">{t.timeliness}</th>
                </tr>
              </thead>
              <tbody>
                {[...countries]
                  .sort((a, b) => (b[sortBy]?.value || 0) - (a[sortBy]?.value || 0))
                  .map((country, idx) => {
                    const overall = country.lpi_overall?.value;
                    return (
                      <tr key={country.country_iso} className={`border-b ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50`}>
                        <td className="text-center p-2">
                          <Badge variant={idx < 3 ? 'default' : 'outline'} className={idx === 0 ? 'bg-yellow-500' : idx === 1 ? 'bg-gray-400' : idx === 2 ? 'bg-amber-700' : ''}>
                            #{idx + 1}
                          </Badge>
                        </td>
                        <td className="p-2 font-medium">{country.country_name}</td>
                        <td className="text-center p-2">
                          <span className="font-bold" style={{ color: scoreColor(overall) }}>
                            {overall?.toFixed(2) || 'N/A'}
                          </span>
                        </td>
                        {['lpi_customs', 'lpi_infrastructure', 'lpi_logistics_quality', 'lpi_tracking', 'lpi_timeliness'].map(dim => (
                          <td key={dim} className="text-center p-2 text-gray-600">
                            {country[dim]?.value?.toFixed(2) || '—'}
                          </td>
                        ))}
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Source */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="py-3">
          <p className="text-xs text-gray-500 text-center">{t.source}</p>
        </CardContent>
      </Card>
    </div>
  );
}
