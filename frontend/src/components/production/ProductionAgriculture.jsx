import React, { useState, useEffect } from 'react';
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

const TEXTS = {
  fr: {
    title: 'Production Agricole FAO',
    subtitle: 'Données officielles FAOSTAT — Cultures, Élevage, Pêche & Aquaculture',
    selectCountry: 'Sélectionner un pays',
    loading: 'Chargement des données FAO…',
    noData: 'Aucune donnée disponible pour ce pays',
    tabCultures: 'Cultures',
    tabElevage: 'Élevage',
    tabPeche: 'Pêche & Aquaculture',
    cultures: 'Grandes cultures',
    production: 'Production 2023',
    tonnes: 'tonnes',
    tetes: 'têtes',
    hectares: 'ha',
    rendement: 'Rendement',
    surface: 'Surface',
    rankAfrique: 'Rang Afrique',
    evolution: 'Évolution 2020–2023',
    livestock: 'Cheptel',
    livestockProd: 'Production animale',
    capture: 'Pêche de capture',
    aquaculture: 'Aquaculture',
    species: 'Espèces principales',
    ports: 'Principaux ports',
    indicators: 'Indicateurs clés',
    agriGDP: 'Part dans le PIB',
    agriEmploy: 'Emploi agricole',
    arable: 'Terres arables',
    irrigated: 'Terres irriguées',
    source: 'Source',
    noLivestock: 'Données élevage non disponibles pour ce pays',
    noFisheries: 'Données pêche non disponibles pour ce pays',
    topCerealsDZA: 'Grandes céréales (cultures stratégiques)',
  },
  en: {
    title: 'FAO Agricultural Production',
    subtitle: 'Official FAOSTAT data — Crops, Livestock, Fisheries & Aquaculture',
    selectCountry: 'Select a country',
    loading: 'Loading FAO data…',
    noData: 'No data available for this country',
    tabCultures: 'Crops',
    tabElevage: 'Livestock',
    tabPeche: 'Fisheries & Aquaculture',
    cultures: 'Major crops',
    production: '2023 Production',
    tonnes: 'tonnes',
    tetes: 'heads',
    hectares: 'ha',
    rendement: 'Yield',
    surface: 'Area',
    rankAfrique: 'Africa Rank',
    evolution: 'Trend 2020–2023',
    livestock: 'Livestock population',
    livestockProd: 'Animal production',
    capture: 'Capture fisheries',
    aquaculture: 'Aquaculture',
    species: 'Main species',
    ports: 'Main ports',
    indicators: 'Key indicators',
    agriGDP: 'Share of GDP',
    agriEmploy: 'Agricultural employment',
    arable: 'Arable land',
    irrigated: 'Irrigated land',
    source: 'Source',
    noLivestock: 'Livestock data not available for this country',
    noFisheries: 'Fisheries data not available for this country',
    topCerealsDZA: 'Major cereals (strategic crops)',
  }
};

const fmt = (n) => {
  if (!n && n !== 0) return '—';
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(0)}K`;
  return n.toLocaleString();
};

const fmtUnit = (n, unit = 'tonnes') => `${fmt(n)} ${unit}`;

export default function ProductionAgriculture({ language = 'fr' }) {
  const t = TEXTS[language] || TEXTS.fr;
  const [country, setCountry]   = useState('DZA');
  const [detail, setDetail]     = useState(null);
  const [faoStats, setFaoStats] = useState(null);
  const [loading, setLoading]   = useState(false);
  const [activeTab, setActiveTab] = useState('cultures');

  useEffect(() => { fetchFaoStats(); }, []);

  useEffect(() => {
    if (country) fetchDetail(country);
  }, [country]);

  const fetchFaoStats = async () => {
    try {
      const r = await axios.get(`${API}/faostat/statistics`);
      setFaoStats(r.data);
    } catch (_) {}
  };

  const fetchDetail = async (iso3) => {
    setLoading(true);
    setDetail(null);
    try {
      const r = await axios.get(`${API}/faostat/country-detail/${iso3}?language=${language}`);
      setDetail(r.data);
    } catch (err) {
      console.error('Error fetching country detail:', err);
    } finally {
      setLoading(false);
    }
  };

  // ── Charts data ──────────────────────────────────────────────────────────
  const culturesChartData = () =>
    (detail?.cultures || []).map((c, i) => ({
      name: c.name.length > 14 ? c.name.slice(0, 14) + '…' : c.name,
      fullName: c.name,
      value: c.value_2023,
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
      { name: t.capture, value: p.capture_tonnes, fill: COLORS_PECHE[0] },
      { name: t.aquaculture, value: p.aquaculture_tonnes, fill: COLORS_PECHE[2] },
    ].filter(x => x.value > 0);
  };

  const evoLines = Object.keys(detail?.evolution || {}).slice(0, 5);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-5">

      {/* Header */}
      <Card className="bg-gradient-to-r from-green-700 via-emerald-700 to-teal-700 text-white shadow-xl overflow-hidden">
        <CardHeader>
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <CardTitle className="text-2xl font-bold flex items-center gap-3">
                <Wheat className="w-7 h-7" /> {t.title}
              </CardTitle>
              <CardDescription className="text-green-100 mt-1">{t.subtitle}</CardDescription>
            </div>
            {faoStats && (
              <div className="flex flex-col items-end gap-1">
                <Badge className="bg-white/20 text-white text-sm px-3 py-1">
                  <Globe className="w-3 h-3 mr-1" /> {faoStats.total_countries} pays
                </Badge>
                <span className="text-xs text-green-200">
                  {faoStats.total_commodities} produits · {faoStats.data_year}
                </span>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Country Selector */}
      <Card className="border-2 border-green-200 shadow-lg" style={{ overflow: 'visible' }}>
        <CardContent className="pt-5" style={{ overflow: 'visible' }}>
          <EnhancedCountrySelector
            value={country}
            onChange={setCountry}
            label={t.selectCountry}
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
              <Loader2 className="w-10 h-10 animate-spin text-green-600 mx-auto" />
              <p className="mt-3 text-gray-500">{t.loading}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Country detail */}
      {!loading && detail && (
        <>
          {/* Country header */}
          <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
            <CardHeader>
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                  <CardTitle className="text-xl text-green-800 flex items-center gap-2">
                    <span className="text-3xl">🌍</span> {detail.country_name}
                    <Badge variant="outline" className="border-green-500 text-green-700 text-xs ml-2">
                      {detail.region}
                    </Badge>
                  </CardTitle>
                  <div className="flex gap-2 mt-2 flex-wrap">
                    <Badge className="bg-green-100 text-green-800 border-green-300">
                      {detail.cultures?.length || 0} cultures
                    </Badge>
                    {detail.has_livestock && (
                      <Badge className="bg-amber-100 text-amber-800 border-amber-300">
                        <Beef className="w-3 h-3 mr-1" /> Élevage
                      </Badge>
                    )}
                    {detail.has_fisheries && (
                      <Badge className="bg-blue-100 text-blue-800 border-blue-300">
                        <Fish className="w-3 h-3 mr-1" /> Pêche
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">{t.source}</p>
                  <p className="text-xs font-medium text-gray-700">{detail.source}</p>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Sub-tabs: Cultures / Élevage / Pêche */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-5">
            <TabsList className="grid w-full grid-cols-3 bg-green-100 p-1 h-auto">
              <TabsTrigger
                value="cultures"
                className="data-[state=active]:bg-green-600 data-[state=active]:text-white py-2.5"
              >
                <Wheat className="w-4 h-4 mr-2" /> {t.tabCultures}
              </TabsTrigger>
              <TabsTrigger
                value="elevage"
                className="data-[state=active]:bg-amber-600 data-[state=active]:text-white py-2.5"
                disabled={!detail.has_livestock}
              >
                <Beef className="w-4 h-4 mr-2" /> {t.tabElevage}
              </TabsTrigger>
              <TabsTrigger
                value="peche"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white py-2.5"
                disabled={!detail.has_fisheries}
              >
                <Fish className="w-4 h-4 mr-2" /> {t.tabPeche}
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
                        <CardTitle className="text-base text-gray-700 flex items-center gap-2">
                          <BarChart3 className="w-4 h-4 text-green-600" /> {t.production}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={320}>
                          <BarChart data={culturesChartData()} layout="vertical" margin={{ left: 10, right: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" tickFormatter={fmt} tick={{ fontSize: 11 }} />
                            <YAxis type="category" dataKey="name" width={105} tick={{ fontSize: 11 }} />
                            <Tooltip
                              formatter={(v, _, p) => [fmtUnit(v, t.tonnes), p?.payload?.fullName || '']}
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
                        <CardTitle className="text-base text-gray-700">{t.cultures}</CardTitle>
                      </CardHeader>
                      <CardContent className="p-0">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-green-50 border-b">
                                <th className="text-left px-3 py-2 font-semibold">Produit</th>
                                <th className="text-right px-3 py-2 font-semibold">{t.production}</th>
                                <th className="text-right px-3 py-2 font-semibold hidden sm:table-cell">{t.surface}</th>
                                <th className="text-center px-3 py-2 font-semibold">{t.rankAfrique}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detail.cultures.map((c, i) => (
                                <tr key={c.name} className="border-b hover:bg-gray-50">
                                  <td className="px-3 py-2">
                                    <div className="flex items-center gap-2">
                                      <div className="w-3 h-3 rounded-full flex-shrink-0"
                                        style={{ backgroundColor: COLORS_CULTURES[i % COLORS_CULTURES.length] }} />
                                      <span className="font-medium">{c.name}</span>
                                    </div>
                                  </td>
                                  <td className="px-3 py-2 text-right font-mono text-green-700 font-bold">
                                    {fmt(c.value_2023)} t
                                  </td>
                                  <td className="px-3 py-2 text-right text-gray-500 hidden sm:table-cell">
                                    {c.area_ha ? `${fmt(c.area_ha)} ha` : '—'}
                                  </td>
                                  <td className="px-3 py-2 text-center">
                                    {c.rank_africa ? (
                                      <Badge className={`text-xs ${c.rank_africa <= 3 ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-700'}`}>
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
                        <CardTitle className="text-base text-green-700 flex items-center gap-2">
                          <TrendingUp className="w-4 h-4" /> {t.evolution}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={280}>
                          <LineChart data={evolutionChartData()}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="year" />
                            <YAxis tickFormatter={fmt} />
                            <Tooltip formatter={(v) => [fmt(v) + ' ' + t.tonnes]} />
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
                    <Card className="shadow-md bg-green-50 border-green-200">
                      <CardHeader>
                        <CardTitle className="text-base text-green-800 flex items-center gap-2">
                          <Info className="w-4 h-4" /> {t.indicators}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {detail.key_indicators.agri_gdp_percent && (
                            <div className="text-center">
                              <p className="text-2xl font-bold text-green-700">{detail.key_indicators.agri_gdp_percent}%</p>
                              <p className="text-xs text-gray-600 mt-1">{t.agriGDP}</p>
                            </div>
                          )}
                          {detail.key_indicators.agri_employment_percent && (
                            <div className="text-center">
                              <p className="text-2xl font-bold text-green-700">{detail.key_indicators.agri_employment_percent}%</p>
                              <p className="text-xs text-gray-600 mt-1">{t.agriEmploy}</p>
                            </div>
                          )}
                          {detail.key_indicators.arable_land_ha && (
                            <div className="text-center">
                              <p className="text-2xl font-bold text-green-700">{fmt(detail.key_indicators.arable_land_ha)}</p>
                              <p className="text-xs text-gray-600 mt-1">{t.arable} (ha)</p>
                            </div>
                          )}
                          {detail.key_indicators.irrigated_land_ha && (
                            <div className="text-center">
                              <p className="text-2xl font-bold text-blue-700">{fmt(detail.key_indicators.irrigated_land_ha)}</p>
                              <p className="text-xs text-gray-600 mt-1">{t.irrigated} (ha)</p>
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
                    <AlertTriangle className="w-10 h-10 text-amber-500 flex-shrink-0" />
                    <p className="text-gray-600">{t.noData}</p>
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
                        <CardTitle className="text-base text-amber-800 flex items-center gap-2">
                          <Beef className="w-4 h-4" /> {t.livestock} 2023
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={280}>
                          <BarChart data={elevageChartData()} layout="vertical" margin={{ left: 10, right: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" tickFormatter={fmt} tick={{ fontSize: 11 }} />
                            <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
                            <Tooltip formatter={(v) => [fmt(v) + ' ' + t.tetes]} />
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
                        <CardTitle className="text-base text-amber-800">{t.livestock}</CardTitle>
                      </CardHeader>
                      <CardContent className="p-0">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-amber-50 border-b">
                              <th className="text-left px-3 py-2 font-semibold">Espèce</th>
                              <th className="text-right px-3 py-2 font-semibold">Effectif</th>
                              <th className="text-center px-3 py-2 font-semibold">{t.rankAfrique}</th>
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
                                <td className="px-3 py-2.5 text-right font-mono font-bold text-amber-800">
                                  {fmt(e.value)} {e.unit}
                                </td>
                                <td className="px-3 py-2.5 text-center">
                                  {e.rank_africa ? (
                                    <Badge className={`text-xs ${e.rank_africa <= 5 ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-700'}`}>
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
                    <Card className="shadow-md bg-amber-50 border-amber-200">
                      <CardHeader>
                        <CardTitle className="text-base text-amber-900">{t.livestockProd} 2023</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(detail.livestock_production_2023).map(([name, d]) => (
                            <div key={name} className="text-center bg-white rounded-xl p-3 border border-amber-100 shadow-sm">
                              <p className="text-xl font-bold text-amber-700">{fmt(d.value)}</p>
                              <p className="text-xs text-gray-500 mt-1">{d.unit}</p>
                              <p className="text-sm font-medium text-gray-700 mt-1">{name}</p>
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
                    <AlertTriangle className="w-10 h-10 text-amber-500 flex-shrink-0" />
                    <p className="text-gray-600">{t.noLivestock}</p>
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
                    <Card className="shadow-md border-l-4 border-l-blue-500 bg-blue-50">
                      <CardContent className="pt-5">
                        <div className="flex items-center gap-4">
                          <Fish className="w-10 h-10 text-blue-600 flex-shrink-0" />
                          <div>
                            <p className="text-3xl font-bold text-blue-800">
                              {fmt(detail.peche_aquaculture?.capture_tonnes)} t
                            </p>
                            <p className="text-sm text-blue-600 mt-1">{t.capture} 2023</p>
                            {detail.peche_aquaculture?.capture_rank_africa && (
                              <Badge className="bg-blue-100 text-blue-800 mt-2 text-xs">
                                Rang Afrique #{detail.peche_aquaculture.capture_rank_africa}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="shadow-md border-l-4 border-l-teal-500 bg-teal-50">
                      <CardContent className="pt-5">
                        <div className="flex items-center gap-4">
                          <Droplets className="w-10 h-10 text-teal-600 flex-shrink-0" />
                          <div>
                            <p className="text-3xl font-bold text-teal-800">
                              {fmt(detail.peche_aquaculture?.aquaculture_tonnes)} t
                            </p>
                            <p className="text-sm text-teal-600 mt-1">{t.aquaculture} 2023</p>
                            {detail.peche_aquaculture?.aquaculture_rank_africa && (
                              <Badge className="bg-teal-100 text-teal-800 mt-2 text-xs">
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
                        <CardTitle className="text-base text-blue-800">Répartition de la production halieutique</CardTitle>
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
                        <CardTitle className="text-base text-blue-800">Détails pêche & aquaculture</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {detail.peche_aquaculture?.species?.length > 0 && (
                          <div>
                            <p className="text-sm font-semibold text-gray-700 mb-2">
                              <Fish className="w-3.5 h-3.5 inline mr-1 text-blue-500" /> {t.species}
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {detail.peche_aquaculture.species.map(s => (
                                <Badge key={s} className="bg-blue-50 text-blue-700 border-blue-200">{s}</Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        {detail.peche_aquaculture?.main_ports?.length > 0 && (
                          <div>
                            <p className="text-sm font-semibold text-gray-700 mb-2">
                              ⚓ {t.ports}
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {detail.peche_aquaculture.main_ports.map(p => (
                                <Badge key={p} className="bg-gray-100 text-gray-700">{p}</Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
                          <p className="text-xs text-gray-500">Source : FAO FishStat 2023 / Direction des Pêches</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              ) : (
                <Card className="border-l-4 border-l-blue-400">
                  <CardContent className="flex items-center gap-4 py-8">
                    <AlertTriangle className="w-10 h-10 text-blue-500 flex-shrink-0" />
                    <p className="text-gray-600">{t.noFisheries}</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </>
      )}

      {/* No data fallback */}
      {!loading && !detail && (
        <Card className="border-l-4 border-l-amber-400">
          <CardContent className="flex items-center gap-4 py-8">
            <AlertTriangle className="w-10 h-10 text-amber-500 flex-shrink-0" />
            <p className="text-gray-600">{t.noData}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
