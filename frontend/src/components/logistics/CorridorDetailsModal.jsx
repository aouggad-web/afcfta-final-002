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
          <DialogTitle className="text-2xl font-bold text-[var(--text)] flex items-center gap-2">
            <span>{getTypeIcon(corridor.corridor_type)}</span>
            {corridor.corridor_name}
          </DialogTitle>
          <DialogDescription className="flex gap-2 mt-2 flex-wrap">
            <Badge className="bg-[var(--afcfta-card2)]">{corridor.corridor_type}</Badge>
            <Badge variant="outline">{corridor.status}</Badge>
            {corridor.importance === 'high' && <Badge className="bg-amber-500">⭐ {t.pidaPriority}</Badge>}
            <Badge variant="outline">{corridor.length_km} km</Badge>
          </DialogDescription>
        </DialogHeader>

        {/* Description */}
        {corridor.description && (
          <div className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-4 rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] mb-4">
            <p className="text-sm text-[var(--text)]">
              <span className="font-semibold">📋 {t.description}: </span>
              {corridor.description}
            </p>
          </div>
        )}

        {/* KPI Cards Section */}
        {stats.freight_throughput_tons && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-4">
            <Card className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
              <CardContent className="pt-4">
                <p className="text-xs font-semibold text-[var(--info)] mb-1">📦 {t.annualFreight}</p>
                <p className="text-2xl font-bold text-[var(--info)]">{formatNumber(stats.freight_throughput_tons)}</p>
                <p className="text-xs text-[var(--afcfta-muted)]">{t.tons} ({stats.year || 2024})</p>
              </CardContent>
            </Card>

            {stats.avg_transit_time_hours && (
              <Card className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                <CardContent className="pt-4">
                  <p className="text-xs font-semibold text-[var(--success)] mb-1">⏱️ {t.transitTime}</p>
                  <p className="text-2xl font-bold text-[var(--success)]">{stats.avg_transit_time_hours}</p>
                  <p className="text-xs text-[var(--afcfta-muted)]">{t.hours}</p>
                </CardContent>
              </Card>
            )}

            {stats.avg_border_crossing_time_hours && (
              <Card className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--terra)_30%,transparent)]">
                <CardContent className="pt-4">
                  <p className="text-xs font-semibold text-[var(--terra)] mb-1">🚧 {t.borderTime}</p>
                  <p className="text-2xl font-bold text-[var(--terra)]">{stats.avg_border_crossing_time_hours}</p>
                  <p className="text-xs text-[var(--afcfta-muted)]">{t.hours}</p>
                </CardContent>
              </Card>
            )}

            {stats.truck_volumes_daily && (
              <Card className="bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
                <CardContent className="pt-4">
                  <p className="text-xs font-semibold text-[var(--violet)] mb-1">🚛 {t.dailyTraffic}</p>
                  <p className="text-2xl font-bold text-[var(--violet)]">{formatNumber(stats.truck_volumes_daily)}</p>
                  <p className="text-xs text-[var(--afcfta-muted)]">{t.trucksDay}</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Infrastructure Section */}
        <Card className="mb-4">
          <CardHeader className="bg-[var(--afcfta-card2)]">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>🔧</span>
              {t.infrastructureRoute}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-[var(--text)]">{t.countriesCrossed}:</p>
                <p className="text-base">{corridor.countries_spanned?.join(' → ')}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--text)]">{t.startEndPoints}:</p>
                <p className="text-base">{corridor.start_node} → {corridor.end_node}</p>
              </div>
              <div className="bg-[var(--afcfta-card2)] p-3 rounded">
                <p className="text-sm font-semibold text-[var(--text)] mb-1">{t.technicalDetails}:</p>
                <p className="text-sm text-[var(--text)]">{corridor.infra_details}</p>
              </div>
              {stats.source_org && (
                <div className="text-xs text-[var(--afcfta-muted)]">
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
                  <p className="text-sm text-[var(--success)] font-semibold">✓ {osbpNodes.length} {t.osbpOperational}</p>
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
                            ? 'bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)]' 
                            : node.node_type === 'border_crossing'
                            ? 'bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--terra)_30%,transparent)]'
                            : 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--info)_30%,transparent)]'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-bold text-base flex items-center gap-2">
                              <span>{getNodeTypeIcon(node.node_type)}</span>
                              {node.node_name}
                              {node.is_osbp && <Badge className="bg-[var(--success)] text-[var(--bg)] text-xs">OSBP</Badge>}
                            </p>
                            <p className="text-sm text-[var(--afcfta-muted)]">{node.country_iso} • {node.node_type}</p>
                            {node.notes && (
                              <p className="text-xs text-[var(--text)] mt-1">{node.notes}</p>
                            )}
                          </div>
                          <div className="text-xs text-[var(--afcfta-muted)]">
                            {node.geo_lat?.toFixed(3)}, {node.geo_lon?.toFixed(3)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[var(--afcfta-muted)] text-center py-8">{t.noNodes}</p>
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
                            ? 'bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--danger)_30%,transparent)]'
                            : 'bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--info)_30%,transparent)]'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-bold text-base">
                              {operator.operator_type === 'rail_operator' ? '🚂' : '🚛'} {operator.operator_name}
                            </p>
                            <p className="text-sm text-[var(--afcfta-muted)]">{operator.group}</p>
                            <p className="text-xs text-[var(--afcfta-muted)] mt-1">{operator.country_iso}</p>
                          </div>
                          {operator.fleet_size > 0 && (
                            <div className="text-right">
                              <p className="text-2xl font-bold text-[var(--text)]">{operator.fleet_size}</p>
                              <p className="text-xs text-[var(--afcfta-muted)]">
                                {operator.operator_type === 'rail_operator' ? t.locomotives : t.trucks}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[var(--afcfta-muted)] text-center py-8">{t.noOperators}</p>
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
                      <CardTitle className="text-sm font-semibold text-[var(--info)]">🌐 {t.global3pl}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2">
                        {logisticsNetwork.global_3pl_present.map((c, i) => (
                          <Badge key={i} className="bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)]">{c}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.regional_trucking_operators?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-[var(--terra)]">🚛 {t.regionalTrucking}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2">
                        {logisticsNetwork.regional_trucking_operators.map((c, i) => (
                          <Badge key={i} className="bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] text-[var(--terra)]">{c}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.rail_operators_present?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-[var(--danger)]">🚂 {t.railOperators}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex flex-wrap gap-2">
                        {logisticsNetwork.rail_operators_present.map((c, i) => (
                          <Badge key={i} className="bg-[color-mix(in_srgb,var(--danger)_8%,var(--afcfta-card))] text-[var(--danger)]">{c}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.corridor_management_bodies?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-[var(--violet)]">🏛️ {t.corridorBodies}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-1">
                        {logisticsNetwork.corridor_management_bodies.map((c, i) => (
                          <p key={i} className="text-sm text-[var(--text)] flex items-start gap-2">
                            <span className="text-[var(--violet)]">▸</span>{c}
                          </p>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {logisticsNetwork.local_agents_by_country && Object.keys(logisticsNetwork.local_agents_by_country).length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-semibold text-[var(--success)]">👥 {t.localAgents}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-4 max-h-80 overflow-y-auto">
                        {Object.entries(logisticsNetwork.local_agents_by_country).map(([country, agents]) => (
                          <div key={country}>
                            <p className="text-xs font-bold text-[var(--afcfta-muted)] uppercase mb-2 border-b pb-1">{country}</p>
                            <div className="space-y-2">
                              {agents.map((agent, i) => (
                                <div key={i} className="p-2 bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] rounded border-l-2 border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
                                  <p className="font-semibold text-sm text-[var(--success)]">{agent.company_name}</p>
                                  {agent.city && <p className="text-xs text-[var(--afcfta-muted)]">📍 {agent.city}{agent.address ? ` – ${agent.address}` : ''}</p>}
                                  <div className="flex flex-wrap gap-2 mt-1">
                                    {agent.phone && (
                                      <a href={`tel:${agent.phone}`} className="text-xs text-[var(--info)] hover:underline">📞 {agent.phone}</a>
                                    )}
                                    {agent.email && (
                                      <a href={`mailto:${agent.email}`} className="text-xs text-[var(--info)] hover:underline">✉️ {agent.email}</a>
                                    )}
                                    {agent.website && (
                                      <a href={agent.website} target="_blank" rel="noopener noreferrer" className="text-xs text-[var(--info)] hover:underline">🌐 {agent.website.replace(/^https?:\/\//, '')}</a>
                                    )}
                                  </div>
                                  {agent.operating_hours && <p className="text-xs text-[var(--afcfta-muted)] mt-1">🕐 {agent.operating_hours}</p>}
                                  {agent.services?.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {agent.services.map((s, si) => (
                                        <Badge key={si} variant="secondary" className="text-xs bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)]">{s}</Badge>
                                      ))}
                                    </div>
                                  )}
                                  {agent.certifications?.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {agent.certifications.map((c, ci) => (
                                        <Badge key={ci} className="text-xs bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] text-[var(--info)]">{c}</Badge>
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
                      <CardTitle className="text-sm font-semibold text-[var(--text)]">⚙️ {t.serviceProviders}</CardTitle>
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
              <div className="text-center p-8 text-[var(--afcfta-muted)]">
                <p>{t.noNetwork}</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Source information */}
        <div className="mt-4 text-xs text-[var(--afcfta-muted)] bg-[var(--afcfta-card2)] p-3 rounded">
          <span className="font-semibold">{t.source}: </span>
          {corridor.source_org}
        </div>
      </DialogContent>
    </Dialog>
  );
}
