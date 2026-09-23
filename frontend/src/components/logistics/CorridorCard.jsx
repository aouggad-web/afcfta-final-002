import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

const formatNumber = (num) => {
  if (num === null || num === undefined) return 'N/A';
  return new Intl.NumberFormat('fr-FR').format(num);
};

const getTypeIcon = (type) => {
  if (type === 'road') return '🛣️';
  if (type === 'rail') return '🚂';
  if (type === 'multimodal') return '🚛🚂';
  return '🛤️';
};

const getTypeColor = (type) => {
  if (type === 'road') return 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)]';
  if (type === 'rail') return 'bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] text-[var(--danger)] border-[color-mix(in_srgb,var(--danger)_30%,transparent)]';
  if (type === 'multimodal') return 'bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] text-[var(--violet)] border-[color-mix(in_srgb,var(--violet)_30%,transparent)]';
  return 'bg-[var(--afcfta-card2)] text-[var(--text)] border-[var(--afcfta-border)]';
};

const getStatusColor = (status) => {
  if (status === 'Opérationnel') return 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]';
  if (status === 'En construction' || status === 'En réhabilitation') return 'bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]';
  if (status === 'Projet') return 'bg-[var(--afcfta-card2)] text-[var(--text)]';
  if (status === 'Partiellement opérationnel') return 'bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)]';
  return 'bg-[var(--afcfta-card2)] text-[var(--text)]';
};

export default function CorridorCard({ corridor, onOpenDetails, language = 'fr' }) {
  const texts = {
    fr: {
      length: "Longueur",
      status: "Statut",
      annualFreight: "Fret Annuel",
      transitTime: "Temps Transit",
      nodes: "Nœuds",
      operators: "Opérateurs",
      infrastructure: "Infrastructure",
      viewDetails: "Voir les détails complets",
      priority: "Prioritaire",
      tonsYear: "tonnes/an",
      hours: "heures"
    },
    en: {
      length: "Length",
      status: "Status",
      annualFreight: "Annual Freight",
      transitTime: "Transit Time",
      nodes: "Nodes",
      operators: "Operators",
      infrastructure: "Infrastructure",
      viewDetails: "View full details",
      priority: "Priority",
      tonsYear: "tons/year",
      hours: "hours"
    }
  };

  const t = texts[language];

  const stats = corridor?.stats || {};
  const nodes = corridor?.nodes || [];
  const operators = corridor?.operators || [];
  const osbpCount = nodes.filter(n => n.is_osbp).length;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="bg-gradient-to-r from-slate-50 to-gray-50 border-b">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-bold text-[var(--text)] flex items-center gap-2">
              <span>{getTypeIcon(corridor.corridor_type)}</span>
              <span>{corridor.corridor_name}</span>
            </CardTitle>
            <CardDescription className="text-sm mt-1">
              {corridor.countries_spanned?.join(' → ')}
            </CardDescription>
          </div>
          <div className="flex flex-col gap-1 items-end">
            <Badge className={getTypeColor(corridor.corridor_type)}>
              {corridor.corridor_type}
            </Badge>
            {corridor.importance === 'high' && (
              <Badge className="bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] text-[var(--gold)]">⭐ {t.priority}</Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {/* Status and Length */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-[var(--afcfta-card2)] p-2 rounded">
            <p className="text-xs font-semibold text-[var(--text)]">📏 {t.length}</p>
            <p className="text-lg font-bold text-[var(--text)]">{formatNumber(corridor.length_km)} km</p>
          </div>
          <div className="bg-[var(--afcfta-card2)] p-2 rounded">
            <p className="text-xs font-semibold text-[var(--text)]">🚦 {t.status}</p>
            <Badge className={getStatusColor(corridor.status)} variant="outline">
              {corridor.status}
            </Badge>
          </div>
        </div>

        {/* Stats if available */}
        {stats.freight_throughput_tons && (
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-2 rounded border-l-4 border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
              <p className="text-xs font-semibold text-[var(--info)]">📦 {t.annualFreight}</p>
              <p className="text-base font-bold text-[var(--info)]">
                {formatNumber(stats.freight_throughput_tons)}
              </p>
              <p className="text-xs text-[var(--afcfta-muted)]">{t.tonsYear}</p>
            </div>
            <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] p-2 rounded border-l-4 border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
              <p className="text-xs font-semibold text-[var(--success)]">⏱️ {t.transitTime}</p>
              <p className="text-base font-bold text-[var(--success)]">
                {stats.avg_transit_time_hours || 'N/A'}
              </p>
              <p className="text-xs text-[var(--afcfta-muted)]">{t.hours}</p>
            </div>
          </div>
        )}

        {/* Nodes and Operators */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="bg-[var(--afcfta-card2)] p-2 rounded text-center">
            <p className="text-xs font-semibold text-[var(--text)]">🚧 {t.nodes}</p>
            <p className="text-lg font-bold text-[var(--text)]">{nodes.length}</p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] p-2 rounded text-center">
            <p className="text-xs font-semibold text-[var(--success)]">✅ OSBP</p>
            <p className="text-lg font-bold text-[var(--success)]">{osbpCount}</p>
          </div>
          <div className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] p-2 rounded text-center">
            <p className="text-xs font-semibold text-[var(--terra)]">🚛 {t.operators}</p>
            <p className="text-lg font-bold text-[var(--terra)]">{operators.length}</p>
          </div>
        </div>

        {/* Infrastructure details preview */}
        {corridor.infra_details && (
          <div className="bg-[var(--afcfta-card2)] p-2 rounded mb-4">
            <p className="text-xs text-[var(--text)]">
              <span className="font-semibold">🔧 {t.infrastructure}: </span>
              {corridor.infra_details.substring(0, 80)}{corridor.infra_details.length > 80 ? '...' : ''}
            </p>
          </div>
        )}

        <Button 
          onClick={() => onOpenDetails(corridor)} 
          className="w-full bg-[var(--afcfta-card2)] hover:bg-[var(--afcfta-card2)] text-[var(--text)]"
        >
          🔍 {t.viewDetails}
        </Button>
      </CardContent>
    </Card>
  );
}
