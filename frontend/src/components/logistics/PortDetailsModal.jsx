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
      logistics_network: 'Réseau Logistique', global_carriers: 'Transporteurs mondiaux',
      regional_specialists: 'Spécialistes régionaux', service_providers: 'Prestataires',
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
      logistics_network: 'Logistics Network', global_carriers: 'Global carriers',
      regional_specialists: 'Regional specialists', service_providers: 'Service providers',
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
    if (!score) return 'text-[var(--afcfta-muted)]';
    if (score >= 3.5) return 'text-[var(--success)] font-bold';
    if (score >= 2.5) return 'text-[var(--gold)] font-bold';
    return 'text-[var(--danger)] font-bold';
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
          <DialogTitle className="text-2xl font-bold text-[var(--info)] flex items-center gap-2">
            <span>&#x1F6A2;</span>
            <span>{port.port_name}</span>
          </DialogTitle>
          <DialogDescription>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <Badge variant="outline">{port.country_name}</Badge>
              <Badge variant="secondary">{port.port_type}</Badge>
              {port.un_locode && <Badge>{port.un_locode}</Badge>}
              {(perfMetrics.efficiency_grade || latestStats.performance_grade) && (
                <Badge className={`${gradeColor(perfMetrics.efficiency_grade || latestStats.performance_grade)} text-[var(--text)]`}>
                  Grade: {perfMetrics.efficiency_grade || latestStats.performance_grade}
                </Badge>
              )}
              {lsci && (
                <Badge className="bg-[var(--violet)] text-[var(--bg)]">
                  LSCI: {lsci.value} (#{lsci.world_rank} {t.worldRank})
                </Badge>
              )}
            </div>
          </DialogDescription>
        </DialogHeader>

        {/* KPI Row 1 */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 my-4">
          <div className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-3 rounded-lg text-center">
            <p className="text-xs text-[var(--info)] font-semibold">&#x1F4E6; {t.teuYear}</p>
            <p className="text-lg font-bold text-[var(--info)]">{formatNumber(latestStats.container_throughput_teu)}</p>
            <p className="text-xs text-[var(--afcfta-muted)]">{latestStats.year || 2024}</p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] p-3 rounded-lg text-center">
            <p className="text-xs text-[var(--success)] font-semibold">&#x2696;&#xFE0F; {t.tonsYear}</p>
            <p className="text-lg font-bold text-[var(--success)]">{formatNumber(latestStats.cargo_throughput_tons)}</p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] p-3 rounded-lg text-center">
            <p className="text-xs text-[var(--violet)] font-semibold">&#x2693; {t.calls}</p>
            <p className="text-lg font-bold text-[var(--violet)]">{formatNumber(latestStats.vessel_calls)}</p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] p-3 rounded-lg text-center">
            <p className="text-xs text-[var(--terra)] font-semibold">&#x23F1;&#xFE0F; {t.portTime}</p>
            <p className="text-lg font-bold text-[var(--terra)]">
              {perfMetrics.avg_port_stay_hours
                ? `${perfMetrics.avg_port_stay_hours}${t.hours}`
                : latestStats.median_time_in_port_hours
                ? `${latestStats.median_time_in_port_hours}${t.hours}`
                : 'N/A'}
            </p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] p-3 rounded-lg text-center">
            <p className="text-xs text-[var(--danger)] font-semibold">&#x23F3; {t.waiting}</p>
            <p className="text-lg font-bold text-[var(--danger)]">
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
            <div className="bg-[color-mix(in_srgb,var(--atlantic)_8%,var(--afcfta-card))] p-3 rounded-lg border-l-4 border-[color-mix(in_srgb,var(--atlantic)_30%,transparent)]">
              <p className="text-xs font-semibold text-[var(--atlantic)]">&#x1F3D7;&#xFE0F; {t.berthProductivity}</p>
              <p className="text-lg font-bold text-[var(--atlantic)]">
                {perfMetrics.berth_productivity || latestStats.berth_productivity_moves_per_hour} {t.movesPerHour}
              </p>
            </div>
          )}
          {trsAnalysis && trsAnalysis.container_dwell_time_days && trsAnalysis.container_dwell_time_days !== 'NA' && (
            <div className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] p-3 rounded-lg border-l-4 border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
              <p className="text-xs font-semibold text-[var(--gold)]">&#x1F4E6; {t.dwellTime}</p>
              <p className="text-lg font-bold text-[var(--gold)]">{trsAnalysis.container_dwell_time_days} {t.days}</p>
              <p className="text-xs text-[var(--gold)] truncate">{trsAnalysis.source_reliability_label || trsAnalysis.source_type}</p>
            </div>
          )}
          {trsAnalysis && (trsAnalysis.vessel_waiting_days || (trsAnalysis.vessel_turnaround_hours && trsAnalysis.vessel_turnaround_hours !== 'NA')) && (
            <div className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] p-3 rounded-lg border-l-4 border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
              <p className="text-xs font-semibold text-[var(--violet)]">&#x1F6A2; {t.vesselWaiting}</p>
              <p className="text-lg font-bold text-[var(--violet)]">
                {trsAnalysis.vessel_waiting_days
                  ? `${trsAnalysis.vessel_waiting_days} ${t.days}`
                  : `${trsAnalysis.vessel_turnaround_hours}${t.hours}`}
              </p>
              {trsAnalysis.vessel_waiting_source && (
                <p className="text-xs text-[var(--violet)] truncate">{trsAnalysis.vessel_waiting_source.split(',')[0]}</p>
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {agents.map((agent, index) => (
                  <div
                    key={index}
                    className="p-3 bg-[var(--afcfta-card2)] rounded-lg border-l-4 border-[color-mix(in_srgb,var(--info)_30%,transparent)] hover:bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] transition-colors flex flex-col gap-1"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-bold text-[var(--text)] text-sm leading-tight">{agent.agent_name}</p>
                      {agent.group && (
                        <Badge variant="outline" className="text-xs shrink-0">
                          {agent.group}
                        </Badge>
                      )}
                    </div>
                    {agent.role && (
                      <p className="text-xs text-[var(--info)] font-medium">{agent.role}</p>
                    )}
                    {agent.contact && (
                      <p className="text-xs text-[var(--afcfta-muted)] flex items-center gap-1">
                        <span>📞</span> {agent.contact}
                      </p>
                    )}
                    {agent.email && (
                      <p className="text-xs text-[var(--afcfta-muted)] flex items-center gap-1 truncate">
                        <span>✉️</span>
                        <span className="truncate">{agent.email}</span>
                      </p>
                    )}
                    {agent.services && agent.services.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {agent.services.map((s, i) => (
                          <span key={i} className="text-xs bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] px-1.5 py-0.5 rounded">
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                    {agent.cargo_types && agent.cargo_types.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {agent.cargo_types.map((c, i) => (
                          <span key={i} className="text-xs bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] px-1.5 py-0.5 rounded">
                            {c}
                          </span>
                        ))}
                      </div>
                    )}
                    {agent.operating_hours && (
                      <p className="text-xs text-[var(--afcfta-muted)]">🕐 {agent.operating_hours}</p>
                    )}
                    {agent.website && agent.website !== 'Non disponible' && (
                      <a
                        href={agent.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-[var(--info)] hover:underline truncate"
                      >
                        🌐 {agent.website.replace('https://','').replace('http://','').split('/')[0]}
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-8 text-[var(--afcfta-muted)]"><p>{t.noAgents}</p></div>
            )}
          </TabsContent>

          {/* SERVICES */}
          <TabsContent value="services" className="mt-4">
            {services.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {services.map((service, index) => (
                  <div key={index} className="p-4 bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                    <p className="font-bold text-[var(--info)] flex items-center gap-2">
                      <span>&#x1F6A2;</span><span>{service.carrier}</span>
                    </p>
                    <p className="text-sm text-[var(--text)] font-semibold mt-1">{service.service_name}</p>
                    {service.frequency && (
                      <p className="text-sm text-[var(--text)] mt-1">
                        <span className="font-semibold">{t.frequency}:</span> {service.frequency}
                      </p>
                    )}
                    {service.rotation && (
                      <p className="text-xs text-[var(--afcfta-muted)] mt-1">
                        <span className="font-semibold">{t.rotation}:</span> {service.rotation}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-8 text-[var(--afcfta-muted)]"><p>{t.noServices}</p></div>
            )}
          </TabsContent>

          {/* EVOLUTION */}
          <TabsContent value="stats" className="mt-4">
            {chartData.length > 0 ? (
              <div className="space-y-4">
                <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border">
                  <h3 className="text-sm font-bold text-[var(--text)] mb-3">{t.teuEvolution}</h3>
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
                  <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border">
                    <h3 className="text-sm font-bold text-[var(--text)] mb-3">{t.portTimeEvolution}</h3>
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
                <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border">
                  <h3 className="text-sm font-bold text-[var(--text)] mb-3">{t.annualComparison}</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b bg-[var(--afcfta-card2)]">
                          <th className="text-left p-2">{t.year}</th>
                          <th className="text-right p-2">{t.teu}</th>
                          <th className="text-right p-2">{language === 'fr' ? 'Navires' : 'Vessels'}</th>
                          <th className="text-right p-2">{t.waiting}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {chartData.map((stat, idx) => (
                          <tr key={idx} className="border-b hover:bg-[var(--afcfta-card2)]">
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
              <div className="text-center p-8 text-[var(--afcfta-muted)]"><p>{t.noHistorical}</p></div>
            )}
          </TabsContent>

          {/* LPI */}
          <TabsContent value="lpi" className="mt-4 space-y-4">
            {lpi2023 && (
              <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border">
                <h3 className="text-sm font-bold text-[var(--text)] mb-3">
                  &#x1F4CA; {t.lpiOverall} — World Bank {lpi2023.year || 2023}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  {[
                    { label: t.lpiOverall, value: lpi2023.overall_score, icon: '&#x1F30D;' },
                    { label: t.lpiCustoms, value: lpi2023.customs_score, icon: '&#x1F6C3;' },
                    { label: t.lpiInfra, value: lpi2023.infrastructure_score, icon: '&#x1F3D7;&#xFE0F;' },
                    { label: t.lpiTimeliness, value: lpi2023.timeliness_score, icon: '&#x23F1;&#xFE0F;' },
                  ].map((item, i) => (
                    <div key={i} className="bg-[var(--afcfta-card2)] p-3 rounded-lg text-center">
                      <p className={`text-xl font-bold ${lpiScoreColor(item.value)}`}>{item.value ?? 'N/A'}</p>
                      <p className="text-xs text-[var(--afcfta-muted)]">{item.label}</p>
                      <p className="text-xs text-[var(--afcfta-muted)]">/5.0</p>
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
                  <p className="mt-2 text-xs text-[var(--afcfta-muted)] text-right">
                    Rang mondial: #{lpi2023.world_rank} &#x2022; {lpi2023.source}
                  </p>
                )}
              </div>
            )}
            {lsci && (
              <div className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] p-4 rounded-lg border border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
                <h3 className="text-sm font-bold text-[var(--violet)] mb-2">
                  &#x1F310; LSCI — {language === 'fr' ? 'Connectivité Maritime' : 'Maritime Connectivity'} ({lsci.year})
                </h3>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <p className="text-3xl font-bold text-[var(--violet)]">{lsci.value}</p>
                    <p className="text-xs text-[var(--afcfta-muted)]">/100</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-[var(--violet)]">#{lsci.world_rank}</p>
                    <p className="text-xs text-[var(--afcfta-muted)]">{t.worldRank}</p>
                  </div>
                </div>
              </div>
            )}
            {globalBenchmarks && (
              <div className="bg-[var(--afcfta-card2)] p-4 rounded-lg border">
                <h3 className="text-sm font-bold text-[var(--text)] mb-3">&#x1F30D; {t.globalBenchmarks}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] p-3 rounded border-l-4 border-[color-mix(in_srgb,var(--terra)_30%,transparent)]">
                    <p className="text-xs font-semibold text-[var(--terra)]">{t.africaAvg}</p>
                    <p className="text-xl font-bold text-[var(--terra)]">{globalBenchmarks.africa_avg_dwell_days} {t.days}</p>
                    <p className="text-xs text-[var(--afcfta-muted)]">{globalBenchmarks.africa_avg_source}</p>
                  </div>
                  {globalBenchmarks.global_median_dwell_days_h2_2023 && (
                    <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] p-3 rounded border-l-4 border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                      <p className="text-xs font-semibold text-[var(--success)]">{t.globalMedian}</p>
                      <p className="text-xl font-bold text-[var(--success)]">{globalBenchmarks.global_median_dwell_days_h2_2023} {t.days}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
            {trsAnalysis && (
              <div className={`p-4 rounded-lg border-l-4 ${trsAnalysis.warning ? 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]' : 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--info)_30%,transparent)]'}`}>
                <h3 className="text-sm font-bold text-[var(--text)] mb-2">
                  &#x1F4CB; TRS — Time Release Study
                  {trsAnalysis.source_reliability_label && (
                    <Badge className="ml-2 text-xs bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]">{trsAnalysis.source_reliability_label}</Badge>
                  )}
                </h3>
                {trsAnalysis.warning && (
                  <p className="text-xs text-[var(--gold)] mb-2 italic">{trsAnalysis.warning.substring(0, 200)}&#x2026;</p>
                )}
                {trsAnalysis.factual_data_points?.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-semibold text-[var(--afcfta-muted)] mb-1">{t.factualData}:</p>
                    <ul className="list-disc list-inside space-y-0.5">
                      {trsAnalysis.factual_data_points.map((pt, i) => (
                        <li key={i} className="text-xs text-[var(--text)]">{pt}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {trsAnalysis.notes && <p className="text-xs text-[var(--afcfta-muted)]">{trsAnalysis.notes}</p>}
              </div>
            )}
            {!lpi2023 && !lsci && !globalBenchmarks && !trsAnalysis && (
              <div className="text-center p-8 text-[var(--afcfta-muted)]">
                <p>{language === 'fr' ? 'Aucune donnée LPI disponible' : 'No LPI data available'}</p>
              </div>
            )}
          </TabsContent>

          {/* AUTHORITY */}
          <TabsContent value="authority" className="mt-4 space-y-4">
            {portAuthority ? (
              <div className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-4 rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                <h3 className="text-base font-bold text-[var(--info)] mb-3">&#x1F3DB;&#xFE0F; {portAuthority.name}</h3>
                <div className="space-y-2 text-sm">
                  {portAuthority.address && (
                    <p className="flex items-start gap-2">
                      <span className="text-[var(--info)]">&#x1F4CD;</span><span>{portAuthority.address}</span>
                    </p>
                  )}
                  {portAuthority.contact_phone && (
                    <p className="flex items-center gap-2">
                      <span className="text-[var(--info)]">&#x1F4DE;</span>
                      <a href={`tel:${portAuthority.contact_phone}`} className="text-[var(--info)] hover:underline">{portAuthority.contact_phone}</a>
                    </p>
                  )}
                  {portAuthority.contact_email && (
                    <p className="flex items-center gap-2">
                      <span className="text-[var(--info)]">&#x2709;&#xFE0F;</span>
                      <a href={`mailto:${portAuthority.contact_email}`} className="text-[var(--info)] hover:underline">{portAuthority.contact_email}</a>
                    </p>
                  )}
                  {portAuthority.website && (
                    <p className="flex items-center gap-2">
                      <span className="text-[var(--info)]">&#x1F310;</span>
                      <a href={portAuthority.website} target="_blank" rel="noopener noreferrer" className="text-[var(--info)] hover:underline">{portAuthority.website}</a>
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center p-6 text-[var(--afcfta-muted)]">
                <p>{language === 'fr' ? 'Données autorité non disponibles' : 'Port authority data unavailable'}</p>
              </div>
            )}
            {logisticsNetwork && (
              <div className="bg-[var(--afcfta-card)] p-4 rounded-lg border">
                <h3 className="text-sm font-bold text-[var(--text)] mb-3">&#x1F517; {t.logistics_network}</h3>
                {logisticsNetwork.global_carriers_present?.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-[var(--afcfta-muted)] mb-1">{t.global_carriers}</p>
                    <div className="flex flex-wrap gap-1">
                      {logisticsNetwork.global_carriers_present.map((c, i) => (
                        <Badge key={i} className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] text-xs">{c}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {logisticsNetwork.regional_specialists_present?.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-[var(--afcfta-muted)] mb-1">{t.regional_specialists}</p>
                    <div className="flex flex-wrap gap-1">
                      {logisticsNetwork.regional_specialists_present.map((c, i) => (
                        <Badge key={i} className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] text-xs">{c}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {logisticsNetwork.service_providers_available?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-[var(--afcfta-muted)] mb-1">{t.service_providers}</p>
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
            <div className="p-3 bg-[var(--afcfta-card2)] rounded-lg">
              <p className="text-sm">
                <span className="font-semibold">&#x1F4CD; {t.coordinates}:</span>{' '}
                {port.geo_lat ?? port.latitude}, {port.geo_lon ?? port.longitude}
              </p>
            </div>
            {port.timezone && (
              <div className="p-3 bg-[var(--afcfta-card2)] rounded-lg">
                <p className="text-sm"><span className="font-semibold">&#x1F550; {t.timezone}:</span> {port.timezone}</p>
              </div>
            )}
            {port.un_locode && (
              <div className="p-3 bg-[var(--afcfta-card2)] rounded-lg">
                <p className="text-sm"><span className="font-semibold">&#x1F516; UN LOCODE:</span> {port.un_locode}</p>
              </div>
            )}
            <div className="p-3 bg-[var(--afcfta-card2)] rounded-lg">
              <p className="text-sm">
                <span className="font-semibold">&#x1F4C5; {t.lastUpdate}:</span>{' '}
                {perfMetrics.last_updated || '2024'}
              </p>
            </div>
            {latestStats.source && (
              <div className="p-3 bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] rounded-lg">
                <p className="text-xs text-[var(--info)]">
                  <span className="font-semibold">{t.source}:</span> {latestStats.source}
                </p>
              </div>
            )}
            <div className="p-3 bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] rounded-lg">
              <p className="text-xs text-[var(--info)]">
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
