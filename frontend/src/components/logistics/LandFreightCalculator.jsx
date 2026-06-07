import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Truck, Clock, Package, Info, MapPin, Flag } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const FALLBACK_CARGO = [
  { value: 'general', label_fr: 'Marchandise générale', label_en: 'General cargo' },
  { value: 'container', label_fr: 'Conteneurisé', label_en: 'Containerised' },
  { value: 'perishable', label_fr: 'Périssable (camion frigo)', label_en: 'Perishable (reefer)' },
  { value: 'dangerous', label_fr: 'Marchandise dangereuse', label_en: 'Dangerous goods' },
  { value: 'bulk', label_fr: 'Vrac', label_en: 'Bulk' },
];

const texts = {
  fr: {
    title: 'Calculateur de fret terrestre',
    subtitle: 'Estimation 2024 — modèle calibré Banque Mondiale SSATP / UNECA / AfDB (corridors africains)',
    corridor: 'Corridor', mode: 'Mode', road: 'Route', rail: 'Rail', multimodal: 'Rail + Route (multimodal)',
    weight: 'Tonnage (tonnes)', cargo: 'Nature de la marchandise',
    calculate: 'Calculer le fret', loading: 'Calcul en cours…', result: 'Décomposition des coûts',
    totalCost: 'Coût total estimé', transport: 'Transport', transship: 'Transbordement (rail↔route)',
    border: 'Passages frontières', handling: 'Documentation',
    distance: 'Distance', transit: 'Délai de transit', operators: 'Opérateurs', days: 'jours', km: 'km',
    perTon: '/tonne', perTonKm: '$/tonne-km', borders: 'frontières', osbp: 'OSBP', split: 'Rail / Route',
    source: 'Source', disclaimer: 'Avertissement', selectAll: 'Sélectionnez un corridor et le tonnage.',
  },
  en: {
    title: 'Land Freight Calculator',
    subtitle: '2024 estimate — World Bank SSATP / UNECA / AfDB calibrated model (African corridors)',
    corridor: 'Corridor', mode: 'Mode', road: 'Road', rail: 'Rail', multimodal: 'Rail + Road (multimodal)',
    weight: 'Weight (tonnes)', cargo: 'Commodity type',
    calculate: 'Calculate freight', loading: 'Calculating…', result: 'Cost breakdown',
    totalCost: 'Total estimated cost', transport: 'Transport', transship: 'Transshipment (rail↔road)',
    border: 'Border crossings', handling: 'Documentation',
    distance: 'Distance', transit: 'Transit time', operators: 'Operators', days: 'days', km: 'km',
    perTon: '/tonne', perTonKm: '$/tonne-km', borders: 'borders', osbp: 'OSBP', split: 'Rail / Road',
    source: 'Source', disclaimer: 'Disclaimer', selectAll: 'Select a corridor and tonnage.',
  },
};

function CostBar({ label, value, total, color }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
        <span className="font-semibold">${value.toLocaleString()}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function LandFreightCalculator({ language = 'fr' }) {
  const t = texts[language];

  const [corridors, setCorridors] = useState([]);
  const [cargoTypes, setCargoTypes] = useState(FALLBACK_CARGO);
  const [corridorId, setCorridorId] = useState('');
  const [mode, setMode] = useState('road');
  const [weight, setWeight] = useState('30');
  const [cargoType, setCargoType] = useState('general');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`${API}/logistics/land/fees/corridors`)
      .then(res => { if (res.data?.corridors?.length) setCorridors(res.data.corridors); })
      .catch(() => {});
    axios.get(`${API}/logistics/land/fees/cargo-types`)
      .then(res => { if (res.data?.cargo_types?.length) setCargoTypes(res.data.cargo_types); })
      .catch(() => {});
  }, []);

  const selectedCorridor = useMemo(
    () => corridors.find(c => c.corridor_id === corridorId),
    [corridors, corridorId]
  );
  const availableModes = selectedCorridor?.modes || ['road'];

  const handleCorridorChange = (value) => {
    setCorridorId(value);
    const c = corridors.find(x => x.corridor_id === value);
    if (c && !c.modes.includes(mode)) setMode(c.modes[0]);
    setResult(null);
    setError('');
  };

  const handleCalculate = async () => {
    if (!corridorId || !weight) { setError(t.selectAll); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.get(`${API}/logistics/land/fees/cost`, {
        params: { corridor_id: corridorId, mode, weight_tons: parseFloat(weight), cargo_type: cargoType },
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || t.selectAll);
    } finally {
      setLoading(false);
    }
  };

  const cargoLabel = (c) => (language === 'fr' ? c.label_fr : c.label_en);
  const modeLabel = (m) => (m === 'rail' ? `🚂 ${t.rail}` : m === 'multimodal' ? `🚂🛣️ ${t.multimodal}` : `🛣️ ${t.road}`);

  return (
    <div className="space-y-4" data-testid="land-freight-calculator">
      <Card className="border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
        <CardHeader className="py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-600 rounded-lg flex items-center justify-center">
              <Truck className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-gray-800">{t.title}</CardTitle>
              <CardDescription className="text-xs text-amber-700">{t.subtitle}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.corridor}</label>
              <select
                value={corridorId}
                onChange={e => handleCorridorChange(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                data-testid="land-corridor-select"
              >
                <option value="">— {t.corridor} —</option>
                {corridors.map(c => (
                  <option key={c.corridor_id} value={c.corridor_id}>
                    {c.name} · {c.length_km} {t.km} · {(c.countries || []).join('–')}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.mode}</label>
              <select
                value={mode}
                onChange={e => { setMode(e.target.value); setResult(null); }}
                disabled={!corridorId}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400 disabled:opacity-50"
                data-testid="land-mode-select"
              >
                {availableModes.map(m => (
                  <option key={m} value={m}>{modeLabel(m)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.weight}</label>
              <input
                type="number" min="1" value={weight}
                onChange={e => setWeight(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                data-testid="land-weight-input"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.cargo}</label>
              <select
                value={cargoType}
                onChange={e => setCargoType(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                data-testid="land-cargo-select"
              >
                {cargoTypes.map(c => (<option key={c.value} value={c.value}>{cargoLabel(c)}</option>))}
              </select>
            </div>
          </div>

          <Button
            onClick={handleCalculate}
            disabled={loading || !corridorId || !weight}
            className="bg-amber-600 hover:bg-amber-700 text-white px-6 py-2 rounded-lg text-sm font-medium w-full md:w-auto"
            data-testid="land-calculate-btn"
          >
            <Truck className="w-4 h-4 mr-2" />
            {loading ? t.loading : t.calculate}
          </Button>

          {error && (
            <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 flex items-start gap-2">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />{error}
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <Card className="border border-green-200 bg-gradient-to-r from-green-50 to-emerald-50" data-testid="land-result-card">
          <CardHeader className="py-4 border-b border-green-100">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-gray-800">{t.result}</CardTitle>
              <Badge className="bg-amber-100 text-amber-800 text-xs">{language === 'fr' ? 'Estimé' : 'Modeled'} · {result.data_year}</Badge>
            </div>
            <div className="flex flex-wrap gap-2 mt-1">
              <Badge variant="outline" className="text-xs"><MapPin className="w-3 h-3 mr-1" />{result.length_km.toLocaleString()} {t.km}</Badge>
              <Badge variant="outline" className="text-xs">{modeLabel(result.mode)}</Badge>
              {result.mode === 'multimodal' && (
                <Badge variant="outline" className="text-xs">{t.split}: {result.rail_km.toLocaleString()} / {result.road_km.toLocaleString()} {t.km}</Badge>
              )}
              <Badge variant="outline" className="text-xs"><Clock className="w-3 h-3 mr-1" />{result.transit_days_min}–{result.transit_days_max} {t.days}</Badge>
              <Badge variant="outline" className="text-xs"><Flag className="w-3 h-3 mr-1" />{result.border_crossings} {t.borders} ({result.osbp_crossings} {t.osbp})</Badge>
              <Badge variant="outline" className="text-xs"><Package className="w-3 h-3 mr-1" />{result.cargo_label}</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-5">
            <div className="text-center py-4 bg-white rounded-xl border border-green-200 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">{t.totalCost}</p>
              <p className="text-4xl font-bold text-green-700" data-testid="land-total-cost">${result.total_cost_usd.toLocaleString()}</p>
              <p className="text-xs text-gray-400 mt-1">
                USD · ${result.cost_per_ton_usd.toLocaleString()}{t.perTon} · {result.cost_per_ton_km_usd} {t.perTonKm} · {result.weight_tons} t
              </p>
            </div>

            <div className="space-y-3">
              <CostBar label={t.transport} value={result.transport_cost_usd} total={result.total_cost_usd} color="bg-amber-500" />
              {result.transshipment_cost_usd > 0 && (
                <CostBar label={t.transship} value={result.transshipment_cost_usd} total={result.total_cost_usd} color="bg-blue-400" />
              )}
              <CostBar label={t.border} value={result.border_cost_usd} total={result.total_cost_usd} color="bg-red-400" />
              <CostBar label={t.handling} value={result.handling_usd} total={result.total_cost_usd} color="bg-emerald-400" />
            </div>

            {result.operators?.length > 0 && (
              <div className="p-3 bg-white rounded-lg border border-gray-100">
                <p className="text-xs font-semibold text-gray-500 mb-1">{t.operators}</p>
                <div className="flex flex-wrap gap-1">
                  {result.operators.map(o => (<Badge key={o} variant="secondary" className="text-xs">{o}</Badge>))}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <div className="p-3 bg-white rounded-lg border border-gray-100 text-xs">
                <span className="font-semibold text-gray-600">{t.source}: </span>
                <span className="text-gray-600">{result.source}</span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-xs text-gray-500">
                <span className="font-semibold">{t.disclaimer}: </span>{result.disclaimer}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
