import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import EnhancedCountrySelector from './EnhancedCountrySelector';
import {
  Wheat, Beef, Fish, TrendingUp, AlertTriangle, Loader2,
  Globe, BarChart3, Droplets, Award, Info
} from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const COLORS_CULTURES  = ['#16a34a','#15803d','#22c55e','#84cc16','#f59e0b','#ea580c','#dc2626','#10b981','#059669'];
const COLORS_ELEVAGE   = ['#92400e','#b45309','#d97706','#fbbf24','#fde68a'];
const COLORS_PECHE     = ['#0369a1','#0284c7','#0ea5e9','#38bdf8','#7dd3fc'];


const fmt = (n) => {
  if (!n && n !== 0) return '—';
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(0)}K`;
  return n.toLocaleString();
};

const fmtUnit = (n, unit = 'tonnes') => `${fmt(n)} ${unit}`;

export default function ProductionAgriculture({ language = 'fr' }) {
  const { t } = useTranslation();
  const [country, setCountry]   = useState('DZA');
  const [detail, setDetail]     = useState(null);
  const [faoStats, setFaoStats] = useState(null);
  const [loading, setLoading]   = useState(false);
  const [activeTab, setActiveTab] = useState('cultures');

  useEffect(() => { fetchFaoStats(); }, []);

  // Refetch aussi au changement de langue : les libellés des cultures bulk sont
  // localisés côté backend (paramètre language), sinon le basculement FR/EN
  // laisserait des noms de cultures dans la langue précédente jusqu'à un
  // changement de pays. Le nettoyage d'effet ignore les réponses obsolètes :
  // un changement rapide de pays/langue ne peut plus laisser une ancienne
  // réponse écraser la sélection courante (condition de course).
  useEffect(() => {
    if (!country) return undefined;
    let cancelled = false;
    setLoading(true);
    setDetail(null);
    (async () => {
      try {
        const r = await axios.get(
          `${API}/faostat/country-detail/${country}?language=${language}`
        );
        if (!cancelled) setDetail(r.data);
      } catch (err) {
        if (!cancelled) console.error('Error fetching country detail:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [country, language]);

  const fetchFaoStats = async () => {
    try {
      const r = await axios.get(`${API}/faostat/statistics`);
      setFaoStats(r.data);
    } catch (_) {}
  };

  // ── Charts data ──────────────────────────────────────────────────────────
  const culturesChartData = () =>
    (detail?.cultures || []).map((c, i) => ({
      name: c.name.length > 14 ? c.name.slice(0, 14) + '…' : c.name,
      fullName: c.name,
      value: c.value_2023,
      year: c.is_bulk_faostat ? c.year : 2023,
      fill: COLORS_CULTURES[i % COLORS_CULTURES.length],
    }));

  const evolutionChartData = () => {
    const evo = detail?.evolution || {};
    const crops = Object.keys(evo);
    if (!crops.length) return [];
    const years = [2020, 2021, 2022, 2023];
    return years.map(y => {
      const row = { year: y };
      crops.forEach(c => { row[c] = evo[c]?.[y] || evo[c]?.[String(y)] || null; });
      return row;
    });
  };

  const elevageChartData = () =>
    (detail?.elevage || []).map((e, i) => ({
      name: e.name,
      value: e.value,
      fill: COLORS_ELEVAGE[i % COLORS_ELEVAGE.length],
    }));

  const pecheChartData = () => {
    const p = detail?.peche_aquaculture;
    if (!p) return [];
    return [
      { name: t('production.agriculture.panel.capture'), value: p.capture_tonnes, fill: COLORS_PECHE[0] },
      { name: t('production.agriculture.panel.aquaculture'), value: p.aquaculture_tonnes, fill: COLORS_PECHE[2] },
    ].filter(x => x.value > 0);
  };

  const evoLines = Object.keys(detail?.evolution || {}).slice(0, 5);


  const commodityShortLabel = (name) => {
    const short = (name || '').replace(/\s*\(projection\)\s*$/i, '').trim();
    return t(`production.agriculture.projectionAggregate.${short.toLowerCase()}`, {
      defaultValue: short,
    });
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-5">

      {/* Header */}
      <Card className="bg-[image:var(--card-grad)] border-l-4 border-l-[var(--success)] shadow-xl overflow-hidden">
        <CardHeader>
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <CardTitle className="text-2xl font-bold flex items-center gap-3">
                <Wheat className="w-7 h-7" /> {t('production.agriculture.panel.title')}
              </CardTitle>
              <CardDescription className="text-[var(--success)] mt-1">{t('production.agriculture.panel.subtitle')}</CardDescription>
            </div>
            {faoStats && (
              <div className="flex flex-col items-end gap-1">
                <Badge className="bg-[var(--overlay)] text-[var(--text)] text-sm px-3 py-1">
                  <Globe className="w-3 h-3 mr-1" /> {faoStats.total_countries} pays
                </Badge>
                <span className="text-xs text-[var(--success)]">
                  {faoStats.total_commodities} produits · {faoStats.data_year}
                </span>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Country Selector */}
      <Card className="border-2 border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-lg" style={{ overflow: 'visible' }}>
        <CardContent className="pt-5" style={{ overflow: 'visible' }}>
          <EnhancedCountrySelector
            value={country}
            onChange={setCountry}
            label={t('production.agriculture.panel.selectCountry')}
            variant="prominent"
            language={language}
          />
        </CardContent>
      </Card>

      {/* Loading */}
      {loading && (
        <Card>
          <CardContent className="flex items-center justify-center h-48">
            <div className="text-center">
              <Loader2 className="w-10 h-10 animate-spin text-[var(--success)] mx-auto" />
              <p className="mt-3 text-[var(--afcfta-muted)]">{t('production.agriculture.panel.loading')}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Country detail */}
      {!loading && detail && (
        <>
          {/* Country header */}
          <Card className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
            <CardHeader>
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                  <CardTitle className="text-xl text-[var(--success)] flex items-center gap-2">
                    <span className="text-3xl">🌍</span> {detail.country_name}
                    <Badge variant="outline" className="border-[color-mix(in_srgb,var(--success)_30%,transparent)] text-[var(--success)] text-xs ml-2">
                      {detail.region}
                    </Badge>
                  </CardTitle>
                  <div className="flex gap-2 mt-2 flex-wrap">
                    <Badge className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                      {detail.cultures?.length || 0} cultures
                    </Badge>
                    {detail.has_livestock && (
                      <Badge className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                        <Beef className="w-3 h-3 mr-1" /> Élevage
                      </Badge>
                    )}
                    {detail.has_fisheries && (
                      <Badge className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                        <Fish className="w-3 h-3 mr-1" /> Pêche
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-[var(--afcfta-muted)]">{t('production.agriculture.panel.source')}</p>
                  {(detail.sources?.length ? detail.sources : [detail.source]).map((s) => (
                    <p key={s} className="text-xs font-medium text-[var(--text)]">{s}</p>
                  ))}
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Sub-tabs: Cultures / Élevage / Pêche */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-5">
            <TabsList className="grid w-full grid-cols-3 bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] p-1 h-auto">
              <TabsTrigger
                value="cultures"
                className="data-[state=active]:bg-green-600 data-[state=active]:text-[var(--text)] py-2.5"
              >
                <Wheat className="w-4 h-4 mr-2" /> {t('production.agriculture.panel.tabCultures')}
              </TabsTrigger>
              <TabsTrigger
                value="elevage"
                className="data-[state=active]:bg-amber-600 data-[state=active]:text-[var(--text)] py-2.5"
                disabled={!detail.has_livestock}
              >
                <Beef className="w-4 h-4 mr-2" /> {t('production.agriculture.panel.tabElevage')}
              </TabsTrigger>
              <TabsTrigger
                value="peche"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-[var(--text)] py-2.5"
                disabled={!detail.has_fisheries}
              >
                <Fish className="w-4 h-4 mr-2" /> {t('production.agriculture.panel.tabPeche')}
              </TabsTrigger>
            </TabsList>

            {/* ═══════════════════ CULTURES ═══════════════════ */}
            <TabsContent value="cultures" className="space-y-5">
              {detail.cultures?.length > 0 ? (
                <>
                  {/* Bar chart + Table */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    <Card className="shadow-md">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--text)] flex items-center gap-2">
                          <BarChart3 className="w-4 h-4 text-[var(--success)]" /> {t('production.agriculture.panel.production')}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={320}>
                          <BarChart data={culturesChartData()} layout="vertical" margin={{ left: 10, right: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" tickFormatter={fmt} tick={{ fontSize: 11 }} />
                            <YAxis type="category" dataKey="name" width={105} tick={{ fontSize: 11 }} />
                            <Tooltip
                              formatter={(v, _, p) => [
                                `${fmtUnit(v, t('production.agriculture.panel.tonnes'))}${p?.payload?.year ? ` (${p.payload.year})` : ''}`,
                                p?.payload?.fullName || '',
                              ]}
                            />
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                              {culturesChartData().map((e, i) => (
                                <Cell key={i} fill={e.fill} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {/* Detailed table */}
                    <Card className="shadow-md">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--text)]">{t('production.agriculture.panel.cultures')}</CardTitle>
                      </CardHeader>
                      <CardContent className="p-0">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] border-b">
                                <th className="text-left px-3 py-2 font-semibold">Produit</th>
                                <th className="text-right px-3 py-2 font-semibold">{t('production.agriculture.panel.production')}</th>
                                <th className="text-right px-3 py-2 font-semibold hidden sm:table-cell">{t('production.agriculture.panel.surface')}</th>
                                <th className="text-center px-3 py-2 font-semibold">{t('production.agriculture.panel.rankAfrique')}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detail.cultures.map((c, i) => (
                                <tr key={c.name} className="border-b hover:bg-[var(--afcfta-card2)]">
                                  <td className="px-3 py-2">
                                    <div className="flex items-center gap-2">
                                      <div className="w-3 h-3 rounded-full flex-shrink-0"
                                        style={{ backgroundColor: COLORS_CULTURES[i % COLORS_CULTURES.length] }} />
                                      <span className="font-medium">{c.name}</span>
                                    </div>
                                  </td>
                                  <td className="px-3 py-2 text-right font-mono text-[var(--success)] font-bold">
                                    {fmt(c.value_2023)} t
                                    <span className="ml-1 text-xs font-normal text-[var(--afcfta-muted)]">
                                      ({c.is_bulk_faostat ? c.year : 2023})
                                    </span>
                                  </td>
                                  <td className="px-3 py-2 text-right text-[var(--afcfta-muted)] hidden sm:table-cell">
                                    {c.area_ha ? `${fmt(c.area_ha)} ha` : '—'}
                                  </td>
                                  <td className="px-3 py-2 text-center">
                                    {c.rank_africa ? (
                                      <Badge className={`text-xs ${c.rank_africa <= 3 ? 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]' : 'bg-[var(--afcfta-card2)] text-[var(--text)]'}`}>
                                        {c.rank_africa <= 3 && <Award className="w-3 h-3 mr-0.5 inline" />}
                                        #{c.rank_africa}
                                      </Badge>
                                    ) : '—'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Evolution chart */}
                  {evoLines.length > 0 && (
                    <Card className="shadow-md">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--success)] flex items-center gap-2">
                          <TrendingUp className="w-4 h-4" /> {t('production.agriculture.panel.evolution')}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={280}>
                          <LineChart data={evolutionChartData()}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="year" />
                            <YAxis tickFormatter={fmt} />
                            <Tooltip formatter={(v) => [fmt(v) + ' ' + t('production.agriculture.panel.tonnes')]} />
                            <Legend />
                            {evoLines.map((crop, i) => (
                              <Line
                                key={crop}
                                type="monotone"
                                dataKey={crop}
                                stroke={COLORS_CULTURES[i % COLORS_CULTURES.length]}
                                strokeWidth={2.5}
                                dot={{ r: 4 }}
                                activeDot={{ r: 7 }}
                              />
                            ))}
                          </LineChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  )}

                  {/* Key indicators */}
                  {detail.key_indicators && Object.keys(detail.key_indicators).length > 0 && (
                    <Card className="shadow-md bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--success)] flex items-center gap-2">
                          <Info className="w-4 h-4" /> {t('production.agriculture.panel.indicators')}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {detail.key_indicators.agri_gdp_percent && (
                            <div className="text-center">
                              <p className="text-2xl font-bold text-[var(--success)]">{detail.key_indicators.agri_gdp_percent}%</p>
                              <p className="text-xs text-[var(--afcfta-muted)] mt-1">{t('production.agriculture.panel.agriGDP')}</p>
                            </div>
                          )}
                          {detail.key_indicators.agri_employment_percent && (
                            <div className="text-center">
                              <p className="text-2xl font-bold text-[var(--success)]">{detail.key_indicators.agri_employment_percent}%</p>
                              <p className="text-xs text-[var(--afcfta-muted)] mt-1">{t('production.agriculture.panel.agriEmploy')}</p>
                            </div>
                          )}
                          {detail.key_indicators.arable_land_ha && (
                            <div className="text-center">
                              <p className="text-2xl font-bold text-[var(--success)]">{fmt(detail.key_indicators.arable_land_ha)}</p>
                              <p className="text-xs text-[var(--afcfta-muted)] mt-1">{t('production.agriculture.panel.arable')} (ha)</p>
                            </div>
                          )}
                          {detail.key_indicators.irrigated_land_ha && (
                            <div className="text-center">
                              <p className="text-2xl font-bold text-[var(--info)]">{fmt(detail.key_indicators.irrigated_land_ha)}</p>
                              <p className="text-xs text-[var(--afcfta-muted)] mt-1">{t('production.agriculture.panel.irrigated')} (ha)</p>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              ) : (
                <Card className="border-l-4 border-l-amber-400">
                  <CardContent className="flex items-center gap-4 py-8">
                    <AlertTriangle className="w-10 h-10 text-[var(--gold)] flex-shrink-0" />
                    <p className="text-[var(--afcfta-muted)]">{t('production.agriculture.panel.noData')}</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* ═══════════════════ ÉLEVAGE ═══════════════════ */}
            <TabsContent value="elevage" className="space-y-5">
              {detail.has_livestock && detail.elevage?.length > 0 ? (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {/* Bar chart élevage */}
                    <Card className="shadow-md">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--gold)] flex items-center gap-2">
                          <Beef className="w-4 h-4" /> {t('production.agriculture.panel.livestock')} 2023
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={280}>
                          <BarChart data={elevageChartData()} layout="vertical" margin={{ left: 10, right: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" tickFormatter={fmt} tick={{ fontSize: 11 }} />
                            <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
                            <Tooltip formatter={(v) => [fmt(v) + ' ' + t('production.agriculture.panel.tetes')]} />
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                              {elevageChartData().map((e, i) => (
                                <Cell key={i} fill={e.fill} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    {/* Table élevage */}
                    <Card className="shadow-md">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--gold)]">{t('production.agriculture.panel.livestock')}</CardTitle>
                      </CardHeader>
                      <CardContent className="p-0">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] border-b">
                              <th className="text-left px-3 py-2 font-semibold">Espèce</th>
                              <th className="text-right px-3 py-2 font-semibold">Effectif</th>
                              <th className="text-center px-3 py-2 font-semibold">{t('production.agriculture.panel.rankAfrique')}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {detail.elevage.map((e, i) => (
                              <tr key={e.name} className="border-b hover:bg-amber-50/50">
                                <td className="px-3 py-2.5">
                                  <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full"
                                      style={{ backgroundColor: COLORS_ELEVAGE[i % COLORS_ELEVAGE.length] }} />
                                    <span className="font-medium">{e.name}</span>
                                  </div>
                                </td>
                                <td className="px-3 py-2.5 text-right font-mono font-bold text-[var(--gold)]">
                                  {fmt(e.value)} {e.unit}
                                </td>
                                <td className="px-3 py-2.5 text-center">
                                  {e.rank_africa ? (
                                    <Badge className={`text-xs ${e.rank_africa <= 5 ? 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]' : 'bg-[var(--afcfta-card2)] text-[var(--text)]'}`}>
                                      #{e.rank_africa}
                                    </Badge>
                                  ) : '—'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Production animale */}
                  {detail.livestock_production_2023 && Object.keys(detail.livestock_production_2023).length > 0 && (
                    <Card className="shadow-md bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--gold)]">{t('production.agriculture.panel.livestockProd')} 2023</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(detail.livestock_production_2023).map(([name, d]) => (
                            <div key={name} className="text-center bg-[var(--afcfta-card)] rounded-xl p-3 border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] shadow-sm">
                              <p className="text-xl font-bold text-[var(--gold)]">{fmt(d.value)}</p>
                              <p className="text-xs text-[var(--afcfta-muted)] mt-1">{d.unit}</p>
                              <p className="text-sm font-medium text-[var(--text)] mt-1">{name}</p>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              ) : (
                <Card className="border-l-4 border-l-amber-400">
                  <CardContent className="flex items-center gap-4 py-8">
                    <AlertTriangle className="w-10 h-10 text-[var(--gold)] flex-shrink-0" />
                    <p className="text-[var(--afcfta-muted)]">{t('production.agriculture.panel.noLivestock')}</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* ═══════════════════ PÊCHE & AQUACULTURE ═══════════════════ */}
            <TabsContent value="peche" className="space-y-5">
              {detail.has_fisheries ? (
                <>
                  {/* KPIs capture + aquaculture */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <Card className="shadow-md border-l-4 border-l-blue-500 bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]">
                      <CardContent className="pt-5">
                        <div className="flex items-center gap-4">
                          <Fish className="w-10 h-10 text-[var(--info)] flex-shrink-0" />
                          <div>
                            <p className="text-3xl font-bold text-[var(--info)]">
                              {fmt(detail.peche_aquaculture?.capture_tonnes)} t
                            </p>
                            <p className="text-sm text-[var(--info)] mt-1">{t('production.agriculture.panel.capture')} 2023</p>
                            {detail.peche_aquaculture?.capture_rank_africa && (
                              <Badge className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] mt-2 text-xs">
                                Rang Afrique #{detail.peche_aquaculture.capture_rank_africa}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="shadow-md border-l-4 border-l-teal-500 bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))]">
                      <CardContent className="pt-5">
                        <div className="flex items-center gap-4">
                          <Droplets className="w-10 h-10 text-[var(--success)] flex-shrink-0" />
                          <div>
                            <p className="text-3xl font-bold text-[var(--success)]">
                              {fmt(detail.peche_aquaculture?.aquaculture_tonnes)} t
                            </p>
                            <p className="text-sm text-[var(--success)] mt-1">{t('production.agriculture.panel.aquaculture')} 2023</p>
                            {detail.peche_aquaculture?.aquaculture_rank_africa && (
                              <Badge className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] mt-2 text-xs">
                                Rang Afrique #{detail.peche_aquaculture.aquaculture_rank_africa}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Pie chart + details */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    <Card className="shadow-md">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--info)]">Répartition de la production halieutique</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={260}>
                          <PieChart>
                            <Pie
                              data={pecheChartData()}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={110}
                              paddingAngle={4}
                              dataKey="value"
                            >
                              {pecheChartData().map((e, i) => (
                                <Cell key={i} fill={e.fill} />
                              ))}
                            </Pie>
                            <Tooltip formatter={(v) => [fmt(v) + ' t']} />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>

                    <Card className="shadow-md">
                      <CardHeader>
                        <CardTitle className="text-base text-[var(--info)]">Détails pêche & aquaculture</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {detail.peche_aquaculture?.species?.length > 0 && (
                          <div>
                            <p className="text-sm font-semibold text-[var(--text)] mb-2">
                              <Fish className="w-3.5 h-3.5 inline mr-1 text-[var(--info)]" /> {t('production.agriculture.panel.species')}
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {detail.peche_aquaculture.species.map(s => (
                                <Badge key={s} className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)]">{s}</Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        {detail.peche_aquaculture?.main_ports?.length > 0 && (
                          <div>
                            <p className="text-sm font-semibold text-[var(--text)] mb-2">
                              ⚓ {t('production.agriculture.panel.ports')}
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {detail.peche_aquaculture.main_ports.map(p => (
                                <Badge key={p} className="bg-[var(--afcfta-card2)] text-[var(--text)]">{p}</Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        <div className="mt-4 p-3 bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                          <p className="text-xs text-[var(--afcfta-muted)]">Source : FAO FishStat 2023 / Direction des Pêches</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              ) : (
                <Card className="border-l-4 border-l-blue-400">
                  <CardContent className="flex items-center gap-4 py-8">
                    <AlertTriangle className="w-10 h-10 text-[var(--info)] flex-shrink-0" />
                    <p className="text-[var(--afcfta-muted)]">{t('production.agriculture.panel.noFisheries')}</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>

          {/* Perspectives / Prévisions OCDE-FAO — agrégats nationaux transversaux
              (cultures ET élevage), donc affichés hors des sous-onglets sectoriels. */}
          {detail.has_projections && (
            <Card className="shadow-md border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
              <CardHeader>
                <CardTitle className="text-base text-[var(--success)] flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" /> {t('production.agriculture.panel.perspectives')}
                </CardTitle>
                <CardDescription className="text-xs text-[var(--afcfta-muted)]">
                  {t('production.agriculture.panel.perspectivesSubtitle')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {detail.projections.map((proj) => {
                    const points = proj.points || [];
                    const first = points[0];
                    const last = points[points.length - 1];
                    const growthPct =
                      first && last && first.value
                        ? ((last.value - first.value) / first.value) * 100
                        : null;
                    return (
                      <div
                        key={proj.commodity}
                        className="rounded-xl border border-[color-mix(in_srgb,var(--success)_30%,transparent)] bg-emerald-50/60 p-4"
                      >
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="font-semibold text-[var(--success)] text-sm">
                            {commodityShortLabel(proj.commodity)}
                          </span>
                          <Badge
                            className={`text-[11px] text-[var(--text)] ${
                              proj.is_livestock ? 'bg-amber-600' : 'bg-emerald-600'
                            }`}
                          >
                            {proj.is_livestock ? t('production.agriculture.panel.sectorLivestock') : t('production.agriculture.panel.sectorCrops')}
                          </Badge>
                        </div>
                        <div className="flex items-end gap-3 flex-wrap">
                          {points.map((p) => (
                            <div key={p.year} className="text-center">
                              <p className="text-lg font-bold text-[var(--success)]">
                                {fmt(p.value)}
                              </p>
                              <p className="text-[11px] text-[var(--afcfta-muted)]">
                                {p.year} · {proj.unit}
                              </p>
                            </div>
                          ))}
                        </div>
                        {growthPct !== null && (
                          <p className="text-xs text-[var(--success)] mt-2">
                            {growthPct >= 0 ? '+' : ''}
                            {growthPct.toFixed(1)}% ({first.year}→{last.year})
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
                <p className="text-[11px] text-[var(--afcfta-muted)] mt-3">{t('production.agriculture.panel.perspectivesSource')}</p>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* No data fallback */}
      {!loading && !detail && (
        <Card className="border-l-4 border-l-amber-400">
          <CardContent className="flex items-center gap-4 py-8">
            <AlertTriangle className="w-10 h-10 text-[var(--gold)] flex-shrink-0" />
            <p className="text-[var(--afcfta-muted)]">{t('production.agriculture.panel.noData')}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
