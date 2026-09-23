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
    if (!grade) return 'bg-[var(--afcfta-card2)] text-[var(--text)]';
    if (grade.startsWith('A')) return 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]';
    if (grade.startsWith('B')) return 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]';
    if (grade.startsWith('C')) return 'bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)]';
    return 'bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] text-[var(--danger)]';
  };

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] border-b pb-3">
        <CardTitle className="text-xl font-bold text-[var(--info)] flex items-center gap-2">
          <span>🚢</span>
          <span className="flex-1">{port.port_name}</span>
          {port.un_locode && (
            <span className="text-sm font-normal text-[var(--afcfta-muted)]">({port.un_locode})</span>
          )}
        </CardTitle>
        <CardDescription className="text-sm flex items-center gap-2 flex-wrap">
          <span className="font-semibold">{port.country_name}</span>
          <span className="text-[var(--afcfta-muted)]">•</span>
          <span className="text-[var(--info)]">{port.port_type}</span>
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
          <div className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-2 rounded-lg border-l-4 border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
            <p className="text-xs font-semibold text-[var(--info)] mb-0.5">📦 TEU</p>
            <p className="text-base font-bold text-[var(--info)] truncate">
              {formatNumber(stats?.container_throughput_teu)}
            </p>
            <p className="text-xs text-[var(--afcfta-muted)]">{stats?.year || 2024}</p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] p-2 rounded-lg border-l-4 border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
            <p className="text-xs font-semibold text-[var(--success)] mb-0.5">⚖️ {t.tonsYear.split('/')[0]}</p>
            <p className="text-base font-bold text-[var(--success)] truncate">
              {formatNumber(stats?.cargo_throughput_tons)}
            </p>
            <p className="text-xs text-[var(--afcfta-muted)]">{t.tonsYear}</p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] p-2 rounded-lg border-l-4 border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
            <p className="text-xs font-semibold text-[var(--violet)] mb-0.5">⚓ {t.calls}</p>
            <p className="text-base font-bold text-[var(--violet)]">
              {formatNumber(stats?.vessel_calls)}
            </p>
            <p className="text-xs text-[var(--afcfta-muted)]">{t.shipsYear}</p>
          </div>
        </div>

        {/* Performance metrics row */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {trs?.container_dwell_time_days && trs.container_dwell_time_days !== 'NA' && (
            <div className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] p-2 rounded border-l-2 border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
              <p className="text-xs font-semibold text-[var(--gold)]">📦 {t.dwellTime}</p>
              <p className="text-sm font-bold text-[var(--gold)]">{trs.container_dwell_time_days} {t.days}</p>
            </div>
          )}
          {(perfMetrics.avg_waiting_time_hours) && (
            <div className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] p-2 rounded border-l-2 border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
              <p className="text-xs font-semibold text-[var(--violet)]">⏳ {t.waitTime}</p>
              <p className="text-sm font-bold text-[var(--violet)]">{perfMetrics.avg_waiting_time_hours} {t.hours}</p>
            </div>
          )}
        </div>

        {/* Agents, lines, LSCI, LPI row */}
        <div className="grid grid-cols-4 gap-1.5 mb-3">
          <div className="bg-[var(--afcfta-card2)] p-1.5 rounded text-center">
            <p className="text-xs font-semibold text-[var(--afcfta-muted)]">👥</p>
            <p className="text-sm font-bold text-[var(--text)]">{port.agents?.length || 0}</p>
            <p className="text-xs text-[var(--afcfta-muted)]">{t.maritimeAgents.split(' ')[0]}</p>
          </div>
          <div className="bg-[var(--afcfta-card2)] p-1.5 rounded text-center">
            <p className="text-xs font-semibold text-[var(--afcfta-muted)]">🚢</p>
            <p className="text-sm font-bold text-[var(--text)]">{port.services?.length || 0}</p>
            <p className="text-xs text-[var(--afcfta-muted)]">{t.regularLines.split(' ')[0]}</p>
          </div>
          {lsci && (
            <div className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] p-1.5 rounded text-center">
              <p className="text-xs font-semibold text-[var(--violet)]">LSCI</p>
              <p className="text-sm font-bold text-[var(--violet)]">{lsci.value}</p>
              <p className="text-xs text-[var(--afcfta-muted)]">#{lsci.world_rank}</p>
            </div>
          )}
          {lpi && (
            <div className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-1.5 rounded text-center">
              <p className="text-xs font-semibold text-[var(--info)]">{t.lpiScore}</p>
              <p className="text-sm font-bold text-[var(--info)]">{lpi.overall_score}</p>
              <p className="text-xs text-[var(--afcfta-muted)]">/5.0</p>
            </div>
          )}
        </div>

        <Button 
          onClick={() => onOpenDetails(port)} 
          className="w-full bg-[var(--info)] hover:bg-[var(--info)] text-[var(--bg)]"
        >
          🔍 {t.viewDetails}
        </Button>
      </CardContent>
    </Card>
  );
}
