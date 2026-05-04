import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Badge } from '../ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function PortDetailsModal({ isOpen, onClose, port, language = 'fr' }) {
  const texts = {
    fr: {
      teuYear: "TEU/an",
      tonsYear: "Tonnes/an",
      calls: "Escales",
      portTime: "Temps Port",
      waiting: "Attente",
      berthProductivity: "Productivité Quai",
      movesPerHour: "mouvements/heure",
      connectivity: "Connectivité",
      worldRank: "mondial",
      dataYear: "Année Données",
      agents: "Agents",
      services: "Lignes",
      evolution: "Évolution",
      info: "Infos",
      noAgents: "Aucun agent maritime répertorié.",
      noServices: "Aucune ligne régulière répertoriée.",
      noHistorical: "Aucune donnée historique disponible.",
      frequency: "Fréquence",
      rotation: "Rotation",
      teuEvolution: "Évolution Trafic Conteneurs (TEU)",
      portTimeEvolution: "Évolution Temps au Port (heures)",
      annualComparison: "Tableau Comparatif Annuel",
      year: "Année",
      teu: "TEU",
      tons: "Tonnes",
      grade: "Grade",
      coordinates: "Coordonnées GPS",
      timezone: "Fuseau horaire",
      lastUpdate: "Dernière mise à jour",
      source: "Source données",
      hours: "h"
    },
    en: {
      teuYear: "TEU/year",
      tonsYear: "Tons/year",
      calls: "Calls",
      portTime: "Port Time",
      waiting: "Waiting",
      berthProductivity: "Berth Productivity",
      movesPerHour: "moves/hour",
      connectivity: "Connectivity",
      worldRank: "world",
      dataYear: "Data Year",
      agents: "Agents",
      services: "Lines",
      evolution: "Evolution",
      info: "Info",
      noAgents: "No maritime agents listed.",
      noServices: "No regular lines listed.",
      noHistorical: "No historical data available.",
      frequency: "Frequency",
      rotation: "Rotation",
      teuEvolution: "Container Traffic Evolution (TEU)",
      portTimeEvolution: "Port Time Evolution (hours)",
      annualComparison: "Annual Comparison Table",
      year: "Year",
      teu: "TEU",
      tons: "Tons",
      grade: "Grade",
      coordinates: "GPS Coordinates",
      timezone: "Timezone",
      lastUpdate: "Last update",
      source: "Data source",
      hours: "h"
    }
  };

  const t = texts[language];

  if (!port) return null;

  const agents = port.agents || [];
  const services = port.services || [];
  const historicalStats = port.historical_stats || [];
  const lsci = port.lsci || null;
  const latestStats = port.latest_stats || {};

  const formatNumber = (num) => {
    if (!num) return 'N/A';
    return language === 'en' 
      ? num.toLocaleString('en-US')
      : num.toLocaleString('fr-FR');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-blue-900 flex items-center gap-2">
            <span>🚢</span>
            <span>{port.port_name}</span>
          </DialogTitle>
          <DialogDescription>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <Badge variant="outline">{port.country_name}</Badge>
              <Badge variant="secondary">{port.port_type}</Badge>
              {port.un_locode && <Badge>{port.un_locode}</Badge>}
              {latestStats.performance_grade && (
                <Badge className={`
                  ${latestStats.performance_grade.startsWith('A') ? 'bg-green-600' : ''}
                  ${latestStats.performance_grade.startsWith('B') ? 'bg-yellow-600' : ''}
                  ${latestStats.performance_grade.startsWith('C') ? 'bg-orange-600' : ''}
                  ${latestStats.performance_grade.startsWith('D') ? 'bg-red-600' : ''}
                  text-white
                `}>
                  Performance: {latestStats.performance_grade}
                </Badge>
              )}
            </div>
          </DialogDescription>
        </DialogHeader>

        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 my-4">
          <div className="bg-blue-50 p-3 rounded-lg text-center">
            <p className="text-xs text-blue-700 font-semibold">📦 {t.teuYear}</p>
            <p className="text-lg font-bold text-blue-600">
              {formatNumber(latestStats.container_throughput_teu)}
            </p>
          </div>
          <div className="bg-green-50 p-3 rounded-lg text-center">
            <p className="text-xs text-green-700 font-semibold">⚖️ {t.tonsYear}</p>
            <p className="text-lg font-bold text-green-600">
              {formatNumber(latestStats.cargo_throughput_tons)}
            </p>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg text-center">
            <p className="text-xs text-purple-700 font-semibold">⚓ {t.calls}</p>
            <p className="text-lg font-bold text-purple-600">
              {formatNumber(latestStats.vessel_calls)}
            </p>
          </div>
          <div className="bg-orange-50 p-3 rounded-lg text-center">
            <p className="text-xs text-orange-700 font-semibold">⏱️ {t.portTime}</p>
            <p className="text-lg font-bold text-orange-600">
              {latestStats.median_time_in_port_hours ? `${latestStats.median_time_in_port_hours}${t.hours}` : 'N/A'}
            </p>
          </div>
          <div className="bg-pink-50 p-3 rounded-lg text-center">
            <p className="text-xs text-pink-700 font-semibold">⏳ {t.waiting}</p>
            <p className="text-lg font-bold text-pink-600">
              {latestStats.average_waiting_time_hours ? `${latestStats.average_waiting_time_hours}${t.hours}` : 'N/A'}
            </p>
          </div>
        </div>

        {/* Advanced Indicators */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          {latestStats.berth_productivity_moves_per_hour && (
            <div className="bg-gradient-to-r from-cyan-50 to-blue-50 p-3 rounded-lg border-l-4 border-cyan-500">
              <p className="text-xs font-semibold text-cyan-700">🏗️ {t.berthProductivity}</p>
              <p className="text-lg font-bold text-cyan-900">
                {latestStats.berth_productivity_moves_per_hour} {t.movesPerHour}
              </p>
            </div>
          )}
          
          {lsci && (
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-3 rounded-lg border-l-4 border-indigo-500">
              <p className="text-xs font-semibold text-indigo-700">🌍 LSCI ({t.connectivity})</p>
              <p className="text-lg font-bold text-indigo-900">
                {lsci.value} / 100
                <span className="text-sm text-gray-600 ml-2">(#{lsci.world_rank} {t.worldRank})</span>
              </p>
            </div>
          )}
          
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-3 rounded-lg border-l-4 border-green-500">
            <p className="text-xs font-semibold text-green-700">📊 {t.dataYear}</p>
            <p className="text-lg font-bold text-green-900">
              {latestStats.year || 2024}
            </p>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="agents" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="agents">
              👥 {t.agents} ({agents.length})
            </TabsTrigger>
            <TabsTrigger value="services">
              🚢 {t.services} ({services.length})
            </TabsTrigger>
            <TabsTrigger value="stats">
              📈 {t.evolution}
            </TabsTrigger>
            <TabsTrigger value="info">
              ℹ️ {t.info}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="agents" className="mt-4">
            {agents.length > 0 ? (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {agents.map((agent, index) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500 hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-blue-600 font-bold">✓</span>
                        <div>
                          <p className="font-bold text-gray-900">{agent.agent_name}</p>
                          {agent.group && (
                            <Badge variant="outline" className="text-xs mt-1">
                              {agent.group}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-8 text-gray-500">
                <p>{t.noAgents}</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="services" className="mt-4">
            {services.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {services.map((service, index) => (
                  <div
                    key={index}
                    className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg border border-blue-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-bold text-blue-900 flex items-center gap-2">
                          <span>🚢</span>
                          <span>{service.carrier}</span>
                        </p>
                        <p className="text-sm text-gray-800 font-semibold mt-1">
                          {service.service_name}
                        </p>
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
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-8 text-gray-500">
                <p>{t.noServices}</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="stats" className="mt-4">
            {historicalStats.length > 0 ? (
              <div className="space-y-4">
                {/* TEU Chart */}
                <div className="bg-white p-4 rounded-lg border">
                  <h3 className="text-sm font-bold text-gray-700 mb-3">{t.teuEvolution}</h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={historicalStats}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="year" />
                      <YAxis />
                      <Tooltip formatter={(value) => formatNumber(value)} />
                      <Line type="monotone" dataKey="container_throughput_teu" stroke="#3b82f6" strokeWidth={2} name="TEU" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {/* Port Time Chart */}
                {historicalStats[0]?.median_time_in_port_hours && (
                  <div className="bg-white p-4 rounded-lg border">
                    <h3 className="text-sm font-bold text-gray-700 mb-3">{t.portTimeEvolution}</h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={historicalStats}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="year" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="median_time_in_port_hours" stroke="#f59e0b" strokeWidth={2} name={t.hours} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Comparison Table */}
                <div className="bg-white p-4 rounded-lg border">
                  <h3 className="text-sm font-bold text-gray-700 mb-3">{t.annualComparison}</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">{t.year}</th>
                          <th className="text-right p-2">{t.teu}</th>
                          <th className="text-right p-2">{t.tons}</th>
                          <th className="text-right p-2">{t.calls}</th>
                          <th className="text-right p-2">{t.portTime}</th>
                          <th className="text-center p-2">{t.grade}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historicalStats.map((stat, idx) => (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="p-2 font-bold">{stat.year}</td>
                            <td className="text-right p-2">{formatNumber(stat.container_throughput_teu)}</td>
                            <td className="text-right p-2">{formatNumber(stat.cargo_throughput_tons)}</td>
                            <td className="text-right p-2">{formatNumber(stat.vessel_calls)}</td>
                            <td className="text-right p-2">{stat.median_time_in_port_hours}{t.hours}</td>
                            <td className="text-center p-2">
                              <Badge className={`text-xs ${
                                stat.performance_grade?.startsWith('A') ? 'bg-green-600' :
                                stat.performance_grade?.startsWith('B') ? 'bg-yellow-600' :
                                stat.performance_grade?.startsWith('C') ? 'bg-orange-600' : 'bg-red-600'
                              }`}>
                                {stat.performance_grade}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center p-8 text-gray-500">
                <p>{t.noHistorical}</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="info" className="mt-4 space-y-3">
            <div className="p-3 bg-gray-100 rounded-lg">
              <p className="text-sm">
                <span className="font-semibold">📍 {t.coordinates}:</span> {port.latitude}, {port.longitude}
              </p>
            </div>
            {port.timezone && (
              <div className="p-3 bg-gray-100 rounded-lg">
                <p className="text-sm">
                  <span className="font-semibold">🕐 {t.timezone}:</span> {port.timezone}
                </p>
              </div>
            )}
            <div className="p-3 bg-gray-100 rounded-lg">
              <p className="text-sm">
                <span className="font-semibold">📅 {t.lastUpdate}:</span> 2024
              </p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-700">
                <span className="font-semibold">{t.source}:</span> UNCTAD Maritime Transport Review 2023 | World Bank Logistics Performance Index | AfCFTA Secretariat
              </p>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
