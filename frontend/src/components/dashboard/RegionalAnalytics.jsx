import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { apiV2 } from '../../services/api-v2';

const BLOCS = [
  { id: 'ECOWAS', label: 'ECOWAS', color: 'from-green-600 to-emerald-700', emoji: '🌿' },
  { id: 'SADC', label: 'SADC', color: 'from-blue-600 to-cyan-700', emoji: '🌊' },
  { id: 'EAC', label: 'EAC', color: 'from-orange-500 to-amber-600', emoji: '🦁' },
  { id: 'UMA', label: 'UMA', color: 'from-purple-600 to-indigo-700', emoji: '🌙' },
  { id: 'ECCAS', label: 'ECCAS', color: 'from-red-600 to-rose-700', emoji: '🌴' },
];

function Spinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
    </div>
  );
}

function KPICard({ label, value, sub, color = 'text-blue-700' }) {
  return (
    <div className="bg-gray-50 rounded-xl p-4 text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function BlocPanel({ bloc, data, language }) {
  const kpis = data?.kpis || {};
  const corridors = data?.corridors || [];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KPICard
          label={language === 'fr' ? 'Volume Commercial' : 'Trade Volume'}
          value={kpis.tradeVolume}
          color="text-blue-700"
        />
        <KPICard
          label={language === 'fr' ? 'Croissance' : 'Growth'}
          value={kpis.growth}
          color="text-green-700"
        />
        <KPICard
          label={language === 'fr' ? 'Pays Membres' : 'Member States'}
          value={kpis.memberCount}
          color="text-indigo-700"
        />
        <KPICard
          label={language === 'fr' ? 'Commerce Intra' : 'Intra-Trade'}
          value={kpis.intraTrade}
          color="text-orange-600"
        />
      </div>

      {corridors.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            {language === 'fr' ? 'Corridors Commerciaux Clés' : 'Key Trade Corridors'}
          </h4>
          <div className="space-y-2">
            {corridors.map((c, i) => (
              <div key={i} className="flex items-center justify-between bg-white border rounded-lg px-3 py-2 text-sm">
                <span className="text-gray-700 font-medium">{c.name || c.route}</span>
                <Badge variant="outline" className="text-xs">{c.volume || c.value}</Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {!kpis.tradeVolume && corridors.length === 0 && (
        <p className="text-center text-gray-400 py-8 text-sm">
          {language === 'fr' ? 'Données non disponibles' : 'Data not available'}
        </p>
      )}
    </div>
  );
}

export default function RegionalAnalytics({ language = 'fr' }) {
  const [activeBloc, setActiveBloc] = useState('ECOWAS');
  const [analytics, setAnalytics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    apiV2.getDashboardAnalytics()
      .then((data) => {
        if (!cancelled) {
          setAnalytics(data?.regional || data || {});
        }
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const currentBloc = BLOCS.find((b) => b.id === activeBloc);

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-slate-700 via-slate-800 to-slate-900 text-white shadow-xl">
        <CardHeader>
          <CardTitle className="text-2xl font-bold flex items-center gap-3">
            🌍 {language === 'fr' ? 'Analytique Régionale' : 'Regional Analytics'}
          </CardTitle>
          <CardDescription className="text-slate-300">
            {language === 'fr'
              ? 'Performance des blocs économiques régionaux africains'
              : 'African regional economic bloc performance metrics'}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Bloc Tabs */}
      <div className="flex gap-2 flex-wrap">
        {BLOCS.map((bloc) => (
          <button
            key={bloc.id}
            onClick={() => setActiveBloc(bloc.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border transition-all ${
              activeBloc === bloc.id
                ? 'bg-blue-700 text-white border-blue-700 shadow-md'
                : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400 hover:text-blue-700'
            }`}
          >
            <span>{bloc.emoji}</span>
            {bloc.label}
          </button>
        ))}
      </div>

      {/* Content Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <span>{currentBloc?.emoji}</span>
            <span>{currentBloc?.label}</span>
            {!loading && !error && (
              <Badge className="ml-2 bg-green-100 text-green-700 border-0 text-xs">
                {language === 'fr' ? 'En direct' : 'Live'}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <Spinner />}
          {error && !loading && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
              {language === 'fr'
                ? 'Impossible de charger les données analytiques.'
                : 'Failed to load analytics data.'}
            </div>
          )}
          {!loading && !error && (
            <BlocPanel
              bloc={activeBloc}
              data={analytics[activeBloc] || analytics[activeBloc?.toLowerCase()]}
              language={language}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
