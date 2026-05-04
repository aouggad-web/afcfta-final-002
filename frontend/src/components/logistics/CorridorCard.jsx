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
  if (type === 'road') return 'bg-blue-100 text-blue-800 border-blue-300';
  if (type === 'rail') return 'bg-red-100 text-red-800 border-red-300';
  if (type === 'multimodal') return 'bg-purple-100 text-purple-800 border-purple-300';
  return 'bg-gray-100 text-gray-800 border-gray-300';
};

const getStatusColor = (status) => {
  if (status === 'Opérationnel') return 'bg-green-100 text-green-800';
  if (status === 'En construction' || status === 'En réhabilitation') return 'bg-yellow-100 text-yellow-800';
  if (status === 'Projet') return 'bg-gray-100 text-gray-800';
  if (status === 'Partiellement opérationnel') return 'bg-orange-100 text-orange-800';
  return 'bg-gray-100 text-gray-800';
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
            <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
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
              <Badge className="bg-amber-100 text-amber-800">⭐ {t.priority}</Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {/* Status and Length */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-gray-50 p-2 rounded">
            <p className="text-xs font-semibold text-gray-700">📏 {t.length}</p>
            <p className="text-lg font-bold text-gray-900">{formatNumber(corridor.length_km)} km</p>
          </div>
          <div className="bg-gray-50 p-2 rounded">
            <p className="text-xs font-semibold text-gray-700">🚦 {t.status}</p>
            <Badge className={getStatusColor(corridor.status)} variant="outline">
              {corridor.status}
            </Badge>
          </div>
        </div>

        {/* Stats if available */}
        {stats.freight_throughput_tons && (
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-blue-50 p-2 rounded border-l-4 border-blue-500">
              <p className="text-xs font-semibold text-blue-700">📦 {t.annualFreight}</p>
              <p className="text-base font-bold text-blue-900">
                {formatNumber(stats.freight_throughput_tons)}
              </p>
              <p className="text-xs text-gray-600">{t.tonsYear}</p>
            </div>
            <div className="bg-green-50 p-2 rounded border-l-4 border-green-500">
              <p className="text-xs font-semibold text-green-700">⏱️ {t.transitTime}</p>
              <p className="text-base font-bold text-green-900">
                {stats.avg_transit_time_hours || 'N/A'}
              </p>
              <p className="text-xs text-gray-600">{t.hours}</p>
            </div>
          </div>
        )}

        {/* Nodes and Operators */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="bg-gray-50 p-2 rounded text-center">
            <p className="text-xs font-semibold text-gray-700">🚧 {t.nodes}</p>
            <p className="text-lg font-bold text-gray-900">{nodes.length}</p>
          </div>
          <div className="bg-green-50 p-2 rounded text-center">
            <p className="text-xs font-semibold text-green-700">✅ OSBP</p>
            <p className="text-lg font-bold text-green-900">{osbpCount}</p>
          </div>
          <div className="bg-orange-50 p-2 rounded text-center">
            <p className="text-xs font-semibold text-orange-700">🚛 {t.operators}</p>
            <p className="text-lg font-bold text-orange-900">{operators.length}</p>
          </div>
        </div>

        {/* Infrastructure details preview */}
        {corridor.infra_details && (
          <div className="bg-slate-50 p-2 rounded mb-4">
            <p className="text-xs text-gray-700">
              <span className="font-semibold">🔧 {t.infrastructure}: </span>
              {corridor.infra_details.substring(0, 80)}{corridor.infra_details.length > 80 ? '...' : ''}
            </p>
          </div>
        )}

        <Button 
          onClick={() => onOpenDetails(corridor)} 
          className="w-full bg-slate-700 hover:bg-slate-800 text-white"
        >
          🔍 {t.viewDetails}
        </Button>
      </CardContent>
    </Card>
  );
}
