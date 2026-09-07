import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function AirportDetailsModal({ airport, open, onClose, language = 'fr' }) {
  const texts = {
    fr: {
      cargoFreight: "Fret Cargo",
      mail: "Courrier",
      movements: "Mouvements",
      cargoAircraft: "avions cargo",
      annualCapacity: "Capacité Annuelle",
      tonsYear: "tonnes/an",
      tons: "tonnes",
      cargoInfrastructure: "Infrastructure Cargo",
      cargoTerminalArea: "Surface Terminal Cargo",
      gpsCoordinates: "Coordonnées GPS",
      notes: "Notes",
      cargoActors: "Acteurs Cargo",
      routes: "Routes",
      historicalStats: "Statistiques Historiques",
      airCargoActors: "Acteurs du Cargo Aérien",
      cargoAirlines: "Compagnies Aériennes Cargo",
      handlersGround: "Handlers & Services au Sol",
      forwarders: "Transitaires & Freight Forwarders",
      noActors: "Aucun acteur enregistré",
      regularCargoRoutes: "Routes Cargo Régulières",
      destination: "Destination",
      carrier: "Opérateur",
      frequency: "Fréquence",
      aircraftType: "Type Avion",
      noRoutes: "Aucune route régulière enregistrée",
      cargoEvolution: "Évolution du Fret Cargo",
      tonsPerYear: "Tonnes par année",
      mailEvolution: "Évolution du Courrier",
      movementsEvolution: "Mouvements Cargo par Année",
      noHistorical: "Aucune donnée historique disponible",
      dataSource: "Source données",
      sourceText: "IATA Cargo Database 2023 | ACI World Airport Traffic Report | National Civil Aviation Authorities"
    },
    en: {
      cargoFreight: "Cargo Freight",
      mail: "Mail",
      movements: "Movements",
      cargoAircraft: "cargo aircraft",
      annualCapacity: "Annual Capacity",
      tonsYear: "tons/year",
      tons: "tons",
      cargoInfrastructure: "Cargo Infrastructure",
      cargoTerminalArea: "Cargo Terminal Area",
      gpsCoordinates: "GPS Coordinates",
      notes: "Notes",
      cargoActors: "Cargo Actors",
      routes: "Routes",
      historicalStats: "Historical Statistics",
      airCargoActors: "Air Cargo Actors",
      cargoAirlines: "Cargo Airlines",
      handlersGround: "Handlers & Ground Services",
      forwarders: "Freight Forwarders",
      noActors: "No actors registered",
      regularCargoRoutes: "Regular Cargo Routes",
      destination: "Destination",
      carrier: "Carrier",
      frequency: "Frequency",
      aircraftType: "Aircraft Type",
      noRoutes: "No regular routes registered",
      cargoEvolution: "Cargo Freight Evolution",
      tonsPerYear: "Tons per year",
      mailEvolution: "Mail Evolution",
      movementsEvolution: "Cargo Movements per Year",
      noHistorical: "No historical data available",
      dataSource: "Data source",
      sourceText: "IATA Cargo Database 2023 | ACI World Airport Traffic Report | National Civil Aviation Authorities"
    }
  };

  const t = texts[language];

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return language === 'en' 
      ? new Intl.NumberFormat('en-US').format(num)
      : new Intl.NumberFormat('fr-FR').format(num);
  };

  if (!airport) return null;

  const latestStats = airport.historical_stats?.[0] || {};
  const historicalData = airport.historical_stats ? [...airport.historical_stats].reverse() : [];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-sky-900 flex items-center gap-2">
            <span>✈️</span>
            {airport.airport_name}
            {airport.iata_code && (
              <Badge variant="outline" className="ml-2 text-sm">{airport.iata_code}</Badge>
            )}
          </DialogTitle>
          <DialogDescription className="flex gap-2 mt-2">
            <Badge className="bg-sky-600">{airport.country_name}</Badge>
            <Badge variant="outline">{airport.icao_code}</Badge>
          </DialogDescription>
        </DialogHeader>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-4">
          <Card className="bg-gradient-to-br from-sky-50 to-sky-100 border-sky-200">
            <CardContent className="pt-4">
              <p className="text-xs font-semibold text-sky-700 mb-1">📦 {t.cargoFreight} {latestStats.year}</p>
              <p className="text-2xl font-bold text-sky-900">{formatNumber(latestStats.cargo_throughput_tons)}</p>
              <p className="text-xs text-gray-600">{t.tons}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
            <CardContent className="pt-4">
              <p className="text-xs font-semibold text-amber-700 mb-1">📬 {t.mail} {latestStats.year}</p>
              <p className="text-2xl font-bold text-amber-900">{formatNumber(latestStats.mail_throughput_tons)}</p>
              <p className="text-xs text-gray-600">{t.tons}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="pt-4">
              <p className="text-xs font-semibold text-green-700 mb-1">🛩️ {t.movements} {latestStats.year}</p>
              <p className="text-2xl font-bold text-green-900">{formatNumber(latestStats.cargo_aircraft_movements)}</p>
              <p className="text-xs text-gray-600">{t.cargoAircraft}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <CardContent className="pt-4">
              <p className="text-xs font-semibold text-purple-700 mb-1">📊 {t.annualCapacity}</p>
              <p className="text-2xl font-bold text-purple-900">{formatNumber(airport.annual_capacity_tons)}</p>
              <p className="text-xs text-gray-600">{t.tonsYear}</p>
            </CardContent>
          </Card>
        </div>

        {/* Infrastructure */}
        <Card className="mb-4">
          <CardHeader className="bg-gray-50">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>🏗️</span>
              {t.cargoInfrastructure}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🏢</span>
                <div>
                  <p className="text-xs text-gray-600">{t.cargoTerminalArea}</p>
                  <p className="font-bold text-gray-900">{formatNumber(airport.cargo_terminal_area_sqm)} m²</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">📍</span>
                <div>
                  <p className="text-xs text-gray-600">{t.gpsCoordinates}</p>
                  <p className="font-bold text-gray-900">{airport.geo_lat?.toFixed(4)}, {airport.geo_lon?.toFixed(4)}</p>
                </div>
              </div>
            </div>
            {airport.cargo_infra_notes && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-700">
                  <span className="font-semibold">💡 {t.notes}: </span>
                  {airport.cargo_infra_notes}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue="actors" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="actors">✈️ {t.cargoActors} ({airport.actors?.length || 0})</TabsTrigger>
            <TabsTrigger value="routes">🌐 {t.routes} ({airport.routes?.length || 0})</TabsTrigger>
            <TabsTrigger value="stats">📈 {t.historicalStats}</TabsTrigger>
          </TabsList>

          {/* Actors */}
          <TabsContent value="actors" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{t.airCargoActors}</CardTitle>
              </CardHeader>
              <CardContent>
                {airport.actors && airport.actors.length > 0 ? (
                  <div className="space-y-3">
                    <div>
                      <h4 className="font-semibold text-sky-900 mb-2 flex items-center gap-2">
                        <span>✈️</span>
                        {t.cargoAirlines}
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {airport.actors.filter(a => a.actor_type === 'airline').map((actor, idx) => (
                          <div key={idx} className="flex items-center gap-2 p-2 bg-sky-50 rounded">
                            <span className="text-lg">✈️</span>
                            <div className="flex-1">
                              <p className="font-semibold text-sm">{actor.actor_name}</p>
                              <p className="text-xs text-gray-600">{actor.group}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {airport.actors.filter(a => a.actor_type === 'handler').length > 0 && (
                      <div>
                        <h4 className="font-semibold text-amber-900 mb-2 flex items-center gap-2">
                          <span>🔧</span>
                          {t.handlersGround}
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {airport.actors.filter(a => a.actor_type === 'handler').map((actor, idx) => (
                            <div key={idx} className="flex items-center gap-2 p-2 bg-amber-50 rounded">
                              <span className="text-lg">🔧</span>
                              <div className="flex-1">
                                <p className="font-semibold text-sm">{actor.actor_name}</p>
                                <p className="text-xs text-gray-600">{actor.group}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {airport.actors.filter(a => a.actor_type === 'forwarder').length > 0 && (
                      <div>
                        <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                          <span>📦</span>
                          {t.forwarders}
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {airport.actors.filter(a => a.actor_type === 'forwarder').map((actor, idx) => (
                            <div key={idx} className="flex items-center gap-2 p-2 bg-green-50 rounded">
                              <span className="text-lg">📦</span>
                              <div className="flex-1">
                                <p className="font-semibold text-sm">{actor.actor_name}</p>
                                <p className="text-xs text-gray-600">{actor.group}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">{t.noActors}</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Routes */}
          <TabsContent value="routes" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{t.regularCargoRoutes}</CardTitle>
              </CardHeader>
              <CardContent>
                {airport.routes && airport.routes.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="text-left p-3">{t.destination}</th>
                          <th className="text-left p-3">{t.carrier}</th>
                          <th className="text-left p-3">{t.frequency}</th>
                          <th className="text-left p-3">{t.aircraftType}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {airport.routes.map((route, idx) => (
                          <tr key={idx} className="border-b hover:bg-gray-50">
                            <td className="p-3 font-semibold">{route.destination_airport}</td>
                            <td className="p-3">{route.airline}</td>
                            <td className="p-3">{route.frequency}</td>
                            <td className="p-3">{route.aircraft_type}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">{t.noRoutes}</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Stats */}
          <TabsContent value="stats" className="mt-4">
            {historicalData.length > 0 ? (
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">{t.cargoEvolution}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={historicalData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="year" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatNumber(value)} />
                        <Bar dataKey="cargo_throughput_tons" fill="#0ea5e9" name={t.tonsPerYear} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">{t.movementsEvolution}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={historicalData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="year" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatNumber(value)} />
                        <Line type="monotone" dataKey="cargo_aircraft_movements" stroke="#22c55e" strokeWidth={2} name={t.movements} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">{t.noHistorical}</p>
            )}
          </TabsContent>
        </Tabs>

        {/* Footer Source */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500">
            <span className="font-semibold">{t.dataSource}:</span> {t.sourceText}
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
