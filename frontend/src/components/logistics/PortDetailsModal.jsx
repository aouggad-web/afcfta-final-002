import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  LineChart, Line, Legend, AreaChart, Area 
} from 'recharts';

function PortDetailsModal({ isOpen, onClose, port, language = 'fr' }) {
  const texts = {
    fr: {
      overview: "Vue d'ensemble",
      performance: "Performance & TRS (WCO)",
      connectivity: "Connectivité & Réseau",
      portAuthority: "Autorité Portuaire",
      website: "Site Web",
      phone: "Téléphone",
      email: "Email",
      fax: "Fax",
      annualTraffic: "Trafic Annuel (TEU)",
      globalTonnage: "Tonnage Global",
      vesselCalls: "Escales Navires",
      portTime: "Temps au Port",
      hours: "heures",
      services: "services",
      containers: "conteneurs",
      ships: "navires",
      tons: "tonnes",
      teuYear: "TEU/an",
      tonsYear: "tonnes/an",
      trafficEvolution: "Évolution du Trafic",
      performanceMetrics: "Métriques de Performance",
      trsAnalysis: "Analyse TRS (Time Release Study)",
      wcoProgramSince: "Pays membre programme TRS OMD depuis",
      trsStudiesPerformed: "Études TRS réalisées dans ce port",
      clearanceTimes: "Temps de Dédouanement",
      avgPhysicalInspection: "Inspection physique moyenne",
      withoutInspection: "Sans inspection",
      withInspection: "Avec inspection",
      improvements: "Améliorations",
      vsLastTrs: "vs dernière TRS",
      lsciConnectivity: "Connectivité LSCI (CNUCED)",
      lsciDesc: "Liner Shipping Connectivity Index - Mesure la connectivité maritime",
      currentScore: "Score Actuel",
      trend: "Tendance",
      evolution5Years: "Évolution 5 ans",
      worldRank: "Rang Mondial",
      africaRank: "Rang Afrique",
      topConnections: "Top Connexions",
      shippingLines: "Lignes Maritimes",
      servicesOffered: "Services Offerts",
      noShippingLines: "Aucune ligne maritime référencée",
      source: "Source données",
      sourceText: "UNCTAD Maritime Review 2024, WCO TRS Database, World Bank LPI",
      grade: "Grade",
      location: "Localisation",
      viewOnMaps: "Voir sur Google Maps",
      dataYear: "Année Données",
      methodology: "Méthodologie",
      viewEstimationMethod: "Voir la méthodologie d'estimation",
      whyNoOfficialData: "Pourquoi pas de données officielles",
      factualDataUsed: "Données factuelles utilisées",
      viewSourceReport: "Voir le rapport source",
      viewWcoReport: "Voir le rapport TRS officiel WCO",
      trsNotAvailable: "Données TRS Non Disponibles",
      trsNotAvailableDesc: "Aucune étude TRS (Time Release Study) n'a été publiée pour ce port.",
      sourcesFooter: "Sources: Études TRS WCO officielles, TRS nationales (ex: Egypt Customs), Autorités portuaires (KPA, Transnet, PAA), World Bank CPPI.",
      directConnections: "Connexions directes et rotations"
    },
    en: {
      overview: "Overview",
      performance: "Performance & TRS (WCO)",
      connectivity: "Connectivity & Network",
      portAuthority: "Port Authority",
      website: "Website",
      phone: "Phone",
      email: "Email",
      fax: "Fax",
      annualTraffic: "Annual Traffic (TEU)",
      globalTonnage: "Global Tonnage",
      vesselCalls: "Vessel Calls",
      portTime: "Port Time",
      hours: "hours",
      services: "services",
      containers: "containers",
      ships: "vessels",
      tons: "tons",
      teuYear: "TEU/year",
      tonsYear: "tons/year",
      trafficEvolution: "Traffic Evolution",
      performanceMetrics: "Performance Metrics",
      trsAnalysis: "TRS Analysis (Time Release Study)",
      wcoProgramSince: "WCO TRS program member since",
      trsStudiesPerformed: "TRS studies performed at this port",
      clearanceTimes: "Clearance Times",
      avgPhysicalInspection: "Average physical inspection",
      withoutInspection: "Without inspection",
      withInspection: "With inspection",
      improvements: "Improvements",
      vsLastTrs: "vs last TRS",
      lsciConnectivity: "LSCI Connectivity (UNCTAD)",
      lsciDesc: "Liner Shipping Connectivity Index - Measures maritime connectivity",
      currentScore: "Current Score",
      trend: "Trend",
      evolution5Years: "5-year evolution",
      worldRank: "World Rank",
      africaRank: "Africa Rank",
      topConnections: "Top Connections",
      shippingLines: "Shipping Lines",
      servicesOffered: "Services Offered",
      noShippingLines: "No shipping lines referenced",
      source: "Data source",
      sourceText: "UNCTAD Maritime Review 2024, WCO TRS Database, World Bank LPI",
      grade: "Grade",
      location: "Location",
      viewOnMaps: "View on Google Maps",
      dataYear: "Data Year",
      methodology: "Methodology",
      viewEstimationMethod: "View estimation methodology",
      whyNoOfficialData: "Why no official data",
      factualDataUsed: "Factual data used",
      viewSourceReport: "View source report",
      viewWcoReport: "View official WCO TRS report",
      trsNotAvailable: "TRS Data Not Available",
      trsNotAvailableDesc: "No TRS (Time Release Study) study has been published for this port.",
      sourcesFooter: "Sources: Official WCO TRS studies, National TRS (e.g. Egypt Customs), Port Authorities (KPA, Transnet, PAA), World Bank CPPI.",
      directConnections: "Direct connections and rotations"
    }
  };

  const t = texts[language];

  if (!port) return null;

  const getEfficiencyColor = (grade) => {
    switch (grade) {
      case 'A+': return 'bg-emerald-600';
      case 'A': return 'bg-green-500';
      case 'B': return 'bg-blue-500';
      case 'B-': return 'bg-yellow-500';
      case 'C': return 'bg-orange-500';
      case 'D': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const metrics = port.performance_metrics || {};
  const history = port.traffic_evolution || [];
  const authority = port.port_authority;
  const trs = port.trs_analysis;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl w-[95vw] max-h-[90vh] overflow-y-auto p-0">
        <DialogHeader className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white p-6 rounded-t-lg shadow-lg sticky top-0 z-10">
          <div className="flex flex-col md:flex-row justify-between items-start gap-4">
            <div>
              <div className="flex items-center gap-3">
                <span className="text-4xl">⚓</span>
                <div>
                  <DialogTitle className="text-3xl font-bold text-white">
                    {port.port_name}
                  </DialogTitle>
                  <DialogDescription className="text-blue-100 mt-1 text-lg flex items-center gap-2">
                    <span>📍 {port.city}, {port.country_name}</span>
                    {port.un_locode && <Badge variant="outline" className="text-white border-white/30 text-xs">{port.un_locode}</Badge>}
                  </DialogDescription>
                </div>
              </div>
            </div>
            <div className="flex flex-col items-end gap-2">
              <Badge className="bg-white/20 hover:bg-white/30 text-white border-0 px-3 py-1">
                {port.port_type}
              </Badge>
              {metrics.efficiency_grade && (
                <Badge className={`${getEfficiencyColor(metrics.efficiency_grade)} text-white font-bold px-4 py-1 text-base shadow-sm border border-white/20`}>
                  {t.grade} {metrics.efficiency_grade}
                </Badge>
              )}
            </div>
          </div>
        </DialogHeader>

        <div className="p-6">
        <Tabs defaultValue="overview" className="mt-2">
          <TabsList className="grid w-full grid-cols-3 bg-blue-50/50 p-1 rounded-lg">
            <TabsTrigger value="overview" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">{t.overview}</TabsTrigger>
            <TabsTrigger value="performance" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">{t.performance}</TabsTrigger>
            <TabsTrigger value="connectivity" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">{t.connectivity}</TabsTrigger>
          </TabsList>

          {/* ONGLET VUE D'ENSEMBLE */}
          <TabsContent value="overview" className="space-y-6 mt-6">
            
            {/* Port Authority Section (if available) */}
            {authority && (
              <Card className="border-l-4 border-l-blue-800 bg-gradient-to-r from-blue-50 to-white">
                <CardContent className="pt-6">
                  <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                    <div>
                      <h4 className="text-sm font-bold text-blue-800 uppercase tracking-wide mb-1">🏛️ {t.portAuthority}</h4>
                      <h3 className="text-xl font-bold text-gray-900">{authority.name}</h3>
                      {authority.address && <p className="text-sm text-gray-600 mt-1">📍 {authority.address}</p>}
                    </div>
                  </div>
                  
                  {/* Contact Details Grid */}
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                    {authority.website && authority.website !== 'N/A' && authority.website !== 'Non disponible' && (
                      <a 
                        href={authority.website.startsWith('http') ? authority.website : `https://${authority.website}`}
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 p-3 bg-white rounded-lg border border-blue-200 hover:bg-blue-50 hover:border-blue-400 transition-colors"
                      >
                        <span className="text-xl">🌐</span>
                        <div>
                          <p className="text-xs text-gray-500 font-medium">{t.website}</p>
                          <p className="text-sm text-blue-600 font-semibold truncate max-w-[150px]">
                            {authority.website.replace('https://', '').replace('http://', '')}
                          </p>
                        </div>
                      </a>
                    )}
                    
                    {authority.contact_phone && authority.contact_phone !== 'Voir site officiel' && authority.contact_phone !== '' && (
                      <a 
                        href={`tel:${authority.contact_phone.replace(/\s/g, '')}`}
                        className="flex items-center gap-2 p-3 bg-white rounded-lg border border-green-200 hover:bg-green-50 hover:border-green-400 transition-colors"
                      >
                        <span className="text-xl">📞</span>
                        <div>
                          <p className="text-xs text-gray-500 font-medium">{t.phone}</p>
                          <p className="text-sm text-green-700 font-semibold">{authority.contact_phone}</p>
                        </div>
                      </a>
                    )}
                    
                    {authority.contact_email && authority.contact_email !== 'contact@authority.com' && authority.contact_email !== '' && (
                      <a 
                        href={`mailto:${authority.contact_email}`}
                        className="flex items-center gap-2 p-3 bg-white rounded-lg border border-orange-200 hover:bg-orange-50 hover:border-orange-400 transition-colors"
                      >
                        <span className="text-xl">✉️</span>
                        <div>
                          <p className="text-xs text-gray-500 font-medium">Email</p>
                          <p className="text-sm text-orange-700 font-semibold truncate max-w-[150px]">{authority.contact_email}</p>
                        </div>
                      </a>
                    )}
                    
                    {authority.address && (
                      <a 
                        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(authority.address)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 p-3 bg-white rounded-lg border border-purple-200 hover:bg-purple-50 hover:border-purple-400 transition-colors"
                      >
                        <span className="text-xl">📍</span>
                        <div>
                          <p className="text-xs text-gray-500 font-medium">{language === 'en' ? 'Location' : 'Localisation'}</p>
                          <p className="text-sm text-purple-700 font-semibold">{language === 'en' ? 'View on Google Maps' : 'Voir sur Google Maps'}</p>
                        </div>
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-6 text-center">
                  <p className="text-sm font-semibold text-blue-600 mb-1">{t.annualTraffic}</p>
                  <p className="text-3xl font-bold text-blue-800">
                    {(port.latest_stats?.container_throughput_teu || 0).toLocaleString()}
                  </p>
                  <p className="text-xs text-blue-500 mt-1">{port.latest_stats?.year || 2024}</p>
                </CardContent>
              </Card>
              <Card className="bg-indigo-50 border-indigo-200">
                <CardContent className="pt-6 text-center">
                  <p className="text-sm font-semibold text-indigo-600 mb-1">{t.globalTonnage}</p>
                  <p className="text-3xl font-bold text-indigo-800">
                    {(port.latest_stats?.cargo_throughput_tons || 0).toLocaleString()}
                  </p>
                  <p className="text-xs text-indigo-500 mt-1">{t.tons}</p>
                </CardContent>
              </Card>
              <Card className="bg-teal-50 border-teal-200">
                <CardContent className="pt-6 text-center">
                  <p className="text-sm font-semibold text-teal-600 mb-1">{t.vesselCalls}</p>
                  <p className="text-3xl font-bold text-teal-800">
                    {(port.latest_stats?.vessel_calls || 0).toLocaleString()}
                  </p>
                  <p className="text-xs text-teal-500 mt-1">{t.ships}</p>
                </CardContent>
              </Card>
            </div>

            {/* Evolution Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg text-gray-700 flex items-center gap-2">
                  📉 {t.trafficEvolution} (2020-2024)
                </CardTitle>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={history}>
                    <defs>
                      <linearGradient id="colorTeu" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="year" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value) => value.toLocaleString()}
                      contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="teu" 
                      stroke="#2563eb" 
                      fillOpacity={1} 
                      fill="url(#colorTeu)" 
                      name="Trafic TEU"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ONGLET PERFORMANCE & TRS */}
          <TabsContent value="performance" className="space-y-6 mt-6">
            
            {/* WCO TRS SECTION - DONNÉES MULTI-SOURCES */}
            <Card className="border-t-4 border-t-purple-600 shadow-md">
              <CardHeader className="bg-purple-50">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl text-purple-900 flex items-center gap-2">
                      ⏱️ {language === 'en' ? 'Container Dwell Time' : 'Temps de Séjour Conteneur (Dwell Time)'}
                    </CardTitle>
                    <CardDescription>
                      {trs?.source_reliability_label ? (
                        <span className="flex items-center gap-2">
                          {t.source}: <Badge variant="outline" className={
                            trs.source_reliability_level === 1 ? "bg-green-100 text-green-800" :
                            trs.source_reliability_level === 2 ? "bg-blue-100 text-blue-800" :
                            trs.source_reliability_level === 3 ? "bg-yellow-100 text-yellow-800" :
                            "bg-gray-100 text-gray-600"
                          }>{trs.source_reliability_label}</Badge>
                        </span>
                      ) : (language === 'en' ? "TRS Data (Time Release Study)" : "Données TRS (Time Release Study)")}
                    </CardDescription>
                  </div>
                  {trs?.container_dwell_time_days && trs.container_dwell_time_days !== "NA" ? (
                    <Badge className="bg-purple-600 text-white text-lg px-4 py-2">
                      {typeof trs.container_dwell_time_days === 'number' ? `${trs.container_dwell_time_days} ${language === 'en' ? 'Days' : 'Jours'}` : trs.container_dwell_time_days}
                    </Badge>
                  ) : (
                    <Badge className="bg-gray-400 text-white text-lg px-4 py-2">
                      NA
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                {trs?.container_dwell_time_days && trs.container_dwell_time_days !== "NA" ? (
                  <div className="space-y-4">
                    {/* Avertissement si source non-officielle */}
                    {trs.warning && (
                      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                        {trs.warning}
                      </div>
                    )}
                    
                    {/* Données disponibles */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-purple-50 p-4 rounded-lg text-center">
                        <p className="text-xs font-semibold text-purple-600">Dwell Time</p>
                        <p className="text-2xl font-bold text-purple-800">
                          {typeof trs.container_dwell_time_days === 'number' ? trs.container_dwell_time_days : trs.container_dwell_time_days}
                        </p>
                        <p className="text-xs text-purple-500">jours</p>
                      </div>
                      {trs.vessel_turnaround_hours && trs.vessel_turnaround_hours !== "NA" && (
                        <div className="bg-blue-50 p-4 rounded-lg text-center">
                          <p className="text-xs font-semibold text-blue-600">Rotation Navire</p>
                          <p className="text-2xl font-bold text-blue-800">{trs.vessel_turnaround_hours}</p>
                          <p className="text-xs text-blue-500">{t.hours}</p>
                        </div>
                      )}
                      {trs.cppi_rank && trs.cppi_rank !== "NA" && (
                        <div className="bg-green-50 p-4 rounded-lg text-center">
                          <p className="text-xs font-semibold text-green-600">Rang CPPI</p>
                          <p className="text-2xl font-bold text-green-800">#{trs.cppi_rank}</p>
                          <p className="text-xs text-green-500">{trs.cppi_year || ''}</p>
                        </div>
                      )}
                      <div className="bg-orange-50 p-4 rounded-lg text-center">
                        <p className="text-xs font-semibold text-orange-600">{t.dataYear}</p>
                        <p className="text-2xl font-bold text-orange-800">{trs.data_year}</p>
                        <p className="text-xs text-orange-500">{trs.source_reliability_label || ''}</p>
                      </div>
                    </div>
                    
                    {/* Source et méthodologie */}
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="font-semibold text-gray-700">📊 {t.source}:</p>
                          <p className="text-gray-600">{trs.source}</p>
                        </div>
                        <div>
                          <p className="font-semibold text-gray-700">📋 {t.methodology}:</p>
                          <p className="text-gray-600">{trs.methodology}</p>
                        </div>
                      </div>
                      {trs.notes && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-xs text-gray-500">💡 {trs.notes}</p>
                        </div>
                      )}
                      
                      {/* Méthodologie d'estimation si applicable */}
                      {trs.estimation_methodology && (
                        <details className="mt-4">
                          <summary className="cursor-pointer text-sm font-semibold text-amber-700 hover:text-amber-800">
                            📐 {t.viewEstimationMethod}
                          </summary>
                          <div className="mt-2 p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-800 whitespace-pre-line font-mono">
                            {trs.estimation_methodology}
                          </div>
                        </details>
                      )}
                      
                      {/* Raison de l'absence de données officielles */}
                      {trs.no_official_data_reason && (
                        <div className="mt-3 p-2 bg-gray-100 rounded text-xs text-gray-600 italic">
                          ℹ️ {t.whyNoOfficialData}: {trs.no_official_data_reason}
                        </div>
                      )}
                      
                      {/* Données factuelles utilisées */}
                      {trs.factual_data_points && trs.factual_data_points.length > 0 && (
                        <div className="mt-3 p-2 bg-blue-50 rounded text-xs">
                          <p className="font-semibold text-blue-700 mb-1">📊 {t.factualDataUsed}:</p>
                          <ul className="list-disc list-inside text-blue-600">
                            {trs.factual_data_points.map((point, idx) => (
                              <li key={idx}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {trs.source_url && (
                        <a 
                          href={trs.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-3 inline-flex items-center gap-2 text-sm text-purple-600 hover:text-purple-800"
                        >
                          📄 {t.viewSourceReport}
                        </a>
                      )}
                      {trs.wco_report_url && (
                        <a 
                          href={trs.wco_report_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-3 inline-flex items-center gap-2 text-sm text-purple-600 hover:text-purple-800"
                        >
                          📄 {t.viewWcoReport}
                        </a>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-6xl mb-4">📊</div>
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">{t.trsNotAvailable}</h3>
                    <p className="text-sm text-gray-500 max-w-md mx-auto mb-4">
                      {t.trsNotAvailableDesc}
                    </p>
                    {trs?.no_official_data_reason && (
                      <p className="text-xs text-gray-400 mb-4 italic">
                        ℹ️ {trs.no_official_data_reason}
                      </p>
                    )}
                    {trs?.wco_trs_in_progress && (
                      <Badge className="bg-yellow-100 text-yellow-800 border border-yellow-300">
                        ⏳ Étude TRS WCO en cours
                      </Badge>
                    )}
                    {trs?.notes && trs.notes !== "Aucune étude TRS (Time Release Study) disponible pour ce port." && (
                      <p className="text-xs text-gray-400 mt-4">{trs.notes}</p>
                    )}
                    
                    {/* Benchmarks de comparaison */}
                    {port.global_benchmarks && (
                      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200 text-left">
                        <p className="text-sm font-semibold text-blue-800 mb-2">📈 Benchmarks de référence</p>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-blue-600">Moyenne Afrique:</p>
                            <p className="font-bold text-blue-800">{port.global_benchmarks.africa_avg_dwell_days} jours</p>
                            <p className="text-xs text-blue-500">{port.global_benchmarks.africa_avg_source}</p>
                          </div>
                          <div>
                            <p className="text-blue-600">Médiane Mondiale:</p>
                            <p className="font-bold text-blue-800">{port.global_benchmarks.global_median_dwell_days_h2_2023} jour</p>
                            <p className="text-xs text-blue-500">UNCTAD H2 2023</p>
                          </div>
                        </div>
                        <p className="text-xs text-blue-400 mt-2 italic">{port.global_benchmarks.africa_avg_note}</p>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Note sur la couverture TRS en petit caractère */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-400 italic leading-relaxed">
                    📊 <strong>Note sur la couverture TRS:</strong> La couverture des données TRS officielles pour les ports africains est limitée (~15-20% des ports majeurs). 
                    Cela reflète la réalité: peu d'études TRS WCO ont été conduites pour l'Afrique, et les autorités portuaires ne publient pas systématiquement leurs données de performance.
                    {t.sourcesFooter}
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Waiting Times (Ship) */}
              <Card className="border-l-4 border-l-yellow-500 shadow-md">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    ⏳ Temps d'Attente Navire
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Attente au mouillage</span>
                        <span className="text-sm font-bold text-yellow-700">{metrics.avg_waiting_time_hours || 0} {t.hours}</span>
                      </div>
                      <Progress value={Math.min((metrics.avg_waiting_time_hours / 48) * 100, 100)} className="h-3 bg-gray-100" indicatorClassName="bg-yellow-500" />
                      <p className="text-xs text-gray-500 mt-1">Indicateur de congestion nautique</p>
                    </div>
                    
                    <div className="pt-4 border-t bg-gray-50 -mx-6 px-6 pb-2 mt-4">
                      <div className="flex justify-between items-center py-2">
                        <span className="text-base font-bold text-gray-700">Temps Total de Rotation</span>
                        <span className="text-2xl font-extrabold text-blue-800">{metrics.avg_port_stay_hours || 0} h</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Productivity Indicators */}
              <Card className="border-l-4 border-l-green-500 shadow-md">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    🏗️ Productivité
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="bg-green-50 p-4 rounded-lg flex items-center justify-between border border-green-100">
                    <div>
                      <p className="text-sm text-green-800 font-semibold">{language === 'en' ? 'Moves/Hour' : 'Mouvements / Heure'}</p>
                      <p className="text-3xl font-bold text-green-900">
                        {port.latest_stats?.berth_productivity_moves_per_hour || (port.port_type === 'Hub Transhipment' ? '45+' : '25-30')}
                      </p>
                    </div>
                    <div className="text-3xl">🏗️</div>
                  </div>
                  
                  <div className="bg-blue-50 p-4 rounded-lg flex items-center justify-between border border-blue-100">
                    <div>
                      <p className="text-sm text-blue-800 font-semibold">{t.lsciConnectivity}</p>
                      <p className="text-3xl font-bold text-blue-900">
                        {port.lsci?.value || (port.port_type === 'Hub Transhipment' ? 'High' : 'Medium')}
                      </p>
                      {port.lsci?.world_rank && <p className="text-xs text-blue-600">{t.worldRank}: #{port.lsci.world_rank}</p>}
                    </div>
                    <div className="text-3xl">🌍</div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ONGLET CONNECTIVITÉ */}
          <TabsContent value="connectivity" className="space-y-6 mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Lignes Régulières */}
              <Card className="shadow-md h-full">
                <CardHeader className="bg-gray-50 border-b">
                  <CardTitle className="text-lg flex items-center gap-2">
                    🚢 {t.shippingLines}
                  </CardTitle>
                  <CardDescription>
                    {t.directConnections}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-4 max-h-[500px] overflow-y-auto">
                  <ul className="space-y-4">
                    {(port.services || port.connectivity?.liner_services || []).map((service, idx) => (
                      <li key={idx} className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-sm transition-shadow">
                        {typeof service === 'object' ? (
                          <>
                            <div className="flex justify-between items-start mb-2">
                              <span className="font-bold text-blue-800">{service.service_name || service.carrier}</span>
                              <Badge variant="secondary" className="text-xs">{service.frequency || (language === 'en' ? 'Regular' : 'Régulier')}</Badge>
                            </div>
                            <div className="text-sm text-gray-600 mb-1">
                              <span className="font-semibold">{language === 'en' ? 'Carrier:' : 'Armateur:'}</span> {service.carrier}
                            </div>
                            {service.rotation && (
                              <div className="text-xs bg-gray-50 p-2 rounded mt-2 border-l-2 border-blue-400">
                                <span className="font-semibold text-gray-700 block mb-1">{language === 'en' ? 'Rotation:' : 'Rotation:'}</span>
                                <span className="text-gray-600 leading-relaxed">{service.rotation}</span>
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="flex items-center gap-2">
                            <span className="text-blue-500">●</span>
                            <span className="font-medium text-gray-700">{service}</span>
                          </div>
                        )}
                      </li>
                    ))}
                    {(!port.services && !port.connectivity?.liner_services) && (
                      <p className="text-gray-500 italic text-center py-4">{language === 'en' ? 'No regular shipping line data available.' : 'Aucune donnée de ligne régulière disponible.'}</p>
                    )}
                  </ul>
                </CardContent>
              </Card>

              {/* Agents Maritimes */}
              <Card className="shadow-md h-full">
                <CardHeader className="bg-gray-50 border-b">
                  <CardTitle className="text-lg flex items-center gap-2">
                    🏢 {language === 'en' ? 'Maritime Agents' : 'Agents Maritimes'}
                  </CardTitle>
                  <CardDescription>
                    {language === 'en' ? 'Local representatives and contacts' : 'Représentants et contacts locaux'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-4 max-h-[500px] overflow-y-auto">
                  <ul className="space-y-3">
                    {(port.agents || port.connectivity?.shipping_agents || []).map((agent, idx) => (
                      <li key={idx} className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-sm transition-shadow">
                        {typeof agent === 'object' ? (
                          <div>
                            <div className="flex justify-between items-start">
                              <span className="font-bold text-gray-800">{agent.agent_name}</span>
                              {agent.group && <Badge variant="outline" className="text-xs text-gray-500">{agent.group}</Badge>}
                            </div>
                            
                            {agent.address && (
                              <div className="flex items-start gap-2 mt-2 text-xs text-gray-600">
                                <span>📍</span>
                                <span>{agent.address}</span>
                              </div>
                            )}
                            
                            <div className="flex flex-wrap gap-3 mt-3">
                              {agent.website && agent.website !== 'Non disponible' && agent.website !== 'N/A' && (
                                <a 
                                  href={agent.website.startsWith('http') ? agent.website : `https://${agent.website}`}
                                  target="_blank" 
                                  rel="noopener noreferrer" 
                                  className="text-xs text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1 bg-blue-50 px-2 py-1 rounded"
                                >
                                  🌐 Site Web
                                </a>
                              )}
                              {agent.contact && agent.contact !== 'N/A' && (
                                <a 
                                  href={`tel:${agent.contact.replace(/\s/g, '')}`}
                                  className="text-xs text-green-600 hover:text-green-800 flex items-center gap-1 bg-green-50 px-2 py-1 rounded"
                                >
                                  📞 {agent.contact}
                                </a>
                              )}
                              {agent.email && (
                                <a 
                                  href={`mailto:${agent.email}`}
                                  className="text-xs text-orange-600 hover:text-orange-800 flex items-center gap-1 bg-orange-50 px-2 py-1 rounded"
                                >
                                  ✉️ Email
                                </a>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <span className="text-green-500">●</span>
                            <span className="font-medium text-gray-700">{agent}</span>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default PortDetailsModal;
