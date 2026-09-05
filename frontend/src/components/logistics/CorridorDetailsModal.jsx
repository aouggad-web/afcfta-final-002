import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

const getTypeIcon = (type) => {
  if (type === 'road') return '🛣️';
  if (type === 'rail') return '🚂';
  if (type === 'multimodal') return '🚛🚂';
  return '🛤️';
};

const getNodeTypeIcon = (type) => {
  if (type === 'border_crossing') return '🚧';
  if (type === 'dry_port') return '📦';
  if (type === 'rail_terminal') return '🚂';
  if (type === 'intermodal_hub') return '🔀';
  return '📍';
};

export default function CorridorDetailsModal({ corridor, open, onClose, language = 'fr' }) {
  const texts = {
    fr: {
      pidaPriority: "Prioritaire PIDA",
      description: "Description",
      annualFreight: "Fret Annuel",
      tons: "tonnes",
      transitTime: "Temps Transit",
      hours: "heures",
      borderTime: "Temps Frontière",
      dailyTraffic: "Trafic Quotidien",
      trucksDay: "camions/jour",
      infrastructureRoute: "Infrastructure & Tracé",
      countriesCrossed: "Pays traversés",
      startEndPoints: "Points de départ/arrivée",
      technicalDetails: "Détails techniques",
      source: "Source",
      logisticsNodes: "Nœuds Logistiques",
      transportOperators: "Opérateurs",
      logisticsNodesBorder: "Nœuds Logistiques & Postes-Frontières",
      osbpOperational: "OSBP (One-Stop Border Post) opérationnel(s)",
      noNodes: "Aucun nœud enregistré",
      transportOperatorsTitle: "Opérateurs de Transport",
      noOperators: "Aucun opérateur enregistré",
      locomotives: "locomotives",
      trucks: "camions",
      network: "Réseau Logistique",
      global3pl: "3PL Mondiaux",
      regionalTrucking: "Transport Routier Régional",
      railOperators: "Opérateurs Ferroviaires",
      corridorBodies: "Organismes de Gestion",
      localAgents: "Agents Locaux",
      serviceProviders: "Prestataires",
      noNetwork: "Réseau logistique non disponible",
      city: "Ville",
      phone: "Tél",
      certifications: "Certifications",
      openingHours: "Horaires",
    },
    en: {
      pidaPriority: "PIDA Priority",
      description: "Description",
      annualFreight: "Annual Freight",
      tons: "tons",
      transitTime: "Transit Time",
      hours: "hours",
      borderTime: "Border Time",
      dailyTraffic: "Daily Traffic",
      trucksDay: "trucks/day",
      infrastructureRoute: "Infrastructure & Route",
      countriesCrossed: "Countries crossed",
      startEndPoints: "Start/End points",
      technicalDetails: "Technical details",
      source: "Source",
      logisticsNodes: "Logistics Nodes",
      transportOperators: "Operators",
      logisticsNodesBorder: "Logistics Nodes & Border Posts",
      osbpOperational: "OSBP (One-Stop Border Post) operational",
      noNodes: "No nodes registered",
      transportOperatorsTitle: "Transport Operators",
      noOperators: "No operators registered",
      locomotives: "locomotives",
      trucks: "trucks",
      network: "Logistics Network",
      global3pl: "Global 3PL",
      regionalTrucking: "Regional Trucking",
      railOperators: "Rail Operators",
      corridorBodies: "Management Bodies",
      localAgents: "Local Agents",
      serviceProviders: "Service Providers",
      noNetwork: "Logistics network data not available",
      city: "City",
      phone: "Phone",
      certifications: "Certifications",
      openingHours: "Opening Hours",
    }
  };

  const t = texts[language];

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return language === 'en' 
      ? new Intl.NumberFormat('en-US').format(num)
      : new Intl.NumberFormat('fr-FR').format(num);
  };

  if (!corridor) return null;

  const stats = corridor.stats || {};
  const nodes = corridor.nodes || [];
  const operators = corridor.operators || [];
  const osbpNodes = nodes.filter(n => n.is_osbp);
  const logisticsNetwork = corridor.logistics_network || null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <span>{getTypeIcon(corridor.corridor_type)}</span>
            {corridor.corridor_name}
          </DialogTitle>
          <DialogDescription className="flex gap-2 mt-2 flex-wrap">
            <Badge className="bg-slate-700">{corridor.corridor_type}</Badge>
            <Badge variant="outline">{corridor.status}</Badge>
            {corridor.importance === 'high' && <Badge className="bg-amber-500">⭐ {t.pidaPriority}</Badge>}
            <Badge variant="outline">{corridor.length_km} km</Badge>
          </DialogDescription>
        </DialogHeader>

        {/* Description */}
        {corridor.description && (
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-4">
            <p className="text-sm text-gray-800">
              <span className="font-semibold">📋 {t.description}: </span>
              {corridor.description}
            </p>
          </div>
        )}

        {/* KPI Cards Section */}
        {stats.freight_throughput_tons && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-4">
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardContent className="pt-4">
                <p className="text-xs font-semibold text-blue-700 mb-1">📦 {t.annualFreight}</p>
                <p className="text-2xl font-bold text-blue-900">{formatNumber(stats.freight_throughput_tons)}</p>
                <p className="text-xs text-gray-600">{t.tons} ({stats.year || 2024})</p>
              </CardContent>
            </Card>

            {stats.avg_transit_time_hours && (
              <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                <CardContent className="pt-4">
                  <p className="text-xs font-semibold text-green-700 mb-1">⏱️ {t.transitTime}</p>
                  <p className="text-2xl font-bold text-green-900">{stats.avg_transit_time_hours}</p>
                  <p className="text-xs text-gray-600">{t.hours}</p>
                </CardContent>
              </Card>
            )}

            {stats.avg_border_crossing_time_hours && (
              <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
                <CardContent className="pt-4">
                  <p className="text-xs font-semibold text-orange-700 mb-1">🚧 {t.borderTime}</p>
                  <p className="text-2xl font-bold text-orange-900">{stats.avg_border_crossing_time_hours}</p>
                  <p className="text-xs text-gray-600">{t.hours}</p>
                </CardContent>
              </Card>
            )}

            {stats.truck_volumes_daily && (
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                <CardContent className="pt-4">
                  <p className="text-xs font-semibold text-purple-700 mb-1">🚛 {t.dailyTraffic}</p>
                  <p className="text-2xl font-bold text-purple-900">{formatNumber(stats.truck_volumes_daily)}</p>
                  <p className="text-xs text-gray-600">{t.trucksDay}</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Infrastructure Section */}
        <Card className="mb-4">
          <CardHeader className="bg-gray-50">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>🔧</span>
              {t.infrastructureRoute}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-gray-700">{t.countriesCrossed}:</p>
                <p className="text-base">{corridor.countries_spanned?.join(' → ')}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-700">{t.startEndPoints}:</p>
                <p className="text-base">{corridor.start_node} → {corridor.end_node}</p>
              </div>
              <div className="bg-slate-50 p-3 rounded">
                <p className="text-sm font-semibold text-gray-700 mb-1">{t.technicalDetails}:</p>
                <p className="text-sm text-gray-800">{corridor.infra_details}</p>
              </div>
              {stats.source_org && (
                <div className="text-xs text-gray-600">
                  <span className="font-semibold">{t.source}: </span>
                  {stats.source_org}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Tabs for Nodes, Operators, Network */}
        <Tabs defaultValue="nodes" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="nodes">🚧 {t.logisticsNodes} ({nodes.length})</TabsTrigger>
            <TabsTrigger value="operators">🚛 {t.transportOperators} ({operators.length})</TabsTrigger>
            <TabsTrigger value="network">🔗 {t.network}</TabsTrigger>
          </TabsList>

          {/* Nodes Tab */}
          <TabsContent value="nodes" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{t.logisticsNodesBorder}</CardTitle>
                {osbpNodes.length > 0 && (
                  <p className="text-sm text-green-600 font-semibold">✓ {osbpNodes.length} {t.osbpOperational}</p>
                )}
              </CardHeader>
              <CardContent>
                {nodes.length > 0 ? (
                  <div className="space-y-3">
                    {nodes.map((node, idx) => (
                      <div 
                        key={idx} 
                        className={`p-3 rounded-lg border-l-4 ${
                          node.is_osbp 
                            ? 'bg-green-50 border-green-500' 
                            : node.node_type === 'border_crossing'
                            ? 'bg-orange-50 border-orange-500'
                            : 'bg-blue-50 border-blue-500'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-bold text-base flex items-center gap-2">
                              <span>{getNodeTypeIcon(node.node_type)}</span>
                              {node.node_name}
                              {node.is_osbp && <Badge className="bg-green-600 text-white text-xs">OSBP</Badge>}
                            </p>
                            <p className="text-sm text-gray-600">{node.country_iso} • {node.node_type}</p>
                            {node.notes && (
                              <p className="text-xs text-gray-700 mt-1">{node.notes}</p>
                            )}
                          </div>
                          <div className="text-xs text-gray-500">
                            {node.geo_lat?.toFixed(3)}, {node.geo_lon?.toFixed(3)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">{t.noNodes}</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Operators Tab */}
          <TabsContent value="operators" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{t.transportOperatorsTitle}</CardTitle>
              </CardHeader>
              <CardContent>
                {operators.length > 0 ? (
                  <div className="space-y-3">
                    {operators.map((operator, idx) => (
                      <div 
                        key={idx} 
                        className={`p-3 rounded-lg ${
                          operator.operator_type === 'rail_operator'
                            ? 'bg-red-50 border border-red-200'
                            : 'bg-blue-50 border border-blue-200'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-bold text-base">
                              {operator.operator_type === 'rail_operator' ? '🚂' : '🚛'} {operator.operator_name}
                            </p>
                            <p className="text-sm text-gray-600">{operator.group}</p>
                            <p className="text-xs text-gray-500 mt-1">{operator.country_iso}</p>
                          </div>
                          {operator.fleet_size > 0 && (
                            <div className="text-right">
                              <p className="text-2xl font-bold text-gray-900">{operator.fleet_size}</p>
                              <p className="text-xs text-gray-600">
                                {operator.operator_type === 'rail_operator' ? t.locomotives : t.trucks}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">{t.noOperators}</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Logistics Network Tab */}
          <TabsContent value="network" className="mt-4">
            {logisticsNetwork ? (
              <div className="space-y-4">
                {logisticsNetwork.global_3pl_present?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-blue-700">🌐 {t.global3pl}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2">
                        {logisticsNetwork.global_3pl_present.map((c, i) => (
                          <Badge key={i} className="bg-blue-100 text-blue-800">{c}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.regional_trucking_operators?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-orange-700">🚛 {t.regionalTrucking}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2">
                        {logisticsNetwork.regional_trucking_operators.map((c, i) => (
                          <Badge key={i} className="bg-orange-100 text-orange-800">{c}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.rail_operators_present?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-red-700">🚂 {t.railOperators}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2">
                        {logisticsNetwork.rail_operators_present.map((c, i) => (
                          <Badge key={i} className="bg-red-100 text-red-800">{c}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.corridor_management_bodies?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-purple-700">🏛️ {t.corridorBodies}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-1">
                        {logisticsNetwork.corridor_management_bodies.map((c, i) => (
                          <p key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <span className="text-purple-400">▸</span>{c}
                          </p>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.local_agents_by_country && Object.keys(logisticsNetwork.local_agents_by_country).length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-green-700">👥 {t.localAgents}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-4 max-h-80 overflow-y-auto">
                        {Object.entries(logisticsNetwork.local_agents_by_country).map(([country, agents]) => (
                          <div key={country}>
                            <p className="text-xs font-bold text-gray-500 uppercase mb-2 border-b pb-1">{country}</p>
                            <div className="space-y-2">
                              {agents.map((agent, i) => (
                                <div key={i} className="p-2 bg-green-50 rounded border-l-2 border-green-400">
                                  <p className="font-semibold text-sm text-green-900">{agent.company_name}</p>
                                  {agent.city && <p className="text-xs text-gray-500">📍 {agent.city}{agent.address ? ` – ${agent.address}` : ''}</p>}
                                  <div className="flex flex-wrap gap-2 mt-1">
                                    {agent.phone && (
                                      <a href={`tel:${agent.phone}`} className="text-xs text-blue-600 hover:underline">📞 {agent.phone}</a>
                                    )}
                                    {agent.email && (
                                      <a href={`mailto:${agent.email}`} className="text-xs text-blue-600 hover:underline">✉️ {agent.email}</a>
                                    )}
                                    {agent.website && (
                                      <a href={agent.website} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline">🌐 {agent.website.replace(/^https?:\/\//, '')}</a>
                                    )}
                                  </div>
                                  {agent.operating_hours && <p className="text-xs text-gray-500 mt-1">🕐 {agent.operating_hours}</p>}
                                  {agent.services?.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {agent.services.map((s, si) => (
                                        <Badge key={si} variant="secondary" className="text-xs bg-green-100 text-green-800">{s}</Badge>
                                      ))}
                                    </div>
                                  )}
                                  {agent.certifications?.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {agent.certifications.map((c, ci) => (
                                        <Badge key={ci} className="text-xs bg-blue-100 text-blue-700">{c}</Badge>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.service_providers_available?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-gray-700">⚙️ {t.serviceProviders}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2">
                        {logisticsNetwork.service_providers_available.map((s, i) => (
                          <Badge key={i} variant="outline">{s}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <div className="text-center p-8 text-gray-400">
                <p>{t.noNetwork}</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Source information */}
        <div className="mt-4 text-xs text-gray-600 bg-gray-50 p-3 rounded">
          <span className="font-semibold">{t.source}: </span>
          {corridor.source_org}
        </div>
      </DialogContent>
    </Dialog>
  );
}
