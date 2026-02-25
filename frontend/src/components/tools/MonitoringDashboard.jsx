import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function MonitoringDashboard({ language = 'fr' }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [error, setError] = useState(null);
  const [sortField, setSortField] = useState('code');
  const [sortAsc, setSortAsc] = useState(true);

  const t = language === 'fr' ? {
    title: "Monitoring des Données Tarifaires",
    subtitle: "Suivi en temps réel de la collecte des positions tarifaires nationales",
    totalCountries: "Pays collectés",
    totalLines: "Lignes HS6",
    totalSub: "Sous-positions (HS8-12)",
    totalPositions: "Positions totales",
    collectAll: "Collecter les 55 pays",
    collecting: "Collecte en cours...",
    refresh: "Actualiser",
    country: "Pays",
    tariffLines: "Lignes HS6",
    subPositions: "Sous-positions",
    total: "Total",
    vatRate: "TVA %",
    ddAvg: "DD moy %",
    chapters: "Chapitres",
    generatedAt: "Dernière collecte",
    noData: "Aucune donnée. Lancez une collecte.",
    success: "Collecte terminée avec succès !",
    errorMsg: "Erreur lors de la collecte",
    coverage: "Couverture",
    withSub: "Avec sous-positions",
    scheduler: "Planification",
    schedulerDesc: "Collecte automatique: 1 fois par an (janvier)",
    lastRun: "Dernière exécution",
    nextRun: "Prochaine exécution: Janvier",
  } : {
    title: "Tariff Data Monitoring",
    subtitle: "Real-time tracking of national tariff position collection",
    totalCountries: "Countries collected",
    totalLines: "HS6 Lines",
    totalSub: "Sub-positions (HS8-12)",
    totalPositions: "Total Positions",
    collectAll: "Collect all 54 countries",
    collecting: "Collecting...",
    refresh: "Refresh",
    country: "Country",
    tariffLines: "HS6 Lines",
    subPositions: "Sub-positions",
    total: "Total",
    vatRate: "VAT %",
    ddAvg: "DD avg %",
    chapters: "Chapters",
    generatedAt: "Last collected",
    noData: "No data. Run a collection.",
    success: "Collection completed successfully!",
    errorMsg: "Error during collection",
    coverage: "Coverage",
    withSub: "With sub-positions",
    scheduler: "Scheduling",
    schedulerDesc: "Automatic collection: once per year (January)",
    lastRun: "Last run",
    nextRun: "Next run: January",
  };

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API}/tariff-data/monitoring/stats`);
      setStats(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  const handleCollectAll = async () => {
    setCollecting(true);
    setError(null);
    try {
      await axios.post(`${API}/tariff-data/collect`, { all_countries: true });
      await fetchStats();
    } catch (err) {
      setError(t.errorMsg);
    } finally {
      setCollecting(false);
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const sortedCountries = stats?.countries ? [...stats.countries].sort((a, b) => {
    let va = a[sortField], vb = b[sortField];
    if (typeof va === 'string') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    return sortAsc ? va - vb : vb - va;
  }) : [];

  const formatNumber = (n) => n?.toLocaleString() || '0';
  const formatDate = (d) => d ? new Date(d).toLocaleDateString(language === 'fr' ? 'fr-FR' : 'en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '-';

  return (
    <div className="space-y-6">
      <Card className="afcfta-dark-gradient border-2" style={{borderColor:'rgba(96,165,250,0.3)'}}>
        <CardHeader>
          <CardTitle className="text-2xl text-blue-400">{t.title}</CardTitle>
          <CardDescription>{t.subtitle}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="rounded-xl p-4 shadow text-center" style={{background:'rgba(255,255,255,0.06)'}}>
              <div className="text-3xl font-bold text-blue-400">{stats?.country_count || 0}</div>
              <div className="text-sm" style={{color:'var(--afcfta-muted)'}}>{t.totalCountries}</div>
            </div>
            <div className="rounded-xl p-4 shadow text-center" style={{background:'rgba(255,255,255,0.06)'}}>
              <div className="text-3xl font-bold text-green-400">{formatNumber(stats?.total_tariff_lines)}</div>
              <div className="text-sm" style={{color:'var(--afcfta-muted)'}}>{t.totalLines}</div>
            </div>
            <div className="rounded-xl p-4 shadow text-center" style={{background:'rgba(255,255,255,0.06)'}}>
              <div className="text-3xl font-bold text-purple-400">{formatNumber(stats?.total_sub_positions)}</div>
              <div className="text-sm" style={{color:'var(--afcfta-muted)'}}>{t.totalSub}</div>
            </div>
            <div className="rounded-xl p-4 shadow text-center" style={{background:'rgba(255,255,255,0.06)'}}>
              <div className="text-3xl font-bold text-orange-400">{formatNumber(stats?.total_positions)}</div>
              <div className="text-sm" style={{color:'var(--afcfta-muted)'}}>{t.totalPositions}</div>
            </div>
          </div>

          <div className="flex gap-3 mb-4">
            <Button onClick={fetchStats} variant="outline" disabled={loading}>
              {t.refresh}
            </Button>
            <Button onClick={handleCollectAll} disabled={collecting} className="bg-blue-600 hover:bg-blue-700 text-white">
              {collecting ? t.collecting : t.collectAll}
            </Button>
          </div>

          {error && <div className="border text-red-400 p-3 rounded-lg mb-4" style={{background:'rgba(239,68,68,0.1)', borderColor:'rgba(239,68,68,0.3)'}}>{error}</div>}

          <Card className="mb-4" style={{background:'rgba(251,191,36,0.08)', border:'1px solid rgba(251,191,36,0.25)'}}>
            <CardContent className="p-4 flex items-center gap-4">
              <Badge variant="outline" className="text-amber-400 border-amber-400 text-xs px-2 py-1">{t.scheduler}</Badge>
              <span className="text-sm text-amber-400">{t.schedulerDesc}</span>
              {stats?.countries?.[0]?.generated_at && (
              <span className="text-xs text-amber-400 ml-auto">{t.lastRun}: {formatDate(stats.countries[0].generated_at)}</span>
              )}
            </CardContent>
          </Card>
        </CardContent>
      </Card>

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : !stats?.countries?.length ? (
        <div className="text-center py-8 text-gray-500">{t.noData}</div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 border-b">
                  <tr>
                    {[
                      { key: 'code', label: t.country },
                      { key: 'tariff_lines', label: t.tariffLines },
                      { key: 'sub_positions', label: t.subPositions },
                      { key: 'total_positions', label: t.total },
                      { key: 'lines_with_sub_positions', label: t.withSub },
                      { key: 'vat_rate', label: t.vatRate },
                      { key: 'dd_avg', label: t.ddAvg },
                      { key: 'chapters', label: t.chapters },
                      { key: 'generated_at', label: t.generatedAt },
                    ].map(col => (
                      <th
                        key={col.key}
                        onClick={() => handleSort(col.key)}
                        className="px-3 py-2 text-left cursor-pointer hover:bg-gray-200 select-none"
                      >
                        {col.label} {sortField === col.key ? (sortAsc ? '▲' : '▼') : ''}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedCountries.map((c, i) => (
                    <tr key={c.code} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 font-bold text-blue-700">{c.code}</td>
                      <td className="px-3 py-2">{formatNumber(c.tariff_lines)}</td>
                      <td className="px-3 py-2 text-purple-600">{formatNumber(c.sub_positions)}</td>
                      <td className="px-3 py-2 font-semibold text-orange-600">{formatNumber(c.total_positions)}</td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${Math.min(100, (c.lines_with_sub_positions / c.tariff_lines) * 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-500">{Math.round((c.lines_with_sub_positions / c.tariff_lines) * 100)}%</span>
                        </div>
                      </td>
                      <td className="px-3 py-2">{c.vat_rate}%</td>
                      <td className="px-3 py-2">{c.dd_avg}%</td>
                      <td className="px-3 py-2">{c.chapters}</td>
                      <td className="px-3 py-2 text-xs text-gray-500">{formatDate(c.generated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
