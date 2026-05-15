import React from 'react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function PortDetailsModal({ isOpen, onClose, port, language = 'fr' }) {
  const texts = {
    fr: {
      teuYear: 'TEU/an', tonsYear: 'Tonnes/an', calls: 'Escales', portTime: 'Temps Port',
      waiting: 'Attente', berthProductivity: 'Productivité Quai', movesPerHour: 'mvt/h',
      worldRank: 'mondial', agents: 'Agents', services: 'Lignes', evolution: 'Évolution',
      info: 'Infos', authority: 'Autorité', lpi: 'LPI',
      noAgents: 'Aucun agent maritime répertorié.', noServices: 'Aucune ligne régulière répertoriée.',
      noHistorical: 'Aucune donnée historique.', frequency: 'Fréquence', rotation: 'Rotation',
      teuEvolution: 'Évolution TEU', portTimeEvolution: "Évolution temps d'attente (h)",
      annualComparison: 'Comparatif annuel', year: 'Année', teu: 'TEU', tons: 'Tonnes',
      coordinates: 'Coordonnées GPS', timezone: 'Fuseau horaire', lastUpdate: 'Mise à jour',
      source: 'Source', hours: 'h', days: 'j',
      dwellTime: 'Séjour conteneurs', vesselWaiting: 'Attente navires',
      lpiOverall: 'LPI Global', lpiCustoms: 'Douanes', lpiInfra: 'Infrastructure',
      lpiTimeliness: 'Ponctualité', globalBenchmarks: 'Benchmarks Mondiaux',
      africaAvg: 'Moy. Afrique', globalMedian: 'Médiane mondiale (H2-2023)',
      logistics_network: 'Réseau Logistique', global_carriers: 'Transporteurs Mondiaux',
      regional_specialists: 'Spécialistes Régionaux', service_providers: 'Prestataires',
      factualData: 'Données factuelles',
    },
    en: {
      teuYear: 'TEU/year', tonsYear: 'Tons/year', calls: 'Calls', portTime: 'Port Time',
      waiting: 'Waiting', berthProductivity: 'Berth Productivity', movesPerHour: 'moves/h',
      worldRank: 'world', agents: 'Agents', services: 'Lines', evolution: 'Evolution',
      info: 'Info', authority: 'Authority', lpi: 'LPI',
      noAgents: 'No maritime agents listed.', noServices: 'No regular lines listed.',
      noHistorical: 'No historical data available.', frequency: 'Frequency', rotation: 'Rotation',
      teuEvolution: 'Container Traffic (TEU)', portTimeEvolution: 'Waiting Time (hours)',
      annualComparison: 'Annual Comparison', year: 'Year', teu: 'TEU', tons: 'Tons',
      coordinates: 'GPS Coordinates', timezone: 'Timezone', lastUpdate: 'Last update',
      source: 'Source', hours: 'h', days: 'd',
      dwellTime: 'Container dwell time', vesselWaiting: 'Vessel waiting',
      lpiOverall: 'Overall LPI', lpiCustoms: 'Customs', lpiInfra: 'Infrastructure',
      lpiTimeliness: 'Timeliness', globalBenchmarks: 'Global Benchmarks',
      africaAvg: 'Africa Avg.', globalMedian: 'Global Median (H2-2023)',
      logistics_network: 'Logistics Network', global_carriers: 'Global Carriers',
      regional_specialists: 'Regional Specialists', service_providers: 'Service Providers',
      factualData: 'Factual data points',
    },
  };

  const t = texts[language];
  if (!port) return null;

  const agents = port.agents || [];
  const services = port.services || [];
  // ports use traffic_evolution field (not historical_stats)
  const historicalStats = port.traffic_evolution || port.historical_stats || [];
  const lsci = port.lsci || null;
  const latestStats = port.latest_stats || {};
  const perfMetrics = port.performance_metrics || {};
  const portAuthority = port.port_authority || null;
  const trsAnalysis = port.trs_analysis || null;
  const lpi2023 = port.lpi_2023 || null;
  const globalBenchmarks = port.global_benchmarks || null;
  const logisticsNetwork = port.logistics_network || null;

  const formatNumber = (num) => {
    if (num === null || num === undefined || num === 'NA') return 'N/A';
    if (typeof num !== 'number') return String(num);
    return language === 'en' ? num.toLocaleString('en-US') : num.toLocaleString('fr-FR');
  };

  const gradeColor = (grade) => {
    if (!grade) return '';
    if (grade.startsWith('A')) return 'bg-green-600';
    if (grade.startsWith('B')) return 'bg-yellow-600';
    if (grade.startsWith('C')) return 'bg-orange-600';
    return 'bg-red-600';
  };

  const lpiScoreColor = (score) => {
    if (!score) return 'text-gray-500';
    if (score >= 3.5) return 'text-green-600 font-bold';
    if (score >= 2.5) return 'text-yellow-600 font-bold';
    return 'text-red-600 font-bold';
  };

  const chartData = historicalStats.map((s) => ({
    year: s.year,
    teu: s.teu || s.container_throughput_teu,
    vessels: s.vessels || s.vessel_calls,
    avg_wait: s.avg_wait_time || s.median_time_in_port_hours,
  }));

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-blue-900 flex items-center gap-2">
            <span>&#x1F6A2;</span>
            <span>{port.port_name}</span>
          </DialogTitle>
          <DialogDescription>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <Badge variant="outline">{port.country_name}</Badge>
              <Badge variant="secondary">{port.port_type}</Badge>
              {port.un_locode && <Badge>{port.un_locode}</Badge>}
              {(perfMetrics.efficiency_grade || latestStats.performance_grade) && (
                <Badge className={`${gradeColor(perfMetrics.efficiency_grade || latestStats.performance_grade)} text-white`}>
                  Grade: {perfMetrics.efficiency_grade || latestStats.performance_grade}
                </Badge>
              )}
              {lsci && (
                <Badge className="bg-indigo-600 text-white">
                  LSCI: {lsci.value} (#{lsci.world_rank} {t.worldRank})
                </Badge>
              )}
            </div>
          </DialogDescription>
        </DialogHeader>

        {/* KPI Row 1 */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 my-4">
          <div className="bg-blue-50 p-3 rounded-lg text-center">
            <p className="text-xs text-blue-700 font-semibold">&#x1F4E6; {t.teuYear}</p>
            <p className="text-lg font-bold text-blue-600">{formatNumber(latestStats.container_throughput_teu)}</p>
            <p className="text-xs text-gray-500">{latestStats.year || 2024}</p>
          </div>
          <div className="bg-green-50 p-3 rounded-lg text-center">
            <p className="text-xs text-green-700 font-semibold">&#x2696;&#xFE0F; {t.tonsYear}</p>
            <p className="text-lg font-bold text-green-600">{formatNumber(latestStats.cargo_throughput_tons)}</p>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg text-center">
            <p className="text-xs text-purple-700 font-semibold">&#x2693; {t.calls}</p>
            <p className="text-lg font-bold text-purple-600">{formatNumber(latestStats.vessel_calls)}</p>
          </div>
          <div className="bg-orange-50 p-3 rounded-lg text-center">
            <p className="text-xs text-orange-700 font-semibold">&#x23F1;&#xFE0F; {t.portTime}</p>
            <p className="text-lg font-bold text-orange-600">
              {perfMetrics.avg_port_stay_hours
                ? `${perfMetrics.avg_port_stay_hours}${t.hours}`
                : latestStats.median_time_in_port_hours
                ? `${latestStats.median_time_in_port_hours}${t.hours}`
                : 'N/A'}
            </p>
          </div>
          <div className="bg-pink-50 p-3 rounded-lg text-center">
            <p className="text-xs text-pink-700 font-semibold">&#x23F3; {t.waiting}</p>
            <p className="text-lg font-bold text-pink-600">
              {perfMetrics.avg_waiting_time_hours
                ? `${perfMetrics.avg_waiting_time_hours}${t.hours}`
                : latestStats.average_waiting_time_hours
                ? `${latestStats.average_waiting_time_hours}${t.hours}`
                : 'N/A'}
            </p>
          </div>
        </div>

        {/* KPI Row 2 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          {(perfMetrics.berth_productivity || latestStats.berth_productivity_moves_per_hour) && (
            <div className="bg-gradient-to-r from-cyan-50 to-blue-50 p-3 rounded-lg border-l-4 border-cyan-500">
              <p className="text-xs font-semibold text-cyan-700">&#x1F3D7;&#xFE0F; {t.berthProductivity}</p>
              <p className="text-lg font-bold text-cyan-900">
                {perfMetrics.berth_productivity || latestStats.berth_productivity_moves_per_hour} {t.movesPerHour}
              </p>
            </div>
          )}
          {trsAnalysis && trsAnalysis.container_dwell_time_days && trsAnalysis.container_dwell_time_days !== 'NA' && (
            <div className="bg-gradient-to-r from-amber-50 to-yellow-50 p-3 rounded-lg border-l-4 border-amber-500">
              <p className="text-xs font-semibold text-amber-700">&#x1F4E6; {t.dwellTime}</p>
              <p className="text-lg font-bold text-amber-900">{trsAnalysis.container_dwell_time_days} {t.days}</p>
              <p className="text-xs text-amber-600 truncate">{trsAnalysis.source_reliability_label || trsAnalysis.source_type}</p>
            </div>
          )}
          {trsAnalysis && (trsAnalysis.vessel_waiting_days || (trsAnalysis.vessel_turnaround_hours && trsAnalysis.vessel_turnaround_hours !== 'NA')) && (
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-3 rounded-lg border-l-4 border-indigo-500">
              <p className="text-xs font-semibold text-indigo-700">&#x1F6A2; {t.vesselWaiting}</p>
              <p className="text-lg font-bold text-indigo-900">
                {trsAnalysis.vessel_waiting_days
                  ? `${trsAnalysis.vessel_waiting_days} ${t.days}`
                  : `${trsAnalysis.vessel_turnaround_hours}${t.hours}`}
              </p>
              {trsAnalysis.vessel_waiting_source && (
                <p className="text-xs text-indigo-500 truncate">{trsAnalysis.vessel_waiting_source.split(',')[0]}</p>
              )}
            </div>
          )}
        </div>

        {/* Tabs */}
        <Tabs defaultValue="agents" className="w-full">
          <TabsList className="grid w-full grid-cols-6 text-xs">
            <TabsTrigger value="agents">&#x1F465; {t.agents} ({agents.length})</TabsTrigger>
            <TabsTrigger value="services">&#x1F6A2; {t.services} ({services.length})</TabsTrigger>
            <TabsTrigger value="stats">&#x1F4C8; {t.evolution}</TabsTrigger>
            <TabsTrigger value="lpi">&#x1F30D; {t.lpi}</TabsTrigger>
            <TabsTrigger value="authority">&#x1F3DB;&#xFE0F; {t.authority}</TabsTrigger>
            <TabsTrigger value="info">&#x2139;&#xFE0F; {t.info}</TabsTrigger>
          </TabsList>

          {/* AGENTS */}
          <TabsContent value="agents" className="mt-4">
            {agents.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {agents.map((agent, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500 hover:bg-gray-100 transition-colors">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-bold text-gray-900">{agent.agent_name}</p>
                          {agent.group && <Badge variant="outline" className="text-xs">{agent.group}</Badge>}
                        </div>
                        {agent.address && <p className="text-xs text-gray-500 mt-1">&#x1F4CD; {agent.address}</p>}
                        <div className="flex flex-wrap gap-2 mt-1">
                          {agent.contact && (
                            <a href={`tel:${agent.contact}`} className="text-xs text-blue-600 hover:underline">&#x1F4DE; {agent.contact}</a>
                          )}
                          {agent.email && (
                            <a href={`mailto:${agent.email}`} className="text-xs text-blue-600 hover:underline">&#x2709;&#xFE0F; {agent.email}</a>
                          )}
                          {agent.website && (
                            <a href={agent.website.startsWith('http') ? agent.website : `https://${agent.website}`}
                              target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline">
                              &#x1F310; {agent.website.replace(/^https?:\/\//, '')}
                            </a>
                          )}
                        </div>
                        {agent.operating_hours && <p className="text-xs text-gray-500 mt-1">&#x1F550; {agent.operating_hours}</p>}
                      </div>
                      <div className="flex flex-col gap-1 items-end shrink-0">
                        {agent.certifications?.map((cert, i) => (
                          <Badge key={i} className="bg-green-100 text-green-800 text-xs">{cert}</Badge>
                        ))}
                      </div>
                    </div>
                    {(agent.services?.length > 0 || agent.cargo_types?.length > 0) && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {agent.services?.map((s, i) => (
                          <Badge key={i} variant="secondary" className="text-xs bg-blue-50 text-blue-700">{s}</Badge>
                        ))}
                        {agent.cargo_types?.map((ct, i) => (
                          <Badge key={`ct-${i}`} variant="secondary" className="text-xs bg-purple-50 text-purple-700">{ct}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-8 text-gray-500"><p>{t.noAgents}</p></div>
            )}
          </TabsContent>

          {/* SERVICES */}
          <TabsContent value="services" className="mt-4">
            {services.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {services.map((service, index) => (
                  <div key={index} className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-200">
                    <p className="font-bold text-blue-900 flex items-center gap-2">
                      <span>&#x1F6A2;</span><span>{service.carrier}</span>
                    </p>
                    <p className="text-sm text-gray-800 font-semibold mt-1">{service.service_name}</p>
                    {service.frequency && (
                      <p className="text-sm text-gray-700 mt-1">
                        <span className="font-semibold">{t.frequency}:</span> {service.frequency}
                      </p>
                    )}
                    {service.rotation && (
                      <p className="text-xs text-gray-600 mt-1">
                        <span className="font-semibold">{t.rotation}:</span> {service.rotation}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-8 text-gray-500"><p>{t.noServices}</p></div>
            )}
          </TabsContent>

          {/* EVOLUTION */}
          <TabsContent value="stats" className="mt-4">
            {chartData.length > 0 ? (
              <div className="space-y-4">
                <div className="bg-white p-4 rounded-lg border">
                  <h3 className="text-sm font-bold text-gray-700 mb-3">{t.teuEvolution}</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="year" />
                      <YAxis />
                      <Tooltip formatter={(value) => formatNumber(value)} />
                      <Line type="monotone" dataKey="teu" stroke="#3b82f6" strokeWidth={2} name="TEU" dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                {chartData.some((d) => d.avg_wait) && (
                  <div className="bg-white p-4 rounded-lg border">
                    <h3 className="text-sm font-bold text-gray-700 mb-3">{t.portTimeEvolution}</h3>
                    <ResponsiveContainer width="100%" height={180}>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="year" />
                        <YAxis />
                        <Tooltip formatter={(v) => `${v}${t.hours}`} />
                        <Line type="monotone" dataKey="avg_wait" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
                <div className="bg-white p-4 rounded-lg border">
                  <h3 className="text-sm font-bold text-gray-700 mb-3">{t.annualComparison}</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b bg-gray-50">
                          <th className="text-left p-2">{t.year}</th>
                          <th className="text-right p-2">{t.teu}</th>
                          <th className="text-right p-2">{language === 'fr' ? 'Navires' : 'Vessels'}</th>
                          <th className="text-right p-2">{t.waiting}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {chartData.map((stat, idx) => (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="p-2 font-bold">{stat.year}</td>
                            <td className="text-right p-2">{formatNumber(stat.teu)}</td>
                            <td className="text-right p-2">{formatNumber(stat.vessels)}</td>
                            <td className="text-right p-2">{stat.avg_wait ? `${stat.avg_wait}${t.hours}` : 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center p-8 text-gray-500"><p>{t.noHistorical}</p></div>
            )}
          </TabsContent>

          {/* LPI */}
          <TabsContent value="lpi" className="mt-4 space-y-4">
            {lpi2023 && (
              <div className="bg-white p-4 rounded-lg border">
                <h3 className="text-sm font-bold text-gray-700 mb-3">
                  &#x1F4CA; {t.lpiOverall} — World Bank {lpi2023.year || 2023}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  {[
                    { label: t.lpiOverall, value: lpi2023.overall_score, icon: '&#x1F30D;' },
                    { label: t.lpiCustoms, value: lpi2023.customs_score, icon: '&#x1F6C3;' },
                    { label: t.lpiInfra, value: lpi2023.infrastructure_score, icon: '&#x1F3D7;&#xFE0F;' },
                    { label: t.lpiTimeliness, value: lpi2023.timeliness_score, icon: '&#x23F1;&#xFE0F;' },
                  ].map((item, i) => (
                    <div key={i} className="bg-gray-50 p-3 rounded-lg text-center">
                      <p className={`text-xl font-bold ${lpiScoreColor(item.value)}`}>{item.value ?? 'N/A'}</p>
                      <p className="text-xs text-gray-600">{item.label}</p>
                      <p className="text-xs text-gray-400">/5.0</p>
                    </div>
                  ))}
                </div>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={[
                    { dim: 'Global', val: lpi2023.overall_score },
                    { dim: t.lpiCustoms.slice(0, 8), val: lpi2023.customs_score },
                    { dim: 'Infra', val: lpi2023.infrastructure_score },
                    { dim: t.lpiTimeliness.slice(0, 8), val: lpi2023.timeliness_score },
                  ].filter(d => d.val != null)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="dim" tick={{ fontSize: 10 }} />
                    <YAxis domain={[0, 5]} />
                    <Tooltip formatter={(v) => `${v}/5.0`} />
                    <Bar dataKey="val" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                {lpi2023.world_rank && (
                  <p className="mt-2 text-xs text-gray-500 text-right">
                    Rang mondial: #{lpi2023.world_rank} &#x2022; {lpi2023.source}
                  </p>
                )}
              </div>
            )}
            {lsci && (
              <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-lg border border-indigo-200">
                <h3 className="text-sm font-bold text-indigo-700 mb-2">
                  &#x1F310; LSCI — {language === 'fr' ? 'Connectivité Maritime' : 'Maritime Connectivity'} ({lsci.year})
                </h3>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <p className="text-3xl font-bold text-indigo-900">{lsci.value}</p>
                    <p className="text-xs text-gray-600">/100</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-indigo-700">#{lsci.world_rank}</p>
                    <p className="text-xs text-gray-600">{t.worldRank}</p>
                  </div>
                </div>
              </div>
            )}
            {globalBenchmarks && (
              <div className="bg-gray-50 p-4 rounded-lg border">
                <h3 className="text-sm font-bold text-gray-700 mb-3">&#x1F30D; {t.globalBenchmarks}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-orange-50 p-3 rounded border-l-4 border-orange-400">
                    <p className="text-xs font-semibold text-orange-700">{t.africaAvg}</p>
                    <p className="text-xl font-bold text-orange-900">{globalBenchmarks.africa_avg_dwell_days} {t.days}</p>
                    <p className="text-xs text-gray-500">{globalBenchmarks.africa_avg_source}</p>
                  </div>
                  {globalBenchmarks.global_median_dwell_days_h2_2023 && (
                    <div className="bg-green-50 p-3 rounded border-l-4 border-green-400">
                      <p className="text-xs font-semibold text-green-700">{t.globalMedian}</p>
                      <p className="text-xl font-bold text-green-900">{globalBenchmarks.global_median_dwell_days_h2_2023} {t.days}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
            {trsAnalysis && (
              <div className={`p-4 rounded-lg border-l-4 ${trsAnalysis.warning ? 'bg-yellow-50 border-yellow-400' : 'bg-blue-50 border-blue-400'}`}>
                <h3 className="text-sm font-bold text-gray-700 mb-2">
                  &#x1F4CB; TRS — Time Release Study
                  {trsAnalysis.source_reliability_label && (
                    <Badge className="ml-2 text-xs bg-yellow-100 text-yellow-800">{trsAnalysis.source_reliability_label}</Badge>
                  )}
                </h3>
                {trsAnalysis.warning && (
                  <p className="text-xs text-yellow-700 mb-2 italic">{trsAnalysis.warning.substring(0, 200)}&#x2026;</p>
                )}
                {trsAnalysis.factual_data_points?.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-semibold text-gray-600 mb-1">{t.factualData}:</p>
                    <ul className="list-disc list-inside space-y-0.5">
                      {trsAnalysis.factual_data_points.map((pt, i) => (
                        <li key={i} className="text-xs text-gray-700">{pt}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {trsAnalysis.notes && <p className="text-xs text-gray-600">{trsAnalysis.notes}</p>}
              </div>
            )}
            {!lpi2023 && !lsci && !globalBenchmarks && !trsAnalysis && (
              <div className="text-center p-8 text-gray-400">
                <p>{language === 'fr' ? 'Aucune donnée LPI disponible' : 'No LPI data available'}</p>
              </div>
            )}
          </TabsContent>

          {/* AUTHORITY */}
          <TabsContent value="authority" className="mt-4 space-y-4">
            {portAuthority ? (
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200">
                <h3 className="text-base font-bold text-blue-800 mb-3">&#x1F3DB;&#xFE0F; {portAuthority.name}</h3>
                <div className="space-y-2 text-sm">
                  {portAuthority.address && (
                    <p className="flex items-start gap-2">
                      <span className="text-blue-500">&#x1F4CD;</span><span>{portAuthority.address}</span>
                    </p>
                  )}
                  {portAuthority.contact_phone && (
                    <p className="flex items-center gap-2">
                      <span className="text-blue-500">&#x1F4DE;</span>
                      <a href={`tel:${portAuthority.contact_phone}`} className="text-blue-600 hover:underline">{portAuthority.contact_phone}</a>
                    </p>
                  )}
                  {portAuthority.contact_email && (
                    <p className="flex items-center gap-2">
                      <span className="text-blue-500">&#x2709;&#xFE0F;</span>
                      <a href={`mailto:${portAuthority.contact_email}`} className="text-blue-600 hover:underline">{portAuthority.contact_email}</a>
                    </p>
                  )}
                  {portAuthority.website && (
                    <p className="flex items-center gap-2">
                      <span className="text-blue-500">&#x1F310;</span>
                      <a href={portAuthority.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{portAuthority.website}</a>
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center p-6 text-gray-400">
                <p>{language === 'fr' ? 'Données autorité non disponibles' : 'Port authority data unavailable'}</p>
              </div>
            )}
            {logisticsNetwork && (
              <div className="bg-white p-4 rounded-lg border">
                <h3 className="text-sm font-bold text-gray-700 mb-3">&#x1F517; {t.logistics_network}</h3>
                {logisticsNetwork.global_carriers_present?.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-1">{t.global_carriers}</p>
                    <div className="flex flex-wrap gap-1">
                      {logisticsNetwork.global_carriers_present.map((c, i) => (
                        <Badge key={i} className="bg-blue-100 text-blue-800 text-xs">{c}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {logisticsNetwork.regional_specialists_present?.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-1">{t.regional_specialists}</p>
                    <div className="flex flex-wrap gap-1">
                      {logisticsNetwork.regional_specialists_present.map((c, i) => (
                        <Badge key={i} className="bg-green-100 text-green-800 text-xs">{c}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {logisticsNetwork.service_providers_available?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-1">{t.service_providers}</p>
                    <div className="flex flex-wrap gap-1">
                      {logisticsNetwork.service_providers_available.map((s, i) => (
                        <Badge key={i} variant="outline" className="text-xs">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* INFO */}
          <TabsContent value="info" className="mt-4 space-y-3">
            <div className="p-3 bg-gray-100 rounded-lg">
              <p className="text-sm">
                <span className="font-semibold">&#x1F4CD; {t.coordinates}:</span>{' '}
                {port.geo_lat ?? port.latitude}, {port.geo_lon ?? port.longitude}
              </p>
            </div>
            {port.timezone && (
              <div className="p-3 bg-gray-100 rounded-lg">
                <p className="text-sm"><span className="font-semibold">&#x1F550; {t.timezone}:</span> {port.timezone}</p>
              </div>
            )}
            {port.un_locode && (
              <div className="p-3 bg-gray-100 rounded-lg">
                <p className="text-sm"><span className="font-semibold">&#x1F516; UN LOCODE:</span> {port.un_locode}</p>
              </div>
            )}
            <div className="p-3 bg-gray-100 rounded-lg">
              <p className="text-sm">
                <span className="font-semibold">&#x1F4C5; {t.lastUpdate}:</span>{' '}
                {perfMetrics.last_updated || '2024'}
              </p>
            </div>
            {latestStats.source && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-700">
                  <span className="font-semibold">{t.source}:</span> {latestStats.source}
                </p>
              </div>
            )}
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-700">
                <span className="font-semibold">{t.source}:</span>{' '}
                UNCTAD Maritime Transport Review 2024 | World Bank LPI 2023 | AfCFTA Secretariat
              </p>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
