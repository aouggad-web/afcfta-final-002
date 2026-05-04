import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';

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
      viewDetails: "Voir les détails complets"
    },
    en: {
      containersTeu: "Containers (TEU)",
      totalTonnage: "Total Tonnage",
      tonsYear: "tons/year",
      calls: "Calls",
      shipsYear: "vessels/year",
      maritimeAgents: "Maritime Agents",
      regularLines: "Regular Lines",
      viewDetails: "View full details"
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

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50 border-b">
        <CardTitle className="text-xl font-bold text-blue-900 flex items-center gap-2">
          <span>🚢</span>
          <span>{port.port_name}</span>
          {port.un_locode && (
            <span className="text-sm font-normal text-gray-600">({port.un_locode})</span>
          )}
        </CardTitle>
        <CardDescription className="text-sm">
          <span className="font-semibold">{port.country_name}</span> • 
          <span className="ml-2 text-blue-600">{port.port_type}</span>
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Conteneurs TEU */}
          <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">
            <p className="text-xs font-semibold text-blue-700 mb-1">📦 {t.containersTeu}</p>
            <p className="text-xl font-bold text-blue-600">
              {formatNumber(stats?.container_throughput_teu)}
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {stats?.year || 2024}
            </p>
          </div>

          {/* Tonnage Total */}
          <div className="bg-green-50 p-3 rounded-lg border-l-4 border-green-500">
            <p className="text-xs font-semibold text-green-700 mb-1">⚖️ {t.totalTonnage}</p>
            <p className="text-xl font-bold text-green-600">
              {formatNumber(stats?.cargo_throughput_tons)}
            </p>
            <p className="text-xs text-gray-600 mt-1">{t.tonsYear}</p>
          </div>

          {/* Escales Navires */}
          <div className="bg-purple-50 p-3 rounded-lg border-l-4 border-purple-500">
            <p className="text-xs font-semibold text-purple-700 mb-1">⚓ {t.calls}</p>
            <p className="text-xl font-bold text-purple-600">
              {formatNumber(stats?.vessel_calls)}
            </p>
            <p className="text-xs text-gray-600 mt-1">{t.shipsYear}</p>
          </div>
        </div>

        {/* Agents et Services - Aperçu rapide */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-gray-50 p-2 rounded">
            <p className="text-xs font-semibold text-gray-700">👥 {t.maritimeAgents}</p>
            <p className="text-sm font-bold text-gray-900">
              {port.agents?.length || 0}
            </p>
          </div>
          <div className="bg-gray-50 p-2 rounded">
            <p className="text-xs font-semibold text-gray-700">🚢 {t.regularLines}</p>
            <p className="text-sm font-bold text-gray-900">
              {port.services?.length || 0}
            </p>
          </div>
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
