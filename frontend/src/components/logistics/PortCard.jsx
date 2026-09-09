import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

export default function PortCard({ port, onOpenDetails, language = 'fr' }) {
  const texts = {
    fr: {
      containersTeu: "Conteneurs (TEU)",
      totalTonnage: "Tonnage Total",
      tonsYear: "tonnes/an",
      calls: "Escales",
      shipsYear: "navires/an",
      maritimeAgents: "Agents Maritimes",
      regularLines: "Lignes Régulières",
      viewDetails: "Voir les détails complets",
      dwellTime: "Séjour conteneurs",
      days: "j",
      waitTime: "Attente navires",
      hours: "h",
      lpiScore: "LPI",
    },
    en: {
      containersTeu: "Containers (TEU)",
      totalTonnage: "Total Tonnage",
      tonsYear: "tons/year",
      calls: "Calls",
      shipsYear: "vessels/year",
      maritimeAgents: "Maritime Agents",
      regularLines: "Regular Lines",
      viewDetails: "View full details",
      dwellTime: "Container dwell",
      days: "d",
      waitTime: "Vessel waiting",
      hours: "h",
      lpiScore: "LPI",
    }
  };

  const t = texts[language];

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return language === 'en'
      ? new Intl.NumberFormat('en-US').format(num)
      : new Intl.NumberFormat('fr-FR').format(num);
  };

  const stats = port?.latest_stats;
  const trs = port?.trs_analysis;
  const lpi = port?.lpi_2023;
  const perfMetrics = port?.performance_metrics || {};
  const lsci = port?.lsci;

  const gradeColor = (grade) => {
    if (!grade) return 'bg-gray-100 text-gray-700';
    if (grade.startsWith('A')) return 'bg-green-100 text-green-800';
    if (grade.startsWith('B')) return 'bg-yellow-100 text-yellow-800';
    if (grade.startsWith('C')) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50 border-b pb-3">
        <CardTitle className="text-xl font-bold text-blue-900 flex items-center gap-2">
          <span>🚢</span>
          <span className="flex-1">{port.port_name}</span>
          {port.un_locode && (
            <span className="text-sm font-normal text-gray-600">({port.un_locode})</span>
          )}
        </CardTitle>
        <CardDescription className="text-sm flex items-center gap-2 flex-wrap">
          <span className="font-semibold">{port.country_name}</span>
          <span className="text-gray-400">•</span>
          <span className="text-blue-600">{port.port_type}</span>
          {perfMetrics.efficiency_grade && (
            <Badge className={`text-xs ${gradeColor(perfMetrics.efficiency_grade)}`}>
              {perfMetrics.efficiency_grade}
            </Badge>
          )}
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-4">
        {/* Main traffic KPIs */}
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="bg-blue-50 p-2 rounded-lg border-l-4 border-blue-500">
            <p className="text-xs font-semibold text-blue-700 mb-0.5">📦 TEU</p>
            <p className="text-base font-bold text-blue-600 truncate">
              {formatNumber(stats?.container_throughput_teu)}
            </p>
            <p className="text-xs text-gray-500">{stats?.year || 2024}</p>
          </div>
          <div className="bg-green-50 p-2 rounded-lg border-l-4 border-green-500">
            <p className="text-xs font-semibold text-green-700 mb-0.5">⚖️ {t.tonsYear.split('/')[0]}</p>
            <p className="text-base font-bold text-green-600 truncate">
              {formatNumber(stats?.cargo_throughput_tons)}
            </p>
            <p className="text-xs text-gray-500">{t.tonsYear}</p>
          </div>
          <div className="bg-purple-50 p-2 rounded-lg border-l-4 border-purple-500">
            <p className="text-xs font-semibold text-purple-700 mb-0.5">⚓ {t.calls}</p>
            <p className="text-base font-bold text-purple-600">
              {formatNumber(stats?.vessel_calls)}
            </p>
            <p className="text-xs text-gray-500">{t.shipsYear}</p>
          </div>
        </div>

        {/* Performance metrics row */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {trs?.container_dwell_time_days && trs.container_dwell_time_days !== 'NA' && (
            <div className="bg-amber-50 p-2 rounded border-l-2 border-amber-400">
              <p className="text-xs font-semibold text-amber-700">📦 {t.dwellTime}</p>
              <p className="text-sm font-bold text-amber-900">{trs.container_dwell_time_days} {t.days}</p>
            </div>
          )}
          {(perfMetrics.avg_waiting_time_hours) && (
            <div className="bg-indigo-50 p-2 rounded border-l-2 border-indigo-400">
              <p className="text-xs font-semibold text-indigo-700">⏳ {t.waitTime}</p>
              <p className="text-sm font-bold text-indigo-900">{perfMetrics.avg_waiting_time_hours} {t.hours}</p>
            </div>
          )}
        </div>

        {/* Agents, lines, LSCI, LPI row */}
        <div className="grid grid-cols-4 gap-1.5 mb-3">
          <div className="bg-gray-50 p-1.5 rounded text-center">
            <p className="text-xs font-semibold text-gray-600">👥</p>
            <p className="text-sm font-bold text-gray-900">{port.agents?.length || 0}</p>
            <p className="text-xs text-gray-500">{t.maritimeAgents.split(' ')[0]}</p>
          </div>
          <div className="bg-gray-50 p-1.5 rounded text-center">
            <p className="text-xs font-semibold text-gray-600">🚢</p>
            <p className="text-sm font-bold text-gray-900">{port.services?.length || 0}</p>
            <p className="text-xs text-gray-500">{t.regularLines.split(' ')[0]}</p>
          </div>
          {lsci && (
            <div className="bg-indigo-50 p-1.5 rounded text-center">
              <p className="text-xs font-semibold text-indigo-600">LSCI</p>
              <p className="text-sm font-bold text-indigo-900">{lsci.value}</p>
              <p className="text-xs text-gray-500">#{lsci.world_rank}</p>
            </div>
          )}
          {lpi && (
            <div className="bg-blue-50 p-1.5 rounded text-center">
              <p className="text-xs font-semibold text-blue-600">{t.lpiScore}</p>
              <p className="text-sm font-bold text-blue-900">{lpi.overall_score}</p>
              <p className="text-xs text-gray-500">/5.0</p>
            </div>
          )}
        </div>

        <Button 
          onClick={() => onOpenDetails(port)} 
          className="w-full bg-blue-600 hover:bg-blue-700 text-white"
        >
          🔍 {t.viewDetails}
        </Button>
      </CardContent>
    </Card>
  );
}
