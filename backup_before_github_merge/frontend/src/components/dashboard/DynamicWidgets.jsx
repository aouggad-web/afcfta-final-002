import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  TrendingUp, TrendingDown, Ship, Plane, Factory, Wheat,
  AlertTriangle, CheckCircle, Clock, RefreshCw, Loader2,
  Globe, DollarSign, Users, BarChart3, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar,
  PieChart, Pie, Cell, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// ============================================================
// WIDGET: Live Trade Statistics (données temps réel)
// ============================================================
export function LiveTradeWidget({ language }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/statistics`);
      setData(res.data);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching trade data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) {
    return <WidgetLoader />;
  }

  const evolution = data?.trade_evolution || {};
  const exporters = data?.top_exporters_2024?.slice(0, 5) || [];

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-xs text-gray-500 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {lastUpdate ? lastUpdate.toLocaleTimeString() : '--'}
        </span>
        <Button variant="ghost" size="sm" onClick={fetchData} className="h-6 w-6 p-0">
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <StatCard
          label={language === 'en' ? 'Intra-African' : 'Intra-Africain'}
          value={`$${evolution.intra_african_trade_2024 || 218.7}B`}
          change="+13.7%"
          positive
        />
        <StatCard
          label={language === 'en' ? 'Total Exports' : 'Exports Totaux'}
          value={`$${evolution.total_exports_2024 || 553.7}B`}
          change="+8.2%"
          positive
        />
      </div>

      <div className="space-y-1">
        <p className="text-xs font-medium text-gray-600">
          {language === 'en' ? 'Top Exporters' : 'Top Exportateurs'}
        </p>
        {exporters.map((exp, idx) => (
          <div key={exp.country} className="flex justify-between items-center text-xs">
            <span className="flex items-center gap-1">
              <span className="w-4 text-gray-400">{idx + 1}.</span>
              {exp.name}
            </span>
            <Badge variant="outline" className="text-xs py-0">
              {exp.share_pct}%
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// WIDGET: Live Port Statistics (UNCTAD temps réel)
// ============================================================
export function LivePortsWidget({ language }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/statistics/unctad/ports`);
        setData(res.data);
      } catch (err) {
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <WidgetLoader />;

  const ports = data?.top_ports?.slice(0, 6) || [];
  const chartData = ports.map(p => ({
    name: p.port.length > 8 ? p.port.substring(0, 8) + '...' : p.port,
    teu: p.throughput_teu / 1000000,
    growth: p.growth_rate
  }));

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <div>
          <p className="text-2xl font-bold text-blue-700">
            {(data?.total_african_port_throughput_teu_2023 / 1000000).toFixed(1)}M
          </p>
          <p className="text-xs text-gray-500">TEU Total 2023</p>
        </div>
        <Badge className="bg-green-100 text-green-700">
          +{data?.growth_rate_2022_2023}% YoY
        </Badge>
      </div>

      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={chartData} layout="vertical">
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="name" width={60} tick={{ fontSize: 10 }} />
          <Tooltip 
            formatter={(val) => [`${val.toFixed(1)}M TEU`, 'Throughput']}
            contentStyle={{ fontSize: 11 }}
          />
          <Bar dataKey="teu" fill="#3b82f6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================
// WIDGET: LSCI Connectivity Index (graphique interactif)
// ============================================================
export function LSCIChartWidget({ language }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/statistics/unctad/lsci`);
        setData(res.data || []);
      } catch (err) {
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <WidgetLoader />;

  const chartData = data.slice(0, 8).map(d => ({
    name: language === 'en' ? d.country : d.country_fr,
    lsci: d.lsci_2023,
    rank: d.rank_africa
  }));

  const COLORS = ['#f59e0b', '#6b7280', '#b45309', '#8b5cf6', '#3b82f6', '#10b981', '#ef4444', '#6366f1'];

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-gray-600 text-center">
        LSCI {language === 'en' ? 'Connectivity Index' : 'Indice de Connectivité'}
      </p>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="name" tick={{ fontSize: 8 }} angle={-45} textAnchor="end" height={50} />
          <YAxis tick={{ fontSize: 9 }} domain={[0, 100]} />
          <Tooltip 
            formatter={(val, name, props) => [
              `LSCI: ${val}`,
              `#${props.payload.rank} Africa`
            ]}
            contentStyle={{ fontSize: 11 }}
          />
          <Bar dataKey="lsci" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================
// WIDGET: Country Profile Quick View
// ============================================================
export function CountryProfileWidget({ language, countryCode = 'DZ' }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/country-profile/${countryCode}`);
        setData(res.data);
      } catch (err) {
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [countryCode]);

  if (loading) return <WidgetLoader />;
  if (!data || data.detail) return <div className="text-xs text-gray-500">No data</div>;

  const flag = countryCode === 'DZ' ? '🇩🇿' : countryCode === 'MA' ? '🇲🇦' : 
               countryCode === 'EG' ? '🇪🇬' : countryCode === 'ZA' ? '🇿🇦' : '🌍';

  return (
    <div className="space-y-3">
      <div className="text-center">
        <span className="text-4xl">{flag}</span>
        <p className="font-bold text-lg">{data.country_name}</p>
      </div>

      <div className="grid grid-cols-2 gap-2 text-center text-xs">
        <div className="bg-blue-50 p-2 rounded">
          <DollarSign className="w-4 h-4 mx-auto text-blue-600" />
          <p className="font-bold text-blue-700">${(data.gdp_usd / 1e9).toFixed(0)}B</p>
          <p className="text-gray-500">PIB</p>
        </div>
        <div className="bg-green-50 p-2 rounded">
          <Users className="w-4 h-4 mx-auto text-green-600" />
          <p className="font-bold text-green-700">{data.population_millions}M</p>
          <p className="text-gray-500">Pop.</p>
        </div>
        <div className="bg-purple-50 p-2 rounded">
          <TrendingUp className="w-4 h-4 mx-auto text-purple-600" />
          <p className="font-bold text-purple-700">${data.exports_2024_bln_usd}B</p>
          <p className="text-gray-500">Exports</p>
        </div>
        <div className="bg-amber-50 p-2 rounded">
          <Globe className="w-4 h-4 mx-auto text-amber-600" />
          <p className="font-bold text-amber-700">{data.international_ports || 10}</p>
          <p className="text-gray-500">Ports</p>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// WIDGET: Trade Balance Chart
// ============================================================
export function TradeBalanceWidget({ language }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/statistics`);
        setData(res.data);
      } catch (err) {
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <WidgetLoader />;

  const exporters = data?.top_exporters_2024?.slice(0, 5) || [];
  const importers = data?.top_importers_2024?.slice(0, 5) || [];

  const chartData = exporters.map((exp, idx) => {
    const imp = importers.find(i => i.country === exp.country) || {};
    return {
      name: exp.country,
      exports: (exp.exports_2024 / 1e9).toFixed(0),
      imports: (imp.imports_2024 / 1e9 || 0).toFixed(0)
    };
  });

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-gray-600 text-center">
        {language === 'en' ? 'Exports vs Imports (Top 5)' : 'Exports vs Imports (Top 5)'}
      </p>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="name" tick={{ fontSize: 9 }} />
          <YAxis tick={{ fontSize: 9 }} />
          <Tooltip contentStyle={{ fontSize: 10 }} />
          <Bar dataKey="exports" fill="#10b981" name="Exports" radius={[4, 4, 0, 0]} />
          <Bar dataKey="imports" fill="#ef4444" name="Imports" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <div className="flex justify-center gap-4 text-xs">
        <span className="flex items-center gap-1">
          <div className="w-2 h-2 bg-green-500 rounded" /> Exports
        </span>
        <span className="flex items-center gap-1">
          <div className="w-2 h-2 bg-red-500 rounded" /> Imports
        </span>
      </div>
    </div>
  );
}

// ============================================================
// WIDGET: AfCFTA Progress Tracker
// ============================================================
export function AfCFTAProgressWidget({ language }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/statistics`);
        setData(res.data);
      } catch (err) {
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <WidgetLoader />;

  const metrics = data?.zlecaf_impact_metrics || {};
  const current = data?.trade_evolution?.intra_african_trade_2024 || 218.7;
  const target = data?.trade_evolution?.projected_intra_trade_2030 || 385;
  const progress = ((current / target) * 100).toFixed(0);

  const milestones = [
    { year: 2021, value: 156, done: true },
    { year: 2022, value: 175, done: true },
    { year: 2023, value: 192, done: true },
    { year: 2024, value: 219, done: true },
    { year: 2025, value: 250, done: false },
    { year: 2030, value: 385, done: false }
  ];

  return (
    <div className="space-y-3">
      <div className="text-center">
        <p className="text-3xl font-bold text-green-700">{progress}%</p>
        <p className="text-xs text-gray-500">
          {language === 'en' ? 'Progress to 2030 Target' : 'Progression vers Objectif 2030'}
        </p>
      </div>

      <div className="relative pt-1">
        <div className="flex mb-2 items-center justify-between text-xs">
          <span className="text-green-600 font-semibold">${current}B</span>
          <span className="text-gray-400">${target}B</span>
        </div>
        <div className="overflow-hidden h-3 text-xs flex rounded-full bg-gray-200">
          <div
            style={{ width: `${progress}%` }}
            className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-green-500 to-emerald-600 transition-all duration-500"
          />
        </div>
      </div>

      <ResponsiveContainer width="100%" height={80}>
        <AreaChart data={milestones}>
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#10b981" 
            fill="#d1fae5" 
            strokeWidth={2}
          />
          <XAxis dataKey="year" tick={{ fontSize: 9 }} />
          <Tooltip contentStyle={{ fontSize: 10 }} formatter={(v) => [`$${v}B`, '']} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ============================================================
// WIDGET: Regional Trade Distribution (Pie Chart)
// ============================================================
export function RegionalTradeWidget({ language }) {
  const regions = [
    { name: language === 'en' ? 'North Africa' : 'Afrique du Nord', value: 35, color: '#3b82f6' },
    { name: language === 'en' ? 'West Africa' : 'Afrique de l\'Ouest', value: 28, color: '#10b981' },
    { name: language === 'en' ? 'Southern Africa' : 'Afrique Australe', value: 20, color: '#f59e0b' },
    { name: language === 'en' ? 'East Africa' : 'Afrique de l\'Est', value: 12, color: '#8b5cf6' },
    { name: language === 'en' ? 'Central Africa' : 'Afrique Centrale', value: 5, color: '#ef4444' }
  ];

  return (
    <div className="space-y-2">
      <p className="text-xs font-medium text-gray-600 text-center">
        {language === 'en' ? 'Trade by Region' : 'Commerce par Région'}
      </p>
      <ResponsiveContainer width="100%" height={130}>
        <PieChart>
          <Pie
            data={regions}
            cx="50%"
            cy="50%"
            innerRadius={30}
            outerRadius={50}
            paddingAngle={2}
            dataKey="value"
          >
            {regions.map((entry, idx) => (
              <Cell key={idx} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            formatter={(val) => [`${val}%`, '']}
            contentStyle={{ fontSize: 10 }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="grid grid-cols-2 gap-1 text-xs">
        {regions.slice(0, 4).map(r => (
          <div key={r.name} className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: r.color }} />
            <span className="truncate">{r.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// WIDGET: Alerts & Notifications
// ============================================================
export function AlertsWidget({ language }) {
  const alerts = [
    {
      type: 'success',
      icon: CheckCircle,
      title: language === 'en' ? 'Trade Growth' : 'Croissance Commerce',
      message: language === 'en' ? '+13.7% intra-African trade in 2024' : '+13.7% commerce intra-africain en 2024'
    },
    {
      type: 'warning',
      icon: AlertTriangle,
      title: language === 'en' ? 'Port Congestion' : 'Congestion Portuaire',
      message: language === 'en' ? 'Durban port delays reported' : 'Retards signalés au port de Durban'
    },
    {
      type: 'info',
      icon: TrendingUp,
      title: language === 'en' ? 'New Corridor' : 'Nouveau Corridor',
      message: language === 'en' ? 'Trans-Saharan corridor progress' : 'Avancement corridor Transsaharien'
    }
  ];

  const getAlertStyle = (type) => {
    switch (type) {
      case 'success': return 'bg-green-50 border-green-200 text-green-700';
      case 'warning': return 'bg-amber-50 border-amber-200 text-amber-700';
      case 'info': return 'bg-blue-50 border-blue-200 text-blue-700';
      default: return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  return (
    <div className="space-y-2">
      {alerts.map((alert, idx) => (
        <div 
          key={idx} 
          className={`p-2 rounded-lg border ${getAlertStyle(alert.type)} transition-all hover:scale-[1.02]`}
        >
          <div className="flex items-start gap-2">
            <alert.icon className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-semibold text-xs">{alert.title}</p>
              <p className="text-xs opacity-80">{alert.message}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ============================================================
// Helper Components
// ============================================================
function WidgetLoader() {
  return (
    <div className="flex items-center justify-center h-32">
      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
    </div>
  );
}

function StatCard({ label, value, change, positive }) {
  return (
    <div className="bg-gradient-to-br from-gray-50 to-white p-2 rounded-lg border">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-bold text-gray-800">{value}</p>
      <div className={`flex items-center text-xs ${positive ? 'text-green-600' : 'text-red-600'}`}>
        {positive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
        {change}
      </div>
    </div>
  );
}

export default {
  LiveTradeWidget,
  LivePortsWidget,
  LSCIChartWidget,
  CountryProfileWidget,
  TradeBalanceWidget,
  AfCFTAProgressWidget,
  RegionalTradeWidget,
  AlertsWidget
};
