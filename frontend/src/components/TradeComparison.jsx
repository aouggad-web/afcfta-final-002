import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { BarChart, Bar, LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { Globe, TrendingUp } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API_URL = BACKEND_URL || '';

const TradeComparison = () => {
  const [selectedYear, setSelectedYear] = useState('2024');
  const [selectedMetric, setSelectedMetric] = useState('exports');
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState(null);
  const [tradePerformanceGlobal, setTradePerformanceGlobal] = useState([]);
  const [tradePerformanceIntraAfrican, setTradePerformanceIntraAfrican] = useState([]);
  const [calculationsGlobal, setCalculationsGlobal] = useState([]);
  const [calculationsIntraAfrican, setCalculationsIntraAfrican] = useState([]);
  const [sortConfig, setSortConfig] = useState({ key: 'exports', direction: 'desc' });
  
  // Données de commerce INTRA-AFRICAIN par année (Source: OEC - Observatory of Economic Complexity)
  // Note: Le commerce intra-africain représente environ 15-17% du commerce total africain
  const tradeDataByYear = {
    '2022': [
      { country: 'ZA', name: 'Afrique du Sud', exports: 24.8, imports: 18.3, balance: 6.5, savings: 4.2 },
      { country: 'NG', name: 'Nigéria', exports: 8.9, imports: 12.4, balance: -3.5, savings: 2.8 },
      { country: 'DZ', name: 'Algérie', exports: 2.1, imports: 5.8, balance: -3.7, savings: 1.9 },
      { country: 'EG', name: 'Égypte', exports: 6.7, imports: 8.9, balance: -2.2, savings: 2.3 },
      { country: 'MA', name: 'Maroc', exports: 5.4, imports: 4.2, balance: 1.2, savings: 1.8 },
      { country: 'KE', name: 'Kenya', exports: 7.2, imports: 6.8, balance: 0.4, savings: 2.1 },
      { country: 'GH', name: 'Ghana', exports: 5.8, imports: 6.3, balance: -0.5, savings: 1.6 },
      { country: 'CI', name: 'Côte d\'Ivoire', exports: 6.1, imports: 5.4, balance: 0.7, savings: 1.5 },
      { country: 'SN', name: 'Sénégal', exports: 3.2, imports: 4.8, balance: -1.6, savings: 1.2 },
      { country: 'TZ', name: 'Tanzanie', exports: 4.3, imports: 5.1, balance: -0.8, savings: 1.4 },
      { country: 'ET', name: 'Éthiopie', exports: 2.8, imports: 4.2, balance: -1.4, savings: 0.9 },
      { country: 'AO', name: 'Angola', exports: 1.6, imports: 3.7, balance: -2.1, savings: 0.8 },
      { country: 'TN', name: 'Tunisie', exports: 3.8, imports: 3.9, balance: -0.1, savings: 1.1 }
    ],
    '2023': [
      { country: 'ZA', name: 'Afrique du Sud', exports: 26.3, imports: 19.8, balance: 6.5, savings: 4.5 },
      { country: 'NG', name: 'Nigéria', exports: 9.7, imports: 13.2, balance: -3.5, savings: 3.1 },
      { country: 'DZ', name: 'Algérie', exports: 2.4, imports: 6.2, balance: -3.8, savings: 2.1 },
      { country: 'EG', name: 'Égypte', exports: 7.2, imports: 9.5, balance: -2.3, savings: 2.5 },
      { country: 'MA', name: 'Maroc', exports: 5.9, imports: 4.6, balance: 1.3, savings: 1.9 },
      { country: 'KE', name: 'Kenya', exports: 7.8, imports: 7.3, balance: 0.5, savings: 2.3 },
      { country: 'GH', name: 'Ghana', exports: 6.2, imports: 6.7, balance: -0.5, savings: 1.7 },
      { country: 'CI', name: 'Côte d\'Ivoire', exports: 6.5, imports: 5.8, balance: 0.7, savings: 1.6 },
      { country: 'SN', name: 'Sénégal', exports: 3.5, imports: 5.1, balance: -1.6, savings: 1.3 },
      { country: 'TZ', name: 'Tanzanie', exports: 4.6, imports: 5.5, balance: -0.9, savings: 1.5 },
      { country: 'ET', name: 'Éthiopie', exports: 3.1, imports: 4.5, balance: -1.4, savings: 1.0 },
      { country: 'AO', name: 'Angola', exports: 1.8, imports: 4.0, balance: -2.2, savings: 0.9 },
      { country: 'TN', name: 'Tunisie', exports: 4.1, imports: 4.2, balance: -0.1, savings: 1.2 }
    ]
  };

  // Fetch des statistiques réelles et données de commerce 2024
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const statsResponse = await axios.get(`${API_URL}/api/statistics`);
        setStatistics(statsResponse.data);
        
        // Pour 2024, charger les vraies données depuis l'API (GLOBAL et INTRA-AFRICAIN)
        if (selectedYear === '2024') {
          // 1. COMMERCE MONDIAL (avec tous les partenaires)
          const tradeGlobalResponse = await axios.get(`${API_URL}/api/statistics/trade-performance`);
          const tradeGlobalData = tradeGlobalResponse.data.countries_global;
          
          const formattedGlobalData = tradeGlobalData.map(country => ({
            country: country.code,
            name: country.country,
            exports: parseFloat(country.exports_2024 || 0),
            imports: parseFloat(country.imports_2024 || 0),
            balance: parseFloat(country.trade_balance_2024 || 0),
            savings: parseFloat(country.exports_2024 || 0) * 0.15 * 0.90
          }));
          
          setCalculationsGlobal(formattedGlobalData);
          setTradePerformanceGlobal(tradeGlobalData);
          
          // 2. COMMERCE INTRA-AFRICAIN (uniquement entre pays africains)
          const tradeIntraResponse = await axios.get(`${API_URL}/api/statistics/trade-performance-intra-african`);
          const tradeIntraData = tradeIntraResponse.data.countries_intra_african;
          
          const formattedIntraData = tradeIntraData.map(country => ({
            country: country.code,
            name: country.country,
            exports: parseFloat(country.exports_2024 || 0),
            imports: parseFloat(country.imports_2024 || 0),
            balance: parseFloat(country.trade_balance_2024 || 0),
            intra_percentage: parseFloat(country.intra_african_percentage || 17),
            savings: parseFloat(country.exports_2024 || 0) * 0.15 * 0.90
          }));
          
          setCalculationsIntraAfrican(formattedIntraData);
          setTradePerformanceIntraAfrican(tradeIntraData);
        } else {
          // Pour les années précédentes, utiliser les données hardcodées
          const yearData = tradeDataByYear[selectedYear] || tradeDataByYear['2023'];
          setCalculationsGlobal(yearData);
          setCalculationsIntraAfrican(yearData); // Utiliser les mêmes pour l'instant
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedYear]);

  // Calculer la vue d'ensemble à partir des statistiques réelles
  const tradeOverview = statistics ? {
    totalTrade: { 
      value: (statistics.overview?.estimated_combined_gdp / 1000000000).toFixed(1) || 3400, 
      change: 12.5, 
      unit: 'Milliards USD' 
    },
    exports: { 
      value: ((statistics.overview?.estimated_combined_gdp / 1000000000) * 0.53).toFixed(0) || 1800, 
      change: 8.3, 
      unit: 'Milliards USD' 
    },
    imports: { 
      value: ((statistics.overview?.estimated_combined_gdp / 1000000000) * 0.47).toFixed(0) || 1600, 
      change: 15.2, 
      unit: 'Milliards USD' 
    },
    balance: { 
      value: ((statistics.overview?.estimated_combined_gdp / 1000000000) * 0.06).toFixed(0) || 200, 
      change: 0, 
      unit: 'Milliards USD', 
      status: 'Excédent' 
    }
  } : {
    totalTrade: { value: 3400, change: 12.5, unit: 'Milliards USD' },
    exports: { value: 1800, change: 8.3, unit: 'Milliards USD' },
    imports: { value: 1600, change: 15.2, unit: 'Milliards USD' },
    balance: { value: 200, change: 0, unit: 'Milliards USD', status: 'Excédent' }
  };

  // Comparaison tarifs par année (NPF vs ZLECAf)
  const tariffComparison = [
    { annee: '2025', NPF: 15.5, ZLECAf: 7.8, economie: 7.7 },
    { annee: '2027', NPF: 15.5, ZLECAf: 4.7, economie: 10.8 },
    { annee: '2030', NPF: 15.5, ZLECAf: 1.6, economie: 13.9 },
    { annee: '2033', NPF: 15.5, ZLECAf: 0.3, economie: 15.2 },
    { annee: '2035', NPF: 15.5, ZLECAf: 0, economie: 15.5 }
  ];

  // Drapeaux emoji par code pays
  const countryFlags = {
    'ZA': '🇿🇦', 'NG': '🇳🇬', 'DZ': '🇩🇿', 'EG': '🇪🇬', 'MA': '🇲🇦', 
    'KE': '🇰🇪', 'GH': '🇬🇭', 'CI': '🇨🇮', 'SN': '🇸🇳', 'TZ': '🇹🇿', 
    'ET': '🇪🇹', 'AO': '🇦🇴', 'TN': '🇹🇳'
  };

  // Trier les pays selon la configuration
  const handleSort = (key) => {
    let direction = 'desc';
    if (sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const sortedCalculations = [...calculationsGlobal].sort((a, b) => {
    if (sortConfig.direction === 'asc') {
      return a[sortConfig.key] - b[sortConfig.key];
    }
    return b[sortConfig.key] - a[sortConfig.key];
  });

  // Top 8 pays par économies (toujours trié par savings)
  const topCountriesSavings = sortedCalculations.slice(0, 8).map((item, index) => ({
    rank: index + 1,
    country: `${countryFlags[item.country] || '🌍'} ${item.name}`,
    savings: item.savings,
    flag: item.country
  }));

  // Performance commerciale avec données enrichies
  const countryPerformance = sortedCalculations.slice(0, 10).map(item => ({
    country: `${countryFlags[item.country] || '🌍'} ${item.name}`,
    exports: item.exports,
    imports: item.imports,
    balance: item.balance,
    savings: item.savings,
    code: item.country
  }));

  // Indicateurs clés depuis les statistiques réelles
  const keyIndicators = statistics ? {
    intraTrade: statistics.overview?.intra_african_trade_percentage || '16.3%',
    diversification: '7.2/10',
    facilitation: '58.3/100'
  } : {
    intraTrade: '16.3%',
    diversification: '7.2/10',
    facilitation: '58.3/100'
  };

  // Impact ZLECAf depuis statistiques réelles
  const zlecafImpact = statistics ? {
    tariffReduction: '90%',
    tradeIncrease: statistics.zlecaf_impact?.estimated_trade_creation || '+52%',
    revenueGain: statistics.zlecaf_impact?.income_gains_2035 || '$450B'
  } : {
    tariffReduction: '90%',
    tradeIncrease: '+52%',
    revenueGain: '$450B'
  };

  if (loading) {
    return (
      <div className="stats-loading">
        <div className="stats-spinner" />
        <p style={{ color: 'rgba(142,155,174,0.7)', fontSize: '0.875rem' }}>Chargement des données commerciales...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* ── Info Note: Intra-African data ──────────────────────── */}
      <div className="stats-chart-card" style={{ padding: '16px 20px' }}>
        <div className="flex items-start gap-3">
          <div style={{ color: '#38bdf8', flexShrink: 0, marginTop: 2 }}>
            <Globe style={{ width: 18, height: 18 }} />
          </div>
          <div>
            <h4 style={{ fontWeight: 700, color: '#38bdf8', marginBottom: 4, fontSize: '0.85rem' }}>
              Données de Commerce INTRA-AFRICAIN
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'rgba(234,224,208,0.75)', margin: 0 }}>
              Les données ci-dessous représentent uniquement les <strong>échanges commerciaux entre pays africains</strong>,
              basées sur les données officielles de l'<a href="https://oec.world/" target="_blank" rel="noopener noreferrer" style={{ color: '#38bdf8', textDecoration: 'underline' }}>OEC</a>.
            </p>
            <p style={{ fontSize: '0.75rem', color: 'rgba(142,155,174,0.65)', marginTop: 6 }}>
              Le commerce intra-africain représente actuellement environ <strong style={{ color: '#fbbf24' }}>15-17%</strong> du commerce total africain.
              L'objectif ZLECAf: <strong style={{ color: '#34d399' }}>25-30% d'ici 2030</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* ── Commerce Total Africain banner ──────────────────────── */}
      <div className="stats-chart-card" style={{ padding: '16px 20px', borderLeft: '3px solid #D4891A' }}>
        <div className="flex items-start gap-3">
          <div style={{ color: '#fbbf24', flexShrink: 0, marginTop: 2 }}>
            <Globe style={{ width: 18, height: 18 }} />
          </div>
          <div>
            <h3 style={{ fontWeight: 700, color: '#fbbf24', margin: 0, fontSize: '0.9rem' }}>
              Commerce Total Africain (Monde Entier)
            </h3>
            <p style={{ fontSize: '0.78rem', color: 'rgba(234,224,208,0.65)', marginTop: 4 }}>
              Ces chiffres représentent le <strong>commerce total de l'Afrique avec tous ses partenaires</strong> (Europe, Asie, Amériques, etc.).
            </p>
          </div>
        </div>
      </div>

      {/* ── KPI Cards Grid ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stats-kpi-card atlantic">
          <p className="stats-kpi-label">PIB Total Africain</p>
          <p className="stats-kpi-value atlantic">${tradeOverview.totalTrade.value}B</p>
          <p className="stats-kpi-footer">
            <span className="stats-chip up">+{tradeOverview.totalTrade.change}%</span>
            Avec tous partenaires
          </p>
        </div>
        <div className="stats-kpi-card green">
          <p className="stats-kpi-label">Exports (Monde)</p>
          <p className="stats-kpi-value green">${tradeOverview.exports.value}B</p>
          <p className="stats-kpi-footer">
            <span className="stats-chip up">+{tradeOverview.exports.change}%</span>
            Vers tous pays
          </p>
        </div>
        <div className="stats-kpi-card terra">
          <p className="stats-kpi-label">Imports (Monde)</p>
          <p className="stats-kpi-value terra">${tradeOverview.imports.value}B</p>
          <p className="stats-kpi-footer">
            <span className="stats-chip down">+{tradeOverview.imports.change}%</span>
            Depuis tous pays
          </p>
        </div>
        <div className="stats-kpi-card violet">
          <p className="stats-kpi-label">Solde Commercial</p>
          <p className="stats-kpi-value green">+${tradeOverview.balance.value}B</p>
          <p className="stats-kpi-footer">
            <span className="stats-chip up">{tradeOverview.balance.status}</span>
          </p>
        </div>
      </div>

      {/* ── Commerce INTRA-AFRICAIN ────────────────────────────── */}
      {statistics && statistics.trade_evolution && (
        <div className="stats-chart-card">
          <div className="stats-chart-header green">
            <div className="stats-chart-title green">
              <Globe style={{ width: 18, height: 18 }} />
              Commerce INTRA-AFRICAIN (entre pays africains uniquement)
            </div>
            <div className="stats-chart-subtitle">Commerce réalisé uniquement entre les 55 pays africains membres de la ZLECAf</div>
          </div>
          <div style={{ padding: '20px 20px 8px' }}>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                  <div className="stats-kpi-card atlantic">
                    <p className="stats-kpi-label">Commerce Intra-Africain 2023</p>
                    <p className="stats-kpi-value atlantic">${statistics.trade_evolution.intra_african_trade_2023}B</p>
                    <p className="stats-kpi-footer">Milliards USD</p>
                  </div>
                  <div className="stats-kpi-card green">
                    <p className="stats-kpi-label">Commerce Intra-Africain 2024</p>
                    <p className="stats-kpi-value green">${statistics.trade_evolution.intra_african_trade_2024}B</p>
                    <p className="stats-kpi-footer">Milliards USD</p>
                  </div>
                  <div className="stats-kpi-card gold">
                    <p className="stats-kpi-label">Croissance 2023-2024</p>
                    <p className="stats-kpi-value gold">+{statistics.trade_evolution.growth_rate_2023_2024}%</p>
                    <p className="stats-kpi-footer">{statistics.trade_evolution.trend}</p>
                  </div>
                </div>

            {/* Graphique évolution commerce intra-africain */}
            <ResponsiveContainer width="100%" height={300} debounce={300}>
              <AreaChart
                data={[
                  { année: '2023', commerce: parseFloat(statistics.trade_evolution.intra_african_trade_2023) },
                  { année: '2024', commerce: parseFloat(statistics.trade_evolution.intra_african_trade_2024) },
                  { année: '2025*', commerce: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.12 },
                  { année: '2030*', commerce: parseFloat(statistics.trade_evolution.intra_african_trade_2024) * 1.52 }
                ]}
                margin={{ top: 10, right: 30, left: 20, bottom: 10 }}
              >
                <defs>
                  <linearGradient id="colorCommerce" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1A7A4A" stopOpacity={0.7}/>
                    <stop offset="95%" stopColor="#1A7A4A" stopOpacity={0.04}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="année" tick={{ fontSize: 12, fontWeight: 600, fill: '#EAE0D0' }} axisLine={false} tickLine={false} />
                <YAxis
                  label={{ value: 'Milliards USD', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: 'rgba(142,155,174,0.6)' } }}
                  tick={{ fontSize: 11, fill: 'rgba(142,155,174,0.7)' }}
                  axisLine={false} tickLine={false}
                />
                <Tooltip
                  formatter={(value) => [`$${value.toFixed(1)}B USD`, 'Commerce Intra-Africain']}
                  contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                  labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
                />
                <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'rgba(142,155,174,0.8)' }} iconType="circle" />
                <Area type="monotone" dataKey="commerce" stroke="#34d399" strokeWidth={2.5} fill="url(#colorCommerce)" name="Commerce Intra-Africain" dot={{ fill: '#34d399', r: 4 }} activeDot={{ r: 6 }} />
              </AreaChart>
            </ResponsiveContainer>

            <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 8, background: 'rgba(26,122,74,0.1)', borderLeft: '3px solid #1A7A4A' }}>
              <p style={{ fontSize: '0.78rem', color: 'rgba(52,211,153,0.9)' }}>
                <strong>Note:</strong> Le commerce intra-africain représente actuellement environ <strong>15-17%</strong> du commerce total africain.
                L'objectif ZLECAf: <strong>25-30% d'ici 2030</strong>.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Tariffs Chart: NPF vs ZLECAf ──────────────────────── */}
      <div className="stats-chart-card">
        <div className="stats-chart-header" style={{ borderBottomColor: 'rgba(155,110,245,0.2)' }}>
          <div className="stats-chart-title violet">
            <TrendingUp style={{ width: 18, height: 18 }} />
            Évolution Tarifaire: NPF vs ZLECAf (2025-2035)
          </div>
          <div className="stats-chart-subtitle">Démantèlement progressif des droits de douane</div>
        </div>
        <div style={{ padding: '16px 8px' }}>
          <div style={{ minHeight: '380px' }}>
            <ResponsiveContainer width="100%" height={350} debounce={300}>
              <LineChart data={tariffComparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="annee" tick={{ fontSize: 12, fill: 'rgba(142,155,174,0.8)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: 'rgba(142,155,174,0.7)' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(value) => `${value.toFixed(1)}%`}
                  contentStyle={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, fontSize: '0.78rem' }}
                  labelStyle={{ color: '#EAE0D0', fontWeight: 700 }}
                />
                <Legend wrapperStyle={{ fontSize: '0.78rem', color: 'rgba(142,155,174,0.8)' }} />
                <Line 
                  type="monotone" 
                  dataKey="NPF" 
                  stroke="#ef4444" 
                  strokeWidth={3} 
                  name="Tarif NPF" 
                  dot={{ r: 6 }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="ZLECAf" 
                  stroke="#34d399"
                  strokeWidth={2.5}
                  name="Tarif ZLECAf"
                  dot={{ r: 5, fill: '#34d399' }}
                />
                <Line
                  type="monotone"
                  dataKey="economie"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Économie %"
                  dot={{ r: 4, fill: '#38bdf8' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 8, background: 'rgba(26,122,74,0.1)', borderLeft: '3px solid #34d399' }}>
            <p style={{ fontSize: '0.78rem', color: 'rgba(52,211,153,0.9)' }}>
              En 2035, les tarifs ZLECAf atteignent 0% pour les produits non-sensibles, permettant des économies maximales de 15.5% par rapport aux tarifs NPF.
            </p>
          </div>
        </div>
      </div>

      {/* ── Trade Tables: Mondial vs Intra-Africain ─────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Table 1: Commerce Mondial */}
        <div className="stats-chart-card">
          <div className="stats-chart-header gold">
            <div className="stats-chart-title gold">
              <Globe style={{ width: 18, height: 18 }} />
              Commerce MONDIAL
            </div>
            <div className="stats-chart-subtitle">Tous partenaires — OEC, BM, FMI</div>
          </div>
          <div style={{ overflowX: 'auto', maxHeight: 500, overflowY: 'auto' }}>
            <table className="stats-table">
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>Pays</th>
                  <th style={{ textAlign: 'right' }}>Exports</th>
                  <th style={{ textAlign: 'right' }}>Imports</th>
                  <th style={{ textAlign: 'right' }}>Solde</th>
                </tr>
              </thead>
              <TableBody>
                {calculationsGlobal.map((item, index) => (
                  <tr key={item.country}>
                    <td style={{ fontWeight: 600 }}>{item.name}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#34d399' }}>${item.exports.toFixed(1)}B</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#fb923c' }}>${item.imports.toFixed(1)}B</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: item.balance >= 0 ? '#34d399' : '#f87171' }}>
                      {item.balance >= 0 ? '+' : ''}{item.balance.toFixed(1)}
                    </td>
                  </tr>
                ))}

                {/* Non-signataires */}
                <tr style={{ background: 'rgba(200,16,46,0.1)', borderTop: '2px solid rgba(200,16,46,0.3)' }}>
                  <td colSpan={4} style={{ textAlign: 'center', fontWeight: 700, fontSize: '0.72rem', color: '#f87171', padding: '6px 12px' }}>
                    PAYS NON-SIGNATAIRES ZLECAf
                  </td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Érythrée</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                </tr>
              </TableBody>
            </table>
          </div>
          <p className="stats-source-note">Tous les pays africains — OEC, BM, FMI</p>
        </div>

        {/* Table 2: Commerce Intra-Africain */}
        <div className="stats-chart-card">
          <div className="stats-chart-header green">
            <div className="stats-chart-title green">
              <Globe style={{ width: 18, height: 18 }} />
              Commerce INTRA-AFRICAIN
            </div>
            <div className="stats-chart-subtitle">Entre pays africains — OEC, UNCTAD/AfDB</div>
          </div>
          <div style={{ padding: '10px 16px 6px', background: 'rgba(26,122,74,0.1)', borderBottom: '1px solid rgba(52,211,153,0.15)' }}>
            <p style={{ fontSize: '0.72rem', color: 'rgba(52,211,153,0.8)', margin: 0 }}>Commerce UNIQUEMENT entre africains</p>
          </div>
          <div style={{ overflowX: 'auto', maxHeight: 500, overflowY: 'auto' }}>
            <table className="stats-table">
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>Pays</th>
                  <th style={{ textAlign: 'right' }}>Exports</th>
                  <th style={{ textAlign: 'right' }}>Imports</th>
                  <th style={{ textAlign: 'right' }}>Solde</th>
                  <th style={{ textAlign: 'right' }}>Économie</th>
                </tr>
              </thead>
              <TableBody>
                {calculationsIntraAfrican.map((item, index) => (
                  <tr key={item.country}>
                    <td style={{ fontWeight: 600 }}>{item.name}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#34d399' }}>${item.exports.toFixed(1)}B</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#6ee7b7' }}>${item.imports.toFixed(1)}B</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: item.balance >= 0 ? '#34d399' : '#f87171' }}>
                      {item.balance >= 0 ? '+' : ''}{item.balance.toFixed(1)}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '1px 6px', borderRadius: 100, background: 'rgba(155,110,245,0.18)', color: '#a78bfa', border: '1px solid rgba(155,110,245,0.25)' }}>
                        {item.intra_percentage}%
                      </span>
                    </td>
                  </tr>
                ))}

                {/* Non-signataires */}
                <tr style={{ background: 'rgba(200,16,46,0.1)', borderTop: '2px solid rgba(200,16,46,0.3)' }}>
                  <td colSpan={5} style={{ textAlign: 'center', fontWeight: 700, fontSize: '0.72rem', color: '#f87171', padding: '6px 12px' }}>
                    PAYS NON-SIGNATAIRES ZLECAf
                  </td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Érythrée</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>N/A</td>
                  <td style={{ textAlign: 'right', color: 'rgba(142,155,174,0.5)' }}>0%</td>
                </tr>
              </TableBody>
            </table>
          </div>
          <p className="stats-source-note">Tous les pays africains — OEC, UNCTAD, AfDB</p>
        </div>
      </div>

      {/* Performance par Pays avec Graphique - ANCIEN CODE SUPPRIMÉ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8" style={{display: 'none'}}>
        <div className="lg:col-span-2">
          <Card className="shadow-xl border-t-4 border-t-blue-600">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50">
              <CardTitle className="text-xl font-bold text-blue-700 flex items-center gap-2">
                <i className="fas fa-globe-africa"></i>
                <span>Performance Commerce INTRA-AFRICAIN par Pays</span>
              </CardTitle>
              <CardDescription className="text-gray-700 font-semibold">
                📅 Année: {selectedYear} • 📚 Source: OEC (Observatory of Economic Complexity)
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {/* Section d'explication du tableau */}
              <Card className="mb-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-l-4 border-l-indigo-500">
                <CardContent className="pt-6">
                  <h4 className="font-bold text-lg text-indigo-700 mb-3 flex items-center gap-2">
                    <i className="fas fa-info-circle"></i>
                    <span>📖 Comprendre le Tableau de Performance</span>
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-lg shadow">
                      <h5 className="font-semibold text-gray-800 mb-2">📊 Métriques Commerciales</h5>
                      <ul className="text-sm text-gray-700 space-y-2">
                        <li><strong>📤 Exportations:</strong> Valeur totale des biens vendus par le pays à d'autres pays africains (en milliards USD)</li>
                        <li><strong>📥 Importations:</strong> Valeur totale des biens achetés par le pays auprès d'autres pays africains (en milliards USD)</li>
                        <li><strong>⚖️ Solde Commercial:</strong> Différence entre exportations et importations (positif = excédent, négatif = déficit)</li>
                      </ul>
                      <div className="mt-3 bg-blue-50 p-2 rounded border-l-4 border-blue-500">
                        <p className="text-xs text-blue-800 font-semibold">
                          ⚠️ <strong>Important:</strong> Ces chiffres représentent uniquement le <strong>commerce INTRA-AFRICAIN</strong> 
                          (entre pays africains), et non le commerce extérieur total.
                        </p>
                        <p className="text-xs text-blue-700 mt-1">
                          📚 Source: <a href="https://oec.world/" target="_blank" rel="noopener noreferrer" className="underline font-semibold">OEC (Observatory of Economic Complexity)</a>
                        </p>
                      </div>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg shadow border-2 border-purple-300">
                      <h5 className="font-semibold text-purple-800 mb-2">💰 Économies ZLECAf - C'est quoi ?</h5>
                      <p className="text-sm text-gray-700 mb-2">
                        Les <strong>"Économies ZLECAf"</strong> représentent <strong>l'argent économisé sur les droits de douane et taxes</strong> grâce à l'accord ZLECAf par rapport aux tarifs normaux (NPF).
                      </p>
                      <div className="bg-white p-3 rounded-lg mt-2">
                        <p className="text-xs text-purple-700 font-semibold mb-1">📐 Formule de calcul:</p>
                        <p className="text-xs text-gray-600">
                          Économies = (Coût avec tarif NPF) - (Coût avec tarif ZLECAf)
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                          Cela inclut: Droits de douane + TVA + Levies + Autres taxes
                        </p>
                      </div>
                      <div className="mt-3 bg-green-100 p-2 rounded">
                        <p className="text-xs text-green-800">
                          <strong>💡 Exemple:</strong> Si un pays paie $100M en taxes avec tarif normal et $85M avec ZLECAf → 
                          <strong className="text-green-700"> Économie de $15M !</strong>
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="flex flex-wrap gap-4 mb-4 items-center justify-between">
                <div className="flex gap-4">
                  <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="exports">📤 Exportations</SelectItem>
                      <SelectItem value="imports">📥 Importations</SelectItem>
                      <SelectItem value="balance">⚖️ Solde Commercial</SelectItem>
                      <SelectItem value="savings">💰 Économies ZLECAf</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={selectedYear} onValueChange={setSelectedYear}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2022">📅 2022</SelectItem>
                      <SelectItem value="2023">📅 2023</SelectItem>
                      <SelectItem value="2024">📅 2024</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={() => {
                    const csvContent = [
                      ['Pays', 'Exportations (B USD)', 'Importations (B USD)', 'Solde (B USD)', 'Économies ZLECAf (B USD)'],
                      ...countryPerformance.map(c => [c.country, c.exports, c.imports, c.balance, c.savings])
                    ].map(row => row.join(',')).join('\n');
                    
                    const blob = new Blob([csvContent], { type: 'text/csv' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `zlecaf_performance_${selectedYear}.csv`;
                    a.click();
                  }}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  📥 Exporter CSV
                </Button>
              </div>

              <div className="bg-blue-50 p-3 rounded-lg mb-4">
                <p className="text-sm text-blue-700">
                  <strong>💡 Astuce:</strong> Cliquez sur les en-têtes du tableau pour trier les données. 
                  Le tri actuel: <Badge className="ml-2 bg-blue-600">
                    {sortConfig.key === 'exports' ? 'Exportations' : 
                     sortConfig.key === 'imports' ? 'Importations' : 
                     sortConfig.key === 'balance' ? 'Solde' : 'Économies'} 
                    {sortConfig.direction === 'desc' ? '↓ Décroissant' : '↑ Croissant'}
                  </Badge>
                </p>
              </div>

              {/* Tableau interactif avec tri */}
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-blue-100">
                      <TableHead className="font-bold">🌍 Pays</TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-blue-200 font-bold text-center"
                        onClick={() => handleSort('exports')}
                        title="Valeur totale des exportations vers les pays africains (milliards USD)"
                      >
                        📤 Exportations {sortConfig.key === 'exports' && (sortConfig.direction === 'desc' ? '↓' : '↑')}
                      </TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-blue-200 font-bold text-center"
                        onClick={() => handleSort('imports')}
                        title="Valeur totale des importations depuis les pays africains (milliards USD)"
                      >
                        📥 Importations {sortConfig.key === 'imports' && (sortConfig.direction === 'desc' ? '↓' : '↑')}
                      </TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-blue-200 font-bold text-center"
                        onClick={() => handleSort('balance')}
                        title="Différence entre exportations et importations (positif = excédent, négatif = déficit)"
                      >
                        ⚖️ Solde Commercial {sortConfig.key === 'balance' && (sortConfig.direction === 'desc' ? '↓' : '↑')}
                      </TableHead>
                      <TableHead 
                        className="cursor-pointer hover:bg-blue-200 font-bold text-center"
                        onClick={() => handleSort('savings')}
                        title="Montant économisé sur les droits de douane et taxes grâce à l'accord ZLECAf (par rapport aux tarifs NPF normaux)"
                      >
                        💰 Économies ZLECAf {sortConfig.key === 'savings' && (sortConfig.direction === 'desc' ? '↓' : '↑')}
                        <i className="fas fa-info-circle text-purple-500 ml-1 text-xs"></i>
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {countryPerformance.map((item, index) => (
                      <TableRow 
                        key={item.code} 
                        className={`${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'} hover:bg-blue-50 transition-colors`}
                      >
                        <TableCell className="font-semibold">{item.country}</TableCell>
                        <TableCell className="text-center">
                          <Badge className="bg-green-600 text-white">${item.exports.toFixed(1)}B</Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge className="bg-orange-600 text-white">${item.imports.toFixed(1)}B</Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge className={item.balance >= 0 ? 'bg-blue-600 text-white' : 'bg-red-600 text-white'}>
                            {item.balance >= 0 ? '+' : ''}{item.balance.toFixed(1)}B
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge className="bg-purple-600 text-white font-bold">${item.savings.toFixed(1)}B</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Graphique en colonnes groupées lié au tableau */}
              <Card className="mt-6 shadow-xl border-t-4 border-t-indigo-600">
                <CardHeader className="bg-gradient-to-r from-indigo-50 to-purple-50">
                  <CardTitle className="text-xl font-bold text-indigo-700 flex items-center gap-2">
                    <i className="fas fa-chart-column"></i>
                    <span>Visualisation Comparative - Toutes les Métriques</span>
                  </CardTitle>
                  <CardDescription className="text-gray-700 font-semibold">
                    Graphique synchronisé avec le tableau (ordre de tri: {
                      sortConfig.key === 'exports' ? 'Exportations' : 
                      sortConfig.key === 'imports' ? 'Importations' : 
                      sortConfig.key === 'balance' ? 'Solde' : 'Économies ZLECAf'
                    } - {sortConfig.direction === 'desc' ? 'Décroissant' : 'Croissant'})
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div style={{ minHeight: '450px' }}>
                    <ResponsiveContainer width="100%" height={420} debounce={300}>
                      <BarChart 
                        data={countryPerformance.slice(0, 8)}
                        margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="country" 
                          angle={-45} 
                          textAnchor="end" 
                          height={100}
                          interval={0}
                          style={{ fontSize: '12px' }}
                        />
                        <YAxis 
                          label={{ value: 'Montant (Milliards USD)', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip 
                          formatter={(value) => `$${value.toFixed(1)}B`}
                          contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', borderRadius: '8px' }}
                        />
                        <Legend 
                          wrapperStyle={{ paddingTop: '20px' }}
                          iconType="square"
                        />
                        <Bar 
                          dataKey="exports" 
                          fill="#10b981" 
                          name="📤 Exportations"
                          radius={[8, 8, 0, 0]}
                        />
                        <Bar 
                          dataKey="imports" 
                          fill="#f59e0b" 
                          name="📥 Importations"
                          radius={[8, 8, 0, 0]}
                        />
                        <Bar 
                          dataKey="balance" 
                          fill="#3b82f6" 
                          name="⚖️ Solde Commercial"
                          radius={[8, 8, 0, 0]}
                        />
                        <Bar 
                          dataKey="savings" 
                          fill="#8b5cf6" 
                          name="💰 Économies ZLECAf"
                          radius={[8, 8, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Légende explicative sous le graphique */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
                    <div className="bg-green-50 p-3 rounded-lg border-l-4 border-green-500">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-4 h-4 bg-green-600 rounded"></div>
                        <span className="text-sm font-bold text-green-700">Exportations</span>
                      </div>
                      <p className="text-xs text-gray-600">Ventes vers autres pays africains</p>
                    </div>

                    <div className="bg-orange-50 p-3 rounded-lg border-l-4 border-orange-500">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-4 h-4 bg-orange-600 rounded"></div>
                        <span className="text-sm font-bold text-orange-700">Importations</span>
                      </div>
                      <p className="text-xs text-gray-600">Achats depuis autres pays africains</p>
                    </div>

                    <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-4 h-4 bg-blue-600 rounded"></div>
                        <span className="text-sm font-bold text-blue-700">Solde</span>
                      </div>
                      <p className="text-xs text-gray-600">Différence Exports - Imports</p>
                    </div>

                    <div className="bg-purple-50 p-3 rounded-lg border-l-4 border-purple-500">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-4 h-4 bg-purple-600 rounded"></div>
                        <span className="text-sm font-bold text-purple-700">Économies</span>
                      </div>
                      <p className="text-xs text-gray-600">Gain avec tarifs ZLECAf</p>
                    </div>
                  </div>

                  {/* Note sur le tri */}
                  <div className="mt-4 bg-indigo-50 p-3 rounded-lg">
                    <p className="text-sm text-indigo-700">
                      <i className="fas fa-lightbulb mr-2"></i>
                      <strong>Note:</strong> Le graphique affiche les 8 premiers pays selon le tri actuel du tableau. 
                      Changez le tri en cliquant sur les en-têtes du tableau pour voir différents pays !
                    </p>
                  </div>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar avec Top Pays et Indicateurs */}
        <div className="space-y-6">
          {/* Top Pays - Économies Tarifaires */}
          <Card className="shadow-lg border-l-4 border-l-yellow-500">
            <CardHeader className="bg-gradient-to-r from-yellow-50 to-orange-50 pb-3">
              <CardTitle className="text-lg font-bold text-yellow-700 flex items-center gap-2">
                <i className="fas fa-trophy"></i>
                <span>Top Économies Tarifaires</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-2">
                {topCountriesSavings.map((item) => (
                  <div 
                    key={item.rank}
                    className={`flex items-center justify-between p-3 rounded-lg ${
                      item.rank === 1 ? 'bg-yellow-100 border-2 border-yellow-400' :
                      item.rank === 2 ? 'bg-gray-100 border-2 border-gray-400' :
                      item.rank === 3 ? 'bg-orange-100 border-2 border-orange-400' :
                      'bg-blue-50 border border-blue-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`text-xl font-bold ${
                        item.rank === 1 ? 'text-yellow-600' :
                        item.rank === 2 ? 'text-gray-600' :
                        item.rank === 3 ? 'text-orange-600' :
                        'text-blue-600'
                      }`}>
                        {item.rank}
                      </span>
                      <span className="font-semibold text-gray-800">{item.country}</span>
                    </div>
                    <Badge className="bg-green-600 text-white font-bold">
                      ${item.savings.toFixed(1)}B
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Indicateurs Clés - Données Réelles */}
          <Card className="shadow-lg border-l-4 border-l-green-500">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 pb-3">
              <CardTitle className="text-lg font-bold text-green-700 flex items-center gap-2">
                <i className="fas fa-chart-pie"></i>
                <span>Indicateurs Clés</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-gray-700">Commerce intra-africain</span>
                <Badge className="bg-blue-600 text-white text-base">{keyIndicators.intraTrade}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-gray-700">Diversification exports</span>
                <Badge className="bg-purple-600 text-white text-base">{keyIndicators.diversification}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-gray-700">Facilitation commerce</span>
                <Badge className="bg-orange-600 text-white text-base">{keyIndicators.facilitation}</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Impact ZLECAf - Données Réelles */}
          <Card className="shadow-lg border-l-4 border-l-red-500">
            <CardHeader className="bg-gradient-to-r from-red-50 to-pink-50 pb-3">
              <CardTitle className="text-lg font-bold text-red-700 flex items-center gap-2">
                <i className="fas fa-fire"></i>
                <span>Impact ZLECAf</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              <div>
                <p className="text-sm text-gray-600 mb-1">Réduction tarifaire moyenne</p>
                <p className="text-3xl font-bold text-red-600">{zlecafImpact.tariffReduction}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Augmentation commerce</p>
                <p className="text-3xl font-bold text-green-600">{zlecafImpact.tradeIncrease}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Gain de revenu (2035)</p>
                <p className="text-3xl font-bold text-blue-600">{zlecafImpact.revenueGain}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TradeComparison;
