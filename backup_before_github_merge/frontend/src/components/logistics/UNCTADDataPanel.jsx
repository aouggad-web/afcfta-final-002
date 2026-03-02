import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Ship, TrendingUp, Globe, Award, Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#1e3a8a', '#60a5fa', '#93c5fd', '#bfdbfe'];

export default function UNCTADDataPanel({ language = 'fr' }) {
  const [portData, setPortData] = useState(null);
  const [lsciData, setLsciData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const texts = {
    fr: {
      title: "Statistiques UNCTAD",
      subtitle: "Données officielles - UNCTAD Maritime Transport Review 2024",
      portStats: "Trafic Portuaire Africain",
      totalThroughput: "Trafic Total",
      growth: "Croissance 2022-2023",
      globalShare: "Part du Commerce Mondial",
      topPorts: "Top Ports Africains (TEU)",
      algerianPorts: "Ports Algériens",
      lsciTitle: "Indice de Connectivité Maritime (LSCI)",
      lsciDesc: "L'indice LSCI mesure la connectivité d'un pays au réseau mondial de transport maritime",
      rankAfrica: "Rang Afrique",
      rankGlobal: "Rang Mondial",
      teu: "TEU",
      mTeu: "M TEU",
      loading: "Chargement des données UNCTAD...",
      error: "Erreur lors du chargement des données",
      source: "Source: UNCTAD - Review of Maritime Transport 2024"
    },
    en: {
      title: "UNCTAD Statistics",
      subtitle: "Official data - UNCTAD Maritime Transport Review 2024",
      portStats: "African Port Traffic",
      totalThroughput: "Total Throughput",
      growth: "Growth 2022-2023",
      globalShare: "Global Trade Share",
      topPorts: "Top African Ports (TEU)",
      algerianPorts: "Algerian Ports",
      lsciTitle: "Liner Shipping Connectivity Index (LSCI)",
      lsciDesc: "The LSCI measures a country's connectivity to global maritime transport networks",
      rankAfrica: "Africa Rank",
      rankGlobal: "Global Rank",
      teu: "TEU",
      mTeu: "M TEU",
      loading: "Loading UNCTAD data...",
      error: "Error loading data",
      source: "Source: UNCTAD - Review of Maritime Transport 2024"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchUNCTADData();
  }, []);

  const fetchUNCTADData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [portsRes, lsciRes] = await Promise.all([
        axios.get(`${API}/statistics/unctad/ports`),
        axios.get(`${API}/statistics/unctad/lsci`)
      ]);
      setPortData(portsRes.data);
      setLsciData(lsciRes.data);
    } catch (err) {
      console.error('Error fetching UNCTAD data:', err);
      setError(t.error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num?.toLocaleString() || '0';
  };

  const preparePortChartData = () => {
    if (!portData?.top_ports) return [];
    return portData.top_ports.map(port => ({
      name: port.port.length > 12 ? port.port.substring(0, 12) + '...' : port.port,
      fullName: port.port,
      throughput: port.throughput_teu / 1000000,
      country: language === 'en' ? port.country : port.country_fr,
      growth: port.growth_rate
    }));
  };

  const prepareLSCIChartData = () => {
    if (!lsciData) return [];
    return lsciData.slice(0, 10).map(item => ({
      name: language === 'en' ? item.country : item.country_fr,
      lsci: item.lsci_2023,
      rankAfrica: item.rank_africa,
      rankGlobal: item.rank_global
    }));
  };

  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardContent className="flex items-center justify-center h-48">
          <div className="text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto" />
            <p className="mt-4 text-gray-600">{t.loading}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-l-4 border-l-red-500">
        <CardContent className="py-8 text-center text-red-600">
          {error}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" data-testid="unctad-panel">
      {/* Header */}
      <Card className="bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 text-white shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl font-bold flex items-center gap-3">
            <Ship className="w-7 h-7" />
            {t.title}
          </CardTitle>
          <CardDescription className="text-cyan-100 text-base">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Key Metrics */}
      {portData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-blue-500 to-cyan-600 text-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm">{t.totalThroughput}</p>
                  <p className="text-3xl font-bold">
                    {(portData.total_african_port_throughput_teu_2023 / 1000000).toFixed(1)} {t.mTeu}
                  </p>
                </div>
                <Ship className="w-10 h-10 text-blue-200" />
              </div>
              <p className="text-xs text-blue-200 mt-2">2023</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-emerald-100 text-sm">{t.growth}</p>
                  <p className="text-3xl font-bold">+{portData.growth_rate_2022_2023}%</p>
                </div>
                <TrendingUp className="w-10 h-10 text-emerald-200" />
              </div>
              <p className="text-xs text-emerald-200 mt-2">YoY</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-violet-600 text-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">{t.globalShare}</p>
                  <p className="text-3xl font-bold">{portData.share_global_trade}%</p>
                </div>
                <Globe className="w-10 h-10 text-purple-200" />
              </div>
              <p className="text-xs text-purple-200 mt-2">{language === 'en' ? 'World Trade' : 'Commerce Mondial'}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Top Ports Chart */}
      {portData?.top_ports && (
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50">
            <CardTitle className="text-xl text-blue-700 flex items-center gap-2">
              <Award className="w-5 h-5" /> {t.topPorts}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={preparePortChartData()} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => `${v.toFixed(1)}M`} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                <Tooltip 
                  formatter={(value, name, props) => [
                    `${(value * 1000000).toLocaleString()} TEU`,
                    props.payload.fullName
                  ]}
                  labelFormatter={(label) => {
                    const data = preparePortChartData().find(d => d.name === label);
                    return data ? `${data.fullName} (${data.country})` : label;
                  }}
                />
                <Bar dataKey="throughput" radius={[0, 4, 4, 0]}>
                  {preparePortChartData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Port Details Table */}
            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">{language === 'en' ? 'Port' : 'Port'}</th>
                    <th className="px-4 py-2 text-left">{language === 'en' ? 'Country' : 'Pays'}</th>
                    <th className="px-4 py-2 text-right">{t.teu}</th>
                    <th className="px-4 py-2 text-right">{t.growth}</th>
                    <th className="px-4 py-2 text-center">{t.rankAfrica}</th>
                    <th className="px-4 py-2 text-center">{t.rankGlobal}</th>
                  </tr>
                </thead>
                <tbody>
                  {portData.top_ports.map((port, idx) => (
                    <tr key={port.port} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-2 font-medium">{port.port}</td>
                      <td className="px-4 py-2">{language === 'en' ? port.country : port.country_fr}</td>
                      <td className="px-4 py-2 text-right font-mono">{formatNumber(port.throughput_teu)}</td>
                      <td className="px-4 py-2 text-right">
                        <Badge className={port.growth_rate > 5 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}>
                          +{port.growth_rate}%
                        </Badge>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Badge variant="outline">#{port.rank_africa}</Badge>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Badge variant="outline" className="text-gray-500">#{port.rank_global}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* LSCI Chart */}
      {lsciData && lsciData.length > 0 && (
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-violet-50">
            <CardTitle className="text-xl text-purple-700 flex items-center gap-2">
              <Globe className="w-5 h-5" /> {t.lsciTitle}
            </CardTitle>
            <CardDescription className="text-purple-600">
              {t.lsciDesc}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={prepareLSCIChartData()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={80} />
                <YAxis domain={[0, 100]} />
                <Tooltip 
                  formatter={(value, name, props) => [
                    `LSCI: ${value}`,
                    `${t.rankAfrica}: #${props.payload.rankAfrica} | ${t.rankGlobal}: #${props.payload.rankGlobal}`
                  ]}
                />
                <Bar dataKey="lsci" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                  {prepareLSCIChartData().map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={index === 0 ? '#f59e0b' : index === 1 ? '#6b7280' : index === 2 ? '#b45309' : '#8b5cf6'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Source Footer */}
      <Card className="bg-gray-50 border-gray-200">
        <CardContent className="py-3">
          <p className="text-xs text-gray-500 text-center">
            {t.source}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
